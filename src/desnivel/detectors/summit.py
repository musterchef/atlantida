"""Rilevatore della vetta principale di una tappa.

Emette **al più un evento `summit`** per tappa (MAJOR), corrispondente
al picco con **prominenza topografica massima** sopra una soglia di
config. Non al massimo globale: se la tappa termina in cima (es. arrivo
in collina), il massimo globale è sul bordo e la prominenza è zero da
quel lato. La selezione per prominenza cattura invece il colle vero
attraversato a metà strada — che è il contenuto musicale interessante.

Definizione di prominenza usata: per ogni massimo locale, la differenza
tra l'altezza del picco e il *più alto* fra i minimi laterali calcolati
percorrendo il segnale verso sinistra/destra finché non si incontra un
punto più alto del picco. Variante "two-sided" classica del concetto
topografico, robusta e implementabile in O(n) ammortizzato.

Riferimenti: ARCHITETTURA-MUSICALE.md §4.1, CONTRATTO-MODULAZIONI.md
§3.1 (v0.3).
"""
from __future__ import annotations

from typing import Iterable

import numpy as np

from ..config import DEFAULT_CONFIG, Config
from ..events import Event, EventCategory
from ..track import GeoPoint, Track
from ._elevation import sample_at, smooth_elevation


class SummitDetector:
    """Restituisce la vetta principale della tappa, se abbastanza prominente.

    Convenzioni:
    - massimo **una** vetta per tappa: quella con prominenza massima;
    - se nessun picco supera ``EventConfig.summit_min_prominence_m``,
      non emette nulla;
    - i picchi sul bordo (tappa che inizia o finisce in cima) hanno
      prominenza zero su un lato e vengono ignorati: per quel caso esiste
      l'evento ``arrival_climb``;
    - se l'elevazione non è presente nei sample, non emette nulla.

    La selezione "una sola" è fatta qui dentro, non dalla pipeline: il
    cooldown del Pipeline resta come rete di sicurezza generica.
    """

    def __init__(self, config: Config = DEFAULT_CONFIG) -> None:
        self.config = config

    def detect(self, track: Track) -> Iterable[Event]:
        ele = track.samples.get("ele")
        if ele is None or track.n_samples < 3:
            return []
        ele = np.asarray(ele, dtype=float)
        if not np.isfinite(ele).any():
            return []

        smoothed = smooth_elevation(ele, self.config.timing.internal_rate_hz)
        peak_idx, prominence = _highest_prominence_peak(smoothed)
        if peak_idx is None:
            return []

        threshold = self.config.events.summit_min_prominence_m
        if prominence < threshold:
            return []

        return [self._build_event(track, peak_idx, smoothed, prominence)]

    def _build_event(
        self,
        track: Track,
        peak_idx: int,
        smoothed: np.ndarray,
        prominence: float,
    ) -> Event:
        lat = sample_at(track, "lat", peak_idx)
        lon = sample_at(track, "lon", peak_idx)
        location: GeoPoint | None = None
        if lat is not None and lon is not None:
            location = GeoPoint(lat=lat, lon=lon, ele=float(smoothed[peak_idx]))
        return Event(
            kind="summit",
            category=EventCategory.MAJOR,
            t=float(track.t[peak_idx]),
            location=location,
            payload={
                "ele_m": float(smoothed[peak_idx]),
                "prominence_m": float(prominence),
            },
            source_id="gpx_auto",
        )


# ── helper ─────────────────────────────────────────────────────────


def _local_maxima(signal: np.ndarray) -> np.ndarray:
    """Indici dei massimi locali stretti (escludendo i bordi)."""
    if signal.size < 3:
        return np.array([], dtype=int)
    interior = np.where(
        (signal[1:-1] > signal[:-2]) & (signal[1:-1] >= signal[2:])
    )[0]
    return interior + 1


def _peak_prominence(signal: np.ndarray, idx: int) -> float:
    """Prominenza topografica del picco in ``idx``.

    Cammina a sinistra e a destra finché non incontra un punto **più
    alto** del picco (o il bordo). La prominenza è la differenza tra il
    picco e il *più alto* dei due minimi incontrati.
    Picchi sul bordo: la prominenza dal lato del bordo si comporta come
    se il bordo fosse a quota -inf e si confronta col minimo dell'altro
    lato. In pratica un picco al bordo ha prominenza zero perché il
    "minimo" su quel lato coincide col picco stesso.
    """
    if idx <= 0 or idx >= signal.size - 1:
        return 0.0
    peak = float(signal[idx])

    # Sinistra: scendi finché non incontri un punto > peak.
    left_slice = signal[:idx]
    higher_left = np.where(left_slice > peak)[0]
    left_start = int(higher_left[-1]) + 1 if higher_left.size > 0 else 0
    left_min = float(np.min(signal[left_start:idx + 1]))

    # Destra: stessa cosa specchiata.
    right_slice = signal[idx + 1:]
    higher_right = np.where(right_slice > peak)[0]
    right_end = idx + 1 + int(higher_right[0]) if higher_right.size > 0 else signal.size
    right_min = float(np.min(signal[idx:right_end]))

    higher_valley = max(left_min, right_min)
    return peak - higher_valley


def _highest_prominence_peak(signal: np.ndarray) -> tuple[int | None, float]:
    """Trova il picco con la prominenza massima. Ritorna (idx, prom) o (None, 0)."""
    candidates = _local_maxima(signal)
    if candidates.size == 0:
        return None, 0.0
    best_idx: int | None = None
    best_prom = -1.0
    for i in candidates:
        prom = _peak_prominence(signal, int(i))
        if prom > best_prom:
            best_prom = prom
            best_idx = int(i)
    return best_idx, max(best_prom, 0.0)

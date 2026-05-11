"""Rilevatore della vetta principale di una tappa.

Emette **al più un evento `summit`** per tappa (MAJOR), corrispondente
al massimo globale dell'elevazione, se la sua *prominenza* supera la
soglia di config.

La prominenza è definita come la differenza tra il massimo globale e il
più basso tra i due minimi laterali (a sinistra e a destra del massimo):
una semplificazione robusta del concetto topografico. Soglia minima:
``EventConfig.summit_min_prominence_m`` (50 m di default).

Riferimenti: ARCHITETTURA-MUSICALE.md §4.1 (eventi maggiori),
CONTRATTO-MODULAZIONI.md §3.1.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np

from .._filters import savgol_filter
from ..config import DEFAULT_CONFIG, Config
from ..events import Event, EventCategory
from ..track import GeoPoint, Track

# Finestra di smoothing dell'elevazione: ~30 secondi a 10 Hz.
# Riduce il rumore GPS sull'altimetria barometrica senza alterare la
# forma delle salite/discese (durata >> 30 s).
_SMOOTH_WINDOW_S = 30.0


class SummitDetector:
    """Restituisce la vetta principale della tappa, se abbastanza prominente.

    Convenzioni:
    - massimo **una** vetta per tappa: la più alta;
    - se la prominenza è sotto soglia, non emette nulla (vetta troppo
      banale per essere un evento musicale);
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

        smoothed = self._smooth(ele)
        peak_idx = int(np.argmax(smoothed))
        prominence = _prominence(smoothed, peak_idx)

        threshold = self.config.events.summit_min_prominence_m
        if prominence < threshold:
            return []

        return [self._build_event(track, peak_idx, smoothed, prominence)]

    # ── interni ────────────────────────────────────────────────────

    def _smooth(self, ele: np.ndarray) -> np.ndarray:
        rate_hz = self.config.timing.internal_rate_hz
        window = int(_SMOOTH_WINDOW_S * rate_hz)
        # savgol_filter richiede finestra dispari
        if window % 2 == 0:
            window += 1
        if window < 3 or ele.size < window:
            return ele
        return savgol_filter(ele, window_length=window, polyorder=2)

    def _build_event(
        self,
        track: Track,
        peak_idx: int,
        smoothed: np.ndarray,
        prominence: float,
    ) -> Event:
        lat = _sample_at(track, "lat", peak_idx)
        lon = _sample_at(track, "lon", peak_idx)
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


def _prominence(signal: np.ndarray, peak_idx: int) -> float:
    """Prominenza semplificata: max - max(min_sinistro, min_destro).

    Misura quanto il picco emerge rispetto al "fondovalle" più alto fra i
    due lati. Per un picco al bordo (tappa che inizia o finisce in cima)
    la prominenza è 0 da quel lato: scartata correttamente come "non vetta".
    """
    if peak_idx <= 0 or peak_idx >= signal.size - 1:
        return 0.0
    peak = float(signal[peak_idx])
    left_min = float(np.min(signal[:peak_idx]))
    right_min = float(np.min(signal[peak_idx + 1:]))
    higher_valley = max(left_min, right_min)
    return peak - higher_valley


def _sample_at(track: Track, channel: str, idx: int) -> float | None:
    arr = track.samples.get(channel)
    if arr is None:
        return None
    value = float(arr[idx])
    return value if np.isfinite(value) else None

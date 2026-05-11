"""Rilevatore di tappa che termina in salita.

Emette **al più un evento `arrival_climb`** per tappa (MAJOR), se la
tappa finisce significativamente più in alto del minimo della seconda
metà. Cattura il caso tipico dell'arrivo in collina (Dogliani, Castel
del Monte): musicalmente è un "arrivo conquistato", distinto sia da
``summit`` (vetta intermedia, prominenza topografica) sia da ``end``
(rarefazione finale generica).

Riferimenti: CONTRATTO-MODULAZIONI.md §3.1 (v0.3).
"""
from __future__ import annotations

from typing import Iterable

import numpy as np

from ..config import DEFAULT_CONFIG, Config
from ..events import Event, EventCategory
from ..track import GeoPoint, Track
from ._elevation import sample_at, smooth_elevation


class ArrivalClimbDetector:
    """Emette ``arrival_climb`` se la tappa termina in salita significativa.

    Logica: confronta l'elevazione finale (smoothed) con il *minimo* della
    seconda metà della tappa. Se la differenza supera
    ``EventConfig.arrival_climb_min_delta_m``, l'evento viene emesso al
    timestamp finale della tappa.

    Scegliere la seconda metà evita di triggerare su tappe che semplicemente
    iniziano in pianura e finiscono in collina dopo una discesa: vogliamo
    catturare l'arrivo in salita, non la salita complessiva.
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

        half = smoothed.size // 2
        second_half = smoothed[half:]
        final_ele = float(second_half[-1])
        min_after_half = float(np.min(second_half))
        delta = final_ele - min_after_half

        threshold = self.config.events.arrival_climb_min_delta_m
        if delta < threshold:
            return []

        return [self._build_event(track, smoothed, delta, final_ele)]

    def _build_event(
        self,
        track: Track,
        smoothed: np.ndarray,
        delta_m: float,
        final_ele_m: float,
    ) -> Event:
        last = track.n_samples - 1
        lat = sample_at(track, "lat", last)
        lon = sample_at(track, "lon", last)
        location: GeoPoint | None = None
        if lat is not None and lon is not None:
            location = GeoPoint(lat=lat, lon=lon, ele=float(smoothed[last]))
        return Event(
            kind="arrival_climb",
            category=EventCategory.MAJOR,
            t=float(track.t[last]),
            location=location,
            payload={
                "climb_delta_m": float(delta_m),
                "final_ele_m": float(final_ele_m),
            },
            source_id="gpx_auto",
        )

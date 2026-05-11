"""Rilevatore di \"prima volta in vista del mare\".

Emette **al piu' un evento `sea`** per tappa (MAJOR) la prima volta che
la distanza dalla costa scende sotto soglia
(``EventConfig.sea_distance_threshold_m``).

Tappe che partono gia' sotto soglia (es. costiera fin dall'inizio)
**non emettono**: non c'e' \"arrivo al mare\", semmai e' una tappa
costiera nel suo complesso (lavoro del ``CoastalClassifier``).

Per costo: valuta a 1 Hz (``EventConfig.sea_detector_eval_rate_hz``)
invece che al sample rate interno (10 Hz). E' sufficiente per cogliere
la prima transizione.

Vedi CONTRATTO-MODULAZIONI.md \u00a73.1.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np

from ..config import DEFAULT_CONFIG, Config
from ..events import Event, EventCategory
from ..geo.coastline import CoastlineProvider, get_default_coastline
from ..track import GeoPoint, Track


class SeaDetector:
    """Emette un MAJOR `sea` alla prima discesa sotto soglia.

    Args:
        config: configurazione (legge `events.sea_distance_threshold_m`,
            `events.sea_detector_eval_rate_hz`, `geo.coastline_bbox`).
        coastline: provider di distanze dalla costa. Se None, viene
            caricato al primo `detect()` da `get_default_coastline()`.
            Inietta un fake nei test per evitare shapely.
    """

    def __init__(
        self,
        config: Config = DEFAULT_CONFIG,
        coastline: CoastlineProvider | None = None,
    ) -> None:
        self.config = config
        self._coastline = coastline

    def _get_coastline(self) -> CoastlineProvider:
        if self._coastline is None:
            self._coastline = get_default_coastline(
                bbox=self.config.geo.coastline_bbox,
            )
        return self._coastline

    def detect(self, track: Track) -> Iterable[Event]:
        lat = track.samples.get("lat")
        lon = track.samples.get("lon")
        if lat is None or lon is None or track.n_samples < 2:
            return []
        lat = np.asarray(lat, dtype=float)
        lon = np.asarray(lon, dtype=float)
        if not (np.isfinite(lat).any() and np.isfinite(lon).any()):
            return []

        # Sottocampionamento per costo.
        rate_in = self.config.timing.internal_rate_hz
        rate_eval = max(self.config.events.sea_detector_eval_rate_hz, 1e-3)
        step = max(int(round(rate_in / rate_eval)), 1)
        idxs = np.arange(0, track.n_samples, step)
        if idxs[-1] != track.n_samples - 1:
            idxs = np.append(idxs, track.n_samples - 1)

        coast = self._get_coastline()
        distances = coast.distances_m(lat[idxs], lon[idxs])

        threshold = self.config.events.sea_distance_threshold_m
        if distances[0] < threshold:
            # Tappa che inizia gia' al mare: niente "prima volta".
            return []

        below = np.where(distances < threshold)[0]
        if below.size == 0:
            return []

        first_idx = int(idxs[int(below[0])])
        return [self._build_event(track, first_idx, float(distances[int(below[0])]))]

    def _build_event(self, track: Track, idx: int, distance_m: float) -> Event:
        lat_v = float(track.samples["lat"][idx])
        lon_v = float(track.samples["lon"][idx])
        ele_arr = track.samples.get("ele")
        ele_v = float(ele_arr[idx]) if ele_arr is not None else None
        return Event(
            kind="sea",
            category=EventCategory.MAJOR,
            t=float(track.t[idx]),
            location=GeoPoint(lat=lat_v, lon=lon_v, ele=ele_v),
            payload={"distance_m": distance_m},
            source_id="gpx_auto",
        )

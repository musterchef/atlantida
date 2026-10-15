"""Rilevatore di passaggio in POI (città, borghi, landmark).

Emette un MAJOR `poi` ogni volta che la traccia **entra** nel raggio
di un POI del registry. Una entrata = la prima volta che il cerchio
contiene il punto, fino a quando la traccia non esce e non rientra
(con cooldown di re-entry per evitare jitter su POI grandi).

Pattern simmetrico a `SeaDetector`: registry iniettabile (niente IO
nei test), valutazione a 1 Hz, payload con `name`, `kind`, `tags`,
`distance_from_center_m`.

Vedi CONTRATTO-MODULAZIONI.md (sezione POI da aggiornare).
"""
from __future__ import annotations

from typing import Iterable

import numpy as np

from ..config import DEFAULT_CONFIG, Config
from ..events import Event, EventCategory
from ..geo.poi import POIRegistry, get_default_registry
from ..track import GeoPoint, Track


class POIDetector:
    """Emette un MAJOR `poi` ad ogni entrata nel raggio di un POI.

    Args:
        config: legge `events.poi_detector_eval_rate_hz` e
            `events.poi_reentry_cooldown_s`.
        registry: insieme di POI. Se None, viene caricato al primo
            `detect()` da `get_default_registry()` (file
            `data/poi.json`, registry vuoto se assente).
    """

    def __init__(
        self,
        config: Config = DEFAULT_CONFIG,
        registry: POIRegistry | None = None,
    ) -> None:
        self.config = config
        self._registry = registry

    def _get_registry(self) -> POIRegistry:
        if self._registry is None:
            self._registry = get_default_registry()
        return self._registry

    def detect(self, track: Track) -> Iterable[Event]:
        registry = self._get_registry()
        if len(registry) == 0:
            return []
        lat = track.samples.get("lat")
        lon = track.samples.get("lon")
        if lat is None or lon is None or track.n_samples < 2:
            return []
        lat = np.asarray(lat, dtype=float)
        lon = np.asarray(lon, dtype=float)
        if not (np.isfinite(lat).any() and np.isfinite(lon).any()):
            return []

        rate_in = self.config.timing.internal_rate_hz
        rate_eval = max(self.config.events.poi_detector_eval_rate_hz, 1e-3)
        step = max(int(round(rate_in / rate_eval)), 1)
        idxs = np.arange(0, track.n_samples, step)
        if idxs[-1] != track.n_samples - 1:
            idxs = np.append(idxs, track.n_samples - 1)

        cooldown_s = self.config.events.poi_reentry_cooldown_s
        n_poi = len(registry)
        # Per ogni POI: timestamp dell'ultima entrata emessa, `-inf` = mai.
        last_entry_t = np.full(n_poi, -np.inf)
        # Stato "dentro": evita di riemettere mentre si attraversa.
        inside_now = np.zeros(n_poi, dtype=bool)

        events: list[Event] = []
        for k in idxs:
            t_k = float(track.t[k])
            d = registry.distances_m(float(lat[k]), float(lon[k]))
            inside = d <= np.array([p.radius_m for p in registry.pois])
            # Entrate fresche: ora dentro, prima fuori, cooldown rispettato.
            fresh = inside & (~inside_now) & (t_k - last_entry_t >= cooldown_s)
            for i in np.where(fresh)[0]:
                i = int(i)
                events.append(self._build_event(track, int(k), registry.pois[i], float(d[i])))
                last_entry_t[i] = t_k
            inside_now = inside

        return events

    def _build_event(self, track: Track, idx: int, poi, distance_m: float) -> Event:
        lat_v = float(track.samples["lat"][idx])
        lon_v = float(track.samples["lon"][idx])
        ele_arr = track.samples.get("ele")
        ele_v = float(ele_arr[idx]) if ele_arr is not None else None
        return Event(
            kind="poi",
            category=EventCategory.MAJOR,
            t=float(track.t[idx]),
            location=GeoPoint(lat=lat_v, lon=lon_v, ele=ele_v),
            payload={
                "name": poi.name,
                "kind": poi.kind,
                "tags": list(poi.tags),
                "distance_from_center_m": distance_m,
            },
            source_id="gpx_auto",
        )

"""Detector dei *bookends*: ``start`` ed ``end`` della tappa.

Ogni tappa ha esattamente un ``start`` (primo campione) e un ``end``
(ultimo campione). I classifier pluggabili (vedi ``classifiers/``)
arricchiscono il payload con varianti come ``climb``, ``sunset``,
``urban``, senza moltiplicare i tipi di evento.

Vedi CONTRATTO-MODULAZIONI.md §3.1.1.
"""
from __future__ import annotations

from typing import Iterable

from ..config import DEFAULT_CONFIG, Config
from ..events import Event, EventCategory
from ..track import GeoPoint, Track
from ._elevation import sample_at


def _location_at(track: Track, idx: int) -> GeoPoint | None:
    lat = sample_at(track, "lat", idx)
    lon = sample_at(track, "lon", idx)
    if lat is None or lon is None:
        return None
    ele = sample_at(track, "ele", idx)
    return GeoPoint(lat=lat, lon=lon, ele=ele)


def _empty_payload() -> dict:
    """Payload base dei bookends: lista di varianti vuota, da arricchire
    coi classifier."""
    return {"variants": []}


class StartDetector:
    """Emette ``start`` al primo campione della tappa."""

    def __init__(self, config: Config = DEFAULT_CONFIG) -> None:
        self.config = config

    def detect(self, track: Track) -> Iterable[Event]:
        if track.n_samples == 0:
            return []
        return [Event(
            kind="start",
            category=EventCategory.MAJOR,
            t=float(track.t[0]),
            location=_location_at(track, 0),
            payload=_empty_payload(),
            source_id="gpx_auto",
        )]


class EndDetector:
    """Emette ``end`` all'ultimo campione della tappa."""

    def __init__(self, config: Config = DEFAULT_CONFIG) -> None:
        self.config = config

    def detect(self, track: Track) -> Iterable[Event]:
        if track.n_samples == 0:
            return []
        last = track.n_samples - 1
        return [Event(
            kind="end",
            category=EventCategory.MAJOR,
            t=float(track.t[last]),
            location=_location_at(track, last),
            payload=_empty_payload(),
            source_id="gpx_auto",
        )]

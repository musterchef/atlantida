"""Test per `SeaDetector` con FakeCoastline (niente shapely)."""
from __future__ import annotations

import numpy as np
import pytest

import desnivel.events_builtin  # noqa: F401
from desnivel.config import DEFAULT_CONFIG
from desnivel.detectors import SeaDetector
from desnivel.events import EventCategory
from desnivel.track import Track


RATE_HZ = 10.0


class _DistanceProfileCoastline:
    """Fake coastline che ritorna distanze dipendenti solo dal *valore di lat*.

    I test costruiscono `lat` come "distanza in metri / 1000": cosi'
    e' facile pilotare la traiettoria sopra/sotto soglia.
    """

    def __init__(self, lat_to_m: float = 1000.0) -> None:
        self._k = lat_to_m

    def distance_m(self, lat: float, lon: float) -> float:
        return float(lat) * self._k

    def distances_m(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
        return np.asarray(lats, dtype=float) * self._k


def _make_track(distances_m: np.ndarray) -> Track:
    """Costruisce un track in cui lat = distance/1000 (km), lon costante."""
    n = distances_m.size
    t = np.arange(n, dtype=float) / RATE_HZ
    lats = distances_m / 1000.0
    lons = np.full(n, 10.0)
    ele = np.zeros(n)
    return Track(
        stage_id="test", t=t,
        samples={"lat": lats, "lon": lons, "ele": ele},
        metadata={},
    )


def test_sea_emitted_on_first_crossing():
    n = 60 * int(RATE_HZ)  # 60 s
    distances = np.concatenate([
        np.full(30 * int(RATE_HZ), 5000.0),   # 5 km dalla costa
        np.full(30 * int(RATE_HZ), 100.0),    # 100 m: ben sotto soglia (500)
    ])
    track = _make_track(distances)
    det = SeaDetector(DEFAULT_CONFIG, coastline=_DistanceProfileCoastline())
    events = list(det.detect(track))
    assert len(events) == 1
    ev = events[0]
    assert ev.kind == "sea"
    assert ev.category is EventCategory.MAJOR
    assert ev.payload["distance_m"] == pytest.approx(100.0, abs=1.0)
    # La transizione e' al secondo 30; con eval a 1 Hz arriva
    # a t fra 30 e 31.
    assert 29.0 <= ev.t <= 31.0
    assert ev.source_id == "gpx_auto"


def test_sea_not_emitted_if_starts_below_threshold():
    """Tappa costiera dall'inizio: niente evento."""
    distances = np.full(120 * int(RATE_HZ), 200.0)
    track = _make_track(distances)
    det = SeaDetector(DEFAULT_CONFIG, coastline=_DistanceProfileCoastline())
    assert list(det.detect(track)) == []


def test_sea_not_emitted_if_always_above():
    distances = np.full(120 * int(RATE_HZ), 10_000.0)
    track = _make_track(distances)
    det = SeaDetector(DEFAULT_CONFIG, coastline=_DistanceProfileCoastline())
    assert list(det.detect(track)) == []


def test_sea_emits_once_even_with_multiple_crossings():
    """Sotto, sopra, sotto: emette solo la prima volta."""
    seg = 20 * int(RATE_HZ)
    distances = np.concatenate([
        np.full(seg, 5000.0),
        np.full(seg, 100.0),
        np.full(seg, 5000.0),
        np.full(seg, 100.0),
    ])
    track = _make_track(distances)
    det = SeaDetector(DEFAULT_CONFIG, coastline=_DistanceProfileCoastline())
    events = list(det.detect(track))
    assert len(events) == 1
    # Prima transizione a t=20s
    assert 19.0 <= events[0].t <= 21.0


def test_sea_returns_empty_without_geo():
    track = Track(
        stage_id="t",
        t=np.arange(100) / RATE_HZ,
        samples={"ele": np.zeros(100)},
        metadata={},
    )
    det = SeaDetector(DEFAULT_CONFIG, coastline=_DistanceProfileCoastline())
    assert list(det.detect(track)) == []

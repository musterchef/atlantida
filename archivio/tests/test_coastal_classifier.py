"""Test per `CoastalClassifier`."""
from __future__ import annotations

import numpy as np
import pytest

import desnivel.events_builtin  # noqa: F401
from desnivel.classifiers import CoastalClassifier
from desnivel.config import DEFAULT_CONFIG
from desnivel.events import Event, EventCategory
from desnivel.track import GeoPoint, Track


RATE_HZ = 10.0


class _FixedCoastline:
    """Fake che ritorna una distanza pre-impostata."""

    def __init__(self, distance_m: float) -> None:
        self._d = float(distance_m)

    def distance_m(self, lat: float, lon: float) -> float:
        return self._d

    def distances_m(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
        return np.full(np.shape(lats), self._d)


def _end_at(lat: float, lon: float) -> Event:
    return Event(
        kind="end",
        category=EventCategory.MAJOR,
        t=1000.0,
        location=GeoPoint(lat=lat, lon=lon, ele=0.0),
        payload={"variants": []},
        source_id="gpx_auto",
    )


def _empty_track() -> Track:
    return Track(stage_id="t", t=np.array([0.0]), samples={}, metadata={})


def test_coastal_variant_added_when_near_coast():
    out = CoastalClassifier(
        DEFAULT_CONFIG, coastline=_FixedCoastline(200.0),
    ).classify(_end_at(44.0, 10.0), _empty_track())
    assert out["variants"] == ["coastal"]
    assert out["coast_distance_m"] == pytest.approx(200.0)


def test_no_variant_when_far_from_coast():
    out = CoastalClassifier(
        DEFAULT_CONFIG, coastline=_FixedCoastline(5000.0),
    ).classify(_end_at(44.0, 10.0), _empty_track())
    assert out == {}


def test_threshold_boundary_excluded():
    """Soglia coastal_arrival_threshold_m = 1000 di default: 1000 e' fuori."""
    out = CoastalClassifier(
        DEFAULT_CONFIG,
        coastline=_FixedCoastline(DEFAULT_CONFIG.events.coastal_arrival_threshold_m),
    ).classify(_end_at(44.0, 10.0), _empty_track())
    assert out == {}


def test_no_location_means_no_variant():
    ev = Event(kind="end", category=EventCategory.MAJOR, t=0.0, payload={"variants": []})
    out = CoastalClassifier(
        DEFAULT_CONFIG, coastline=_FixedCoastline(50.0),
    ).classify(ev, _empty_track())
    assert out == {}


def test_applies_only_to_end():
    assert CoastalClassifier.applies_to_kinds == ("start", "end")

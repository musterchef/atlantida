"""Test per ``ArrivalClimbDetector``."""
from __future__ import annotations

import numpy as np
import pytest

import desnivel.events_builtin  # noqa: F401
from desnivel.config import DEFAULT_CONFIG
from desnivel.detectors import ArrivalClimbDetector
from desnivel.events import EventCategory
from desnivel.track import Track


RATE_HZ = 10.0


def _make_track(ele: np.ndarray, lat: np.ndarray | None = None, lon: np.ndarray | None = None) -> Track:
    n = len(ele)
    t = np.arange(n, dtype=float) / RATE_HZ
    samples: dict[str, np.ndarray] = {"ele": ele}
    if lat is not None:
        samples["lat"] = lat
    if lon is not None:
        samples["lon"] = lon
    return Track(stage_id="test", t=t, samples=samples, metadata={})


def test_arrival_climb_emitted_on_uphill_finish():
    """Tappa che termina 200m sopra il minimo della seconda meta'."""
    n = 60 * 60 * int(RATE_HZ)
    half = n // 2
    # Prima meta' piatta a 100m, seconda meta' sale fino a 300m.
    ele = np.concatenate([
        np.full(half, 100.0),
        np.linspace(100.0, 300.0, n - half),
    ])
    track = _make_track(ele)
    events = list(ArrivalClimbDetector(DEFAULT_CONFIG).detect(track))
    assert len(events) == 1
    e = events[0]
    assert e.kind == "arrival_climb"
    assert e.category is EventCategory.MAJOR
    assert e.payload["climb_delta_m"] == pytest.approx(200.0, abs=2.0)
    assert e.payload["final_ele_m"] == pytest.approx(300.0, abs=2.0)
    # Evento sul timestamp finale.
    assert e.t == pytest.approx((n - 1) / RATE_HZ, abs=0.5)
    assert e.source_id == "gpx_auto"


def test_arrival_climb_not_emitted_on_flat_finish():
    """Tappa piatta: niente evento."""
    n = 30 * 60 * int(RATE_HZ)
    ele = np.full(n, 100.0)
    track = _make_track(ele)
    assert list(ArrivalClimbDetector(DEFAULT_CONFIG).detect(track)) == []


def test_arrival_climb_not_emitted_on_descent_finish():
    """Tappa che finisce in discesa: niente evento."""
    n = 30 * 60 * int(RATE_HZ)
    ele = np.linspace(500.0, 100.0, n)
    track = _make_track(ele)
    assert list(ArrivalClimbDetector(DEFAULT_CONFIG).detect(track)) == []


def test_arrival_climb_ignores_first_half_descent():
    """Tappa che parte in alto, scende, finisce in piano: niente evento.

    L'algoritmo deve guardare solo la seconda metà: una salita nella
    prima metà non conta come 'arrivo in salita'."""
    n = 60 * 60 * int(RATE_HZ)
    half = n // 2
    ele = np.concatenate([
        np.linspace(500.0, 100.0, half),    # discesa nella prima meta'
        np.full(n - half, 100.0),           # piatto nella seconda
    ])
    track = _make_track(ele)
    assert list(ArrivalClimbDetector(DEFAULT_CONFIG).detect(track)) == []


def test_arrival_climb_below_threshold_not_emitted():
    """Dislivello finale 20m: sotto soglia (50m), niente evento."""
    n = 30 * 60 * int(RATE_HZ)
    half = n // 2
    ele = np.concatenate([
        np.full(half, 100.0),
        np.linspace(100.0, 120.0, n - half),
    ])
    track = _make_track(ele)
    assert list(ArrivalClimbDetector(DEFAULT_CONFIG).detect(track)) == []


def test_arrival_climb_returns_empty_without_elevation():
    n = 100
    track = Track(
        stage_id="t",
        t=np.arange(n) / RATE_HZ,
        samples={},
        metadata={},
    )
    assert list(ArrivalClimbDetector(DEFAULT_CONFIG).detect(track)) == []

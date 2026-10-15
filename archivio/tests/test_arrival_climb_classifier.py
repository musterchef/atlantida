"""Test per ``ArrivalClimbClassifier``.

Il classifier riceve un evento ``end`` (sintetico) e il `Track`, e ritorna
un dict da fondere nel payload. Test indipendenti dalla pipeline.
"""
from __future__ import annotations

import numpy as np
import pytest

import desnivel.events_builtin  # noqa: F401
from desnivel.classifiers import ArrivalClimbClassifier
from desnivel.config import DEFAULT_CONFIG
from desnivel.events import Event, EventCategory
from desnivel.track import Track


RATE_HZ = 10.0


def _make_track(ele: np.ndarray) -> Track:
    n = len(ele)
    t = np.arange(n, dtype=float) / RATE_HZ
    return Track(stage_id="test", t=t, samples={"ele": ele}, metadata={})


def _end_event(track: Track) -> Event:
    last = track.n_samples - 1
    return Event(
        kind="end",
        category=EventCategory.MAJOR,
        t=float(track.t[last]),
        payload={"variants": []},
        source_id="gpx_auto",
    )


def test_climb_variant_added_on_uphill_finish():
    n = 60 * 60 * int(RATE_HZ)
    half = n // 2
    ele = np.concatenate([
        np.full(half, 100.0),
        np.linspace(100.0, 300.0, n - half),
    ])
    track = _make_track(ele)
    out = ArrivalClimbClassifier(DEFAULT_CONFIG).classify(_end_event(track), track)
    assert out["variants"] == ["climb"]
    assert out["climb_delta_m"] == pytest.approx(200.0, abs=2.0)
    assert out["final_ele_m"] == pytest.approx(300.0, abs=2.0)


def test_no_variant_on_flat_finish():
    n = 30 * 60 * int(RATE_HZ)
    ele = np.full(n, 100.0)
    track = _make_track(ele)
    assert ArrivalClimbClassifier(DEFAULT_CONFIG).classify(_end_event(track), track) == {}


def test_no_variant_on_descent_finish():
    n = 30 * 60 * int(RATE_HZ)
    ele = np.linspace(500.0, 100.0, n)
    track = _make_track(ele)
    assert ArrivalClimbClassifier(DEFAULT_CONFIG).classify(_end_event(track), track) == {}


def test_ignores_first_half_descent():
    """Salita solo nella prima meta' non e' arrivo in salita."""
    n = 60 * 60 * int(RATE_HZ)
    half = n // 2
    ele = np.concatenate([
        np.linspace(500.0, 100.0, half),
        np.full(n - half, 100.0),
    ])
    track = _make_track(ele)
    assert ArrivalClimbClassifier(DEFAULT_CONFIG).classify(_end_event(track), track) == {}


def test_below_threshold_no_variant():
    n = 30 * 60 * int(RATE_HZ)
    half = n // 2
    ele = np.concatenate([
        np.full(half, 100.0),
        np.linspace(100.0, 120.0, n - half),
    ])
    track = _make_track(ele)
    assert ArrivalClimbClassifier(DEFAULT_CONFIG).classify(_end_event(track), track) == {}


def test_empty_without_elevation():
    n = 100
    track = Track(stage_id="t", t=np.arange(n) / RATE_HZ, samples={}, metadata={})
    assert ArrivalClimbClassifier(DEFAULT_CONFIG).classify(_end_event(track), track) == {}


def test_applies_only_to_end():
    assert ArrivalClimbClassifier.applies_to_kinds == ("end",)

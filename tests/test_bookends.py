"""Test per ``StartDetector`` e ``EndDetector``."""
from __future__ import annotations

import numpy as np

import desnivel.events_builtin  # noqa: F401
from desnivel.config import DEFAULT_CONFIG
from desnivel.detectors import EndDetector, StartDetector
from desnivel.events import EventCategory
from desnivel.track import Track


RATE_HZ = 10.0


def _make_track(n: int, with_geo: bool = True) -> Track:
    t = np.arange(n, dtype=float) / RATE_HZ
    samples: dict[str, np.ndarray] = {"ele": np.linspace(100.0, 200.0, n)}
    if with_geo:
        samples["lat"] = np.linspace(44.0, 45.0, n)
        samples["lon"] = np.linspace(7.0, 8.0, n)
    return Track(stage_id="test", t=t, samples=samples, metadata={})


def test_start_emitted_at_first_sample():
    track = _make_track(100)
    events = list(StartDetector(DEFAULT_CONFIG).detect(track))
    assert len(events) == 1
    ev = events[0]
    assert ev.kind == "start"
    assert ev.category is EventCategory.MAJOR
    assert ev.t == 0.0
    assert ev.payload == {"variants": []}
    assert ev.source_id == "gpx_auto"
    assert ev.location is not None
    assert ev.location.lat == 44.0


def test_end_emitted_at_last_sample():
    track = _make_track(100)
    events = list(EndDetector(DEFAULT_CONFIG).detect(track))
    assert len(events) == 1
    ev = events[0]
    assert ev.kind == "end"
    assert ev.category is EventCategory.MAJOR
    assert ev.t == (100 - 1) / RATE_HZ
    assert ev.payload == {"variants": []}
    assert ev.location is not None
    assert ev.location.lat == 45.0


def test_bookends_empty_on_empty_track():
    track = Track(stage_id="t", t=np.array([], dtype=float), samples={}, metadata={})
    assert list(StartDetector(DEFAULT_CONFIG).detect(track)) == []
    assert list(EndDetector(DEFAULT_CONFIG).detect(track)) == []


def test_bookends_without_geo():
    track = _make_track(50, with_geo=False)
    s = list(StartDetector(DEFAULT_CONFIG).detect(track))[0]
    e = list(EndDetector(DEFAULT_CONFIG).detect(track))[0]
    assert s.location is None
    assert e.location is None

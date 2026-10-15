"""Test per la fusione classifier nella ``Pipeline`` e per il bypass
cooldown dei framing (``start``/``end``)."""
from __future__ import annotations

from typing import Any, Mapping

import numpy as np

import desnivel.events_builtin  # noqa: F401
from desnivel.classifiers import ArrivalClimbClassifier
from desnivel.config import DEFAULT_CONFIG
from desnivel.detectors import EndDetector, StartDetector
from desnivel.events import Event, EventCategory
from desnivel.pipeline import Pipeline
from desnivel.track import Track


RATE_HZ = 10.0


def _make_uphill_track(n: int) -> Track:
    t = np.arange(n, dtype=float) / RATE_HZ
    half = n // 2
    ele = np.concatenate([
        np.full(half, 100.0),
        np.linspace(100.0, 300.0, n - half),
    ])
    return Track(stage_id="t", t=t, samples={"ele": ele}, metadata={})


def test_arrival_climb_classifier_marks_end():
    track = _make_uphill_track(60 * 60 * int(RATE_HZ))
    pipe = Pipeline(
        detectors=[StartDetector(DEFAULT_CONFIG), EndDetector(DEFAULT_CONFIG)],
        classifiers=[ArrivalClimbClassifier(DEFAULT_CONFIG)],
        config=DEFAULT_CONFIG,
    )
    _, events = pipe.run(track)
    kinds = [e.kind for e in events]
    assert kinds == ["start", "end"]
    start, end = events
    assert start.payload["variants"] == []
    assert end.payload["variants"] == ["climb"]
    assert end.payload["climb_delta_m"] > 100.0


def test_classifier_does_not_apply_to_other_kinds():
    """Un classifier con ``applies_to_kinds=('end',)`` non tocca ``start``."""

    class TaggingClassifier:
        applies_to_kinds = ("end",)

        def classify(self, event: Event, track: Track) -> Mapping[str, Any]:
            return {"variants": ["tagged"]}

    track = _make_uphill_track(1000)
    pipe = Pipeline(
        detectors=[StartDetector(DEFAULT_CONFIG), EndDetector(DEFAULT_CONFIG)],
        classifiers=[TaggingClassifier()],
        config=DEFAULT_CONFIG,
    )
    _, events = pipe.run(track)
    by_kind = {e.kind: e for e in events}
    assert by_kind["start"].payload["variants"] == []
    assert by_kind["end"].payload["variants"] == ["tagged"]


def test_multiple_classifiers_merge_variants():
    """Piu' classifier che contribuiscono varianti diverse si accumulano."""

    class A:
        applies_to_kinds = ("end",)

        def classify(self, event: Event, track: Track) -> Mapping[str, Any]:
            return {"variants": ["climb"]}

    class B:
        applies_to_kinds = ("end",)

        def classify(self, event: Event, track: Track) -> Mapping[str, Any]:
            return {"variants": ["sunset"], "sun_delta_s": 120.0}

    track = _make_uphill_track(1000)
    pipe = Pipeline(
        detectors=[EndDetector(DEFAULT_CONFIG)],
        classifiers=[A(), B()],
        config=DEFAULT_CONFIG,
    )
    _, events = pipe.run(track)
    end = events[0]
    assert end.payload["variants"] == ["climb", "sunset"]
    assert end.payload["sun_delta_s"] == 120.0


def test_framing_bypasses_cooldown():
    """Anche se start e end fossero a distanza minore del cooldown
    (qui artificialmente piccolissimo), devono comparire entrambi."""
    n = 100
    track = Track(
        stage_id="t",
        t=np.arange(n, dtype=float) / RATE_HZ,
        samples={"ele": np.full(n, 100.0)},
        metadata={},
    )
    pipe = Pipeline(
        detectors=[StartDetector(DEFAULT_CONFIG), EndDetector(DEFAULT_CONFIG)],
        config=DEFAULT_CONFIG,
    )
    _, events = pipe.run(track)
    assert [e.kind for e in events] == ["start", "end"]

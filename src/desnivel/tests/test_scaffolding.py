"""Smoke test dello scaffolding end-to-end."""
from __future__ import annotations

import json
from pathlib import Path

import desnivel.events_builtin  # noqa: F401
from desnivel.config import DEFAULT_CONFIG
from desnivel.events import EVENT_REGISTRY, Event, EventCategory
from desnivel.pipeline import Pipeline
from desnivel.sinks import FileSink
from desnivel.track import make_empty_track


def test_registry_populated() -> None:
    assert EVENT_REGISTRY.has("summit")
    assert EVENT_REGISTRY.has("start")
    assert EVENT_REGISTRY.get("summit").default_category is EventCategory.MAJOR


def test_pipeline_empty_runs_end_to_end(tmp_path: Path) -> None:
    track = make_empty_track(
        stage_id="tappa_test",
        duration_s=60.0,
        rate_hz=DEFAULT_CONFIG.timing.internal_rate_hz,
    )
    sink = FileSink(output_dir=tmp_path)
    pipeline = Pipeline(sinks=[sink])
    frame, events = pipeline.run(track)

    assert frame.n_samples == track.n_samples
    assert frame.channel_names == ()
    assert events == []

    csv_path = tmp_path / "tappa_test_modulations.csv"
    json_path = tmp_path / "tappa_test_events.json"
    assert csv_path.exists()
    assert json_path.exists()
    payload = json.loads(json_path.read_text())
    assert payload == {"stage_id": "tappa_test", "events": []}

    # Solo la riga di header + una riga per campione.
    rows = csv_path.read_text().strip().splitlines()
    assert rows[0] == "t"
    assert len(rows) == track.n_samples + 1


def test_pipeline_filters_major_events_with_cooldown(tmp_path: Path) -> None:
    track = make_empty_track(
        stage_id="tappa_test",
        duration_s=3600.0,
        rate_hz=DEFAULT_CONFIG.timing.internal_rate_hz,
    )

    class _BurstDetector:
        def detect(self, track):
            # Due eventi major a 1s di distanza: ne deve sopravvivere uno solo.
            return [
                Event(kind="summit", category=EventCategory.MAJOR, t=100.0),
                Event(kind="summit", category=EventCategory.MAJOR, t=101.0),
            ]

    pipeline = Pipeline(detectors=[_BurstDetector()])
    _, events = pipeline.run(track)
    assert len(events) == 1
    assert events[0].t == 100.0


def test_pipeline_caps_major_events_per_stage(tmp_path: Path) -> None:
    cfg = DEFAULT_CONFIG
    track = make_empty_track(
        stage_id="tappa_test",
        duration_s=10 * 3600.0,
        rate_hz=cfg.timing.internal_rate_hz,
    )

    class _LotsDetector:
        def detect(self, track):
            # Distanziati ben oltre il cooldown massimo.
            return [
                Event(kind="summit", category=EventCategory.MAJOR, t=float(i * 3600))
                for i in range(10)
            ]

    pipeline = Pipeline(detectors=[_LotsDetector()])
    _, events = pipeline.run(track)
    assert len(events) == cfg.events.major_max_per_stage

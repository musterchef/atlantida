"""CLI: esegue la pipeline su una singola tappa.

In questa fase di scaffolding la sorgente del `Track` è sintetica:
un Track vuoto di durata configurabile, sufficiente a validare la
catena end-to-end. Il loader GPX vero sostituirà ``_build_track``
senza modifiche al resto della CLI.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import desnivel.events_builtin  # noqa: F401  (registra i tipi standard)
from desnivel.config import DEFAULT_CONFIG, Config
from desnivel.pipeline import Pipeline
from desnivel.sinks import FileSink
from desnivel.track import Track, make_empty_track


def _build_track(stage_id: str, duration_s: float, config: Config) -> Track:
    """Sorgente del Track. Placeholder finché non c'è il loader GPX."""
    return make_empty_track(
        stage_id=stage_id,
        duration_s=duration_s,
        rate_hz=config.timing.internal_rate_hz,
    )


def _build_sink(name: str, output_dir: Path) -> FileSink:
    if name == "file":
        return FileSink(output_dir=output_dir)
    raise SystemExit(f"Sink '{name}' non supportato in questa fase.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_stage",
        description="Esegue la pipeline DESNIVEL su una tappa.",
    )
    parser.add_argument("--stage", required=True, help="Identificatore tappa (es. tappa_01).")
    parser.add_argument(
        "--duration", type=float, default=3600.0,
        help="Durata della tappa in secondi (placeholder, finché non c'è il loader GPX).",
    )
    parser.add_argument("--sink", default="file", choices=["file"])
    parser.add_argument(
        "--output-dir", default="output",
        help="Cartella di output per il sink 'file'.",
    )
    args = parser.parse_args(argv)

    config = DEFAULT_CONFIG
    track = _build_track(args.stage, args.duration, config)
    sink = _build_sink(args.sink, Path(args.output_dir))

    pipeline = Pipeline(
        modulators=[],
        detectors=[],
        sinks=[sink],
        config=config,
    )
    frame, events = pipeline.run(track)

    print(
        f"[run_stage] {track.stage_id}: "
        f"{track.n_samples} campioni, {len(frame.channel_names)} canali, "
        f"{len(events)} eventi → {args.output_dir}/",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

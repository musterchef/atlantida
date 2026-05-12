"""CLI: esegue la pipeline su una singola tappa."""
from __future__ import annotations

import argparse
from pathlib import Path

import desnivel.events_builtin  # noqa: F401  (registra i tipi standard)
from desnivel.classifiers import (
    ArrivalClimbClassifier,
    CoastalClassifier,
    CoastalStageClassifier,
    SeaViewClassifier,
)
from desnivel.config import DEFAULT_CONFIG, Config
from desnivel.loader import load_track
from desnivel.detectors import EndDetector, POIDetector, SeaDetector, StartDetector, SummitDetector
from desnivel.modulators import JourneyModulator, MacroModulator, TensionModulator
from desnivel.pipeline import Pipeline
from desnivel.sinks import FileSink
from desnivel.track import Track, make_empty_track


def _resolve_gpx_path(stage: str, gpx_dir: Path) -> Path | None:
    """Cerca un file GPX la cui parte iniziale corrisponde a ``stage``.

    Convenzione: ``stage='tappa_01'`` matcha ``tappa01_*.gpx``.
    """
    head = stage.replace("_", "")  # tappa_01 -> tappa01
    matches = sorted(gpx_dir.glob(f"{head}_*.gpx"))
    return matches[0] if matches else None


def _build_track(
    stage: str, gpx_dir: Path, duration_s: float, config: Config,
) -> Track:
    """Costruisce un Track. Preferisce il GPX vero; altrimenti placeholder vuoto."""
    gpx_path = _resolve_gpx_path(stage, gpx_dir)
    if gpx_path is not None:
        return load_track(gpx_path, config=config, stage_id=stage)
    return make_empty_track(
        stage_id=stage,
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
        "--gpx-dir", default="gpx", type=Path,
        help="Cartella con i file .gpx delle tappe.",
    )
    parser.add_argument(
        "--duration", type=float, default=3600.0,
        help="Durata fallback in secondi se non viene trovato il GPX.",
    )
    parser.add_argument("--sink", default="file", choices=["file"])
    parser.add_argument(
        "--output-dir", default="output", type=Path,
        help="Cartella di output per il sink 'file'.",
    )
    args = parser.parse_args(argv)

    config = DEFAULT_CONFIG
    track = _build_track(args.stage, args.gpx_dir, args.duration, config)
    sink = _build_sink(args.sink, args.output_dir)

    pipeline = Pipeline(
        modulators=[
            JourneyModulator(config),
            TensionModulator(config),
            MacroModulator(config),
        ],
        detectors=[
            StartDetector(config),
            EndDetector(config),
            SummitDetector(config),
            SeaDetector(config),
            POIDetector(config),
        ],
        classifiers=[
            ArrivalClimbClassifier(config),
            CoastalClassifier(config),
            CoastalStageClassifier(config),
            SeaViewClassifier(config),
        ],
        sinks=[sink],
        config=config,
    )
    frame, events = pipeline.run(track)

    source = track.metadata.get("source_path", "(synthetic)")
    print(
        f"[run_stage] {track.stage_id}: "
        f"durata={track.duration_s:.1f}s, {track.n_samples} campioni, "
        f"{len(frame.channel_names)} canali, {len(events)} eventi  "
        f"<- {source}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

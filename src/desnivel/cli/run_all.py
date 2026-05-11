"""CLI: esegue la pipeline su tutte le tappe e produce un report.

Riusa la costruzione di Track/sink/pipeline di ``run_stage`` ma aggiunge:
- discovery automatico delle tappe da ``--gpx-dir``;
- report di metriche per tappa (durata, n_samples, range dei canali,
  conteggio eventi per categoria);
- riepilogo aggregato (totali e medie) a fine corsa.

Serve a validare che la pipeline si comporti in modo coerente sull'intero
corpus, senza dover lanciare 12 volte ``run_stage``.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

import desnivel.events_builtin  # noqa: F401  (registra i tipi standard)
from desnivel.config import DEFAULT_CONFIG, Config
from desnivel.events import Event, EventCategory
from desnivel.modulation import ModulationFrame
from desnivel.modulators import JourneyModulator
from desnivel.pipeline import Pipeline
from desnivel.sinks import FileSink
from desnivel.track import Track

from desnivel.cli.run_stage import _build_track


# ── Discovery ──────────────────────────────────────────────────────────


_STAGE_PATTERN = re.compile(r"^tappa(\d{2})_")


def discover_stages(gpx_dir: Path) -> list[str]:
    """Trova tutte le tappe disponibili in ``gpx_dir``.

    Convenzione: file ``tappaNN_*.gpx`` → stage_id ``tappa_NN``.
    Ritorna ordinato per numero di tappa.
    """
    stages: list[tuple[int, str]] = []
    for path in gpx_dir.glob("tappa*_*.gpx"):
        m = _STAGE_PATTERN.match(path.name)
        if m:
            n = int(m.group(1))
            stages.append((n, f"tappa_{m.group(1)}"))
    return [s for _, s in sorted(stages)]


# ── Metriche ───────────────────────────────────────────────────────────


@dataclass
class StageMetrics:
    """Sintesi numerica di una tappa, serializzabile in JSON."""

    stage_id: str
    duration_s: float
    n_samples: int
    n_channels: int
    n_events_major: int
    n_events_minor: int
    # Min/max per canale di modulazione (utile per spottare canali piatti
    # o fuori range [0,1] attesi).
    channel_ranges: dict[str, tuple[float, float]]


def _channel_ranges(frame: ModulationFrame) -> dict[str, tuple[float, float]]:
    out: dict[str, tuple[float, float]] = {}
    for name, values in frame.channels.items():
        out[name] = (float(np.min(values)), float(np.max(values)))
    return out


def _count_by_category(events: list[Event]) -> tuple[int, int]:
    major = sum(1 for e in events if e.category is EventCategory.MAJOR)
    minor = sum(1 for e in events if e.category is EventCategory.MINOR)
    return major, minor


# ── Esecuzione ─────────────────────────────────────────────────────────


def _process_stage(
    stage: str, gpx_dir: Path, config: Config, sink: FileSink | None,
) -> StageMetrics:
    track: Track = _build_track(stage, gpx_dir, duration_s=3600.0, config=config)
    pipeline = Pipeline(
        modulators=[JourneyModulator(config)],
        detectors=[],
        sinks=[sink] if sink is not None else [],
        config=config,
    )
    frame, events = pipeline.run(track)
    major, minor = _count_by_category(events)
    return StageMetrics(
        stage_id=track.stage_id,
        duration_s=float(track.duration_s),
        n_samples=int(track.n_samples),
        n_channels=len(frame.channel_names),
        n_events_major=major,
        n_events_minor=minor,
        channel_ranges=_channel_ranges(frame),
    )


# ── Report ─────────────────────────────────────────────────────────────


def _format_table(rows: list[StageMetrics]) -> str:
    header = f"{'stage':<10} {'durata':>10} {'campioni':>10} {'canali':>7} {'maj':>4} {'min':>4}"
    lines = [header, "-" * len(header)]
    for r in rows:
        lines.append(
            f"{r.stage_id:<10} {r.duration_s:>9.1f}s {r.n_samples:>10d} "
            f"{r.n_channels:>7d} {r.n_events_major:>4d} {r.n_events_minor:>4d}"
        )
    return "\n".join(lines)


def _format_summary(rows: list[StageMetrics]) -> str:
    if not rows:
        return "Nessuna tappa processata."
    total_dur = sum(r.duration_s for r in rows)
    total_samples = sum(r.n_samples for r in rows)
    total_major = sum(r.n_events_major for r in rows)
    total_minor = sum(r.n_events_minor for r in rows)
    return (
        f"\nTotale: {len(rows)} tappe, "
        f"{total_dur / 3600:.2f}h, {total_samples} campioni, "
        f"{total_major} eventi major, {total_minor} eventi minor."
    )


def _format_channel_ranges(rows: list[StageMetrics]) -> str:
    """Range min/max aggregato per canale su tutte le tappe.

    Aiuta a vedere se un canale sfora il [0,1] atteso o resta piatto.
    """
    if not rows:
        return ""
    # Unisce le chiavi mantenendo l'ordine di prima apparizione.
    all_channels: list[str] = []
    for r in rows:
        for name in r.channel_ranges:
            if name not in all_channels:
                all_channels.append(name)
    lines = ["\nRange canali (min/max su tutte le tappe):"]
    for name in all_channels:
        mins = [r.channel_ranges[name][0] for r in rows if name in r.channel_ranges]
        maxs = [r.channel_ranges[name][1] for r in rows if name in r.channel_ranges]
        lines.append(f"  {name:<24} [{min(mins):+.3f} .. {max(maxs):+.3f}]")
    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run_all",
        description="Esegue la pipeline DESNIVEL su tutte le tappe e produce un report.",
    )
    parser.add_argument(
        "--gpx-dir", default="gpx", type=Path,
        help="Cartella con i file .gpx delle tappe.",
    )
    parser.add_argument(
        "--output-dir", default="output", type=Path,
        help="Cartella di output per il sink 'file'.",
    )
    parser.add_argument(
        "--no-write", action="store_true",
        help="Non scrive i file di output, esegue solo il report.",
    )
    parser.add_argument(
        "--report", type=Path, default=None,
        help="Se passato, salva il report aggregato come JSON in questo path.",
    )
    parser.add_argument(
        "--stages", nargs="*", default=None,
        help="Subset di stage_id da processare (default: tutti quelli trovati).",
    )
    args = parser.parse_args(argv)

    config = DEFAULT_CONFIG
    stages = args.stages or discover_stages(args.gpx_dir)
    if not stages:
        print(f"[run_all] Nessuna tappa trovata in {args.gpx_dir}")
        return 1

    sink = None if args.no_write else FileSink(output_dir=args.output_dir)

    rows: list[StageMetrics] = []
    for stage in stages:
        metrics = _process_stage(stage, args.gpx_dir, config, sink)
        rows.append(metrics)
        print(
            f"[run_all] {metrics.stage_id}: "
            f"{metrics.duration_s:.0f}s, {metrics.n_samples} campioni, "
            f"{metrics.n_channels} canali, "
            f"{metrics.n_events_major}+{metrics.n_events_minor} eventi"
        )

    print()
    print(_format_table(rows))
    print(_format_channel_ranges(rows))
    print(_format_summary(rows))

    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps([asdict(r) for r in rows], indent=2),
            encoding="utf-8",
        )
        print(f"\nReport JSON scritto in {args.report}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

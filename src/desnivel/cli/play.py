"""CLI `desnivel-play`: stream OSC in tempo reale di una tappa.

Costruisce la pipeline standard, calcola modulazioni + eventi, e li
invia via OSC a TouchDesigner/Ableton. Supporta playback accelerato
(`--speed`) per audit rapido.

Esempio::

    desnivel-play --stage tappa_04 --speed 8

Riceve dal contratto:
- canali continui su ``/mod/<group>/<name>`` (frequenze in `config.osc.rates_hz`);
- eventi su ``/event/{major,minor}/<kind>`` con payload JSON.

Vedi `doc/CONTRATTO-MODULAZIONI.md`.
"""
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
from desnivel.config import DEFAULT_CONFIG, Config, OscConfig
from desnivel.detectors import (
    EndDetector,
    POIDetector,
    SeaDetector,
    StartDetector,
    SummitDetector,
)
from desnivel.loader import load_track
from desnivel.modulators import JourneyModulator, TensionModulator
from desnivel.pipeline import Pipeline
from desnivel.sinks import OscSink, UdpOscClient
from desnivel.track import Track, make_empty_track


def _resolve_gpx_path(stage: str, gpx_dir: Path) -> Path | None:
    head = stage.replace("_", "")
    matches = sorted(gpx_dir.glob(f"{head}_*.gpx"))
    return matches[0] if matches else None


def _build_track(
    stage: str, gpx_dir: Path, duration_s: float, config: Config,
) -> Track:
    gpx_path = _resolve_gpx_path(stage, gpx_dir)
    if gpx_path is not None:
        return load_track(gpx_path, config=config, stage_id=stage)
    return make_empty_track(
        stage_id=stage,
        duration_s=duration_s,
        rate_hz=config.timing.internal_rate_hz,
    )


def _build_pipeline(config: Config) -> Pipeline:
    """Costruisce la pipeline standard (stessi detector/modulator di
    `desnivel-run` e `desnivel-all`)."""
    return Pipeline(
        modulators=[JourneyModulator(config), TensionModulator(config)],
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
        sinks=[],  # il sink lo aggiunge il chiamante
        config=config,
    )


def _make_config(host: str, port: int) -> Config:
    """Config standard con override di host/port OSC."""
    base = DEFAULT_CONFIG
    return Config(
        timing=base.timing,
        smoothing=base.smoothing,
        journey=base.journey,
        gpx=base.gpx,
        events=base.events,
        osc=OscConfig(host=host, port=port, rates_hz=base.osc.rates_hz),
        geo=base.geo,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="desnivel-play",
        description="Stream OSC in tempo reale di una tappa.",
    )
    parser.add_argument(
        "--stage", required=True,
        help="Identificatore tappa (es. tappa_01).",
    )
    parser.add_argument(
        "--gpx-dir", default="gpx", type=Path,
        help="Cartella con i file .gpx delle tappe.",
    )
    parser.add_argument(
        "--duration", type=float, default=3600.0,
        help="Durata fallback in secondi se non viene trovato il GPX.",
    )
    parser.add_argument(
        "--speed", type=float, default=1.0,
        help="Moltiplicatore di playback (1.0 = tempo reale).",
    )
    parser.add_argument(
        "--osc-host", default="127.0.0.1",
        help="Host OSC di destinazione (default: localhost).",
    )
    parser.add_argument(
        "--osc-port", type=int, default=9000,
        help="Porta OSC di destinazione (default: 9000).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Calcola la schedule e stampa un riepilogo senza inviare nulla.",
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="Riavvia la tappa all'infinito (Ctrl+C per uscire).",
    )
    args = parser.parse_args(argv)

    if args.speed <= 0:
        raise SystemExit("--speed deve essere > 0")

    config = _make_config(args.osc_host, args.osc_port)
    track = _build_track(args.stage, args.gpx_dir, args.duration, config)
    pipeline = _build_pipeline(config)
    frame, events = pipeline.run(track)

    source = track.metadata.get("source_path", "(synthetic)")
    print(
        f"[desnivel-play] {track.stage_id}: "
        f"durata={track.duration_s:.1f}s, {len(frame.channel_names)} canali, "
        f"{len(events)} eventi  <- {source}",
    )

    if args.dry_run:
        from desnivel.sinks.osc import build_schedule
        schedule = build_schedule(frame, events, config)
        print(f"[dry-run] {len(schedule)} messaggi OSC pianificati. "
              f"Primi 5 e ultimi 5:")
        for m in schedule[:5] + schedule[-5:]:
            print(f"  t={m.t:7.2f}s  {m.address}")
        return 0

    client = UdpOscClient(args.osc_host, args.osc_port)
    sink = OscSink(client=client, config=config, speed=args.speed)
    estimated = track.duration_s / args.speed
    print(
        f"[desnivel-play] invio a {args.osc_host}:{args.osc_port} "
        f"@ speed={args.speed}x (~{estimated:.0f}s previsti)"
        + ("  [loop]" if args.loop else ""),
    )
    try:
        iteration = 0
        while True:
            iteration += 1
            if args.loop:
                print(f"[desnivel-play] giro #{iteration}")
            sink.emit(track.stage_id, frame, events)
            if not args.loop:
                break
    except KeyboardInterrupt:
        print("\n[desnivel-play] interrotto.")
    print("[desnivel-play] fine.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

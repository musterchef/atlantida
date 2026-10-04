"""Riproduce decisioni musicali dal viaggio attraverso l'adattatore Snake."""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

from desnivel.loader import load_track
from desnivel.trip_metrics import build_metric_samples
from desnivel.music import rule_from_dict
from desnivel.journey_music import compose
from desnivel.adapters.snake import ADDRESS, pattern_messages, section_pattern_messages
from desnivel.sinks.osc import UdpOscClient
from desnivel.sinks.schedule import ScheduledMessage, play_schedule


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gpx", type=Path, required=True)
    modes = p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--rules", type=Path)
    modes.add_argument("--stage-music", type=Path)
    p.add_argument("--preset", type=Path)
    p.add_argument("--adapter", choices=["snake"], default="snake")
    p.add_argument("--speed", type=float, default=1)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=9001)
    p.add_argument("--seed", type=int, help="Ripete le estrazioni delle Shape di Snake.")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    if not math.isfinite(args.speed) or args.speed <= 0:
        p.error("speed deve essere finita e positiva")
    try:
        samples = build_metric_samples(load_track(args.gpx))
        if args.stage_music:
            if not args.preset:
                p.error("--stage-music richiede --preset")
            changes = compose(samples, json.loads(args.stage_music.read_text()),
                              json.loads(args.preset.read_text()))
        else:
            if args.preset:
                p.error("--preset richiede --stage-music")
            rule = rule_from_dict(json.loads(args.rules.read_text()))
            pattern_messages(rule.low)
            pattern_messages(rule.high)
            changes = [change for sample in samples if (change := rule.update(sample)) is not None]
        for change in changes:
            pattern_messages(change.pattern)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        p.error(str(exc))
    schedule = []
    for change, messages in section_pattern_messages(changes, random.Random(args.seed)):
        print(f"t={change.elapsed_s:g}s ({change.elapsed_s / args.speed:.1f}s replay) "
              f"{change.state}: {sum(change.pattern.gates)} gate; note={change.pattern.notes}")
        for name, value in messages:
            if name == "gate_shape":
                print(f"  Gate Shape = {value:g}")
        schedule.extend(ScheduledMessage(change.elapsed_s, ADDRESS, (name, value))
                        for name, value in messages)
    print(f"{len(changes)} pattern, {len(schedule)} comandi OSC")
    if not args.dry_run and schedule:
        try:
            play_schedule(schedule, UdpOscClient(args.host, args.port), args.speed)
        except KeyboardInterrupt:
            print("Interrotto; Snake mantiene l'ultimo pattern.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

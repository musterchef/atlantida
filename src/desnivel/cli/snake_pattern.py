"""Configura gate e note di Snake via OSC.

Esempi:
  python -m desnivel.cli.snake_pattern --gates "1000 0100 0010 0001"
  python -m desnivel.cli.snake_pattern --gates-random 0.5 --seed 7
  python -m desnivel.cli.snake_pattern --scale minor --root 36
"""
from __future__ import annotations

import argparse
import random

from desnivel.adapters import snake
from desnivel.sinks.osc import UdpOscClient

ADDRESS = snake.ADDRESS


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="snake_pattern", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group()
    g.add_argument("--gates", help='16 valori 0/1, es. "1000 0100 0010 0001".')
    g.add_argument("--gates-random", type=float, metavar="DENSITA",
                   help="Gate casuali con probabilita' 0..1.")
    p.add_argument("--seed", type=int, help="Seme per --gates-random.")
    p.add_argument("--scale", choices=sorted(snake.SCALES), help="Scala per le 16 note.")
    p.add_argument("--root", type=int, default=36,
                   help=f"Nota di partenza {snake.NOTE_MIN}-{snake.NOTE_MAX} (default 36).")
    p.add_argument("--port", type=int, default=9001)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--dry-run", action="store_true", help="Stampa senza inviare.")
    args = p.parse_args(argv)

    messages: list[tuple[str, float]] = []
    try:
        if args.gates is not None:
            messages += snake.gate_messages(snake.parse_gate_pattern(args.gates))
        if args.gates_random is not None:
            rng = random.Random(args.seed)
            messages += snake.gate_messages(snake.random_gates(args.gates_random, rng))
        if args.scale:
            messages += snake.note_messages(snake.scale_notes(args.scale, args.root))
    except ValueError as exc:
        p.error(str(exc))
    if not messages:
        p.error("indica almeno --gates, --gates-random o --scale")

    client = None if args.dry_run else UdpOscClient(args.host, args.port)
    for name, value in messages:
        print(f"{name} = {value:g}")
        if client:
            client.send_message(ADDRESS, [name, value])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

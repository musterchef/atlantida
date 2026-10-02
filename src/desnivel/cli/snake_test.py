"""Invia un valore a un parametro di Snake via OSC (prova di trasporto)."""
from __future__ import annotations

import argparse

from desnivel.sinks.osc import UdpOscClient

ADDRESS = "/desnivel/v1/control/snake/set"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="snake_test",
        description="Imposta un parametro di Snake per nome, es. Note_03, Gate_05, Velocity_01.",
    )
    parser.add_argument("--param", required=True, help="Nome del parametro Snake.")
    parser.add_argument("--value", required=True, type=float, help="Valore da inviare.")
    parser.add_argument("--port", type=int, default=9001, help="Porta del server OSC.")
    parser.add_argument("--host", default="127.0.0.1", help="Host del server OSC.")
    args = parser.parse_args(argv)

    client = UdpOscClient(args.host, args.port)
    client.send_message(ADDRESS, [args.param, args.value])
    print(f"[snake_test] {args.param} = {args.value} -> {args.host}:{args.port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

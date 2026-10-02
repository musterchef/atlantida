"""Test snake metrics streaming via OSC."""
from __future__ import annotations

import argparse

from desnivel.sinks.osc import UdpOscClient

ADDRESS = "/desnivel/v1/control/snake/note_01"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="snake_test",
        description="Test snake metrics streaming via OSC.",
    )
    parser.add_argument("--value", required=True, type=float, help="Valore da inviare.")
    parser.add_argument("--port", type=int, default=9001, help="Porta del server OSC.")
    parser.add_argument("--host", default="127.0.0.1", help="Host del server OSC.")

    args = parser.parse_args(argv)

    client = UdpOscClient(args.host, args.port)
    client.send_message(ADDRESS, args.value)
    print(f"[snake_test] inviato {args.value} a {ADDRESS} su {args.host}:{args.port}")
    print("[snake_test] fine.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
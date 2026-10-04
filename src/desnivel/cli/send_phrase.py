"""Invia una frase completa al player M4L; non scandisce le note."""
import argparse
import json
from pathlib import Path

from desnivel.phrases import Phrase
from desnivel.adapters.phrase_player import encode
from desnivel.sinks.osc import UdpOscClient


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phrase', type=Path, required=True)
    p.add_argument('--voice', required=True)
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', type=int, default=9002)
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args(argv)
    try:
        if not 1 <= args.port <= 65535:
            raise ValueError('porta fuori da 1–65535')
        phrase = Phrase.from_dict(json.loads(args.phrase.read_text()))
        address, payload = encode(phrase, args.voice)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        p.error(str(exc))
    print(address, payload)
    if not args.dry_run:
        UdpOscClient(args.host, args.port).send_message(address, payload)
        print('Inviata; verificare ricezione nel player.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

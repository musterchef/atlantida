"""Genera una frase di basso da una melodia o da uno stato Snake esplicito."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

from desnivel.music.bass.generator import generate_bass
from desnivel.cli.bass_options import add_bass_options, bass_settings
from desnivel.music.phrases import Phrase
from desnivel.adapters.snake_sequence import SnakeState, predict


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--melody', type=Path)
    source.add_argument('--snake-state', type=Path)
    parser.add_argument('--beats', type=float, help='Finestra della previsione Snake, in semiminime.')
    parser.add_argument('--output', type=Path, required=True)
    add_bass_options(parser)
    parser.add_argument('--previous-pitch', type=int)
    args = parser.parse_args(argv)
    if args.snake_state and args.beats is None:
        parser.error('--snake-state richiede --beats')
    if args.melody and args.beats is not None:
        parser.error('--beats si usa solo con --snake-state')
    try:
        data = json.loads((args.melody or args.snake_state).read_text())
        melody = Phrase.from_dict(data) if args.melody else predict(SnakeState.from_dict(data), args.beats)
        settings = bass_settings(args)
        bass = generate_bass(melody, settings, args.previous_pitch)
        # Non sovrascrivere frasi o sorgenti già presenti.
        with args.output.open('x') as stream:
            json.dump(asdict(bass), stream, indent=2)
            stream.write('\n')
    except (ValueError, TypeError, KeyError, OSError) as exc:
        parser.error(str(exc))
    print(f'{len(bass.notes)} note, {bass.length_beats:g} beat → {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

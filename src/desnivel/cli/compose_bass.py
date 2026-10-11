"""Genera una frase di basso da una melodia o da uno stato Snake esplicito."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

from desnivel.bass import BassSettings, generate_bass
from desnivel.phrases import Phrase
from desnivel.adapters.snake_sequence import SnakeState, predict


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--melody', type=Path)
    source.add_argument('--snake-state', type=Path)
    parser.add_argument('--beats', type=float, help='Finestra della previsione Snake, in semiminime.')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--lowest', type=int, default=28)
    parser.add_argument('--highest', type=int, default=47)
    parser.add_argument('--min-spacing', type=float, default=1)
    parser.add_argument('--articulation', type=float, default=0.9)
    parser.add_argument('--velocity-ratio', type=float, default=0.9)
    parser.add_argument('--previous-pitch', type=int)
    parser.add_argument('--strategy', choices=['responsive','follow'], default='responsive')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--variation-period', type=int, default=4)
    parser.add_argument('--max-hold', type=float, default=2)
    parser.add_argument('--grid', type=float, default=.5)
    args = parser.parse_args(argv)
    if args.snake_state and args.beats is None:
        parser.error('--snake-state richiede --beats')
    if args.melody and args.beats is not None:
        parser.error('--beats si usa solo con --snake-state')
    try:
        data = json.loads((args.melody or args.snake_state).read_text())
        melody = Phrase.from_dict(data) if args.melody else predict(SnakeState.from_dict(data), args.beats)
        settings = BassSettings(args.lowest, args.highest, args.min_spacing,
                                args.articulation, args.velocity_ratio, args.strategy,args.seed,
                                args.variation_period,args.max_hold,args.grid)
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

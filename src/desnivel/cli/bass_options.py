"""Opzioni musicali comuni alla composizione offline e al basso live."""
from dataclasses import fields

from desnivel.bass import BassSettings, PRESETS


def add_bass_options(parser):
    parser.add_argument('--preset', '--strategy', dest='strategy', choices=tuple(PRESETS),
                        default='responsive', help='Valori iniziali; --strategy è un alias compatibile.')
    parser.add_argument('--lowest', type=int, default=28)
    parser.add_argument('--highest', type=int, default=47)
    parser.add_argument('--min-spacing', type=float, help='Distanza minima fra attacchi, in beat.')
    parser.add_argument('--articulation', type=float, help='Frazione della durata disponibile, in (0, 1].')
    parser.add_argument('--velocity-ratio', type=float, default=.9)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--variation-period', type=int, default=4, help='Frasi fra gli appoggi di chiusura.')
    parser.add_argument('--max-hold', type=float, default=2)
    parser.add_argument('--grid', type=float, default=.5)
    parser.add_argument('--density', type=float, help='Attacchi desiderati per beat; 0 produce silenzio.')
    for name, help_text in (
        ('syncopation', 'Preferenza per i levare.'),
        ('rhythm-follow', 'Legame con gli attacchi della melodia.'),
        ('melody-follow', 'Legame con le altezze locali della melodia.'),
        ('mobility', 'Propensione a muoversi nel registro e rispondere più in alto.'),
        ('variation', 'Ampiezza delle variazioni fra frasi.'),
    ):
        parser.add_argument('--' + name, type=float, help=help_text + ' Intervallo [0, 1].')


def bass_settings(args):
    return BassSettings(**{field.name: getattr(args, field.name) for field in fields(BassSettings)})

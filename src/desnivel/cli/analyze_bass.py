"""Su richiesta, analizza una tappa e genera automaticamente un assetto basso."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import shlex

from desnivel.bass_analysis import recommend_bass
from desnivel.journey_music import compose
from desnivel.loader import load_track
from desnivel.trip_metrics import build_metric_samples


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpx', type=Path, required=True)
    parser.add_argument('--stage-music', type=Path, required=True)
    parser.add_argument('--preset', type=Path, default=Path('presets/misto.json'),
                        help='Interpretazione del viaggio usata anche nel replay.')
    args = parser.parse_args(argv)
    try:
        samples = build_metric_samples(load_track(args.gpx))
        changes = compose(samples, json.loads(args.stage_music.read_text()),
                          json.loads(args.preset.read_text()))
        recommendation = recommend_bass(changes, max(s.elapsed_s for s in samples))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        parser.error(str(exc))
    print(f'Tappa: {args.gpx.name}; interpretazione: {args.preset.name}')
    print(f'Analizzati {recommendation.analyzed_seconds / 60:.1f} minuti dal primo pattern; '
          f'gate aperti medi {recommendation.mean_gate_fraction:.1%}, '
          f'deviazione {recommendation.gate_deviation:.1%}.')
    print('Più gate melodici → meno attacchi, meno levare e note più corte nel basso.\n'
          'Più variabilità dei gate → più variazione nelle scelte del basso.\n'
          'Registro e mobilità restano quelli prudenti di responsive: '
          'clock e configurazione Live non sono noti.\n'
          'Suggerimento generato automaticamente; nessun comando inviato a Live.\n'
          'Esegui il comando seguente per provarlo.\n')
    command = ['./comandi/07 - Basso e acquisizione.command']
    for name, value in asdict(recommendation.settings).items():
        option = 'preset' if name == 'strategy' else name.replace('_', '-')
        command.extend(['--' + option, str(value)])
    print(shlex.join(command))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

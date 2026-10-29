"""Scarica una copia locale dei dati Strava per il confronto con un GPX."""
import argparse
from datetime import datetime, timezone
from getpass import getpass
import hashlib
import json
from pathlib import Path

import numpy as np

from desnivel.cli._strava_auth import authorize
from desnivel.trip.loader._parse import parse_gpx_points
from desnivel.trip.strava import download_activity, list_activities


def overlapping_activities(activities, start, end):
    """Conserva i candidati temporalmente sovrapposti al GPX, senza scegliere."""
    return [activity for activity in activities
            if (datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00')).timestamp() <= end
                and datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00')).timestamp()
                + activity['elapsed_time'] >= start)]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpx', required=True, type=Path)
    parser.add_argument('--activity-id', type=int, help='ID numerico Strava; senza questo argomento mostra i candidati.')
    parser.add_argument('--output', type=Path, help='Snapshot JSON; predefinito output/strava/<nome GPX>.json.')
    args = parser.parse_args(argv)
    output = args.output or Path('output/strava')/args.gpx.with_suffix('.json').name
    if output.resolve() == args.gpx.resolve():
        parser.error('la destinazione deve essere diversa dal GPX')
    if output.exists():
        parser.error(f'destinazione già presente: {output}; scegliere un nuovo --output')
    if args.activity_id is not None and args.activity_id <= 0:
        parser.error('--activity-id deve essere positivo')
    try:
        raw = parse_gpx_points(args.gpx)
        times = raw['t_unix'][np.isfinite(raw['t_unix'])]
        if not len(times):
            raise ValueError('il GPX non contiene orari utilizzabili per il confronto')
        start, end = float(times.min()), float(times.max())
        print('Prerequisito: applicazione API Strava registrata; la creazione richiede un abbonamento Strava attivo.')
        print('Configurazione app: https://www.strava.com/settings/api · Authorization Callback Domain: 127.0.0.1')
        client_id = input('Client ID: ').strip()
        if not client_id.isdecimal() or int(client_id) <= 0:
            raise ValueError('Client ID numerico positivo richiesto')
        secret = getpass('Client Secret (nascosto, non salvato): ').strip()
        if not secret:
            raise ValueError('Client Secret richiesto')
        token = authorize(client_id, secret)
        activity_id = args.activity_id
        if activity_id is None:
            candidates = overlapping_activities(list_activities(token, start-86400, end+86400), start, end)
            if not candidates:
                raise ValueError('nessuna attività sovrapposta agli orari del GPX')
            for activity in candidates:
                print(f"{activity['id']} · {activity['start_date']} · {activity['name']}")
            activity_id = int(input('ID dell’attività da confrontare: ').strip())
            if activity_id not in {activity['id'] for activity in candidates}:
                raise ValueError('scegliere un ID fra i candidati mostrati')
        snapshot = download_activity(token, activity_id)
        if not overlapping_activities([snapshot['activity']], start, end):
            raise ValueError('l’attività scelta non si sovrappone agli orari del GPX')
        snapshot.update(version=1, fetched_at=datetime.now(timezone.utc).isoformat(),
                        source_gpx={'path': str(args.gpx), 'sha256': hashlib.sha256(args.gpx.read_bytes()).hexdigest()})
        payload = json.dumps(snapshot, ensure_ascii=False, allow_nan=False, indent=2)+'\n'
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('x', encoding='utf-8') as handle:
            handle.write(payload)
    except (ValueError, KeyError, TypeError, OSError, EOFError) as error:
        parser.error(str(error))
    print(f'Dati salvati: {output.resolve()}')
    print(f"Moving Time Strava: {snapshot['activity']['moving_time']} s; campioni: {len(snapshot['streams']['time']['data'])}")
    print('Credenziali non salvate. GPX e selezione del viaggio invariati.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

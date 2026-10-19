"""Analizza le zone del percorso senza generare o inviare musica."""
import argparse
import json
from pathlib import Path

from desnivel.trip.analysis import analyze_track
from desnivel.trip.loader import load_track
from desnivel.trip.sections import group_zones
from desnivel.reports.trip import render_trip_report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpx', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--grouping', type=Path, help='Famiglie JSON per raggruppare le zone in macrosezioni.')
    parser.add_argument('--output', type=Path, help='Salva zone, misure e configurazione in JSON.')
    parser.add_argument('--html', type=Path, help='Salva il report visuale HTML autonomo.')
    args = parser.parse_args(argv)
    if args.output and args.html and args.output.resolve() == args.html.resolve():
        parser.error('JSON e HTML richiedono percorsi distinti')
    try:
        result = analyze_track(load_track(args.gpx), json.loads(args.config.read_text()))
        if args.grouping:
            result['grouping'] = group_zones(result, json.loads(args.grouping.read_text()))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2)+'\n', encoding='utf-8')
        if args.html:
            args.html.parent.mkdir(parents=True, exist_ok=True)
            args.html.write_text(render_trip_report(result), encoding='utf-8')
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.error(str(error))
    print(f"{result['stage']} | {result['total_distance_m']/1000:.2f} km | {len(result['zones'])} zone")
    print('Da km   A km    Zona                 Pendenza media   Dislivello netto   Concordanza')
    for zone in result['zones']:
        print(f"{zone['start_distance_m']/1000:6.2f}  {zone['end_distance_m']/1000:6.2f}  "
              f"{zone['kind']:20} {zone['mean_slope_ratio']:+8.1%}         {zone['elevation_delta_m']:+7.0f} m"
              f"          {zone['matching_distance_ratio']:5.0%}")
    print('Concordanza: quota di distanza con classificazione locale uguale alla zona confermata.')
    if 'grouping' in result:
        sections = result['grouping']['sections']
        print(f'\nMacrosezioni: {len(sections)} (zone originali conservate)')
        print('Da km   A km    Famiglia             Zone incluse')
        for section in sections:
            print(f"{section['start_distance_m']/1000:6.2f}  {section['end_distance_m']/1000:6.2f}  "
                  f"{section['kind']:20} " + ', '.join(str(i+1) for i in section['zone_indices']))
    if args.output:
        print(f'Analisi completa: {args.output}')
    if args.html:
        print(f'Report visuale: {args.html.resolve()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Analizza le zone del percorso senza generare o inviare musica."""
import argparse
import json
from pathlib import Path

import numpy as np

from desnivel.trip.analysis import analyze_track
from desnivel.trip.loader import load_track
from desnivel.trip.sections import group_zones
from desnivel.reports.trip import render_trip_report
from desnivel.music.timeline import allocate_timeline, TimelineManager


def _linear_spans(track, sections, total_beats):
    """Proietta i tempi del Track sullo stesso budget dell'anteprima musicale."""
    if track.duration_s <= 0:
        raise ValueError('durata del percorso positiva richiesta per il confronto lineare')
    boundaries = [sections[0]['start_distance_m']] + [s['end_distance_m'] for s in sections]
    times = np.interp(np.asarray(boundaries)+track.samples['cum_dist_m'][0],
                      track.samples['cum_dist_m'], track.t)
    # Include la sosta iniziale; le soste sugli altri confini restano nella
    # sezione uscente (interpola usando l'ultimo tempo a pari distanza).
    times[0], times[-1] = track.t[0], track.t[-1]
    beats = ((times-track.t[0])/track.duration_s*total_beats).tolist()
    return [{'source_index': index, 'start_beat': start, 'end_beat': end,
             'duration_beats': end-start} for index, (start, end) in enumerate(zip(beats, beats[1:]))]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpx', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--grouping', type=Path, help='Famiglie JSON per raggruppare le zone in macrosezioni.')
    parser.add_argument('--timeline-session', type=Path,
                        help='Sessione JSON da cui leggere window_beats e timeline per l’anteprima musicale.')
    parser.add_argument('--output', type=Path, help='Salva zone, misure e configurazione in JSON.')
    parser.add_argument('--html', type=Path, help='Salva il report visuale HTML autonomo.')
    args = parser.parse_args(argv)
    if args.timeline_session and not args.grouping:
        parser.error('--timeline-session richiede --grouping')
    if args.output and args.html and args.output.resolve() == args.html.resolve():
        parser.error('JSON e HTML richiedono percorsi distinti')
    try:
        track = load_track(args.gpx)
        result = analyze_track(track, json.loads(args.config.read_text()))
        if args.grouping:
            result['grouping'] = group_zones(result, json.loads(args.grouping.read_text()))
        if args.timeline_session:
            session = json.loads(args.timeline_session.read_text(encoding='utf-8'))
            settings = session['timeline']
            if not isinstance(settings, dict) or set(settings) != {'target_beats', 'min_windows', 'distance_exponent'}:
                raise ValueError('timeline richiede target_beats, min_windows e distance_exponent')
            sections = result['grouping']['sections']
            timeline = allocate_timeline([s['end_distance_m']-s['start_distance_m'] for s in sections],
                                         window_beats=session['window_beats'], **settings)
            result['timeline'] = {**timeline.to_dict(), 'position': TimelineManager(timeline).snapshot(),
                                  'linear_reference': _linear_spans(track, sections, timeline.total_beats)}
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
    if 'timeline' in result:
        t = result['timeline']
        print(f"Timeline: {t['requested_beats']:g} beat richiesti; {t['total_beats']:g} effettivi; {t['total_windows']} finestre")
        for adjustment in t['adjustments']:
            reason = 'minimi garantiti' if adjustment['code'] == 'minimum_extension' else 'quantizzazione alle finestre'
            print(f"Avviso timeline: {reason}: {adjustment['from_beats']:g} → {adjustment['to_beats']:g} beat")
    if args.html:
        print(f'Report visuale: {args.html.resolve()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

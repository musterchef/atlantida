"""Genera i report delle tappe GPX e una pagina per scegliere quale consultare."""
import argparse
import json
from pathlib import Path

from desnivel.cli.analyze_trip import analyze_trip
from desnivel.reports.trip import render_trip_report, render_trip_index


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gpx-dir', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--grouping', type=Path)
    parser.add_argument('--pause-context', nargs=2, action='append', metavar=('FLANK', 'MIDDLE'))
    parser.add_argument('--timeline-session', type=Path)
    parser.add_argument('--output-dir', type=Path, default=Path('output/tappe'))
    args = parser.parse_args(argv)
    if (args.pause_context or args.timeline_session) and not args.grouping:
        parser.error('--pause-context e --timeline-session richiedono --grouping')
    try:
        sources = sorted((p for p in args.gpx_dir.iterdir() if p.is_file() and p.suffix.lower() == '.gpx'),
                         key=lambda p: p.name.casefold())
        if not sources:
            raise ValueError(f'nessun file GPX in {args.gpx_dir}')
        reports = []
        for source in sources:
            try:
                result = analyze_trip(source, args.config, grouping=args.grouping,
                                      pause_context=args.pause_context, timeline_session=args.timeline_session)
            except (ValueError, KeyError, TypeError, OSError) as error:
                raise ValueError(f'{source.name}: {error}') from error
            reports.append((source, result))
        args.output_dir.mkdir(parents=True, exist_ok=True)
        entries = []
        for source, result in reports:
            filename = f'report-{source.stem}.html'
            (args.output_dir/filename).write_text(render_trip_report(result), encoding='utf-8')
            (args.output_dir/f'report-{source.stem}.json').write_text(
                json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2)+'\n', encoding='utf-8')
            label = source.stem.replace('_', ' ')
            entry = {'label': label, 'filename': filename, 'distance_m': result['total_distance_m']}
            if 'timeline' in result:
                entry['total_beats'] = result['timeline']['total_beats']
            entries.append(entry)
            print(f"{label}: {result['total_distance_m']/1000:.2f} km")
        index = args.output_dir/'index.html'
        index.write_text(render_trip_index(entries), encoding='utf-8')
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.error(str(error))
    print(f'{len(entries)} tappe. Selezione: {index.resolve()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

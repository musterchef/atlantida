"""Report HTML autonomo del risultato di analyze_track."""
import json
from datetime import datetime
from html import escape
from importlib.resources import files
from urllib.parse import quote
from zoneinfo import ZoneInfo


def render_trip_index(entries):
    """Indice locale: selettore e report individuali, senza ricalcolare i dati."""
    if not entries:
        raise ValueError('almeno una tappa richiesta per l’indice')
    options, links = [], []
    for entry in entries:
        href = escape(quote(entry['filename'], safe=''), quote=True)
        text = f"{entry['label']} · {entry['distance_m']/1000:.2f} km"
        if entry.get('total_beats') is not None:
            text += f" · {entry['total_beats']:g} beat"
        label = escape(text)
        options.append(f'<option value="{href}">{label}</option>')
        links.append(f'<li><a href="{href}">{label}</a></li>')
    assets = files('desnivel.reports')
    return (assets.joinpath('trip_index.html').read_text(encoding='utf-8')
            .replace('/* INDEX_SCRIPT */', assets.joinpath('trip_index.js').read_text(encoding='utf-8'))
            .replace('REPORT_OPTIONS', ''.join(options))
            .replace('REPORT_LINKS', ''.join(links))
            .replace('FIRST_REPORT', escape(quote(entries[0]['filename'], safe=''), quote=True)))


def render_trip_report(analysis: dict) -> str:
    """Incorpora dati e risorse locali; non ricalcola o classifica il percorso."""
    if analysis.get('version') != 1 or not analysis.get('profile'):
        raise ValueError('analisi versione 1 con profilo altimetrico richiesta per il report')
    assets = files('desnivel.reports')
    # I dati restano testo JSON anche quando nomi o percorsi contengono markup.
    payload = json.dumps(analysis, ensure_ascii=False, allow_nan=False)
    for character, escaped in (('&', '\\u0026'), ('<', '\\u003c'), ('>', '\\u003e'),
                               ('\u2028', '\\u2028'), ('\u2029', '\\u2029')):
        payload = payload.replace(character, escaped)
    template = assets.joinpath('trip.html').read_text(encoding='utf-8')
    return (template.replace('/* REPORT_STYLE */', assets.joinpath('trip.css').read_text(encoding='utf-8'))
            .replace('/* REPORT_SCRIPT */', assets.joinpath('trip.js').read_text(encoding='utf-8'))
            .replace('/* QUALITY_SCRIPT */', assets.joinpath('trip_quality.js').read_text(encoding='utf-8'))
            .replace('REPORT_DATA', payload))


def render_source_review(entries):
    """Elenco delle segnalazioni già calcolate, con riferimenti originali e orari italiani."""
    if not entries:
        raise ValueError('almeno una tappa richiesta per la revisione')
    labels = {'speed_limit': 'velocità oltre il limite', 'moving_sampling_gap': 'intervallo senza campioni con spostamento',
              'resume_after_stationary_coordinates': 'spostamento dopo coordinate quasi ferme',
              'invalid_coordinates': 'coordinate non valide', 'missing_time': 'orari mancanti',
              'non_increasing_time': 'orari non crescenti', 'segment_boundary': 'confine di segmento',
              'skipped_point': 'punti intermedi mancanti'}
    def time(value):
        return datetime.fromisoformat(value).astimezone(ZoneInfo('Europe/Rome')).strftime('%d/%m/%Y %H:%M:%S') if value else 'non disponibile'
    def number(value, digits=1):
        return f'{value:.{digits}f}'.replace('.', ',') if value is not None else '—'
    def location(point):
        if point['lat'] is None or point['lon'] is None:
            return 'coordinate non disponibili'
        coords = f'{point["lat"]:.6f},{point["lon"]:.6f}'
        return f'<a href="https://www.google.com/maps?q={coords}" target="_blank" rel="noopener">{coords}</a>'
    def ref(point):
        return f'punto {point["source_index"]} · {time(point["time_utc"])} · {location(point)}'
    counts, stages = [], []
    total = 0
    for entry in entries:
        quality, stage = entry['source_quality'], entry['stage']
        segments = quality['review_segments']
        total += len(segments)
        heading = escape(entry['label'])
        counts.append(f'<tr><td><a href="#{escape(stage, quote=True)}">{heading}</a></td><td>{len(segments)}</td></tr>')
        rows = []
        removed = {point for item in entry['source_filter']['reconnections'] for point in item['removed_source_indices']}
        unresolved = {(item['start_source_index'], item['end_source_index']) for item in entry['source_filter']['unresolved_intervals']}
        for item in segments:
            review_id = f'{stage}:{item["id"]}'
            flags = ', '.join(labels[name] for name in item['reasons'])
            states = []
            if any(edge['start_source_index'] in removed or edge['end_source_index'] in removed for edge in item['flagged_intervals']):
                states.append('include punti già esclusi dal filtro')
            if any((edge['start_source_index'], edge['end_source_index']) in unresolved for edge in item['flagged_intervals']):
                states.append('include misure di movimento non disponibili')
            if not states:
                states.append('segnalazione di revisione; nessuna esclusione aggiuntiva')
            start, end = item['start'], item['end']
            rows.append(f'''<details id="{escape(review_id, quote=True)}">
<summary><strong>{escape(review_id)}</strong> · {time(start['time_utc'])} → {time(end['time_utc'])}
· km sorgente {number(start['source_distance_m']/1000, 3)}–{number(end['source_distance_m']/1000, 3)}
· massimo {number(item['peak_speed_kmh'])} km/h</summary>
<p><strong>Indizi:</strong> {escape(flags)}. {item['flagged_interval_count']} intervalli segnalati.</p>
<p><strong>Inizio:</strong> {ref(start)}<br><strong>Fine:</strong> {ref(end)}</p>
<p><strong>Picco:</strong> {ref(item['peak_start'])} → punto {item['peak_end']['source_index']}.</p>
<p><strong>Contesto da confrontare:</strong><br>{ref(item['context_start'])}<br>{ref(item['context_end'])}.</p>
<p><strong>Trattamento attuale:</strong> {escape('; '.join(states))}.</p>
<p>La tua annotazione: <code>{escape(review_id)}: …</code></p></details>''')
        link = escape(quote(entry['filename'], safe=''), quote=True)
        stages.append(f'<section id="{escape(stage, quote=True)}"><h2>{heading}</h2>'
                      f'<p><a href="{link}">Apri il report completo della tappa</a></p>'
                      + (''.join(rows) if rows else '<p>Nessun segmento segnalato dai criteri di questa revisione.</p>') + '</section>')
    settings = entries[0]['source_quality']['review_settings']
    criteria = (f'Velocità oltre {number(settings["max_speed_kmh"])} km/h; intervalli oltre '
                f'{number(settings["sampling_gap_s"], 0)} s con più di {number(settings["gap_distance_m"], 0)} m fra gli estremi; '
                f'spostamenti oltre {number(settings["resume_distance_m"], 0)} m preceduti da almeno '
                f'{number(settings["stationary_duration_s"], 0)} s di coordinate entro '
                f'{number(settings["stationary_radius_m"], 0)} m. Si segnalano anche dati mancanti o strutturalmente discontinui. '
                f'Gli indizi distanti al massimo {number(settings["group_gap_s"], 0)} s nello stesso segmento sono raggruppati. '
                f'Il contesto mostra fino a {number(settings["context_s"], 0)} s prima e dopo; '
                'con orari non utilizzabili si mostrano invece punti adiacenti.')
    assets = files('desnivel.reports')
    return (assets.joinpath('source_review.html').read_text(encoding='utf-8')
            .replace('REVIEW_TOTAL', str(total)).replace('REVIEW_CRITERIA', escape(criteria))
            .replace('REVIEW_COUNTS', ''.join(counts)).replace('REVIEW_STAGES', ''.join(stages)))

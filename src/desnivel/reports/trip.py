"""Report HTML autonomo del risultato di analyze_track."""
import json
from html import escape
from importlib.resources import files
from urllib.parse import quote


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
            .replace('REPORT_DATA', payload))

"""Report HTML autonomo del risultato di analyze_track."""
import json
from importlib.resources import files


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

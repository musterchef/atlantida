"""Report autonomo della concordanza delle pause GPX con i timer FIT."""
from datetime import datetime
from html import escape
import json
from zoneinfo import ZoneInfo


def render_pause_validation(result):
    def clock(value):
        return datetime.fromtimestamp(value, ZoneInfo('Europe/Rome')).strftime('%d/%m %H:%M:%S')

    def number(value):
        return f'{value:g}'

    summary = result['summary']
    previous = result.get('baseline_summary')
    rows, details = [], []
    max_error = max(s['metrics']['extra_pause_s']+s['metrics']['missed_pause_s'] for s in result['stages'])
    if previous:
        max_error = max(max_error, max(s['baseline_metrics']['extra_pause_s']+s['baseline_metrics']['missed_pause_s'] for s in result['stages']))
    for stage in result['stages']:
        metrics = stage['metrics']
        label = escape(stage['stage'])
        bars = []
        for title, data in ([('Prima', stage['baseline_metrics'])] if previous else [])+[('Ora', metrics)]:
            extra = data['extra_pause_s']/max(max_error, 1)*100
            missed = data['missed_pause_s']/max(max_error, 1)*100
            bars.append(f'<div class="bar"><span>{title}</span><div class="track"><i style="width:{extra:.3f}%;background:#af422d"></i>'
                        f'<i style="width:{missed:.3f}%;background:#23758b"></i></div></div>')
        old = stage.get('baseline_metrics')
        old_cells = (f'<td>{number(old["extra_pause_s"])}</td><td>{number(old["missed_pause_s"])}</td>') if old else ''
        rows.append(f'<tr><th><a href="#{label}">{label}</a></th>{old_cells}'
                    f'<td>{number(metrics["extra_pause_s"])}</td><td>{number(metrics["missed_pause_s"])}</td>'
                    f'<td>{metrics["compared_s"]/3600:.2f} h</td><td class="bars">{"".join(bars)}</td></tr>')
        differences = ''.join(f'<tr><td>{clock(d["start_unix"])}</td><td>{clock(d["end_unix"])}</td>'
                              f'<td>{number(d["duration_s"])} s</td><td>{"Conservato con timer fermo" if d["kind"] == "missed_pause" else "Escluso con timer attivo"}</td>'
                              f'<td>{d["start_source_index"]}–{d["end_source_index"]}</td></tr>'
                              for d in stage['differences'])
        inference = stage['pause_inference']
        details.append(f'<section id="{label}"><h2>{label}</h2><p>Cadenza stimata: {inference["typical_sample_interval_s"]} s; '
                       f'soglia degli intervalli radi: {inference["pause_gap_threshold_s"]} s. '
                       f'{stage["shared_timestamps"]} timestamp comuni alle due sorgenti.</p>'
                       f'<p>GPX: <code>{escape(stage["gpx"])}</code><br>FIT: <code>{escape(stage["fit"])}</code>.</p>'
                       f'<p>{number(metrics["not_compared_s"])} s fuori dal confronto: lacune, misure non valide, '
                       'limiti della copertura o intervalli misti ai confini degli eventi.</p>'
                       '<details><summary>Intervalli discordanti</summary><div class="scroll"><table><tr><th>Da</th><th>A</th><th>Durata</th><th>Differenza</th><th>Punti GPX</th></tr>'
                       +differences+'</table></div></details></section>')
    before = (f'<p>Confronto precedente: <strong>{number(previous["extra_pause_s"])} s</strong> esclusi con timer attivo; '
              f'<strong>{number(previous["missed_pause_s"])} s</strong> conservati con timer fermo.</p>') if previous else ''
    headers = '<th>Esclusi prima (s)</th><th>Conservati prima (s)</th>' if previous else ''
    missing = ', '.join(escape(s) for s in result['without_fit']) or 'nessuna'
    config = escape(json.dumps(result['config'], ensure_ascii=False, indent=2))
    return f'''<!doctype html><html lang="it"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Desnivel · Validazione delle pause GPX / FIT</title><style>
body{{font:16px/1.55 system-ui,sans-serif;background:#f3f6f5;color:#19343b;max-width:1200px;margin:auto;padding:24px}}
section{{background:white;border:1px solid #d2dfdb;border-radius:10px;padding:22px;margin:20px 0}}h1,h2{{line-height:1.2}}
table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}td,th{{padding:9px;text-align:left;border-bottom:1px solid #dce5e2}}
.scroll{{overflow:auto}}.bars{{width:260px;min-width:200px}}.bar{{height:19px;display:flex;align-items:center;margin:3px 0}}
.bar span{{flex:0 0 42px;font-size:12px}}.track{{display:flex;flex:1;min-width:0;height:12px}}.bar i{{height:12px;display:inline-block;flex-shrink:0}}code,pre{{overflow-wrap:anywhere;white-space:pre-wrap}}
</style><h1>Pause GPX confrontate con i timer FIT</h1><p>Orari Europe/Rome. Il riferimento indica timer attivo o fermo, non certifica il movimento fisico.</p>
<section><h2>Risultato su {len(result['stages'])} coppie</h2>{before}
<p>Configurazione attuale: <strong>{number(summary['extra_pause_s'])} s</strong> esclusi con timer attivo;
<strong>{number(summary['missed_pause_s'])} s</strong> conservati con timer fermo.</p>
<p>Durata confrontata: {summary['compared_s']/3600:.2f} ore. Entrano soltanto intervalli GPS validi entro
{result['config']['recording_gap_s']:g} s, interamente nello stesso stato del timer. Le lunghe lacune GPS e gli intervalli ai confini non sono valutati come errori di pausa.</p>
<p>Tappe senza riferimento FIT: <strong>{missing}</strong>. Nessuna misura di accuratezza viene attribuita a queste tappe.</p></section>
<section><h2>Per tappa</h2><p>Rosso: tempo escluso con timer attivo. Blu: tempo conservato con timer fermo. Barre sulla stessa scala.</p>
<div class="scroll"><table><tr><th>Tappa</th>{headers}<th>Esclusi ora (s)</th><th>Conservati ora (s)</th><th>Valutati</th><th>Confronto</th></tr>{''.join(rows)}</table></div></section>
{''.join(details)}<section><details><summary>Configurazione utilizzata</summary><pre>{config}</pre></details>
<p>Dati e riferimenti SHA-256: <a href="confronto-pause.json">confronto-pause.json</a>.</p></section></html>'''

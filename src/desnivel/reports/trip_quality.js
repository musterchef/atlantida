/* Ispezione dei dati sorgente: nessuna correzione o classificazione. */
(() => {
  'use strict';
  const analysis = JSON.parse(document.getElementById('analysis-data').textContent);
  const data = analysis.source_quality;
  if (!data) return;
  const byId = id => document.getElementById(id);
  const number = (v, digits = 1) => v === null || v === undefined ? '—'
    : v.toLocaleString('it-IT', {minimumFractionDigits: digits, maximumFractionDigits: digits});
  const utc = value => value ? value.replace('T', ' ').replace('+00:00', '') : '—';
  function row(parent, values) {
    const tr = document.createElement('tr');
    for (const value of values) {
      const td = document.createElement('td');
      if (value instanceof Node) td.appendChild(value); else td.textContent = value;
      tr.appendChild(td);
    }
    parent.appendChild(tr);
  }
  function svg(tag, attributes, text) {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    return node;
  }
  byId('quality-panel').hidden = false;
  const filter = analysis.source_filter;
  if (filter) {
    byId('quality-filter').hidden = false;
    byId('quality-filter-summary').textContent = `Limite: ${number(filter.max_speed_kmh)} km/h · `
      + `${filter.removed_points} punti esclusi · ${filter.reconnections.length} riconnessioni · `
      + `${filter.unresolved_intervals.length} intervalli non risolti. `
      + `Controllo locale: massimo ${filter.max_removed_points} punti, ${number(filter.max_gap_s)} secondi fra gli estremi, `
      + `riduzione della deviazione almeno ${number(filter.min_detour_ratio*100, 0)}%.`;
    for (const r of filter.reconnections) row(byId('quality-reconnections'), [r.removed_source_indices.join(', '),
      `${r.start_source_index} → ${r.end_source_index}`, `${number(r.duration_s)} s`,
      `${number(r.original_distance_m)} → ${number(r.reconnected_distance_m)} m`, `${number(r.reconnected_speed_kmh)} km/h`]);
    for (const r of filter.unresolved_intervals) row(byId('quality-unresolved'), [
      `${r.start_source_index} → ${r.end_source_index}`, `${number(r.distance_m)} m`, `${number(r.duration_s)} s`,
      number(r.speed_kmh), r.reason === 'above_speed_limit' ? 'Oltre il limite; riconnessione non verificata'
        : r.reason === 'skipped_point' ? 'Punti mancanti intermedi' : 'Coordinate, tempi o segmento non validi']);
  }
  const reasons = Object.entries(data.unavailable_reasons).filter(([, count]) => count)
    .map(([name, count]) => `${name}: ${count}`).join('; ');
  byId('quality-summary').textContent = `${number(data.points, 0)} punti · ${number(data.segments, 0)} segmenti · `
    + `${data.missing_time_points} punti senza tempo · ${data.missing_elevation_points} senza quota · `
    + `${data.invalid_coordinate_points} con coordinate non valide. `
    + `Velocità disponibile su ${number(data.available_speed_intervals, 0)} intervalli; `
    + `${data.unavailable_speed_intervals} non disponibili${reasons ? ` (${reasons})` : ''}. `
    + `Mediana: ${number(data.speed_median_kmh)} km/h; percentile 95: ${number(data.speed_p95_kmh)} km/h, senza filtri.`;

  function select(item) {
    byId('quality-selection').textContent = `Punti ${item.start.source_index} → ${item.end.source_index}: `
      + `${utc(item.start.time_utc)} → ${utc(item.end.time_utc)} UTC · `
      + `${number(item.distance_m)} m / ${number(item.duration_s)} s × 3,6 = ${number(item.speed_kmh)} km/h.`;
    const table = byId('quality-points'); table.replaceChildren();
    for (const p of item.neighbors) {
      const incoming = p.incoming_interval;
      row(table, [p.source_index, p.segment_index, utc(p.time_utc), number(p.lat, 6), number(p.lon, 6),
        number(p.elevation_m), number(incoming?.distance_m), number(incoming?.duration_s), number(incoming?.speed_kmh)]);
    }
    const map = byId('quality-map'); map.replaceChildren();
    const points = item.neighbors.filter(p => p.lat !== null && p.lon !== null);
    if (!points.length) return;
    const cosine = Math.cos(points.reduce((sum, p) => sum + p.lat, 0)/points.length*Math.PI/180);
    const projected = points.map(p => ({...p, x: (p.lon-points[0].lon)*cosine, y: p.lat-points[0].lat}));
    const xs = projected.map(p => p.x), ys = projected.map(p => p.y);
    const xmin = Math.min(...xs), xmax = Math.max(...xs), ymin = Math.min(...ys), ymax = Math.max(...ys);
    const scale = Math.min(900/Math.max(xmax-xmin, 1e-7), 230/Math.max(ymax-ymin, 1e-7));
    const x = p => 550 + (p.x-(xmin+xmax)/2)*scale;
    const y = p => 165 - (p.y-(ymin+ymax)/2)*scale;
    const defs = svg('defs', {}), marker = svg('marker', {id: 'quality-arrow', viewBox: '0 0 10 10',
      refX: 9, refY: 5, markerWidth: 6, markerHeight: 6, orient: 'auto'});
    marker.appendChild(svg('path', {d: 'M 0 0 L 10 5 L 0 10 z', fill: '#be3232'}));
    defs.appendChild(marker); map.appendChild(defs);
    map.appendChild(svg('text', {x: 20, y: 25}, 'N ↑ · coordinate originali'));
    for (let i = 1; i < projected.length; i++) {
      const a = projected[i-1], b = projected[i];
      if (a.segment_index !== b.segment_index || b.source_index !== a.source_index+1) continue;
      map.appendChild(svg('line', {x1: x(a), y1: y(a), x2: x(b), y2: y(b), stroke: '#7e8d91', 'stroke-width': 2}));
    }
    const a = projected.find(p => p.source_index === item.start.source_index);
    const b = projected.find(p => p.source_index === item.end.source_index);
    if (a && b) map.appendChild(svg('line', {x1: x(a), y1: y(a), x2: x(b), y2: y(b),
      stroke: '#be3232', 'stroke-width': 3, 'marker-end': 'url(#quality-arrow)'}));
    const positions = new Map();
    for (const p of projected) {
      const key = `${p.lat},${p.lon}`;
      if (!positions.has(key)) positions.set(key, {point: p, indices: []});
      positions.get(key).indices.push(p.source_index);
    }
    let i = 0;
    for (const {point: p, indices} of positions.values()) {
      const dot = svg('circle', {cx: x(p), cy: y(p), r: 4, fill: '#193039'});
      dot.appendChild(svg('title', {}, `Punti ${indices.join(', ')} · ${p.lat}, ${p.lon}`));
      map.appendChild(dot);
      map.appendChild(svg('text', {x: x(p)+7, y: y(p)+(i++%2 ? -10 : 19)}, indices.join('/')));
    }
  }
  data.fastest_intervals.forEach((item, index) => {
    const button = document.createElement('button'); button.type = 'button'; button.textContent = `Esamina ${index+1}`;
    button.addEventListener('click', () => select(item));
    row(byId('quality-intervals'), [button, `${item.start.source_index} → ${item.end.source_index}`,
      `${number(item.start.source_distance_m/1000, 3)} → ${number(item.end.source_distance_m/1000, 3)}`,
      `${number(item.distance_m)} m`, `${number(item.duration_s)} s`, `${number(item.speed_kmh)} km/h`, utc(item.start.time_utc)]);
  });
  if (data.fastest_intervals.length) select(data.fastest_intervals[0]);
  else byId('quality-selection').textContent = 'Nessun intervallo con velocità disponibile nei dati sorgente.';
})();

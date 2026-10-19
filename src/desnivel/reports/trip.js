/* Presentazione del risultato: nessuna classificazione o soglia musicale. */
(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('analysis-data').textContent);
  const byId = id => document.getElementById(id);
  const number = (value, digits = 2) => value.toLocaleString('it-IT', {minimumFractionDigits: digits, maximumFractionDigits: digits});
  const percent = value => number(value * 100, 1) + '%';
  const signed = (value, digits = 1) => (value > 0 ? '+' : '') + number(value, digits);
  const bands = data.config.bands;
  const colors = new Map(bands.map((band, i) => [band.name, `hsl(${Math.round(215 - i * 190 / Math.max(1, bands.length - 1))} 58% 48%)`]));
  const sections = data.grouping ? data.grouping.sections : [];
  const families = data.grouping ? Object.keys(data.grouping.config.families) : [];
  const familyColors = new Map(families.map((name, i) => [name, `hsl(${Math.round(155 + i * 220 / Math.max(1, families.length))} 45% 40%)`]));
  const total = data.total_distance_m;
  let view = [0, total], charts = [];
  const svgNode = (tag, attributes = {}, text) => {
    const node = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const add = (parent, tag, attributes, text) => {
    const node = svgNode(tag, attributes, text); parent.appendChild(node); return node;
  };
  byId('source').textContent = `${data.stage} · ${data.source_path || 'Track fornito all’analisi'}`;
  byId('distance').textContent = number(total / 1000) + ' km';
  byId('zone-count').textContent = data.zones.length;
  byId('observation').textContent = number(data.config.slope_window_m, 0) + ' m';
  byId('persistence').textContent = number(data.config.min_zone_distance_m, 0) + ' m';
  byId('config').textContent = JSON.stringify(data.config, null, 2);
  function legend(id, names, palette) {
    for (const name of names) {
      const item = document.createElement('span'), swatch = document.createElement('i');
      swatch.className = 'swatch'; swatch.style.background = palette.get(name);
      item.append(swatch, document.createTextNode(name)); byId(id).appendChild(item);
    }
  }
  legend('legend', bands.map(b => b.name), colors);
  byId('macro-status').textContent = sections.length
    ? `${sections.length} macrosezioni · ${data.zones.length} zone originali. La fascia superiore mostra il raggruppamento; il profilo mantiene le zone di dettaglio.`
    : 'Macrosezioni non richieste: questa vista mostra soltanto le zone rilevate.';
  for (const id of ['macro-panel', 'macro-legend', 'sections-chart', 'grouping-config']) byId(id).hidden = !sections.length;
  if (sections.length) {
    legend('macro-legend', families, familyColors);
    byId('families-config').textContent = JSON.stringify(data.grouping.config, null, 2);
  }

  const W = 1100, L = 74, R = 30, T = 30;
  function makeChart(id, height, values, label) {
    const svg = byId(id); svg.replaceChildren();
    const bottom = height - 48;
    let min = Math.min(...values), max = Math.max(...values);
    const padding = Math.max((max - min) * .12, id === 'slope-chart' ? .005 : 1);
    min -= padding; max += padding;
    const x = d => L + (d - view[0]) / (view[1] - view[0]) * (W - L - R);
    const y = value => bottom - (value - min) / (max - min) * (bottom - T);
    for (const zone of data.zones) {
      const start = Math.max(view[0], zone.start_distance_m), end = Math.min(view[1], zone.end_distance_m);
      if (end > start) add(svg, 'rect', {x: x(start), y: T, width: x(end) - x(start), height: bottom - T, fill: colors.get(zone.kind), opacity: .12});
    }
    for (let i = 0; i <= 4; i++) {
      const value = min + (max - min) * i / 4;
      add(svg, 'line', {x1: L, x2: W - R, y1: y(value), y2: y(value), stroke: '#dbe3df'});
      add(svg, 'text', {x: L - 10, y: y(value) + 4, 'text-anchor': 'end'}, id === 'slope-chart' ? percent(value) : number(value, 0));
    }
    for (let i = 0; i <= 6; i++) {
      const d = view[0] + (view[1] - view[0]) * i / 6;
      add(svg, 'text', {x: x(d), y: height - 16, 'text-anchor': 'middle'}, number(d / 1000));
    }
    add(svg, 'text', {x: L, y: 17}, label);
    add(svg, 'text', {x: W - R, y: height - 2, 'text-anchor': 'end'}, 'Distanza · km');
    const cursor = add(svg, 'line', {y1: T, y2: bottom, stroke: '#193039', 'stroke-dasharray': '3 3', visibility: 'hidden'});
    return {svg, x, y, bottom, cursor};
  }
  function render() {
    const profile = data.profile.filter(p => p.distance_m >= view[0] && p.distance_m <= view[1]);
    // Includi i punti adiacenti per disegnare il profilo anche a zoom stretto.
    const before = data.profile.filter(p => p.distance_m < view[0]).slice(-1);
    const after = data.profile.find(p => p.distance_m > view[1]);
    const points = [...before, ...profile, ...(after ? [after] : [])];
    const windows = data.windows.filter(w => w.end_distance_m > view[0] && w.start_distance_m < view[1]);
    const elevation = makeChart('elevation-chart', 290, points.map(p => p.elevation_m), 'Quota · m');
    const slope = makeChart('slope-chart', 240, [...windows.map(w => w.slope_ratio), 0, ...bands.slice(1).map(b => b.from_slope_ratio)], 'Pendenza osservata');
    const defs = add(elevation.svg, 'defs');
    const clip = add(defs, 'clipPath', {id: 'profile-clip'});
    add(clip, 'rect', {x: L, y: T, width: W - L - R, height: elevation.bottom - T});
    const pattern = add(defs, 'pattern', {id: 'mismatch', width: 6, height: 6, patternUnits: 'userSpaceOnUse'});
    add(pattern, 'path', {d: 'M-1 1L1 -1M0 6L6 0M5 7L7 5', stroke: '#193039', 'stroke-width': 1.3});
    add(elevation.svg, 'polyline', {points: points.map(p => `${elevation.x(p.distance_m)},${elevation.y(p.elevation_m)}`).join(' '), fill: 'none', stroke: '#193039', 'stroke-width': 2, 'clip-path': 'url(#profile-clip)'});
    for (const band of bands.slice(1)) {
      add(slope.svg, 'line', {x1: L, x2: W - R, y1: slope.y(band.from_slope_ratio), y2: slope.y(band.from_slope_ratio), stroke: colors.get(band.name), 'stroke-dasharray': '5 5'});
    }
    let path = '';
    for (const window of windows) {
      const start = Math.max(view[0], window.start_distance_m), end = Math.min(view[1], window.end_distance_m);
      path += `${path ? 'L' : 'M'}${slope.x(start)},${slope.y(window.slope_ratio)}L${slope.x(end)},${slope.y(window.slope_ratio)}`;
      add(elevation.svg, 'rect', {x: elevation.x(start), y: elevation.bottom + 5, width: elevation.x(end) - elevation.x(start), height: 8, fill: colors.get(window.observed_kind)});
      if (window.observed_kind !== data.zones[window.zone_index].kind) {
        add(elevation.svg, 'rect', {x: elevation.x(start), y: elevation.bottom + 5, width: elevation.x(end) - elevation.x(start), height: 8, fill: 'url(#mismatch)'});
      }
    }
    add(slope.svg, 'path', {d: path, fill: 'none', stroke: '#193039', 'stroke-width': 1.8});
    charts = [elevation, slope];
    if (sections.length) {
      const svg = byId('sections-chart'); svg.replaceChildren();
      add(svg, 'text', {x: L, y: 17}, 'Macrosezioni · famiglie configurate');
      for (const section of sections) {
        const start = Math.max(view[0], section.start_distance_m), end = Math.min(view[1], section.end_distance_m);
        if (end <= start) continue;
        const width = elevation.x(end) - elevation.x(start);
        const block = add(svg, 'rect', {x: elevation.x(start), y: T, width, height: 32, fill: familyColors.get(section.kind), stroke: 'white'});
        add(block, 'title', {}, `${section.index+1}. ${section.kind} · km ${number(section.start_distance_m/1000)}–${number(section.end_distance_m/1000)} · zone ${section.zone_indices.map(i => i+1).join(', ')}`);
        if (width > section.kind.length * 8 + 18) {
          add(svg, 'text', {x: elevation.x(start) + width/2, y: 51, 'text-anchor': 'middle', style: 'fill:white'}, section.kind);
        }
      }
      for (let i = 0; i <= 6; i++) {
        const d = view[0] + (view[1] - view[0]) * i/6;
        add(svg, 'text', {x: elevation.x(d), y: 87, 'text-anchor': 'middle'}, number(d/1000));
      }
      const cursor = add(svg, 'line', {y1: T, y2: 62, stroke: '#193039', 'stroke-dasharray': '3 3', visibility: 'hidden'});
      charts.push({svg, x: elevation.x, cursor});
    }
    for (const chart of charts) {
      chart.svg.appendChild(chart.cursor);
      chart.svg.onpointermove = event => {
        const box = chart.svg.getBoundingClientRect();
        const px = (event.clientX - box.left) / box.width * W;
        const d = view[0] + Math.max(0, Math.min(1, (px - L) / (W - L - R))) * (view[1] - view[0]);
        inspect(d);
      };
      chart.svg.onpointerleave = () => charts.forEach(c => c.cursor.setAttribute('visibility', 'hidden'));
    }
    byId('range-start').value = view[0] / 1000;
    byId('range-end').value = view[1] / 1000;
  }
  function inspect(distance) {
    const window = data.windows.find(w => w.end_distance_m > distance) || data.windows[data.windows.length - 1];
    const zone = data.zones[window.zone_index];
    const section = sections.find(s => s.zone_indices.includes(zone.index));
    const macro = section ? ` · macrosezione ${section.index+1}: ${section.kind}` : '';
    byId('inspection').textContent = `km ${number(distance / 1000)}${macro} · zona ${zone.index + 1}: ${zone.kind} · fascia osservata: ${window.observed_kind} · pendenza osservata ${percent(window.slope_ratio)} · quota al centro dell’intervallo ${number(window.elevation_m, 0)} m · concordanza zona ${percent(zone.matching_distance_ratio)}`;
    for (const chart of charts) {
      chart.cursor.setAttribute('x1', chart.x(distance)); chart.cursor.setAttribute('x2', chart.x(distance));
      chart.cursor.setAttribute('visibility', 'visible');
    }
  }
  function setRange(start, end) {
    const tolerance = total * Number.EPSILON * 4;
    if (!Number.isFinite(start) || !Number.isFinite(end) || start < 0 || end > total + tolerance || end <= start) {
      byId('range-error').textContent = `Indica un intervallo crescente fra 0 e ${number(total / 1000, 4)} km.`; return;
    }
    end = Math.min(end, total);
    byId('range-error').textContent = ''; view = [start, end]; render();
    inspect((start + end) / 2);
  }
  const rows = [], macroRows = [];
  function clearSelection() {
    [...rows, ...macroRows].forEach(r => r.classList.remove('selected'));
  }
  function focusRange(item) {
    const margin = (item.end_distance_m - item.start_distance_m) * .12;
    setRange(Math.max(0, item.start_distance_m - margin), Math.min(total, item.end_distance_m + margin));
    byId('profile-title').scrollIntoView({behavior: 'smooth', block: 'start'});
  }
  for (const zone of data.zones) {
    const row = document.createElement('tr'), name = document.createElement('td');
    const button = document.createElement('button'), swatch = document.createElement('i');
    swatch.className = 'swatch'; swatch.style.background = colors.get(zone.kind);
    button.append(swatch, document.createTextNode(`${zone.index + 1}. ${zone.kind}`));
    button.onclick = () => {
      clearSelection(); row.classList.add('selected'); focusRange(zone);
    };
    name.appendChild(button); row.appendChild(name);
    for (const text of [`${number(zone.start_distance_m / 1000)} → ${number(zone.end_distance_m / 1000)}`, signed(zone.mean_slope_ratio * 100) + '%', signed(zone.elevation_delta_m, 0) + ' m', percent(zone.matching_distance_ratio)]) {
      const cell = document.createElement('td'); cell.textContent = text; row.appendChild(cell);
    }
    rows.push(row); byId('zones').appendChild(row);
  }
  for (const section of sections) {
    const row = document.createElement('tr'), name = document.createElement('td');
    const button = document.createElement('button'), swatch = document.createElement('i');
    swatch.className = 'swatch'; swatch.style.background = familyColors.get(section.kind);
    button.append(swatch, document.createTextNode(`${section.index+1}. ${section.kind}`));
    button.onclick = () => {
      clearSelection(); row.classList.add('selected');
      section.zone_indices.forEach(i => rows[i].classList.add('selected'));
      focusRange(section);
    };
    name.appendChild(button); row.appendChild(name);
    for (const text of [`${number(section.start_distance_m/1000)} → ${number(section.end_distance_m/1000)}`,
      section.zone_indices.map(i => i+1).join(', '), signed(section.mean_slope_ratio*100) + '%', signed(section.elevation_delta_m, 0) + ' m']) {
      const cell = document.createElement('td'); cell.textContent = text; row.appendChild(cell);
    }
    macroRows.push(row); byId('macro-sections').appendChild(row);
  }
  byId('range-form').onsubmit = event => {
    event.preventDefault();
    setRange(byId('range-start').valueAsNumber * 1000, byId('range-end').valueAsNumber * 1000);
  };
  byId('reset').onclick = () => {clearSelection(); setRange(0, total);};
  function renderTimeline() {
    const timeline = data.timeline;
    byId('timeline-panel').hidden = !timeline;
    if (!timeline) return;
    byId('timeline-summary').textContent = `${number(timeline.requested_beats, 0)} beat richiesti → ${number(timeline.total_beats, 0)} beat effettivi · ${timeline.total_windows} finestre da ${number(timeline.window_beats)} beat · minimo ${timeline.min_windows} finestre per macrosezione · esponente ${number(timeline.distance_exponent)}`;
    const reasons = {minimum_extension: 'Estensione per garantire i minimi', window_quantization: 'Arrotondamento alle finestre'};
    byId('timeline-adjustments').textContent = timeline.adjustments.map(a => `${reasons[a.code] || a.code}: ${number(a.from_beats)} → ${number(a.to_beats)} beat`).join(' · ');
    const svg = byId('timeline-chart'), width = W-L-R;
    add(svg, 'text', {x: L, y: 18}, 'Percorso · quote di distanza');
    add(svg, 'text', {x: L, y: 83}, 'Tempo lineare GPX · stesso totale di beat');
    add(svg, 'text', {x: L, y: 148}, 'Timeline allocata · quote di beat');
    const timelineRows = [];
    for (const span of timeline.spans) {
      const section = sections[span.source_index], color = familyColors.get(section.kind);
      const distanceBar = add(svg, 'rect', {x: L+section.start_distance_m/total*width, y: 28,
        width: (section.end_distance_m-section.start_distance_m)/total*width, height: 28, fill: color, stroke: 'white'});
      add(distanceBar, 'title', {}, `${span.source_index+1}. ${section.kind} · ${number(section.end_distance_m-section.start_distance_m, 0)} m`);
      const linear = timeline.linear_reference[span.source_index];
      const linearBar = add(svg, 'rect', {x: L+linear.start_beat/timeline.total_beats*width, y: 93,
        width: linear.duration_beats/timeline.total_beats*width, height: 28, fill: color, stroke: 'white'});
      add(linearBar, 'title', {}, `${span.source_index+1}. ${section.kind} · lineare GPX ${number(linear.duration_beats)} beat`);
      const musicBar = add(svg, 'rect', {x: L+span.start_beat/timeline.total_beats*width, y: 158,
        width: span.duration_beats/timeline.total_beats*width, height: 28, fill: color, stroke: 'white'});
      add(musicBar, 'title', {}, `${span.source_index+1}. ${section.kind} · beat ${number(span.start_beat)}–${number(span.end_beat)} · ${span.window_count} finestre`);
      const row = document.createElement('tr'), name = document.createElement('td'), button = document.createElement('button');
      button.textContent = `${span.source_index+1}. ${section.kind}`;
      button.onclick = () => {
        byId('timeline-position').value = span.start_window;
        inspectTimeline(span.start_window);
        clearSelection(); macroRows[span.source_index].classList.add('selected');
        section.zone_indices.forEach(i => rows[i].classList.add('selected'));
        focusRange(section);
      };
      name.appendChild(button); row.appendChild(name);
      for (const text of [`${number(section.start_distance_m/1000)} → ${number(section.end_distance_m/1000)}`,
        String(span.window_count), `${number(span.start_beat)} → ${number(span.end_beat)}`, number(span.duration_beats), number(linear.duration_beats)]) {
        const cell = document.createElement('td'); cell.textContent = text; row.appendChild(cell);
      }
      timelineRows.push(row); byId('timeline-spans').appendChild(row);
    }
    const cursor = add(svg, 'line', {y1: 154, y2: 193, stroke: '#193039', 'stroke-width': 2});
    function inspectTimeline(index) {
      timelineRows.forEach(row => row.classList.remove('selected'));
      const beat = index*timeline.window_beats;
      cursor.setAttribute('x1', L+beat/timeline.total_beats*width);
      cursor.setAttribute('x2', L+beat/timeline.total_beats*width);
      const span = timeline.spans.find(s => index >= s.start_window && index < s.start_window+s.window_count);
      if (!span) {
        byId('timeline-inspection').textContent = `Timeline terminata · ${number(timeline.total_beats)} beat`;
        return;
      }
      timelineRows[span.source_index].classList.add('selected');
      const section = sections[span.source_index], remaining = span.start_window+span.window_count-index;
      byId('timeline-inspection').textContent = `Beat ${number(beat)} · finestra ${index+1}/${timeline.total_windows} · macrosezione ${span.source_index+1}: ${section.kind} · ${remaining} finestre rimanenti nella macrosezione`;
    }
    byId('timeline-position').max = timeline.total_windows;
    byId('timeline-position').value = timeline.position.window_index;
    byId('timeline-position').oninput = event => inspectTimeline(Number(event.target.value));
    inspectTimeline(timeline.position.window_index);
  }
  render();
  renderTimeline();
})();

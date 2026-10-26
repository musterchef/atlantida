// Controlli delle interazioni DOM con nomi di fascia arbitrari, senza browser.
const vm = require('vm'), fs = require('fs'), assert = require('assert');
class Element {
  constructor(tag = '') {this.tag = tag; this.children = []; this.attributes = {}; this.value = ''; this.textContent = ''; this.style = {}; this.classes = new Set(); this.classList = {add: x => this.classes.add(x), remove: x => this.classes.delete(x)};}
  appendChild(child) {this.children = this.children.filter(x => x !== child); this.children.push(child); return child;}
  append(...children) {children.forEach(x => this.appendChild(x));}
  replaceChildren(...children) {this.children = [...children];}
  setAttribute(key, value) {this.attributes[key] = String(value);}
  getBoundingClientRect() {return {left: 0, width: 1100};}
  scrollIntoView() {}
  get valueAsNumber() {return this.value === '' ? NaN : Number(this.value);}
}
function run(data) {
  const elements = {};
  const document = {getElementById: id => elements[id] ||= new Element(),
    createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag),
    createTextNode: text => ({textContent: text})};
  document.getElementById('analysis-data').textContent = JSON.stringify(data);
  vm.runInNewContext(fs.readFileSync('src/desnivel/reports/trip.js', 'utf8'), {document});
  return elements;
}
const data = {stage: 'test', total_distance_m: 400, config: {slope_window_m: 100, min_zone_distance_m: 100,
  bands: [{name: 'alpha', from_slope_ratio: null}, {name: 'beta', from_slope_ratio: .02}]},
  profile: [{distance_m: 0, elevation_m: 100}, {distance_m: 200, elevation_m: 100}, {distance_m: 400, elevation_m: 110}],
  zones: [{index: 0, kind: 'alpha', start_distance_m: 0, end_distance_m: 200, mean_slope_ratio: 0, elevation_delta_m: 0, matching_distance_ratio: .5},
    {index: 1, kind: 'beta', start_distance_m: 200, end_distance_m: 400, mean_slope_ratio: .05, elevation_delta_m: 10, matching_distance_ratio: 1}],
  windows: Array.from({length: 4}, (_, i) => ({start_distance_m: i * 100, end_distance_m: (i + 1) * 100,
    elevation_m: 100 + i, slope_ratio: i ? .05 : 0, observed_kind: i ? 'beta' : 'alpha', zone_index: i < 2 ? 0 : 1}))};
const e = run(data);
assert.equal(e.zones.children.length, 2);
assert.equal(e.legend.children.length, 2);
assert.equal(Number(e['range-end'].value), .4);
assert.equal(e['macro-panel'].hidden, true);
e['elevation-chart'].onpointermove({clientX: 600});
assert(e.inspection.textContent.includes('beta'));
assert(e.inspection.textContent.includes('pendenza osservata'));
const secondButton = e.zones.children[1].children[0].children[0];
secondButton.onclick();
assert(Number(e['range-start'].value) > 0);
assert(e.zones.children[1].classes.has('selected'));
e.reset.onclick(); assert.equal(Number(e['range-start'].value), 0); assert.equal(Number(e['range-end'].value), .4);
e['range-start'].value = '.3'; e['range-end'].value = '.1';
e['range-form'].onsubmit({preventDefault() {}});
assert(e['range-error'].textContent.includes('intervallo crescente'));
e['range-start'].value = '.201'; e['range-end'].value = '.202';
e['range-form'].onsubmit({preventDefault() {}}); assert.equal(e['range-error'].textContent, '');
function checkCoordinates(node) {
  for (const value of Object.values(node.attributes || {})) assert(!/NaN|Infinity/.test(value), value);
  (node.children || []).forEach(checkCoordinates);
}
checkCoordinates(e['elevation-chart']); checkCoordinates(e['slope-chart']);
// Un solo intervallo, quota costante e una sola fascia rimangono visualizzabili.
run({...data, total_distance_m: 100, config: {...data.config, bands: data.config.bands.slice(0, 1)},
  zones: [{...data.zones[0], end_distance_m: 100}], windows: data.windows.slice(0, 1),
  profile: [{distance_m: 0, elevation_m: 100}, {distance_m: 100, elevation_m: 100}]});
// Le macrosezioni arrivano dal modulo di raggruppamento, non vengono ricavate dal report.
const grouped = run({...data, grouping: {config: {families: {journey: ['alpha', 'beta']}}, sections: [
  {index: 0, kind: 'journey', start_distance_m: 0, end_distance_m: 400,
    zone_indices: [0, 1], mean_slope_ratio: .025, elevation_delta_m: 10}
]}});
assert.equal(grouped['macro-panel'].hidden, false);
assert.equal(grouped['macro-sections'].children.length, 1);
assert.equal(grouped.zones.children.length, 2);
assert.equal(grouped['macro-legend'].children.length, 1);
assert(grouped['families-config'].textContent.includes('journey'));
grouped['macro-sections'].children[0].children[0].children[0].onclick();
assert(grouped.zones.children.every(r => r.classes.has('selected')));
grouped['sections-chart'].onpointermove({clientX: 600});
assert(grouped.inspection.textContent.includes('macrosezione 1: journey'));
checkCoordinates(grouped['sections-chart']);
grouped.reset.onclick();
assert(grouped.zones.children.every(r => !r.classes.has('selected')));
assert(!grouped['macro-sections'].children[0].classes.has('selected'));
const timed = run({...data,
  grouping: {config: {families: {alpha: ['alpha'], beta: ['beta']}},
    sections: data.zones.map((zone, index) => ({...zone, zone_indices: [index]}))},
  timeline: {beats_per_km: 12, requested_beats: 32, total_beats: 32, total_windows: 8, window_beats: 4,
    min_windows: 2, distance_exponent: .5, adjustments: [], position: {window_index: 0},
    linear_reference: [{source_index: 0, start_beat: 0, end_beat: 4, duration_beats: 4},
      {source_index: 1, start_beat: 4, end_beat: 32, duration_beats: 28}],
    spans: [{source_index: 0, start_window: 0, window_count: 3, start_beat: 0, end_beat: 12, duration_beats: 12},
      {source_index: 1, start_window: 3, window_count: 5, start_beat: 12, end_beat: 32, duration_beats: 20}]}
});
assert.equal(timed['timeline-panel'].hidden, false);
assert(timed['timeline-summary'].textContent.includes('12,00 beat/km'));
assert.equal(timed['timeline-spans'].children.length, 2);
assert.equal(timed['timeline-spans'].children[0].children[5].textContent, '4,00');
assert(timed['timeline-chart'].children.some(node => node.textContent === 'Tempo lineare GPX · stesso totale di beat'));
assert(timed['timeline-inspection'].textContent.includes('macrosezione 1: alpha'));
assert(timed['timeline-duration'].textContent.includes('Totale: 0 min 16 s'));
timed['timeline-bpm'].value = '60';
timed['timeline-bpm'].oninput();
assert(timed['timeline-duration'].textContent.includes('Totale: 0 min 32 s'));
assert(timed['timeline-duration'].textContent.includes('Macrosezione 1: 0 min 12 s'));
for (const invalid of ['', '0', '-20', 'Infinity']) {
  timed['timeline-bpm'].value = invalid;
  timed['timeline-bpm'].oninput();
  assert(timed['timeline-duration'].textContent.includes('Inserisci un BPM'));
}
timed['timeline-bpm'].value = '60';
timed['timeline-bpm'].oninput();
timed['timeline-position'].oninput({target: {value: '3'}});
assert(timed['timeline-inspection'].textContent.includes('macrosezione 2: beta'));
assert(timed['timeline-inspection'].textContent.includes('5 finestre rimanenti'));
assert(timed['timeline-duration'].textContent.includes('Macrosezione 2: 0 min 20 s'));
timed['timeline-position'].oninput({target: {value: '8'}});
assert(timed['timeline-inspection'].textContent.includes('Timeline terminata'));
timed['timeline-spans'].children[1].children[0].children[0].onclick();
assert.equal(timed['timeline-position'].value, 3);
assert(timed['timeline-inspection'].textContent.includes('Beat 12'));
checkCoordinates(timed['timeline-chart']);
assert.equal(e['context-panel'].hidden, true);
const contextZones = [
  {...data.zones[0], index: 0, kind: 'up', start_distance_m: 0, end_distance_m: 100},
  {...data.zones[0], index: 1, kind: 'flat', start_distance_m: 100, end_distance_m: 300},
  {...data.zones[1], index: 2, kind: 'up', start_distance_m: 300, end_distance_m: 400}
];
const contextData = {...data, zones: contextZones,
  grouping: {config: {families: {up: ['alpha'], flat: ['beta']}},
    sections: contextZones.map(z => ({...z, zone_indices: [z.index]}))},
  section_context: [{flank_kind: 'up', middle_kind: 'flat', candidates: [
    {before_index: 0, middle_index: 1, after_index: 2,
      before_distance_m: 100, middle_distance_m: 200, after_distance_m: 100,
      reference_distance_m: 100, distance_ratio: 2}
  ]}]};
const contextView = run(contextData);
assert.equal(contextView['context-panel'].hidden, false);
assert.equal(contextView['context-sections'].children.length, 1);
assert.equal(contextView['context-sections'].children[0].children[6].textContent, '200,0%');
contextView['context-sections'].children[0].children[0].children[0].onclick();
assert(contextView['macro-sections'].children.every(row => row.classes.has('selected')));
assert(contextView.zones.children.every(row => row.classes.has('selected')));
const emptyContext = run({...contextData, section_context: [{...contextData.section_context[0], candidates: []}]});
assert.equal(emptyContext['context-sections'].children.length, 0);
assert(emptyContext['context-summary'].textContent.startsWith('0 sezioni'));
console.log('OK: report zones, macrosections, timeline, local context, selection, zoom and empty candidates');

const bothContexts = run({...contextData, section_context: [
  contextData.section_context[0],
  {...contextData.section_context[0], flank_kind: 'down'}
]});
assert.equal(bothContexts['context-sections'].children.length, 2);
assert(bothContexts['context-summary'].textContent.includes('tra due up'));
assert(bothContexts['context-summary'].textContent.includes('tra due down'));
assert.equal(bothContexts['context-sections'].children[1].children[7].textContent, 'down');

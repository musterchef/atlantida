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
console.log('OK: report zones, arbitrary bands, macrosections, selection, pointer details, zoom, reset, invalid ranges and short profiles');

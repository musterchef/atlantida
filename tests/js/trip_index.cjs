// Cambio della tappa visualizzata e del collegamento al report completo.
const vm = require('vm'), fs = require('fs'), assert = require('assert');
const elements = {
  'stage-select': {value: 'report-uno.html', selectedIndex: 0,
    options: [{textContent: 'Tappa uno'}, {textContent: 'Tappa due'}]},
  'stage-report': {setAttribute(key, value) {this[key] = value;}},
  'open-report': {setAttribute(key, value) {this[key] = value;}}
};
vm.runInNewContext(fs.readFileSync('src/desnivel/reports/trip_index.js', 'utf8'),
  {document: {getElementById: id => elements[id]}});
assert.equal(elements['stage-report'].src, 'report-uno.html');
elements['stage-select'].value = 'report-due.html';
elements['stage-select'].selectedIndex = 1;
elements['stage-select'].onchange();
assert.equal(elements['stage-report'].src, 'report-due.html');
assert.equal(elements['stage-report'].title, 'Report · Tappa due');
assert.equal(elements['open-report'].href, 'report-due.html');
console.log('OK: scelta della tappa e apertura del report completo');

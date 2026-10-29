const assert = require('node:assert/strict');
const {frameAt} = require('../../src/desnivel/viewer/position.js');

const segments = [[[0, 43, 11], [10, 43.1, 11.1]], [[10, 44, 12], [20, 44.1, 12.1]]];
assert.deepEqual(frameAt(segments, 0).position, [43, 11]);
assert.deepEqual(frameAt(segments, 5).position, [43.05, 11.05]);
// Il confine passa al tratto successivo: nessuna interpolazione attraverso il buco.
assert.deepEqual(frameAt(segments, 10).position, [44, 12]);
assert.equal(frameAt(segments, 15).completed.length, 2);
assert.deepEqual(frameAt(segments, 20).position, [44.1, 12.1]);
assert.deepEqual(frameAt(segments, 200).position, [44.1, 12.1]);
// Un arretramento ricostruisce soltanto i tratti già attraversati.
assert.equal(frameAt(segments, 5).completed.length, 1);
assert.deepEqual(frameAt([[[0, 43, 11]]], 0).position, [43, 11]);
console.log('journey_view: interpolazione e interruzioni verificate');

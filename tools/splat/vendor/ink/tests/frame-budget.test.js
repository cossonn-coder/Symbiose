const test = require('node:test');
const assert = require('node:assert/strict');
const { artScale, uploadRows } = require('../src/frame-budget.js');
const studio = require('..');

test('a native pixel budget raises the integer scale without changing a finer-grid override', () => {
  assert.equal(artScale(1280, 720, 1, 288000), 2);
  assert.equal(artScale(1920, 1080, 4, 288000), 4);
  assert.equal(artScale(1920, 1080, 1), 1);
  assert.equal(artScale(1920, 1080, 1, 1), 18);
  assert.throws(() => artScale(100, 100, 1, -1), RangeError);
  assert.ok(studio.files().some(file => file.endsWith('/src/frame-budget.js')));
});

test('dirty rows coalesce across an optional small gap and clear only after upload', () => {
  const rows = Uint8Array.from([0,1,1,0,1,0,0,1]);
  const ranges = [];
  uploadRows(rows, (first, end) => ranges.push([first, end]), 1);
  assert.deepEqual(ranges, [[1,5],[7,8]]);
  assert.ok(rows.every(row => row === 0));
  rows[0] = rows[2] = 1;
  assert.throws(() => uploadRows(rows, () => { throw new Error('upload stalled'); }), /upload stalled/);
  assert.deepEqual(Array.from(rows), [1,0,1,0,0,0,0,0]);
  ranges.length = 0;
  uploadRows(rows, (first, end) => ranges.push([first, end]));
  assert.deepEqual(ranges, [[0,1],[2,3]]);
});

test('static group culling respects stable indices, uncertainty and off-center covariance', () => {
  const { staticGroups, visibleIndices } = require('../src/frame-budget.js');
  const data = new Float32Array(64);
  data[0] = 0.9;
  data[16] = 1.62;
  data[20] = .09;
  data[32] = 2.1;
  data[48] = 5;
  const matrix = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
  const groups = staticGroups(data, 4, [[3,4]], 1);
  const indices = new Int32Array(4);
  assert.equal(visibleIndices(groups, matrix, indices, 1, 1, 0), 3);
  assert.deepEqual(Array.from(indices.slice(0, 3)), [0,1,3]);
  assert.equal(visibleIndices(groups, matrix, indices, .5, 1, 0), 2);
  data[43] = 12;
  assert.equal(visibleIndices(staticGroups(data, 4, [[3,4]], 1), matrix, indices, 1, 1, 0), 4);
  assert.throws(() => staticGroups(data, 4, [], 0), RangeError);
});

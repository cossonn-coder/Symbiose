const test = require('node:test');
const assert = require('node:assert/strict');
const {matchIntervals} = require('..').load().KIT.procedural;
const fit = (...args) => Array.from(matchIntervals(...args));

test('unrelated inserts, removals and resizing retain the original span indices', () => {
  assert.deepEqual(fit([[8,10],[2,4],[12,13]], [[1,1.5],[1.9,4.5],[8.25,9.5]]),[-1,1,0]);
  assert.deepEqual(fit([[4,8]],[[4,5],[6,8]]),[-1,0]);
  assert.deepEqual(fit([[4,5],[6,8]],[[4,8]]),[1]);
});

test('small moves can be matched in a bounded radius and a caller can reject an edge', () => {
  assert.deepEqual(fit([[1,2],[3,4]],[[2.2,2.8]],{maxShift:1.25,accept:i=>i!==0}),[1]);
  assert.deepEqual(fit([[1,2],[3,4]],[[2.2,2.8]]),[-1]);
  assert.throws(()=>fit([[1,3],[2,4]],[]),/disjoint/);
});

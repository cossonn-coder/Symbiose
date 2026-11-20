const test = require('node:test');
const assert = require('node:assert/strict');
const { traceSignedIntervals: trace } = require('..').load().KIT.procedural;

test('a signed trace keeps narrow interruptions and skips homogeneous space with a slope bound', () => {
  const field = t => Math.max(Math.abs(t - 5) - 3, .012 - Math.abs(t - 5.024));
  const options = { range: [0, 10], step: .005, tolerance: 1e-6 };
  const regular = trace(field, options);
  const adaptive = trace(field, { ...options, maxSlope: 1 });
  assert.equal(adaptive.complete, true);
  assert.deepEqual(adaptive.intervals, regular.intervals);
  assert.equal(adaptive.intervals.length, 2);
  const bounds = adaptive.intervals.flat();
  [2, 5.012, 5.036, 8].forEach((value, index) => assert(Math.abs(value - bounds[index]) < 1e-6));
  assert(adaptive.samples < regular.samples / 10);
});

test('signed tracing preserves open endpoints and reports exhausted budgets', () => {
  assert.deepEqual(trace(() => -1, { maxSlope: 0 }).intervals, [[0, 1]]);
  assert.deepEqual(trace(() => 0, { maxSlope: 0 }).intervals, []);
  const result = trace(t => 0.45 - t, { maxSlope: 1, maxSamples: 2 });
  assert.deepEqual(result, { intervals: [[.5, 1]], samples: 2, complete: false });
  assert.throws(() => trace(() => NaN), /numeric/);
  assert.throws(() => trace(t => t, { step: -.01 }), /resolution/);
});

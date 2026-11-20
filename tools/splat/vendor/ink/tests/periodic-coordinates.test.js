const test = require('node:test'), assert = require('node:assert/strict');
const { periodicCoordinates } = require('..').load().KIT.procedural;
const { wrap, delta, unwrap } = periodicCoordinates;
const near = (a, b) => assert(Math.abs(a - b) < 1e-12, `${a} != ${b}`);

test('wrapped coordinates use a half-open period and signed steps cross the seam', () => {
  assert.equal(wrap(-24, 12), 0);
  assert.equal(wrap(-5, 12), 7);
  assert.equal(wrap(2, 1), 0);
  near(delta(.03, .97), .06);
  near(delta(3.97, -4.97), -.06);
  assert.equal(delta(6, 0, 12), -6);
});

test('unwrapping puts each station in the smallest covering interval in its input order', () => {
  assert.deepEqual(unwrap([1, 11, 0, 13], 12), [13, 11, 12, 13]);
  assert.deepEqual(unwrap([3, 2, 4], 12), [3, 2, 4]);
  assert.deepEqual(unwrap([0, 6], 12), [0, 6]);
  assert.deepEqual(unwrap([]), []);
  assert.deepEqual(unwrap(new Float32Array([1, .25, .75])), [1, 1.25, .75]);
  near(wrap(unwrap([.99, .01]).reduce((sum, u) => sum + u / 2, 0)), 0);
});

test('a measured loop maps keyed span positions through unequal spans and repeated turns',()=>{
  const plan=periodicCoordinates.loop([
    {key:'a',length:2},{key:'b',length:.5},{key:'c',length:3.5}
  ]);
  assert.equal(plan.length,6);
  assert.equal(plan.station('c',.5),4.25);
  assert.deepEqual(plan.locate(plan.station('c',.5)-12),{key:'c',fraction:.5});
  assert.deepEqual(plan.locate(plan.station('a',1)),{key:'b',fraction:0});
  assert.deepEqual(plan.locate(plan.station('a',1.125)),{key:'b',fraction:.5});
  assert.deepEqual(plan.locate(18),{key:'a',fraction:0});
  assert.throws(()=>plan.station('missing',0),/known span/);
  assert.throws(()=>plan.locate(Infinity),/finite/);
  assert.throws(()=>periodicCoordinates.loop([{key:'a',length:1},{key:'a',length:1}]),/unique/);
});

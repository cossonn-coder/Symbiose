const test = require('node:test');
const assert = require('node:assert/strict');
const { layerMix } = require('..').load().KIT.procedural;

test('independent controls combine, clamp at their endpoints, and share a gain budget', () => {
  const points = [[.2, 0], [.8, 1]];
  const mix = layerMix.create([
    { id: 'base', gain: .5 },
    { id: 'upper', curves: { daylight: points, density: [[0, .2], [1, 1]] } }
  ], { budget: .75 });
  points[1][1] = 0;
  assert.deepEqual(mix.sample({ daylight: 0, density: 1 }), { base: .5, upper: 0 });
  assert.deepEqual(mix.sample({ daylight: 1, density: 1 }), { base: .25, upper: .5 });
  assert(Math.abs(mix.sample({ daylight: .5, density: .25 }).upper - .2) < 1e-12);
  assert.throws(() => mix.sample({ daylight: 1 }), /density/);
  assert.throws(() => mix.sample({ daylight: NaN, density: 1 }), /daylight/);
});

test('crossfades are bounded, time-partition independent and support different release rates', () => {
  const mix = layerMix.create([
    { id: 'sun', curves: { sun: [[0, 0], [1, 1]] }, fadeIn: .3, fadeOut: 2 },
    { id: 'moon', curves: { sun: [[0, 1], [1, 0]] }, fadeIn: .7, fadeOut: .5 }
  ], { budget: .8 });
  const one = mix.state({ sun: 1 }), many = mix.state({ sun: 1 });
  const target = { sun: 0 };
  assert.deepEqual(one.advance(target, 0), { sun: .8, moon: 0 });
  const elapsed = one.advance(target, 1);
  for (let i = 0; i < 10; i++) many.advance(target, .1);
  assert(Math.abs(elapsed.sun - many.gains().sun) < 1e-12);
  assert(Math.abs(elapsed.moon - many.gains().moon) < 1e-12);
  assert(elapsed.sun > 0 && elapsed.moon > 0 && elapsed.sun + elapsed.moon <= .80000001);
  assert.deepEqual(one.advance(target, 100), { sun: 0, moon: .8 });
  assert.throws(() => one.advance(target, -.1), /elapsed/);
});

test('invalid layers and malformed curves fail at construction', () => {
  assert.throws(() => layerMix.create([{ id: 'same' }, { id: 'same' }]), /layer/);
  assert.throws(() => layerMix.create([{ id: 'quiet', fadeOut: -1 }]), /layer/);
  assert.throws(() => layerMix.create([{ id: 'quiet', curves: { x: [[.5, 0], [.5, 1]] } }]), /stops/);
});

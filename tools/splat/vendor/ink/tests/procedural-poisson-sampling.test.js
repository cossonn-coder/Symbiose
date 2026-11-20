const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const { poisson } = KIT.procedural.sampling;
const bounds = { min: [-3, -2], max: [3, 2] };

function separated(samples, scale) {
  for (const [i, { point, radius }] of samples.entries()) {
    for (const other of samples.slice(i + 1)) {
      const d = Math.hypot(...point.map((x, axis) => (x - other.point[axis]) / scale[axis]));
      assert(d >= Math.max(radius, other.radius) - 1e-9);
    }
  }
}

test('seeded Bridson sampling reproduces an ordinary bounded 2D patch', () => {
  const opts = { bounds, radius: 0.29, seed: 23, mask: p => Math.hypot(p[0] / 3, p[1] / 2) < 1 };
  const result = poisson(opts);
  assert.equal(result.status, 'complete');
  assert(result.samples.length > 110);
  assert.deepEqual(result, poisson(opts));
  assert.notDeepEqual(result.samples, poisson({ ...opts, seed: 24 }).samples);
  assert(result.samples.every(({ point }) => opts.mask(point)));
  separated(result.samples, [1, 1]);
});

test('variable radii, pinned seeds, and anisotropic world spacing share a symmetric distance rule', () => {
  const axisScale = [0.65, 1.4, 1],
    pin = [0, 0, 0],
    radius = p => p[0] < 0 ? 0.28 : 0.51,
    result = poisson({
      bounds: { min: [-2, -1, -1], max: [2, 1, 1] },
      seeds: [pin], axisScale, radius, minRadius: 0.28, maxRadius: 0.51,
      maxPoints: 220, seed: 8
    });
  assert(result.samples.length > 30);
  assert.deepEqual(result.samples[0].point, pin);
  assert(!Object.isFrozen(pin));
  assert(result.samples.some(s => s.radius === 0.28) && result.samples.some(s => s.radius === 0.51));
  assert(result.samples.every(s => s.radius === radius(s.point)));
  separated(result.samples, axisScale);
});

test('Poisson sampling handles explicit budgets, empty masks, and invalid pins', () => {
  const opts = { bounds, radius: 0.25 };
  assert.equal(poisson({ ...opts, mask: () => false }).samples.length, 0);
  assert.equal(poisson({ ...opts, maxTrials: 1 }).status, 'budget');
  assert.equal(poisson({ ...opts, maxPoints: 3 }).status, 'point-limit');
  assert.throws(() => poisson({ ...opts, seeds: [[0, 0], [0.1, 0]] }), /spacing/);
  assert.throws(() => poisson({ ...opts, radius: () => 0.6, minRadius: 0.2, maxRadius: 0.4 }), /declared bounds/);
});

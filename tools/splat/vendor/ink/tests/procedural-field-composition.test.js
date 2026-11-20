const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT, makeBuilder, makeSculpt } = require('..').load();
const F = KIT.procedural.fields;

function near(a, b, tolerance = 1e-8) {
  assert(Math.abs(a - b) <= tolerance * Math.max(1, Math.abs(a), Math.abs(b)), a + ' differs from ' + b);
}
function numeric(fn, p, i) {
  const small = p.slice(), large = p.slice(), h = 1e-6;
  small[i] -= h;
  large[i] += h;
  return (fn(...large) - fn(...small)) / (2 * h);
}

test('2D, 3D and 4D simplex values are seeded and their analytic derivatives agree with finite differences', () => {
  for (const dimension of [2, 3, 4]) {
    const sampler = F.simplex({ dimension, seed: 124 }),
      duplicate = F.simplex({ dimension, seed: 124 }),
      changed = F.simplex({ dimension, seed: 125 });
    let mismatch = 0;
    for (let i = 0; i < 30; i++) {
      const args = Array.from({ length: dimension }, (_, axis) => Math.sin(i * (axis + 2.1)) * 3 + 0.17 * (axis + 1)),
        sample = sampler.sample(...args);
      assert.deepEqual(sample, duplicate.sample(...args));
      assert.equal(sample.value, sampler.value(...args));
      mismatch += Number(sample.value !== changed.value(...args));
      for (const [axis, derivative] of sample.gradient.entries()) near(derivative, numeric(sampler.value, args, axis), 2e-5);
    }
    assert(mismatch > 20);
  }
});

test('periodic gradient fields tile with matching slopes at positive and negative world offsets', () => {
  const periodic = F.compile({ type: 'periodic', period: [3.75, null, 4.2], scale: [0.7, 1.0, 0.45], seed: 17 });
  for (const point of [[0, 0.55, 0], [-5.2, 1.6, 3.8], [0.25, 0, -0.2]]) {
    const [x, y, z] = point,
      a = periodic.sample(...point),
      b = periodic.sample(x + 7.5, y, z - 4.2);
    near(a.value, b.value);
    for (const [i, derivative] of a.gradient.entries()) {
      near(derivative, b.gradient[i]);
      near(derivative, numeric(periodic, point, i), 1e-5);
    }
  }
});

test('4D loop fields repeat in time and report the time derivative', () => {
  const loop = F.compile({ type: 'loop', period: 2.75, radius: 0.56, scale: [0.85, 1, 1.3], seed: 22 }),
    a = [0.37, 1.82, -0.79, 0.75],
    at = loop.sample(...a),
    next = loop.sample(...a.slice(0, 3), -2);
  near(at.value, next.value);
  near(at.dt, next.dt);
  near(at.dt, numeric(loop, a, 3), 2e-5);
  near(at.gradient[0], numeric(loop, a, 0), 2e-5);
  assert.equal(at.gradient[1], 0);
  assert.notEqual(at.value, loop(...a.slice(0, 3), 0.9));
});

test('progressive warp, ridges, billows, distance and terraces compose as serializable expressions', () => {
  const spec = {
      type: 'add', inputs: [
        {
          type: 'warp', scale: [0.9, 1.8, 0.7], strength: 0.18, iterations: 3,
          source: { type: 'ridge', scale: 1.25, octaves: 3, feedback: 1.1 }
        },
        { type: 'multiply', inputs: [0.31, { type: 'billow', scale: 2, octaves: 3 }] },
        { type: 'terrace', source: { type: 'distance', axes: 'xz', paths: [[[-2, 0, -1], [2, 0, -1]]] }, step: 0.4, transition: 0.5 }
      ]
    },
    f = F.compile(spec, { seed: 55 }),
    args = [0.71, 0.33, 0.32, 0.22],
    sample = f.sample(...args);
  near(sample.value, f(...args));
  for (const [axis, derivative] of sample.gradient.entries()) near(derivative, numeric(f, args, axis), 8e-5);
  const repaired = F.compile(JSON.parse(JSON.stringify(f.spec)), { seed: f.seed });
  assert.deepEqual(repaired.sample(...args), sample);
  spec.inputs[1].inputs[0] = 0.8;
  assert.deepEqual(f.sample(...args), sample);
  const terrace = F.compile({ type: 'terrace', source: { type: 'axis', axis: 'x' }, step: 1, transition: 0.3 });
  assert.equal(terrace(0.2, 0, 0), 0);
  assert.equal(terrace(0.8, 0, 0), 1);
  assert.equal(terrace(0.5, 0, 0), 0.5);
});

test('the sculpt displacement node accepts an expression and leaves callbacks compatible', () => {
  const B = makeBuilder(5), S = KIT.sculpt(makeSculpt(B)),
    ball = S.ball([0, 0.8, 0], 0.65, { r: [1, 2, 3] }, { hold: true, res: 0.12 }),
    jit = { type: 'clamp', source: { type: 'add', inputs: [0.6, { type: 'multiply', inputs: [0.4, { type: 'simplex', scale: 0.7 }] }] } },
    fromData = S.displace(ball, jit, 0.04, { seed: 29, hold: true }),
    fromCode = S.displace(ball, F.compile(jit, { seed: 29 }), 0.04, { hold: true });
  for (const p of [[0.3, 0.2, 0], [0, 0.8, 0.5], [-0.3, 0.5, 0.12]]) near(fromData.sd(...p), fromCode.sd(...p));
  const solid = S.displace(ball, jit, 0.04, { seed: 29, res: 0.12 });
  assert(Number.isFinite(S.psd(solid, 0.4, 0.6, 0.3)));
  S.bake();
  assert(B.finish({}).count > 50);
});

test('invalid field trees and compounded field evaluation budgets fail explicitly', () => {
  const cycle = { type: 'clamp' };
  cycle.source = cycle;
  assert.throws(() => F.compile(cycle), /noncyclic/);
  assert.throws(() => F.compile({ type: 'loop', period: -1 }), /period/);
  assert.throws(() => F.compile({ type: 'fbm', octaves: 10, source: { type: 'fbm', octaves: 10 } }, { maxOperations: 50 }), /operation budget/);
});

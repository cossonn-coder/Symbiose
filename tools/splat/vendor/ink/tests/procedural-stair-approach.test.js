const { test } = require('node:test');
const assert = require('node:assert/strict');
const fit = require('..').load().KIT.procedural.routes.fitStairApproach;
const spec = { landing: [2, .62, 3], direction: [0, .1, 5], height: () => 0, rise: .17, tread: .23 };

test('a fitted approach chooses the shortest sampled run with comfortable treads', () => {
  const r = fit(spec);
  assert.equal(r.risers, 4);
  assert(r.tread >= .23);
  assert(r.run - 4 * .23 < .06);
  assert.equal(r.rise * r.risers, .62);
  assert.deepEqual(r.axis, [0, 0, 1]);
  assert.deepEqual(r.toe, [2, 0, 3 + r.run]);
  assert(Object.isFrozen(r.toe));
});

test('approaches respect discontinuous masks, local terrain and probe budgets', () => {
  assert.equal(fit({ ...spec, accept: p => p[2] < 3.8 || p[2] > 4 }), null);
  assert.equal(fit({ ...spec, height: (x,z) => z < 3.5 ? .72 : 0 }), null);
  const r = fit({ ...spec, inside: p => p[2] < 3.12 });
  assert(r && r.toe[2] > 3.12);
  assert.equal(fit({ ...spec, inside: p => p[2] < 3.12 || p[2] > 3.35 }), null);
  assert.throws(() => fit({ ...spec, step: .001, budget: 12 }), /budget/);
  assert.throws(() => fit({ ...spec, direction: [0, 1, 0] }), /horizontal/);
});

test('the landing seats the whole stair width against a faceted platform edge', () => {
  const r = fit({ ...spec, outline: [[1, 2], [3, 2], [2, 3]], width: .6 });
  assert(r.landing[2] < 2.71);
  assert(r.landing[2] > 2.69);
  assert.equal(fit({ ...spec, outline: [[1, 2], [3, 2], [2, 3]], width: 3 }), null);
});

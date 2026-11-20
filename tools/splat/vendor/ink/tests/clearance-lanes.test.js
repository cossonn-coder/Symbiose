const test = require('node:test');
const assert = require('node:assert/strict');
const P = require('..').load().KIT.procedural;

test('lane fitting ranks by distance along the carrier and refines the first clear station', () => {
  const pointAt = t => [2 * Math.cos(t), 1, 2 * Math.sin(t)];
  const value = P.fitAlongLane({
    range: [-1, 1], start: 0, pointAt, spacing: .11,
    fit: t => t <= -.21 || t >= .33 ? { point: pointAt(t) } : null
  });
  assert(value.parameter <= -.21 && value.parameter > -.212);
  assert(Math.abs(value.distance - .42) < .004);
  assert.deepEqual(value.value.point, pointAt(value.parameter));
  assert.equal(P.fitAlongLane({
    range: [0, Math.PI / 2], start: 0, pointAt, maxDistance: 2.9,
    fit: t => t > 1.52
  }), null);
});

test('a lane ends when its support chart stops and spends only the supplied probe budget', () => {
  const pointAt = t => t > .29 && t < .71 ? null : [t, 0, 0];
  let last = 0;
  const found = P.fitAlongLane({
    range: [0, 1], start: 0, pointAt, spacing: .25, fit(t) {
      last = Math.max(last, t);
      return t >= .28;
    }
  });
  assert(found.parameter >= .28 && found.parameter <= .282);
  assert(last <= .29);
  assert.equal(P.fitAlongLane({range:[0,1], start:0, pointAt, fit:t=>t>.9}), null);
  let tests = 0;
  assert.equal(P.fitAlongLane({
    range:[0,1], start:.5, pointAt:t=>[t,0,0], maxTests:4,
    fit(){tests++; return false;}
  }),null);
  assert.equal(tests,4);
});

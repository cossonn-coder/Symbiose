const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: K, makeBuilder, makeSculpt } = require('..').load();
const { construct } = K.procedural;
const close = (a, b, eps = 1e-7) => assert(Math.abs(a - b) <= eps, a + ' differs from ' + b);
const rectangle = [[0,0],[6,0],[6,4],[0,4]];

test('signed polygon offsets preserve holes and extrude an exact rounded footprint', () => {
  const hole = [[2,1],[4,1],[4,3],[2,3]], footprint = construct.profile([rectangle, hole]),
    outset = construct.offset(footprint, 0.25), inset = construct.offset(footprint, -0.25),
    prism = construct.extrude(outset, { low: -0.1, high: 0.55 });
  assert(footprint.sd(1,2) < 0 && footprint.sd(3,2) > 0);
  close(outset.sd(-0.25,2), 0);
  close(outset.sd(2.25,2), 0);
  close(inset.sd(1.75,2), 0);
  assert(prism.sd(1,0.2,2) < 0 && prism.sd(3,0.2,2) > 0);
  close(prism.sd(-0.35,0.65,2), Math.hypot(0.1,0.1));
  const paths = outset.contours({ cell: 0.09 });
  assert.equal(paths.length, 2);
  assert(paths.every(p => p.closed));
  assert.throws(() => construct.profile([rectangle, [[2,-1],[4,1],[2,2]]]), /inside|cross/);
});

test('weighted ridge heights follow the given pitch and retain a flat terminal ridge', () => {
  const angle = 0.57, plain = construct.weightedRoof([rectangle], { pitch: angle }),
    weighted = construct.weightedRoof([rectangle], { pitches: [[0.49,0.69,0.82,0.69]] });
  assert.equal(plain.status, 'ok');
  close(plain.area, plain.coverage);
  close(plain.query(3,2).height, 2 * Math.tan(angle));
  const ridge = plain.arcs.find(a => a.a[1] > 0 && Math.abs(a.a[1] - a.b[1]) < 1e-8);
  assert(ridge && ridge.kind === 'ridge');
  close(K.V.dist(ridge.a, ridge.b), 2);
  close(weighted.query(2.8,0.3).height, 0.3 * Math.tan(0.49));
  close(weighted.query(2.8,3.7).height, 0.3 * Math.tan(0.82));
  assert.equal(weighted.query(2.8,4.1), null);
});

test('reflex vertices split the wavefront while courtyard fronts join it', () => {
  const hook = [[0,0],[6,0],[6,2],[3,2],[3,5],[0,5]],
    angle = [[0.56,0.6,0.9,0.68,0.68,0.56]],
    lean = construct.weightedRoof([hook], { pitches: angle }),
    outer = [[0,0],[8,0],[8,6],[0,6]], hole = [[2,2],[5,2],[5,4],[2,4]],
    court = construct.weightedRoof([outer, hole], { pitches: [[0.6,0.7,0.68,0.62],[0.6,0.9,0.45,0.7]] });
  assert.equal(lean.status, 'ok');
  assert(lean.events.some(e => e.kind === 'split'));
  assert(lean.arcs.some(a => a.kind === 'valley'));
  close(lean.coverage, 21);
  assert.equal(lean.query(4,3), null);
  assert.equal(court.status, 'ok');
  assert(court.events.some(e => e.kind === 'join'));
  assert.equal(court.query(3,3), null);
  close(court.coverage, 42);
  for (const p of [[1,1],[5,1],[7,3],[4,5],[1,4]]) assert(court.query(...p).height > 0);
  const B = makeBuilder(11), S = K.sculpt(makeSculpt(B)), roof = lean.solid({ base: 1.7, thickness: 0.14 });
  S.implicitForm(roof, { r: [1,2,3] }, { res: 0.1 });
  S.bake();
  assert(B.finish({}).count > 500);
});

test('weighted fronts cover seeded concave rings and expose exhausted searches', () => {
  const random = K.grow.dice(1791);
  for (let trial = 0; trial < 45; trial++) {
    const count = 5 + (trial % 10), ring = Array.from({ length: count }, (_, i) => {
      const angle = (i + random() * 0.31) * Math.PI * 2 / count, radius = 0.9 + random() * 2.2;
      return [Math.cos(angle) * radius, Math.sin(angle) * radius];
    }), widths = ring.map(() => 0.48 + random() * 0.56),
      roof = construct.weightedRoof([ring], { pitches: [widths] });
    assert.equal(roof.status, 'ok', roof.reason);
    close(roof.area, roof.coverage, 1e-6);
    for (const [i, p] of ring.entries())
      close(roof.query(...p).height, 0, widths[i] * 1e-7);
  }
  const limited = construct.weightedRoof([rectangle], { maxChecks: 1 });
  assert.equal(limited.status, 'budget');
  assert.throws(() => limited.solid(), /complete roof/);
});

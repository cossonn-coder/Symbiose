const test = require('node:test'),
  assert = require('node:assert/strict'),
  A = require('..').load().KIT.procedural,
  C = A.planarCells;
const box = (r = 1) => ({ min: [-r, 0, -r], max: [r, 0, r] }),
  near = (a, b, e = 1e-6) => assert(Math.abs(a - b) < e, `${a} != ${b}`);
function manifold(mesh) {
  const edges = new Map();
  for (let i = 0; i < mesh.positions.length; i += 9) {
    const ps = [0, 1, 2].map(j =>
      Array.from(mesh.positions.slice(i + j * 3, i + j * 3 + 3))
        .map(v => v.toFixed(6))
        .join('/')
    );
    for (let k = 0; k < 3; k++) {
      const key = [ps[k], ps[(k + 1) % 3]].sort().join('|');
      edges.set(key, (edges.get(key) || 0) + 1);
    }
  }
  assert(
    [...edges.values()].every(n => n === 2),
    'every closed prism mesh edge has two incident triangles'
  );
}
test('shared jittered cells are deterministic, inset, nonoverlapping and independent of layout traversal', () => {
  const raw = { size: 0.6, jitter: 0.2, gap: 0.08, seed: 17 },
    a = C.cell(0, 0, raw),
    b = C.cell(1, 0, raw);
  assert.deepEqual(C.cell(0, 0, raw), a);
  assert(!Object.isFrozen(raw));
  const layout = C.layout({ min: [0, 0, 0], max: [1.2, 0, 1.2] }, () => -1, raw);
  for (const cell of layout.cells)
    for (const other of layout.cells)
      if (cell !== other) for (const q of cell.polygon) assert(other.distance(...q) > -0.000001);
  assert.notDeepEqual(a.polygon, b.polygon);
});
test('bounded clipping preserves a hole inside one cell and produces a closed, pickable solid', () => {
  const work = { min: [0, 0, 0], max: [2, 0, 2] },
    f = C.layout(work, (x, z) => 0.35 - Math.hypot(x - 1, z - 1), {
      size: 2,
      gap: 0,
      jitter: 0,
      chamfer: 0,
      resolution: 0.08
    }),
    cell = f.cells.find(c => c.key === '0:0'),
    p = C.prism(cell, { bottom: -0.3, top: 0.2 });
  assert(cell.distance(1, 1) > 0.3);
  assert(cell.distance(0.3, 0.3) < 0);
  assert.equal(p.raycast([1, 1, 1], [0, -1, 0]), null);
  near(p.raycast([0.3, 1, 0.3], [0, -2, 0]).p[1], 0.2);
  const side = p.raycast([1, 0, 1], [1, 0, 0]);
  near(side.p[0], 1.35, 0.002);
  assert(side.n[0] < -0.9);
  manifold(p.mesh());
  assert(p.mesh().positions.every(Number.isFinite));
});
test('minimum editor-width diagonal strokes retain clipped pieces and physical gaps between cells', () => {
  const f = C.layout(box(), (x, z) => Math.abs(z - 0.37 * x) - 0.1);
  assert(f.cells.length > 3);
  let area = 0;
  for (const c of f.cells) {
    area += c.area;
    for (const poly of c.fragments) for (const q of poly) assert(Math.abs(q[1] - 0.37 * q[0]) <= 0.10001);
    manifold(C.prism(c).mesh());
  }
  assert(area > 0.15 && area < 0.45);
});
test('disconnected masks and erasures do not acquire connecting faces across the removed region', () => {
  const f = C.layout(box(), (x, z) => Math.max(Math.abs(z) - 0.3, 0.2 - Math.abs(x)));
  for (const c of f.cells) {
    assert(c.distance(0, 0) > 0);
    const p = C.prism(c);
    assert.equal(p.raycast([0, 1, 0], [0, -1, 0]), null);
    manifold(p.mesh());
  }
});
test('prism samples remain on its actual closed surface, including the clipped sides', () => {
  const c = C.layout(box(0.5), (x, z) => Math.hypot(x, z) - 0.4, { size: 1, jitter: 0, gap: 0.02 }).cells[0],
    p = C.prism(c, { bottom: -0.4, top: 0.15 });
  let count = 0,
    sides = 0;
  p.sample(0.1, (q, n) => {
    assert(q.every(Number.isFinite) && n.every(Number.isFinite));
    near(p.distance(q), 0, 0.000001);
    if (Math.abs(n[1]) < 0.1) sides++;
    count++;
  });
  assert(count > 30 && sides > 10);
  assert.throws(() => p.sample(0.0000001, () => {}), /budget/);
});
test('work regions are deduplicated and extending work bounds keeps existing complete cell identities', () => {
  const a = C.layout(box(), () => -1),
    b = C.layout(box(2), () => -1),
    c = C.layout(box(), () => -1, { regions: [box(), box()] });
  assert.deepEqual(
    a.cells.map(c => c.key),
    c.cells.map(c => c.key)
  );
  for (const cell of a.cells.filter(c => c.polygon.every(q => Math.abs(q[0]) < 0.7 && Math.abs(q[1]) < 0.7))) {
    const other = b.cells.find(c => c.key === cell.key);
    assert.deepEqual(cell.polygon, other.polygon);
    near(cell.area, other.area);
  }
});
test('an explicit caller cache reuses immutable clipped cells and empty results without new mask queries', () => {
  const cache = new Map(),
    memo = { get: r => cache.get(r.key), set: (r, v) => cache.set(r.key, v) },
    options = { cache: memo },
    first = C.layout(box(), (x, z) => Math.hypot(x, z) - 0.3, options);
  assert(first.sampling.samples > 100);
  const second = C.layout(box(), () => assert.fail('cached geometry must not resample'), options);
  assert.equal(second.sampling.samples, 0);
  assert.deepEqual(second.cells, first.cells);
  assert(Object.isFrozen(first.cells[0].fragments));
});
test('invalid shapes, coordinates, callbacks and excessive work fail explicitly without freezing caller data', () => {
  for (const raw of [
    { size: 0 },
    { gap: 1 },
    { jitter: 0.25 },
    { resolution: 0 },
    { seed: NaN },
    { maxCells: 0 },
    null,
    []
  ])
    assert.throws(() => C.parameters(raw));
  assert.throws(() => C.layout(box(), () => NaN));
  assert.throws(() => C.layout(box(), () => -1, { maxSamples: 2 }), /budget/);
  assert.throws(() => C.layout(box(50), () => -1, { maxCells: 2 }), /budget/);
  assert.throws(() => C.layout(box(), () => -1, { cache: {} }));
  assert.throws(() => C.layout({ min: [NaN, 0, 0], max: [1, 0, 1] }, () => -1));
  const raw = { regions: [box()] };
  C.layout(box(), () => Infinity, raw);
  assert(!Object.isFrozen(raw.regions[0]));
});

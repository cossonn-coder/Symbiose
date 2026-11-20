const test = require('node:test'),
  assert = require('node:assert/strict'),
  K = require('..').load().KIT,
  A = K.procedural;
const near = (a, b, eps = 1e-8) => assert(Math.abs(a - b) < eps, `${a} != ${b}`);
test('fitted panels fill arbitrary spans and retain distinct staggered end cells', () => {
  for (const width of [1e-8, 0.13, 1.35, 3.1, 17.9]) {
    const h = width * 0.73,
      f = A.fittedCourses({ width, height: h, unit: [width / 7.3, h / 4.6], joint: width * 0.002, stagger: 0.5 });
    near(f.rows[0].min, 0);
    near(f.rows.at(-1).max, h);
    let area = 0;
    for (const row of f.rows) {
      near(row.cells[0].bounds.min[0], 0);
      near(row.cells.at(-1).bounds.max[0], width);
      assert.equal(new Set(row.cells.map(c => c.id)).size, row.cells.length);
      for (let i = 0; i < row.cells.length; i++) {
        const c = row.cells[i];
        if (i) near(row.cells[i - 1].bounds.max[0], c.bounds.min[0]);
        assert(c.inset.min.every((v, k) => v < c.inset.max[k]));
        area += (c.bounds.max[0] - c.bounds.min[0]) * (c.bounds.max[1] - c.bounds.min[1]);
      }
    }
    near(area, width * h, Math.max(1e-20, width * h * 1e-8));
    assert(Object.isFrozen(f.cells[0].inset.min));
  }
});
test('a periodic staggered course shares identity and joint distance across its wrap', () => {
  const f = A.fittedCourses({ width: 3.1, height: 2, unit: [0.42, 0.2], joint: 0.025, stagger: 0.5, periodic: true });
  for (const v of [0.1, 0.3, 0.5, 1.3]) {
    const a = f.at(1e-9, v),
      b = f.at(3.1 - 1e-9, v);
    if (a.row % 2) assert.equal(a.id, b.id);
    near(f.jointDistance(1e-9, v), f.jointDistance(3.1 - 1e-9, v));
    assert.equal(f.at(-0.1, v).id, f.at(3, v).id);
  }
  const one = A.fittedCourses({ width: 1, height: 1, unit: [1, 1], budget: 1 });
  assert.equal(one.cells.length, 1);
  assert.equal(one.jointDistance(0, 0.5), -Infinity);
  assert.equal(one.at(-0.1, 0.5), null);
});
test('invalid dimensions, fragmented ends and cell explosions fail before allocation', () => {
  for (const x of [
    { width: 0 },
    { height: Infinity },
    { unit: [0, 1] },
    { unit: [1e-12, 1e-12] },
    { joint: 0.2 },
    { stagger: 1 },
    { stagger: 0.001, joint: 0.01 },
    { budget: 0 },
    { periodic: 1 }
  ])
    assert.throws(() => A.fittedCourses({ width: 3, height: 2, unit: [0.4, 0.2], ...x }));
  assert.throws(() => A.fittedCourses({ width: 3, height: 2, unit: [0.4, 0.2] }).at(NaN, 0), /finite/);
});

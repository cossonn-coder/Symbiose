const test = require('node:test'),
  assert = require('node:assert/strict'),
  K = require('..').load().KIT,
  A = K.procedural,
  V = K.V;
const near = (a, b, e = 1e-6) => assert(Math.abs(a - b) < e, `${a} != ${b}`);
test('catenaries keep endpoints and exact horizontal midpoint sag for level and unequal heights', () => {
  for (const rise of [0, 2, -3, 20])
    for (const sag of [0.001, 0.2, 1]) {
      const a = [1, 2, -1],
        b = [7, 2 + rise, -1],
        q = A.spans.catenary(a, b, { sag });
      assert.deepEqual(q.sample(0).point, a);
      assert.deepEqual(q.sample(1).point, b);
      assert(q.length > V.dist(a, b));
      let lo = 0,
        hi = 1;
      for (let i = 0; i < 50; i++) {
        const t = (lo + hi) / 2;
        if (q.sample(t).point[0] < 4) lo = t;
        else hi = t;
      }
      near(q.sample((lo + hi) / 2).point[1], 2 + rise / 2 - sag, 1e-7);
      const lengths = [];
      for (let i = 0; i < 20; i++) {
        let length = 0,
          prev = q.sample(i / 20).point;
        for (let j = 1; j <= 100; j++) {
          const next = q.sample((i + j / 100) / 20).point;
          length += V.dist(prev, next);
          prev = next;
        }
        lengths.push(length);
      }
      for (const length of lengths) near(length, q.length / 20, 2e-5);
      for (const t of [0.1, 0.35, 0.8]) near(q.closest(q.sample(t).point).t, t, 2e-7);
    }
});
test('gravity frames have conservative world bounds, and taut or vertical spans stay finite', () => {
  for (const gravity of [
    [0, -1, 0],
    [-1, -2, 3],
    [1, 0, 0]
  ]) {
    const q = A.spans.catenary([-2, 3, 1], [4, -1, 6], { sag: 1, gravity });
    for (let i = 0; i <= 1000; i++) {
      const at = q.sample(i / 1000);
      assert(at.point.every((v, j) => v >= q.bounds.min[j] - 1e-7 && v <= q.bounds.max[j] + 1e-7));
      near(V.len(at.tangent), 1);
      near(V.dot(at.side, at.tangent), 0);
    }
  }
  for (const q of [
    A.spans.catenary([0, 0, 0], [0, 3, 0], { sag: 1 }),
    A.spans.catenary([0, 0, 0], [3, 2, 0], { sag: 0 })
  ]) {
    assert(q.straight);
    assert(q.sample(0.5).point.every(Number.isFinite));
    near(q.length, V.dist(q.sample(0).point, q.sample(1).point));
  }
  for (const args of [
    [[0, 0, 0], [0, 0, 0], {}],
    [[0, 0, 0], [1, 0, 0], { sag: -1 }],
    [[0, 0, 0], [1, 0, 0], { sag: 3 }],
    [[0, 0, 0], [1, 0, 0], { gravity: [0, 0, 0] }]
  ])
    assert.throws(() => A.spans.catenary(...args));
});

const test = require('node:test');
const assert = require('node:assert/strict');
const P = require('..').load().KIT.procedural;

const roots = [{ key: 'base', point: [0, 0, 0] }, { key: 'base/0', point: [2, 0, 0] }];
const plane = ([x, y]) => ({ point: [x, y, 0], normal: [0, 0, 1] });

test('surface growth yields deterministic branching with stable, unique keys across chart splits', () => {
  const config = { roots, steps: 18, seed: 8, branchEvery: 4 };
  const whole = P.surfaceGrowth.trace({ ...config, project: plane });
  const split = P.surfaceGrowth.trace({ ...config, project: p => ({ ...plane(p), chart: p[1] > 1 ? 'upper' : 'lower' }) });
  assert(whole.edges.length > 36);
  assert(whole.ends.length > roots.length);
  assert.equal(new Set(whole.nodes.map(n => n.key)).size, whole.nodes.length);
  assert.deepEqual(whole.nodes.map(n => [n.key, n.point]), split.nodes.map(n => [n.key, n.point]));
  assert.deepEqual(whole, P.surfaceGrowth.trace({ ...config, project: plane }));
  assert(Object.isFrozen(whole.edges[0].frames));
});

test('freezing a growth graph leaves the projector’s reusable metadata mutable', () => {
  const tag = { chart: ['wall'] };
  const result = P.surfaceGrowth.trace({ roots, project: p => ({ ...plane(p), tag }), steps: 2 });
  tag.chart.push('top');
  assert.deepEqual(result.nodes[0].tag.chart, ['wall']);
  assert(Object.isFrozen(result.nodes[0].tag.chart));
});

test('link validation blocks thin gaps and can supply intermediate carrier frames', () => {
  const config = { roots: roots.slice(0, 1), project: plane, step: .2, steps: 24, spread: 0 };
  const graph = P.surfaceGrowth.trace({ ...config, connect(a, b) {
    if (a.point[1] < .35 && b.point[1] >= .35) return null;
    return [plane(a.point.map((v, i) => (v + b.point[i]) / 2))];
  } });
  assert(graph.edges.length);
  assert(graph.nodes.every(n => n.point[1] < .35));
  assert(graph.edges.every(e => e.frames.length === 3));
  assert.equal(P.surfaceGrowth.trace({ ...config, budget: 2 }).nodes.length, 2);
});

test('surface normals transport a tangent across curvature without drifting off the carrier', () => {
  const result = P.surfaceGrowth.trace({
    roots: [{ key: 'ring', point: [1, 0, 0], direction: [0, 0, 1] }],
    project([x, y, z]) {
      const r = Math.hypot(x, z);
      return { point: [x / r, y, z / r], normal: [x / r, 0, z / r] };
    },
    step: .18, steps: 24, spread: 0, attraction: 0, tips: 1,
  });
  assert.equal(result.nodes.length, 25);
  assert(result.nodes.every(n => Math.abs(Math.hypot(n.point[0], n.point[2]) - 1) < 1e-8));
  assert(result.nodes.some(n => n.point[0] < -.95));
});

test('links can round an exact corner and continue in the transported heading', () => {
  const result = P.surfaceGrowth.trace({
    roots: [{ key: 'corner', point: [0, 0, 0], direction: [1, 0, 0] }],
    project(point, last, step) {
      if (!last) return { point, normal: [0, 0, 1] };
      return last.depth ? { point, normal: [1, 0, 0] } : { point: [0, 0, -step], normal: [1, 0, 0] };
    },
    step: .2, steps: 3, spread: 0, attraction: 0,
  });
  assert.deepEqual(result.nodes[3].point.map(v => Math.round(v * 10)), [0, 0, -6]);
  assert.deepEqual(P.surfaceGrowth.transport([1, 0, 0], [0, 0, 1], [1, 0, 0]), [0, 0, -1]);
});

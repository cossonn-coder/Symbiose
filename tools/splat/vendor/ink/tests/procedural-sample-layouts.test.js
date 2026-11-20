const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const { sampling } = KIT.procedural;

test('a centered grid window retains the original phase and includes exact boundary centers',()=>{
  const axis=[-.67,3.91],count=237;
  const points=Array.from({length:count},(_,i)=>axis[0]+(axis[1]-axis[0])*((i+.5)/count));
  for(const region of [[-4,-2],[4,8],[-1,.2],[.35,.36],[points[33],points[80]],[points[7],points[7]],axis]){
    const [start,end]=sampling.centeredGridRange(axis,count,region);
    assert.deepEqual(points.slice(start,end),points.filter(x=>x>=region[0]&&x<=region[1]));
  }
  assert.deepEqual(sampling.centeredGridRange(axis,count),[0,count]);
  assert.throws(()=>sampling.centeredGridRange(axis,0),/positive sample count/);
  assert.throws(()=>sampling.centeredGridRange(axis,100,[2,1]),/finite intervals/);
});

function nearestGap(set) {
  let min = Infinity;
  for (const [i, p] of set.entries())
    for (const q of set.slice(i + 1)) min = Math.min(min, Math.hypot(...p.map((v, axis) => v - q[axis])));
  return min;
}

test('weighted elimination yields reproducible, exact-count progressive subsets from a crowded candidate set', () => {
  const dice = KIT.grow.dice(48),
    points = Array.from({ length: 215 }, () => [dice() * 4, dice() * 2]),
    options = { count: 43, progressive: true },
    selection = sampling.eliminate(points, options);
  assert.equal(selection.points.length, 43);
  assert.equal(selection.indices.length, new Set(selection.indices).size);
  assert.deepEqual(selection, sampling.eliminate(points, options));
  assert.deepEqual(selection.levels, [1, 2, 3, 6, 11, 22, 43]);
  assert(nearestGap(selection.points) > nearestGap(points.slice(0, 43)) * 3);
  assert(nearestGap(selection.points.slice(0, 6)) > nearestGap(selection.points));
  const chosen = sampling.eliminate([[0, 0], [0, 0]], { count: 1, weights: [1, 3] });
  assert.deepEqual(chosen.indices, [1]);
  assert.throws(() => sampling.eliminate(points, { count: 10, maxChecks: 1 }), /budget/);
});

test('Lloyd moves sites toward weighted cell centroids, preserving fixed sites and the domain mask', () => {
  const raw = [[0.03, 0.28], [0.4, 0.4], [0.58, 0.52], [0.94, 0.7]],
    bounds = { min: [0, 0], max: [1, 1] },
    mask = (x, y) => !(x > 0.72 && y < 0.36),
    r = sampling.lloyd(raw, { bounds, spacing: 0.04, iterations: 7, mask, fixed: [0], density: (x, y) => 1 + y });
  assert.deepEqual(r.points[0], raw[0]);
  assert.notDeepEqual(r.points, raw);
  assert(r.points.every(p => mask(...p)));
  const [first] = sampling.lloyd([[0.12, 0.1]], { bounds, spacing: 0.05, iterations: 1 }).points;
  assert(Math.hypot(first[0] - 0.5, first[1] - 0.5) < 1e-12);
  assert.throws(() => sampling.lloyd(raw, { bounds, maxChecks: 2 }), /budget/);
});

test('adaptive chart samples jitter within strata and concentrate samples where the surface bends', () => {
  const sample = (u, v) => [Math.cos(u * Math.PI * 1.2), v * 2, Math.sin(u * Math.PI * 1.2)],
    spec = { spacing: 0.3, seed: 5, sample },
    ordinary = sampling.patch(spec),
    jittered = sampling.patch({ ...spec, seed: 6 }),
    curved = sampling.patch({ ...spec, curvature: 4 }),
    atCenter = sampling.patch({ ...spec, jitter: 0 });
  assert.equal(ordinary.length, atCenter.length);
  assert.notDeepEqual(ordinary, atCenter);
  assert.notDeepEqual(ordinary, jittered);
  assert.deepEqual(ordinary, sampling.patch(spec));
  assert(curved.length > ordinary.length * 2);
  assert(curved.every(({ point, uv }) => Math.abs(Math.hypot(point[0], point[2]) - 1) < 1e-10 &&
    uv.every(v => v > 0 && v < 1)));
});

test('area strata distribute samples across triangles in proportion to area and omit degeneracies', () => {
  const triangles = new Float32Array([0,0,0, 1,0,0, 0,1,0, 0,0,1, 3,0,1, 0,1,1, 0,0,2, 0,0,2, 0,0,2]);
  const samples = sampling.triangles(triangles, { count: 80, seed: 12 });
  assert.equal(samples.length, 80);
  assert.equal(samples.filter(p => p.triangle === 0).length, 20);
  assert.equal(samples.filter(p => p.triangle === 1).length, 60);
  assert(samples.every(p => Math.abs(p.point[2] - p.triangle) < 1e-12));
  assert(samples.every(p => Math.abs(p.barycentric.reduce((sum, v) => sum + v, 0) - 1) < 1e-12));
});

test('geodesic selection follows surface links instead of jumping to nearby points across a fold', () => {
  const points = [[0, 0, 0], [1, 0, 0], [1, 0.07, 0], [0, 0.07, 0], [0.1, 0, 0]],
    links = [[0, 4], [4, 1], [1, 2], [2, 3]],
    a = sampling.geodesicSpacing(points, links, { candidates: [0, 4, 3, 2, 1], distance: 0.15 });
  assert(a.indices.includes(0));
  assert(a.indices.includes(3));
  assert(!a.indices.includes(4));
  assert.throws(() => sampling.geodesicSpacing(points, links, { distance: 2, maxTraversals: 1 }), /budget/);
});

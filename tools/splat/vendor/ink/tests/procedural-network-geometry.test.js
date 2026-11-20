const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const { geometry, routes } = KIT.procedural;
const key = (a, b) => [Math.min(a, b), Math.max(a, b)].join(':');
const area = ([a, b, c]) => (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]);

function circumcircle(a, b, c, d) {
  const [x, y] = [a[0] - d[0], a[1] - d[1]], [i, j] = [b[0] - d[0], b[1] - d[1]],
    [k, l] = [c[0] - d[0], c[1] - d[1]];
  return (x * x + y * y) * (i * l - j * k) + (i * i + j * j) * (k * y - l * x) +
    (k * k + l * l) * (x * j - y * i);
}

test('native Delaunay keeps every site and forms locally valid triangles including very thin hulls', () => {
  const dice = KIT.grow.dice(16), sites = Array.from({ length: 90 }, () => [dice() * 2, dice()]),
    d = geometry.delaunay(sites);
  assert(d.triangles.length > 150);
  assert.equal(new Set(d.edges.flat()).size, sites.length);
  for (const tri of d.triangles) {
    const points = tri.map(i => sites[i]);
    assert(area(points) > 0);
    for (const [i, p] of sites.entries()) if (!tri.includes(i))
      assert(circumcircle(...points, p) <= 1e-10);
  }
  assert.equal(geometry.delaunay([[0,0],[0.7,1e-20],[1,0]]).triangles.length, 1);
  const collinear = geometry.delaunay([[0,0],[4,0],[2,0]], { constraints: [[0,1]] });
  assert.equal(collinear.triangles.length, 0);
  assert.deepEqual(new Set(collinear.constraints.map(pair => key(...pair))), new Set(['0:2', '1:2']));
});

test('constraint cavities recover every link in a crossing-free fan and reject crossing constraints', () => {
  const dice = KIT.grow.dice(107), sites = Array.from({ length: 70 }, () => [dice(), dice()]),
    constraints = Array.from({ length: 10 }, (_, i) => [0, i + 1]),
    d = geometry.delaunay(sites, { constraints }),
    edges = new Set(d.edges.map(pair => key(...pair)));
  assert(constraints.every(pair => edges.has(key(...pair))));
  assert.equal(new Set(d.edges.flat()).size, sites.length);
  assert.throws(() => geometry.delaunay([[0,0],[2,0],[2,2],[0,2]], { constraints: [[0,2],[1,3]] }), /cross/);
  assert.throws(() => geometry.delaunay(sites, { maxChecks: 2 }), /budget/);
});

test('polygon triangulation preserves concave boundaries and holes', () => {
  const outer = [[0,0],[7,0],[7,5],[4,5],[4,6],[0,6]],
    hole = [[1,1],[4,1],[4,3],[1,3]],
    result = geometry.triangulatePolygon([outer, hole]),
    sum = result.triangles.reduce((total, indices) => total + area(indices.map(i => result.points[i])) * 0.5, 0);
  assert.equal(sum, 33);
  assert(result.triangles.every(indices => {
    const center = indices.reduce(([x, z], i) => [x + result.points[i][0] / 3, z + result.points[i][1] / 3], [0,0]);
    return center[0] < 1 || center[0] > 4 || center[1] < 1 || center[1] > 3;
  }));
});

test('Delaunay networks span their sites and add beneficial loops in deterministic order', () => {
  const points = [[0,0,0],[2,0,0],[0,0,2],[2,0,2]],
    result = routes.network(points, { loops: 1 });
  assert.equal(result.status, 'ok');
  assert.equal(result.edges.length, 4);
  assert.equal(result.edges.filter(e => e.loop).length, 1);
  assert.equal(result.edges.filter(e => !e.loop).reduce((sum, e) => sum + e.cost, 0), 6);
  assert(result.edges.every(e => e.route.length === e.cost));
  assert.deepEqual(result.edges.map(e => [e.a,e.b]), routes.network(points, { loops: 1 }).edges.map(e => [e.a,e.b]));
  assert.equal(routes.network(points, { cost: () => Infinity }).status, 'unreachable');
});

test('a graph Steiner approximation keeps useful junctions and removes unrelated leaves', () => {
  const points = [[-1,0,0],[1,0,0],[0,0,1],[0,0,0],[0,0,-1]],
    links = [{a:0,b:3},{a:1,b:3},{a:2,b:3},{a:4,b:3},{a:0,b:1,cost:2.5},{a:0,b:2,cost:2.5},{a:1,b:2,cost:2.5}],
    r = routes.steiner(points, links, [0,1,2]);
  assert.equal(r.status, 'ok');
  assert.deepEqual(r.nodes, [0,1,2,3]);
  assert.equal(r.cost, 3);
  assert(r.edges.every(e => e.b === 3));
  assert.equal(routes.steiner(points, links, [0,1,2], { maxChecks: 1 }).status, 'budget');
});

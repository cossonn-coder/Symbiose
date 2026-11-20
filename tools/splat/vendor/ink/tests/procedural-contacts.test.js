const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const P = KIT.procedural;
const near = (a, b) => assert(Math.abs(a - b) < 1e-6, `${a} != ${b}`);
const identity = [1, 0, 0, 0, 1, 0, 0, 0, 1];

test('surface contacts retain the group identities and connect the sampled intersection', () => {
  const x = P.geometry.builder(),
    y = P.geometry.builder();
  x.quad([-2, 0, -1], [2, 0, -1], [2, 0, 1], [-2, 0, 1], { surface: 'horizontal' });
  y.quad([-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0], { surface: 'vertical' });
  const a = P.contacts.index(x.finish()),
    b = P.contacts.index(y.finish());
  const result = P.contacts.intersections(a, b);
  assert.equal(result.length, 1);
  assert.equal(result[0].surfaceA, 'horizontal');
  assert.equal(result[0].surfaceB, 'vertical');
  assert(result[0].points.every(p => Math.abs(p[1]) < 1e-6 && Math.abs(p[2]) < 1e-6));
  near(Math.min(...result[0].points.map(p => p[0])), -1);
  near(Math.max(...result[0].points.map(p => p[0])), 1);
  assert.deepEqual(P.contacts.intersections(a, a), []);
  assert.throws(() => P.contacts.intersections(a, b, { maxPairs: 1 }), /budget/);
});

test('curve trimming identifies even a thin, closed obstruction and keeps edge ownership', () => {
  const solid = P.pieces.box([0.17, 0, 0], [0.015, 0.4, 0.4], identity, { owner: 'clamp' });
  const index = P.contacts.index(solid.mesh);
  const start = [-2, 0, 0],
    end = [2, 0, 0];
  assert.equal(index.crossings(start, end).length, 2);
  assert(index.contains([0.17, 0, 0]));
  assert(!index.contains([0.5, 0, 0]));
  const [before, after] = P.contacts.clipCurve([start, end], [{ id: 'clamp', index }]);
  assert.equal(before.after[0], 'clamp');
  near(before.points.at(-1)[0], 0.155);
  near(after.points[0][0], 0.185);
  assert.deepEqual(after.points.at(-1), end);
  assert.throws(() => P.contacts.index(solid.mesh, { maxTriangles: 1 }), /budget/);
  assert(Object.isFrozen(index.triangles[0].p));
});

test('a ray that only grazes a solid edge does not hide a nearby curve', () => {
  const main = P.pieces.box([0, 0, 0], [1, 1, 1], identity).mesh;
  const side = P.pieces.box([-4, -2, 0], [1, 1, 1], identity).mesh;
  const index = P.contacts.index({
    positions: [...main.positions, ...side.positions],
    groups: [...main.groups, ...side.groups.map(group => ({ ...group, start: group.start + main.positions.length / 3 }))]
  });
  // From this midpoint the default containment ray touches the box at [1, -1, 0].
  const midpoint = [0, -1.371391, -0.217173];
  const start = [-0.05, midpoint[1], midpoint[2]], end = [0.05, midpoint[1], midpoint[2]];
  assert.equal(index.crossings(midpoint, [10, 2.342519, 1.954557]).length, 1);
  assert.equal(index.contains(midpoint), false);
  assert.equal(index.contains([0, 0, 0]), true);
  assert.equal(index.contains([-4, -2, 0]), true);
  const runs = P.contacts.clipCurve([start, end], [{ id: 'solid', index }]);
  assert.equal(runs.length, 1);
  assert.deepEqual(runs[0].points, [start, end]);
});

test('a contact ray returns the nearest triangle owner and surface at a physical distance', () => {
  const { KIT } = require('..').load(), P = KIT.procedural;
  const mesh = P.geometry.builder();
  for (const [height, owner] of [[0, 'ground'], [2, 'fitting']]) {
    mesh.triangle([-1, height, -1], [-1, height, 1], [1, height, 0], { owner, surface: owner + '-face' });
  }
  const index = P.contacts.index(mesh.finish());
  const hit = index.raycast([0, 5, 0], [0, -8, 0], 6);
  assert.deepEqual(hit, { p: [0, 2, 0], n: [0, 1, 0], distance: 3, owner: 'fitting', surface: 'fitting-face' });
  assert.equal(index.raycast([0, 5, 0], [0, -8, 0], 2), null);
  assert.equal(index.raycast([6, 5, 0], [0, -8, 0], 6), null);
});

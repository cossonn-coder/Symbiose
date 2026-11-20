const test = require('node:test');
const assert = require('node:assert/strict');
const P = require('..').load().KIT.procedural;
const close = (actual, expected) => assert(Math.abs(actual - expected) < 1e-6, `${actual} ≠ ${expected}`);

test('cell profiles keep the uncut coordinate when a footprint is clipped', () => {
  const layout = P.fittedCourses({ width: 2, height: 1, unit: [1, 1], joint: .1 });
  const relief = P.courseRelief(layout, { rise: .3, slope: [1, 0], profile: u => .1 + .9 * u });
  close(relief.height(.475, .5), .165);
  close(relief.top(1, .5), 0);
  close(relief.top(2.1, .5), 0);
  assert(relief.slope[0] >= .3);
  const cut = P.surfaceCells.clip(layout.cells, {
    boundary: [[.35, 0], [1.8, 0], [1.8, 1], [.35, 1]]
  });
  const seen = new Set();
  const mesh = P.surfaceCells.loft(cut, {
    sample: ([u, v], level, key) => {
      seen.add(key);
      return [u, level ? relief.height(u, v, key) : -.05, v];
    },
    metadata: key => ({ owner: key })
  }).finish();
  assert.deepEqual([...seen], ['0/0', '0/1']);
  for (const group of mesh.groups) {
    for (let i = group.start; i < group.start + group.count; i++) {
      const [u, y, v] = mesh.positions.subarray(i * 3, i * 3 + 3);
      if (y > 0) close(y, relief.height(u, v, group.owner));
    }
  }
});

test('a staggered cell keeps a continuous relief across a periodic seam', () => {
  const layout = P.fittedCourses({ width: 4, height: 2, unit: [1, 1], joint: .12, periodic: true, stagger: .5 });
  const relief = P.courseRelief(layout, { rise: .4, slope: [1, 0], profile: u => u });
  const key = layout.at(0, 1.5).id;
  assert.equal(key, layout.at(3.99, 1.5).id);
  close(relief.top(-.01, 1.5), relief.top(3.99, 1.5));
  close(relief.height(0, 1.5, key), .2);
  close(relief.height(4, 1.5, key), .2);
  assert(relief.top(3.99, 1.5) < relief.top(.01, 1.5));
  assert.throws(() => P.courseRelief(layout, { rise: .2, slope: [0, 0], profile: () => 2 }).height(0, 1.5), /zero and one/);
});

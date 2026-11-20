const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const { contacts, contours, surface } = KIT.procedural;
const square = { min: [-2, -2], max: [2, 2] };

test('marching squares stitches a closed shoreline and handles exact lattice vertices', () => {
  const [ring, ...others] = contours.march((x, z) => Math.hypot(x, z), { bounds: square, iso: 1, cell: 0.05 });
  assert.equal(others.length, 0);
  assert.equal(ring.closed, true);
  assert(ring.points.length > 100);
  assert.deepEqual(ring.points[0], ring.points.at(-1));
  assert(ring.points.every(p => Math.abs(Math.hypot(...p) - 1) < 0.001));
  const lineAtZero = contours.march(x => x, { bounds: square, cell: 0.5 });
  assert.equal(lineAtZero.length, 1);
  assert.equal(lineAtZero[0].closed, false);
  assert(lineAtZero[0].points.every(p => p[0] === 0));
});

test('marching squares uses the bilinear saddle and avoids undefined cells and oversized regions', () => {
  const bounds = { min: [0, 0], max: [1, 1] },
    field = (x, y) => ((1 - x) * 4 - x) * (1 - y) + (-(1 - x) + x * 3) * y;
  const parts = contours.march(field, { bounds, cell: 1 });
  assert.equal(parts.length, 2);
  assert(parts.some(({ points }) => points.some(p => p[1] === 0) && points.some(p => p[0] === 1)));
  assert.deepEqual(contours.march((x, y) => x === 0 && y === 0 ? null : field(x, y), { bounds, cell: 1 }), []);
  assert.throws(() => contours.march(() => 0, { bounds, cell: 0.01, maxCells: 10 }), /budget/);
});

test('a carrier chart traces a native SDF seam, then SDF exposure splits and trims it', () => {
  const wall = surface.plane({ id: 'wall', origin: [-2, -2, 0], u: [4, 0, 0], v: [0, 4, 0] }),
    sphere = (x, y, z) => Math.hypot(x, y, z) - 1;
  const [ring] = contacts.traceSdf(wall, sphere, { id: 'sphere', cell: 0.008 });
  assert(ring.closed);
  assert(ring.points.every(p => Math.abs(Math.hypot(...p) - 1) < 0.001 && p[2] === 0));

  const halves = contacts.expose([ring], x => Math.abs(x) - 0.3, { step: 0.02 });
  assert.equal(halves.length, 2);
  assert(halves.every(run => !run.closed && run.points.every(p => Math.abs(p[0]) >= 0.299999)));
  const ends = halves.flatMap(run => [run.points[0], run.points.at(-1)]);
  assert(ends.every(p => Math.abs(Math.abs(p[0]) - 0.3) < 0.000005));

  const clipped = contacts.traceSdf(wall, sphere, { occluder: () => -1 });
  assert.deepEqual(clipped, []);
});

test('nearest curve fields expose world distance, arc information, and weighted falloffs', () => {
  const points = [[-2, 0, 0], [0, 0, 0], [2, 0, 0]], data = contacts.field([{ id: 'ledge', points }]);
  points[0][1] = 5;
  const hit = data.nearest([0.5, 0.3, 0.4]);
  assert.deepEqual(hit.point, [0.5, 0, 0]);
  assert.deepEqual(hit.tangent, [1, 0, 0]);
  assert.equal(hit.distance, 0.5);
  assert.equal(hit.arc, 2.5);
  assert.equal(hit.t, 0.625);
  const masked = data.mask({ inner: 0.25, outer: 0.75, weight: (hit, p) => hit.id === 'ledge' && p[1] >= 0 ? 0.5 : 0 });
  assert.equal(masked(0, 0.5, 0), 0.25);
  assert.equal(masked(0, -0.1, 0), 0);
  assert.equal(masked(0, 0, 1), 0);
  assert.equal(contacts.field([]).distance(0, 0, 0), Infinity);
  assert.throws(() => contacts.field([points], { maxSegments: 1 }), /segment budget/);
});

test('runoff remains pinned to a sloped carrier and stops outside its projection domain', () => {
  const seam = [{ id: 'ledge', points: [[-1, 2, 0], [1, 2, 0]] }],
    project = ([x, y]) => y < 0.5 ? null : { p: [x, y, 0.25 * (2 - y)], n: [0, 0.25, 1] };
  const trails = contacts.runoff(seam, project, { spacing: 0.6, step: 0.1, distance: 3 });
  assert.equal(trails.length, 4);
  for (const run of trails) {
    assert(run.points.length > 10);
    for (const [i, [x, y, z]] of run.points.entries()) {
      assert.equal(z, 0.25 * (2 - y));
      assert(y >= 0.5);
      if (i) assert(y < run.points[i - 1][1]);
    }
  }
  assert.deepEqual(contacts.runoff(seam, p => ({ p, n: [0, 1, 0] })), []);
});

test('a contact field can drive a surface finish and signed relief in unscaled rest coordinates', () => {
  const base = [0.19, 0.19, 0.19],
    data = contacts.field([[[-2, 0, 0], [2, 0, 0]]]),
    sdf = data.sdf(0.3),
    material = KIT.surface.material({ r: [0, 1] }, {
      origin: [4, 3, -2], scale: 0.2, layers: {
        finish: { type: 'reflection', f0: 1, strength: 1, mask: data.mask({ inner: 0.05, outer: 0.2 }) }
      }
    }),
    look = KIT.surface.prepare(material.surface);
  assert(sdf(0, 0.2, 0) < 0);
  assert(sdf(0, 0.4, 0) > 0);
  const shade = position => KIT.surface.shade(look, { position, normal: [0, 0, 1], view: [1, 1, 1] }, base).slice(0, 3);
  assert.notDeepEqual(shade([0, 0, 0]), base);
  assert.deepEqual(shade([0, 0.3, 0]), base);
});

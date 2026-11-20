const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const P = KIT.procedural;
const near = (a, b) => assert(Math.abs(a - b) < 1e-6, `${a} != ${b}`);

test('affine carriers preserve attachment coordinates, normals and ray distance', () => {
  const base = P.surface.cylinder({ id: 'beam', origin: [0, 0, 0], radii: [2, 1], height: 3 });
  const carrier = P.surface.transform(
    base,
    P.transforms.local({ position: [1, 2, 3], rotation: 0.35, scale: [-1, 2, 1.5] })
  );
  const frame = carrier.sample([0.13, 0.4]);
  carrier.project(frame.p).forEach((v, i) => near(v, frame.uv[i]));
  near(KIT.V.dot(frame.n, frame.tangent), 0);
  near(KIT.V.dot(frame.n, frame.bitangent), 0);
  const hit = carrier.raycast(KIT.V.mad(frame.p, frame.n, 3), KIT.V.mul(frame.n, -1), 5);
  near(hit.distance, 3);
  assert.equal(carrier.periodicU, true);
});

test('planar position and normal samples agree through chained affine charts', () => {
  const plane = P.surface.plane({ id: 'facet', origin: [1, 0, 2], u: [2, 0, 1], v: [1, 4, 0] });
  const transformed = P.surface.transform(plane, P.transforms.local({
    position: [2, 1, -1], rotation: [.1, .3, .4], scale: [-2, 1, .5]
  }));
  const chained = P.surface.transform(transformed, P.transforms.local({ rotation: .27, scale: [1, 3, .8] }));
  for (const chart of [plane, transformed, chained]) {
    for (const at of [[0, 0], [.4, .6], [-.25, 1.2]]) {
      const { p, n } = chart.sample(at), fast = chart.samplePointNormal(at);
      assert.deepEqual(fast, { p, n });
      assert.deepEqual(chart.planePoint(at), p);
      fast.n[0] = 99;
      assert.deepEqual(chart.samplePointNormal(at).n, n);
    }
  }
});

test('convex clipping creates a material-tagged cap and feeds the existing mesh tooling', () => {
  const box = P.pieces.box([0, 0, 0], [1, 1, 1], [1, 0, 0, 0, 1, 0, 0, 0, 1], { owner: 'block', material: 'body' });
  const cut = P.geometry.clipConvex(box.mesh, [{ normal: [1, 0, 0], offset: 0.21 }], { material: 'cut' });
  const cap = cut.groups.find(g => g.material === 'cut');
  assert(cap);
  for (let i = cap.start; i < cap.start + cap.count; i++) {
    near(cut.positions[i * 3], 0.21);
    near(cut.normals[i * 3], 1);
  }
  const mesh = P.geometry.toKitMesh(cut, (owner, role) => (role === 'cut' ? [1, 0.4, 0.2] : [0.1, 0.5, 0.9]));
  assert.equal(KIT.mesh.info(mesh).tris, cut.positions.length / 9);
  assert.equal(KIT.mesh.info(mesh).open, 0);
});

test('deterministic socket matching honors compatibility and composes with catenaries', () => {
  const nodes = [
    { id: 'a', group: 'line', point: [-2, 2, 0] },
    { id: 'b', group: 'line', point: [0, 3, 0] },
    { id: 'c', group: 'line', point: [1, 2, 0] },
    { id: 'd', group: 'other', point: [-1, 2, 0] }
  ];
  const edges = P.proximity.connect(nodes, { degree: 1 });
  assert.deepEqual(
    edges,
    P.proximity.connect(nodes.toReversed ? nodes.toReversed() : nodes.slice().reverse(), { degree: 1 })
  );
  assert.equal(edges.length, 1);
  assert.deepEqual([edges[0].a, edges[0].b].sort(), ['b', 'c']);
  const span = P.spans.catenary(nodes[1].point, nodes[2].point, { sag: 0.3 });
  assert(span.length > edges[0].distance);
});

test('browser bundle provides procedural primitives without Node or document globals', () => {
  const vm = require('node:vm');
  const context = vm.createContext({});
  const result = vm.runInContext(
    require('..').bundle() + '\nKIT.procedural.fittedCourses({width: 4, height: 2, unit: [1, .5]}).cells.length',
    context
  );
  assert.equal(result, 16);
});

test('carrier operators retain source height outside the mask and can feed another operation', () => {
  const base = {
    height: x => x,
    normal: () => KIT.V.norm([-1, 1, 0]),
    inside: (x, z) => Math.abs(x) <= 2 && Math.abs(z) <= 2,
    bounds: { min: [-2, -2, -2], max: [2, 2, 2] },
    slopeBound: 1
  };
  const basin = P.basins.surface(base, (x, z) => Math.hypot(x, z) - 1, { level: 0, depth: 0.5, shore: 0.25 });
  near(basin.height(0, 0), -0.5);
  near(basin.height(1.5, 0), 1.5);
  near(base.height(0, 0), 0);
  const terrace = P.terraces.surface(basin, (x, z) =>
    z > 1.2
      ? {
          distance: -0.4,
          owner: 'slope',
          parameters: { rise: 0.4, transition: 0.02 }
        }
      : null
  );
  near(terrace.height(0.91, 1.7), 0.8);
  near(terrace.height(0.91, 1.1), 0.91);
  assert.equal(terrace.sample(0.91, 1.7).owner, 'slope');
});

test('material bands route local coordinates to metadata without imposing a palette', () => {
  const bands = P.materialBands({
    axis: 0,
    fallback: { material: 'shell' },
    layers: [{ min: -1, max: 0, material: 'inset', pattern: 'linear' }]
  });
  assert.equal(bands.at([-0.5, 8, 0]).material, 'inset');
  assert.equal(bands.at(0).material, 'shell');
  assert.deepEqual(
    bands.segments(-2, 1).map(s => [s.min, s.max, s.material]),
    [
      [-2, -1, 'shell'],
      [-1, 0, 'inset'],
      [0, 1, 'shell']
    ]
  );
});

test('repeating material bands project onto a direction and split exact intervals across negative cycles', () => {
  const diagonal = Math.SQRT1_2;
  const slabs = P.materialBands({ direction:[0,1,-1], origin:[3,1,2], period:2,
    fallback:{material:'soft'}, layers:[{min:0,max:.5,material:'seam'},{min:1,max:1.75,material:'hard'}] });
  assert.equal(slabs.atXYZ(3,1+diagonal,2).material,'soft');
  assert.equal(slabs.at([3,1,2]).material,'seam');
  assert.equal(slabs.at(-.6).material,'hard');
  assert.equal(slabs.at(2).material,'seam');
  assert.deepEqual(slabs.segments(-.75,2.5).map(({min,max,material})=>[min,max,material]),[
    [-.75,-.25,'hard'],[-.25,0,'soft'],[0,.5,'seam'],[.5,1,'soft'],[1,1.75,'hard'],
    [1.75,2,'soft'],[2,2.5,'seam']
  ]);
  assert.throws(()=>slabs.segments(0,1e7),/budget/);
});

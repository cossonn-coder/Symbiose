const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const coast = require('../examples/biome-world');
const { verticalSpans, waterBodies, sparseBricks, traversalGraph, biomeRecipes, biomeWorld } = KIT.procedural;
const close = (a, b, tolerance = 1e-5) => assert(Math.abs(a - b) < tolerance, a + ' differs from ' + b);

test('vertical spans bake independent solid and medium boundaries into compact half-open columns', () => {
  const bounds = { min: [-1, -5, -1], max: [1, 3, 1] };
  const band = (a, b) => (_, y) => Math.max(a - y, y - b);
  const grid = verticalSpans.bake({ bounds, resolution: [2, 2], solid: band(-2, -1.94), step: 0.04, volumes: [
    { id: 'aquifer', kind: 'water', field: band(-4, -1), current: [1, 0.5, -0.25] },
    { id: 'pocket', kind: 'air', priority: 1, field: band(-3, -2.45) },
    { id: 'pond', kind: 'water', field: band(0, 1.5) }
  ] });
  const rows = grid.column(0, 0);
  assert.deepEqual(rows.map(row => row.kind), ['air', 'water', 'air', 'water', 'solid', 'water', 'air', 'water', 'air']);
  close(rows[4].max, -1.94);
  assert.equal(grid.at(-0.5, rows[2].min, -0.5).id, 'pocket');
  assert.equal(grid.at(1, 0, 0), null);
  assert.equal(grid.at(0, 3, 0), null);
  const packed = grid.pack();
  assert.deepEqual([...packed.offsets], [0, 9, 18, 27, 36]);
  packed.heights.fill(0);
  assert.equal(grid.column(0, 0)[0].min, -5);

  const water = waterBodies.scene([waterBodies.fromSpans(grid, { id: 'layers' })]);
  assert.equal(water.mediumAt(0.5, -2.7, 0.5).id, 'pocket');
  assert.deepEqual(water.mediumAt(0.5, -3.5, 0.5).current, [1, 0.5, -0.25]);
  close(water.mediumAt(0.5, -3.5, 0.5).depth, 0.5);
  close(water.mediumAt(0.5, -1.5, 0.5).depth, 0.5);
  close(water.mediumAt(0.5, 0.5, 0.5).depth, 1);
  assert.throws(() => verticalSpans.bake({ bounds, solid: () => 1, maxSamples: 2 }), /sample budget/);
});

test('layered water diffs isolate separated column edits and keep tiled medium IDs', () => {
  const make = (name, x, wet) => waterBodies.fromSpans(verticalSpans.create({
    bounds: { min: [x, -1, 0], max: [x + 5, 2, 1] }, resolution: [5, 1],
    sample: (_, z, i) => [
      { kind: 'water', id: 'sea', min: -1, max: wet(i) },
      { kind: 'water', id: 'brackish', min: wet(i), max: 1.5 }
    ]
  }), { id: name });
  const first = waterBodies.scene([make('east', 5, () => 0), make('west', 0, () => 0)]);
  const next = waterBodies.scene([make('east', 5, () => 0), make('west', 0, i => i % 4 === 0 ? 1 : 0)]);
  assert.equal(next.mediumAt(5, 0.5, 0.5).id, 'brackish');
  assert.equal(next.mediumAt(0.5, 0.5, 0.5).id, 'sea');
  assert.equal(next.mediumAt(0.5, 0.5, 0.5).surface, 1.5);
  assert.deepEqual(next.changesFrom(first), [
    { min: [0, -1, 0], max: [1, 2, 1] },
    { min: [4, -1, 0], max: [5, 2, 1] }
  ]);
  const air = waterBodies.fromSpans(verticalSpans.create({
    bounds: { min: [0, -1, 0], max: [1, 2, 1] }, sample: () => [{ kind: 'air', id: 'pocket', min: -1, max: 1 }]
  }), { id: 'other-patch' });
  assert.throws(() => waterBodies.scene([make('west', 0, () => 0), air]), /bounds overlap/);
  assert.equal(waterBodies.scene([air]).mediumAt(0.5, 0, 0.5).id, 'pocket');
});

test('sparse bricks compress uniform channels, interpolate across signed brick addresses and preserve revisions', () => {
  const root = sparseBricks.create({ cell: 0.25, brickSize: 4, base: (x, y) => y + x * x });
  const uniform = root.setBrick([-1, 0, 0], { offset: -2, material: 'basalt', medium: 'pool' });
  assert.deepEqual(uniform.stats, { bricks: 1, uniform: 1, dense: 0, sculpted: 1 });
  assert.equal(uniform.distance(-0.25, 0, 0), -1.9375);
  close(uniform.distance(-0.125, 0, 0), -0.984375);
  close(uniform.distance(-1e-6, 0, 0), uniform.distance(1e-6, 0, 0));
  assert.deepEqual(root.attributes(-0.5, 0, 0), { material: null, medium: null });
  assert.equal(uniform.mediumField('pool')(-0.5, 0, 0), -1);
  assert.equal(uniform.mediumField('pool')(0.5, 0, 0), 1);
  assert.deepEqual(uniform.changesFrom(root), [{ min: [-1.25, -0.25, -0.25], max: [0, 1, 1] }]);
  const painted = uniform.edit({ bounds: { min: [-1, 0, 0], max: [-1, 0, 0] }, material: 'copper' });
  assert.equal(painted.stats.dense, 1);
  assert.equal(painted.attributes(-1, 0, 0).material, 'copper');
  assert.equal(uniform.attributes(-1, 0, 0).material, 'basalt');
  assert.deepEqual(painted.setBrick([-1, 0, 0], { offset: 0, material: null, medium: null }).changesFrom(root), []);
  assert.throws(() => root.edit({ bounds: { min: [-1, -1, -1], max: [1, 1, 1] }, material: 'a', maxSamples: 1 }),
    /sample budget/);
});

test('an XYZ cave brush changes the shared SDF, splats and wet volumes on both sides of a chunk seam', async () => {
  const view = biomeRecipes.create({ fallback: 'rock', recipes: [
    { id: 'rock', materials: { stone: [0x779088] },
      populations: [{ id: 'heath', density: 1, habitat: { media: ['air'] } }] }
  ] }).view();
  const compiler = biomeWorld.create({ height: () => 0, terrainSlope: 0, cell: 0.2, chunkCells: 20,
    verticalCells: [-12, 8], materialRamps: { copper: [0xa35f37] },
    layers: [{ id: 'ground', habitatOffset: 0.14, options: { spacing: 1, slots: 1 } }] });
  const base = compiler.prepare(view), indices = [[-1, 0], [0, 0], [3, 0]];
  await compiler.update(base, indices);
  const original = new Map(compiler.chunks().map(chunk => [chunk.key, chunk]));
  assert(original.get('3/0').placements.length > 0);
  const bounds = { min: [-1.4, -1.7, 0], max: [1.4, 1, 2.5] };
  const sphere = (x, y, z) => Math.hypot(x, y + 0.3, (z - 1.2) * 1.2);
  const bricks = sparseBricks.create({ cell: 0.2, brickSize: 4, base: base.distance })
    .edit({ bounds, operation: 'subtract', smooth: 0.12, sdf: (x, y, z) => sphere(x, y, z) - 0.72 })
    .edit({ bounds, material: 'copper', sdf: (x, y, z) => sphere(x, y, z) - 1 })
    .edit({ bounds, medium: 'pool', sdf: (x, y, z) => Math.max(sphere(x, y, z) - 0.72, y + 0.25) });
  const cut = compiler.prepare(view, { bricks });
  const grid = cut.bakeSpans({ bounds: { min: [-2, -2.4, 0], max: [2, 1.6, 4] },
    resolution: [16, 16], step: 0.08, volumes: [{ id: 'pool', kind: 'water', field: bricks.mediumField('pool') }] });
  const water = waterBodies.scene([waterBodies.fromSpans(grid, { id: 'pit' })]);
  const frame = compiler.prepare(view, { bricks, water });
  assert(base.distance(0, -0.4, 1.2) < 0);
  assert(frame.distance(0, -0.4, 1.2) > 0.4);
  assert.equal(frame.view.mediumAt(0, -0.4, 1.2).id, 'pool');
  assert.equal(frame.view.mediumAt(0, -1.25, 1.2).kind, 'solid');
  const patch = await compiler.update(frame, indices);
  assert.deepEqual(patch.replaced.map(chunk => chunk.key), ['-1/0', '0/0']);
  for (const chunk of patch.replaced) {
    assert.notDeepEqual(chunk.splats.data, original.get(chunk.key).splats.data);
    assert.deepEqual(chunk.splats.data, compiler.build(frame, chunk.index).splats.data);
    const copper = 0x375fa3;
    assert(chunk.splats.data.some((value, index) => index % 16 === 7 && value === copper));
  }
  const [left, right] = patch.replaced;
  for (const y of [-0.8, -0.6, -0.4, 0]) close(left.field.sample(0, y, 1.2), right.field.sample(0, y, 1.2));
  const far = compiler.chunks().find(chunk => chunk.key === '3/0');
  assert.equal(far, original.get(far.key));
  assert.deepEqual(far.splats.ids, compiler.build(frame, far.index).splats.ids);
  assert.deepEqual(far.placements, compiler.build(frame, far.index).placements);
  const undone = await compiler.update(base, indices);
  for (const chunk of undone.replaced) assert.deepEqual(chunk.splats.data, original.get(chunk.key).splats.data);
});

test('traversal separates stacked rooms and provides directed climbs and drops', () => {
  const tile = (x, raised) => verticalSpans.create({ bounds: { min: [x, -1, 0], max: [x + 1, 6, 1] },
    sample: () => [
      { kind: 'solid', min: -1, max: raised ? 0.7 : 0 },
      { kind: 'solid', min: 2, max: 2.7 }
    ]
  });
  const options = { tiles: [tile(0, false), tile(1, true)], radius: 0.14, height: 0.5, stepUp: 0.25 };
  const noClimb = traversalGraph.create(options);
  const graph = traversalGraph.create({ ...options, canClimb: (from, to) => to.point[0] > from.point[0] });
  const [low, roof, ledge, farRoof] = graph.nodes;
  assert.equal(noClimb.route(low.id, ledge.id).reason, 'disconnected');
  assert.equal(graph.route(low.id, ledge.id).edges[0].mode, 'climb');
  assert.equal(graph.route(ledge.id, low.id).edges[0].mode, 'drop');
  assert.equal(graph.route(roof.id, farRoof.id).edges[0].mode, 'walk');
  assert.equal(graph.route(low.id, roof.id).reason, 'disconnected');
  assert(graph.edges.every(edge => edge.crossTile));
  assert.throws(() => traversalGraph.create({ ...options, tiles: [options.tiles[0], tile(1.25, true)] }), /aligned/);
});

test('the headless coast routes from ridge to named air chamber across seams and explains a rising tide', () => {
  const fixture = coast(KIT);
  function graph(level) {
    const { frame, tiles } = fixture.layered(level);
    return { frame, graph: frame.traversalGraph({ tiles, radius: 0.14, height: 0.48, stepUp: 0.33 }) };
  }
  const first = graph(0.38), high = graph(0.9), current = first.graph;
  const start = current.nodes.find(node => node.point[0] === -13.75 && node.point[2] === 0.75 && node.supported);
  const end = current.nodes.find(node => node.point[0] === 8.75 && node.point[2] === 0.75 && node.mediumId === 'chamber-air');
  const trip = current.route(start.id, end.id);
  assert(trip.ok);
  assert(trip.edges.filter(edge => edge.crossTile).length >= 5);
  assert(trip.edges.some(edge => edge.mode === 'walk'));
  assert(trip.edges.some(edge => edge.mode === 'swim'));
  assert.equal(current.route(start.id, end.id, { allow: ['walk'] }).reason, 'disconnected');
  const trace = first.frame.traceRoute(trip.points, { radius: 0.11 });
  assert(trace.ok);
  assert.deepEqual(trace.media.map(({ kind, id }) => [kind, id]), [
    ['air', null], ['water', 'coast-water'], ['air', 'chamber-air']
  ]);
  const delta = high.graph.changesFrom(current);
  assert(delta.some(change => change.reason === 'flooded' && change.before === 'walk' && change.after === 'swim'));
  assert(current.changesFrom(high.graph).some(change => change.reason === 'drained'));
  assert.deepEqual(current.changesFrom(current), []);
});

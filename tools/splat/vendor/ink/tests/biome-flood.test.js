const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const floodValley = require('../examples/biome-flood');
const { spanFlood, verticalSpans, waterBodies, traversalGraph, biomeWorld, biomeRecipes } = KIT.procedural;
const bounds = x => ({ min: [x, -4, 0], max: [x + 1, 3, 1] });

test('tiled span baking retains immutable grids and rebakes moved, removed, or dirty tiles', () => {
  const tiles = [0, 1, 2].map(x => ({ id: String(x), bounds: bounds(x) }));
  const first = verticalSpans.bakeTiles({ tiles, solid: (_, y) => y });
  const second = verticalSpans.bakeTiles({
    tiles: [tiles[0], tiles[1]], previous: first, dirtyBounds: [{ min: [1.2, -1, 0], max: [1.8, 1, 1] }],
    solid: (x, y) => y + (x > 1.2 ? 0.5 : 0)
  });
  assert.deepEqual(second.work.rebuilt, ['1']);
  assert.deepEqual(second.work.removed, ['2']);
  assert.equal(second.tiles[0], first.tiles[0]);
  assert.equal(second.tiles[1].at(1.5, -0.25, 0.5).kind, 'air');
  assert.equal(first.tiles[1].at(1.5, -0.25, 0.5).kind, 'solid');
  const rebaked = verticalSpans.bakeTiles({ tiles, solid: (_, y) => y, previous: first, dirtyBounds: [bounds(1)] });
  assert(rebaked.work.rebuilt.length > 0);
  assert.deepEqual(rebaked.work.changed, []);
  assert(rebaked.tiles.every((tile, i) => tile === first.tiles[i]));
  const moved = verticalSpans.bakeTiles({ tiles: [tiles[0], { ...tiles[1], bounds: bounds(2) }],
    previous: second, dirtyBounds: [], solid: (_, y) => y });
  assert.deepEqual(moved.work.rebuilt, ['1']);
  assert(moved.tiles[1].at(2.5, 0.5, 0.5));
});

test('fixed-head fill crosses only openings below its head and unwets disconnected volumes', () => {
  const column = (x, floor) => verticalSpans.create({ bounds: bounds(x), sample: () => [
    { min: -4, max: floor, kind: 'solid' }, { min: floor, max: 1, kind: 'air', id: 'hall' }
  ] });
  const left = column(0, -3), sill = column(1, -0.5), chamber = column(2, -3), far = column(5, -3);
  const sources = [{ id: 'cistern', point: [0.5, -2, 0.5], level: -1, current: [0, 0, 1] }];
  const first = spanFlood.create({ tiles: [left, sill, chamber, far], sources });
  assert.equal(first.tiles[2].at(2.5, -2, 0.5).id, 'hall');
  const opened = column(1, -1.5);
  const flooded = spanFlood.create({ tiles: [left, opened, chamber, far], sources, previous: first });
  assert.equal(flooded.tiles[0], first.tiles[0]);
  assert.equal(flooded.tiles[3], first.tiles[3]);
  assert.deepEqual(flooded.work.topologyTiles, ['1/0']);
  assert.deepEqual(flooded.work.waterTiles, ['1/0', '2/0']);
  assert.equal(flooded.tiles[2].at(2.5, -2, 0.5).id, 'cistern');
  assert.equal(flooded.tiles[2].at(2.5, -1, 0.5).id, 'hall');
  const scene = waterBodies.sceneFromSpans(flooded.tiles);
  assert.deepEqual(scene.mediumAt(2.5, -2, 0.5).current, [0, 0, 1]);
  assert.equal(waterBodies.sceneFromSpans(flooded.tiles, { previous: scene }), scene);

  const again = spanFlood.create({ tiles: [left, sill, chamber, far], sources, previous: flooded });
  assert.equal(again.tiles[2], chamber);
  assert.equal(again.tiles[2].at(2.5, -2, 0.5).id, 'hall');
  const high = { id: 'spring', point: [2.5, -2, 0.5], level: 0 };
  const connected = spanFlood.create({ tiles: [left, sill, chamber, far], sources: [...sources, high] });
  assert.equal(connected.tiles[0].at(0.5, -2, 0.5).id, 'spring');
  assert.equal(connected.tiles[3], far);
});

test('traversal retains far nodes and invalidates links when tiles stream in or out', () => {
  const column = x => verticalSpans.create({ bounds: bounds(x), sample: () => [{ min: -4, max: 0, kind: 'solid' }] });
  const [a, b, c, far] = [0, 1, 2, 7].map(column);
  const options = { origin: [0, 0], radius: 0.12, height: 0.48 };
  const first = traversalGraph.create({ ...options, tiles: [a, b, c, far] });
  const farNode = first.nodes.find(n => n.point[0] === 7.5);
  const from = first.nodes.find(n => n.point[0] === 0.5), to = first.nodes.find(n => n.point[0] === 2.5);
  assert(first.route(from.id, to.id).ok);
  const removed = traversalGraph.create({ ...options, tiles: [c, far, a], previous: first });
  assert.equal(removed.route(from.id, to.id).reason, 'disconnected');
  assert.equal(removed.nodes.find(n => n.id === farNode.id), farNode);
  const next = traversalGraph.create({ ...options, tiles: [far, c, a, b], previous: removed });
  assert(next.route(from.id, to.id).ok);
  assert.deepEqual(next.edges, first.edges);
  assert(next.work.checks < first.work.checks);

  const clearance = (_, y) => y;
  const ready = traversalGraph.create({ ...options, tiles: [a, b, c, far], clearance });
  const blocked = traversalGraph.create({ ...options, tiles: [a, b, c, far], previous: ready,
    clearance: (x, y) => Math.min(y, Math.abs(x - 1) - 0.08),
    dirtyBounds: [{ min: [0.9, 0, 0], max: [1.1, 2, 1] }] });
  assert.equal(blocked.route(from.id, to.id).reason, 'disconnected');
  assert.equal(blocked.nodes.find(n => n.id === farNode.id), ready.nodes.find(n => n.id === farNode.id));
});

test('one seam edit floods the lower route and incremental and cold worlds are identical', async () => {
  const fixture = floodValley(KIT), before = await fixture.build();
  const after = await fixture.build(fixture.brush(), { previous: before });
  const other = floodValley(KIT), cold = await other.build(other.brush());
  const { keys } = fixture;
  const medium = (stage, key) => stage.frame.view.mediumAt(...keys[key]);
  assert.equal(medium(before, 'floodedHall').kind, 'air');
  assert.equal(medium(after, 'floodedHall').id, 'reservoir');
  assert.equal(medium(after, 'floodedHall').surface, -3.25);
  assert.equal(medium(after, 'lake').id, 'lake');
  assert.deepEqual(medium(after, 'lake'), medium(before, 'lake'));
  assert.equal(medium(after, 'upperRoute').kind, 'air');
  assert.equal(medium(after, 'dryChamber').kind, 'air');
  assert.equal(before.frame.view.mediumAt(0, -4.3, 1.25).kind, 'solid');
  assert.equal(after.frame.view.mediumAt(0, -4.3, 1.25).id, 'reservoir');

  for (const stage of [before, after]) {
    const { graph } = stage;
    const first = graph.route(keys.routeStart, keys.floodedHall), second = graph.route(keys.floodedHall, keys.routeEnd);
    const upper = graph.route(keys.routeStart, keys.routeEnd, { allow: ['walk'] });
    assert(first.ok && second.ok && upper.ok);
    assert.equal(first.nodes[0].id, upper.nodes[0].id);
    assert.equal(second.nodes.at(-1).id, upper.nodes.at(-1).id);
    assert.equal(first.nodes.at(-1).id, second.nodes[0].id);
    assert(upper.edges.every(edge => edge.mode === 'walk'));
    assert.equal([...first.edges, ...second.edges].some(edge => edge.mode === 'swim'), stage === after);
    assert.equal(graph.route(keys.reservoir, keys.floodedHall).ok, stage === after);
  }
  assert(after.graph.changesFrom(before.graph).some(c => c.before === 'walk' && c.after === 'swim' && c.reason === 'flooded'));

  assert.deepEqual(after.spans.tiles.map(tile => tile.pack()), cold.spans.tiles.map(tile => tile.pack()));
  assert.deepEqual(after.flood.tiles.map(tile => tile.pack()), cold.flood.tiles.map(tile => tile.pack()));
  assert.deepEqual(after.graph.nodes, cold.graph.nodes);
  assert.deepEqual(after.graph.edges, cold.graph.edges);
  assert.deepEqual(after.water.pack(), cold.water.pack());
  assert.deepEqual(after.world.data, cold.world.data);
  assert.deepEqual(after.world.splatIds, cold.world.splatIds);
  assert.deepEqual(after.chunks.map(chunk => chunk.placements), cold.chunks.map(chunk => chunk.placements));

  assert(after.spans.work.rebuilt.length < cold.spans.work.rebuilt.length);
  assert(after.flood.work.topologyTiles.length < cold.flood.work.topologyTiles.length);
  assert(after.graph.work.relinked.length < cold.graph.work.relinked.length);
  assert(after.graph.work.checks < cold.graph.work.checks);
  assert(after.patch.replaced.length < cold.patch.replaced.length);
  const unchanged = before.chunks.find(chunk => chunk.key === '4/2');
  assert(unchanged.placements.length > 0);
  assert.equal(after.chunks.find(chunk => chunk.key === unchanged.key), unchanged);
  const far = before.graph.nodes.find(node => node.point[0] > 16);
  assert.equal(after.graph.nodes.find(node => node.id === far.id), far);
});

test('surface scatter keeps lattice IDs and relocates splat centers along the SDF', () => {
  const view = biomeRecipes.create({ fallback: 'stone', recipes: [
    { id: 'stone', materials: { rock: [0x779088] } }
  ] }).view();
  const build = surfaceScatter => {
    const compiler = biomeWorld.create({ height: () => 0, cell: 0.25, chunkCells: 8, surfaceScatter });
    const frame = compiler.prepare(view);
    return [[-1, 0], [0, 0]].map(index => compiler.build(frame, index).splats);
  };
  const regular = build(0), scattered = build(0.24), repeated = build(0.24);
  for (let i = 0; i < regular.length; i++) {
    const original = regular[i], shifted = scattered[i];
    assert.deepEqual(shifted.ids, original.ids);
    assert.deepEqual(shifted.data, repeated[i].data);
    assert(shifted.data.some((v, j) => j % 16 === 0 && v !== original.data[j]));
    for (let j = 0; j < shifted.data.length; j += 16) {
      assert(Math.abs(shifted.data[j + 1]) < 1e-5);
      assert(Math.hypot(shifted.data[j] - original.data[j], shifted.data[j + 2] - original.data[j + 2]) < 0.09);
    }
  }
});

const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const { biomeWorld, biomeRevisions, biomeRecipes } = KIT.procedural;

test('a failed publication leaves the world, history and geometry cache on the last complete revision', async () => {
  const author = biomeRecipes.create({ fallback: 'land', recipes: [{ id: 'land', materials: { stone: [0x56626d] } }] });
  const view = author.view();
  const compiler = biomeWorld.create({ height: () => 0, cell: 0.25, chunkCells: 4, verticalCells: [-6, 8] });
  const indices = [[0, 0], [1, 0], [8, 0]];
  const tiles = indices.map(([x, z]) => ({ id: String(x), resolution: [2, 2],
    bounds: { min: [x, -1.5, z], max: [x + 1, 2, z + 1] } }));
  const sources = [{ id: 'pool', point: [0.25, 0.3, 0.25], level: 0.9 }];
  const world = biomeRevisions.create({ compiler, tiles, indices, historyLimit: 2, brushGrid: { cell: 0.25, brickSize: 4 },
    agent: { radius: 0.12, height: 0.4, origin: [0, 0] },
    derive(staged, previous) {
      assert.equal(staged.frame.water, staged.world.water);
      assert.equal(staged.graph, staged.world.traversalGraph);
      if (staged.world.radius === 3) throw new Error('creator rejected the staged revision');
      return Object.freeze({ previous: previous?.id ?? null, count: staged.world.count });
    } });
  const first = await world.commit({ view });
  assert.equal(first.extra.count, first.world.count);
  assert.equal(first.frame.view.mediumAt(0.25, 0.25, 0.25).kind, 'air');
  await assert.rejects(world.commit({ sources, meta: { radius: 3 } }), /creator rejected/);
  assert.equal(world.current(), first);
  assert.equal(await world.undo(), null);
  assert.equal(compiler.frame(), null);

  const wet = await world.commit({ sources });
  assert.equal(wet.id, 2);
  assert.equal(wet.extra.previous, first.id);
  assert.equal(wet.frame.view.mediumAt(1.25, 0.25, 0.25).id, 'pool');
  const query = KIT.world.query.fromScene(wet.world);
  assert.equal(query.probe('water/water', [1.25, 0.25, 0.25]).value.id, 'pool');
  assert.equal(first.frame.view.mediumAt(1.25, 0.25, 0.25).kind, 'air');
  assert(wet.patch.replaced.length > 0);
  assert(wet.patch.replaced.every(chunk => chunk.work.reusedSurface));
  assert.equal(wet.chunks.find(chunk => chunk.key === '8/0'), first.chunks.find(chunk => chunk.key === '8/0'));

  const stroke = x => ({ operation: 'paint', material: 'marker', bounds: { min: [x, 0, 0.5], max: [x, 0, 0.5] } });
  const [left, right] = await Promise.all([world.sculpt(stroke(0.5)), world.sculpt(stroke(1.5))]);
  assert.equal(left.bricks.attributes(1.5, 0, 0.5).material, null);
  assert.equal(right.bricks.attributes(0.5, 0, 0.5).material, 'marker');
  assert.equal(right.bricks.attributes(1.5, 0, 0.5).material, 'marker');
  assert.equal(await world.undo(), left);
  assert.equal(await world.undo(), wet);
  assert.equal(await world.redo(), left);
  assert.equal(await world.redo(), right);
  assert.equal(await world.undo(), left);
  const branch = await world.commit({ sources: [] });
  assert.equal(branch.id, 5);
  assert.equal(await world.redo(), null);
  assert.equal(branch.frame.view.mediumAt(1.25, 0.25, 0.25).kind, 'air');
});

test('point lighting admits creator palettes and falls off in world space', () => {
  const shade = biomeWorld.pointLighting({ lights: [{ point: [1, 2, 3], radius: 2,
    color: [1, 0, 0], strength: 2, wrap: 0 }] });
  const base = [60, 65, 85], point = [1, 1, 3];
  const near = shade(base, { point, normal: [0, 1, 0] });
  assert(near[0] > base[0] && near[1] === base[1] && near[2] === base[2]);
  assert.deepEqual(shade(base, { point, normal: [0, -1, 0] }), base);
  assert.deepEqual(shade(base, { point: [5, 1, 3], normal: [0, 1, 0] }), base);
});

const assert = require('node:assert/strict');
const test = require('node:test');
const studio = require('../index.js');
const { makeBuilder, makeSculpt, ArtPasses } = studio.load();

const camera = { target: [0, 0, 0], dist: 5, yaw: 0, pitch: 0 };
const view = { w: 41, h: 41, px: 1, ortho: true };

test('art passes expose a consistent visible surface and composite only visible emission', () => {
  const builder = makeBuilder(1, [0, 0xff4000, 0x5080aa, 0xffffff]);
  builder.disc(0, 0, -1, [0, 0, 1], 0.4, 0.03, builder.P[1], 3, { em: true });
  builder.describeSplats(0, 1, { object: 'torch', material: 'fire' });
  builder.disc(0, 0, 0, [0, 0, 1], 0.18, 0.02, builder.P[2], 3);
  builder.describeSplats(1, 2, { object: 'wall', material: 'stone' });
  builder.disc(0, 0, 1, [0, 0, 1], 0.1, 0.02, builder.P[3], 0.2, { em: true, emission: false, nd: true });
  const world = builder.finish({ cam: camera });

  const original = studio.render(world, view);
  const frame = studio.render(world, { ...view, passes: true });
  const { coverage, depth, normal, objectId, materialId, emission, splatId, objects, materials } = frame.passes;
  const center = 20 * 41 + 20;
  assert.deepEqual(frame.rgb, original.rgb);
  assert(coverage[center] > 0.99);
  assert.equal(depth[center], 37);
  assert.deepEqual(Array.from(normal.subarray(center * 3, center * 3 + 3)), [0, 0, 1]);
  assert.equal(objects[objectId[center]], 'wall');
  assert.equal(materials[materialId[center]], 'stone');
  assert.equal(splatId[center], 2);
  assert(emission[center * 3] < 0.02);
  assert(emission.some(value => value > 0.9));
  assert.equal(depth[0], Infinity);
  assert.equal(coverage[0], 0);
  assert.equal(objectId[0], 0);
  assert.deepEqual(studio.render(world, { ...view, passes: ['coverage'] }).passes, { w: 41, h: 41, coverage });
  assert.throws(() => studio.render(world, { ...view, passes: ['light'] }), /Unknown art pass/);
  const colored = studio.render(world, { ...view, colored: true, passes: true });
  assert.deepEqual(colored.passes, frame.passes);
});

test('sculpt tags and material identities reach the public pass API', () => {
  const builder = makeBuilder(2, [0, 0x405060, 0xdcd0aa]);
  const sculpt = makeSculpt(builder);
  sculpt.ball([0, 0.5, 0], 0.3, { r: [1, 2], materialId: 'granite' }, { tag: 'crown', res: 0.055 });
  sculpt.bake();
  const world = builder.finish({ cam: camera });
  const { passes } = studio.render(world, { ...view, passes: true });
  const hit = 14 * view.w + 20;
  assert.equal(passes.objects[passes.objectId[hit]], 'crown');
  assert.equal(passes.materials[passes.materialId[hit]], 'granite');
  assert(passes.normal[hit * 3 + 2] > 0.7);
  assert(!passes.objectId.slice(23 * view.w).some(Boolean));
  assert.equal(ArtPasses.ownsSurface(.5, true, 1, Infinity), false);
  assert.equal(ArtPasses.ownsSurface(.51, true, 1, Infinity), true);
  assert.equal(ArtPasses.ownsSurface(.99, true, 2, 1), false);
});

test('surface ordering resolves crossovers and falls back atomically under a low budget', () => {
  const b = makeBuilder(1, [0, 0xee6644, 0x44aadd]);
  const norm = Math.SQRT1_2;
  b.disc(0, 0, .04, [-norm, 0, norm], .72, .009, b.P[1], 3);
  b.disc(0, 0, 0, [norm, 0, norm], .72, .009, b.P[2], 3);
  const world = b.finish({ cam: camera });
  const options = { w: 64, h: 64, px: 1, ortho: true, raw: true, passes: ['splatId'] };
  const center = studio.render(world, options);
  const resolved = studio.render(world, { ...options, splatOrder: 'surface' });
  const capped = studio.render(world, { ...options, splatOrder: 'surface', fragmentBudget: 11 });
  const left = 32 * 64 + 27, right = 32 * 64 + 37;
  assert.equal(center.passes.splatId[left], 1);
  assert.equal(resolved.passes.splatId[left], 2);
  assert.equal(resolved.passes.splatId[right], 1);
  assert(resolved.rgb[left * 3 + 2] > resolved.rgb[left * 3]);
  assert(capped.orderFallback);
  assert.deepEqual(capped.rgb, center.rgb);
  assert.deepEqual(capped.passes, center.passes);
});

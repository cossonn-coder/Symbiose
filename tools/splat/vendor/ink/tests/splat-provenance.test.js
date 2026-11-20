const assert = require('node:assert/strict');
const test = require('node:test');
const studio = require('../index.js');
const api = studio.load();
const { KIT: K, SplatProvenance, TargetSelectors, makeBuilder, makeSculpt } = api;
const { procedural: P, world: W } = K;
const cam = { target: [0, 0, 0], dist: 5, yaw: 0, pitch: 0 };
const pal = [0x121929, 0x626262, 0xcacaca];
const view = { w: 96, h: 72, px: 1, ortho: true };
const tint = (name, offset) => ({ name, steps: [{
  type: 'channelMix', matrix: [[0, 0, 0], [0, 0, 0], [0, 0, 0]], offset
}] });

function lookOf(world, select) {
  return W.query.fromScene(world).probe('look/provenance', select).value.targets[0];
}

test('bakes use authored identifiers on identical ramps and carry effective top materials', () => {
  const spec = { id: 'stable-ids', solids: [
    { id: 'west', kind: 'box', at: [-.52, 0, 0], half: [.3, .3, .3], mat: { ramp: [1, 2], materialId: 'steel', surfaceId: 'trim' } },
    { id: 'east', kind: 'box', at: [.52, 0, 0], half: [.3, .3, .3], surfaceId: 'trim', mat: { ramp: [1, 2], materialId: 'enamel' } }
  ] };
  const first = K.diorama.build(spec);
  const next = K.diorama.build({ ...spec, solids: spec.solids.slice().reverse().map(row => ({ ...row, res: .14 })) });
  const select = { entity: 'west', surface: 'trim', material: 'steel' };
  for (const world of [first, next]) {
    assert.equal(lookOf(world, select).surfaceId, 'trim');
    assert.equal(lookOf(world, select).materialId, 'steel');
  }
  const B = makeBuilder(8, pal), S = makeSculpt(B);
  S.box([0, 0, 0], [.8, .5, .65], { r: [1], materialId: 'base', top: { min: .65, r: [2],
    materialId: 'polished', surfaceId: 'top' } }, { objectId: 'tile', res: .08 });
  S.bake();
  const world = B.finish({ cam });
  assert(lookOf(world, { object: 'tile', surface: 'top' }).count > 0);
  assert.equal(lookOf(world, { object: 'tile', surface: 'top' }).materialId, 'polished');
  assert(lookOf(world, { object: 'tile', material: 'base' }).count > 0);
});

test('retained chunks remap local lookup slots and retain surface shader bindings across a rebake', async () => {
  const chunks = P.chunks.create({ preview({ key, input: offset }) {
    const B = makeBuilder(5, pal);
    B.surfaceNext({ id: 'coil', renderStages: [{ stage: 'lit', stack: tint(key, key === 'left' ? [0, 0, 1] : [1, 0, 0]) }] },
      0, 0, 1, [0, 1, 0]);
    B.disc(offset, 0, 0, [0, 0, 1], .50, .017, B.P[2], 3);
    B.describeSplats(0, 1, { object: key, material: 'enamel', target: { surface: 'coil', tags: [key] } });
    B.describeAlbedo(0, 1, 2);
    return B.finish();
  } });
  const requests = [{ key: 'left', revision: 1, input: -.80 }, { key: 'right', revision: 1, input: .80 }];
  await chunks.update(requests, { quality: 'preview' });
  const retained = chunks.entries().find(row => row.key === 'left').value;
  const assemble = () => SplatProvenance.join(chunks.entries().map(row => row.value).reverse(),
    { cam, detail: 18, radius: 4, dither: 0, fog: { c: 0, start: 1, max: 0 } });
  for (let pass = 0; pass < 2; pass++) {
    const world = assemble();
    const index = TargetSelectors.index(world);
    assert.notEqual(world.surfaceData[0], world.surfaceData[8]);
    assert.equal(world.materialAlbedo[0], 0xcacacb);
    assert.equal(world.materialAlbedo[1], 0xcacacb);
    assert.equal(index.row(0).object, 'right');
    assert.equal(index.row(1).object, 'left');
    assert.equal(lookOf(world, { material: 'enamel', surface: 'coil', tag: 'left' }).object, 'left');
    const image = studio.render(world, view).rgb;
    assert(image.some((n, i) => i % 3 === 0 && n > 240 && image[i + 2] < 5));
    assert(image.some((n, i) => i % 3 === 0 && n < 5 && image[i + 2] > 240));
    if (!pass) await chunks.update([requests[0], { ...requests[1], revision: 2, input: 1.05 }], { quality: 'preview' });
  }
  assert.equal(chunks.entries().find(row => row.key === 'left').value, retained);
});

test('offline and interactive LOD preserve named surface and prefab scopes at a shared seam', () => {
  const raw = ['seam', 'panel'].flatMap((surface, group) => [0, 1].map(i => ({
    id: surface + i, position: [group * .018 + i * .012, 0, 0], normal: [0, 0, 1],
    color: [.6, .6, .6], radius: .08, owner: 'relay', material: 'steel', surface,
    target: { prefabs: ['west'], tags: [surface] }
  })));
  const options = { ratio: .5, lockSeams: false, maxDistance: .15, maxRadius: .15 };
  const base = P.lod.mergeSplats(raw, { ratio: 1 });
  const packed = P.lod.packSplats(base);
  const coarse = P.lod.packSplats(P.lod.mergeSplats(raw, options));
  assert.equal(coarse.count, 2);
  assert.equal(lookOf(coarse, { material: 'steel', prefab: 'west', surface: 'seam' }).count, 1);
  assert.equal(lookOf(coarse, { tag: 'panel' }).surfaceId, 'panel');
  assert.deepEqual(coarse.splatIds, ['seam0', 'panel0']);

  const world = P.lod.reduceWorld(packed, options);
  assert.equal(world.count, 2);
  assert.equal(lookOf(world, { surface: 'panel' }).materialId, 'steel');
  assert.equal(lookOf(world, { surface: 'seam' }).object, 'relay');
  const level = K.splatInteractionDetail.compile(packed, .25);
  assert.equal(level.indices.length, 2);
  const selected = SplatProvenance.subset(packed, level.indices);
  assert.equal(lookOf(selected, { surface: 'seam' }).count, 1);
  assert.equal(lookOf(selected, { surface: 'panel' }).count, 1);
});

test('a prefab appearance override keeps the same selector and stable IDs in a reduced bake', () => {
  const demo = require('../examples/provenance-relays.js')(api);
  const full = demo.build(demo.seed), rebaked = demo.build(demo.seed, { controls: { variant: 'rebaked' } });
  const coarse = P.lod.reduceWorld(rebaked, { ratio: .7, maxDistance: .093, maxRadius: .105 });
  const selector = { prefab: 'east', material: 'enamel', surface: 'housing' };
  for (const world of [full, rebaked, coarse]) {
    const row = lookOf(world, selector);
    assert.equal(row.entity, 'east.body');
    assert.equal(row.surfaceId, 'housing');
    assert.equal(row.materialId, 'enamel');
  }
  assert(coarse.count < rebaked.count);
  assert.notDeepEqual(studio.render(full, view).rgb, studio.render(rebaked, view).rgb);
  const query = W.query.fromScene(coarse);
  const paint = query.probe('look/output', selector, { stage: 'lit', rgb: [.5, .5, .5] }).value.targets[0];
  assert.equal(paint.stages.lit[0].asset, 'relay/ochre');
  assert.equal(paint.stages.lit[0].effectiveWeight, .88);
});

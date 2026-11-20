const assert = require('node:assert/strict');
const test = require('node:test');
const studio = require('../index.js');
const kit = studio.load(), { KIT: K, SplatEffects, makeBuilder, PixelLook } = kit;
const { authoring: A, world: W } = K;

test('mask samplers distinguish world and rest points and reuse projected channels and raster frames', () => {
  const sample = { position: [.25, .25, .75], worldPosition: [.25, .75, .75], time: 0 };
  const axis = space => SplatEffects.prepareMask({ type: 'axis', space, interpolation: 'linear' })(sample);
  assert.equal(axis('world'), .75);
  assert.equal(axis('rest'), .25);
  let reads = 0;
  const source = { fields: { layer: { channels: ['wear'], frame() {
    reads++;
    return { sample: (_channel, u, v) => v - u };
  } } } };
  const field = SplatEffects.prepareMask({ type: 'field', field: 'layer', channel: 'wear',
    range: [0, 1], interpolation: 'linear' }, source);
  assert.equal(field(sample), .5);
  assert.equal(field(sample), .5);
  assert.equal(reads, 1);
  const texture = SplatEffects.prepareMask({
    type: 'texture', channel: 'red', interpolation: 'linear',
    raster: { width: 2, height: 1, frames: [[255, 0, 0, 128, 0, 0, 0, 255], [0, 0, 0, 255, 255, 0, 0, 255]] }
  });
  assert.equal(texture(sample), 128 / 255);
  assert.equal(texture({ ...sample, time: 1 }), 0);
  assert.equal(texture({ position: [1.3, 0, 0] }), 0);
  const data = { query: { probe: (_key, point) => point[1] < 0 ? { status: 'missing' } :
    { status: 'ok', value: { water: { wetness: point[1] } } } } };
  const query = SplatEffects.prepareMask({ type: 'query', field: 'river/water', path: ['water', 'wetness'], invert: true }, data);
  assert.equal(query({ worldPosition: [0, .5, 0] }), .5);
  assert.equal(query({ worldPosition: [0, -1, 0] }), 0);
  assert.throws(() => SplatEffects.prepareMask({ type: 'axis', range: [1, 0] }), /increasing/);
});

const stack = { name: 'Damp', steps: [{ type: 'exposure', stops: -1 }] };
const mask = { type: 'axis', space: 'world', range: [-.65, .65], invert: true };
const pack = { format: 'ink-studio/asset-pack', id: 'mask', title: 'Masks', version: 1, revision: 1, looks: [
  { id: 'mask/damp', label: 'Damp', stack, mask }
] };
test('asset masks apply to scenes, material bindings and shared targets', () => {
  const catalog = A.assetPacks.create({ packs: [pack] }), id = 'mask/damp';
  const adjusted = A.looks.bind({ asset: id, mask: false }, catalog);
  assert.equal(adjusted.mask, undefined);
  assert.equal(A.looks.bind(id, catalog).mask.type, 'axis');
  assert.equal(A.assetPacks.reviseLook(pack, id, { mask: { ...mask, space: 'rest' } }).revision, 2);
  const select = { entity: 'stone' };
  const scope = [
    { look: A.looks.scene({ asset: id }, catalog) },
    { look: A.looks.scene({ targets: [{ select, asset: id }] }, catalog) },
    { surface: A.looks.material({}, id, catalog).surface }
  ];
  for (const { look, surface } of scope) {
    const B = makeBuilder(1, [0x101421, 0xe0e0e0]);
    if (surface) B.surfaceNext(surface, 0, 0, 1, [0, 1, 0]);
    B.disc(0, 0, 0, [0, 0, 1], .63, .03, B.P[1], 3);
    B.describeSplats(0, 1, { object: 'stone' });
    const world = B.finish({ cam: { target: [0, 0, 0], dist: 4.8, yaw: 0, pitch: 0 }, look });
    for (const options of [{}, { colored: true }, { stable: { resolve: 'coverage' } }]) {
      const view = { w: 72, h: 72, px: 1, ortho: true, ...options };
      const active = studio.render(world, view), dry = studio.render(world, { ...view, lookMasks: false });
      const point = (36 * 72 + 36) * 3;
      assert(dry.rgb[point] > active.rgb[point] && active.rgb[point] > 112);
      assert.equal(active.rgb[0], dry.rgb[0]);
    }
    const row = W.query.fromScene(world).probe('look/output', select, { at: [0,0,0], rgb: [.8,.8,.8] }).value.targets[0];
    assert.equal(row.maskWeight, .5);
  }
  const options = { palette: [0, 0xffffff], skipMasks: true };
  assert.equal(PixelLook.preparePaletteConstraints({ default: { stack, mask } }, options), null);
});

test('a simulation look reads query-backed wetness from its current visual snapshot', () => {
  const world = { systems: { spring: { kind: 'fields', config: { fields: { wetness: { default: .5 } } } } },
    entities: { wall: { position: [0,.6,0], visual: { half: [.5,.5,.3], surfaceId: 'wall' } } }, assetPacks: [pack],
    visual: { look: { targets: [{ select: { surface: 'wall' }, asset: 'mask/damp',
      mask: { type: 'query', field: 'spring/wetness', interpolation: 'linear' } }] } } };
  const run = W.runtime.create(world);
  const result = run.query().probe('look/output', { surface: 'wall' }, { at: [0,.5,0], rgb: [.6,.6,.6] });
  assert.equal(result.value.targets[0].maskWeight, .5);
});

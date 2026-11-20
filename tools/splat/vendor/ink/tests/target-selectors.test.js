const assert = require('node:assert/strict');
const test = require('node:test');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const studio = require('../index.js');
const kit = studio.load(), { KIT, TargetSelectors, PixelLook, makeBuilder, SceneOptics } = kit;
const { world: W, authoring: A } = KIT;

test('a saved render selector works unchanged for validation and probe output', () => {
  const root = path.resolve(__dirname, '..'), file = 'examples/shared-look-selectors.js';
  const cli = (...args) => JSON.parse(execFileSync(process.execPath, [path.join(root, 'cli/ink-studio.js'), ...args],
    { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }));
  const select = { tag: 'paint-sample', material: 'bone' }, json = JSON.stringify(select);
  const inspected = cli('inspect', file, '--select', json);
  assert.equal(inspected.targets[0].surface, 'east-enamel');
  assert.deepEqual(cli('validate', file, '--select', json).targets, inspected.targets);
  const result = cli('probe', file, '--select', json, '--args', '{"rgb":[0.6,0.6,0.6],"pixel":[8,7]}');
  const row = result.value.targets[0];
  assert.equal(row.asset, 'relay/glazed-enamel');
  assert.deepEqual(row.rule, select);
  assert(row.palette.includes(0xae5653));
  const color = row.rgb.reduce((packed, value) => packed * 256 + Math.round(value * 255), 0);
  assert(row.palette.includes(color));
  assert.equal(cli('probe', file, '--select', '{"surface":"unknown"}').status, 'missing');
  assert.throws(() => cli('validate', file, '--select', '{"surface":"unknown"}'), /No render target matches/);
  assert.throws(() => TargetSelectors.prepare({ group: 'typo' }), /Invalid target selector/);
});

test('world queries use the entity and prefab instance IDs from the same simulation snapshot', () => {
  const pack = require('../examples/relay-look-pack.json');
  const source = require('../examples/look-prefabs.json');
  const select = { prefab: 'west', surface: 'lid', tag: 'paintable', material: 'ceramic' };
  const world = W.manifest({ ...source, assetPacks: [pack], prefabs: { relay: {
    entities: { box: { position: [0,.55,0], tags: ['paintable'], visual: { half: [.5,.5,.45], surfaceId: 'lid', material: 'ceramic' } } }
  } }, visual: { ...source.visual, look: { targets: [{ select, asset: 'relay/glazed-enamel' }] } } });
  const west = W.stamp(world, 'relay', 'west', { position: [-1,0,0] }).world;
  const both = W.stamp(west, 'relay', 'east', { position: [1,0,0] }).world;
  const run = W.runtime.create(both), query = run.query();
  assert.deepEqual(query.probe('world/position', { entity: 'west.box' }).value, [-1,.55,0]);
  assert.equal(query.select(select).length, 1);
  assert.equal(query.select(select)[0].entity, 'west.box');
  assert.deepEqual(query.select({ ...select, entity: 'east.box' }), []);
  assert.equal(query.probe('look/output', select).value.targets[0].asset, 'relay/glazed-enamel');
  const image = studio.render(W.visual(kit, run.view(), query), { w: 240, h: 180, ortho: true });
  assert(image.use[image.palette.indexOf(0x65ab97)] > 0);
});

test('named native media share look matching, with independent optics and unchanged queries', () => {
  const palette = [0, 0xffffff], select = { medium: 'basin', mediumKind: 'water' };
  const plan = PixelLook.preparePaletteConstraints({ targets: [{ select, palette: ['#38b890'] }] }, { palette });
  const water = KIT.procedural.waterBodies;
  const make = (id, x) => water.create({ id, bounds: { min: [x,-1], max: [x+1,1] },
    sample: () => ({ bed: -2, surface: 0 }) });
  const source = water.scene([make('basin', -1), make('spillway', 1)]);
  const styled = source.mapColors((medium, mediumKind) => PixelLook.mediumTransform(plan, { medium, mediumKind }));
  const a = source.pack().uniforms.u_waterTint, b = styled.pack().uniforms.u_waterTint;
  assert.notDeepEqual(a.slice(0,3), b.slice(0,3));
  assert.deepEqual(a.slice(4), b.slice(4));
  assert.deepEqual(styled.mediumAt(-.5,-1,0), source.mediumAt(-.5,-1,0));

  const builder = makeBuilder(1, palette);
  const atmosphere = [SceneOptics.sphere({ id: 'mist', at: [0,0,0], radius: 1, density: 1, color: '#444444' })];
  const mist = { medium: 'mist', mediumKind: 'sphere' };
  const scene = builder.finish({ cam: { target: [0,0,0], dist: 5, yaw: 0, pitch: 0 }, atmosphere, water: styled,
    look: { paletteConstraints: { targets: [{ select: mist, palette: ['#ffffff'] }] } } });
  const query = W.query.fromScene(scene);
  assert.equal(query.select(select)[0].medium, 'basin');
  assert.deepEqual(query.probe('look/output', mist, { rgb: [.4,.4,.4] }).value.targets[0].rgb, [1,1,1]);
  const center = (22 * 45 + 22) * 3;
  assert.equal(studio.render(scene, { w: 45, h: 45, px: 1 }).rgb[center], 255);
  assert.equal(studio.render(scene, { w: 45, h: 45, px: 1, paletteConstraints: false }).rgb[center], 0);
});

const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const studio = require('../index.js');
const PNG = require('../cli/png.js');
const { makeBuilder } = studio.load();

const root = path.resolve(__dirname, '..');
const select = { entity: 'panel' };
const stack = { name: 'Red paint', steps: [{ type: 'channelMix', matrix: [[0, 0, 0], [0, 0, 0], [0, 0, 0]], offset: [1, 0, 0] }] };
const mask = { type: 'axis', axis: 'z', range: [-1, 1], space: 'world', interpolation: 'linear' };
const tint = { stage: 'frame', stack, select, mask };
const camera = { target: [0, 0, 0], dist: 4, yaw: 0, pitch: 0 };
const options = { w: 64, h: 64, px: 1, ortho: true };
const center = 32 * 64 + 32;

test('target and mask passes record the actual applied stage and preserve the color render', () => {
  const B = makeBuilder(1, [0, 0x606060]);
  B.disc(0, 0, 0, [0, 0, 1], .5, .025, B.P[1], 3);
  B.describeSplats(0, 1, { object: 'panel', material: 'iron' });
  const world = B.finish({ cam: camera, look: { renderStages: [
    tint, { stage: 'palette', palette: { palette: ['#101010', '#904040'] } }
  ] } });
  const diagnostic = studio.render(world, { ...options, passes: ['target', 'mask', 'materialId'] });
  assert.deepEqual(diagnostic.rgb, studio.render(world, options).rgb);
  const { passes } = diagnostic;
  assert.equal(passes.mask[center], .5);
  assert.equal(passes.mask[0], 0);
  assert.equal(passes.targets[passes.target[0]].scope, 'scene');
  assert.deepEqual(passes.targets[passes.target[center]].select, select);
  assert.equal(passes.materials[passes.materialId[center]], 'iron');

  const disabled = studio.render(world, { ...options, passes: ['target', 'mask'], lookMasks: false });
  assert(disabled.passes.target.every(id => id === 0 || disabled.passes.targets[id].scope === 'scene'));
  assert(disabled.passes.mask.every(weight => weight === 0));
});

test('a translucent scoped splat contributes its own mask over the material behind it', () => {
  const B = makeBuilder(1, [0, 0x808080]);
  B.disc(0, 0, 0, [0, 0, 1], .7, .025, B.P[1], 3);
  B.describeSplats(0, 1, { object: 'rear', material: 'stone' });
  B.disc(0, 0, .2, [0, 0, 1], .5, .025, B.P[1], .48, { gl: true, nd: true });
  B.describeSplats(1, 2, { object: 'panel', material: 'glass' });
  const world = B.finish({ cam: camera, refract: 0, look: { coverageAware: true, paletteConstraints: {
    targets: [{ select, palette: ['#ff0000'], mask }]
  } } });
  for (const renderOptions of [options, { ...options, splatOrder: 'surface' }]) {
    const { passes, rgb } = studio.render(world, { ...renderOptions, passes: ['target', 'mask', 'materialId'] });
    assert.deepEqual(rgb, studio.render(world, renderOptions).rgb);
    assert(passes.mask[center] > .25 && passes.mask[center] < .31);
    assert.deepEqual(passes.targets[passes.target[center]].select, select);
    assert.equal(passes.materials[passes.materialId[center]], 'stone');
  }
});

function tempPaths(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-look-previews-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return name => path.join(dir, name);
}
function cli(...args) {
  const result = spawnSync(process.execPath, ['cli/ink-studio.js', ...args], { cwd: root, encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
}
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const fileHex = (image, pixel) => '#' + Buffer.from(image.rgb.subarray(pixel * 3, pixel * 3 + 3)).toString('hex');

test('render, sheet and clip apply preview overrides and export aligned diagnostic files', t => {
  const file = tempPaths(t), scene = file('scene.js'), look = file('look.json');
  fs.writeFileSync(look, JSON.stringify({ renderStages: [tint] }));
  fs.writeFileSync(scene, `module.exports = ({ makeBuilder }) => ({ id:'preview', seed:1, build() {
    const B = makeBuilder(1, [0, 0x606060]);
    B.disc(0, 0, 0, [0, 0, 1], .5, .025, B.P[1], 3);
    B.describeSplats(0, 1, { object:'panel', material:'iron' });
    return B.finish({ cam:{ target:[0,0,0], dist:4, yaw:0, pitch:0 } });
  } });`);
  const common = ['--look', look, '--passes', 'target,mask,materialId', '--w', '64', '--h', '64', '--px', '1', '--ortho'];
  cli('render', scene, '--out', file('normal.png'), '--w', '64', '--h', '64', '--px', '1', '--ortho');
  cli('render', scene, ...common, '--out', file('still.png'));
  assert.notEqual(fileHex(PNG.read(file('still.png')), center), fileHex(PNG.read(file('normal.png')), center));
  const still = readJSON(file('still-passes.json'));
  assert.equal(fileHex(PNG.read(file(still.files.mask)), center), '#808080');
  const target = still.targets.find(row => row.color === fileHex(PNG.read(file(still.files.target)), center));
  assert.deepEqual(target.label.select, select);
  const material = still.materials.find(row => row.color === fileHex(PNG.read(file(still.files.materialId)), center));
  assert.equal(material.label, 'iron');

  const pack = file('pack.json');
  fs.writeFileSync(pack, JSON.stringify({ format: 'ink-studio/asset-pack', version: 1, revision: 1, id: 'paint', title: 'Paint',
    looks: [{ id: 'paint/red', label: 'Red', stage: 'lit', stack }] }));
  cli('render', scene, '--look', 'paint/red', '--asset-pack', pack, '--look-select', JSON.stringify(select),
    '--look-strength', '0.5', '--passes', 'target', '--w', '64', '--h', '64', '--px', '1', '--ortho',
    '--out', file('named.png'));
  const named = readJSON(file('named-passes.json'));
  const applied = named.targets.find(row => row.color === fileHex(PNG.read(file(named.files.target)), center));
  assert.equal(applied.label.asset, 'paint/red');
  assert.deepEqual(applied.label.select, select);

  cli('sheet', scene, ...common, '--t', '0,0.1', '--cols', '2', '--out', file('sheet.png'));
  assert.deepEqual(readJSON(file('sheet-passes.json')).times, [0, .1]);
  const sheet = PNG.read(file('sheet.png')), maskSheet = PNG.read(file('sheet-mask.png'));
  assert.deepEqual([sheet.w, sheet.h], [maskSheet.w, maskSheet.h]);
  const frames = name => {
    const chunks = fs.readFileSync(file(name));
    return chunks.readUInt32BE(chunks.indexOf('acTL') + 4);
  };
  cli('clip', scene, ...common, '--to', '.2', '--fps', '10', '--out', file('clip.png'));
  assert.equal(readJSON(file('clip-passes.json')).fps, 10);
  assert.equal(frames('clip.png'), 2);
  assert.equal(frames('clip-mask.png'), 2);
  assert.equal(frames('clip-target.png'), 2);
  assert.equal(frames('clip-materialId.png'), 2);
});

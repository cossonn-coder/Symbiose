const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const studio = require('../index.js');
const { KIT, ColorStack, ColorLUT, PixelLook } = studio.load();
const { assetPacks, looks } = KIT.authoring;

const root = path.resolve(__dirname, '..');
const run = (...args) => spawnSync(process.execPath, ['cli/ink-studio.js', ...args], { cwd: root, encoding: 'utf8' });
function cli(...args) {
  const child = run(...args);
  assert.equal(child.status, 0, child.stderr);
  return child.stdout ? JSON.parse(child.stdout) : undefined;
}
const json = file => JSON.parse(fs.readFileSync(file, 'utf8'));
function tempPaths(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-look-bake-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return (name, data) => {
    const file = path.join(dir, name);
    if (data !== undefined) fs.writeFileSync(file, typeof data === 'string' ? data : JSON.stringify(data));
    return file;
  };
}

test('palette baking preserves roles, protection, strength and the editable source', t => {
  const file = tempPaths(t), palette = [0, 0x224466, 0x8899aa], roles = { ink: [1, 2] };
  const stack = { name: 'Ink coat', amount: .8, steps: [
    { type: 'paletteRemap', remap: { rules: [{ from: 'ink.shadow', to: '#2030d0' }], protect: [0] } },
    { type: 'saturation', factor: .65 }
  ] };
  const input = file('stack.json', stack), reference = file('ref.hex', '#000000\n#224466\n#8899aa\n');
  const bundle = file('looks.json'), metrics = file('metrics.json');
  cli('look', 'bake', input, '--swatches', reference, '--roles', file('roles.json', roles),
    '--id', 'source/paint', '--as', 'fast/paint', '--exact', '--out', bundle, '--report', metrics);
  assert.equal(json(metrics).error.maxChannelError, 0);
  assert.deepEqual(json(bundle).packs[0].looks[0].stack, stack);
  const catalog = assetPacks.create({ packs: json(bundle).packs });
  const source = looks.bind({ asset: 'source/paint', strength: .5 }, catalog).stack;
  const baked = looks.bind({ asset: 'fast/paint', strength: .5 }, catalog).stack;
  assert.equal(baked.steps[0].type, 'paletteRemap');
  const normalize = packed => [packed >> 16, packed >> 8 & 255, packed & 255].map(value => value / 255);
  for (const [colors, roleMap] of [[palette, roles], [palette, { ink: [2, 1] }], [[0, 0x123456, 0xaabbcc], roles]]) {
    const original = PixelLook.prepareColorStack(source, colors, roleMap), compiled = PixelLook.prepareColorStack(baked, colors, roleMap);
    assert.equal(compiled.protects(0), true);
    for (const [index, value] of colors.entries()) {
      const sample = normalize(value);
      assert(compiled.sample(sample, undefined, index).every((n, i) => Math.abs(n - original.sample(sample, undefined, index)[i]) < 1e-14));
      const animated = [.24, .25, .26];
      assert.deepEqual(compiled.sample(animated, undefined, index), original.sample(animated, undefined, index));
    }
  }
  const exported = file('colors.hex');
  cli('look', 'export', bundle, '--look', 'fast/paint', '--out', exported, '--swatches', reference);
  assert.equal(fs.readFileSync(exported, 'utf8').trim().split('\n').length, 3);
});

test('sampled LUT reports measured error, preserves outside-domain color and exports its table', t => {
  const file = tempPaths(t);
  const stack = { name: 'Bend and lift', steps: [
    { type: 'curves', curves: { channels: { red: { interpolation: 'smooth', stops: [[0, 0], [.4, .1], [1, 1]] } } } },
    { type: 'exposure', stops: .5 }
  ] };
  const input = file('curve.json', stack), output = file('baked.json'), report = file('error.json');
  cli('look', 'bake', input, '--format', 'lut', '--size', '5', '--out', output, '--report', report);
  const table = json(report);
  assert.equal(table.error.mode, 'sampled');
  assert.equal(table.error.midpointChecks, 64);
  assert(table.error.maxChannelError > 0);
  assert.equal(table.error.samples, 125);
  const baked = json(output).packs[1].looks[0].stack;
  const original = ColorStack.prepare(stack), compiled = ColorStack.prepare(baked);
  assert.deepEqual(compiled.sample([.25, .5, .75]), original.sample([.25, .5, .75]));
  assert.deepEqual(compiled.sample([-.2, 1.8, .1]), original.sample([-.2, 1.8, .1]));
  const target = file('table.cube');
  cli('look', 'export', output, '--look', table.compiled, '--out', target, '--report', report);
  assert.deepEqual(ColorLUT.parseCube(fs.readFileSync(target, 'utf8')).data, baked.steps[0].lut.data);
  assert.equal(json(report).baked.maxChannelError, table.error.maxChannelError);
  assert(json(report).losses.some(item => item.code === 'baked-source'));

  file('preserved.json', 'previous output');
  const strict = run('look', 'bake', input, '--size', '5', '--max-error', '0', '--out', file('preserved.json'));
  assert.equal(strict.status, 1);
  assert.match(strict.stderr, /exceeds --max-error/);
  assert.equal(fs.readFileSync(file('preserved.json'), 'utf8'), 'previous output');
});

test('exact LUT baking keeps the table and named asset baking keeps pack revisions', t => {
  const file = tempPaths(t), cube = path.join(root, 'examples/blue-shadow.cube');
  const bundle = cli('look', 'bake', cube, '--exact');
  assert.deepEqual(bundle.packs[0].looks[0].stack.steps[0].lut, bundle.packs[1].looks[0].stack.steps[0].lut);
  assert.equal(bundle.packs[1].looks[0].stack.baked.error.mode, 'exact');

  const pack = path.join(root, 'examples/relay-look-pack.json');
  const result = cli('look', 'bake', pack, '--look', 'relay/glazed-enamel', '--size', '3',
    '--params', '{"mid":"#bf4756"}', '--report', file('report.json'));
  assert.deepEqual(result.packs[0], assetPacks.manifest(fs.readFileSync(pack, 'utf8')));
  assert.equal(json(file('report.json')).parameters.mid, '#bf4756');
  const compiled = result.packs[1].looks[0];
  assert.equal(compiled.stack.baked.source.steps[0].curves.ramp.stops[1][1], '#bf4756');
  assert.deepEqual(compiled.palette, result.packs[0].looks[0].palette);
});

test('render can select a palette bake or its editable stack in the same bundle', t => {
  const file = tempPaths(t);
  const input = file('source.json', { name: 'Ink', steps: [{ type: 'exposure', stops: -.5 }, { type: 'saturation', factor: 1.2 }] });
  const reference = file('colors.hex', '#000000\n#406080\n#e0e0cc\n');
  const bundle = file('bundle.json');
  cli('look', 'bake', input, '--id', 'source/ink', '--as', 'fast/ink', '--swatches', reference, '--out', bundle);
  const scene = file('scene.js', `module.exports = ({ makeBuilder }) => ({
    id: 'paint', seed: 1, build() {
      const B = makeBuilder(1, [0, 0x406080, 0xe0e0cc]);
      B.disc(0, 0, 0, [0,0,1], .45, .02, B.P[1], 3);
      return B.finish({ cam: { target:[0,0,0], dist:3, yaw:0, pitch:0 } });
    }
  });`);
  const images = ['source/ink', 'fast/ink'].map((asset, index) => {
    const output = file('image-' + index + '.png');
    const command = run('render', scene, '--asset-pack', bundle, '--look', asset, '--w', '48', '--h', '48', '--px', '1', '--out', output);
    assert.equal(command.status, 0, command.stderr);
    return fs.readFileSync(output);
  });
  assert.deepEqual(images[0], images[1]);
});

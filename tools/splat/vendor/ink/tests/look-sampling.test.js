const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const ColorLUT = require('../src/color-lut.js');
const PNG = require('../cli/png.js');
const { KIT, makeBuilder } = require('../index.js').load();

const root = path.resolve(__dirname, '..');
const examples = name => path.join(root, 'examples', name);
const run = (...args) => spawnSync(process.execPath, ['cli/ink-studio.js', ...args], { cwd: root, encoding: 'utf8' });
function cli(...args) {
  const result = run(...args);
  assert.equal(result.status, 0, result.stderr);
  return result.stdout ? JSON.parse(result.stdout) : undefined;
}
function temporary(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-sample-look-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return (name, contents) => {
    const file = path.join(dir, name);
    if (contents !== undefined) fs.writeFileSync(file, typeof contents === 'string' ? contents : JSON.stringify(contents));
    return file;
  };
}

test('look sample evaluates supplied colors and generates a paired PNG chart', t => {
  const temp = temporary(t), cube = examples('blue-shadow.cube');
  const output = cli('look', 'sample', cube, '--colors', '["#182c55",[0.8,0.1,0.05]]');
  assert.equal(output.samples.length, 2);
  const lut = ColorLUT.prepare(ColorLUT.parseCube(fs.readFileSync(cube, 'utf8')));
  for (const sample of output.samples) {
    assert.deepEqual(sample.rgb, lut.apply(sample.input));
    assert.equal(sample.swatch, null);
  }
  const chart = cli('look', 'sample', cube, '--chart');
  assert.deepEqual(chart.chart, { columns: 8, rows: 4 });
  assert.equal(chart.samples.length, 32);
  const out = temp('chart.png');
  cli('look', 'sample', cube, '--chart', '--out', out);
  const image = PNG.read(out);
  assert.deepEqual([image.w, image.h], [386, 114]);
  const pixel = (x, y) => Array.from(image.rgb.slice((image.w * y + x) * 3, (image.w * y + x) * 3 + 3));
  assert.deepEqual(pixel(4, 4), [0, 0, 0]);
  assert.deepEqual(pixel(52, 4), [36, 36, 36]);
  assert.notDeepEqual(pixel(248, 33), pixel(276, 33));
});

test('standalone sampling uses indexed references, masks and authored palette assets', t => {
  const temp = temporary(t);
  const stack = temp('remap.json', { name: 'Remapped blue', steps: [
    { type: 'paletteRemap', remap: { rules: [{ from: 1, to: '#eeee22' }], protect: [0] } }
  ] });
  const reference = temp('reference.hex', '#111111\n#2222dd\n');
  assert.match(run('look', 'sample', stack, '--colors', '["#2222dd"]').stderr, /Indexed remaps need --swatches/);
  const remap = cli('look', 'sample', stack, '--swatches', reference, '--colors', '["#111111","#2222dd"]');
  assert.deepEqual(remap.samples.map(row => row.paletteIndex), [0, 1]);
  assert.deepEqual(remap.samples[1].rgb, [238 / 255, 238 / 255, 34 / 255]);

  const asset = cli('look', 'sample', examples('relay-look-pack.json'), '--look', 'relay/glazed-enamel',
    '--params', '{"mid":"#bb6644"}', '--colors', '["#555555"]');
  assert.equal(asset.look, 'relay/glazed-enamel');
  assert(asset.palette.includes(asset.samples[0].swatch));

  const pack = temp('masked.json', { format: 'ink-studio/asset-pack', version: 1, revision: 1, id: 'test', title: 'Masks',
    looks: [{ id: 'test/masked', label: 'Masked', palette: { palette: ['#ffffff'] },
      mask: { type: 'axis', axis: 'x', space: 'world', range: [0, 2], interpolation: 'linear' } }] });
  const masked = cli('look', 'sample', pack, '--at', '1,0,0', '--colors', '["#000000"]');
  assert.equal(masked.maskWeight, .5);
  assert.deepEqual(masked.samples[0].rgb, [.5, .5, .5]);
  assert.equal(masked.samples[0].swatch, null);
});

test('point probes explain the sampled splat and its masked stages and swatch', t => {
  const temp = temporary(t);
  const scene = temp('test-scene.js', `module.exports = ({ makeBuilder }) => ({
    id: 'sample-pair', seed: 1,
    build(seed) {
      const B = makeBuilder(seed, [0, 0x404040, 0x777777]);
      const surface = 'painted-face';
      B.disc(-3, 0, 0, [0, 0, 1], .4, .025, B.P[2], 1);
      B.describeSplats(0, 1, { object: 'left', material: 'enamel', target: { surface } });
      B.disc(0, 0, 0, [0, 0, 1], .4, .025, B.P[1], 1);
      B.describeSplats(1, 2, { object: 'right', material: 'enamel', target: { surface } });
      return B.finish({ cam: { target: [0, 0, 0], dist: 4, yaw: 0, pitch: 0 }, look: { renderStages: [
        { stage: 'lit', select: { surface }, stack: { name: 'Lift', steps: [{ type: 'exposure', stops: 1 }] },
          mask: { type: 'axis', axis: 'x', space: 'world', range: [-1, 1], interpolation: 'linear' } },
        { stage: 'palette', palette: { palette: ['#404040', '#606060', '#808080'] } }
      ] } });
    }
  });`);
  const pick = cli('probe', scene, '--at', '0.1,0,0', '--select', '{"surface":"painted-face"}');
  assert.equal(pick.status, 'ok');
  const sample = pick.value;
  assert.equal(sample.kind, 'splat');
  assert.equal(sample.splat, 1);
  assert.equal(sample.target.entity, 'right');
  assert.equal(sample.material, 'enamel');
  assert.deepEqual(sample.input, Array(3).fill(64 / 255));
  assert.deepEqual(sample.position, [0, 0, 0]);
  assert.equal(sample.looks[0].stack, 'Lift');
  assert.equal(sample.looks[0].maskWeight, .5);
  assert.deepEqual(sample.looks[0].output, Array(3).fill(96 / 255));
  assert.equal(sample.swatch, '#606060');
  assert.equal(cli('probe', scene, '--at', '0.1,0,0', '--radius', '.05').status, 'missing');
  assert.equal(cli('probe', scene, '--field', 'look/sample', '--entity', 'left').value.splat, 0);
});

test('scene sample explains a surface layer and the blended palette color', () => {
  const B = makeBuilder(1, [0, 0x333333]);
  B.surfaceNext({ layers: { lift: { type: 'colorStack', stack: { name: 'Coating',
    steps: [{ type: 'exposure', stops: 1 }] } } } }, 0, 0, 1, [1, 0, 0]);
  B.disc(0, 0, 0, [0, 0, 1], .3, .025, B.P[1], 1);
  B.describeSplats(0, 1, { object: 'slab', material: 'stone' });
  const world = B.finish({ look: { coverageAware: true, paletteConstraints: { targets: [
    { select: { material: 'stone' }, palette: ['#ffffff'],
      mask: { type: 'axis', axis: 'x', range: [-1, 1], space: 'world', interpolation: 'linear' } }
  ] } } });
  const result = KIT.world.query.fromScene(world).probe('look/sample', { material: 'stone' }).value;
  assert.equal(result.looks[0].layer, 'lift');
  assert.deepEqual(result.looks[0].output, [.4, .4, .4]);
  assert.equal(result.looks[1].maskWeight, .5);
  assert.equal(result.looks[1].selectedSwatch, '#ffffff');
  assert.deepEqual(result.rgb, [.7, .7, .7]);
  assert.equal(result.swatch, null);
});

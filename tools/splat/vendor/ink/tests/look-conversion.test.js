const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const ColorLUT = require('../src/color-lut.js');
const ColorStack = require('../src/color-stack.js');
const { assetPacks, looks } = require('../index.js').load().KIT.authoring;

const root = path.resolve(__dirname, '..');
const examples = path.join(root, 'examples');
const read = file => fs.readFileSync(file, 'utf8');
const relay = require('../examples/relay-look-pack.json');

function fixture(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-look-conversion-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const file = name => path.join(dir, name);
  const write = (name, value) => {
    const target = file(name);
    fs.writeFileSync(target, typeof value === 'string' ? value : JSON.stringify(value));
    return target;
  };
  const run = (...args) => spawnSync(process.execPath, ['cli/ink-studio.js', 'look', ...args],
    { cwd: root, encoding: 'utf8' });
  const cli = (...args) => {
    const { status, stderr, stdout } = run(...args);
    assert.equal(status, 0, stderr);
    return { stderr, stdout };
  };
  return { file, write, run, cli };
}

test('look import installs a 3D LUT and exports the same RGB table and domain', t => {
  const { file, write, cli } = fixture(t);
  const rows = ['0 0 -0.15', '1.3 0 0', '0 1 0', '1 1 0', '0 0 1', '1 0 1', '0 1 1', '1 1 1'];
  const input = write('table.cube', ['TITLE "Teal #4"', 'LUT_3D_SIZE 2',
    'DOMAIN_MIN -0.25 0.1 0.2', 'DOMAIN_MAX 1.1 0.9 0.8', ...rows].join('\n'));
  const output = file('looks.json'), report = file('report.json');
  cli('import', input, '--id', 'grades/teal', '--out', output, '--exact', '--report', report);
  const catalog = assetPacks.create({ packs: [read(output)] });
  const original = ColorLUT.parseCube(read(input));
  assert.deepEqual(looks.bind('grades/teal', catalog).stack.steps[0].lut, original);
  assert.equal(JSON.parse(read(report)).mode, 'exact');

  const { stdout, stderr } = cli('export', output, '--format', 'cube', '--exact', '--report', report);
  assert.deepEqual(ColorLUT.parseCube(stdout), original);
  assert.match(stderr, /reader selects the interpolation/);
  assert.equal(JSON.parse(read(report)).mode, 'exact');

  const resized = cli('export', output, '--format', 'cube', '--size', '3', '--report', report);
  assert.deepEqual(ColorLUT.parseCube(resized.stdout).domainMin, original.domainMin);
  assert.deepEqual(ColorLUT.parseCube(resized.stdout).domainMax, original.domainMax);
  assert.equal(JSON.parse(read(report)).mode, 'sampled');
});

test('sampled LUTs report measured error and strict mode preserves existing output', t => {
  const { file, write, run, cli } = fixture(t);
  const stack = { name: 'Smooth red', steps: [{ type: 'curves', curves: {
    channels: { red: { interpolation: 'smooth', stops: [[0, 0], [.6, .14], [1, .9]] } }
  } }] };
  const input = write('curves.json', stack), output = file('sampled.cube'), report = file('report.json');
  cli('export', input, '--size', '5', '--out', output, '--report', report);
  const result = JSON.parse(read(report));
  assert.equal(result.mode, 'sampled');
  assert.equal(result.samples.count, 125);
  assert.equal(result.samples.midpointChecks, 64);
  assert(result.samples.maxChannelError > .01);
  assert(result.samples.rmse > 0 && result.samples.rmse < result.samples.maxChannelError);
  const rendered = ColorLUT.prepare(ColorLUT.parseCube(read(output)));
  const rgb = [.25, .5, .75];
  assert.deepEqual(rendered.sample(rgb), ColorStack.prepare(stack).sample(rgb));

  write('sampled.cube', 'existing output');
  const rejected = run('export', input, '--size', '5', '--out', output, '--report', report, '--exact');
  assert.equal(rejected.status, 1);
  assert.match(rejected.stderr, /--exact rejected/);
  assert.equal(JSON.parse(read(report)).mode, 'sampled');
  assert.equal(read(output), 'existing output');

  const cube = path.join(examples, 'half-gain-legal.cube');
  const imported = cli('import', cube, '--input-range', '0.0625,0.921875', '--output-space', 'srgb-linear');
  const packed = write('legal.json', imported.stdout);
  const exported = cli('export', packed, '--format', 'cube', '--size', '3', '--report', report);
  const look = looks.bind('half-gain-legal/half-gain-legal',
    assetPacks.create({ packs: [imported.stdout] }));
  assert.equal(JSON.parse(read(report)).mode, 'sampled');
  assert.deepEqual(ColorLUT.prepare(ColorLUT.parseCube(exported.stdout)).sample([.5, .5, .5]),
    ColorStack.prepare(look.stack).sample([.5, .5, .5]));
});

test('palette conversion preserves swatches and reports unsupported metadata', t => {
  const { file, write, run, cli } = fixture(t);
  const gpl = 'GIMP Palette\nName: Coast\nColumns: 2\n#\n23 51 95\tDeep blue\n255 180 50\tReeds\n';
  const input = write('coast.gpl', gpl), palette = file('coast.pal'), report = file('report.json');
  assert.equal(cli('export', input, '--format', 'gpl', '--exact').stdout, gpl);
  const pack = cli('import', input, '--report', report);
  assert.deepEqual(JSON.parse(pack.stdout).looks[0].palette.palette, ['#17335f', '#ffb432']);
  let info = JSON.parse(read(report));
  assert.equal(info.mode, 'lossy');
  assert.deepEqual(info.losses.map(({ code }) => code), ['palette-presentation']);

  cli('export', input, '--out', palette, '--report', report);
  assert.equal(read(palette), 'JASC-PAL\n0100\n2\n23 51 95\n255 180 50\n');
  assert.equal(cli('export', palette, '--format', 'hex', '--exact').stdout, '#17335f\n#ffb432\n');
  const swatches = write('swatches.json', ['#17335f', 0xffb432]);
  assert.equal(cli('export', swatches, '--format', 'hex', '--exact').stdout, '#17335f\n#ffb432\n');
  assert.match(run('export', palette, '--format', 'cube').stderr, /continuous RGB stack/);
  assert.match(run('import', write('bad.pal', 'JASC-PAL\n0100\n2\n23 51 95\n')).stderr, /matching swatch count/);
  assert.match(run('import', write('bad.gpl', gpl.replace('Columns: 2', 'Columns: 256'))).stderr, /count from 0 to 255/);

  const policy = write('policy.json', { reserved: ['#ffffff'] });
  assert.match(run('export', policy, '--format', 'hex').stderr, /scene-dependent palette/);
  assert.equal(cli('export', policy, '--swatches', palette, '--format', 'hex').stdout, '#17335f\n#ffb432\n#ffffff\n');

  const stack = write('indexed.json', { name: 'Index remap', steps: [
    { type: 'paletteRemap', remap: { rules: [{ from: 1, to: '#e0c945' }], protect: [0] } },
    { type: 'exposure', stops: 1 }
  ] });
  assert.equal(cli('export', stack, '--swatches', palette, '--format', 'hex', '--report', report).stdout,
    '#17335f\n#ffff8a\n');
  info = JSON.parse(read(report));
  assert.deepEqual(info.samples, { kind: 'palette-swatches', count: 2, clipped: 1, rounded: 0 });
  assert.match(run('export', stack, '--format', 'cube').stderr, /has no palette indices/);
});

test('native bundles preserve versions and require selection for external export', t => {
  const { file, write, run, cli } = fixture(t);
  const original = assetPacks.bundle([relay]);
  const input = write('bundle.json', original), report = file('report.json');
  assert.deepEqual(JSON.parse(cli('export', input, '--exact').stdout), original);
  assert.match(run('export', input, '--format', 'gpl').stderr, /Select one named look/);
  const reference = write('reference.hex', '#000000\n#777777\n#ffffff\n');
  const { stdout } = cli('export', input, '--look', 'relay/glazed-enamel', '--params', '{"mid":"#ee2626"}',
    '--swatches', reference, '--format', 'hex', '--report', report);
  const binding = looks.bind({ asset: 'relay/glazed-enamel', params: { mid: '#ee2626' } },
    assetPacks.create({ packs: [relay] }));
  const rgb = ColorStack.prepare(binding.stack).sample([.4666666666666667, .4666666666666667, .4666666666666667]);
  assert.equal(stdout.split('\n')[1], '#' + rgb.map(channel => Math.round(channel * 255).toString(16).padStart(2, '0')).join(''));
  const info = JSON.parse(read(report));
  assert.equal(info.look, 'relay/glazed-enamel');
  assert.equal(info.samples.count, 3);
  assert(info.losses.some(loss => loss.code === 'parameterized'));
});

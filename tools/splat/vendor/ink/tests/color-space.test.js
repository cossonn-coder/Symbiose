const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { ColorSpace, ColorLUT, ColorCurves, ColorStack, PixelLook, SurfaceLook } = require('..').load();
const cube = path.resolve(__dirname, '../examples/half-gain-legal.cube');
const legal = (space, outOfRange) => ({ space, range: [16, 235], ...(outOfRange && { outOfRange }) });
const close = (actual, expected, tolerance = 1e-10) => {
  assert(actual.every((value, i) => Math.abs(value - expected[i]) <= tolerance), `${actual} differs from ${expected}`);
};

test('sRGB transfer and D65 P3 conversion preserve extended values and round-trip', () => {
  close(ColorSpace.convert([.5, 0, -1], 'srgb', 'srgb-linear'), [.21404114048223255, 0, -1]);
  close(ColorSpace.convert([1, 0, 0], 'display-p3-linear', 'srgb-linear'),
    [1.2249401762805598, -.04205695470968818, -.01963755459033439]);
  const original = [1.12, .42, -.12];
  const moved = ColorSpace.convert(original, 'srgb', 'display-p3');
  close(ColorSpace.convert(moved, 'display-p3', 'srgb'), original);
  close(ColorSpace.convert([1, 0, 0], 'display-p3-linear', { space: 'srgb-linear', outOfRange: 'clamp' }), [1, 0, 0]);
  assert.throws(() => ColorSpace.convert([1, 0, 0], 'display-p3-linear', { space: 'srgb-linear', outOfRange: 'error' }), /outside/);
});

test('shared and per-channel ranges apply explicit input and output policies', () => {
  const custom = { space: 'srgb', range: { min: [16, 64, -100], max: [235, 940, 100] } };
  close(ColorSpace.convert([125.5, 502, 0], custom, 'srgb'), [.5, .5, .5]);
  close(ColorSpace.convert([16, 125.5, 235], legal('srgb'), custom), [16, 502, 100]);
  close(ColorSpace.convert([-16, 16, 235], legal('srgb', 'clamp'), 'srgb'), [0, 0, 1]);
  assert(ColorSpace.convert([-16, 16, 235], legal('srgb'), 'srgb')[0] < 0);
  assert.throws(() => ColorSpace.convert([-16, 16, 235], legal('srgb', 'error'), 'srgb'), /outside/);
  assert.throws(() => ColorSpace.descriptor({ space: 'unknown' }), /Unknown color space/);
  assert.throws(() => ColorSpace.descriptor({ range: [1, 0] }), /increasing/);
  assert.throws(() => ColorSpace.descriptor({ range: { min: [0, 0, 0], max: [1, 1, null] } }), /increasing/);
});

test('LUT sampling domain is separate from encoded ranges and defaults are compatible', () => {
  const text = fs.readFileSync(cube, 'utf8');
  const base = ColorLUT.parseCube(text), ordinary = ColorLUT.prepare(base);
  close(ordinary.sample([16, 125.5, 235]), [16, 70.75, 125.5]);
  close(ordinary.apply([16, 125.5, 235]), [16, 70.75, 125.5]);
  close(ordinary.sample([-1, 16, 300]), [16, 16, 125.5]);
  assert.throws(() => ColorLUT.prepare({ ...base, domainPolicy: 'error' }).sample([16, 16, 300]), /outside the LUT domain/);
  for (const interpolation of ['tetrahedral', 'trilinear'])
    close(ColorLUT.prepare({ ...base, domainPolicy: 'extrapolate', interpolation }).sample([-16, 125.5, 300]), [0, 70.75, 158]);
  const managed = ColorLUT.prepare(ColorLUT.parseCube(text, {
    color: { input: legal('srgb-linear'), output: legal('srgb-linear') }, domainPolicy: 'error'
  }));
  close(managed.apply([.5, 0, 1]), [.3607802138332792, 0, .7353569830524495]);
  const finished = SurfaceLook.prepare({ layers: { tone: { type: 'colorLut', lut: managed.definition } } });
  const sample = { position: [0, 0, 0], normal: [0, 1, 0], view: [0, 1, 0] };
  close(SurfaceLook.shade(finished, sample, [.5, 0, 1]).slice(0, 3), managed.apply([.5, 0, 1]));
});

test('curves, parameter operations and indexed remaps respect per-transform declarations', () => {
  const input = legal('srgb-linear'), output = legal('srgb-linear'), color = { input, output };
  const exposure = ColorStack.prepare({ name: 'Half', steps: [{ type: 'exposure', stops: -1, color }] });
  close(exposure.sample([.5, 1, 0]), [.3607802138332792, .7353569830524495, 0]);

  const kod = { input: legal('srgb'), output: { space: 'srgb', range: [64, 940] } };
  const shape = ColorCurves.prepare({ color: kod, channels: { red: { stops: [[16, 64], [235, 502]] } } });
  close(shape([1, .5, .25]), [.5, .5, .25]);
  const field = ColorCurves.prepare({ color: kod, ramp: { stops: [[20, [64, 64, 64]], [80, [940, 502, 64]]] } });
  close(field([0, 0, 0], undefined, 50), [.5, .25, 0]);
  const options = { color: { output: 'srgb-linear' }, rules: [{ from: 1, to: [.5, 0, 0] }], protect: [0] };
  const base = [0x777777, 0x336699];
  assert.deepEqual(PixelLook.gradePalette(PixelLook.prepareRemap(options, base).grade()), [0x777777, 0xbc0000]);

  const table = ColorLUT.parseCube(fs.readFileSync(cube, 'utf8'), { color });
  const encoded = ColorStack.prepare({ name: 'Reassign LUT input and output', steps: [
    { type: 'lut', lut: table, color: { input: legal('srgb'), output: legal('srgb') } }
  ] });
  close(encoded.sample([.5, .5, 1]), [.25, .25, .5]);
});

test('CLI imports keep declarations through JSON round trips and change actual output pixels', () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-color-space-')), root = path.resolve(__dirname, '..');
  const cli = (...args) => execFileSync(process.execPath, [path.join(root, 'cli/ink-studio.js'), ...args],
    { cwd: temp, encoding: 'utf8' });
  try {
    const check = execFileSync(process.execPath, ['-e',
      'const { ColorSpace } = require(' + JSON.stringify(root) + ').load(); process.stdout.write(typeof ColorSpace.prepare);'],
    { encoding: 'utf8' });
    assert.equal(check, 'function');
    const input = path.join(temp, 'linear.json'), next = path.join(temp, 'preserved.json');
    cli('lut', 'import', cube, '--input-space', 'srgb-linear', '--output-space', 'srgb-linear',
      '--input-range', '16,235', '--output-range', '16,235', '--domain-policy', 'error', '--out', input);
    cli('lut', 'import', input, '--output-out-of-range', 'clamp', '--out', next);
    const meta = JSON.parse(fs.readFileSync(next, 'utf8'));
    assert.equal(meta.color.input.space, 'srgb-linear');
    assert.equal(meta.color.output.outOfRange, 'clamp');
    assert.deepEqual(meta.color.output.range.max, [235, 235, 235]);
    assert.equal(meta.domainPolicy, 'error');
    const encoded = path.join(temp, 'encoded.json');
    cli('lut', 'import', next, '--input-space', 'srgb', '--output-space', 'srgb', '--out', encoded);
    for (const [name, lut] of [['linear', next], ['encoded', encoded]])
      cli('render', path.join(root, 'examples/rgb-lut.js'), '--w', '144', '--h', '108',
        '--lut', lut, '--out', path.join(temp, name + '.png'));
    assert.notDeepEqual(fs.readFileSync(path.join(temp, 'linear.png')), fs.readFileSync(path.join(temp, 'encoded.png')));
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
});

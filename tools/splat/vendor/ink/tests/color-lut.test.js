const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const core = require('..');
const { ColorLUT, PixelLook, SurfaceLook, KIT } = core.load();

function table(size, transform = (r, g, b) => [r, g, b]) {
  const data = [];
  for (let b = 0; b < size; b++) for (let g = 0; g < size; g++) for (let r = 0; r < size; r++)
    data.push(...transform(r / (size - 1), g / (size - 1), b / (size - 1)));
  return { size, data };
}

function close(actual, expected) {
  assert(actual.every((n, i) => Math.abs(n - expected[i]) < 1e-12), `${actual} differs from ${expected}`);
}

test('a .cube imports exact red-fastest rows, title, custom domain and decimal exponents', () => {
  const native = table(2, (r, g, b) => [r * 2 - .25, g, b + .1]);
  const rows = Array.from({ length: 8 }, (_, i) => native.data.slice(i * 3, i * 3 + 3).map(n => n.toExponential()).join(' '));
  const cube = '\uFEFFTITLE "Studio #2" # comment\r\nDOMAIN_MAX 1 3 5\r\n\r' +
    'LUT_3D_SIZE 2\nDOMAIN_MIN -1 1 2\n' + rows.join('\r\n');
  const lut = ColorLUT.parseCube(cube);
  assert.equal(lut.title, 'Studio #2');
  assert.deepEqual(lut.domainMin, [-1, 1, 2]);
  assert.deepEqual(lut.domainMax, [1, 3, 5]);
  assert.deepEqual(lut.data, native.data);
  const plan = ColorLUT.prepare(lut);
  assert.equal(ColorLUT.prepare(lut), plan);
  assert.deepEqual(ColorLUT.normalize(JSON.parse(JSON.stringify(lut))), lut);
  close(plan.sample([0, 2, 3.5]), [.75, .5, .6]);
  close(plan.sample([4, -3, 6]), [1.75, 0, 1.1]);

  const resolve = ColorLUT.parseCube('LUT_3D_SIZE 2\nLUT_3D_INPUT_RANGE -2 2\n' + rows.join('\n'));
  assert.deepEqual(resolve.domainMin, [-2, -2, -2]);
  close(ColorLUT.prepare(resolve).sample([0, 0, 0]), [.75, .5, .6]);
});

test('trilinear and tetrahedral evaluation interpolate distinct non-affine tables', () => {
  const corner = table(2, (r, g, b) => [r * g * b, g, b]);
  close(ColorLUT.prepare(corner).sample([.5, .5, .5]), [.5, .5, .5]);
  close(ColorLUT.prepare({ ...corner, interpolation: 'trilinear' }).sample([.5, .5, .5]), [.125, .5, .5]);
  for (const interpolation of ['tetrahedral', 'trilinear']) {
    const sample = ColorLUT.prepare({ ...table(3, (r, g, b) => [g, b, r]), interpolation }).sample;
    for (const point of [[.11, .23, .46], [.11, .46, .23], [.23, .11, .46], [.23, .46, .11], [.46, .11, .23],
      [.46, .23, .11], [.99, .31, .57], [1, 0, 1]]) {
      const output = new Float64Array(point);
      assert.equal(sample(output, output), output);
      close(Array.from(output), [point[1], point[2], point[0]]);
    }
  }
  const original = table(2), plan = ColorLUT.prepare(original);
  original.data[0] = 1;
  assert.equal(plan.sample([0, 0, 0])[0], 0);
  assert.equal(ColorLUT.prepare(original).sample([0, 0, 0])[0], 1);
});

test('LUT validation rejects truncated files, conflicting headers, and invalid native data', () => {
  const rows = '\n' + '0 0 0\n'.repeat(8);
  assert.throws(() => ColorLUT.parseCube('LUT_1D_SIZE 2'), /1D table/);
  assert.throws(() => ColorLUT.parseCube('LUT_3D_SIZE 2\n0 0 0'), /exactly 8 RGB rows/);
  assert.throws(() => ColorLUT.parseCube('LUT_3D_SIZE 2' + rows + '0 0 0'), /Too many RGB rows/);
  assert.throws(() => ColorLUT.parseCube('LUT_3D_SIZE 2\nDOMAIN_MIN 0 1 0\nLUT_3D_INPUT_RANGE 0 1' + rows), /either DOMAIN/);
  assert.throws(() => ColorLUT.parseCube('LUT_3D_SIZE 2\nDOMAIN_MAX 0 1 1' + rows), /increasing input ranges/);
  assert.throws(() => ColorLUT.parseCube('LUT_3D_SIZE 2\n0x00 0 0'), /line 2/);
  assert.throws(() => ColorLUT.normalize({ ...table(2), version: 2 }), /version/);
  assert.throws(() => ColorLUT.normalize({ ...table(2), data: new Array(24) }), /finite numbers/);
  assert.throws(() => ColorLUT.prepare(table(2)).sample([.2, NaN, .3]), /finite RGB/);
  const invalid = { id: 'invalid-lut', solids: [], finish: { look: { colorLut: { size: 2, data: [] } } } };
  assert(KIT.diorama.check(invalid).some(row => row.path === 'finish.look.colorLut' && row.level === 'error'));
});

test('scene and material layers share the RGB transform and honor protected swatches', () => {
  const lut = ColorLUT.normalize(table(2, (r, g, b) => [b, g, r]));
  const colors = [0x112233, 0x112233, 0x2070b0];
  const curves = { channels: { red: { stops: [[0, 0], [1, 0]] } } };
  const remap = { rules: [{ from: 0, to: '#aabbcc' }], protect: [1] };
  const grade = PixelLook.colorGrade(colors, {}, null, remap, curves, lut);
  assert.deepEqual(PixelLook.gradePalette(grade), [0xaabbcc, 0x112233, 0xb07000]);

  const settings = { layers: { glaze: { type: 'colorLut', lut, strength: .5, outputPalette: ['#aabbcc'] } } };
  const material = SurfaceLook.material([0], settings);
  const sample = { position: [0, 0, 0], normal: [0, 1, 0], view: [0, 1, 0] };
  const base = [.2, .5, .8];
  const enabled = SurfaceLook.shade(SurfaceLook.prepare(material.surface, colors), sample, base);
  close(enabled.slice(0, 3), [.5, .5, .5]);
  assert.equal(PixelLook.gradePalette(enabled[5][0])[0], 0xaabbcc);
  const off = SurfaceLook.prepare(material.surface, colors, undefined, {}, { colorLut: false });
  assert.deepEqual(SurfaceLook.shade(off, sample, base).slice(0, 3), base);
});

test('headless rendering applies a material LUT only on its bound surface', () => {
  const { makeBuilder, makeSculpt } = core.load();
  const B = makeBuilder(1, [0x121117, 0x4666a8]), S = KIT.sculpt(makeSculpt(B));
  const lut = table(2, () => [.8, .1, .4]);
  const material = KIT.surface.material([1], { layers: {
    mark: { type: 'colorLut', lut, outputPalette: ['#cc1a66'] }
  } });
  S.box([-.65, .4, 0], [.4, .4, .4], material, { res: .08 });
  S.box([.65, .4, 0], [.4, .4, .4], [1], { res: .08 });
  S.bake();
  const world = B.finish({ cam: { target: [0, .4, 0], dist: 4.4, yaw: 0, pitch: .2 }, radius: 4 });
  const options = { w: 128, h: 96, px: 1, ortho: true };
  const off = core.render(world, { ...options, colorLut: false });
  const on = core.render(world, options);
  let marked = 0;
  for (let y = 0; y < on.h; y++) for (let x = 0; x < on.w; x++) {
    const i = (y * on.w + x) * 3;
    if (x >= on.w / 2) assert.deepEqual(on.rgb.subarray(i, i + 3), off.rgb.subarray(i, i + 3));
    else if (on.rgb[i] === 204 && on.rgb[i + 1] === 26 && on.rgb[i + 2] === 102) marked++;
  }
  assert(marked > 100);
});

test('the CLI imports a cube and renders the cube and the native LUT identically', () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-rgb-lut-'));
  const root = path.resolve(__dirname, '..'), fixture = path.join(root, 'examples/blue-shadow.cube');
  const cli = (...args) => execFileSync(process.execPath, [path.join(root, 'cli/ink-studio.js'), ...args],
    { cwd: temp, encoding: 'utf8' });
  try {
    const exported = execFileSync(process.execPath, ['-e',
      'const { ColorLUT, ColorCurves } = require(' + JSON.stringify(root) + ').load(); ' +
      'process.stdout.write(typeof ColorLUT.prepare + " " + typeof ColorCurves.prepare);'], { encoding: 'utf8' });
    assert.equal(exported, 'function function');
    const native = path.join(temp, 'native.json');
    cli('lut', 'import', fixture, '--out', native);
    const lut = JSON.parse(fs.readFileSync(native, 'utf8')), plan = ColorLUT.prepare(lut);
    const red = [122, 51, 20].map(n => n / 255), blue = [32, 51, 200].map(n => n / 255);
    const luma = ([r, g, b]) => .30 * r + .55 * g + .15 * b;
    assert(Math.abs(luma(red) - luma(blue)) < 1e-12);
    close(plan.sample(red), red);
    assert(plan.sample(blue)[0] > blue[0] + .2);

    for (const [name, input] of [['before', 'off'], ['cube', fixture], ['native', native]])
      cli('render', path.join(root, 'examples/rgb-lut.js'), '--w', '216', '--h', '144',
        '--ortho', '--lut', input, '--out', path.join(temp, name + '.png'));
    const images = ['before', 'cube', 'native'].map(name => fs.readFileSync(path.join(temp, name + '.png')));
    assert.deepEqual(images[1], images[2]);
    assert.notDeepEqual(images[0], images[1]);
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
});

const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const studio = require('../index.js');
const { KIT, PixelLook, makeBuilder } = studio.load();

const view = { w: 120, h: 80, px: 1, ortho: true };
const targets = { targets: [
  { material: 'clay', palette: ['#127844'] },
  { object: 'right', material: 'clay', palette: ['#a63955'] }
] };
function build(makeBuilder, look) {
  const b = makeBuilder(7, [0x101421, 0x808080]);
  for (const [x, object] of [[-.8, 'left'], [.8, 'right']]) {
    const start = b.count();
    b.disc(x, 0, 0, [0, 0, 1], .47, .035, b.P[1], 3);
    b.describeSplats(start, b.count(), { object, material: 'clay' });
  }
  return b.finish({ cam: { target: [0, 0, 0], dist: 5, yaw: 0, pitch: 0 }, look });
}

test('palette constraints reserve exact swatches and dither between allowed candidates', () => {
  const definition = { palette: ['#000000', '#ffffff', 'accent'], reserved: ['accent'],
    dither: { pattern: 'checker', strength: 1 } };
  const plan = PixelLook.preparePalette(definition, { palette: [0xff0000], roles: { accent: [0] } });
  assert.deepEqual(plan.packed, [0, 0xffffff, 0xff0000]);
  assert.equal(plan.index([1, 0, 0], 0, 0), 2);
  assert.notEqual(plan.index([.98, 0, 0], 0, 0), 2);
  assert.equal(plan.index([.45, .45, .45], 0, 0), 1);
  assert.equal(plan.index([.45, .45, .45], 1, 0), 0);
  assert.equal(plan.index([.45, .45, .45], -1, -1), 1);
  assert.equal(plan.index([.45, .45, .45], 0, 0, false), 0);
  assert.throws(() => PixelLook.preparePalette({ ...definition, reserved: ['#010203'], dither: { strength: 2 } },
    { palette: [0xff0000], roles: { accent: [0] } }), /strength/);
  const blue = seed => PixelLook.preparePalette({ palette: ['#000000', '#ffffff'],
    dither: { pattern: 'blue-noise', strength: 1, seed } }, { blueNoise: KIT.procedural.materials.blueNoise });
  assert.deepEqual(blue(1).ranks, blue(1).ranks);
  assert.notDeepEqual(blue(1).ranks, blue(2).ranks);
});

test('renderer routes native, colored and coverage resolves by visible object and material', () => {
  const world = build(makeBuilder, { paletteConstraints: targets });
  const pixel = ({ rgb, w }, x, y) => Array.from(rgb.slice((y * w + x) * 3, (y * w + x) * 3 + 3));
  for (const options of [{ clean: true }, { colored: true }, { stable: { resolve: 'coverage' } },
    { stable: { resolve: 'clusters', dither: 'object' } }]) {
    const image = studio.render(world, { ...view, ...options });
    assert.deepEqual(pixel(image, 41, 40), [0x12, 0x78, 0x44]);
    assert.deepEqual(pixel(image, 79, 40), [0xa6, 0x39, 0x55]);
    assert.deepEqual(pixel(image, 0, 0), [0x10, 0x14, 0x21]);
    assert(image.palette.includes(0x127844) && image.palette.includes(0xa63955));
  }
  const off = studio.render(world, { ...view, paletteConstraints: false });
  assert.deepEqual(pixel(off, 41, 40), [0x80, 0x80, 0x80]);
  assert.deepEqual(studio.render(world, { ...view, raw: true }).rgb,
    studio.render(world, { ...view, raw: true, paletteConstraints: false }).rgb);
});

test('diorama validation and bake retain the names targeted by palette constraints', () => {
  const spec = {
    id: 'palette-targets',
    solids: [{ id: 'gate', kind: 'box', at: [0, 0, 0], half: [.4, .5, .3], mat: 'stone' }],
    finish: { look: { paletteConstraints: { targets: [{ object: 'gate', material: 'stone', palette: ['#556633'] }] } } }
  };
  const world = KIT.diorama.build(spec);
  const metadata = world.renderMetadata;
  assert(metadata.objects.includes('gate') && metadata.materials.includes('stone'));
  const plan = PixelLook.preparePaletteConstraints(world.look.paletteConstraints, { palette: world.pal });
  assert(plan.slots(world).some(slot => slot === 1));
  spec.finish.look.paletteConstraints.targets[0].dither = { pattern: 'unknown' };
  assert.throws(() => KIT.diorama.build(spec), /finish\.look\.paletteConstraints/);
});

function checkWebGL(createRenderer, build, targets, expected) {
  const world = build(makeBuilder, { paletteConstraints: targets });
  const canvas = document.querySelector('canvas');
  const renderer = createRenderer(canvas, { toolkit: { KIT, PixelLook } });
  const gl = canvas.getContext('webgl2');
  function check(options) {
    renderer.render(world, { ortho: true, dither: 0, outline: false, ...options });
    const pixels = new Uint8Array(canvas.width * canvas.height * 4);
    gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    const pixel = (x, y) => pixels.slice(((canvas.height - 1 - y) * canvas.width + x) * 4,
      ((canvas.height - 1 - y) * canvas.width + x) * 4 + 3).join();
    if (expected.some(([x, y, rgb]) => pixel(x, y) !== rgb.join()))
      throw new Error('GPU did not match CPU target palette at a sample pixel');
  }
  check({ colored: false, clean: true });
  check({ colored: true });
  const waterBodies = KIT.procedural.waterBodies;
  world.water = waterBodies.scene([waterBodies.create({
    id: 'water', bounds: { min: [-2, -2], max: [2, 2] }, sample: () => ({ bed: -2, surface: -1 })
  })]);
  check({ colored: false });
  delete world.water;
  targets.targets[1].palette[0] = '#070809';
  expected[1][2] = [7, 8, 9];
  check({ colored: false });
  Object.assign(targets.targets[0], { palette: ['#000000', '#ffffff'], dither: { pattern: 'checker', strength: 1 } });
  renderer.render(world, { ortho: true, colored: false, dither: 0, outline: false });
  const stripe = new Uint8Array(4 * 4);
  gl.readPixels(40, 39, 4, 1, gl.RGBA, gl.UNSIGNED_BYTE, stripe);
  if (new Set([stripe[0], stripe[4], stripe[8], stripe[12]]).size !== 2 || stripe[0] !== stripe[8] || stripe[4] !== stripe[12])
    throw new Error('GPU did not use the target checker pattern');
  const paletteConstraints = { default: { source: 'graded', palette: ['#080c10', '#b6ced0'] } };
  const colorStack = { name: 'Lower exposure', steps: [{ type: 'exposure', stops: -4 }] };
  expected[0][2] = expected[1][2] = [8, 12, 16];
  expected[2][2] = [1, 1, 2];
  check({ colored: false, colorStack, paletteConstraints });
  check({ colored: true, colorStack, paletteConstraints });
  const selected = { targets: [{ select: { entity: 'right' }, stack: colorStack }] };
  expected[0][2] = [128, 128, 128];
  expected[1][2] = [8, 8, 8];
  expected[2][2] = [16, 20, 33];
  check({ colored: false, paletteConstraints: selected });
  check({ colored: true, paletteConstraints: selected });
  renderer.dispose();
}

test('WebGL uses the same target palettes as the CPU and accepts live edits', { skip: !process.env.INK_TEST_CHROME }, () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-constraints-'));
  const page = path.join(temp, 'constraints.html');
  const image = studio.render(build(makeBuilder, { paletteConstraints: targets }), view);
  const expected = [[41, 40], [79, 40], [0, 0]].map(([x, y]) =>
    [x, y, Array.from(image.rgb.slice((y * view.w + x) * 3, (y * view.w + x) * 3 + 3))]);
  try {
    fs.writeFileSync(path.join(temp, 'bundle.js'), studio.bundle());
    fs.writeFileSync(page, `<!doctype html><canvas width="120" height="80"></canvas><pre id="result">PENDING</pre>
<script src="bundle.js"></script><script type="module">
import { createRenderer } from ${JSON.stringify(pathToFileURL(path.resolve(__dirname, '../webgl.mjs')).href)};
const result = document.querySelector('#result');
try {
  (${checkWebGL.toString()})(createRenderer, ${build.toString()}, ${JSON.stringify(targets)}, ${JSON.stringify(expected)});
  result.textContent = 'PASS';
} catch (error) { result.textContent = error.stack; }
</script>`);
    const html = execFileSync(process.env.INK_TEST_CHROME, ['--headless', '--no-first-run', '--disable-background-networking',
      '--allow-file-access-from-files', '--enable-unsafe-swiftshader', '--use-angle=swiftshader',
      '--user-data-dir=' + path.join(temp, 'profile'), '--dump-dom', pathToFileURL(page).href],
    { timeout: 60000, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    assert.equal(html.match(/<pre id="result">([^<]*)<\/pre>/)?.[1], 'PASS');
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
});

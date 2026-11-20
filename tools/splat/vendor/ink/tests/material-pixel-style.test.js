const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const ink = require('..');
const { KIT, makeBuilder, makeSculpt, SplatProvenance } = ink.load();

function plates(makeBuilder, makeSculpt, style, pixel = false) {
  const b = makeBuilder(11, [0, 0x505050, 0xc0c0c0]);
  const s = makeSculpt(b);
  Object.assign(s, { amb: .5, sky: 0, sunK: 0, aoK: 0, pixel });
  s.box([-1.15, 0, 0], [.66, .61, .19], { r: [1, 2], pixelStyle: style }, { res: .15 });
  s.box([1.15, 0, 0], [.66, .61, .19], { r: [1, 2] }, { res: .15 });
  s.bake();
  return b.finish({ cam: { target: [0, 0, 0], dist: 7, pitch: 0, yaw: 0 },
    radius: 7, detail: 12, look: { pixel }, dither: 0 });
}

function sphere(style) {
  const shades = Array.from({ length: 12 }, (_, i) => 0x151515 + i * 0x101010);
  const builder = makeBuilder(17, [0, ...shades]);
  const s = makeSculpt(builder);
  Object.assign(s, { amb: .22, sky: .07, sunK: .57, aoK: 0, sun: [0, 0, 1], view: [0, 0, 1] });
  s.ball([0, 0, 0], .8, { r: shades.map((_, i) => i + 1), pixelStyle: style }, { res: .17 });
  s.bake();
  return builder.finish({ cam: { target: [0, 0, 0], dist: 7, pitch: 0, yaw: 0 }, detail: 12, radius: 8 });
}

const view = { w: 96, h: 64, px: 1, dither: 0 };
function scan(pixels, stride, x, y = 31) {
  return Array.from({ length: 6 }, (_, i) => pixels[(y * 96 + x + i) * stride]);
}

test('material ramp dithering follows the art grid and leaves its neighbor alone', () => {
  for (const pixel of [false, true]) {
    const frame = ink.render(plates(makeBuilder, makeSculpt, { dither: 'checker' }, pixel), view);
    assert.deepEqual(scan(frame.rgb, 3, 30), [192, 80, 192, 80, 192, 80]);
    assert.deepEqual(scan(frame.rgb, 3, 59), [80, 80, 80, 80, 80, 80]);
    const diagonal = ink.render(plates(makeBuilder, makeSculpt, { dither: 'diagonal' }, pixel), view);
    assert.notDeepEqual(scan(diagonal.rgb, 3, 30), scan(frame.rgb, 3, 30));
  }
});

test('hardness controls coverage while highlight shape and step count change baked shading', () => {
  const coverage = (edgeHardness, splatFilter) =>
    ink.render(sphere({ edgeHardness }), { ...view, splatFilter, passes: ['coverage'] }).passes.coverage;
  for (const filter of [undefined, 'footprint']) {
    const soft = coverage(0, filter), hard = coverage(1, filter);
    assert(soft.some((value, i) => value > .05 && hard[i] === 0));
  }
  const colors = world => world.data.filter((_, i) => i % 16 === 7);
  assert(new Set(colors(sphere())).size > 2);
  assert.equal(new Set(colors(sphere({ shadeSteps: 2 }))).size, 2);
  const spot = colors(sphere({ highlight: 'spot' }));
  const streak = colors(sphere({ highlight: 'streak' }));
  const rim = colors(sphere({ highlight: { shape: 'rim', strength: 1 } }));
  assert.notDeepEqual(spot, streak);
  assert.notDeepEqual(spot, rim);
  assert.notDeepEqual(streak, rim);
  assert.notDeepEqual(rim, colors(sphere()));
});

test('JSON accepts material styles and splat subsets and joins retain the baked attributes', () => {
  const spec = { id: 'material-style', solids: [
    { kind: 'ball', at: [0, 0, 0], r: .7, mat: { role: 'stone', pixelStyle: { edgeHardness: .9 } } }
  ] };
  const world = KIT.diorama.build(spec);
  assert(Math.abs(world.materialPixelStyles[0] - 1.9) < 1e-6);
  const styled = SplatProvenance.subset(world, [1, 0]);
  const ordinary = SplatProvenance.subset(sphere(), []);
  ordinary.pal = styled.pal;
  const joined = SplatProvenance.join([ordinary, styled]);
  assert.deepEqual(joined.materialPixelStyles, world.materialPixelStyles.slice(0, 8));
  spec.solids[0].mat.pixelStyle.shadeSteps = 1;
  assert.throws(() => KIT.diorama.build(spec), /mat\.pixelStyle[\s\S]*shadeSteps/);
});

test('ray coverage matches the material edge control', () => {
  const b = makeBuilder(2, [0, 0xffffff]);
  b.disc(0, 0, 0, [0, 0, 1], .45, .025, b.P[1], 3);
  const world = b.finish(), edge = Math.sqrt(2 * world.data[4] * Math.log(3 / .42));
  function pick(hardness) {
    return ink.createSplatPicker({ ...world, materialPixelStyles: Float32Array.of(1 + hardness, 0, 0, 0) })
      .ray({ origin: [edge, 0, 2], direction: [0, 0, -1], maxDistance: 4 });
  }
  assert(pick(0).dominant?.alpha > 0);
  assert.equal(pick(1).dominant, null);
});

function checkWebGL(createRenderer, createSplatInstances, plates, scan, makeBuilder, makeSculpt, toolkit) {
  const canvas = document.querySelector('canvas');
  const renderer = createRenderer(canvas, { toolkit });
  const gl = canvas.getContext('webgl2'), pixels = new Uint8Array(96 * 64 * 4);
  function draw(world, frame = {}) {
    renderer.render(world, { width: 96, height: 64, dither: 0, colored: false, damp: false, ...frame });
    gl.readPixels(0, 0, 96, 64, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    if (gl.getError()) throw Error('Unexpected WebGL error');
    return scan(pixels, 4, 30, 32);
  }
  function checker(row, label) {
    if (new Set(row).size !== 2 || row.some((v, i) => i >= 2 && v !== row[i - 2]))
      throw Error(label + ' did not alternate: ' + row);
  }
  for (const pixel of [false, true]) {
    const world = plates(makeBuilder, makeSculpt, { dither: 'checker', edgeHardness: .85 }, pixel);
    checker(draw(world), pixel ? 'per-pixel shader' : 'splat shader');
  }
  checker(draw(plates(makeBuilder, makeSculpt, { dither: 'checker' }), { colored: true }), 'colored contours');
  checker(draw(plates(makeBuilder, makeSculpt, { dither: 'checker' }), {
    coverageAware: true, paletteConstraints: { default: { palette: ['#505050', '#c0c0c0'] } }
  }), 'coverage-aware palette');
  draw(plates(makeBuilder, makeSculpt, { edgeHardness: 0 }));
  const soft = pixels.slice();
  draw(plates(makeBuilder, makeSculpt, { edgeHardness: 1 }));
  if (!pixels.some((v, i) => v !== soft[i] && (i >> 2) % 96 < 48) ||
      pixels.some((v, i) => v !== soft[i] && (i >> 2) % 96 >= 48))
    throw Error('Edge hardness did not stay scoped to the authored material');
  const prototype = plates(makeBuilder, makeSculpt, { dither: 'checker', edgeHardness: 1 });
  const base = makeBuilder(11, prototype.pal).finish({ cam: prototype.cam, radius: 7, detail: 12, dither: 0 });
  const instances = createSplatInstances({ prototype }, [{ id: 'plate', prototype: 'prototype' }]);
  const initial = draw(base, { instances });
  checker(initial, 'shared-instance shader');
  if (String(initial) !== String(draw(instances.flatten(base)))) throw Error('Expanded instance lost its authored style');
  instances.update('plate', { palette: { '#c0c0c0': '#505050' } });
  const recolored = draw(base, { instances });
  if (new Set(recolored).size !== 1 || String(recolored) !== String(draw(instances.flatten(base))))
    throw Error('Instance palette failed to recolor a borrowed shade: ' + recolored);
  renderer.dispose();
}

test('WebGL applies authored patterns on splats, pixel surfaces and shared instances', { skip: !process.env.INK_TEST_CHROME }, () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-material-pixel-'));
  const page = path.join(temp, 'style.html');
  try {
    fs.writeFileSync(path.join(temp, 'bundle.js'), ink.bundle());
    fs.writeFileSync(page, `<!doctype html><canvas width="96" height="64"></canvas><pre id="result">PENDING</pre>
<script src="bundle.js"></script><script type="module">
import { createRenderer, createSplatInstances } from ${JSON.stringify(pathToFileURL(path.resolve(__dirname, '../webgl.mjs')).href)};
const result = document.querySelector('#result');
try {
  (${checkWebGL})(createRenderer, createSplatInstances, ${plates}, ${scan}, makeBuilder, makeSculpt, { KIT, PixelLook });
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

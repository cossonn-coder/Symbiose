const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const ink = require('..');
const PNG = require('../cli/png.js');
const { makeBuilder, makeSculpt, PaintCorrections, SplatProvenance } = ink.load();

const palette = [0, 0x505050, 0xbb0000, 0x0000bb, 0x880088, 0x557755];
const at = [0, 0, .27, 0, 0, 1];
const direction = angle => [Math.sin(angle), 0, Math.cos(angle)];
const center = 32 * 96 + 48;
const view = { w: 96, h: 64, px: 1, yaw: 0, ortho: true, dither: 0 };

function makeWorld(B, S, pixel, occluded = false) {
  const b = B(11, [0, 0x505050, 0xbb0000, 0x0000bb, 0x880088, 0x557755]);
  const s = S(b);
  Object.assign(s, { pixel, amb: 1, sky: 0, sunK: 0, aoK: 0 });
  s.box([0, 0, 0], [1, 1, .25], { r: [1] }, { res: .11 });
  if (occluded) s.box([0, 0, .65], [.35, .35, .08], { r: [5] }, { res: .08 });
  s.bake();
  return b.finish({
    cam: { target: [0, 0, 0], dist: 5, pitch: 0, yaw: 0 }, detail: 8, radius: 4,
    look: { pixel }, dither: 0, paint: { layers: [
      { id: 'front', view: { direction: [0, 0, 1] }, angle: 55, feather: 35, decals: [[0, 0, .27, 0, 0, 1, 2]] },
      { id: 'side', view: { direction: [Math.sqrt(3) / 2, 0, .5] }, angle: 55, feather: 35,
        decals: [[0, 0, .27, 0, 0, 1, 3]] }
    ] }
  });
}
const rgb = (image, i) => Array.from(image.slice(i * 3, i * 3 + 3));

test('nearby paint samples blend on a carrier and retain per-layer and per-sample masks', () => {
  const b = makeBuilder(1, palette);
  const world = b.finish({ detail: 10, paint: { layers: [
    { id: 'left', view: { direction: direction(0) }, angle: 50, feather: 30,
      decals: [[...at, 2], [.5, 0, .27, 0, 0, 1, 2, .5]] },
    { id: 'right', view: { direction: direction(Math.PI / 3) }, angle: 50, feather: 30,
      region: { min: [-.2, -.5, 0], max: [.2, .5, .5], feather: .1 },
      decals: [[.01, 0, .27, 0, 0, 1, 3], [.5, 0, .27, 0, 0, 1, 3]] },
    { id: 'back', view: { direction: [0, 0, -1] },
      decals: [[0, 0, .27, 0, 0, -1, 5]] }
  ] } });
  const plan = world.paintCorrections, data = world.data.slice();
  assert.equal(plan.rows.length, 3);
  const sample = angle => plan.paint(data, palette, { direction: direction(angle) });
  assert(sample(0));
  assert.equal(data[7], 0xbb);
  assert(Math.abs(data[19] - .495) < 1e-6);
  assert.equal(data[35], 0);
  assert(sample(Math.PI / 6));
  assert.equal(data[7] & 255, data[7] >> 16);
  assert(data[7] & 255);
  assert(sample(Math.PI / 3));
  assert.equal(data[7], 0xbb0000);
  assert.equal(data[19], 0);
  assert(sample(Math.PI));
  assert.equal(data[3], 0);
  assert(data[35] > .9);
  assert.equal(world.data[3], 0);
  const reversed = SplatProvenance.subset(world, [2, 0]);
  assert.deepEqual(reversed.paintCorrections.rows.map(row => row.index), [1, 0]);
  const joined = SplatProvenance.join([world, reversed]);
  assert.equal(joined.paintCorrections.rows.length, 5);
  assert.throws(() => PaintCorrections.layer({ id: 'wrong', view: { direction: [1, 0, 0] }, opacity: 2 }), /opacity/);
});

test('CPU paint fades with angle, respects surface occlusion and leaves packed rows reusable', () => {
  for (const pixel of [false, true]) {
    const w = makeWorld(makeBuilder, makeSculpt, pixel), saved = w.data.slice();
    const frame = options => ink.render(w, { ...view, ...options }).rgb;
    assert.deepEqual(rgb(frame({}), center), [187, 0, 0]);
    assert.deepEqual(rgb(frame({ paintCorrections: false }), center), [80, 80, 80]);
    const between = frame({ yaw: Math.PI / 6 });
    assert(between.some((value, i) => i % 3 === 0 && value === 136 && between[i + 2] === 136));
    assert.deepEqual(frame({ yaw: Math.PI }), frame({ yaw: Math.PI, paintCorrections: false }));
    assert.deepEqual(w.data, saved);
    const blocked = makeWorld(makeBuilder, makeSculpt, pixel, true);
    assert.deepEqual(ink.render(blocked, view).rgb, ink.render(blocked, { ...view, paintCorrections: false }).rgb);
  }
});

test('CLI retains multiple named captures, masks and legacy decals independently', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-paint-captures-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const scene = path.join(dir, 'scene.json'), output = path.join(dir, 'decals.json');
  const old = [[0, .42, .27, 0, 0, 1, 8]];
  fs.writeFileSync(output, JSON.stringify({ decals: old }));
  fs.writeFileSync(scene, JSON.stringify({ id: 'paint-check', camera: { target: [0, 0, 0], yaw: 0, pitch: 0, dist: 5 },
    finish: { look: { pixel: true } },
    solids: [{ kind: 'box', at: [0, 0, 0], half: [1, 1, .25], mat: 'stone', res: .12 }]
  }));
  const cli = (...args) => execFileSync(process.execPath, [path.resolve(__dirname, '../cli/ink-studio.js'),
    'paint', args[0], scene, '--dir', dir, ...args.slice(1)], { cwd: dir, encoding: 'utf8' });
  function capture(name, yaw, color, grayscale) {
    cli('export', '--layer', name, '--ortho', '--yaw', String(yaw), '--w', '96', '--h', '64', '--px', '1');
    const folder = path.join(dir, 'layers', name), painted = path.join(folder, 'paint.png');
    const { rgb, w, h } = PNG.read(painted);
    for (let y = 29; y <= 35; y++) for (let x = 45; x <= 51; x++) rgb.set(color, (y * w + x) * 3);
    PNG.write(painted, w, h, rgb);
    const mask = path.join(folder, 'mask.png');
    PNG.write(mask, w, h, new Uint8Array(w * h * 3).fill(grayscale));
    cli('absorb', '--layer', name, '--paint-mask', mask, '--angle', '70', '--opacity', '.8');
  }
  capture('front', 0, [255, 120, 10], 128);
  capture('left', -.4, [100, 180, 220], 255);
  const retained = () => JSON.parse(fs.readFileSync(output, 'utf8'));
  assert.deepEqual(retained().decals, old);
  assert.deepEqual(retained().layers.map(layer => layer.id), ['front', 'left']);
  for (const [i, layer] of retained().layers.entries()) {
    assert(layer.decals.length > 10);
    assert(Math.abs(layer.decals[0][7] - (i ? 1 : 128 / 255)) < 1e-6);
    assert.equal(layer.view.eye, undefined);
  }
  assert.notDeepEqual(retained().layers[0].view.direction, retained().layers[1].view.direction);
  cli('tune', '--layer', 'left', '--region', '{"min":[-1,-1,0],"max":[0,1,1],"feather":0.1}', '--opacity', '.4');
  const report = JSON.parse(cli('layers'));
  assert.equal(report.permanent, 1);
  assert.equal(report.layers[1].opacity, .4);
  assert.deepEqual(report.layers[1].region.max, [0, 1, 1]);
  cli('clear', '--layer', 'front');
  assert.deepEqual(retained().layers.map(layer => layer.id), ['left']);
  assert.deepEqual(retained().decals, old);
});

test('WebGL updates painted views with unchanged source rows, including patterned surfaces', { skip: !process.env.INK_TEST_CHROME }, t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-paint-gl-')), page = path.join(dir, 'paint.html');
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  fs.writeFileSync(path.join(dir, 'bundle.js'), ink.bundle());
  fs.writeFileSync(page, `<!doctype html><canvas width="96" height="64"></canvas><pre id="result">PENDING</pre>
<script src="bundle.js"></script><script type="module">
import { createRenderer } from ${JSON.stringify(pathToFileURL(path.resolve(__dirname, '../webgl.mjs')).href)};
const result = document.querySelector('#result');
try {
  const canvas = document.querySelector('canvas'), renderer = createRenderer(canvas, { toolkit: { KIT, PixelLook } });
  const gl = canvas.getContext('webgl2'), build = ${makeWorld.toString()};
  const read = (world, yaw, enabled = true, raw = false) => {
    const rgba = new Uint8Array(96 * 64 * 4);
    renderer.render(world, { width: 96, height: 64, colored: false, dither: 0, changedRows: [],
      damp: false, camera: { yaw, ortho: true }, paintCorrections: enabled, raw });
    gl.readPixels(0, 0, 96, 64, gl.RGBA, gl.UNSIGNED_BYTE, rgba);
    if (gl.getError()) throw Error('WebGL paint pass failed');
    return rgba;
  };
  const has = (data, r, g, b) => data.some((v, i) => i % 4 === 0 && v === r && data[i + 1] === g && data[i + 2] === b);
  for (const pixel of [false, true]) {
    const world = build(makeBuilder, makeSculpt, pixel);
    const front = read(world, 0), between = read(world, Math.PI / 6);
    if (!has(front, 187, 0, 0) || !has(between, 136, 0, 136)) throw Error('Corrections did not blend at their angles ' + pixel);
    if (has(read(world, 0, false), 187, 0, 0)) throw Error('Turning paint off left stale rows');
    if (String(read(world, Math.PI)) !== String(read(world, Math.PI, false))) throw Error('Paint showed from behind');
    const blocked = build(makeBuilder, makeSculpt, pixel, true);
    if (String(read(blocked, 0)) !== String(read(blocked, 0, false))) throw Error('Paint showed through an occluder');
    if (String(read(world, 0)) !== String(front)) throw Error('Changing angles modified the source splats');
  }
  renderer.dispose();
  result.textContent = 'PASS';
} catch (error) { result.textContent = error.stack; }
</script>`);
  const html = execFileSync(process.env.INK_TEST_CHROME, ['--headless', '--no-first-run', '--disable-background-networking',
    '--allow-file-access-from-files', '--enable-unsafe-swiftshader', '--use-angle=swiftshader',
    '--user-data-dir=' + path.join(dir, 'profile'), '--dump-dom', pathToFileURL(page).href],
  { encoding: 'utf8', timeout: 30000, stdio: ['ignore', 'pipe', 'ignore'] });
  assert.match(html, /<pre id="result">PASS<\/pre>/, html.match(/<pre[^>]*>([\s\S]*?)<\/pre>/)?.[1] || html);
});

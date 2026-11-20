const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const ink = require('..');
const PNG = require('../cli/png.js');
const { KIT, makeBuilder } = ink.load();
const options = { w: 112, h: 80, px: 1, ortho: true, dither: 0, outline: false };
const rig = { lights: { key: { at: [-.85, 0, 1], range: 1.65, intensity: 1.4, color: '#ff7878' } } };
const shifted = { lights: { key: { at: [.85, 0, 1] } } };
const neutral = { lights: { key: null } };

function plates(B, K, mode = 'fine') {
  const palette = [0, 0x606060, 0x702a2a, 0x2a2a70, 0x207720, 0x272727, 0x444444, 0x808080,
    0xaaaaaa, 0x9b2d2d, 0xc85353, 0x532e7a, 0x806363, 0x9f6363, 0x723d3d, 0x303030];
  const b = B(21, palette);
  const patterned = K.pixel.tiles({ r: [5, 6, 1, 7, 8], px: .08 });
  const pattern = K.pixel.edge(patterned, { up: [K.sprite.art('#')], share: 1 }).pat;
  for (const x of [-.85, .85]) {
    if (mode === 'fine') {
      const row = 2 + 64 * 3 + 64 ** 2 * 2 + 64 ** 3 * 3;
      b.fineTile(row, row, row, row, .48, 0, 0, 0, .48, 0, b.P[1]);
    }
    if (mode === 'pattern') b.pixNext([5, 6, 1, 7, 8], .52, pattern, 0, 0, 1);
    b.disc(x, 0, 0, [0, 0, 1], .45, .03, b.P[1], 3);
    b.describeSplats(b.count() - 1, b.count(), { object: x < 0 ? 'left' : 'right' });
  }
  b.disc(0, .74, .04, [0, 0, 1], .13, .02, b.P[4], 3, { em: true });
  const world = b.finish({
    cam: { target: [0, 0, 0], dist: 4.6, yaw: 0, pitch: 0 }, dither: 0, radius: 4, detail: 12,
    look: { pixel: mode === 'pattern', fine: mode === 'fine' }
  });
  if (world.pix) {
    world.pixTex = K.pixel.evaluators(world);
    world.pixCell = K.pixel.CELL;
    world.pixUnfold = K.pixel.unfold;
    world.pixAnchors = K.pixel.anchors;
  }
  return world;
}
const pixel = (image, x, y) => Array.from(image.rgb.subarray((y * image.w + x) * 3, (y * image.w + x) * 3 + 3));
const ref = { primarySun: 'main', bodies: [{ id: 'main', kind: 'sun', color: '#ffffff',
  keys: [{ at: 0, azimuth: 0, elevation: .35 }, { at: 4, azimuth: 0, elevation: -.35 }] }] };

test('moving, targeting and removing lamps changes the same baked rows and retains fine texel colors', () => {
  const w = plates(makeBuilder, KIT), { data, fine } = w, saved = data.slice(), tiles = fine.slice();
  w.relighting = rig;
  const draw = relighting => ink.render(w, { ...options, raw: true, fine: true, relighting });
  const base = draw(false), left = draw(true), right = draw(shifted);
  assert.deepEqual(draw(neutral).rgb, base.rgb);
  const colors = new Set();
  for (let y = 29; y < 49; y++) for (let x = 27; x < 41; x++) {
    const before = pixel(base, x, y), after = pixel(left, x, y);
    if (before[0] > 70 && before[2] < 60) colors.add('red');
    if (before[2] > 70 && before[0] < 60) colors.add('blue');
    if (before[0] > 70 && before[2] < 60) assert(after[0] > before[0] && after[0] > after[2]);
    if (before[2] > 70 && before[0] < 60) assert(after[2] > after[0]);
    assert.deepEqual(pixel(right, x, y), before);
  }
  assert.deepEqual([...colors].sort(), ['blue', 'red']);
  assert.notDeepEqual(left.rgb, base.rgb);
  assert.notDeepEqual(right.rgb, base.rgb);
  assert.deepEqual(pixel(left, 56, 20), pixel(base, 56, 20));
  const excluded = draw({ lights: { key: { select: { object: 'right' } } } });
  assert.deepEqual(excluded.rgb, base.rgb);
  assert.deepEqual(data, saved);
  assert.deepEqual(fine, tiles);
});

test('time of day changes surface illumination independently of scene time', () => {
  const w = plates(makeBuilder, KIT, 'plain');
  w.relighting = true;
  w.celestialTracks = ref;
  const render = (skyTime, relighting) => ink.render(w, { ...options, raw: true, t: 7, skyTime, relighting, atmosphere: false });
  const noon = render(0), night = render(4), reference = render(0, false);
  assert.deepEqual(pixel(noon, 35, 40), pixel(reference, 35, 40));
  assert(pixel(night, 35, 40)[0] < pixel(noon, 35, 40)[0] - 15);
  assert.deepEqual(pixel(night, 56, 20), pixel(noon, 56, 20));
  assert.throws(() => KIT.splatRelighting.settings({ lights: { key: { at: [1, 2, 3], color: 'red' } } }), /color/);
});

test('CLI applies a saved relight rig to a JSON scene without changing the source', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-splat-relight-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const file = path.join(dir, 'scene.json'), settings = path.join(dir, 'rig.json');
  const spec = { id: 'relight-check', camera: { target: [0, 0, 0], dist: 5, pitch: 0, yaw: 0 },
    solids: [{ id: 'face', kind: 'box', at: [0, 0, 0], half: [1, 1, .15], mat: 'stone', res: .08 }] };
  const text = JSON.stringify(spec);
  fs.writeFileSync(file, text);
  fs.writeFileSync(settings, JSON.stringify({ lights: { task: { at: [0, 0, 1], intensity: 2, color: '#ff2929' } } }));
  function frame(name, relighting) {
    const out = path.join(dir, name + '.png');
    execFileSync(process.execPath, [path.resolve(__dirname, '../cli/ink-studio.js'), 'render', file,
      '--relighting', relighting, '--w', '96', '--h', '64', '--px', '1', '--raw', '--out', out], { cwd: dir });
    return PNG.read(out).rgb;
  }
  assert.notDeepEqual(frame('reference', 'off'), frame('relit', settings));
  assert.equal(fs.readFileSync(file, 'utf8'), text);
});

test('WebGL keeps fine tiles and procedural surface patterns while relighting', { skip: !process.env.INK_TEST_CHROME }, t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-relight-gl-')), page = path.join(dir, 'relight.html');
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  fs.writeFileSync(path.join(dir, 'bundle.js'), ink.bundle());
  fs.writeFileSync(page, `<!doctype html><canvas width="112" height="80"></canvas><pre id="result">PENDING</pre>
<script src="bundle.js"></script><script type="module">
import { createRenderer, createSplatInstances } from ${JSON.stringify(pathToFileURL(path.resolve(__dirname, '../webgl.mjs')).href)};
const result = document.querySelector('#result');
try {
  const canvas = document.querySelector('canvas'), renderer = createRenderer(canvas, { toolkit: { KIT, PixelLook } });
  const gl = canvas.getContext('webgl2'), build = ${plates.toString()};
  const rig = ${JSON.stringify(rig)}, shift = ${JSON.stringify(shifted)};
  const draw = (world, relighting, frame = {}) => {
    const pixels = new Uint8Array(112 * 80 * 4);
    renderer.render(world, { width: 112, height: 80, colored: false, raw: false, dither: 0, outline: false,
      damp: false, changedRows: [], camera: { ortho: true }, relighting, ...frame });
    gl.readPixels(0, 0, 112, 80, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    if (gl.getError()) throw Error('WebGL relighting failed');
    return pixels;
  };
  function changes(a,b) {
    const sides = [0,0];
    for (let y = 22; y < 57; y++) for (let x = 0; x < 112; x++) {
      if (x >= 49 && x <= 63) continue;
      const i = (y * 112 + x) * 4;
      if (a[i] !== b[i] || a[i + 1] !== b[i + 1] || a[i + 2] !== b[i + 2]) sides[+(x > 56)]++;
    }
    return sides;
  }
  for (const mode of ['plain','fine','pattern']) {
    const world = build(makeBuilder, KIT, mode);
    world.relighting = rig;
    const base = draw(world, false), left = draw(world, true), right = draw(world, shift);
    const a = changes(base,left), b = changes(base,right);
    if (a[0] < 12 || a[1] || b[1] < 12 || b[0]) throw Error('Local light moved incorrectly for ' + mode + ': ' + a + ' / ' + b);
    if (String(draw(world, false)) !== String(base)) throw Error('The bake changed after moving a light');
    if (mode !== 'plain') {
      const detail = new Set();
      for (let y = 31; y < 48; y++) for (let x = 28; x < 41; x++) {
        const i = (y * 112 + x) * 4;
        if (base[i]) detail.add([left[i],left[i+1],left[i+2]].join('/'));
      }
      if (detail.size < 2) throw Error('Relighting flattened ' + mode);
    }
  }
  const day = build(makeBuilder, KIT, 'plain');
  day.relighting = true;
  day.celestialTracks = ${JSON.stringify(ref)};
  if (String(draw(day,true,{environment:false,skyTime:0})) === String(draw(day,true,{environment:false,skyTime:4})))
    throw Error('Time of day had no effect');
  const builder = makeBuilder(1, day.pal);
  builder.disc(0,0,0,[0,0,1],.4,.03,builder.P[1],3);
  const prototype = builder.finish();
  const empty = {...day, count:0, data:new Float32Array(0), renderMetadata:undefined, celestialTracks:undefined, relighting:rig};
  const copies = createSplatInstances({ prototype }, [{id:'placed',prototype:'prototype',position:[-.85,0,0]}]);
  const instanced = { raw:true, instances:copies };
  if (changes(draw(empty,false,instanced),draw(empty,true,instanced))[0] < 12)
    throw Error('The instance did not respond to the lamp');
  renderer.dispose();
  result.textContent = 'PASS';
} catch (error) { result.textContent = error.stack; }
</script>`);
  const html = execFileSync(process.env.INK_TEST_CHROME, ['--headless', '--no-first-run', '--disable-background-networking',
    '--allow-file-access-from-files', '--enable-unsafe-swiftshader', '--use-angle=swiftshader',
    '--user-data-dir=' + path.join(dir, 'profile'), '--dump-dom', pathToFileURL(page).href],
  { encoding: 'utf8', timeout: 60000, stdio: ['ignore', 'pipe', 'ignore'] });
  assert.match(html, /<pre id="result">PASS<\/pre>/, html.match(/<pre[^>]*>([\s\S]*?)<\/pre>/)?.[1] || html);
});

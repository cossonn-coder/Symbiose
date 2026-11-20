const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const ink = require('..');
const LiveSun = require('../cli/live-sun.js');
const PNG = require('../cli/png.js');
const { KIT, makeBuilder, makeSculpt, SplatProvenance } = ink.load();
const art = { ramp: [0, .5, 1], small: { belowPixels: 20, ramp: [.8, 1], strength: 0 } };

function authored(B, S, settings, pixel = false) {
  const b = B(1, [0x101010, 0x343434, 0x666666, 0x999999, 0xcccccc], { shadowArt: settings, initialCapacity: 16 });
  const s = S(b);
  Object.assign(s, { sun: [0, 1, 0], amb: .21, sky: 0, sunK: .75, wob: 0, aoK: 0, res: .11, pixel, captureAlbedo: true });
  s.box([0, -.11, 0], [1.6, .1, 1.6], { r: [1, 2, 3, 4], materialId: 'stone' },
    { objectId: 'floor', target: { entity: 'deck', tags: ['ground'] } });
  s.box([0, .65, 0], [.36, .12, .36], { r: [1, 2, 3, 4], materialId: 'wood' },
    { objectId: 'beam', target: { surface: 'canopy', tags: ['roof'] } });
  s.bake();
  return { s, world: b.finish({ cam: { target: [0, .05, 0], dist: 5, yaw: .65, pitch: .65 },
    radius: 5, detail: 10, look: { pixel }, dither: 0 }) };
}
function floorRows(w, radius = .15) {
  const { objectIds, objects } = w.renderMetadata;
  return Array.from(objectIds, (id, i) => {
    const q = i * 16;
    return objects[id] === 'floor' && w.data[q + 1] > -.03 &&
      Math.abs(w.data[q]) < radius && Math.abs(w.data[q + 2]) < radius ? i : -1;
  }).filter(i => i >= 0);
}
const shade = (w, i) => w.data[i * 16 + 7];
const options = { w: 100, h: 80, px: 1, dither: 0, ortho: true };

test('casting and receiving can be masked independently of the visible sculpt', () => {
  const bake = settings => authored(makeBuilder, makeSculpt, settings);
  const normal = bake({ ramp: [0, 1] });
  const ignoreCaster = bake({ cast: { include: [{ material: 'stone' }, { tag: 'roof' }], exclude: [{ surface: 'canopy' }] } });
  const ignoreReceiver = bake({ receive: { exclude: [{ entity: 'deck' }] } });
  const lowerShadow = bake({ ramp: [.34, 1] });
  const rows = floorRows(normal.world);
  assert(rows.length >= 4);
  for (const i of rows) {
    assert.equal(shade(normal.world, i), 0x343434);
    assert.equal(shade(ignoreCaster.world, i), 0xcccccc);
    assert.equal(shade(ignoreReceiver.world, i), 0xcccccc);
    assert.equal(shade(lowerShadow.world, i), 0x666666);
  }
  assert.equal(ignoreCaster.world.count, normal.world.count);
  assert(ignoreCaster.s.sdf(0, .65, 0) < 0);
  assert(ignoreCaster.s.shadowSdf(0, .65, 0) > 0);
  assert.equal(ignoreReceiver.s.shadowSdf(0, .65, 0), ignoreReceiver.s.sdf(0, .65, 0));
  assert.throws(() => KIT.shadowArt.prepare({ ramp: [.6, .1, 1] }), /ramp/);
  assert.throws(() => KIT.shadowArt.prepare({ cast: { include: [{ medium: 'mist' }] } }), /select solids/);
  assert.throws(() => KIT.shadowArt.prepare({ small: { belowPixels: 0 } }), /threshold/);
});

test('small-size shadow rows preserve palette and pixel metadata through frames and subsets', () => {
  for (const pixel of [false, true]) {
    const { world } = authored(makeBuilder, makeSculpt, art, pixel);
    const rows = floorRows(world), [i] = rows, saved = world.data.slice();
    assert.equal(KIT.shadowArt.frame(world, .04), world);
    const simplified = KIT.shadowArt.frame(world, .1);
    assert.equal(shade(simplified, i), 0xcccccc);
    assert.equal(shade(world, i), 0x343434);
    if (pixel) {
      assert(simplified.pix[i * 8] > 0);
      assert(simplified.pix[i * 8 + 1] > world.pix[i * 8 + 1]);
    }
    const subset = SplatProvenance.subset(world, rows);
    const joined = SplatProvenance.join([subset, subset]);
    assert.equal(shade(KIT.shadowArt.frame(joined, .1), rows.length), 0xcccccc);
    const raster = (zoom, shadowArt) => ink.render(world, { ...options, zoom, shadowArt }).rgb;
    assert.deepEqual(raster(1), raster(1, false));
    assert.notDeepEqual(raster(.55), raster(.55, false));
    assert.deepEqual(world.data, saved);
  }
});

test('live sun uses the same mask, ramp and scale controls', () => {
  const { world } = authored(makeBuilder, makeSculpt, art);
  const pose = { x: [], y: [], z: [], alpha: [], scale: [] };
  for (let i = 0; i < world.count; i++) {
    const q = i * 16;
    pose.x.push(world.data[q]); pose.y.push(world.data[q + 1]); pose.z.push(world.data[q + 2]);
    pose.alpha.push(world.data[q + 3]); pose.scale.push(1);
  }
  const normals = world.renderMetadata.normals;
  const normalAt = i => Array.from(normals.subarray(i * 3, i * 3 + 3));
  const sun = LiveSun.prepare({ direction: [0, 1, 0], mapSize: 80, filter: 0 }, undefined, 0);
  const [i] = floorRows(world), at = [pose.x[i], pose.y[i], pose.z[i]];
  function visibility(shadowArt, footprint = .03) {
    return LiveSun.create(sun, world, pose, normalAt, undefined, undefined, { shadowArt, footprint }).visibility(i, ...at);
  }
  assert.equal(visibility(false), 0);
  assert.equal(visibility({ ramp: [.45, 1] }), .45);
  assert.equal(visibility({ cast: { exclude: [{ tag: 'roof' }] } }), 1);
  assert.equal(visibility({ receive: { include: [{ material: 'wood' }] } }), 1);
  assert.equal(visibility(art, .1), 1);
  assert.notDeepEqual(ink.render(world, { ...options, liveSun: sun, shadowArt: { ramp: [.45, 1] } }).rgb,
    ink.render(world, { ...options, liveSun: sun, shadowArt: false }).rgb);
});

test('JSON and the CLI validate and apply shadow settings before baking', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-shadow-art-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const file = path.join(dir, 'scene.json'), settings = path.join(dir, 'shadows.json');
  const spec = { id: 'shadow-art', light: { sun: [0, 1, 0], amb: .21, sky: 0 },
    camera: { target: [0, .05, 0], dist: 5, yaw: .65, pitch: .65 }, finish: { look: { shadowArt: true } },
    solids: [
      { id: 'floor', kind: 'box', at: [0, -.11, 0], half: [1.6, .1, 1.6], mat: 'stone', res: .12 },
      { id: 'beam', kind: 'box', at: [0, .65, 0], half: [.36, .12, .36], mat: 'wood', res: .12 }
    ] };
  assert.match(KIT.diorama.report(KIT.diorama.check(spec)), /finish.look.shadowArt/);
  spec.finish.look.shadowArt = { ramp: [0, 1] };
  fs.writeFileSync(file, JSON.stringify(spec));
  fs.writeFileSync(settings, JSON.stringify({ cast: { include: [] } }));
  function render(name, extra) {
    const out = path.join(dir, name + '.png');
    execFileSync(process.execPath, [path.resolve(__dirname, '../cli/ink-studio.js'), 'render', file,
      '--w', '100', '--h', '80', '--px', '1', '--ortho', '--out', out, ...extra], { cwd: dir, encoding: 'utf8' });
    return PNG.read(out).rgb;
  }
  assert.notDeepEqual(render('baked', []), render('unshadowed', ['--shadow-art', settings]));
});

test('WebGL selects the smaller shadow look as the camera zooms out', { skip: !process.env.INK_TEST_CHROME }, t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-shadow-gl-')), page = path.join(dir, 'shadows.html');
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  fs.writeFileSync(path.join(dir, 'bundle.js'), ink.bundle());
  fs.writeFileSync(page, `<!doctype html><canvas width="100" height="80"></canvas><pre id="result">PENDING</pre>
<script src="bundle.js"></script><script type="module">
import { createRenderer } from ${JSON.stringify(pathToFileURL(path.resolve(__dirname, '../webgl.mjs')).href)};
const result = document.querySelector('#result');
try {
  const canvas = document.querySelector('canvas'), renderer = createRenderer(canvas, { toolkit: { KIT, PixelLook } });
  const gl = canvas.getContext('webgl2'), build = ${authored.toString()};
  const pixels = new Uint8Array(100 * 80 * 4);
  const draw = (world, dist, shadowArt) => {
    renderer.render(world, { width: 100, height: 80, camera: { ortho: true, dist },
      dither: 0, colored: false, changedRows: [], damp: false, shadowArt });
    gl.readPixels(0, 0, 100, 80, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    if (gl.getError()) throw Error('WebGL shadow frame failed');
    return pixels.join(',');
  };
  for (const pixel of [false, true]) {
    const { world } = build(makeBuilder, makeSculpt, ${JSON.stringify(art)}, pixel);
    const near = draw(world, 5);
    if (near !== draw(world, 5, false)) throw Error('Small shadows activated too early');
    if (draw(world, 9) === draw(world, 9, false)) throw Error('Missing simplified shadows when zoomed out');
    if (draw(world, 5) !== near) throw Error('The alternate frame changed baked data');
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

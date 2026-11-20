const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const ink = require('..');
const { KIT: K, makeBuilder, makeSculpt } = ink.load();
const sculpt = () => K.sculpt(makeSculpt(makeBuilder(3)));
const square = [[0, 0], [1, 0], [1, 1], [0, 1]];
const hole = [[.35, .35], [.65, .35], [.65, .65], [.35, .65]];
const cylinder = { kind: 'cylinder', origin: [0, 0, 0], radius: 1, height: 2 };
const spec = {
  id: 'drawings', seed: 7, camera: { target: [.5, .3, 0], yaw: 0, pitch: 0, dist: 4 },
  solids: [
    { id: 'brush', kind: 'stroke', points: [[-.5, -.25, 0], [1.5, -.25, 0]],
      width: .2, depth: .08, pressure: [.5, 1], taper: [.4, 1], mat: 'ember' },
    { id: 'shape', kind: 'fill', rings: [square, hole], depth: .1, mat: 'moss' }
  ]
};

test('brush pressure, taper, depth and dabs affect the signed geometry', () => {
  const s = sculpt(), { sd } = s.stroke({
    points: [[0, 0, 0], [2, 0, 0], [4, 0, 0]], width: 1, depth: .24,
    pressure: [1, .25, 1], taper: [0, 1], axis: [0, 1, 0]
  }, [3]);
  assert(sd(0, 0, .01) > 0);
  assert(sd(2, 0, .05) < 0);
  assert(sd(2, 0, .08) > 0);
  assert(sd(3.99, 0, .4) < 0);
  assert(sd(3.99, .13, 0) > 0);
  const opposed = s.stroke({
    points: [[0, 0, 0], [2, 0, 0]], width: 1, pressure: [0, 1], taper: [1, 0]
  }, [3]);
  assert(opposed.sd(1, 0, .1) < 0 && opposed.sd(1, 0, .15) > 0);
  const dab = s.stroke({ points: [[1, 2, 3], [1, 2, 3]], pressure: [.2, .5], width: 1 }, [3]);
  assert(dab.sd(1.2, 2, 3) < 0 && dab.sd(1.3, 2, 3) > 0);
  const invisible = s.stroke({ points: [[9, 9, 9]], pressure: [0] }, [3]);
  invisible.sample(() => assert.fail('Zero pressure should emit no samples'));
  assert(s.sdf(9, 9, 9) > 0);
});

test('fills retain holes, frame orientation and outward surface depth', () => {
  const s = sculpt();
  const framed = s.fill({ rings: [square, hole], frame: { origin: [2, 1, 0], u: [0, 1, 0], v: [0, 0, 1] },
    depth: .2 }, [3]);
  assert(framed.sd(2.09, 1.25, .25) < 0);
  assert(framed.sd(2.11, 1.25, .25) > 0);
  assert(framed.sd(2, 1.5, .5) > 0);
  const plane = { kind: 'plane', origin: [0, 0, 0], u: [2, 0, 0], v: [1, 2, 0] };
  const surface = s.fill({ rings: [square, hole], surface: plane, offset: .04, depth: .2 }, [3]);
  assert(surface.sd(.75, .5, .12) < 0);
  assert(surface.sd(.75, .5, .01) > 0);
  assert(surface.sd(.75, .5, .25) > 0);
  assert(surface.sd(1.5, 1, .12) > 0);
  const narrow = s.stroke({ surface: plane, points: [[.2, .5], [.8, .5]], width: .2, depth: .1 }, [3]);
  assert(narrow.sd(1.5, 1.08, 0) < 0);
  assert(narrow.sd(1.5, 1.12, 0) > 0);
});

test('strokes and fill boundaries cross a closed cylinder seam', () => {
  const s = sculpt();
  const stroke = s.stroke({ surface: cylinder, points: [[.92, .4], [.08, .4]], width: .2, depth: .1 }, [3]);
  assert(stroke.sd(1.03, .8, 0) < 0);
  assert(stroke.sd(1.06, .8, 0) > 0);
  assert(stroke.sd(-1.03, .8, 0) > 0);
  assert(stroke.geometryBounds.min[0] > .7);
  const mark = s.fill({ surface: cylinder, depth: .12, rings: [
    [[.9, .2], [.1, .2], [.1, .8], [.9, .8]],
    [[.97, .35], [.03, .35], [.03, .65], [.97, .65]]
  ] }, [3]);
  assert(mark.sd(1.06, .5, 0) < 0);
  assert(mark.sd(1.06, 1, 0) > 0);
  assert(mark.sd(-1.06, .5, 0) > 0);
  let count = 0;
  mark.sample((x, y, z) => {
    assert(Math.abs(mark.sd(x, y, z)) < 1e-6);
    count++;
  });
  assert(count > 20);
});

test('drawing snapshots reopen, reject invalid edits and render undo and redo', () => {
  const scene = K.diorama.scene(spec), { document, realize } = scene.authoring();
  const image = world => ink.render(world, { w: 96, h: 64, px: 1, dither: 0 }).rgb;
  const initial = realize().world;
  assert(initial.count > 0);
  assert.deepEqual(initial.data, scene.build().data);
  document.update('brush', { parameters: { width: .58, pressure: [1, 1] } });
  const edited = realize().world;
  assert.notDeepEqual(image(edited), image(initial));
  assert(document.undo());
  assert.deepEqual(realize().world.data, initial.data);
  assert(document.redo());
  const saved = JSON.parse(document.serialize());
  assert.deepEqual(scene.build(7, { snapshot: saved }).data, edited.data);
  assert.deepEqual(scene.authoring(7, { snapshot: saved }).realize().world.data, edited.data);
  document.update('brush', { parameters: { pressure: [1] } });
  assert.match(realize().checks[0].message, /one value per point/);
  assert(document.undo());
  document.remove('brush');
  document.remove('shape');
  assert.equal(realize().world.count, 0);
  const id = document.create('stroke', { parameters: { points: [[0, 0, 0]] } });
  assert(document.get(id));
  assert(realize().world.count > 0);
  assert.throws(() => K.diorama.scene({ ...spec, id: 'other' }).build(7, { snapshot: saved }), /different scene/);
});

test('the CLI saves a drawing revision and builds it via the scene entry point', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-drawing-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const file = path.join(dir, 'drawing.json'), edits = path.join(dir, 'edit.json'), output = path.join(dir, 'revision.json');
  fs.writeFileSync(file, JSON.stringify(spec));
  const cli = (...args) => execFileSync(process.execPath, [path.resolve(__dirname, '../cli/ink-studio.js'), ...args],
    { cwd: dir, encoding: 'utf8' });
  const before = JSON.parse(cli('authoring', 'inspect', file));
  assert.deepEqual(before.parts.map(p => p.id), ['brush', 'shape']);
  fs.writeFileSync(edits, JSON.stringify({
    revision: before.revision,
    operations: [{ op: 'update', id: 'brush', patch: { parameters: { width: .6, taper: [.7, .8] } } }]
  }));
  const after = JSON.parse(cli('authoring', 'apply', file, edits, '--out', output));
  assert(after.valid && after.splatCount !== before.splatCount);
  const check = JSON.parse(cli('authoring', 'inspect', file, '--authoring', output));
  assert.equal(check.splatCount, after.splatCount);
  cli('render', file, '--authoring', output, '--out', path.join(dir, 'revision.png'));
  assert(fs.statSync(path.join(dir, 'revision.png')).size > 20);
  const glb = path.join(dir, 'revision.glb');
  cli('export-glb', file, '--authoring', output, '--res', '.04', '--texture-size', '0', '--out', glb);
  assert.equal(fs.readFileSync(glb).toString('ascii', 0, 4), 'glTF');
});

test('pointer input commits pen strokes and mouse fills and drops cancelled gestures', async () => {
  const { createDrawingInput } = await import('../webgl.mjs');
  class Target extends EventTarget {
    setPointerCapture(id) { this.captured = id; }
    hasPointerCapture(id) { return this.captured === id; }
    releasePointerCapture() { this.captured = undefined; }
  }
  const element = new Target(), commits = [], previews = [];
  const { document, realize } = K.diorama.scene({ id: 'input', solids: [] }).authoring();
  let kind = 'stroke';
  const input = createDrawingInput(element, {
    brush: () => ({ kind, depth: .1 }), project: event => event.point,
    preview: mark => previews.push(mark),
    commit: mark => {
      document.create(mark.kind, { parameters: mark });
      commits.push(mark);
    }
  });
  function send(type, point, fields = {}) {
    element.dispatchEvent(Object.assign(new Event(type, { cancelable: true }),
      { button: 0, pointerId: 5, pointerType: 'pen', pressure: .25, point, ...fields }));
  }
  send('pointerdown', [0, 0, 0]);
  assert(element.hasPointerCapture(5));
  send('pointermove', [2, 0, 0], { pressure: .9, getCoalescedEvents: () =>
    [{ pointerType: 'pen', pressure: .7, point: [1, 0, 0] }] });
  send('pointermove', [5, 0, 0], { pointerId: 6 });
  send('pointerup', [3, 0, 0], { pressure: 0 });
  assert.deepEqual(commits[0].points, [[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]]);
  assert.deepEqual(commits[0].pressure, [.25, .7, .9, .9]);
  assert.equal(previews.at(-1), null);
  assert(!element.hasPointerCapture(5));
  kind = 'fill';
  send('pointerdown', [0, 0], { pointerType: 'mouse' });
  send('pointermove', [1, 0], { pointerType: 'mouse' });
  send('pointerup', [1, 1], { pointerType: 'mouse' });
  assert.deepEqual(commits[1].rings, [[[0, 0], [1, 0], [1, 1]]]);
  send('pointerdown', [0, 0]);
  send('pointercancel', null);
  send('pointerup', [0, 1]);
  input.dispose();
  assert.equal(commits.length, 2);
  assert(realize().world.count > 0);
});

test('WebGL renders a different frame after editing the same stroke', { skip: !process.env.INK_TEST_CHROME }, t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-drawing-gl-')), page = path.join(dir, 'draw.html');
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  fs.writeFileSync(path.join(dir, 'bundle.js'), ink.bundle());
  fs.writeFileSync(page, `<!doctype html><canvas width="96" height="64"></canvas><pre id="result">PENDING</pre>
<script src="bundle.js"></script><script type="module">
import { createRenderer } from ${JSON.stringify(pathToFileURL(path.resolve(__dirname, '../webgl.mjs')).href)};
const result = document.querySelector('#result');
try {
  const canvas = document.querySelector('canvas'), renderer = createRenderer(canvas, { toolkit: { KIT, PixelLook } });
  const gl = canvas.getContext('webgl2');
  const { document: drawing, realize } = KIT.diorama.scene(${JSON.stringify(spec)}).authoring();
  function draw() {
    const rgba = new Uint8Array(96 * 64 * 4);
    renderer.render(realize().world, { width: 96, height: 64, dither: 0, damp: false });
    gl.readPixels(0, 0, 96, 64, gl.RGBA, gl.UNSIGNED_BYTE, rgba);
    if (gl.getError()) throw Error('WebGL draw failed');
    return rgba;
  }
  const first = draw();
  drawing.update('brush', { parameters: { width: .6, pressure: [1, 1] } });
  const updated = draw();
  const changed = first.reduce((n, v, i) => n + (i % 4 !== 3 && v !== updated[i]), 0);
  if (changed < 30) throw Error('Expected visible changes after editing the stroke');
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

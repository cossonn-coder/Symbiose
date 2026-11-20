const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { pathToFileURL } = require('node:url');
const ink = require('..');
const { KIT, makeBuilder, makeSculpt, TargetSelectors } = ink.load();

function sculpt(makeBuilder, makeSculpt, rules, fine = false) {
  const builder = makeBuilder(1, [0, 0x8a3344, 0x58c4c2, 0xeee2bb], { detailBudgets: rules });
  const shape = makeSculpt(builder);
  shape.fine = fine;
  const material = { r: [1, 2, 3], em: true, tex: (x, y) => Math.floor((x + y) * 38) % 2 === 0 ? 1 : 3 };
  shape.box([-1.2,0,0], [.55,.4,.32], material, { res: .28, objectId: 'hero' });
  shape.box([1.2,0,0], [.55,.4,.32], material, { res: .28, objectId: 'scenery', target: { tags: ['background'] } });
  shape.bake();
  return builder.finish({ cam: { target: [0,0,0], dist: 7, pitch: 0, yaw: 0 }, radius: 8, detail: 12 });
}

function summarize(world) {
  const index = TargetSelectors.index(world), counts = {};
  for (let i = 0; i < world.count; i++) {
    const entry = counts[index.row(i).object] ??= { splats: 0, tiles: 0 };
    entry.splats++;
    if (world.fine?.[i * 12 + 11]) entry.tiles++;
  }
  return counts;
}

test('spacing and fine tiles change only the selected solids', () => {
  const base = summarize(sculpt(makeBuilder, makeSculpt));
  const rules = [{ select: { object: 'hero' }, spacing: .6, fine: true },
    { select: { tag: 'background' }, spacing: 1.6 }];
  const world = sculpt(makeBuilder, makeSculpt, rules);
  const scoped = summarize(world);
  assert(scoped.hero.splats > base.hero.splats * 2);
  assert(scoped.hero.tiles > 0);
  assert(scoped.scenery.splats < base.scenery.splats / 2);
  assert.equal(scoped.scenery.tiles, 0);
  const view = { w: 96, h: 64, px: 1, dither: 0 };
  const withoutFine = { ...world, look: { detailBudgets: false } };
  assert.notDeepEqual(ink.render(world, view).rgb, ink.render(withoutFine, view).rgb);
  const off = summarize(sculpt(makeBuilder, makeSculpt, [{ select: { object: 'hero' }, fine: false }], true));
  assert.equal(off.hero.tiles, 0);
  assert(off.scenery.tiles > 0);
});

test('JSON scenes select entities and accept the first matching rule', () => {
  const spec = { id: 'detail-budget-test', solids: [
    { id: 'scenery', kind: 'ball', at: [1,0,0], r: .5, mat: 'stone', res: .25, tags: ['art'] },
    { id: 'hero', kind: 'ball', at: [-1,0,0], r: .5, mat: 'stone', res: .25, tags: ['art'] }
  ] };
  const base = summarize(KIT.diorama.build(spec));
  spec.finish = { look: { detailBudgets: [
    { select: { entity: 'hero' }, spacing: .5 },
    { select: { tag: 'art' }, spacing: 2 }
  ] } };
  const budgeted = summarize(KIT.diorama.build(spec));
  assert(budgeted.hero.splats > base.hero.splats * 3);
  assert(budgeted.scenery.splats < base.scenery.splats / 2);
  spec.finish.look.detailBudgets[0].spacing = 0;
  assert.throws(() => KIT.diorama.build(spec), /finish\.look\.detailBudgets[\s\S]*spacing/);
});

function dots(makeBuilder, rule, clean) {
  const detailBudgets = rule ? [{ select: { object: 'hero' }, ...rule }] : undefined;
  const builder = makeBuilder(1, [0,0xffffff,0xff7070], { detailBudgets });
  for (const [x, object] of [[-1, 'hero'], [1, 'other']]) {
    const start = builder.count();
    builder.disc(x, .03, 0, [0,0,1], .02, .015, builder.P[1], 3);
    builder.describeSplats(start, builder.count(), { object });
  }
  return builder.finish({ cam: { target: [0,0,0], dist: 7, pitch: 0, yaw: 0 }, radius: 8, detail: 12, look: { clean } });
}

function halves(pixels, stride, width = 96) {
  const counts = [0, 0];
  for (let i = 0; i < pixels.length / stride; i++)
    if (pixels[i * stride]) counts[Number(i % width >= width / 2)]++;
  return counts;
}

test('headless cleanup can enable, disable, or protect a visible subject independently', () => {
  for (const colored of [false, true]) {
    const frame = (rule, clean) => halves(ink.render(dots(makeBuilder, rule, clean),
      { w: 96, h: 64, px: 1, dither: 0, colored }).rgb, 3);
    const base = frame(undefined, false), enabled = frame({ cleanup: true }, false);
    assert(enabled[0] < base[0]);
    assert.equal(enabled[1], base[1]);
    for (const rule of [{ cleanup: false }, { protectSilhouette: true }]) {
      const protectedFrame = frame(rule, true);
      assert.equal(protectedFrame[0], base[0]);
      assert(protectedFrame[1] < base[1]);
    }
  }
});

function checkWebGL(createRenderer, dots, sculpt, halves, makeBuilder, makeSculpt, toolkit) {
  const canvas = document.querySelector('canvas');
  const renderer = createRenderer(canvas, { toolkit });
  const gl = canvas.getContext('webgl2'), pixels = new Uint8Array(96 * 64 * 4);
  const read = world => {
    renderer.render(world, { width: 96, height: 64, dither: 0, colored: false });
    gl.readPixels(0, 0, 96, 64, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    if (gl.getError()) throw new Error('Unexpected WebGL error');
    return pixels.slice();
  };
  const frame = (rule, clean) => halves(read(dots(makeBuilder, rule, clean)), 4);
  const base = frame(undefined, false), enabled = frame({ cleanup: true }, false);
  if (!(enabled[0] < base[0] && enabled[1] === base[1]))
    throw new Error('Cleanup leaked or did not run: ' + [base, enabled]);
  for (const rule of [{ cleanup: false }, { protectSilhouette: true }]) {
    const protectedFrame = frame(rule, true);
    if (!(protectedFrame[0] === base[0] && protectedFrame[1] < base[1]))
      throw new Error('Protection leaked or failed: ' + [base, protectedFrame]);
  }
  const world = sculpt(makeBuilder, makeSculpt, undefined, true);
  const fine = read(world);
  world.look = { detailBudgets: [{ select: { object: 'hero' }, fine: false }] };
  const scoped = read(world);
  if (!scoped.some((v, i) => v !== fine[i] && (i >> 2) % 96 < 48) ||
       scoped.some((v, i) => v !== fine[i] && (i >> 2) % 96 >= 48))
    throw new Error('Fine texture was not disabled only on the selected object');
  renderer.dispose();
}

test('WebGL scopes cleanup and fine tiles to the selected subject', { skip: !process.env.INK_TEST_CHROME }, () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-detail-'));
  const page = path.join(temp, 'detail.html');
  try {
    fs.writeFileSync(path.join(temp, 'bundle.js'), ink.bundle());
    fs.writeFileSync(page, `<!doctype html><canvas width="96" height="64"></canvas><pre id="result">PENDING</pre>
<script src="bundle.js"></script><script type="module">
import { createRenderer } from ${JSON.stringify(pathToFileURL(path.resolve(__dirname, '../webgl.mjs')).href)};
const result = document.querySelector('#result');
try {
  (${checkWebGL})(createRenderer, ${dots}, ${sculpt}, ${halves}, makeBuilder, makeSculpt, { KIT, PixelLook });
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

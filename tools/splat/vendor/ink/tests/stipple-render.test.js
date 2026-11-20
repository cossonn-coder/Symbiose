const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT, SurfaceLook } = require('..').load();
const { render, upscale } = require('../cli/render');
const example = require('../examples/stipple.json');

test('a light track clamps and interpolates directions on the unit sphere', () => {
  const at = SurfaceLook.prepareLightTrack([[0, 3, 0, 0], [2, -3, 0, 0], [4, 0, 2, 0]]);
  assert.deepEqual(at(-1), [1, 0, 0]);
  assert(Math.abs(at(1)[0]) < 1e-8);
  assert(Math.abs(Math.hypot(...at(1)) - 1) < 1e-8);
  assert.deepEqual(at(5), [0, 1, 0]);
});

test('a data scene reports invalid tone, pixel size and light keys together', () => {
  const invalid = structuredClone(example);
  invalid.finish.look.pixelSize = 1.5;
  invalid.finish.look.tone = { stops: [[0, '#000000'], [0, '#ffffff']] };
  invalid.light.surfaceDirection = [[0, 1, 0, 0], [0, 0, 1, 0]];
  const paths = KIT.diorama.check(invalid).filter(entry => entry.level === 'error').map(entry => entry.path);
  assert.deepEqual(paths, ['finish.look.pixelSize', 'finish.look.tone', 'light.surfaceDirection']);
});

test('the stipple scene renders animated lighting at a fixed pixel size with a fixed palette', () => {
  const spec = structuredClone(example);
  spec.finish.look.clean = true;
  const world = KIT.diorama.build(spec);
  const before = world.data.slice();
  const view = { w: 180, h: 180 };
  const first = render(world, { ...view, t: 0 });
  const middle = render(world, { ...view, t: 1.5 });
  const last = render(world, { ...view, t: 3 });
  assert.deepEqual([first.w, first.h, first.px], [90, 90, 2]);
  assert.deepEqual([upscale(first, first.px).w, upscale(first, first.px).h], [180, 180]);
  assert.deepEqual(first.rgb, last.rgb);
  assert.notDeepEqual(first.rgb, middle.rgb);
  assert.deepEqual(world.data, before);
  assert.equal(first.palette[0], 0);
  assert.deepEqual(first.rgb.slice(0, 3), Uint8Array.of(0, 0, 0));
  assert(first.use.slice(1).filter(count => count > 0).length >= 3);
  world.look.clean = false;
  assert.deepEqual(render(world, view).rgb, first.rgb);
  assert.equal(render(world, { ...view, raw: true, px: 3 }).palette, undefined);
  assert.deepEqual(
    render(world, { ...view, surface: false, t: 0 }).rgb,
    render(world, { ...view, surface: false, t: 1.5 }).rgb
  );
});

test('the renderer offers a distinct per-scene blue-noise pattern', () => {
  const spec = structuredClone(example);
  spec.finish.look.tone = { pattern: 'blue-noise', seed: 17 };
  const world = KIT.diorama.build(spec);
  const view = { w: 128, h: 96, t: 1 };
  const first = render(world, view);
  assert.deepEqual(first.rgb, render(world, view).rgb);
  assert.notDeepEqual(first.rgb, render(world, { ...view, tone: 'stipple' }).rgb);
  world.look.tone.seed = 18;
  assert.notDeepEqual(first.rgb, render(world, view).rgb);
});

const assert = require('node:assert/strict');
const test = require('node:test');
const studio = require('../index.js');
const { KIT, makeBuilder } = studio.load();
const { contributionLayers } = require('../cli/look-contributions.js');

const view = { w: 65, h: 65, px: 1, ortho: true };
const center = (32 * 65 + 32) * 3;
const tone = (name, offset) => ({
  name, steps: [{ type: 'channelMix', matrix: [[0, 0, 0], [0, 0, 0], [0, 0, 0]], offset }]
});

function glassScene({ patterned = false, stages, alpha = .4, mask } = {}) {
  const B = makeBuilder(18, [0, 0x302010, 0x00ee00, 0xb07010]);
  if (patterned) B.pixNext([3], 1, null, 0, 0, 1);
  B.disc(0, 0, 0, [0, 0, 1], .8, .025, B.P[1], 3);
  B.describeSplats(0, 1, { object: 'instrument' });
  B.disc(0, 0, .32, [0, 0, 1], .46, .02, B.P[2], alpha, { gl: true, nd: true });
  B.describeSplats(1, 2, { object: 'window' });
  const targets = [
    { select: { object: 'instrument' }, palette: ['#ff0000'] },
    { select: { object: 'window' }, palette: ['#0000ff'], ...(mask && { mask }) }
  ];
  return B.finish({
    cam: { target: [0, 0, 0], dist: 4, yaw: 0, pitch: 0 }, refract: 0, dither: 0,
    look: { coverageAware: !stages, pixel: patterned, renderStages: stages, paletteConstraints: { targets } }
  });
}

function pixel(frame) {
  return Array.from(frame.rgb.slice(center, center + 3));
}

test('the window keeps its own palette contribution below and above dominant coverage', () => {
  for (const alpha of [.25, .75]) {
    const world = glassScene({ alpha });
    const frame = studio.render(world, view);
    assert.deepEqual(pixel(frame), [Math.round(.99 * (1 - alpha) * 255), 0, Math.round(alpha * 255)]);
    for (const splatOrder of ['center', 'surface'])
      assert.deepEqual(studio.render(world, { ...view, splatOrder }).rgb, frame.rgb);
    assert.notDeepEqual(pixel(studio.render(world, { ...view, coverageAware: false })), pixel(frame));
  }
});

test('the glass mask blends only pane color and leaves the rear look and opacity intact', () => {
  const mask = { type: 'axis', axis: 'y', space: 'world', range: [-1, 1], interpolation: 'linear' };
  const world = glassScene({ mask });
  const frame = studio.render(world, { ...view, transparent: true });
  const dry = studio.render(world, { ...view, transparent: true, lookMasks: false });
  const [r, g, b] = pixel(frame);
  assert.equal(r, pixel(dry)[0]);
  assert(g > 40 && g < 52);
  assert(b > 48 && b < 54);
  assert.deepEqual(frame.alpha, dry.alpha);
  assert.equal(frame.alpha[32 * 65 + 32], 253);
  const probe = KIT.world.query.fromScene(world).probe('look/output', { object: 'window' },
    { at: [0, 0, .32], rgb: [0, 238 / 255, 0] }).value.targets[0];
  assert.deepEqual(probe.rgb, [0, 119 / 255, .5]);
});

test('per-pixel material redraw changes only the surviving base contribution beneath glass', () => {
  const identity = { name: 'Identity', steps: [] };
  const window = { stage: 'lit', select: { object: 'window' }, stack: tone('Glass', [0, 0, 1]) };
  const unchanged = { stage: 'lit', stack: identity };
  const unpatterned = studio.render(glassScene({ stages: [window] }), view);
  assert.deepEqual(pixel(unpatterned), [29, 19, 10 + 102]);
  const world = glassScene({ patterned: true, stages: [unchanged, window] });
  const patterned = studio.render(world, view);
  assert.deepEqual(pixel(patterned), [105, 67, 112]);
  const scoped = studio.render(glassScene({ patterned: true }), view);
  assert.deepEqual(pixel(scoped), [151, 0, 102]);
});

test('refraction moves the transmitted sample and retains the front contribution and alpha', () => {
  const rgb = Float32Array.of(1, 0, 0, .5, 0, 0, 0, 1, 0);
  const alpha = Float32Array.of(1, .5, 1);
  const layers = contributionLayers(rgb, alpha, 3, 1, false, 2);
  layers.before(1, 0, 0, 1, .5, false, true, .3);
  rgb.set([.25, 0, .5], 3);
  alpha[1] = .75;
  layers.refract([0, .25, .5], [.6, .6, .6]);
  assert.deepEqual(Array.from(rgb.slice(3, 6)), [0, .5, .5]);
  assert.equal(alpha[1], 1);
});

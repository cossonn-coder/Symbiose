const assert = require('node:assert/strict');
const { test } = require('node:test');
const { execFileSync } = require('node:child_process');
const { mkdtempSync, readFileSync, rmSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { join, resolve } = require('node:path');
const { KIT: K, ...kit } = require('..').load();
const A = K.anim, close = (a, b) => assert(Math.abs(a - b) < 1e-7, a + ' differs from ' + b);

const clip = (tracks, dur = 1) => A.clip({ dur, tracks });
const lane = (id, extras = {}) => ({ id, clip: id, parts: ['arm'], ...extras });
const sample = (motion, time) => motion.sample(time, {}, { sourceTime: true });

test('native override layers blend incoming channels in order while additive layers keep their semantics', () => {
  const lift = clip({ 'arm.pos': [[0, [0, 2, 0]]], 'leg.pos': [[0, [50, 0, 0]]] });
  const raise = clip({ 'arm.pos': [[0, [0, 6, 0]]] });
  const layers = A.motionLayers.create({ duration: 1, sources: { lift, raise },
    layers: [lane('lift'), lane('raise', { weight: 0.5 })] });
  const main = A.clip({ dur: 1, tracks: { 'arm.pos': [[0, [0, 1, 0]]], 'arm.scale': [[0, 1.2]], 'leg.pos': [[0, [0, 0, 1]]] },
    tools: { layers: [...layers.native, { values: { arm: { pos: [0, 0.25, 0] } } }] } });
  assert.deepEqual(sample(main, 0.6), { arm: { pos: [0, 4.25, 0], scale: 1.2 }, leg: { pos: [0, 0, 1] } });
  assert.deepEqual(sample(lift, 0.6).arm.pos, [0, 2, 0]);
  assert.equal(layers.arrange(['raise', 'lift']).apply({}, 0.6).arm.pos[1], 2);
  assert.equal(layers.apply({}, 0.6).arm.pos[1], 4);
  const legs = layers.edit('lift', { parts: ['leg'] }).edit('raise', { enabled: false });
  assert.deepEqual(legs.apply({}, 0.6), { leg: { pos: [50, 0, 0] } });
});

test('fractional rotation takes the shortest arc and opaque overrides replace both orientation channels', () => {
  const from = { arm: { turn: K.deform.euler([0, 170, 0]), scale: 2 } };
  const lift = clip({ 'arm.rot': [[0, [0, -170, 0]]], 'arm.scale': [[0, [1, 3, 1]]], 'arm.show': [[0, 0]] });
  const layers = A.motionLayers.create({ duration: 1, sources: { lift }, layers: [lane('lift', { weight: 0.5 })] });
  const blended = layers.apply(structuredClone(from), 0.5).arm;
  K.M.app(K.deform.euler(blended.rot), [0, 0, 1]).forEach((value, i) => close(value, [0, 0, -1][i]));
  assert.equal(blended.turn, undefined);
  assert.deepEqual(blended.scale, [1.5, 2.5, 1.5]);
  assert.equal(blended.show, 0);
  const full = layers.edit('lift', { weight: 1 }).apply(structuredClone(from), 0.5).arm;
  assert.deepEqual(full.rot, [0, -170, 0]);
  assert.equal(full.turn, undefined);
  const zero = layers.edit('lift', { weight: 0 }).apply(structuredClone(from), 0.5);
  assert.deepEqual(zero, from);
});

test('layer weights use shot time while trims and rate control source time', () => {
  const lift = clip({ 'arm.pos': [[0, [0, 0, 0], 'linear'], [2, [0, 2, 0]]] }, 2);
  const layers = A.motionLayers.create({ duration: 3, sources: { lift }, parts: ['arm'],
    layers: [lane('lift', { start: 0.5, end: 2.5, in: 0.2, out: 0.8,
      weight: [[0.5, 0, 'bezier', [0.25, 0, 0.75, 1]], [2.5, 1]] })] });
  let entry = layers.at(1.5)[0];
  assert(Math.abs(entry.weight - 0.5) < 1e-6);
  close(entry.sourceTime, 0.5);
  close(layers.at(2.5)[0].sourceTime, 0.8);
  assert.deepEqual(layers.at(0.49)[0], { id: 'lift', order: 0, weight: 0, sourceTime: null });
  assert.deepEqual(layers.apply({}, 2.6), {});
  const loop = layers.edit('lift', { speed: 0.6, loop: true });
  close(loop.at(2)[0].sourceTime, 0.5);
  assert.throws(() => layers.edit('lift', { parts: ['missing'] }), /part mask/);
  assert.throws(() => layers.edit('lift', { weight: [[0, 0], [2.5, 1]] }), /weight key/);
  assert.equal(layers.layers[0].parts[0], 'arm');
});

test('the composed timeline preserves both soles and root travel while lifting the lantern', () => {
  const scene = require('../examples/motion-layers')({ KIT: K, ...kit });
  const blend = scene.build(scene.seed), plain = scene.build(scene.seed, { controls: { baseOnly: true } });
  const alternate = scene.build(scene.seed, { controls: { layerOrder: ['glance', 'lantern-lift'] } });
  const time = 1.13, a = blend.animationTimeline, b = plain.animationTimeline;
  const frame = a.frame(time);
  b.frame(time);
  assert.deepEqual(frame.motionLayers.map(layer => [layer.id, layer.weight]), [['lantern-lift', 1], ['glance', 0.72]]);
  const point = (world, part) => {
    const { puppet } = world.retargetRig;
    return puppet.point(part, puppet.parts[part].pivot);
  };
  for (const part of ['body', 'boot-l', 'boot-r']) assert.deepEqual(point(blend, part), point(plain, part));
  assert(point(blend, 'lantern')[1] > point(plain, 'lantern')[1] + 0.8);
  assert.notDeepEqual(a.sample(time).jacket.rot, alternate.animationTimeline.sample(time).jacket.rot);
  assert.deepEqual(a.sample(time, {}, { stage: 'block' }), b.sample(time, {}, { stage: 'block' }));
  assert(a.frame(time, { stage: 'block' }).motionLayers.every(layer => layer.weight === 0));
  assert.deepEqual(a.sample(1.9), b.sample(1.9));
});

test('the existing timeline CLI previews the mix and auditions mask changes from JSON', () => {
  const directory = mkdtempSync(join(tmpdir(), 'ink-motion-layers-'));
  const cli = resolve(__dirname, '../cli/ink-studio.js'), scene = resolve(__dirname, '../examples/motion-layers.js');
  const run = (dir, ...args) => JSON.parse(execFileSync(process.execPath, [cli, 'animation-timeline', scene,
    '--at', '1.13', '--preview', join(directory, dir), '--direction', '2', ...args], { encoding: 'utf8' }));
  try {
    const withLayers = run('mix');
    const edited = run('edit', '--params', '{"layerEdits":{"lantern-lift":{"parts":["jacket"],"weight":0.5}}}');
    assert.deepEqual(edited.lanes.motionLayers[0].parts, ['jacket']);
    assert.equal(edited.frame.motionLayers[0].weight, 0.5);
    assert.equal(withLayers.preview.frames[0].sourceTime, edited.preview.frames[0].sourceTime);
    assert.equal(withLayers.preview.timeline.direction, 2);
    assert(!readFileSync(join(directory, 'mix/color.png')).equals(readFileSync(join(directory, 'edit/color.png'))));
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

const assert = require('node:assert/strict');
const { test } = require('node:test');
const { mkdtempSync, readFileSync, rmSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { join, resolve } = require('node:path');
const { execFileSync } = require('node:child_process');
const studio = require('..');
const kit = studio.load(), { KIT: K } = kit;
const scene = require('../examples/animation-timeline')(kit);

test('one shot clock maps held landmarks, retimed keys, and the six authoring features', () => {
  const timeline = scene.build(scene.seed).animationTimeline;
  const lanes = timeline.report().lanes;
  const breakdown = lanes.poses.find(item => item.kind === 'breakdown');
  assert.equal(breakdown.sourceTime, 0.96);
  assert.notEqual(breakdown.time, breakdown.sourceTime);
  assert(lanes.keys.some(key => key.step === 'pickup' && key.time === breakdown.time));
  assert.equal(lanes.cues[0].time, 3.12);
  assert.equal(lanes.handoffs[0].time, 2.4);
  assert.equal(lanes.contacts[0].id, 'left-plant');
  assert.equal(lanes.transfers[0].part, 'lantern');
  assert.equal(lanes.fx.length, 2);
  assert.equal(lanes.cloth[0].start, 2.22);
  assert(lanes.findings.some(item => item.kind === 'loop-pop'));

  const t = 0.9, held = timeline.sample(t);
  timeline.set({ time: t, part: 'rightForearm', loop: { start: 0.5, end: 1.7 }, direction: 3 });
  const spline = timeline.set({ stage: 'spline' });
  assert.notDeepEqual(timeline.sample().body.pos, held.body.pos);
  assert.deepEqual(timeline.set({ stage: 'polish' }), { ...spline, stage: 'polish' });
  assert.equal(timeline.timeAt(0), 0.5);
  assert(Math.abs(timeline.timeAt(1.4) - 0.7) < 1e-8);
  assert.throws(() => timeline.set({ time: 9, stage: 'block' }), /Playhead/);
  assert.equal(timeline.snapshot().stage, 'polish');
});

test('headless frames evaluate the same prop switch across stages, with FX and cloth during Polish', () => {
  const world = scene.build(scene.seed), timeline = world.animationTimeline;
  for (const stage of K.anim.timeline.stages) {
    const { time, reachStart } = timeline.report().lanes.transfers[0];
    assert.equal(timeline.frame(reachStart - 0.005, { stage }).contacts.reaches.length, 0);
    assert.equal(timeline.frame(reachStart + 0.005, { stage }).contacts.reaches.length, 1);
    assert.equal(timeline.frame(time - 0.001, { stage }).contacts.attachment.owner, 'plinth');
    const switchFrame = timeline.frame(time, { stage });
    assert.equal(switchFrame.contacts.attachment.owner, 'hand');
    assert(switchFrame.contacts.contacts[0].miss < 0.01);
  }
  assert.equal(timeline.frame(1.65, { stage: 'spline' }).effects.emitted, 0);
  assert(timeline.frame(1.65, { stage: 'polish' }).effects.emitted > 0);
  const cloth = timeline.frame(2.6, { stage: 'polish' }).cloth[0];
  assert(cloth.baked && Math.abs(cloth.time - 0.38) < 1e-8);
  assert.equal(timeline.frame(2.6, { stage: 'polish', before: true }).cloth[0].baked, false);
  assert.deepEqual(timeline.frame(2.6, { stage: 'polish' }).cloth[0], cloth);
});

test('seeking a retimed landmark displays its exact held pose after earlier clips', () => {
  const shelf = K.anim.poseShelf.create();
  shelf.save('start', { body: { pos: [0, 0, 0] } });
  shelf.save('hit', { body: { pos: [1, 0, 0] } });
  const block = K.anim.poseBlocking.create(shelf, { duration: 1,
    keys: [{ pose: 'start', time: 0 }, { pose: 'hit', time: 0.03 }] });
  const sequence = K.anim.sequence.create({ clips: { block }, steps: [
    { id: 'first', clip: 'block', duration: 2.3 }, { id: 'second', clip: 'block', duration: 1.333, ease: 'in-sine' }
  ] });
  const { time } = sequence.markers.find(marker => marker.id === 'hit' && marker.step === 'second');
  assert.equal(sequence.sample(time - 0.00001, {}, { held: true }).body.pos[0], 0);
  assert.equal(sequence.sample(time, {}, { held: true }).body.pos[0], 1);
});

test('focus preserves restorable context and renders both exact seam poses at export size', () => {
  const world = scene.build(scene.seed), timeline = world.animationTimeline;
  const context = timeline.set({ stage: 'spline', time: 1.6, part: 'head', loop: { start: 1, end: 2 }, direction: 3 });
  const focused = timeline.focus('loop-pop');
  assert.equal(focused.time, timeline.duration);
  assert.equal(focused.part, timeline.report().lanes.findings.find(item => item.id === 'loop-pop').part);
  assert.equal(focused.loop.wraps, true);
  timeline.set({ stage: 'polish' });
  const live = timeline.snapshot();
  const atlas = studio.previewTimeline(world, { frames: 6 });
  const times = atlas.metadata.frames.map(frame => frame.sourceTime);
  const seam = times.indexOf(timeline.duration);
  assert(seam >= 0 && times[seam + 1] === 0);
  assert(atlas.metadata.frames.every(frame => frame.silhouette.pixels > 0));
  assert.equal(atlas.metadata.tileWidth, timeline.sprite.width);
  assert.equal(atlas.metadata.tileHeight, timeline.sprite.height);
  assert.equal(atlas.metadata.frames[0].yaw, timeline.sprite.yaw + 3 * Math.PI / 4);
  assert.deepEqual(timeline.snapshot(), live);

  const one = studio.previewTimeline(world, { frames: 1 });
  const raw = studio.spriteAtlas({ ...world }, { width: timeline.sprite.width, height: timeline.sprite.height, directions: 1,
    times: [timeline.duration], yaw: one.metadata.frames[0].yaw,
    pose(target, at) {
      timeline.frame(at);
      target.data = K.bones.posed(world);
    }
  });
  assert.deepEqual(one.images.color, raw.images.color);
  assert.deepEqual(timeline.restore(JSON.parse(JSON.stringify(live))), live);
  assert.deepEqual(timeline.clearFocus(), { ...context, stage: 'polish' });
});

test('accepted repair changes Polish pose and source comparison and mute restore it', () => {
  const timeline = scene.build(scene.seed).animationTimeline, t = timeline.duration;
  const motion = timeline.motionReview();
  const pose = timeline.sample(t, {}, { stage: 'polish' });
  assert(motion.accept('loop-pop'));
  const fixed = timeline.sample(t, {}, { stage: 'polish' });
  assert.notDeepEqual(fixed.body.pos, pose.body.pos);
  assert.deepEqual(fixed, motion.sample(t, {}, { sourceTime: true }));
  assert.deepEqual(timeline.sample(t, {}, { stage: 'polish', before: true }), pose);
  assert.deepEqual(timeline.sample(t, {}, { stage: 'spline' }), pose);
  assert(motion.setEnabled('loop-pop', false));
  assert.deepEqual(timeline.sample(t, {}, { stage: 'polish' }), pose);
});

test('CLI preserves a shot context and correction across separate invocations', () => {
  const dir = mkdtempSync(join(tmpdir(), 'ink-timeline-')), state = join(dir, 'context.json');
  const cli = resolve(__dirname, '../cli/ink-studio.js'), shot = resolve(__dirname, '../examples/animation-timeline.js');
  const run = (...args) => JSON.parse(execFileSync(process.execPath,
    [cli, 'animation-timeline', shot, '--state', state, ...args], { encoding: 'utf8' }));
  try {
    const block = run('--at', '1.4', '--part', 'head', '--loop', '1,2', '--direction', '2');
    const spline = run('--stage', 'spline');
    assert.deepEqual(spline.state, { ...block.state, stage: 'spline' });
    const preview = join(dir, 'seam');
    const polish = run('--stage', 'polish', '--finding', 'loop-pop', '--fix', 'accept',
      '--preview', preview, '--frames', '4', '--w', '48', '--h', '40');
    assert.equal(polish.lanes.corrections[0].enabled, true);
    const atlas = JSON.parse(readFileSync(join(preview, 'atlas.json'), 'utf8'));
    assert.equal(atlas.tileWidth, 48);
    assert.equal(atlas.tileHeight, 40);
    assert.deepEqual(atlas.frames.slice(1, 3).map(frame => frame.sourceTime), [4, 0]);
    assert.equal(atlas.timeline.direction, 2);
    const muted = run('--fix', 'mute');
    assert.equal(muted.lanes.corrections[0].enabled, false);
    const restored = run('--finding', 'off');
    assert.deepEqual(restored.state, { ...block.state, stage: 'polish' });
    assert.equal(restored.lanes.corrections[0].enabled, false);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

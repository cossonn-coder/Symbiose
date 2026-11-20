const { test } = require('node:test');
const assert = require('node:assert/strict');
const entry = import('../webgl.mjs');

test('the browser entry exposes all 49 usable defaults in their five groups', async () => {
  const { createTransition, transitionPresets, transitionShaders } = await entry;
  const ids = new Set(transitionPresets.map(({ id }) => id));
  assert.equal(ids.size, 49);
  const groups = {};
  const seen = new Set();
  for (const { id, group, duration } of transitionPresets) {
    groups[group] = (groups[group] ?? 0) + 1;
    const plan = createTransition(id);
    assert.equal(plan.duration, duration);
    const start = plan.sample(-1), end = plan.sample(duration + 1);
    assert.equal(start.progress, 0);
    assert.equal(end.progress, 1);
    assert.equal(end.time, duration);
    for (let i = 0; i <= 100; i++) {
      const frame = plan.sample(duration * i / 100);
      assert(frame.value >= 0 && frame.value <= 1);
      seen.add(frame.shader);
      assert(frame.uniforms.u_color.length === 4);
    }
  }
  assert.deepEqual(Object.values(groups), [8, 9, 12, 12, 8]);
  assert.deepEqual([...seen].sort(), [...transitionShaders].sort());
});

test('built-in presets expose independent timing, anchors, colors, and bounded shader inputs', async () => {
  const { createTransition } = await entry;
  const iris = createTransition('diamond-iris', {
    duration: 4, timing: [1, 1, 2], anchor: [0.1, 0.2], target: [0.8, 0.25],
    color: [0.4, 0.3, 0.2, 1], easing: 'linear', uniforms: ({ phase }) => ({ u_softness: phase / 2 })
  });
  const closing = iris.sample(0.5), hold = iris.sample(1), opening = iris.sample(3);
  assert.deepEqual(closing.uniforms.u_anchor, [0.1, 0.8]);
  assert.equal(closing.value, 0.5);
  assert.equal(hold.from, 'cover');
  assert.deepEqual(opening.uniforms.u_anchor, [0.8, 0.75]);
  assert.deepEqual(opening.uniforms.u_color, [0.4, 0.3, 0.2, 1]);
  assert.equal(opening.uniforms.u_softness, 0.25);
  assert.throws(() => createTransition('not-a-preset'), /Unknown/);
  assert.throws(() => createTransition('diamond-iris', { timing: [1, 1] }), /one positive span/);
  assert.throws(() => createTransition('checkerboard-swap', { cellSize: 0 }), /cellSize/);
  assert.throws(() => createTransition('destination-iris', { target: [0, Infinity] }), /anchor/);
});

test('blink and fragment presets hold darkness at their authored beats', async () => {
  const { createTransition } = await entry;
  const select = (id, positions) => {
    const plan = createTransition(id);
    return positions.map(t => {
      const { from, to, shader } = plan.sample(t * plan.duration);
      return [from, to, shader];
    });
  };
  assert.deepEqual(select('sleepy-double-blink', [0, 0.18, 0.4, 0.55]), [
    ['cover', 'cover', 'mix'], ['cover', 'to', 'eyelid'], ['cover', 'cover', 'mix'], ['cover', 'to', 'eyelid']
  ]);
  assert.deepEqual(select('black-between-fragments', [0.08, 0.19, 0.31, 0.45, 0.56, 0.69, 0.9]), [
    ['from', 'from', 'mix'], ['cover', 'cover', 'mix'], ['fragment1', 'fragment1', 'mix'],
    ['cover', 'cover', 'mix'], ['fragment2', 'fragment2', 'mix'], ['cover', 'cover', 'mix'], ['to', 'to', 'mix']
  ]);
});

test('playback emits chronological cues over black, and seeking remains silent', async () => {
  const { createTransition, createTransitionPlayback, defineTransition } = await entry;
  const wake = createTransition('wake-in-darkness', { duration: 2, cue: 'alarm', cueDetail: { volume: 0.25 } });
  const heard = [];
  const wakeUp = createTransitionPlayback(wake, { onCue: cue => heard.push([cue.name, cue.detail]) });
  assert.equal(wakeUp.update(0).from, 'cover');
  assert.equal(wakeUp.update(1).to, 'cover');
  assert.deepEqual(heard, [['alarm', { volume: 0.25 }]]);
  wakeUp.seek(0);
  wakeUp.update(1);
  assert.equal(heard.length, 1);
  wakeUp.reset();
  wakeUp.update(0.5);
  assert.equal(heard.length, 2);

  const flash = createTransition('freeze-flash-swap', { duration: 2, timing: [2, 1, 1] });
  assert.deepEqual(flash.cues.map(cue => [cue.name, cue.time]), [['freeze', 0], ['flash', 1], ['swap', 1.5]]);
  const custom = createTransitionPlayback(defineTransition({
    duration: 4, stages: [{}], cues: [{ at: 0.9, name: 'last' }, { at: 0.1, name: 'first' }]
  }), { onCue: cue => heard.push(cue.name) });
  custom.update(1);
  custom.update(4);
  assert.deepEqual(heard.slice(-2), ['first', 'last']);
});

test('a user-defined plan forwards custom shader names, samplers, and animated uniforms', async () => {
  const { defineTransition } = await entry;
  const plan = defineTransition({
    duration: 2, stages: [
      { span: 1, shader: 'static', from: 'ad', to: 'cover', start: 0.75, end: 0.25,
        easing: t => t * t, uniforms: ({ time }) => ({ u_noise: time }), samplers: { u_art: 'texture' } },
      { span: 1, to: 'scene' }
    ]
  });
  assert.deepEqual(plan.sample(0.5), {
    shader: 'static', from: 'ad', to: 'cover', mask: 'mask', samplers: { u_art: 'texture' },
    time: 0.5, value: 0.625, progress: 0.25, phase: 0.5, uniforms: { u_noise: 0.5 }
  });
  assert.equal(plan.sample(1).to, 'scene');
  assert.throws(() => plan.sample(NaN), /finite/);
  assert.throws(() => defineTransition({ stages: [{ easing: 'missing' }] }), /easing/);
});

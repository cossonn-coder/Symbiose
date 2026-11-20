const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const lib = require('..').load();
const { KIT: K } = lib;
const scene = require('../examples/motion-fx')(lib);

test('keys, layer intensity, masks, and enabled state can be edited independently', () => {
  const B = lib.makeBuilder(2);
  const fx = K.anim.motionFx.create(B, { duration: 2, capacity: 4, effects: [
    { id: 'squash', kind: 'stretch', parts: ['body'], keys: [[0.2, 0, 'linear'], [1, 1]] },
    { id: 'trail', kind: 'trail', parts: ['cape'], keys: [[1.25, 1], [1.8, 0]] }
  ] });
  const before = fx.effects();
  assert.deepEqual(fx.at(0.6).map(layer => Math.round(layer.amount * 100)), [50, 0]);
  assert.equal(fx.at(1.15)[0].amount, 0);
  fx.edit('squash', { intensity: 0.4, parts: ['head'] });
  assert.ok(Math.abs(fx.at(0.6)[0].amount - 0.2) < 1e-9);
  assert.deepEqual(fx.at(0.6)[0].parts, ['head']);
  assert.deepEqual(fx.effects()[1], before[1]);
  assert.deepEqual(before[0].parts, ['body']);
  fx.edit('squash', { enabled: false });
  assert.equal(fx.at(1)[0].amount, 0);
  assert.throws(() => fx.edit('trail', { keys: [[1.25, 0], [1.25, 1]] }), /unique/);
  assert.equal(fx.at(1.25)[1].amount, 1);
});

test('visual deform layers leave child transforms and unmasked splats unchanged', () => {
  const B = lib.makeBuilder(2);
  B.iso(0, 1, 0, 0.18, B.P[1], 1);
  B.iso(0, 2, 0, 0.15, B.P[1], 1);
  const fx = K.anim.motionFx.create(B, { duration: 2, capacity: 4, effects: [
    { id: 'body-squash', kind: 'stretch', parts: ['body'], axis: [0, 1, 0], keys: [[0, 1], [1, 1]] }
  ] });
  const world = B.finish(), source = (time, actor) => { actor.pose.body = { pos: [time, 0, 0] }; };
  let before = false;
  const puppet = K.puppet(world, { parts: {
    body: { ids: [0], pivot: [0, 1, 0] },
    head: { ids: [1], pivot: [0, 2, 0], parent: 'body' }
  }, pose(time, dt, actor) { source(time, actor); fx.apply(time, { before }); } });
  fx.bind(world, puppet, source);
  world.anim.update(0, 0.6);
  const active = Array.from(K.bones.posed(world));
  before = true;
  world.anim.update(0, 0.6);
  const rest = Array.from(K.bones.posed(world));
  assert.ok(active[8] > rest[8]);
  assert.deepEqual(active.slice(16, 32), rest.slice(16, 32));
  assert.deepEqual(Array.from(puppet.parts.head.visual), []);
  assert.equal(fx.at(0.6)[0].amount, 1);
  assert.throws(() => fx.edit('body-squash', { parts: ['missing'] }), /Unknown Motion FX part/);
});

test('overlapping geometry layers are deterministic across seeks and the sweep writes depth', () => {
  const world = scene.build(scene.seed), fx = world.motionFx, run = world.motionFxDemo.update;
  const off = run(0.6);
  assert.equal(off.emitted, 0);
  const first = run(1.42);
  const trail = first.layers.find(layer => layer.kind === 'trail'), sweep = first.layers.find(layer => layer.kind === 'sweep');
  assert.deepEqual(trail.parts, ['cape']);
  assert.deepEqual(sweep.parts, ['lantern']);
  assert.ok(trail.splats > 0 && sweep.splats > 0);
  assert.ok(first.layers.every(layer => layer.budgetSkipped === 0));
  const rows = () => Array.from(world.data.subarray(fx.first * 16, (fx.first + first.emitted) * 16));
  const prior = rows();
  assert.ok(prior[(trail.splats * 16) + 3] >= 1);
  assert.equal(prior[(trail.splats * 16) + 11] & 16, 0);
  run(1.66);
  run(0.8);
  assert.deepEqual(run(1.42), first);
  assert.deepEqual(rows(), prior);
  assert.equal(run(1.42, { source: true }).emitted, 0);
  const cleared = rows();
  for (let i = 3; i < cleared.length; i += 16) assert.equal(cleared[i], 0);
  assert.deepEqual(run(1.42), first);
  assert.equal(run(1.93).emitted, 0);
});

test('a sweep that exceeds the frame budget leaves existing draws intact', () => {
  const B = lib.makeBuilder(2);
  let result;
  const system = K.frameSplats(B, 2, draw => {
    draw.point([0, 1, 0]);
    result = draw.sweep([
      { base: [0, 0, 0], tip: [0, 1, 0] },
      { base: [1, 0, 0], tip: [1, 1, 0] }
    ]);
    assert.equal(draw.count, 1);
  });
  const world = B.finish();
  K.stage(world).add(system);
  world.anim.update(0, 0);
  assert.equal(result, false);
  assert.equal(world.data[3], 2);
  assert.equal(world.data[19], 0);
});

test('headless Motion FX reports a sampled masked sweep alongside the trail', () => {
  const output = execFileSync(process.execPath, ['cli/ink-studio.js', 'motion-fx',
    'examples/motion-fx.js', '--at', '1.42'], { cwd: path.join(__dirname, '..'), encoding: 'utf8' });
  const report = JSON.parse(output);
  assert.equal(report.effects.length, 4);
  assert.ok(report.sample.layers.find(layer => layer.kind === 'sweep').splats > 0);
  assert.ok(report.sample.layers.find(layer => layer.kind === 'trail').splats > 0);
});

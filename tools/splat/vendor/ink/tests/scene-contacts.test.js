const { test } = require('node:test');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const path = require('node:path');
const kit = require('..').load();
const { KIT: K } = kit;
const scene = require('../examples/scene-contacts')(kit);
const near = (a, b, tolerance = 1e-7) => K.V.dist(a, b) < tolerance;

test('captured mesh points use the ray-facing normal and missed surfaces stay inert', () => {
  const index = K.procedural.contacts.index({ positions: [0,0,0, 1,0,0, 0,0,1],
    groups: [{ start: 0, count: 3, owner: 'landing', surface: 'top' }] });
  const hit = K.anim.contacts.project(index, { origin: [0.2, 1, 0.2], distance: 2 });
  assert(hit.hit);
  assert(near(hit.point, [0.2, 0, 0.2]));
  assert(near(hit.normal, [0, 1, 0]));
  assert.equal(hit.owner, 'landing');
  const missed = K.anim.contacts.project(index, { origin: [1.5, 1, 1.5], distance: 2 });
  assert.equal(missed.hit, false);

  const B = kit.makeBuilder(1);
  B.iso(0, 1, 0, 0.2, B.P[1], 1);
  const puppet = K.puppet(B.finish(), { parts: { foot: { ids: [0], pivot: [0, 1, 0] } } });
  const anchor = { id: 'seat', part: 'foot', point: [0, 1, 0], align: true, start: 0, end: 1 };
  const create = target => K.anim.contacts.create({ duration: 1, puppet, sample: () => ({}),
    contacts: [{ ...anchor, target }] });
  const pose = create(missed).pose(0.5).contacts[0];
  assert.equal(pose.status, 'no-surface');
  assert.equal(pose.target, null);
  assert.deepEqual(pose.position, [0, 1, 0]);
  const aligned = create(hit).pose(0.5).contacts[0];
  assert.equal(aligned.status, 'reached');
  assert(near(aligned.position, hit.point));
});

test('the same sole and palm seat on their captured faces through source motion and stage changes', () => {
  const t = scene.build(scene.seed).animationTimeline;
  for (const stage of ['block', 'spline', 'polish']) for (const time of [1.30, 0.96, 1.18]) {
    const [sole, palm] = t.frame(time, { stage }).contacts.contacts;
    assert.equal(sole.surface.surface, 'sloped-step');
    assert.equal(palm.surface.surface, 'rail');
    assert(sole.normal[2] > 0.3);
    assert(near(palm.normal, [0,0,-1]));
    for (const contact of [sole, palm]) {
      assert.equal(contact.status, 'reached');
      assert(near(contact.position, contact.target));
      assert(contact.normalMiss < 1e-4);
    }
  }
  const start = t.frame(0.25).contacts.contacts[0];
  assert(start.strength > 0 && start.strength < 1);
  assert(start.miss > 0.05);
  assert(start.goalMiss < 1e-8);
  assert.equal(start.status, 'reached');
});

test('cooperative reach reduces the gap within each joint budget and preserves the authored switch pose', () => {
  const t = scene.build(scene.seed).animationTimeline;
  const unassisted = scene.build(scene.seed, { controls: { assist: false } }).animationTimeline;
  const beat = t.report().lanes.transfers[0], time = beat.time;
  const assistedFrame = t.frame(time).contacts;
  const plainFrame = unassisted.frame(time).contacts;
  const assisted = assistedFrame.reaches[0], raw = plainFrame.reaches[0];
  assert.equal(assisted.status, 'out-of-range');
  assert.equal(beat.reachStatus, 'out-of-range');
  assert(assisted.miss > 0.1 && assisted.miss < raw.miss - 0.15);
  assert(Math.abs(beat.reachMiss - assisted.miss) < 1e-8);
  assert.deepEqual(assisted.assist.map(support => support.part), ['chest', 'rightShoulder']);
  assert(assisted.assist[0].degrees <= 13 + 1e-8 && assisted.assist[1].degrees <= 23 + 1e-8);
  assert.deepEqual(assistedFrame.contacts[0].position, plainFrame.contacts[0].position);
  const before = t.frame(time - 1e-8).contacts.attachment;
  assert.equal(before.owner, 'pedestal');
  assert.equal(assistedFrame.attachment.owner, 'grip');
  assert(near(before.position, assistedFrame.attachment.position));
  assert(before.rotation.every((value, i) => Math.abs(value - assistedFrame.attachment.rotation[i]) < 1e-7));
  t.frame(3.1);
  assert.deepEqual(t.frame(time).contacts, assistedFrame);
});

test('reach assistance cannot rotate a support that would move a separate active plant', () => {
  const B = kit.makeBuilder(9), parts = {};
  function add(id, pivot, parent) {
    const index = B.count();
    B.iso(...pivot, 0.05, B.P[1], 1);
    parts[id] = { pivot, parent, ids: [index] };
  }
  add('chest', [0, 0, 0]);
  add('upper', [0, 1, 0], 'chest');
  add('lower', [0, 1.5, 0], 'upper');
  add('brace', [-0.5, 1, 0], 'chest');
  const puppet = K.puppet(B.finish(), { parts });
  const options = {
    puppet, duration: 1, sample: () => ({}), contacts: [{
      id: 'reach', upper: 'upper', part: 'lower', point: [0, 2, 0], target: [1.4, 1.75, 0],
      start: 0, end: 1, pole: [0, 0, 1], assist: [{ part: 'chest', maxDegrees: 20 }]
    }]
  };
  const unlocked = K.anim.contacts.create(options).inspect(0.5).contacts[0];
  assert(unlocked.assist[0].degrees > 5);
  const held = K.anim.contacts.create({ ...options, contacts: [...options.contacts,
    { id: 'brace', part: 'brace', point: [-0.5,1,0], target: [-0.5,1,0], start: 0.2, end: 0.7 }] });
  const [reach, brace] = held.inspect(0.5).contacts;
  assert.deepEqual(reach.assist, []);
  assert(near(brace.position, [-0.5,1,0]));
  assert(held.inspect(0.9).contacts[0].assist.length === 1);
});

test('the headless timeline CLI reports the captured geometry and the remaining grip gap', () => {
  const cli = path.resolve(__dirname, '../cli/ink-studio.js'), file = path.resolve(__dirname, '../examples/scene-contacts.js');
  const run = time => JSON.parse(execFileSync(process.execPath, [cli, 'animation-timeline', file, '--at', time], { encoding: 'utf8' }));
  const seated = run('1.1');
  assert.equal(seated.frame.contacts.contacts[1].surface.owner, 'rail');
  assert(seated.frame.contacts.contacts[0].normalMiss < 1e-4);
  const reach = run('2.42');
  assert.equal(reach.frame.contacts.reaches[0].status, 'out-of-range');
  assert.equal(reach.lanes.transfers[0].reachStatus, 'out-of-range');
});

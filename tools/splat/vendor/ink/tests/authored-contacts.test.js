const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const lib = require('..').load();
const { anim, M, V, puppet } = lib.KIT;
const scene = require('../examples/authored-contacts')(lib);
const near = (a, b, tolerance = 1e-7) =>
  a.length === b.length && a.every((v, i) => Math.abs(v - b[i]) < tolerance);

function rig() {
  const B = lib.makeBuilder(7), parts = {};
  const add = (name, pivot, parent) => {
    const id = B.count();
    B.iso(...pivot, 0.05, B.P[1], 1);
    parts[name] = { pivot, parent, ids: [id] };
  };
  add('root', [0, 0, 0]);
  add('upper', [0, 1, 0], 'root');
  add('hand', [0.5, 1, 0], 'upper');
  add('foot', [-0.2, 0, 0], 'root');
  add('prop', [1, 0, 0]);
  return puppet(B.finish(), { parts });
}

test('contact ranges fade in and out, hold point targets, and leave reusable poses intact', () => {
  const actor = rig();
  const source = Object.freeze({ root: Object.freeze({ pos: Object.freeze([0.2, 0, 0]) }) });
  const timeline = anim.contacts.create({ duration: 2, puppet: actor, sample: () => source, sockets: { floor: { p: [-0.2, 0, 0] } },
    contacts: [
      { id: 'foot', part: 'foot', point: [-0.2, 0, 0], target: 'floor', start: 0.4, end: 1.4, fadeIn: 0.2, fadeOut: 0.2 },
      { id: 'hand', upper: 'upper', part: 'hand', point: [1, 1, 0], target: [0.75, 0.62, 0.15],
        start: 0.7, end: 1.2, pole: [0, 0, 1] }
    ] });
  assert.equal(timeline.inspect(0.3).contacts.length, 0);
  assert.ok(Math.abs(timeline.inspect(0.5).contacts[0].strength - 0.5) < 1e-8);
  assert.ok(Math.abs(timeline.inspect(1.3).contacts[0].strength - 0.5) < 1e-8);
  const contact = timeline.pose(0.9).contacts;
  assert.ok(near(contact[0].position, [-0.2, 0, 0]));
  assert.ok(near(contact[1].position, [0.75, 0.62, 0.15]));
  const previous = actor.pose, data = Array.from(actor.bones);
  assert.equal(timeline.inspect(1.6).contacts.length, 0);
  assert.equal(actor.pose, previous);
  assert.deepEqual(Array.from(actor.bones), data);
  assert.deepEqual(source, { root: { pos: [0.2, 0, 0] } });
});

test('socket keys preserve the rigid transform on every switch, including a half-turn settle', () => {
  const actor = rig(), sockets = {
    bench: { point: [1, 0, 0] },
    hand: { part: 'hand', point: [1, 1, 0], rotation: [0, 180, 0] },
    rack: { p: [-0.4, 0.5, 0], normal: [0, 1, 0], tangent: [1, 0, 0] }
  };
  const timeline = anim.contacts.create({ duration: 2, puppet: actor, sockets, sample: time => ({ root: { pos: [time * 0.1, 0, 0] } }),
    prop: { part: 'prop', socket: 'bench', keys: [
      { id: 'park', time: 1.25, to: 'rack', settle: 0.3 },
      { id: 'lift', time: 0.5, to: 'hand', settle: 0.3 }
    ] } });
  for (const [time, old, current] of [[0.5, 'bench', 'hand'], [1.25, 'hand', 'rack']]) {
    const before = timeline.inspect(time - 1e-8).attachment, after = timeline.inspect(time).attachment;
    assert.equal(before.owner, old);
    assert.equal(after.owner, current);
    assert.ok(near(before.position, after.position));
    assert.ok(near(before.rotation, after.rotation));
  }
  const mid = timeline.inspect(0.65).attachment.rotation;
  assert.ok(near(M.mul(M.tr(mid), mid), M.id()));
  assert.ok(Math.abs(M.det(mid) - 1) < 1e-8);
  assert.ok(near(timeline.inspect(0.9).attachment.position, [1.09, 1, 0]));
  const snapshots = [1.4, 0.3, 0.6, 1.8].map(time => timeline.inspect(time));
  for (const expected of snapshots.reverse()) assert.deepEqual(timeline.inspect(expected.time), expected);
  assert.ok(near(timeline.inspect(1.8).attachment.position, sockets.rack.p));
});

test('pickup preview measures reach, switches ownership, and settles on the moving grip', () => {
  const world = scene.build(scene.seed), timeline = world.contactTimeline;
  const beat = timeline.focus('pickup');
  assert.ok(beat.reachDistance > 0.2 && beat.reachMiss < 1e-8);
  assert.ok(beat.start < beat.reachStart && beat.reachStart < beat.time && beat.settleEnd > beat.time);
  assert.equal(beat.phaseAt(beat.time), 'transfer');
  assert.equal(beat.phaseAt((beat.time + beat.settleEnd) / 2), 'settle');
  assert.ok(Math.abs(beat.timeAt(beat.duration + 0.04) - beat.start - 0.04) < 1e-8);
  const exact = world.contactDemo.update(beat.time);
  assert.equal(exact.attachment.owner, 'right-hand');
  assert.ok(V.dist(exact.attachment.position, exact.reaches[0].position) < 1e-8);
  assert.ok(exact.contacts[0].miss < 1e-8);
  const carried = world.contactDemo.update(beat.settleEnd + 0.1);
  assert.equal(carried.attachment.owner, 'right-hand');
  assert.ok(V.dist(carried.attachment.position, exact.attachment.position) > 0.1);
  const edit = world.contactDemo.edit({ time: 1.35, pin: false });
  assert.equal(edit.inspect(1.22).attachment.owner, 'plinth');
  assert.equal(edit.inspect(1.35).attachment.owner, 'right-hand');
  assert.equal(edit.inspect(1.35).contacts.length, 0);
  assert.equal(timeline.inspect(1.22).attachment.owner, 'right-hand');
});

test('an unreachable grip reports the miss and keeps both limb lengths', () => {
  const actor = rig();
  const timeline = anim.contacts.create({ duration: 2, puppet: actor, sample: () => ({}),
    sockets: { stand: { point: [2.2, 1, 0] }, hand: { part: 'hand', point: [1, 1, 0] } },
    prop: { part: 'prop', socket: 'stand', keys: [
      { id: 'pickup', time: 1, to: 'hand', reach: { upper: 'upper', pole: [0, 0, 1] } }
    ] } });
  assert.ok(timeline.handoffs[0].reachMiss > 1.1);
  const at = timeline.pose(1);
  assert.ok(at.reaches[0].miss > 1.1);
  assert.ok(near(at.attachment.position, [2.2, 1, 0]));
  const shoulder = actor.point('upper', [0, 1, 0]);
  const elbow = actor.point('hand', [0.5, 1, 0]);
  assert.ok(Math.abs(V.dist(shoulder, elbow) - 0.5) < 1e-8);
  assert.ok(Math.abs(V.dist(elbow, at.reaches[0].position) - 0.5) < 1e-8);
});

test('CLI publishes an exact ownership frame without running stateful playback', () => {
  const output = execFileSync(process.execPath, ['cli/ink-studio.js', 'authored-contacts',
    'examples/authored-contacts.js', '--at', '1.22'], { cwd: path.join(__dirname, '..'), encoding: 'utf8' });
  const report = JSON.parse(output);
  assert.equal(report.sample.attachment.owner, 'right-hand');
  assert.equal(report.handoffs[0].time, 1.22);
  assert.ok(report.sample.contacts[0].miss < 1e-8);
});

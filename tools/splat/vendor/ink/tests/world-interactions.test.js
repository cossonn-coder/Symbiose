const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const I = KIT.world.interactions;
const flush = () => new Promise(resolve => setImmediate(resolve));

test('actions serialize state, revisions and effects and reject retries from a stale sequence', async () => {
  let release;
  const gate = new Promise(resolve => { release = resolve; });
  const stages = [], effects = [], sound = Error('audio offline');
  const world = I.create({ id: 'tower', interactables: [I.breakable({ id: 'brick', point: [1, 2, 3], integrity: 2 })],
    async realize(next) {
      if (next.event) {
        stages.push(next.event);
        if (next.sequence === 1) await gate;
      }
      return { collider: next.states.brick.remaining > 0 };
    } });
  const initial = await world.restore();
  const off = world.onEvent(() => { throw sound; });
  world.onEvent((event, snapshot, before) => {
    assert.equal(world.current(), snapshot);
    assert.equal(snapshot.sequence, before.sequence + 1);
    assert.equal(snapshot.revision.collider, snapshot.states.brick.remaining > 0);
    effects.push(event);
  });
  const args = { amount: 1 };
  const hit = world.dispatch('brick', 'hit', { args, expectedSequence: 0 });
  const retry = world.dispatch('brick', 'hit', { args, expectedSequence: 0 });
  args.amount = 10;
  await flush();
  assert.equal(stages[0].detail.remaining, 1);
  assert.equal(world.current(), initial);
  assert.equal(world.checkpoint().sequence, 0);
  assert.deepEqual(effects, []);
  release();
  const first = await hit;
  assert.deepEqual(first.errors, [sound]);
  assert.equal(await retry, null);
  assert.equal(off(), true);
  const broken = await world.dispatch('brick', 'hit', { expectedSequence: 1 });
  assert.equal(broken.snapshot.revision.collider, false);
  assert.deepEqual(broken.event.point, [1, 2, 3]);
  assert.equal(broken.event.cue, 'break');
  assert.equal(await world.dispatch('brick', 'hit'), null);
  assert.deepEqual(effects.map(event => event.sequence), [1, 2]);
  assert.equal(stages.length, 2);
});

test('failure preserves the last published world and due timers, and a retry emits once', async () => {
  let fail = 'press';
  const effects = [];
  const world = I.create({ interactables: [I.latch({ id: 'switch', ticks: 3 })],
    realize(next) {
      if (next.event?.action === fail) throw Error('publication failed');
      return { powered: next.states.switch.active };
    } });
  world.onEvent(event => effects.push(event.cue));
  const initial = await world.restore();
  await assert.rejects(world.dispatch('switch', 'press'), /publication failed/);
  assert.equal(world.current(), initial);
  assert.deepEqual(world.checkpoint().timers, []);
  assert.deepEqual(effects, []);
  fail = null;
  await world.dispatch('switch', 'press', { expectedSequence: 0 });
  await world.advance(2);
  const opening = world.current(), saved = world.checkpoint();
  fail = 'reset';
  await assert.rejects(world.advance(5), /publication failed/);
  assert.equal(world.current(), opening);
  assert.equal(world.checkpoint(), saved);
  assert.deepEqual(effects, ['switch-on']);
  fail = null;
  const settled = await world.advance(5);
  assert.equal(settled.tick, 5);
  assert.deepEqual(settled.outcomes.map(({ event }) => [event.tick, event.cue]), [[3, 'switch-off']]);
  assert.equal(world.current().revision.powered, false);
  assert.deepEqual(effects, ['switch-on', 'switch-off']);
  assert.deepEqual((await world.advance(5)).outcomes, []);
});

test('restored timers run in stable order, respect a work limit and support replacement and cancellation', async () => {
  const unit = id => ({ id, initial: false, actions: {
    start: () => ({ state: true, timers: { timeout: { after: 4, action: 'wake', args: { phase: 'done' } } } }),
    cancel: () => ({ state: false, timers: { timeout: null } }),
    wake: ({ timer, args }) => ({ state: timer === 'timeout' && args.phase, cue: 'woke' })
  } });
  const options = { id: 'test', interactables: ['c', 'b', 'a'].map(unit), realize: next => next.states };
  const session = I.create(options);
  await session.restore();
  await session.dispatch('b', 'start');
  await session.dispatch('c', 'start');
  await session.dispatch('a', 'start');
  await session.advance(1);
  await session.dispatch('a', 'start');
  await session.dispatch('c', 'cancel');
  const checkpoint = JSON.parse(JSON.stringify(session.checkpoint()));
  const next = I.create(options), seen = [];
  next.onEvent(event => seen.push([event.target, event.tick, event.sequence]));
  await next.restore(checkpoint);
  assert.deepEqual(seen, []);
  const first = await next.advance(12, { limit: 1 });
  assert.deepEqual([first.tick, first.complete], [4, false]);
  assert.deepEqual(next.current().states, { c: false, b: 'done', a: true });
  const second = await next.advance(12, { limit: 1 });
  assert.deepEqual([second.tick, second.complete], [12, true]);
  assert.deepEqual(seen, [['b', 4, 6], ['a', 5, 7]]);
  assert.deepEqual(next.checkpoint().timers, []);
  const malformed = I.create(options);
  await assert.rejects(malformed.restore({ ...checkpoint, timers: [{ ...checkpoint.timers[0], action: 'unknown' }] }), /Invalid timer/);
  assert.equal(malformed.current(), null);
});

test('the break and timed gate publish matching splats, clearance, navigation and persistent place state', async () => {
  const { session, wall, gate } = require('../examples/interactable-locks')(KIT);
  try {
    const { asset } = await session.enter('locks'), sim = asset.interactions;
    const sdf = at => sim.current().revision.frame.distance(...at);
    const sealed = asset.world;
    assert(sdf(wall) < 0 && sdf(gate) < 0);
    assert.equal(asset.route().reason, 'disconnected');
    await sim.dispatch('cracked-wall', 'hit');
    assert.equal(asset.world, sealed);
    await sim.dispatch('cracked-wall', 'hit');
    assert(sdf(wall) > 0 && sdf(gate) < 0);
    assert.equal(asset.route().reason, 'disconnected');
    assert(asset.world.count < sealed.count);
    const effect = asset.frameAt(0.24);
    assert(effect.count > asset.world.count);
    assert.deepEqual(effect.data, asset.frameAt(0.24).data);
    assert.equal(asset.frameAt(1), asset.world);
    await sim.dispatch('gate-switch', 'press');
    assert(sdf(gate) > 0);
    assert.equal(asset.route().ok, true);
    await sim.advance(20);
    await session.enter('landing');
    const save = JSON.parse(JSON.stringify(session.checkpoint()));
    const restored = require('../examples/interactable-locks')(KIT).session;
    await restored.restore(save);
    const again = (await restored.enter('locks')).asset;
    assert.equal(again.interactions.current().tick, 20);
    assert.equal(again.interactions.current().sequence, 3);
    assert.equal(again.frameAt(0.24), again.world);
    assert.deepEqual(again.world.data, asset.world.data);
    assert.equal(again.route().ok, true);
    await again.interactions.advance(90);
    const { frame } = again.interactions.current().revision;
    assert(frame.distance(...wall) > 0 && frame.distance(...gate) < 0);
    assert.equal(again.route().reason, 'disconnected');
    restored.dispose();
  } finally {
    session.dispose();
  }
});

test('indexed burst samples match the existing deformation and can be sampled out of order', () => {
  const pieces = [[-0.8, 1.1, 0], [0.8, 1, 0.12]];
  const motion = KIT.deform.burst({ pieces, life: 1 });
  assert.deepEqual(motion.piece(1, 0), { point: pieces[1], scale: 1 });
  const first = motion.piece(1, 0.3);
  motion.t = 0.3;
  assert.deepEqual(motion(pieces[1]), first.point);
  motion.piece(0, 0.9);
  assert.deepEqual(motion.piece(1), first);
  assert.throws(() => motion.piece(-1, 0), /piece index/);
});

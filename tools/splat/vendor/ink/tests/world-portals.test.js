const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { execFileSync } = require('node:child_process');
const core = require('..');
const { KIT } = core.load();
const { portals } = KIT.world;
const deferred = () => {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
};
const settle = () => new Promise(resolve => setImmediate(resolve));
const a = { origin: [0, 0, 0], normal: [0, 0, 1] };
const b = { origin: [8, 1, 4], normal: [1, 0, 0] };
const aperture = { halfWidth: 1.2, halfHeight: 1.5 };
const from = { place: 'a', anchor: 'door' }, to = { place: 'b', anchor: 'door' };

test('doorway crossing sweeps a bounded oriented aperture and maps poses and velocity', () => {
  const door = portals.doorway({ from: a, to: b, ...aperture });
  const reverse = portals.doorway({ from: b, to: a, ...aperture });
  assert.deepEqual(door.point([0, 0, -2]), [10, 1, 4]);
  assert.deepEqual(door.direction([0, 0, -3]), [3, 0, 0]);
  assert(KIT.V.dist(reverse.point(door.point([0.7, 3, -9])), [0.7, 3, -9]) < 1e-12);
  assert.equal(door.hit([3, 0, 1], [0, 0, -1]), null);
  assert.equal(door.hit([0, 0, -1], [0, 0, 1]), null);
  assert.equal(door.hit([1, 0, 2], [1, 0, -2], { radius: 0.3 }), null);
  assert.deepEqual(door.hit([0, 0, 1], [0, 0, -3]), { point: [0, 0, 0], fraction: 0.25 });
  const ellipse = portals.doorway({ from: a, to: b, ...aperture, shape: 'ellipse' });
  assert.equal(ellipse.hit([1.1, 1.3, 1], [1.1, 1.3, -1]), null);
  const camera = { eye: [0, 0, 4], right: [1, 0, 0], up: [0, 1, 0], back: [0, 0, 1] };
  assert.equal(JSON.stringify(door.camera(camera)),
    JSON.stringify({ eye: [4, 1, 4], right: [0, 0, 1], up: [0, 1, 0], back: [-1, 0, 0] }));
  assert.throws(() => portals.anchor({ ...a, up: [0, 0, 1] }), /independent/);
});

test('nearby preview is promoted once, gated, and keeps place state on the return trip', async () => {
  const held = deferred(), loads = [], released = [], assetB = { world: { name: 'dungeon' } };
  let unlocked = false, state = 1;
  const session = portals.create({
    places: [
      { id: 'a', anchors: { door: a }, prepare(context) {
        loads.push(['a', context.reason, context.state?.state]);
        state = context.state?.state ?? state;
        return { world: {}, checkpoint: () => ({ state }), dispose: () => released.push('a') };
      } },
      { id: 'b', anchors: { door: b }, prepare(context) { loads.push(['b', context.reason]); return held.promise; } }
    ],
    links: [
      { id: 'in', from, to, aperture, open: () => unlocked },
      { id: 'out', from: to, to: from, aperture }
    ]
  });
  const start = await session.enter('a');
  assert.equal(session.approach([0, 0, 2]), null);
  unlocked = true;
  const approach = session.approach([0, 0, 2]);
  assert.equal(session.approach([0, 0, 1]).ready, approach.ready);
  assert.equal(session.view(), null);
  held.resolve(assetB);
  await approach.ready;
  assert.equal(session.view().destination, assetB.world);
  const actor = { position: [0, 0, -1], velocity: [0, 0, -2], carried: { id: 'lamp' } };
  unlocked = false;
  assert.equal(await session.cross('in', { previous: [0, 0, 1], actor }), null);
  unlocked = true;
  state = 7;
  const crossed = await session.cross('in', { previous: [0, 0, 1], actor });
  assert.equal(crossed.place.asset, assetB);
  assert.equal(session.current(), crossed.place);
  assert.deepEqual(crossed.actor.position, [9, 1, 4]);
  assert.deepEqual(crossed.actor.velocity, [2, 0, 0]);
  assert.equal(crossed.actor.carried.id, 'lamp');
  assert.equal(Object.isFrozen(actor.carried), false);
  assert.equal(start.id, 'a');
  assert.deepEqual(session.checkpoint(), { place: 'b', saved: { a: { state: 7 } } });
  assert.equal(session.view(), null);
  await session.cross('out', { previous: [9, 1, 4], actor: { position: [7.5, 1, 4] } });
  assert.equal(session.current().id, 'a');
  assert.deepEqual(loads, [['a', 'enter', undefined], ['b', 'preview'], ['a', 'preview', 7]]);
  assert.deepEqual(released, ['a']);
  session.dispose();
});

test('preview replacement aborts an old load and disposes its late result', async () => {
  const held = deferred(), released = [];
  let signal;
  const session = portals.create({ places: [
    { id: 'a', anchors: { door: a }, prepare: () => ({}) },
    { id: 'b', anchors: { door: b }, prepare(context) { signal = context.signal; return held.promise; } }
  ], links: [{ id: 'in', from, to, aperture }] });
  await session.enter('a');
  const pending = session.approach([0, 0, 2]).ready;
  await settle();
  assert.equal(session.approach([0, 0, 12]), null);
  assert.equal(signal.aborted, true);
  held.resolve({ dispose: () => released.push('b') });
  assert.equal(await pending, null);
  assert.deepEqual(released, ['b']);
  assert.equal(session.current().id, 'a');
  session.dispose();
});

test('walking through a still-loading doorway retains that destination', async () => {
  const held = deferred();
  const session = portals.create({ places: [
    { id: 'a', anchors: { door: a }, prepare: () => ({}) },
    { id: 'b', anchors: { door: b }, prepare: () => held.promise }
  ], links: [{ id: 'in', from, to, aperture }] });
  await session.enter('a');
  const preview = session.approach([0, 0, 1]);
  const walking = session.cross('in', { previous: [0, 0, 1], actor: { position: [0, 0, -0.2] } });
  assert.equal(session.approach([0, 0, -0.2]), null);
  assert.equal(session.current().id, 'a');
  held.resolve({});
  assert.equal((await walking).place.asset, await preview.ready);
  assert.equal(session.current().id, 'b');
});

test('fade waits at black for readiness, arrives at the anchor, and recovers from failure', async () => {
  const held = deferred();
  const session = portals.create({ places: [
    { id: 'a', anchors: { door: a }, prepare: () => ({}) },
    { id: 'b', anchors: { door: b }, prepare: () => held.promise }
  ], links: [{ id: 'pool', from, to, mode: 'fade', radius: 1.5, duration: 1 }] });
  await session.enter('a');
  assert.equal(session.fade('pool', { actor: { position: [2, 0, 0] } }), null);
  const fade = session.fade('pool', { actor: { position: [0.3, 0, 0], velocity: [1, 0, 0] } });
  assert.equal(fade.advance(0.25).opacity, 0.5);
  assert.equal(fade.advance(1).phase, 'hold');
  assert.equal(session.current().id, 'a');
  const asset = {};
  held.resolve(asset);
  await settle();
  const swap = fade.advance(0);
  assert.equal(swap.opacity, 1);
  assert.equal(swap.place.asset, asset);
  assert.deepEqual(swap.arrival.actor.position, b.origin);
  assert.deepEqual(swap.arrival.actor.velocity, [0, 0, 0]);
  assert.equal(fade.advance(0.5).phase, 'done');
  session.dispose();

  const fail = portals.create({ places: [
    { id: 'a', anchors: { door: a }, prepare: () => ({}) },
    { id: 'b', anchors: { door: b }, prepare() { throw new Error('offline'); } }
  ], links: [{ id: 'pool', from, to, mode: 'fade', duration: 1 }] });
  await fail.enter('a');
  const play = fail.fade('pool', { actor: { position: [0, 0, 0] } });
  play.advance(0.5);
  await settle();
  const recovered = play.advance(0.5);
  assert.equal(recovered.phase, 'failed');
  assert.equal(recovered.opacity, 0);
  assert.equal(recovered.place.id, 'a');
  assert.match(recovered.error.message, /offline/);
});

test('place clocks tick active and retained places, and survive a JSON checkpoint round trip', async () => {
  const loaded = [], stepped = [], arrivals = [], released = [];
  const hold = deferred();
  const definitions = {
    places: [
      { id: 'a', anchors: { door: a }, prepare: payload },
      { id: 'b', tickPolicy: 'continue', anchors: { door: b }, prepare: payload }
    ],
    links: [{ id: 'in', from, to, aperture }, { id: 'out', from: to, to: from, aperture }]
  };
  function payload({ id, reason, state, time }) {
    loaded.push([id, reason, state?.elapsed, time]);
    let elapsed = state?.elapsed ?? 0;
    return {
      step(frame) { elapsed += frame.dt; stepped.push([frame.id, frame.time, frame.active]); },
      checkpoint: () => ({ elapsed }),
      prepareArrival({ anchor, state, time, signal }) {
        arrivals.push([anchor.origin, state.elapsed, time, signal]);
        return hold.promise;
      },
      dispose: () => released.push(id)
    };
  }
  const session = portals.create(definitions);
  assert.deepEqual(session.place('a'), {
    id: 'a', anchors: { door: portals.anchor(a) }, time: 0, status: 'inactive', tickPolicy: 'pause'
  });
  assert.equal(session.place('missing'), null);
  session.step(1);
  await session.enter('a');
  const preview = await session.prepare('in');
  assert.equal(session.place('b').status, 'inactive');
  session.step(2);
  assert.equal(preview.checkpoint().elapsed, 0);
  assert.equal((await session.enter('b')).id, 'b');
  session.step(3);
  assert.equal(session.place('a').time, 2);
  const bAsset = session.current().asset;
  await session.enter('a', 'door');
  const returnPreview = session.approach([0, 0, 1]);
  await settle();
  assert.deepEqual(arrivals[0].slice(0, 3), [b.origin, 3, 3]);
  assert.equal(session.approach([0, 0, 100]), null);
  assert.equal(arrivals[0][3].aborted, true);
  session.step(4);
  hold.resolve();
  assert.equal(await returnPreview.ready, null);
  assert.equal(session.place('b').status, 'away');
  assert.deepEqual(stepped, [['a', 2, true], ['b', 3, true], ['a', 6, true], ['b', 7, false]]);
  const save = JSON.parse(JSON.stringify(session.checkpoint()));
  assert.deepEqual(save, { place: 'a', saved: { a: { elapsed: 6 }, b: { elapsed: 7 } },
    clocks: { a: 6, b: 7 }, away: ['b'] });
  assert.equal(await session.prepare('in'), bAsset);
  assert.equal((await session.cross('in', { previous: [0, 0, 1], actor: { position: [0, 0, -1] } })).place.asset, bAsset);
  assert.equal(session.place('b').time, 7);
  assert.deepEqual(loaded, [['a', 'enter', undefined, 0], ['b', 'preview', undefined, 0], ['b', 'enter', undefined, 0],
    ['a', 'enter', 2, 2]]);
  session.dispose();
  assert.deepEqual(released, ['b', 'a', 'a', 'b']);

  const restored = portals.create(definitions);
  await restored.restore(save);
  assert.deepEqual(loaded.slice(-2), [['a', 'restore', 6, 6], ['b', 'restore', 7, 7]]);
  assert.equal(restored.place('b').status, 'away');
  assert.throws(() => restored.step(-1), /nonnegative/);
  restored.step(0);
  restored.step(1);
  assert.deepEqual(stepped.slice(-2), [['a', 7, true], ['b', 8, false]]);
  assert.deepEqual(restored.checkpoint().saved, { a: { elapsed: 7 }, b: { elapsed: 8 } });
  const returnTrip = await restored.cross('in', { previous: [0, 0, 1], actor: { position: [0, 0, -1] } });
  assert.deepEqual(returnTrip.place.asset.checkpoint(), { elapsed: 8 });
  assert.equal(loaded.length, 6);
  restored.dispose();
});

test('links describe locked one-way drops and explicit returns between stable anchors', async () => {
  const hatch = { origin: [0, 0, 0], normal: [0, 1, 0], up: [0, 0, 1] };
  const drop = { id: 'drop', mode: 'drop', from: { place: 'a', anchor: 'hatch' }, to, radius: 1,
    requires: { all: [{ path: '/actor/key', value: 'brass' }, { path: '/state/open', value: true },
      { path: '/time', op: 'gte', value: 1 }] } };
  let open = false;
  const session = portals.create({
    places: [
      { id: 'a', anchors: { hatch, door: a }, prepare: () => ({ checkpoint: () => ({ open }) }) },
      { id: 'b', tickPolicy: 'continue', anchors: { door: b }, prepare: () => ({}) }
    ],
    links: [drop, { id: 'return', from: to, to: from, aperture }]
  });
  const history = [];
  session.onCross(event => history.push([event.link.id, event.sourceDisposition]));
  await session.enter('a', 'hatch');
  assert.deepEqual(session.linksFrom('a').map(link => link.id), ['drop']);
  assert.deepEqual(session.linksFrom('b').map(link => link.id), ['return']);
  assert.deepEqual(session.linksFrom('c'), []);
  assert(Object.isFrozen(session.linksFrom('a')));
  const actor = { position: [0, -2, 0], velocity: [0, -4, 0], key: 'brass', forward: [0, 0, 1] };
  const previous = [0, 2, 0];
  const camera = { eye: [0, 0, 4], target: actor.position, back: [0, 0, 1] };
  assert.equal(await session.cross('drop', { previous, actor }), null);
  open = true;
  session.step(1);
  assert.equal(await session.cross('drop', { previous, actor: { ...actor, key: 'tin' } }), null);
  assert.equal(await session.cross('drop', { previous: actor.position, actor: { ...actor, position: previous } }), null);
  assert.equal(await session.cross('drop', { previous: [0.9, 2, 0],
    actor: { ...actor, position: [0.9, -2, 0] }, radius: 0.2 }), null);
  await session.prepare('drop');
  assert.equal(session.view('drop', actor), null);
  const travel = await session.cross('drop', { previous, actor, camera, radius: 0.2 });
  assert.deepEqual(travel.crossing, { fraction: 0.5, point: hatch.origin });
  assert.deepEqual(travel.actor, { ...actor, position: b.origin });
  assert.deepEqual(travel.camera, { ...camera, eye: [8, 3, 8], target: b.origin });
  await assert.rejects(session.cross('drop', { previous, actor }), /active place/);
  await session.cross('return', { previous: [9, 1, 4], actor: { position: [7.5, 1, 4] } });
  assert.equal(session.current().id, 'a');
  assert.equal(session.place('b').status, 'away');
  assert.deepEqual(history, [['drop', 'released'], ['return', 'retained']]);
  session.dispose();
});

test('failed and cancelled restores release staged payloads without publishing place state', async () => {
  const hold = deferred(), released = [];
  let fail = true, restoringSignal;
  const create = () => portals.create({ places: [
    { id: 'a', prepare: () => ({ dispose: () => released.push('a') }) },
    { id: 'b', tickPolicy: 'continue', prepare({ signal }) {
      if (fail) throw new Error('offline');
      restoringSignal = signal;
      return hold.promise;
    } }
  ] });
  const save = { place: 'a', saved: { a: { x: 2 } }, clocks: { a: 4 }, away: ['b'] };
  const session = create();
  await assert.rejects(session.restore({ ...save, away: ['a'] }), /away places/);
  await assert.rejects(session.restore(save), /offline/);
  assert.deepEqual(released, ['a']);
  assert.deepEqual(session.checkpoint(), { place: null, saved: {} });
  fail = false;
  const restoring = session.restore(save);
  await settle();
  assert.equal(session.current(), null);
  assert.equal(session.place('a').time, 0);
  assert.throws(() => session.step(1), /already being updated/);
  session.dispose();
  assert.equal(restoringSignal.aborted, true);
  hold.resolve({ dispose: () => released.push('b') });
  assert.equal(await restoring, null);
  assert.deepEqual(released, ['a', 'a', 'b']);
  const oldSave = create();
  await oldSave.restore({ place: 'a', saved: {} });
  assert.equal(oldSave.current().id, 'a');
  oldSave.dispose();
});

test('arrival checks share the crossing pose and clearance without committing the travel', async () => {
  const hold = deferred(), order = [];
  let locked = false, blocked = true;
  const source = {
    checkpoint() { order.push('save'); return { open: true }; },
    dispose() { order.push('release'); }
  };
  const destination = { canArrive(actor) {
    assert.deepEqual(actor.position, [9, 1.5, 4]);
    assert.deepEqual(actor.inventory, ['lantern']);
    assert.equal(actor.projectiles, undefined);
    return !blocked;
  } };
  const session = portals.create({ places: [
    { id: 'a', anchors: { door: a }, prepare: () => source },
    { id: 'b', anchors: { door: b }, prepare: () => hold.promise }
  ], links: [{ id: 'in', from, to, aperture, open: () => !locked, transfer(context) {
    assert.equal(context.source.asset, source);
    assert.equal(context.destination, destination);
    assert(Object.isFrozen(context.actor.inventory));
    const { projectiles, ...carry } = context.arrival;
    return { ...carry, position: [9, 1.5, 4] };
  } }] });
  const unsubscribe = session.onCross(event => {
    assert.equal(event.link.id, 'in');
    assert.equal(event.source.asset, source);
    assert.equal(event.place, session.current());
    assert.equal(event.place.asset, destination);
    assert.equal(event.sourceDisposition, 'released');
    order.push('cross');
  });
  await session.enter('a');
  const actor = { position: [0, 0, -1], velocity: [0, 0, -2], inventory: ['lantern'], projectiles: ['shot'] };
  const options = { previous: [0, 0, 1], actor,
    camera: { eye: [0, 0, 3], right: [1, 0, 0], up: [0, 1, 0], back: [0, 0, 1], target: [0, 0, 0] } };
  assert.equal(session.checkArrival('in').status, 'unprepared');
  assert.equal(session.checkArrival('in', { actor }).status, 'outside');
  const ready = session.prepare('in');
  assert.equal(session.checkArrival('in', options).status, 'loading');
  hold.resolve(destination);
  assert.equal(await ready, destination);
  assert.equal(session.checkArrival('in').status, 'prepared');
  locked = true;
  assert.equal(session.checkArrival('in', options).status, 'locked');
  locked = false;
  assert.equal(session.checkArrival('in', options).status, 'blocked');
  assert.equal(await session.cross('in', options), null);
  blocked = false;
  const clear = session.checkArrival('in', options);
  assert.equal(clear.status, 'ready');
  assert.deepEqual(clear.camera.eye, [5, 1.5, 4]);
  assert.deepEqual(clear.camera.target, [8, 1.5, 4]);
  assert.equal(session.current().asset, source);
  assert.deepEqual(order, []);
  blocked = true;
  assert.equal(await session.cross('in', options), null);
  blocked = false;
  const crossed = await session.cross('in', options);
  assert.deepEqual(crossed.actor, clear.actor);
  assert.deepEqual(crossed.camera, clear.camera);
  assert.deepEqual(actor.projectiles, ['shot']);
  assert.deepEqual(order, ['save', 'cross', 'release']);
  assert.equal(unsubscribe(), true);
  session.dispose();
});

test('fade emits one crossing and reports observer or release errors on the committed arrival', async () => {
  const events = [], sound = new Error('sound unavailable'), release = new Error('source cleanup failed');
  const session = portals.create({ places: [
    { id: 'a', anchors: { door: a }, prepare: () => ({ dispose() { throw release; } }) },
    { id: 'b', anchors: { door: b }, prepare: () => ({}) }
  ], links: [{ id: 'pool', from, to, mode: 'fade', duration: 1,
    transfer({ arrival }) { return { position: arrival.position, arrived: true }; } }] });
  await session.enter('a');
  session.onCross(() => { throw sound; });
  session.onCross(event => { events.push(event); });
  const remove = session.onCross(() => { assert.fail('unsubscribed observer fired'); });
  assert.equal(remove(), true);
  await session.prepare('pool');
  const options = { actor: { position: a.origin, trail: [1, 2] } };
  assert.deepEqual(session.checkArrival('pool', options).actor, { position: b.origin, arrived: true });
  const playback = session.fade('pool', options);
  await settle();
  const middle = playback.advance(0.5);
  assert.equal(middle.error, null);
  assert.deepEqual(middle.arrival.errors, [sound, release]);
  assert.equal(middle.arrival.place, session.current());
  assert.equal(playback.advance(0.5).phase, 'done');
  assert.equal(playback.advance(1).arrival, middle.arrival);
  assert.deepEqual(events.map(event => event.actor), [{ position: b.origin, arrived: true }]);
  session.dispose();
});

test('abandoning a preview releases its payload but leaves borrowed place assets live', async () => {
  const held = deferred(), disposed = [];
  let previewSignal;
  const source = { dispose() { disposed.push('source'); } };
  const session = portals.create({ places: [
    { id: 'a', anchors: { door: a }, prepare: ({ previous }) => previous ?? source },
    { id: 'b', anchors: { door: b }, prepare({ signal }) { previewSignal = signal; return held.promise; } }
  ], links: [{ id: 'out', from, to, aperture }, { id: 'loop', from, to: from, aperture }] });
  await session.enter('a');
  const preview = session.prepare('out');
  await settle();
  assert.equal(session.cancelPreparation('loop'), false);
  assert.equal(session.cancelPreparation('out'), true);
  assert.equal(previewSignal.aborted, true);
  assert.equal(session.checkArrival('out').status, 'unprepared');
  held.resolve({ dispose() { disposed.push('preview'); } });
  assert.equal(await preview, null);
  assert.deepEqual(disposed, ['preview']);
  assert.equal(await session.prepare('loop'), source);
  assert.equal(session.cancelPreparation(), true);
  assert.deepEqual(disposed, ['preview']);
  const result = await session.cross('loop', { previous: [0, 0, 1], actor: { position: [0, 0, -1] } });
  assert.equal(result.sourceDisposition, 'reused');
  assert.deepEqual(disposed, ['preview']);
  session.dispose();
  assert.deepEqual(disposed, ['preview', 'source']);
});

function browserProbe(createRenderer, createTransitionComposer, defineTransition) {
  const canvas = document.querySelector('canvas');
  const renderer = createRenderer(canvas, { toolkit: { KIT, PixelLook } });
  const gl = canvas.getContext('webgl2'), size = 65;
  const from = { origin: [0, 0, 0], normal: [0, 0, 1] };
  const to = { origin: [8, 0, 4], normal: [1, 0, 0] };
  const door = shape => KIT.world.portals.doorway({ from, to, halfWidth: 0.9, halfHeight: 0.9, shape });
  const s = makeBuilder(1, [0, 0xff2020, 0x20ff20]);
  s.disc(0, 0, -1, [0, 0, 1], 6, 0.02, s.P[1], 1);
  s.disc(-0.45, 0, 1, [0, 0, 1], 0.17, 0.02, s.P[2], 1);
  const source = s.finish({ cam: { target: [0, 0, 0], dist: 4 } });
  const d = makeBuilder(1, [0, 0x2040ff, 0xffac20]);
  d.disc(10, 0, 4, [-1, 0, 0], 6, 0.02, d.P[1], 1);
  d.disc(7, 0, 4, [-1, 0, 0], 6, 0.02, d.P[2], 1);
  const destination = d.finish();
  const read = () => {
    const bytes = new Uint8Array(size * size * 4);
    gl.readPixels(0, 0, size, size, gl.RGBA, gl.UNSIGNED_BYTE, bytes);
    if (gl.getError() !== gl.NO_ERROR) throw new Error('WebGL error during portal render');
    return (x, y) => bytes.slice((y * size + x) * 4, (y * size + x) * 4 + 3);
  };
  const render = (overrides = {}, shape) => {
    renderer.render(source, { width: size, height: size, raw: true, portal: { source, destination, opening: door(shape) },
      ...overrides });
    return read();
  };
  function dominant(image, x, y, channel, label) {
    const rgb = image(x, y);
    if (rgb[channel] < 170 || rgb.some((v, i) => i !== channel && v >= 120))
      throw new Error(label + ' yielded ' + rgb.join(','));
  }
  const front = render();
  dominant(front, 32, 32, 2, 'a rotated destination is visible and geometry before the exit is clipped');
  dominant(front, 17, 32, 1, 'foreground occludes the doorway');
  dominant(front, 3, 32, 0, 'source remains visible outside the doorway');
  dominant(render({ camera: { yaw: Math.PI } }), 32, 32, 0, 'the doorway is hidden from behind');
  dominant(render({ camera: { ortho: true } }), 32, 32, 2, 'orthographic doorway');
  const circle = render({}, 'ellipse');
  dominant(circle, 32, 32, 2, 'ellipse center');
  dominant(circle, 13, 13, 0, 'ellipse corner');

  const { V } = KIT, fov = 38 * Math.PI / 180;
  const cam = { target: [0, 0, 0], dist: 4, fov };
  const red = makeBuilder(1, [0xff2020]).finish({ cam }), blue = makeBuilder(1, [0x2040ff]).finish();
  function pair(source, destination, opening, frame = {}) {
    renderer.render(source, { width: size, height: size, raw: true, ...frame, portal: { source, destination, opening } });
    return read();
  }
  function apertureAt(from, to, halfWidth = 0.9, halfHeight = 0.9) {
    return KIT.world.portals.doorway({ from, to, halfWidth, halfHeight });
  }
  const opposite = { origin: [0, 0, 0], normal: [0, 0, -1] };
  const aligned = apertureAt(from, opposite);
  const slanted = (background, z) => {
    const builder = makeBuilder(1, [background, 0x20ff20]);
    builder.disc(0, 0, z, [Math.SQRT1_2, 0, -Math.SQRT1_2], 1.7, 0.015, builder.P[1], 1);
    return builder.finish({ cam });
  };
  for (const z of [-0.12, 0.12]) {
    const exit = pair(red, slanted(0x2040ff, z), aligned);
    dominant(exit, 22, 32, 1, 'destination fragment behind the plane survives');
    dominant(exit, 42, 32, 2, 'destination fragment in front of the plane is cut');
    const foreground = pair(slanted(0xff2020, z), blue, aligned);
    dominant(foreground, 22, 32, 2, 'source fragment behind the portal leaves the opening visible');
    dominant(foreground, 42, 32, 1, 'source fragment in front of the portal occludes it');
  }

  const rolled = apertureAt({ origin: [0, 0, 0], normal: [0.4, -0.25, 1], up: [-1, 0.35, 0.2] },
    { origin: [12, 8, -9], normal: [0.2, 1, -0.4], up: [0.3, 0.4, 1] }, 0.95, 0.38);
  const oblique = pair(red, blue, rolled);
  const at = (axis, distance) => {
    const p = V.mad(rolled.from.origin, axis, distance);
    const half = (cam.dist - p[2]) * Math.tan(fov / 2);
    return p.slice(0, 2).map(value => Math.floor((value / half + 1) * size / 2));
  };
  dominant(oblique, ...at(rolled.from.right, 0.76), 2, 'inside the rolled opening along its wide axis');
  dominant(oblique, ...at(rolled.from.up, 0.59), 0, 'outside the rolled opening along its short axis');
  const hatch = apertureAt({ origin: [0, 0, 0], normal: [0, 1, 0], up: [0, 0, -1] }, rolled.to);
  const down = { eye: [0, 4, 0], right: [1, 0, 0], up: [0, 0, -1], back: [0, 1, 0] };
  dominant(pair(red, blue, hatch, { camera: { pose: down } }), 32, 32, 2, 'horizontal opening seen from above');
  const offset = apertureAt({ origin: [1, 0, 0], normal: [0.8, 0, 0.6] }, rolled.to);
  const orthographic = pair(red, blue, offset, { camera: { ortho: true, dist: 5,
    pose: { eye: [0, 0, 0], right: [1, 0, 0], up: [0, 1, 0], back: [0, 0, 1] } } });
  dominant(orthographic, 58, 32, 2, 'orthographic ray on the front side with its center eye behind the plane');
  dominant(orthographic, 32, 32, 0, 'orthographic ray starting behind the plane');

  const decorated = (z, background) => {
    const builder = makeBuilder(11, [background, 0x505050, 0xff40e8]);
    const sculpt = KIT.sculpt(makeSculpt(builder));
    const fringe = KIT.sprite.art('xxxxx\nxxxxx\nxxxxx\nxxxxx', { key: { x: { pal: 2 } } });
    const material = KIT.pixel.edge(KIT.pixel.plain({ r: [1] }), { up: [fringe], side: [fringe], every: 2, share: 1 });
    sculpt.pixel = true;
    sculpt.box([0, -0.14, z], [0.42, 0.12, 0.08], material, { res: 0.06 });
    sculpt.bake();
    return builder.finish({ cam, detail: 4, look: { pixel: true } });
  };
  function spriteCount(image) {
    let count = 0;
    for (let y = 15; y <= 49; y++) for (let x = 15; x <= 49; x++) {
      const [r, g, b] = image(x, y);
      if (r > 220 && g < 100 && b > 190) count++;
    }
    return count;
  }
  const frontSprites = decorated(0.4, 0xff2020), backSprites = decorated(-0.4, 0x2040ff);
  if (!spriteCount(pair(frontSprites, blue, aligned, { raw: false })) ||
      spriteCount(pair(frontSprites, blue, aligned, { raw: false, edges: false })))
    throw new Error('source edge sprites should occlude the opening only where their drawn pixels are in front');
  if (!spriteCount(pair(red, backSprites, aligned, { raw: false })) ||
      spriteCount(pair(red, frontSprites, aligned, { raw: false })))
    throw new Error('destination edge sprites should be clipped at the arrival plane');

  const { waterBodies } = KIT.procedural;
  const pool = (min, max) => waterBodies.scene([waterBodies.create({ id: 'pool',
    bounds: { min: [min, 0], max: [max, 8] }, sample: () => ({ bed: -2, surface: 2 }),
    optics: { tint: [0, 0, 0], extinction: [1, 1, 1], foam: 0, surface: 0, caustics: 0, refraction: 0 } })]);
  const underwater = (min, max) => render({ portal: { source, opening: door(),
    destination: { ...destination, water: pool(min, max) } } })(32, 32);
  if (underwater(5, 7.8)[2] < 238 || underwater(8.1, 9.7)[2] > 75)
    throw new Error('water attenuation must start at the destination doorway plane');

  const half = render({ fade: 0.5 }), dark = render({ portal: null, fade: 1 });
  if (half(32, 32)[2] < 119 || half(32, 32)[2] > 130 || dark(32, 32).some(v => v !== 0))
    throw new Error('fade opacity was not applied to the visible frame');
  const pose = door().camera(renderer.cameraPose(source, { width: size, height: size }));
  if (pose.eye[0] !== 4 || pose.back[0] !== -1) throw new Error('camera handoff lost the relative pose');

  const composer = createTransitionComposer(canvas);
  const before = composer.createTarget(size, size), after = composer.createTarget(size, size);
  renderer.render(red, { raw: true, target: before, portal: { destination: blue, opening: rolled } });
  renderer.render(red, { raw: true, target: after });
  composer.setSource('from', before);
  composer.setSource('to', after);
  composer.draw(defineTransition({ stages: [{}] }).sample(0), { width: size, height: size });
  dominant(read(), 32, 32, 2, 'portal view remains in the GPU transition source');
  composer.dispose();
  renderer.dispose();
}

test('WebGL presents oriented apertures with per-fragment clipping, occlusion and transitions', {
  skip: !process.env.INK_TEST_CHROME
}, () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-portals-'));
  try {
    const browserEntry = pathToFileURL(path.resolve(__dirname, '../webgl.mjs')).href;
    const page = path.join(temp, 'portals.html');
    fs.writeFileSync(path.join(temp, 'bundle.js'), core.bundle());
    fs.writeFileSync(page, `<!doctype html><canvas></canvas><pre id="result">PENDING</pre>
<script src="bundle.js"></script><script type="module">
import { createRenderer, createTransitionComposer, defineTransition } from ${JSON.stringify(browserEntry)};
const result = document.querySelector('#result');
try { (${browserProbe.toString()})(createRenderer, createTransitionComposer, defineTransition); result.textContent = 'PASS'; }
catch (error) { result.textContent = error.stack; }
</script>`);
    const html = execFileSync(process.env.INK_TEST_CHROME, [
      '--headless', '--no-first-run', '--disable-background-networking', '--allow-file-access-from-files',
      '--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--user-data-dir=' + path.join(temp, 'profile'),
      '--dump-dom', pathToFileURL(page).href
    ], { timeout: 90000, encoding: 'utf8', maxBuffer: 4e6, stdio: ['ignore', 'pipe', 'ignore'] });
    assert.equal(html.match(/<pre id="result">([^<]*)<\/pre>/)?.[1], 'PASS');
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
});

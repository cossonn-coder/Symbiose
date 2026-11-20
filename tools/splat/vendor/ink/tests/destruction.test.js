const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: K, makeBuilder } = require('..').load();
const { V, M } = K;
const near = (a, b, e = 1e-5) => assert(Math.abs(a - b) < e, `${a} != ${b}`);
const vectorNear = (a, b, e = 1e-5) => a.forEach((x, i) => near(x, b[i], e));
function fixture(points = [[-0.5, 2, 0], [0.5, 2, 0], [0, 3, 0], [0, 2.5, 0.5], [8, 2, 0]]) {
  const B = makeBuilder(17);
  for (const p of points) B.iso(...p, 0.09, B.P[3], 3);
  const W = B.finish(), st = K.stage(W);
  return { W, st, D: st.D };
}
const totalMomentum = pieces => pieces.reduce((p, b) => V.mad(p, b.v, b.mass), [0, 0, 0]);

test('releases the current pose without a snap and inherits translation, spin and point impulses', () => {
  const { st, D } = fixture(), ids = [0, 1, 2, 3], reset = D.slice();
  st.rig = { free: new Uint8Array(st.N) };
  const d = K.destruction(st, { gravity: 0, groups: [{ id: 'moving', ids, mass: 8, fragmentSize: 0.4,
    motion: () => ({ v: [4, 2, 1], w: [0, 0, 2], origin: [2, 3, 0] }) }] });
  const turn = M.rot([0, 1, 0], 0.8);
  for (const id of ids) D.set(V.add(M.app(turn, Array.from(D.subarray(id * 16, id * 16 + 3))), [2, 1, 0]), id * 16);
  d.sync();
  const before = D.slice(), center = d.inspect('moving').center;
  const pieces = d.release('moving', { p: center, impulse: [12, 0, 0] });
  assert(pieces.length > 1);assert.deepEqual(D, before);
  const expected = V.add(V.mul(V.add([4, 2, 1], V.cross([0, 0, 2], V.sub(center, [2, 3, 0]))), 8), [12, 0, 0]);
  vectorNear(totalMomentum(pieces), expected);
  for (const b of pieces) vectorNear(b.w, [0, 0, 2]);
  assert(ids.every(id => st.rig.free[id] === 1));
  d.update(1 / 120);assert(D.every(Number.isFinite));assert.notDeepEqual(D, before);
  d.reset();assert.deepEqual(D, reset);assert(ids.every(id => st.rig.free[id] === 0));
  assert.equal(d.rubble.bodies.length, 0);assert.equal(d.stats.intact, 1);
});

test('estimates rigid motion from consecutive current geometry samples', () => {
  const { st, D } = fixture();
  const d = K.destruction(st, { gravity: 0, groups: [{ id: 'prop', ids: [0, 1, 2, 3] }] });
  const original = D.slice(), rotation = M.rot([0, 1, 0], 0.02), dt = 0.01;
  for (const id of [0, 1, 2, 3]) D.set(V.add(M.app(rotation, Array.from(original.subarray(id * 16, id * 16 + 3))), [0.03, 0, 0]), id * 16);
  d.sync(dt);
  vectorNear(d.inspect('prop').angularVelocity, [0, 2, 0], 1e-4);
  const pose = d.inspect('prop'), b = d.release('prop')[0];
  vectorNear(b.v, pose.velocity);vectorNear(b.w, [0, 2, 0], 1e-4);
});

test('support uses surviving paths to anchors and cascades only after the final support is lost', () => {
  const { st } = fixture();
  const d = K.destruction(st, { groups: [
    { id: 'left', ids: [0], anchor: true }, { id: 'right', ids: [1], anchor: true },
    { id: 'deck', ids: [2] }, { id: 'roof', ids: [3] }
  ], links: [['left', 'deck'], ['right', 'deck'], ['deck', 'roof']] });
  d.release('left');assert(d.intact('deck'));assert(d.intact('roof'));
  const fall = d.release('right');assert.equal(fall.length, 3);
  assert.equal(d.intact('deck'), false);assert.equal(d.intact('roof'), false);
  assert.deepEqual(d.release('deck'), []);
  d.reset();assert.equal(d.stats.intact, 4);
  d.sever('left', 'deck');assert(d.intact('deck'));
  d.sever('right', 'deck');assert.equal(d.intact('deck'), false);
});

test('swept impacts catch thin targets at cannonball speeds, respect holes and transfer momentum', () => {
  const { st } = fixture([[0, 3, 0], [0, 4, 0], [0, 2, 0]]);
  const d = K.destruction(st, { gravity: 0, groups: [{ id: 'wall', ids: [0, 1, 2], strength: 1, mass: 6 }] });
  assert.equal(d.sweep([-10, 3.5, 0], [10, 3.5, 0], 0.02), null);
  const hit = d.sweep([-10, 3, 0], [10, 3, 0], 0.15);
  assert.equal(hit.group, 'wall');assert(hit.fraction > 0.4 && hit.fraction < 0.5);
  const ball = d.launch({ p: [-4, 3, 0], v: [1200, 0, 0], mass: 2, radius: 0.15 });
  d.update(1 / 120);
  assert.equal(d.intact('wall'), false);assert(ball.p[0] > -0.3);
  const momentum = V.add(totalMomentum(d.rubble.bodies), V.mul(ball.v, ball.mass));
  // Rubble's air drag is part of its existing solver, not lost impact momentum.
  near(momentum[0], 2400, 3);
  assert(d.drainEvents().some(e => e.kind === 'projectile-hit' && e.group === 'wall'));
});

test('damage accumulates, radial impacts test actual samples, and unbreakable groups rebound shots', () => {
  const { st } = fixture([[-0.5, 3, 0], [0.5, 3, 0], [4, 3, 0]]);
  const d = K.destruction(st, { gravity: 0, groups: [
    { id: 'arch', ids: [0, 1], strength: 4 }, { id: 'fixed', ids: [2], breakable: false }
  ] });
  assert.deepEqual(d.impact({ p: [0, 3, 0], impulse: [100, 0, 0] }).hits, []);
  d.impact({ p: [-0.5, 3, 0], impulse: [1, 0, 0] });assert(d.intact('arch'));
  near(d.inspect('arch').damage, 0.25);
  d.impact({ p: [-0.5, 3, 0], impulse: [3, 0, 0] });assert.equal(d.intact('arch'), false);
  const ball = d.launch({ p: [3, 3, 0], v: [100, 0, 0], radius: 0.1, restitution: 0.5 });
  d.update(0.025);assert(ball.v[0] < -49);assert(d.intact('fixed'));
});

test('debris expires, reset restores all row fields and frees only its own physics', () => {
  const { st, D } = fixture(), before = D.slice();
  st.rig = { free: Uint8Array.from([0, 1, 0, 0, 0]) };
  const unrelated = K.rubble(st, { gravity: 0 });unrelated.spawn([4], { v: [2, 0, 0] });
  const d = st.add(K.destruction(st, { groups: [{ id: 'chips', ids: [0, 1, 2, 3], mode: 'debris', fragmentSize: 0.4 }] }));
  d.release('chips', { life: 0.1, v: [2, 4, 0] });
  for (let i = 0; i < 15; i++) st.update(0.02, i * 0.02);
  assert.equal(d.debris.chunks.length, 0);assert.equal(D[3], 0);
  d.reset();assert.deepEqual(D, before);assert.deepEqual(Array.from(st.rig.free), [0, 1, 0, 0, 1]);
  assert.equal(unrelated.bodies.length, 1);
  st.repaintAll([0, 1, 2, 3]);st.update(0, 1);assert.equal(D[3], before[3]);
});

test('fragment budgets coarsen before release, failed cascades and malformed inputs preserve geometry', () => {
  const { st, D } = fixture(), before = D.slice();
  const d = K.destruction(st, { maxPieces: 2, groups: [{ id: 'wall', ids: [0, 1, 2, 3], fragmentSize: 0.01 }] });
  assert(d.release('wall').length <= 2);d.reset();
  assert.throws(() => d.release('wall', { v: [NaN, 0, 0] }), /finite/);assert(d.intact('wall'));assert.deepEqual(D, before);
  d.dispose();
  const limited = K.destruction(st, { maxPieces: 1, groups: [{ id: 'pier', ids: [0], anchor: true }, { id: 'deck', ids: [1] }], links: [['pier', 'deck']] });
  assert.throws(() => limited.release('pier'), /budget/);assert(limited.intact('pier'));assert.deepEqual(D, before);
  assert.throws(() => K.destruction(st, { groups: [{ id: 'a', ids: [0] }, { id: 'b', ids: [0] }] }), /ownership/);
  assert.throws(() => K.destruction(st, { groups: [{ id: 'a', ids: [4] }], links: [['a', 'missing']] }), /known/);
  assert.throws(() => limited.launch({ p: [0, 0, 0], v: [1, 0, 0], mass: -1 }), /mass/);
  assert.throws(() => limited.update(1), /step/);
});

test('fixed-step cannon and catapult trajectories give the same impact across render rates and reset replay', () => {
  function run(dt, reset = false) {
    const { st } = fixture([[0, 2, 0], [0, 2.3, 0], [0, 1.7, 0]]);
    const d = K.destruction(st, { gravity: 10, seed: 5, groups: [{ id: 'tower', ids: [0, 1, 2], strength: 1, mass: 3, fragmentSize: 0.2 }] });
    const fire = () => d.launch({ id: 'catapult', p: [-6, 1, 0], v: [8, 5.0833333333, 0], mass: 3, radius: 0.3 });
    fire();
    for (let t = 0; t < 1.5 - dt * 0.5; t += dt) d.update(dt);
    const result = () => ({ released: !d.intact('tower'), bodies: d.rubble.bodies.map(b => ({ p: b.c.slice(), v: b.v.slice() })), events: d.drainEvents().map(e => [e.kind, e.group]) });
    const first = result();assert(first.released);
    if (reset) { d.reset();fire();for (let t = 0; t < 1.5 - dt * 0.5; t += dt) d.update(dt);assert.deepEqual(result(), first); }
    return first;
  }
  assert.deepEqual(run(1 / 30, true), run(1 / 120));
});

test('subsequent projectiles push and wake detached rubble rather than passing through it', () => {
  const { st } = fixture([[0, 3, 0], [0, 3.1, 0], [0, 2.9, 0]]);
  const d = K.destruction(st, { gravity: 0, groups: [{ id: 'loose', ids: [0, 1, 2], mass: 4 }] });
  const body = d.release('loose')[0];body.asleep = true;
  const ball = d.launch({ p: [-1, 3, 0], v: [40, 0, 0], mass: 2, radius: 0.1 });
  for (let i = 0; i < 3; i++) d.update(1 / 120);
  assert(body.v[0] > 1);assert.equal(body.asleep, false);
  near(totalMomentum([body])[0] + ball.v[0] * ball.mass, 80, 0.1);
  assert(d.drainEvents().some(e => e.kind === 'projectile-hit' && e.piece));
});

test('moving rubble strikes other intact groups and starts a second collapse', () => {
  const { st } = fixture([[-1, 3, 0], [-1, 3.1, 0], [0, 3, 0], [0, 3.1, 0]]);
  const d = K.destruction(st, { gravity: 0, groups: [
    { id: 'beam', ids: [0, 1], mass: 5 }, { id: 'wall', ids: [2, 3], mass: 3, strength: 1 }
  ] });
  d.release('beam', { v: [20, 0, 0] });d.update(0.1);
  assert.equal(d.intact('wall'), false);
  assert(d.drainEvents().some(e => e.kind === 'piece-hit' && e.target === 'wall'));
});

test('bindings use shared named selectors, reject overlapping systems and release ownership on disposal', () => {
  const { st, W } = fixture();
  W.renderMetadata = { materialIds: Uint32Array.from([1, 1, 2, 2, 0]), materials: [null, 'stone', 'wood'] };
  const d = st.add(K.destruction(st, { groups: [{ id: 'stone', selector: { material: 'stone' } }] }));
  assert.equal(d.inspect('stone').splats, 2);
  assert.throws(() => K.destruction(st, { groups: [{ id: 'other', ids: [0] }] }), /ownership/);
  assert.throws(() => K.destruction(st, { groups: [{ id: 'other', selector: { material: 'absent' } }] }), /Empty/);
  d.dispose();assert(!st.systems.includes(d));assert(!st.painters.includes(d));
  assert.throws(() => d.release('stone'), /disposed/);
  const again = K.destruction(st, { groups: [{ id: 'other', ids: [0] }] });assert(again.intact('other'));
});

test('off-center impulses induce rotation and balanced fracture scatter preserves net linear momentum', () => {
  const { st } = fixture();
  const d = K.destruction(st, { groups: [{ id: 'gate', ids: [0, 1, 2, 3], mass: 10, fragmentSize: 0.25 }] });
  const center = d.inspect('gate').center;
  const pieces = d.release('gate', { p: V.add(center, [0, 1, 0]), impulse: [5, 0, 0], scatter: 2 });
  vectorNear(totalMomentum(pieces), [5, 0, 0]);assert(pieces.every(p => p.w[2] < 0));
});

test('piece limits reserve capacity for later structures and impacts remain safe when capacity is exhausted', () => {
  const { st } = fixture();
  const d = K.destruction(st, { maxPieces: 3, groups: [
    { id: 'first', ids: [0, 1, 2], fragmentSize: 0.01 }, { id: 'second', ids: [3], strength: 1 }, { id: 'third', ids: [4], strength: 1 }
  ] });
  assert.equal(d.release('first').length, 1);
  d.impact({ p: [0, 2.5, .5], impulse: [2, 0, 0], group: 'second' });
  d.impact({ p: [8, 2, 0], impulse: [2, 0, 0], group: 'third' });
  assert.equal(d.stats.pieces, 3);assert.equal(d.stats.intact, 0);d.dispose();
  const small = K.destruction(st, { maxPieces: 1, groups: [{ id: 'a', ids: [0] }, { id: 'b', ids: [1], strength: 1 }] });
  small.release('a');
  const result = small.impact({ p: [.5, 2, 0], impulse: [10, 0, 0], group: 'b' });
  assert(result.blocked);assert(small.intact('b'));assert(small.drainEvents().some(e => e.kind === 'budget-blocked'));
});

test('the interactive scene can fire both weapons in either order without exhausting its piece budget and resets exactly', () => {
  const kit = require('..').load(), scene = require('../examples/destruction')(kit), world = scene.build(scene.seed);
  const { physics, fire, advance, reset } = world.destructionDemo;
  const before = world.data.slice();
  for (const order of [['catapult', 'cannon'], ['cannon', 'catapult']]) {
    for (const weapon of order) { fire(weapon);advance(2); }
    assert.equal(physics.intact('tower'), false);assert.equal(physics.intact('bridge'), false);
    assert(physics.stats.pieces <= 52);assert(world.data.every(Number.isFinite));
    reset();world.anim.update(0, world.anim.time);
    assert.equal(physics.stats.intact, 7);assert.deepEqual(world.data.subarray(0, (world.count - 32) * 16), before.subarray(0, (world.count - 32) * 16));
  }
});

test('frame models and pool cleanup cannot overwrite or hide released geometry, and reset returns ownership', () => {
  const C = makeBuilder(3);C.iso(0, 0, 0, 0.12, C.P[3], 3);
  const model = K.frameSplats.capture(C.finish()), B = makeBuilder(4);
  let x = 2, visible = true;
  const frame = K.frameSplats(B, 1, draw => { if (visible) draw.model(model, [x, 3, 0]); });
  const W = B.finish(), stage = K.stage(W);stage.add(frame);stage.update(0, 0);
  const d = stage.add(K.destruction(stage, { gravity: 0, groups: [{ id: 'vehicle', ids: [frame.first] }] }));
  d.release('vehicle', { v: [1, 0, 0] });x = 20;
  stage.update(1 / 60, 1 / 60);near(W.data[0], 2 + 1 / 60, 0.001);assert(W.data[3] > 0);
  visible = false;stage.update(1 / 60, 2 / 60);assert(W.data[3] > 0);assert(W.data[1] > 2.9);
  stage.repaintAll([frame.first]);stage.update(0, 1);
  assert(W.data[3] > 0);
  near(W.data[7], C.finish().data[7]);
  assert.equal(stage.physicsOwned[frame.first], 1);
  d.reset();assert.equal(stage.physicsOwned[frame.first], 0);
  visible = true;stage.update(0, 1);near(W.data[0], 20);
});

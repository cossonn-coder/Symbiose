const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT, makeBuilder, makeSculpt } = require('..').load();
const { characters, cameras } = KIT.world;
const ground = y => ({ y, normal: [0, 1, 0], id: 'floor', material: 'stone' });
const flat = { supports: () => [ground(0)], clearance: point => point[1] };
const dead = { kind: 'air' };
const corner=(x,y)=>Math.hypot(Math.max(0,x),Math.max(0,y))+Math.min(0,Math.max(x,y));

function simulate(controller, state, world, frames, input) {
  let actor = state, last;
  const events = [];
  for (let i = 0; i < frames; i++) {
    last = controller.step(actor, input, 1 / 60, world);
    actor = last.actor;
    events.push(...last.events);
  }
  return { ...last, events };
}

test('the capsule steps up, jumps once while held, falls and stops against thin solids', () => {
  const c = characters.create({ tuning: { radius: 0.14, height: 0.82, stepUp: 0.22 } });
  const step = { supports: x => [ground(x < 0.75 ? 0 : 0.17)],
    clearance: ([x, y]) => Math.min(y, Math.max(0.75 - x, y - 0.17)) };
  const start = c.state({ position: [0, 0.41, 0], inventory: ['lamp'] });
  const walked = simulate(c, start, step, 36, { move: [1, 0] });
  assert(walked.actor.position[0] > 1);
  assert(Math.abs(walked.actor.position[1] - 0.58) < 1e-6);
  assert.equal(walked.support.material, 'stone');
  const jumped = simulate(c, walked.actor, step, 90, { jump: true });
  assert.equal(jumped.events.filter(event => event.type === 'jump').length, 1);
  assert.equal(jumped.events.filter(event => event.type === 'land').length, 1);
  assert.deepEqual(jumped.actor.inventory, ['lamp']);

  const edge = { supports: x => x < 0 ? [ground(0)] : [ground(-1)],
    clearance: ([x, y]) => Math.min(y + 1, Math.max(x, y)) };
  const fallen = simulate(c, c.state({ position: [-0.6, 0.41, 0] }), edge, 75, { move: [1, 0] });
  assert(fallen.events.some(event => event.to === 'air'));
  assert(fallen.events.some(event => event.type === 'land'));
  assert(Math.abs(fallen.actor.position[1] + 0.59) < 1e-6);

  const thin = { ...flat, clearance: p => Math.min(p[1], Math.abs(p[0] - 1) - 0.015) };
  const fast = characters.create({ tuning: { walkSpeed: 32, groundAcceleration: 200, maxStep: 0.1 } });
  const hit = fast.step(fast.state({ position: [0, 0.82, 0] }), { move: [1, 0.34] }, 0.3, thin);
  assert(hit.blocked);
  assert(hit.actor.position[0] < 0.826);
  assert(hit.actor.position[2] > 0.25);
  assert(fast.fits(thin, hit.actor.position));
  assert.throws(() => fast.step(hit.actor, {}, 40, thin), /time budget/);
});

test('a flat-bottom character lands and jumps with only its sole overlapping a ledge', () => {
  const tuning={radius:.25,height:1,stepUp:0}, ledge={supports:x=>x<=0?[ground(0)]:[],
    clearance:([x,y])=>corner(x,y)};
  const controller=characters.create({tuning:{...tuning,flatBottom:true}});
  const rounded=characters.create({tuning});
  const actor=controller.state({position:[.21,.81,0],velocity:[0,-2,0]});
  const seated=simulate(controller,actor,ledge,24,{climb:false});
  assert.equal(seated.actor.mode,'ground');
  assert.deepEqual(seated.actor.position,[.21,.5,0]);
  assert.equal(seated.support.support,'floor');
  assert.equal(simulate(rounded,actor,ledge,24,{climb:false}).actor.mode,'air');
  const jump=controller.step(seated.actor,{jump:true},1/60,ledge);
  assert(jump.events.some(event=>event.type==='jump'));
  const walked=simulate(controller,seated.actor,ledge,24,{move:[1,0],climb:false});
  assert(walked.actor.position[0]>.25);
  assert.equal(walked.actor.mode,'air');
});

test('a flat-bottom character checks toe clearance and keeps the rounded head and standing height', () => {
  const tuning={radius:.3,height:1.2,stepUp:.22}, toe=characters.create({tuning:{...tuning,flatBottom:true}});
  const rounded=characters.create({tuning});
  const sill={supports:x=>[ground(x>=.8?.14:0)],clearance:([x,y])=>Math.min(y,corner(.8-x,y-.14))};
  const center=[.52,.6,0];
  assert(rounded.fits(sill,center));
  assert(!toe.fits(sill,center));
  assert(toe.fits(flat,center));
  const walked=simulate(toe,toe.state({position:[0,.6,0]}),sill,40,{move:[1,0]});
  assert(walked.actor.position[0]>1.2);
  assert(Math.abs(walked.actor.position[1]-.74)<1e-6);
  assert(toe.fits({...flat,clearance:([x,y])=>Math.min(y,corner(.8-x,1.07-y))},center));
  assert.throws(()=>characters.create({tuning:{flatBottom:'yes'}}),/Invalid character body/);
});

test('water currents, separate eye probes and climb-out use the scene queries', () => {
  const controller = characters.create({ tuning: { radius: 0.14, height: 0.82 } });
  const bank = { supports: x => [ground(x < 0 ? -1.5 : 0.55)],
    clearance: ([x, y]) => Math.min(y + 1.5, Math.max(-x, y - 0.55)),
    mediumAt: ([x, y]) => x < 0 && y < 0.3 ? { kind: 'water', id: 'pool', current: [0, 0, 0.4] } : dead };
  const start = controller.state({ position: [-1, -0.35, 0] });
  const submerged = simulate(controller, start, bank, 16, {});
  assert.equal(submerged.eyes.kind, 'water');
  assert.equal(submerged.actor.mode, 'swim');
  assert(submerged.actor.position[2] > 0.05);
  const blocked = simulate(controller, controller.state({ ...submerged.actor, position: [-1, 0.25, 0] }),
    bank, 40, { move: [1, 0], climb: false });
  assert.equal(blocked.medium.kind, 'water');
  assert.equal(blocked.eyes.kind, 'air');
  assert(blocked.actor.position[0] < 0);
  const up = simulate(controller, blocked.actor, bank, 30, { move: [1, 0] });
  assert.equal(up.actor.mode, 'ground');
  assert(up.actor.position[0] > 0.35);
  assert(up.events.some(event => event.type === 'climb-out'));
});

test('custom movement modes retain actor data and use the same collision sweep', () => {
  const controller = characters.create({
    selectMode: ({ input, natural }) => input.boost ? 'glide' : natural,
    modes: { glide({ actor }) { return { velocity: [9, 0, 0], actor: { charge: actor.charge + 1 } }; } }
  });
  const wall = { ...flat, clearance: ([x, y]) => Math.min(y, 1 - x) };
  const start = controller.state({ position: [0, 1.2, 0], charge: 0, inventory: ['lamp'] });
  const glide = controller.step(start, { boost: true }, 0.25, wall);
  assert.equal(glide.actor.mode, 'glide');
  assert(glide.actor.charge > 0);
  assert(glide.blocked);
  assert(glide.actor.position[0] <= 0.821);
  assert.deepEqual(glide.actor.inventory, ['lamp']);
  assert.equal(start.charge, 0);
  const fall = controller.step(glide.actor, {}, 0.05, wall);
  assert.equal(fall.actor.mode, 'air');
  assert(fall.actor.position[1] < glide.actor.position[1]);
});

test('the biome adapter seats a capsule on a conservative field', () => {
  const { biomeWorld, biomeRecipes } = KIT.procedural;
  const source = biomeRecipes.create({ fallback: 'land', recipes: [{ id: 'land', materials: { floor: [0x8c898a] } }] });
  const frame = biomeWorld.create({ height: () => 0 }).prepare(source.view());
  const environment = characters.fromBiome(frame), controller = characters.create();
  const initial = controller.state({ position: [0, 1.5, 0] });
  const result = simulate(controller, initial, environment, 70, { move: [0, -1] });
  assert.equal(result.actor.mode, 'ground');
  assert(result.actor.position[2] < -2);
  assert(controller.fits(environment, result.actor.position));
  assert(result.actor.position[1] < 1);
});

test('camera keeps an ordinary jump in frame, follows landings and recovers from arm occlusion', () => {
  const rig = cameras.follow({ tuning: { yaw: 0, pitch: 0, height: 0, distance: 5, jumpRoom: 1.1, airInfluence: 0.1 } });
  const person = { position: [0, 1, 0], mode: 'ground' }, first = rig.start(person);
  const peak = rig.step(first, { position: [0, 1.9, 0], mode: 'air' }, 0.25);
  assert.equal(peak.level, 1);
  assert(Math.abs(peak.focus[1] - 1.09) < 1e-8);
  const hill = rig.step(peak, { position: [0, 1.9, 0], mode: 'ground' }, 1);
  assert(hill.focus[1] > 1.88);
  const falling = rig.step(hill, { position: [0, -0.5, 0], mode: 'air' }, 0.4);
  assert(falling.focus[1] < 0.1);
  const blocked = rig.step(first, person, 0.1, { clearance: ([, , z]) => 2.1 - z });
  assert(blocked.arm > 1.95 && blocked.arm < 2);
  const released = rig.step(blocked, person, 0.1, { yaw: 0.3, pitch: 0.2 });
  assert(released.arm > blocked.arm && released.arm < 5);
  assert(Math.abs(released.pose.back[1] - Math.sin(0.2)) < 1e-8);
  assert(Math.abs(KIT.V.dot(released.pose.right, released.pose.up)) < 1e-8);
});

test('a locked doorway stops the traveler on the source side at the swept motion segment', async () => {
  const controller = characters.create();
  const anchor = { origin: [0, 0.82, 0] };
  const session = KIT.world.portals.create({
    places: [{ id: 'a', anchors: { door: anchor }, prepare: () => ({}) },
      { id: 'b', anchors: { door: anchor }, prepare: () => ({}) }],
    links: [{ id: 'door', from: { place: 'a', anchor: 'door' }, to: { place: 'b', anchor: 'door' },
      aperture: { halfWidth: 1, halfHeight: 1 }, open: () => false }]
  });
  await session.enter('a');
  const start = controller.state({ position: [0, 0.82, 0.3], velocity: [0, 0, -3] });
  const movement = controller.step(start, { move: [0, -1] }, 0.2, flat);
  assert(movement.actor.position[2] < 0);
  const stopped = await controller.cross(session, 'door', movement);
  assert.equal(stopped.status, 'blocked');
  assert.equal(stopped.arrival, null);
  assert(stopped.actor.position[2] >= 0 && stopped.actor.position[2] < 0.06);
  assert.equal(stopped.actor.velocity[2], 0);
  assert.equal(session.current().id, 'a');
  session.dispose();
});

test('the headless canal transfers one actor and follow rig across a rotated doorway', async () => {
  const example = await require('../examples/canal-traversal')(KIT, makeBuilder, makeSculpt);
  try {
    const preview = example.session.view().asset, phase = [];
    let arrival;
    for (let i = 0; i < 300 && !arrival; i++) {
      const tick = await example.advance();
      if (tick.frame.eyes.kind === 'water') phase.push('underwater');
      if (tick.arrival) arrival = tick.arrival;
    }
    assert(phase.includes('underwater'));
    assert.deepEqual(example.events.filter(event => event.type === 'mode').map(event => event.to), ['air', 'swim', 'ground']);
    assert(example.events.some(event => event.type === 'climb-out'));
    assert.equal(arrival.place.asset, preview);
    assert.equal(arrival.place.id, 'court');
    assert.deepEqual(arrival.actor.inventory, ['lantern']);
    assert(arrival.actor.velocity[0] > 2 && Math.abs(arrival.actor.velocity[2]) < 1e-5);
    assert.deepEqual(example.camera().pose, arrival.camera);
    const tick = await example.advance();
    assert(tick.actor.position[0] > arrival.actor.position[0]);
    assert(tick.actor.mode === 'ground');
    assert(KIT.V.dist(tick.camera.pose.eye, arrival.camera.eye) < 0.09);
  } finally {
    example.session.dispose();
  }
});

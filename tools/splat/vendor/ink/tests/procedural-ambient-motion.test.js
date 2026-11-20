const test = require('node:test');
const assert = require('node:assert/strict');
const { ambientMotion } = require('..').load().KIT.procedural;

const place = ([x, , z]) => [x, 0, z];
const move = ([x, , z], [dx, , dz]) => [x + dx, 0, z + dz];
const roster = [
  { id: 'a', kind: 'land', home: [-.3, 0, 0], radius: .22, range: 2 },
  { id: 'b', kind: 'land', home: [.3, 0, 0], radius: .22, range: 2 }
];

test('seeded motion is independent of frame partition and roster order', () => {
  const a = ambientMotion.create(roster, { place, move }), b = ambientMotion.create(roster.slice().reverse(), { place, move });
  a.reconcile();
  b.reconcile();
  for (let i = 0; i < 240; i++) a.advance(1 / 60);
  for (let i = 0; i < 16; i++) b.advance(.25);
  const first = a.poses(), second = b.poses();
  assert.equal(a.time, b.time);
  assert.deepEqual(first, second);
  assert(first.every(p => p.distance > .1));
  assert(Math.hypot(first[0].point[0] - first[1].point[0], first[0].point[2] - first[1].point[2]) >= .43);
});

test('temporary attraction acknowledges a cue, rounds a blocker and follows a moving target', () => {
  const blocked = ([x, , z]) => x > .28 && x < .6 && Math.abs(z) < .28;
  const f = ambientMotion.create([{ id: 'a', home: [0,0,0], speed: 1.4 }], {
    place: q => blocked(q) ? null : place(q),
    move: (a, delta) => {
      const next = move(a, delta);
      return blocked(next) ? null : next;
    }
  });
  f.reconcile();
  f.attract('a', [1.9,0,0], { hold: .5, duration: 5, stop: .25 });
  f.advance(.2);
  assert.equal(f.poses()[0].mode, 'engaged');
  assert.deepEqual(f.poses()[0].point, [0,0,0]);
  for (let i = 0; i < 150; i++) {
    f.advance(.015);
    assert(!blocked(f.poses()[0].point));
  }
  assert(f.poses()[0].point[0] > 1.2);
  f.retarget('a', [2.7,0,.25]);
  f.advance(.85);
  assert(f.poses()[0].point[0] > 2.2);
  f.advance(1);
  f.advance(.85);
  assert(!['engaged', 'follow', 'gathered'].includes(f.poses()[0].mode));
});

test('precise destinations use a configurable arrival distance independent of separation', () => {
  const target = [1,0,0], member = { id: 'a', home: [0,0,0], speed: 2, radius: .35, rest: [.1,.2] };
  const options = { place, move, destination: () => target };
  const docked = ambientMotion.create([{ ...member, arrival: .01 }],options);
  const roaming = ambientMotion.create([member],options);
  for (const solver of [docked, roaming]) {
    solver.reconcile();
    solver.advance(1);
  }
  assert(Math.abs(docked.poses()[0].point[0] - .99) < 1e-6);
  assert(Math.abs(roaming.poses()[0].point[0] - .88) < 1e-6);
  docked.attract('a',[2,0,0],{hold:0,duration:3,stop:.4});
  docked.advance(1);
  assert(Math.abs(docked.poses()[0].point[0] - 1.6) < 1e-6);
  assert.doesNotThrow(() => ambientMotion.create([{ ...member, range: .04 }], options));
  assert.throws(() => ambientMotion.create([{ ...member, arrival: -.01 }], options), /Invalid ambient member/);
});

test('habitat edits relocate or suspend a member while retaining its identity', () => {
  const member = { id: 'boat', kind: 'water', home: [1,1,2], range: 1 };
  const a = ambientMotion.create([member], {
    place: ([x, , z], spec, water) => water && [x, water.y, z],
    move: ([x, y, z], [dx, , dz]) => [x + dx, y, z + dz],
    destination: (point, spec) => [spec.home[0] + .8, point[1], spec.home[2]]
  });
  a.reconcile({ y: 1.5 });
  assert.deepEqual(a.poses()[0].point, [1,1.5,2]);
  a.reconcile(null);
  assert.equal(a.poses()[0].mode, 'dormant');
  assert.equal(a.poses()[0].point, null);
  a.reconcile({ y: 3 });
  assert.equal(a.poses()[0].id, 'boat');
  assert.equal(a.poses()[0].point[1], 3);
  a.advance(.95, { y: 3 });
  assert(a.poses()[0].point[0] > 1);
  assert.throws(() => a.advance(2), /elapsed/);
});

test('a suspended member yields its space and resumes on the current habitat', () => {
  const queries = [];
  const a = ambientMotion.create(roster, {
    place: ([x, , z], spec, y) => {
      queries.push(spec.id);
      return [x, y, z];
    },
    move
  });
  a.reconcile(0);
  a.attract('a', [1, 0, 0]);
  assert.equal(a.suspend('a'), true);
  assert.equal(a.suspend('a'), false);
  assert.equal(a.suspend('missing'), false);
  const paused = a.poses()[0];
  assert.equal(paused.mode, 'suspended');
  assert.equal(paused.point, null);
  queries.length = 0;
  a.reconcile(2);
  a.attract('b', [-.3, 0, 0], { hold: 0, duration: 4, stop: .02 });
  a.advance(.95, 2);
  assert(!queries.includes('a'));
  assert(a.poses()[1].point[0] < -.22);
  assert.deepEqual(a.poses()[0], paused);
  assert.throws(() => a.resume('a', 2, [NaN, 0, 0]), /release point/);
  assert.equal(a.poses()[0].mode, 'suspended');
  assert(a.resume('a', 2, [3, 5, 4]));
  assert.deepEqual(a.poses()[0].point, [3, 2, 4]);
  assert.equal(a.poses()[0].mode, 'rest');
  assert.equal(a.resume('a', 2), false);
});

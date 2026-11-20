const test = require('node:test');
const assert = require('node:assert/strict');
const { traversal } = require('..').load().KIT.procedural;

const up = [0, 1, 0];
const floor = () => [{ y: 0, normal: up, id: 'ground' }];
const clear = () => Infinity;
const near = (a, b) => assert(Math.abs(a - b) < 1e-6);

test('traversal uses actual stair heights and stops at large drops and steep ground', () => {
  const body = traversal.create({
    supports(x) {
      if (x > 2) return [{ y: -1, normal: up }];
      if (x > 1.7) return [{ y: .75, normal: [-1, .25, 0] }];
      return [{ y: Math.max(0, Math.floor(x / .5) * .25), normal: up, id: 'stairs' }];
    },
    clearance: clear
  });
  const climb = body.move([.1, 0, 0], [1.45, 0]);
  assert.equal(climb.support, 'stairs');
  near(climb.foot[1], .75);
  const steep = body.move(climb.foot, [1, 0]);
  assert(steep.blocked);
  assert(steep.foot[0] <= 1.7);
  const cliff = traversal.create({ supports: x => [{ y: x < 1 ? 0 : -1, normal: up }], clearance: clear });
  assert(cliff.move([.8, 0, 0], [.5, 0]).blocked);
  assert.equal(cliff.stand([1.1, 0, 0]), null);
  near(cliff.stand([1.1, 0, 0], { drop: 1.1 }).foot[1], -1);
});

test('traversal sweeps through an aperture, rejects low headroom and slides along walls', () => {
  function gate(height) {
    return traversal.create({ supports: floor, clearance: ([x, y, z]) => {
      const wall = Math.abs(z) - .005;
      const opening = Math.max(Math.abs(x) - .65, y - height);
      return Math.max(wall, -opening);
    } });
  }
  const open = gate(1.9).move([0, 0, -2], [0, 4]);
  assert.equal(open.blocked, false);
  near(open.foot[2], 2);
  const low = gate(1.45).move([0, 0, -2], [0, 4]);
  assert(low.blocked);
  assert(low.foot[2] < -.18);
  const slide = gate(1.9).move([1, 0, -.3], [1, 1]);
  assert(slide.blocked);
  near(slide.foot[0], 2);
  assert(slide.foot[2] < -.18);
});

test('queries try overlapping supports, validate callbacks and bound work', () => {
  const supports = () => [{ y: .3, normal: up, id: 'top' }, ...floor()];
  const body = traversal.create({ supports, clearance: ([, y]) => 1.8 - y, budget: 2 });
  assert.equal(body.stand([0, 0, 0]).support, 'ground');
  assert.throws(() => body.move([0, 0, 0], [1, 0]), /budget/);
  assert.throws(() => traversal.create({ supports: floor, clearance: () => NaN }).stand([0, 0, 0]), /signed distance/);
  assert(traversal.create({ supports: floor, clearance: clear, radius: .04 }).stand([0, 0, 0]));
});

test('contact traces report accepted ground movement and materials, including slides', () => {
  const body = traversal.create({
    supports: x => [{ y: 0, normal: up, id: 'floor', material: x < 1 ? 'grass' : 'wood' }],
    clearance: ([, , z]) => 1 - z
  });
  const start = [0, 0, 0];
  const move = body.move(start, [2, 2], { trace: true });
  assert(move.blocked);
  assert(move.contacts.length > 0);
  assert.equal(move.contacts.at(-1).material, 'wood');
  assert(move.contacts.some(contact => contact.material === 'grass'));
  assert.deepEqual(move.contacts.at(-1).foot, move.foot);
  assert(move.progress > Math.hypot(move.foot[0], move.foot[2]));
  assert.equal(body.stand(start).material, 'grass');
  assert.equal(body.move(start, [.3, 0]).contacts, undefined);
  assert.deepEqual(body.move(start, [0, 0], { trace: true }).contacts, []);
  assert.deepEqual(body.move(move.foot, [0, .5], { trace: true }).contacts, []);
});

test('cadence is independent of frame distance and leaves state intact when a trace exceeds its budget', () => {
  const body = traversal.create({ supports: floor, clearance: clear });
  const cadence = traversal.cadence({ spacing: .6, first: .2 });
  const from = [0, 0, 0];
  const walk = (foot, delta) => body.move(foot, [delta, 0], { trace: true });
  const whole = cadence.advance(from, walk(from, 2).contacts);
  cadence.reset();
  const a = walk(from, .77), b = walk(a.foot, 1.23);
  const split = [...cadence.advance(from, a.contacts), ...cadence.advance(a.foot, b.contacts)];
  assert.equal(whole.length, 4);
  assert.deepEqual(whole.map(step => step.side), ['left', 'right', 'left', 'right']);
  whole.forEach((step, i) => {
    near(step.foot[0], .2 + .6 * i);
    near(split[i].foot[0], step.foot[0]);
    assert.equal(split[i].index, i);
  });
  const limited = traversal.cadence({ spacing: .6, first: .2, budget: 1 });
  assert.throws(() => limited.advance(from, walk(from, 2).contacts), /budget/);
  assert.throws(() => limited.advance(from, [...walk(from, .3).contacts, null]), /contact/);
  const [first] = limited.advance(from, walk(from, .3).contacts);
  assert.equal(first.index, 0);
  near(first.foot[0], .2);
});

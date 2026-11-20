const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT, makeBuilder } = require('..').load();
const { render } = require('../cli/render');
const { frame, bend, pinned, packedFlag } = KIT.procedural.airflow;

test('pinned airflow coefficients keep the seam fixed and support a separate free direction', () => {
  const motion = pinned({ reach: .8, phase: 1, frequency: 3, phaseTravel: 2 });
  assert.deepEqual(motion(0), { k: 11, wind: true, ph: 1, sp: 3, rg: 0 });
  assert.equal(motion(.5).rg, .2);
  assert.equal(motion(.5, 1).rg, .8);
  assert.equal(motion(.5, -.3).rg, 0);
  assert.equal(motion(2, 9).ph, -1);
  assert.throws(() => pinned({ reach: -.1 }));
  assert.throws(() => pinned({ reach: 1, frequency: 0 }));
});

test('offline airflow matches displacement of the same splat and is still in calm', () => {
  const B = makeBuilder(1);
  B.dab(0, 0, 0, [0, 0, 1], [1, 0, 0], .10, .15, .01, B.P[2], 3, pinned({ reach: .8 })(1));
  const world = B.finish({ cam: { yaw: 0, pitch: 0, dist: 4, target: [0, 0, 0] }, detail: 18, radius: 2 });
  assert(Math.round(world.data[11]) & packedFlag);
  const still = { ...world, data: world.data.slice() };
  still.data[11] = Math.round(still.data[11]) - packedFlag - 11;
  const options = { w: 180, h: 140, px: 1, t: .65 };
  assert.deepEqual(render(world, { ...options, wind: [0, 0] }).rgb, render(still, options).rgb);
  const velocity = [-1, 1.5], [vx, vz] = frame(velocity).flex;
  const arc = bend(options.t, world.data[12], world.data[13], world.data[14]);
  still.data[0] += vx * arc;
  still.data[2] += vz * arc;
  const expected = render(still, options).rgb;
  assert.deepEqual(render(world, { ...options, wind: velocity }).rgb, expected);
  assert.deepEqual(render({ ...world, anim: { wind: velocity } }, options).rgb, expected);
  assert.notDeepEqual(render(world, options).rgb, expected);
});

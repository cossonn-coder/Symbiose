const test = require('node:test');
const assert = require('node:assert/strict');
const { create } = require('..').load().KIT.anim.keyframeTrack;
const near = (actual, expected) => assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} != ${expected}`);

test('keyframe tracks sort, clamp, handle mixed channels and cross the angle seam continuously', () => {
  const deg = Math.PI / 180;
  const frame = (time, yaw, xy, scale, weight, ease = 'linear') => ({ time, value: { yaw: yaw * deg, xy, scale, weight }, ease });
  const start = frame(2, 170, [1, 2], 2, 10);
  const middle = frame(4, -170, [3, 6], 8, 6, 'step');
  const last = frame(7, -90, [5, 6], 9, 4);
  const track = create({ yaw: 'radians', xy: 'vector', scale: 'positive', weight: 'number' }, [last, start, middle]);
  start.value.xy[0] = -10;
  assert.equal(track.duration, 7);
  assert.deepEqual(track.keys.map(key => key.time), [2, 4, 7]);
  assert.deepEqual(track.sample(-1).xy, [1, 2]);
  const halfway = track.sample(3);
  near(halfway.yaw, Math.PI);
  near(halfway.scale, 4);
  assert.deepEqual(halfway.xy, [2, 4]);
  assert.equal(halfway.weight, 8);
  near(track.sample(4).yaw, 190 * deg);
  near(track.sample(6.999).yaw, 190 * deg);
  near(track.sample(100).yaw, 270 * deg);
  assert.equal(track.sample(7).scale, 9);
  halfway.xy[0] = 99;
  assert.equal(track.sample(3).xy[0], 2);
});

test('empty tracks, exact cuts, invalid inputs and portable keys', () => {
  assert.equal(create({ power: 'number' }).sample(0), null);
  const key = { time: 0.123, value: { power: 4 }, ease: 'step' };
  const track = create({ power: 'number' }, [key, { time: 0.456, value: { power: -2 } }]);
  assert.deepEqual(create({ power: 'number' }, JSON.parse(JSON.stringify(track.keys))).keys, track.keys);
  assert.equal(track.sample(0.455999).power, 4);
  assert.equal(track.sample(0.456).power, -2);
  assert.throws(() => track.sample(NaN), /finite/);
  assert.throws(() => create({ power: 'number' }, [key, key]), /unique/);
  assert.throws(() => create({ power: 'positive' }, [{ time: 0, value: { power: 0 } }]), /channel/);
  assert.throws(() => create({ power: 'number' }, [{ ...key, ease: 'out-elastic' }]), /easing/);
  assert.throws(() => create({ axis: 'vector' }, [{ time: 0, value: { axis: [1] } }, { time: 1, value: { axis: [1, 2] } }]), /vector/);
  assert.throws(() => create({ axis: 'vector' }, [{ time: 0, value: { axis: Array(2) } }]), /vector/);
});

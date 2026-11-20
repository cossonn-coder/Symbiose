const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT, makeBuilder } = require('..').load();
const { render } = require('../cli/render');
const S = KIT.procedural.lightSchedule;

test('light selection uses effective intensity and keeps inputs intact', () => {
  const lantern = { id: 'lantern', p: [0, 0, 0], radius: 2, intensity: 2, color: [1, .7, .2], schedule: 'dusk' };
  const always = { ...lantern, id: 'always', intensity: .4, schedule: 'always' };
  assert.equal(S.gain(1), 0);
  assert.equal(S.gain(0), 1);
  assert(Math.abs(S.gain(.37) - .5) < 1e-12);
  assert.throws(() => S.gain(NaN));
  assert.deepEqual(S.select([lantern, always], [0,0,0], { daylight: 1 }), [always]);
  assert.deepEqual(S.select([lantern, always], [0,0,0], { daylight: 0, limit: 1 }), [lantern]);
  assert(Math.abs(S.select([lantern, always], [0,0,0], { daylight: .37, duskOnly: true })[0].intensity - 1) < 1e-12);
  assert.equal(lantern.intensity, 2);
  assert.equal(S.contribution({ ...lantern, normal: [0,0,1] }, 0, 0, -.15), 0);
  assert(S.contribution({ ...lantern, normal: [0,0,1] }, 0, 0, .15) > 0);
});

test('offline renders use the same bake for off, twilight and active lights', () => {
  const B = makeBuilder(1);
  B.dab(-.18, 0, 0, [0,0,1], [1,0,0], .14, .16, .008, [170,135,75], 3, S.marker);
  B.dab(.21, 0, 0, [0,0,1], [1,0,0], .15, .13, .008, [72,67,67], 3);
  const world = B.finish({
    cam: { yaw: 0, pitch: 0, dist: 4, target: [0,0,0] }, detail: 16, radius: 2,
    lights: [{ id: 'glow', p: [-.18,0,0], radius: 1.2, intensity: 2, schedule: 'dusk', color: [1,.7,.25] }]
  });
  const original = world.data.slice(), view = { w: 120, h: 90, px: 1, raw: true };
  const day = render(world, { ...view, lightDaylight: 1 }).rgb;
  const twilight = render(world, { ...view, lightDaylight: .37 }).rgb;
  const night = render(world, { ...view, lightDaylight: 0 }).rgb;
  const sum = values => values.reduce((acc, item) => acc + item, 0);
  assert(sum(day) < sum(twilight) && sum(twilight) < sum(night));
  assert.deepEqual(render(world, view).rgb, day);
  assert.deepEqual(world.data, original);
});

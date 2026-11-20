const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const os = require('node:os');
const { execFileSync } = require('node:child_process');
const lib = require('..').load();
const { KIT: K } = lib;
const scene = require('../examples/cloth-review')(lib);

const point = (xyz, i) => Array.from(xyz.slice(i * 3, i * 3 + 3));

test('XPBD resetPose replaces particle state and preserves the original link length', () => {
  const sim = K.xpbd.sim({ gravity: [0, 0, 0] });
  sim.point([0, 0, 0], 0);
  sim.point([1, 0, 0], 1);
  sim.link(0, 1);
  sim.resetPose([2, 0, 0, 4, 0, 0]);
  assert.equal(sim.X[3], 4);
  sim.step(1 / 60, 1 / 60);
  assert.equal(sim.X[3], 3);
  assert.throws(() => sim.resetPose(Array(6)), /finite XYZ/);
});

test('current-pose capture stays exact and protected regions stay fixed while moving pins follow the rig', () => {
  const B = lib.makeBuilder(2);
  const cape = K.cloth(B, { nu: 3, nv: 3, u: [1, 0, 0], v: [0, -1, 0], dabs: 1 });
  const zones = ['pin', 'protected', 'pin', 'free', 'free', 'free', 'free', 'free', 'free'];
  const review = K.cloth.review.create(cape, { regions: zones });
  const visible = cape.restPose().map((p, i) => p + (i % 3 === 0 ? 1.7 : 0));
  const original = visible.slice();
  const legacy = cape.sim.X.slice(0, 27);
  review.start(visible, { sourceTime: 0.9, pinAt: (index, [x, y, z], t) => [x + t, y, z] });
  visible.fill(0);
  zones.fill('free');
  assert.deepEqual(review.sample(0), original);
  assert.throws(() => review.bake(), /settle/);
  review.advance(0.5);
  const after = review.sample(0.5);
  assert.ok(Math.abs(after[0] - (original[0] + 0.5)) < 1e-6);
  assert.deepEqual(point(after, 1), point(original, 1));
  assert.ok(K.V.dist(point(after, 8), point(original, 8)) > 0.05);
  assert.deepEqual(review.sample(0.5, { before: true }), original);
  assert.deepEqual(cape.sim.X.slice(0, 27), legacy);
});

test('fixed steps settle identically across frame schedules and bake the exact recorded endpoints', () => {
  const first = scene.build(scene.seed), second = scene.build(scene.seed);
  first.clothDemo.start(0.9);
  second.clothDemo.start(0.9);
  const a = first.clothReview, b = second.clothReview;
  const coarse = a.advance(8);
  for (let f = 1; f <= 240; f++) b.advance(f / 30);
  assert.equal(coarse.phase, 'settled');
  assert.ok(coarse.quiet >= 0.45);
  assert.deepEqual(coarse, b.state());
  const before = a.sample(0), after = a.sample(coarse.time);
  assert.notDeepEqual(after, before);
  a.regions().forEach((role, i) => {
    if (role !== 'free') assert.deepEqual(point(after, i), point(before, i));
  });
  assert.deepEqual(a.sample(1.517), b.sample(1.517));
  const take = a.bake();
  assert.equal(a.state().phase, 'baked');
  assert.equal(a.bake(), take);
  assert.equal(take.sourceTime, 0.9);
  assert.equal(take.duration, coarse.time);
  const restored = K.cloth.review.clip(JSON.parse(JSON.stringify(take)));
  assert.deepEqual(restored.sample(0), before);
  assert.deepEqual(restored.sample(99), after);
  assert.deepEqual(restored.sample(1.517), a.sample(1.517));
  a.discard();
  assert.deepEqual(first.clothDemo.draw('preview', take.duration, restored), after);
  assert.equal(a.state().phase, 'idle');
});

test('continuous motion never enables bake and editing a region invalidates the preview', () => {
  const B = lib.makeBuilder(3);
  const cape = K.cloth(B, { nu: 3, nv: 3, v: [0, -1, 0] });
  const review = K.cloth.review.create(cape, { maxSeconds: 1, minimum: 0.2, quietFor: 0.2 });
  review.start(cape.restPose(), { pinAt: (i, [x, y, z], t) => [x + t, y, z] });
  assert.equal(review.advance(1).phase, 'unsettled');
  assert.throws(() => review.bake(), /settle/);
  assert.throws(() => review.setRegions(['pin']), /every grid point/);
  assert.equal(review.state().phase, 'unsettled');
  const edited = review.regions().slice();
  edited[1] = 'protected';
  review.setRegions(edited);
  assert.equal(review.state().phase, 'idle');
  assert.throws(() => review.sample(0), /Start/);
});

test('CLI writes an explicit portable bake from a requested source pose', t => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-cape-bake-'));
  t.after(() => fs.rmSync(temp, { recursive: true, force: true }));
  const file = path.join(temp, 'cape.json');
  const json = execFileSync(process.execPath,
    ['cli/ink-studio.js', 'cloth-review', 'examples/cloth-review.js', '--pose', '1.20', '--bake', file],
    { cwd: path.join(__dirname, '..'), encoding: 'utf8' });
  const report = JSON.parse(json);
  assert.equal(report.phase, 'baked');
  assert.ok(report.regions.protected > 0);
  const restored = K.cloth.review.clip(JSON.parse(fs.readFileSync(file, 'utf8')));
  assert.equal(restored.sourceTime, 1.2);
  assert.equal(restored.duration, report.time);
});

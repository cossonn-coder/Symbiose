const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const { KIT: K } = require('..').load();
const { raster } = require('../cli/png');

test('story time and pose bias are independent in held and interpolated playback', () => {
  const shelf = K.anim.poseShelf.create();
  shelf.save('start', { root: { pos: [0, 0, 0], rot: [0, 170, 0] } }, { name: 'Ready' });
  shelf.save('end', { root: { pos: [4, 0, 0], rot: [0, -170, 0] } });
  function timeline(time, bias) {
    return K.anim.poseBlocking.create(shelf, { duration: 3, keys: [
      { time: 2, pose: 'end' },
      { time, bias, name: 'Lift', ease: 'linear' },
      { time: 0, pose: 'start', ease: 'linear' },
      { time: 1.4, bias: 0.8, name: 'Pass' }
    ] });
  }
  const a = timeline(0.5, 0.75), b = timeline(0.9, 0.75), c = timeline(0.5, 0.25);
  assert.deepEqual(a.markers.map(marker => marker.name), ['Ready', 'Lift', 'Pass', 'end']);
  assert.deepEqual(a.clip.sample(0.5), b.clip.sample(0.9));
  assert.equal(a.held.sample(0.25).root.pos[0], 0);
  assert.equal(a.clip.sample(0.25).root.pos[0], 1.5);
  assert.equal(a.held.sample(0.5).root.pos[0], 3);
  assert.equal(b.held.sample(0.5).root.pos[0], 0);
  assert.equal(c.held.sample(0.5).root.pos[0], 1);
  assert.equal(a.clip.sample(0.5).root.rot[1], 185);
  assert.equal(a.clip.sample(1.4).root.pos[0], 3.2);
  assert.equal(a.held.sample(3).root.pos[0], 4);
  shelf.save('end', { root: { pos: [8, 0, 0] } });
  assert.equal(a.clip.sample(3).root.pos[0], 4);
  assert.throws(() => timeline(2, 0.5), /unique times/);
  assert.throws(() => timeline(2.2, 0.5), /between story poses/);
});

test('shelf snapshots, stamps and mirrors the whole pose or selected destination parts', () => {
  const shelf = K.anim.poseShelf.create({ pairs: [['left', 'right']] });
  const source = { head: { rot: [4, 20, 10], bend: [2, 3] },
    right: { pos: [2, 3, 4], rot: [20, 30, 40], turn: [1, 2, 3, 4, 5, 6, 7, 8, 9], scale: 2 } };
  shelf.save('reach', source);
  source.right.pos[0] = 99;
  assert.equal(shelf.apply('reach').right.pos[0], 2);
  const mirrored = shelf.apply('reach', { mirror: true });
  assert.deepEqual(mirrored.head, { rot: [4, -20, -10], bend: [2, 3] });
  assert.deepEqual(mirrored.left, {
    pos: [-2, 3, 4], rot: [20, -30, -40],
    turn: [1, -2, -3, -4, 5, 6, -7, 8, 9], scale: 2
  });
  const base = { head: { rot: [0, 0, 0] }, right: { rot: [10, 20, 30] }, left: { scale: [1, 2, 3] } };
  const stamped = shelf.apply('reach', { base, mirror: true, parts: ['left'] });
  const blended = shelf.apply('reach', { base, mirror: true, parts: ['left'], weight: 0.5 });
  assert.deepEqual(stamped.left.pos, [-2, 3, 4]);
  assert.deepEqual(blended.left.pos, [-1, 1.5, 2]);
  assert.deepEqual(blended.left.scale, [1.5, 2, 2.5]);
  assert.deepEqual(blended.right, base.right);
  assert.deepEqual(blended.head, base.head);
  stamped.right.rot[0] = 99;
  mirrored.left.rot[0] = 99;
  assert.equal(base.right.rot[0], 10);
  assert.equal(shelf.apply('reach', { mirror: true }).left.rot[0], 20);
  const restored = K.anim.poseShelf.create({ poses: JSON.parse(JSON.stringify(shelf.list())) });
  assert.deepEqual(restored.apply('reach'), shelf.apply('reach'));
  assert.throws(() => shelf.apply('reach', { parts: ['unknown'] }), /destination parts/);
});

test('pose-review renders named landmarks and masks on the atlas pixel grid', t => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-poses-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  execFileSync(process.execPath, ['cli/ink-studio.js', 'pose-review', 'examples/pose-blocking.js',
    '--w', '64', '--h', '64', '--directions', '4', '--out', directory], { cwd: path.join(__dirname, '..') });
  const atlas = JSON.parse(fs.readFileSync(path.join(directory, 'atlas.json'), 'utf8'));
  const color = raster(path.join(directory, 'color.png'));
  const mask = raster(path.join(directory, 'silhouette.png'));
  assert.equal(atlas.poses.find(pose => pose.name === 'Lift').bias, 0.72);
  assert.equal(atlas.frames.length, atlas.poses.length * 4);
  assert.deepEqual([mask.w, mask.h], [64 * 4, 64 * atlas.poses.length]);
  for (let offset = 3; offset < mask.data.length; offset += 4)
    assert.equal(mask.data[offset], color.data[offset] < 128 ? 0 : 255);
  assert.ok(atlas.frames.every(frame => frame.silhouette.pixels > 0 && !frame.silhouette.touchesBorder));
  assert.notDeepEqual(atlas.frames[0].silhouette.bounds, atlas.frames[3 * 4].silhouette.bounds);
});

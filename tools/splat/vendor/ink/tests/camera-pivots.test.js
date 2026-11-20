const test = require('node:test'), assert = require('node:assert/strict');
const { V, procedural: { cameraPivots } } = require('..').load().KIT;

test('camera pivot modes choose a pointer, exact center, or nearby surface', () => {
  const fallback = [0, 0, 0], point = [4, 5, 6], samples = [];
  const pick = (u, v) => {
    samples.push([u, v]);
    return u === .25 && v === .75 ? point : null;
  };
  assert.equal(cameraPivots.choose('target', { pick, fallback }), fallback);
  assert.deepEqual(samples, []);
  assert.equal(cameraPivots.choose('cursor', { cursor: [.25, .75], pick }), point);
  assert.equal(cameraPivots.choose('center', { pick, fallback }), fallback);
  assert.deepEqual(samples, [[.25, .75], [.5, .5]]);
  assert.equal(cameraPivots.choose('region', { radius: .25, pick }), point);
  assert.equal(samples.length, 10);
  samples.length = 0;
  assert.equal(cameraPivots.choose('region', { pick, fallback }), fallback);
  assert.equal(samples.length, 9);
  assert.equal(cameraPivots.choose('region', { pick: () => point }), point);
});

function projection(view, point) {
  const { yaw, pitch, dist, target } = view;
  const back = [Math.sin(yaw)*Math.cos(pitch), Math.sin(pitch), Math.cos(yaw)*Math.cos(pitch)];
  const eye = V.mad(target, back, dist), right = V.norm(V.cross([0, 1, 0], back)), up = V.cross(back, right);
  const offset = V.sub(point, eye), depth = -V.dot(offset, back);
  return [V.dot(offset, right)/depth, V.dot(offset, up)/depth];
}

test('orbit and zoom preserve an off-center pivot projection and leave the source view intact', () => {
  const view = Object.freeze({ target: Object.freeze([2, 1, -3]), dist: 12, yaw: .4, pitch: .55 });
  const pivot = [5, 3, -2], start = projection(view, pivot);
  const orbit = cameraPivots.orbit(view, -1.8, 1.25, pivot);
  const zoom = cameraPivots.zoom(orbit, 4, pivot);
  for (const after of [orbit, zoom]) {
    const [x, y] = projection(after, pivot);
    assert(Math.abs(x - start[0]) < 1e-12 && Math.abs(y - start[1]) < 1e-12);
    assert.notDeepEqual(after.target, view.target);
  }
  assert.equal(cameraPivots.orbit(view, .1, .2).target, view.target);
  assert.equal(cameraPivots.zoom(view, 3).target, view.target);
  assert.equal(cameraPivots.zoom(view, view.dist, pivot).target, view.target);
});

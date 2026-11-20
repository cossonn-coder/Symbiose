const test = require('node:test');
const assert = require('node:assert/strict');
const { alignedFeatureGroups } = require('..').load().KIT.procedural;

function feature(id, u, v = .4, opts = {}) {
  return { id, at: [u, v], units: [10, 4], size: [1, .8], gap: .22,
    alignment: .08, sizeTolerance: .1, limit: 3, ...opts };
}

test('aligned features join transitively and use the smallest member limit without changing inputs', () => {
  const input = [feature('far', .8), feature('left', .1, .4, { limit: 2 }),
    feature('right', .34), feature('middle', .22), feature('high', .22, .55)];
  const before = JSON.stringify(input);
  const groups = alignedFeatureGroups(input);
  assert.equal(groups.length, 1);
  assert.deepEqual(groups[0].members, ['left', 'middle']);
  assert.deepEqual(groups[0].stations, [1, 2.2]);
  assert.deepEqual(groups[0].range, [.5, 2.7]);
  assert.deepEqual(groups[0].size, [2.2, .8]);
  assert.deepEqual(groups[0].anchor, [.16, .4]);
  assert.equal(JSON.stringify(input), before);
});

test('periodic alignment works along the row and across a swapped chart axis', () => {
  let group = alignedFeatureGroups([feature('after', .05), feature('before', .96)], { periods: [1,0] })[0];
  assert.deepEqual(group.members, ['before','after']);
  assert(Math.abs(group.anchor[0] - .005) < 1e-8);
  group = alignedFeatureGroups([
    feature('before', .995, .4), feature('after', .001, .66)
  ], { axis: 0, chartAxis: 1, periods: [1,0] })[0];
  assert.deepEqual(group.members, ['before','after']);
  assert(Math.abs(group.anchor[0] - .998) < 1e-8);
  assert.equal(group.anchor[1], .53);
  assert.throws(() => alignedFeatureGroups([feature('same',.4),feature('same',.5)]), /unique/);
});

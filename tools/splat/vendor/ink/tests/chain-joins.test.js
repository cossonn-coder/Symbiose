const test = require('node:test'), assert = require('node:assert/strict');
const { chainJoins } = require('..').load().KIT.procedural;
const chain = (start, end) => ({ start: [start, 0, 0], end: [end, 0, 0], length: Math.abs(end - start) });

test('a chain join maps stations through each possible endpoint orientation', () => {
  for (const firstEnd of [0, 1]) for (const secondEnd of [0, 1]) {
    const a = firstEnd ? chain(-3, 0) : chain(0, -3);
    const b = secondEnd ? chain(5, 0) : chain(0, 5);
    const plan = chainJoins.plan(a, b, { tolerance: 0 });
    assert.equal(plan.firstEnd, firstEnd);
    assert.equal(plan.secondEnd, secondEnd);
    assert.equal(plan.reverseFirst, firstEnd === 0);
    assert.equal(plan.reverseSecond, secondEnd === 1);
    assert.equal(plan.mapFirst(firstEnd), 3 / 8);
    assert.equal(plan.mapSecond(secondEnd), 3 / 8);
    assert.equal(plan.mapFirst(1 - firstEnd), 0);
    assert.equal(plan.mapSecond(1 - secondEnd), 1);
    assert.equal(plan.mapFirst(.5), 3 / 16);
    assert.equal(plan.mapSecond(.5), 11 / 16);
  }
});

test('explicit chain endpoints take precedence and a distant join returns null', () => {
  const a = chain(0, 2), b = chain(.1, 2.2);
  assert.equal(chainJoins.plan(a, b).firstEnd, 0);
  assert.equal(chainJoins.plan(a, b, { firstEnd: 1, secondEnd: 1 }).firstEnd, 1);
  assert.equal(chainJoins.plan(a, b, { firstEnd: 0, secondEnd: 1 }), null);
  assert.equal(chainJoins.plan(a, b, { tolerance: .01 }), null);
  assert.throws(() => chainJoins.plan(a, chain(2, 2)), /positive lengths/);
  assert.throws(() => chainJoins.plan(a, b, { firstEnd: 2 }), /endpoint indices/);
});

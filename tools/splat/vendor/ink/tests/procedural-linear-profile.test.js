const test = require('node:test');
const assert = require('node:assert/strict');
const {linearProfile} = require('..').load().KIT.procedural;

test('a linear profile preserves exact knots and clamps beyond the domain', () => {
  const raw=[[-2,1],[0,4],[.5,2],[5,6]];
  const p=linearProfile.compile(raw);
  assert.equal(p.slopeBound,4);
  assert.equal(p.at(-3),1);
  assert.equal(p.at(-1),2.5);
  assert.equal(p.at(0),4);
  assert.equal(p.at(.25),3);
  assert.equal(p.at(.5),2);
  assert.equal(p.at(10),6);
  raw[1][1]=100;
  assert.equal(p.at(0),4);
  assert(Object.isFrozen(p.knots)&&p.knots.every(Object.isFrozen));
});

test('invalid stations and nonfinite segments are rejected before querying', () => {
  assert.throws(()=>linearProfile.compile([[1,0],[1,2]]),/increase/);
  assert.throws(()=>linearProfile.compile([[2,0],[1,2]]),/increase/);
  assert.throws(()=>linearProfile.compile([[1,0],[2,NaN]]),/finite/);
  assert.throws(()=>linearProfile.compile([[-1e308,0],[1e308,1]]),/finite/);
  assert.throws(()=>linearProfile.compile([[0,0],[1,1]]).at(Infinity),/finite/);
});

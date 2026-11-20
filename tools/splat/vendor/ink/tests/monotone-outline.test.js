const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load(), P = KIT.procedural;

const outline = [[-2,0],[2,0],[2,1],[.9,1],[.9,2],[3,2],[3,3],[2,3],[2,4],
  [-2,4],[-2,3],[-3,3],[-3,2],[-.9,2],[-.9,1],[-2,1]];

test('horizontal profile fitting fills a protected band and keeps distinct ledges on either side', () => {
  const required = [[-1.25,1.4],[1.25,1.4],[1.25,1.75],[-1.25,1.75]];
  const result = P.geometry.fitMonotoneOutline({outline,required});
  const distance = P.geometry.profileDistance(result);
  assert(distance(1.18,1.55)<0);
  assert(distance(1.18,1.33)>0);
  assert(distance(1.18,1.88)>0);
  assert(distance(2.75,2.5)<0);
  assert(distance(2.75,3.25)>0);
  assert.deepEqual(result,P.geometry.fitMonotoneOutline({outline:outline.slice().reverse(),required}));
  assert.throws(()=>P.geometry.fitMonotoneOutline({outline:[[0,0],[2,2],[2,0],[0,2]]}),/monotone/);
});

test('fitting a sloped protector inserts the exact crossover with the authored side', () => {
  const original=[[-1,0],[1,0],[1,3],[-1,3]], required=[[-.8,1],[.6,1],[1.4,2],[-.8,2]];
  const result=P.geometry.fitMonotoneOutline({outline:original,required});
  assert(result.some(p=>Math.abs(p[0]-1)<1e-9&&Math.abs(p[1]-1.5)<1e-9));
  const distance=P.geometry.profileDistance(result);
  assert(distance(1.1,1.55)>0);
  assert(distance(1.1,1.85)<0);
});

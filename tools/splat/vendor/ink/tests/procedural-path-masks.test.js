const test = require('node:test'), assert = require('node:assert/strict');
const { surfaceCells } = require('..').load().KIT.procedural;

test('path clearance polygons and field agree at caps, bends, and split cells', () => {
  const mask = surfaceCells.pathMask([
    { points: [[-1, 0], [0, 0], [1, 0], [1, 1]], radius: .2 },
    { points: [[-1, 1]], radius: .14 }
  ]);
  assert.equal(mask.holes.length, 3);
  assert(mask.distance(.99, .04) < 0);
  assert(mask.distance(-1.17, 0) < 0);
  assert(mask.distance(-1, 1) < 0);
  assert(mask.distance(-1.23, 0) > 0);
  const result = surfaceCells.clip([
    { key: 'crossed', inset: { min: [-.9, -.4], max: [.8, .4] } },
    { key: 'away', inset: { min: [-.5, .5], max: [.4, .9] } }
  ], { holes: mask.holes });
  assert.equal(result.cells[0].key, 'crossed');
  const area=polygon=>polygon.reduce((sum,p,i)=>{
    const q=polygon[(i+1)%polygon.length];
    return sum+(p[0]*q[1]-p[1]*q[0])/2;
  },0);
  assert(Math.abs(result.cells[0].fragments.reduce((sum,p)=>sum+area(p),0)-.68)<1e-8);
  for (const polygon of result.cells[0].fragments) for (const p of polygon)
    assert(mask.distance(...p) >= -1e-8);
  assert.equal(result.cells[1].fragments.length, 1);
});

test('a reversal does not remove a path end and empty masks leave fields unchanged', () => {
  const mask = surfaceCells.pathMask([{ points: [[0, 0], [2, 0], [1, 0]], radius: .1 }]);
  assert(mask.distance(2.05, 0) < 0);
  assert(mask.distance(2.2, 0) > 0);
  assert.equal(surfaceCells.pathMask([]).distance(0, 0), Infinity);
  assert.throws(() => surfaceCells.pathMask([{ points: [[0, 0]], radius: 0 }]), /radii/);
});

test('immutable mask strokes reuse compilation while live inputs reflect edits', () => {
  const {procedural:P}=require('..').load().KIT;
  const points=P.data.freeze({id:'retained',points:[[0,0],[2,0]],width:1});
  assert.equal(P.masks.stroke(points),P.masks.stroke(points));
  const mutable={id:'mutable',points:[[0,0],[2,0]],width:1};
  const old=P.masks.stroke(mutable);
  mutable.points[1][0]=4;
  const next=P.masks.stroke(mutable);
  assert.notEqual(old,next);
  assert(old.distance([3,0])>0);
  assert(next.distance([3,0])<0);
});

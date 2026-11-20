const test = require('node:test');
const assert = require('node:assert/strict');
const { intersectConvexPlans } = require('..').load().KIT.procedural.geometry;

const box = (x0,z0,x1,z1) => [[x0,z0],[x1,z0],[x1,z1],[x0,z1]];
const area = points => points.reduce((sum,p,i) => {
  const q=points[(i+1)%points.length];
  return sum+(p[0]*q[1]-q[0]*p[1])/2;
},0);

test('overlap clips both windings and keeps independent counterclockwise XZ points',()=>{
  const a=box(-1,-1,2,1), b=box(0,-2,3,.5).reverse(), original=JSON.stringify([a,b]);
  const fit=intersectConvexPlans(a,b);
  assert.equal(fit.length,4);
  assert.equal(area(fit),3);
  assert(fit.every(([x,z])=>x>=0&&x<=2&&z>=-1&&z<=.5));
  fit[0][0]=999;
  assert.equal(JSON.stringify([a,b]),original);
});

test('convex overlap handles boundary points, containment and tangencies',()=>{
  const window=box(0,0,2,2);
  assert.deepEqual(intersectConvexPlans(box(2,0,3,1),window),[]);
  assert.deepEqual(intersectConvexPlans(box(2,2,3,3),window),[]);
  assert.deepEqual(intersectConvexPlans(box(3,3,4,4),window),[]);
  assert.equal(area(intersectConvexPlans(window,box(-1,-1,5,5))),4);
  const triangle=intersectConvexPlans(window,[[1,1],[3,1],[1,3],[1,3],[1,1]]);
  assert.equal(area(triangle),1);
});

test('invalid outlines fail before producing an ambiguous overlap ring',()=>{
  assert.throws(()=>intersectConvexPlans(box(0,0,1,1),[[0,0],[2,0],[.5,.5],[2,2],[0,2]]),/convex/);
  assert.throws(()=>intersectConvexPlans([[0,0],[1,0],[2,0]],box(0,0,1,1)),/area/);
  assert.throws(()=>intersectConvexPlans(box(0,0,1,1),[[0,0],[2,0],[0,NaN]]),/finite/);
});

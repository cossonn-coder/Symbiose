const test = require('node:test'), assert = require('node:assert/strict');
const { heightSurface } = require('..').load().KIT.procedural;
const near = (a,b) => assert(Math.abs(a-b)<1e-6, `${a} != ${b}`);
const bounds = { min: [-6,-1,-6], max: [6,4,6] };

test('independent footprint sites keep their keys and plan offsets across local relief and masks', () => {
  const sites = [
    {key:'left',offset:[-.5,0]}, {key:'right',offset:[.5,0]},
    {key:'masked',offset:[0,1]}, {key:'ledgeless',offset:[0,-1]},
  ], height = (x,z) => z > 0 ? null : z < 0 ? -4 : x - 2;
  assert.deepEqual(heightSurface.seatSites([2,0,0], sites, height, {offset:.125,maxDelta:1}),[
    {key:'left',point:[1.5,-.375,0]}, {key:'right',point:[2.5,.625,0]},
  ]);
  assert.deepEqual(heightSurface.seatSites([2,0,0], sites, (x,z)=>z < 0 ? null : height(x,z)),[
    {key:'left',point:[1.5,-.5,0]}, {key:'right',point:[2.5,.5,0]},
  ]);
  assert.throws(()=>heightSurface.seatSites([2,0,0], [sites[0],sites[0]], height),/unique/);
  assert.throws(()=>heightSurface.seatSites([2,0,0], sites, ()=>NaN),/finite/);
});

test('vertical height rays evaluate only one height and honor their physical extent',()=>{
  let queries=0;
  const surface={ bounds, height(){ queries++;return 1.5; }, normal:()=>[0,1,0], inside:x=>x<2 };
  assert.deepEqual(heightSurface.raycast(surface,[1,6,2],[0,-12,0]),
    { p:[1,1.5,2], n:[0,1,0], distance:4.5 });
  assert.equal(queries,1);
  assert.equal(heightSurface.raycast(surface,[1,6,2],[0,-12,0],{maxDistance:4}),null);
  assert.equal(heightSurface.raycast(surface,[3,6,2],[0,-12,0]),null);
});

test('certified height rays preserve the first hit with fewer height probes',()=>{
  const counts=[];
  const results=[undefined,.25].map(slopeBound=>{
    let calls=0;
    const hit=heightSurface.raycast({ bounds,height(x){ calls++;return .25*x; } },
      [-3,5,0],[1,-2,0],{slopeBound});
    counts.push(calls);
    return hit;
  });
  near(results[0].distance,results[1].distance);
  near(results[1].p[0],-4/9);
  assert(counts[1] < counts[0]/2);
  const level={bounds:{min:[-6,0,-6],max:[6,0,6]},height:()=>0};
  const hit=heightSurface.raycast(level,[3,4,3],[-1,-2,-1],{slopeBound:0});
  near(hit.distance,Math.sqrt(24));
  assert.deepEqual(hit.p,[1,0,1]);
});

test('an oblique search keeps testing after a crossing outside the accepted surface',()=>{
  const peak={bounds,height:x=>Math.max(0,1-Math.abs(x-1)),inside:x=>x>1};
  const hit=heightSurface.raycast(peak,[-2,.45,0],[1,0,0],{slopeBound:1});
  near(hit.p[0],1.55);
  near(hit.p[1],.45);
  assert.equal(heightSurface.raycast(peak,[-2,.45,0],[1,0,0],{slopeBound:1,maxDistance:3}),null);
});

test('height range samples the occupied plan and its rim with a fixed work budget', () => {
  const triangle = [[0,0], [2,0], [0,2]];
  const range = heightSurface.rangeOverPlan((x,z) => {
    assert(x >= 0 && z >= 0 && x + z <= 2 + 1e-10);
    return x - 2*z;
  }, triangle, { spacing:.24, budget:190 });
  assert.equal(range.min,-4);
  assert.equal(range.max,2);
  assert(range.samples > 30 && range.samples < 190);
  assert.throws(() => heightSurface.rangeOverPlan(() => 0, triangle, {spacing:.01,budget:20}), /budget/);
  assert.throws(() => heightSurface.rangeOverPlan(() => NaN, triangle), /finite/);
});

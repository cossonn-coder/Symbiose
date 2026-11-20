const test=require('node:test'),assert=require('node:assert/strict');
const {edgeClearance:{strip,footprint,ranges,clipFieldPath}}=require('..').load().KIT.procedural;

test('ordered retained spans handle overlapping angled access, reversed edges and complete removal',()=>{
  const a=[-4,2,0],b=[4,2,0];
  const first=strip([-1,2,-3],[-1,2,3],{halfWidth:1});
  const second=strip([.5,1,-2],[.5,3,2],{halfWidth:1});
  assert.deepEqual(ranges(a,b,[second,first]),{kept:[[0,.25],[.6875,1]],removed:[[.25,.6875]]});
  assert.deepEqual(ranges(b,a,[first,second]),{kept:[[0,.3125],[.75,1]],removed:[[.3125,.75]]});
  const skew=strip([-2,2,-2],[2,2,2],{halfWidth:Math.SQRT1_2});
  for(const x of ranges(a,b,[skew]).removed[0].map((t,i)=>t-[.375,.625][i]))assert(Math.abs(x)<1e-10);
  assert.deepEqual(ranges(a,b,[strip([0,2,-1],[0,2,1],{halfWidth:4})]),{kept:[],removed:[[0,1]]});
});

test('vertical bands protect underpasses, and end extensions and tangent contacts are bounded',()=>{
  const thin=strip([0,1,-2],[0,1,0],{halfWidth:1,extension:.1,above:.2,below:.1});
  const untouched={kept:[[0,1]],removed:[]};
  assert.deepEqual(ranges([-2,2,0],[2,2,0],[thin]),untouched);
  assert.deepEqual(ranges([-2,1,.11],[2,1,.11],[thin]),untouched);
  assert.deepEqual(ranges([-2,1,0],[-1,1,0],[thin]),untouched);
  assert.deepEqual(ranges([-2,1,.09],[2,1,.09],[thin]),{kept:[[0,.25],[.75,1]],removed:[[.25,.75]]});
  assert.throws(()=>strip([0,0,0],[0,1,0],{halfWidth:1}),/horizontal span/);
});

test('convex footprints trim edges at any height and compose with sloped bands',()=>{
  const mask=footprint([[0,-1],[2,-1],[0,1]].reverse()),
    a=[-2,3,0],b=[2,5,0],local=strip([-.5,3.75,-1],[-.5,3.75,1],{halfWidth:.25});
  assert.deepEqual(ranges(a,b,[mask]),{kept:[[0,.5],[.75,1]],removed:[[.5,.75]]});
  assert.deepEqual(ranges(b,a,[mask]),{kept:[[0,.25],[.5,1]],removed:[[.25,.5]]});
  assert.deepEqual(ranges(a,b,[mask,local]).removed,[[.3125,.4375],[.5,.75]]);
  const padded=footprint([[0,-1],[1,-1],[1,1],[0,1]],{padding:.25});
  assert.deepEqual(ranges(a,b,[padded]).removed,[[.4375,.8125]]);
  assert.throws(()=>footprint([[0,-1],[1,-1],[1,1]],{padding:-1}),/padding/);
});

test('bounded signed fields split a bent path and preserve unblocked vertices',()=>{
  function box(min,max){
    return {bounds:{min,max},distance:p=>Math.max(...p.flatMap((v,i)=>[min[i]-v,v-max[i]]))};
  }
  const path=[[-3,0,0],[-1,0,0],[1,0,0],[3,0,2]];
  const a=box([-.4,-.5,-.5],[.25,.5,.5]),b=box([.2,-.5,-.5],[.5,.5,.5]);
  const split=clipFieldPath(path,[b,a],{padding:.1});
  assert.equal(split.length,2);
  assert.deepEqual(split[0].slice(0,-1),path.slice(0,2));
  assert.deepEqual(split[1].slice(1),path.slice(2));
  assert(Math.abs(split[0].at(-1)[0]+.5)<.002);
  assert(Math.abs(split[1][0][0]-.6)<.002);
  const reversed=clipFieldPath(path.slice().reverse(),[a,b],{padding:.1});
  assert(Math.abs(reversed[0].at(-1)[0]-.6)<.002);
  assert(Math.abs(reversed[1][0][0]+.5)<.002);
  assert.deepEqual(clipFieldPath(path,[box([-4,-1,-1],[4,1,3])]),[]);
  assert.equal(clipFieldPath(path,[box([-4,1,-1],[4,2,3])]),null);
  const thin=clipFieldPath([[-2,0,0],[2,0,0]],[box([.217,-.2,-.2],[.221,.2,.2])]);
  assert(thin[0].at(-1)[0]<.221&&thin[1][0][0]>.217);
});

const test=require('node:test'),assert=require('node:assert/strict');
const {supportSweep,traversal}=require('..').load().KIT.procedural;
const box=(lo,hi,height=2)=>({height,footprint:[[lo,-1],[hi,-1],[hi,1],[lo,1]]});
const left=box(-1,-.025),right=box(.025,1);

test('a level sweep detects thin gaps, joins different carriers, and retains bounded rises',()=>{
  const from=[-.04,2,0],to=[.04,2,0];
  assert.deepEqual(supportSweep.segment(from,to,[left,right]),{start:true,end:true,covered:false});
  assert.deepEqual(supportSweep.segment(from,to,[left,right,box(-.025,.025)]),{start:true,end:true,covered:true});
  assert.deepEqual(supportSweep.segment(from,to,[left,right,box(-.025,.025,2.2)]),{start:true,end:true,covered:false});
  assert.deepEqual(supportSweep.segment(from,[.04,2.2,0],[left,box(-.025,1,2.2)]),
    {start:true,end:true,covered:true});
});

test('a hole interrupts the interior of a rotated patch but preserves its boundary',()=>{
  const orient=([x,y])=>[x-y,x+y], floor=box(-1,1), cut=box(-.005,.005);
  const patch={height:2,footprint:floor.footprint.map(orient),
    holes:[cut.footprint.map(([x,z])=>orient([x,z*.4])).reverse()]};
  assert.deepEqual(supportSweep.segment([-.04,2,-.04],[.04,2,.04],[patch]),
    {start:true,end:true,covered:false});
  assert.deepEqual(supportSweep.segment([-.44,2,.36],[-.36,2,.44],[patch]),
    {start:true,end:true,covered:true});
  assert.deepEqual(supportSweep.segment([-.04,2,-.04],[0,2,0],[patch]),
    {start:true,end:false,covered:false});
});

test('traversal validates transitions for straight movement and retries sliding',()=>{
  const supports=()=>[{y:2,normal:[0,1,0],id:'floor'}];
  const body=traversal.create({supports,clearance:()=>Infinity,transition:(a,b,s)=>{
    assert.equal(s.id,'floor');
    return a[0]===b[0];
  }});
  const next=body.move([0,2,0],[.04,.04],{trace:true});
  assert(next.blocked);
  assert.deepEqual(next.foot,[0,2,.04]);
  assert.equal(next.contacts.length,1);
  assert.equal(body.stand([1,2,0]).support,'floor');
  assert.throws(()=>traversal.create({supports,clearance:()=>Infinity,transition:true}),/Invalid traversal/);
});

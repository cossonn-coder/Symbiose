const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const kit = require('..').load();
const {KIT:{world:W,procedural:P}}=kit;
const demo = require('../examples/world-construction-bridge.json');
const {points,constraints}=demo.systems.bridge.config;
const value=(run,field,at,args)=>run.query().probe('bridge/'+field,at,args).value;
const packed=value=>JSON.parse(JSON.stringify(value));
const close=(a,b)=>Math.abs(a-b)<1e-8;

test('opening dimensions move free sockets to satisfy hard bounds and retain unused preferences',()=>{
  const solver=P.construct.constraints.compile({
    from:{position:[0,0,0]}, to:{position:[.8,.5,2],sockets:{lintel:[0,-.2,0]}}
  },[
    {id:'origin',type:'pin',point:'from',position:[0,0,0]},
    {id:'access',type:'opening',width:{axis:'x',a:'from',b:'to',min:1.4},height:{a:'from',b:'to/lintel',min:2}}
  ]);
  const result=solver.solve();
  assert.equal(result.status,'ok');
  assert.deepEqual(result.points.to,[1.4,2.2,2]);
  assert.deepEqual(result.sockets['to/lintel'],[1.4,2,2]);
  assert.throws(()=>solver.solve({typo:[0,0,0]}),/pin constraint IDs/);
});

test('the overlength witness is a closed contradictory cycle of the specific authored constraints',()=>{
  const pins={'east-anchor':[6,1.43,0]}, solver=P.construct.constraints.compile(points,constraints);
  const result=solver.solve(pins);
  assert.equal(result.status,'conflict');
  const [conflict]=result.conflicts, {cycle}=conflict;
  assert.equal(conflict.axis,'x');
  assert.deepEqual(conflict.constraints,['east-anchor','east-span-limit','seat-alignment','west-anchor','west-span-limit']);
  assert(close(conflict.totalBound,-.6));
  assert(close(cycle.reduce((sum,row)=>sum+row.maxDifference,0),conflict.totalBound));
  for(const [i,row] of cycle.entries())assert.equal(row.to,cycle[(i+1)%cycle.length].from);
  for(const id of conflict.constraints){
    const reduced=P.construct.constraints.compile(points,constraints.filter(row=>row.id!==id));
    assert.equal(reduced.solve(id==='east-anchor'?{}:pins).status,'ok');
  }
});

test('a resize publishes fitted bodies, level sockets and support from the new revision',()=>{
  const run=W.runtime.create(demo);
  const original=value(run,'layout');
  assert.equal(value(run,'support',[4.9,1.45,0],{low:1.25,high:1.6}).length,0);
  const proposal=value(run,'fit',{},{pins:{'east-anchor':[5.1,1.43,0]}});
  assert.equal(value(run,'layout'),original);
  assert.equal(proposal.status,'ok');
  run.advance(2);
  const layout=value(run,'layout');
  assert.deepEqual(layout.sockets['left-joint/seat'],layout.sockets['right-joint/seat']);
  assert.equal(layout.sockets['east/seat'][1],layout.sockets['west/seat'][1]);
  assert.deepEqual(layout.members.slice(0,2).map(row=>row.length),[4.1,4.4]);
  assert.equal(layout.openings[0].clear,true);
  assert(value(run,'support',[4.9,1.45,0],{low:1.25,high:1.6}).some(hit=>hit.id==='east-deck'&&close(hit.y,1.43)));
  assert(run.dependencies().changes.some(change=>change.field==='bridge/support'));
  assert.deepEqual(run.query().target({entity:'bridge.east-deck'}).point,layout.bodies['east-deck'].position);
});

test('conflicting and obstructed fits leave the last accepted layout intact through replay',()=>{
  const run=W.runtime.create(demo);
  run.advance(2);
  const layout=value(run,'layout');
  const fork=run.fork();
  run.advance(4);
  const raised=value(run,'fit');
  assert.equal(raised.status,'conflict');
  assert.deepEqual(raised.conflicts[0].constraints,['deck-level','east-anchor','west-anchor']);
  assert.equal(raised.conflicts[0].axis,'y');
  assert.equal(value(run,'layout'),layout);
  run.advance(6);
  assert.equal(value(run,'fit').conflicts[0].axis,'x');
  run.advance(8);
  const collision=value(run,'fit');
  assert.equal(collision.status,'blocked');
  assert.equal(collision.issues[0].constraint,'boat-clearance');
  assert.deepEqual(collision.issues[0].blockers,['canal-bollard']);
  assert.equal(value(run,'layout'),layout);
  assert.equal(run.dependencies().changes.length,0);
  fork.advance(8);
  assert.deepEqual(fork.checkpoint(),run.checkpoint());
  const restored=W.runtime.create(demo,{checkpoint:packed(run.checkpoint())});
  assert.deepEqual(value(restored,'fit'),collision);
  assert.deepEqual(W.runtime.replay(packed(run.recording())).checkpoint(),run.checkpoint());
});

test('the CLI previews conflicts and one render can include construction and an existing mechanics scene',()=>{
  const result=spawnSync(process.execPath,['cli/ink-studio.js','probe','examples/world-construction-bridge.json',
    '--field','bridge/fit','--args',JSON.stringify({pins:{'east-anchor':[6,1.43,0]}}),'--json'],
    {cwd:path.join(__dirname,'..'),encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);
  assert.equal(JSON.parse(result.stdout).value.status,'conflict');
  const run=W.runtime.create({...demo,systems:{...demo.systems,rig:{kind:'mechanics',config:{bodies:{
    marker:{position:[0,.35,1.84],half:[.2,.24,.14],fixed:true,surfaceState:{}}
  }}}},visual:{...demo.visual,fields:{bodies:['bridge/bodies','rig/bodies']}}});
  const world=W.visual(kit,run.view(),run.query()), query=W.query.fromScene(world);
  assert(query.select({entity:'bridge.west-deck'}).length);
  assert(query.select({entity:'marker',surface:'marker/+z'}).length);
});

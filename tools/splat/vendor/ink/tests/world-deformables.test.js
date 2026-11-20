const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT:{world:W}}=require('..').load();
const yard=require('../examples/world-deformable-yard.json');

const packed=value=>JSON.parse(JSON.stringify(value));
const close=(a,b,epsilon=1e-6)=>assert.ok(Math.abs(a-b)<=epsilon,`${a} differs from ${b}`);
const motion=(run,shape)=>run.query().probe('fabric/motion',{}, {shape}).value;
const surfaces=run=>run.query().probe('fabric/surfaces').value;
const create=(shapes,config={},options={})=>W.runtime.create({dt:.05,...options,systems:{
  ...options.systems,fabric:{kind:'deformables',config:{ground:-2,shapes,...config}}
}});

test('swept mechanics catches a falling crate and feeds sustained reactions to the net', () => {
  const run=W.runtime.create(yard);
  let landing, firstReaction;
  run.advance(100,{onTick(){
    const hit=run.query().probe('rig/impacts').value.impacts.find(hit=>hit.surface?.shape==='catch-net');
    if(hit&&!landing)landing=hit;
    const reaction=run.query().probe('rig/deformable-loads').value.find(row=>row.shape==='catch-net');
    if(reaction&&!firstReaction)firstReaction=reaction;
  }});
  assert.equal(landing.a,'crate');
  assert.equal(landing.surface.system,'fabric');
  assert.ok(firstReaction.impulse[1]<-5);
  const crate=run.query().probe('rig/bodies').value.crate;
  const seat=run.query().probe('fabric/support',crate.position).value.find(row=>row.id==='catch-net');
  assert.ok(crate.position[1]>1.3&&Math.abs(crate.velocity[1])<.35);
  close(crate.position[1]-crate.half[1],seat.y,.035);
  assert.ok(motion(run,'catch-net').load.impulse[1]<0);
  assert.ok(run.view().history.some(event=>event.kind==='deformable-contact'&&event.contact==='crate'));
});

test('a tarp carries rain as weight and a cut spills water and removes support', () => {
  const tarp={kind:'cloth',at:[-1,1,-1],u:[2,0,0],v:[0,0,2],nu:3,nv:3,mass:2,stretch:.001,shear:.001,
    water:{rain:.035,capacity:.08,density:160},
    attachments:{a:{node:0,point:[-1,1,-1]},b:{node:2,point:[1,1,-1]},
      c:{node:6,point:[-1,1,1]},d:{node:8,point:[1,1,1]}}};
  const dry={...tarp}; delete dry.water;
  const run=create({tarp},{damping:4}), control=create({tarp:dry},{damping:4});
  run.advance(22); control.advance(22);
  assert.ok(motion(run,'tarp').positions[13]<motion(control,'tarp').positions[13]-.02);
  const report=()=>run.query().probe('fabric/water').value.tarp;
  assert.ok(report().retained>.05);
  const point=surfaces(run).tarp.points[4];
  const seat=()=>run.query().probe('fabric/support',point).value.find(hit=>hit.id==='tarp');
  assert.ok(seat());
  const fork=run.fork();
  run.schedule([{tick:23,action:'fabric/cut',args:{shape:'tarp',point,radius:.15}}]);
  run.step();
  assert.ok(run.events.some(event=>event.kind==='deformable-tear'&&event.reason==='cut'));
  assert.ok(report().runoff.some(row=>row.kind==='tear'&&row.volume>0));
  assert.equal(seat(),undefined);
  close(report().error,0);
  assert.ok(surfaces(fork).tarp.faces.every(Boolean));
});

test('rope attachments follow rotated sockets, emit events and tear under tension', () => {
  const rope={kind:'rope',points:[[0,1,0],[1,1,0],[2,1,0]],tear:1.15,bend:.001,
    attachments:{left:{node:0,point:[0,1,0]},right:{node:2,entity:'winch',socket:'hook',offset:[0,0,.2]}}};
  const run=create({rope},{gravity:[0,0,0]},{entities:{winch:{position:[2,1,0],sockets:{hook:[0,0,0]}}},systems:{
    rig:{kind:'mechanics',config:{gravity:[0,0,0],bodies:{winch:{position:[2,1,0],half:[.2,.2,.2],fixed:true,turn:Math.PI/2}}}}
  }});
  run.step();
  const last=surfaces(run).rope.points[2];
  close(last[0],2.2);close(last[2],0);
  run.schedule([
    {tick:2,action:'fabric/detach',args:{shape:'rope',attachment:'right'}},
    {tick:2,action:'fabric/attach',args:{shape:'rope',attachment:'right',node:2,point:[4,1,0]}},
    {tick:3,action:'fabric/load',args:{shape:'rope',node:1,impulse:[0,-.2,0]}}
  ]);
  run.step();
  assert.ok(run.events.some(event=>event.kind==='deformable-attach'&&event.attachment==='right'));
  assert.ok(run.events.some(event=>event.kind==='deformable-detach'&&event.attachment==='right'));
  assert.ok(run.events.some(event=>event.kind==='deformable-tear'&&event.ratio>1.15));
  assert.ok(surfaces(run).rope.strands.length<2);
  const saved=packed(run.checkpoint());
  run.step();
  assert.deepEqual(packed(run.checkpoint()),packed(W.runtime.replay(packed(run.recording())).checkpoint()));
  const restored=W.runtime.create(saved.world,{checkpoint:saved});
  restored.step();
  assert.deepEqual(packed(restored.checkpoint()),packed(run.checkpoint()));
});

test('agent footfalls load the bridge and sag it relative to the same unloaded crossing', () => {
  const controlSource=packed(yard);
  controlSource.connections=controlSource.connections.filter(edge=>edge.to!=='fabric/traffic');
  const run=W.runtime.create(yard), control=W.runtime.create(controlSource);
  let loads=0, sag=0;
  for(let i=0;i<94;i++){
    run.step();control.step();
    const bridge=motion(run,'bridge');
    loads+=bridge.load.traffic;
    sag=Math.max(sag,motion(control,'bridge').positions[82]-bridge.positions[82]);
  }
  assert.ok(run.query().probe('traffic/agents').value.porter.position[2]<-1.9);
  assert.ok(loads>=12&&sag>.09);
});

test('point sweeps respect a thin world collider and reject invalid bindings', () => {
  const line={kind:'rope',points:[[-1,1,-.08],[-1,1,.08]],radius:.02};
  const run=create({line},{gravity:[0,0,0],clearance:'rig/clearance'},{systems:{rig:{kind:'mechanics',config:{bodies:{
    wall:{fixed:true,position:[0,1,0],half:[.015,.6,.6]}
  }}}}});
  run.schedule([0,1].map(node=>({tick:1,action:'fabric/load',args:{shape:'line',node,impulse:[25,0,0]}})));
  run.step();
  assert.ok(surfaces(run).line.points.every(point=>point[0]<0));
  assert.ok(run.events.some(event=>event.kind==='deformable-contact'&&event.contact==='wall'));
  assert.throws(()=>create({line},{rain:'world/position'}),/Invalid deformable rain field/);
  assert.throws(()=>create({line:{...line,attachments:{pin:{node:2,point:[0,0,0]}}}}),/Invalid deformable attachment/);
});

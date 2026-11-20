const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: { world: W, procedural: P } } = require('..').load();
const watershed = require('../examples/world-watershed.json');
const crossing = require('../examples/world-crossing.json');

test('a fork can lower a live spillway without resetting water, and its outlet floods', () => {
  const baseline=W.runtime.create(watershed);
  baseline.advance(30);
  const opened=baseline.fork(), closed=baseline.fork();
  opened.schedule([{tick:31,action:'river/bed',args:{bounds:{min:[-1.55,-.75],max:[-.55,.75]},height:-.25}}]);
  opened.advance(120);
  closed.advance(120);
  assert.equal(closed.query().probe('water',{entity:'footbridge'}).status,'dry');
  assert(opened.query().probe('water',{entity:'footbridge'}).value.depth>.15);
  const {volume,initial,error}=opened.query().probe('mass').value;
  assert(Math.abs(volume-initial)<1e-10 && Math.abs(error)<1e-10);
  assert.equal(opened.history[0].kind,'bed-edit');
  assert(W.runtime.diff(closed.checkpoint(),opened.checkpoint()).edits.some(edit=>edit.path.includes('depth')));
  assert.equal(W.runtime.replay(JSON.parse(JSON.stringify(opened.recording()))).view().tick,120);
});

test('face gates and paired transfer preserve balance and empty pumps cannot create water', () => {
  const solver=P.motion.shallowWater({width:4,height:3,cell:1,initial:x=>x<2?1:0});
  const blocked=solver.step(1,{opening:(x,z,axis)=>axis===0&&x===2?0:1});
  assert.equal(blocked.sample(2.5,1.5).depth,0);
  const step=solver.step(.3,{opening:(x,z,axis)=>axis===0&&x===2?0:1,transfers:[{from:1,to:2,rate:2}]});
  assert(step.sample(2.5,.5).depth>0);
  assert(Math.abs(step.mass.error)<1e-10);
  assert(step.mass.transferred>0);
  const saved=solver.checkpoint();
  const copy=P.motion.shallowWater({width:4,height:3,cell:1});
  copy.restore(saved);
  assert.deepEqual(copy.snapshot().mass,step.mass);
  const empty=P.motion.shallowWater({width:2,height:1,cell:1});
  assert.equal(empty.step(.2,{transfers:[{from:0,to:1,rate:100}]}).mass.volume,0);
});

test('fracture changes shared routes, transports material and leaves colliding rubble', () => {
  const run=W.runtime.create(crossing);
  run.advance(40);
  const before=run.query().probe('machine/clearance',[0,.74,0]);
  assert(before.value<0);
  const from=[-3,.12,0], to=[3.1,.12,0];
  const detour=run.query().trace('routes/route',from,{to,radius:.24}).value;
  assert.equal(detour.status,'ok');
  assert(detour.points.some(point=>Math.abs(point[2])>1.3));
  run.advance(70);
  assert(run.query().probe('machine/clearance',[0,.74,0]).value>0);
  assert.equal(run.query().probe('position',{entity:'wall'}).status,'missing');
  const bodies=run.query().probe('machine/bodies').value;
  assert.equal(bodies['wall.0'].material,'granite');
  assert(bodies['wall.0'].position[0]>0);
  const shortcut=run.query().trace('routes/route',from,{to,radius:.24}).value;
  assert.equal(shortcut.status,'ok');
  assert(shortcut.points.every(point=>Math.abs(point[2])<.4));
});

test('moving assemblies carry sockets, report a stalled drive, and detach a stage', () => {
  const spec={dt:.05,entities:{ferry:{position:[0,2,0],sockets:{deck:[0,.5,0]}}},systems:{
    shop:{kind:'mechanics',config:{gravity:[0,0,0],bodies:{
      root:{entity:'ferry',position:[0,2,0],half:[.4,.4,.4]},
      stage:{half:[.12,.16,.2]},
      rotor:{half:[.1,.1,.1]}
    },joints:{
      hold:{parent:'root',child:'stage',kind:'fixed',offset:[0,-.6,0]},
      shaft:{parent:'root',child:'rotor',kind:'shaft',offset:[0,.8,0],axis:[0,1,0],speed:4,capacity:1,load:2}
    },forces:{lift:{kind:'thrust',body:'stage',axis:[0,1,0],magnitude:8,input:1}}}}
  }};
  const run=W.runtime.create(spec);
  run.advance(10);
  const from=run.query().probe('position',{entity:'ferry',socket:'deck'}).value;
  assert(from[1]>2.5);
  assert.equal(run.query().probe('joints').value.shaft.stalled,true);
  run.schedule([{tick:11,action:'shop/detach',args:{joint:'hold'}}]);
  run.advance(19);
  const {root,stage}=run.query().probe('bodies').value;
  assert(run.query().probe('joints').value.hold.active===false);
  assert.notEqual(stage.velocity[1],root.velocity[1]);
  assert(run.history.some(event=>event.kind==='detached'));
});

test('habitat reasons, creature rerouting, limb placement and optional wear share world state', () => {
  const run=W.runtime.create(crossing);
  const habitat=run.query().probe('habitat/suitability',[3,.12,0],{species:'woolly'});
  assert.equal(habitat.value.suitable,true);
  assert.equal(habitat.value.reasons[1].value.id,'feeding-stone');
  run.advance(70);
  assert(run.query().probe('agents').value.sheep.limbs.length>0);
  assert(Object.keys(run.query().probe('wornCells').value).length>0);
  const branch=run.fork();
  branch.schedule([{tick:71,action:'world/input',args:{port:'wear/enabled',value:false}}]);
  const wear=branch.query().probe('wornCells').value;
  branch.advance(90);
  assert.deepEqual(branch.query().probe('wornCells').value,wear);
  run.advance(180,{stopOnOutcome:true});
  assert.equal(run.scenario.status,'win');
  assert.equal(run.scenario.score,100);
  assert(run.view().tick<180);
});

test('accumulated contacts can be retained as an editable path', () => {
  const bounds={min:[0,-1,0],max:[5,1,4]}, contacts=[];
  for(let i=1;i<=15;i++)contacts.push({point:[.125+i*.25,0,1.125],support:'ground',weight:4});
  const run=W.runtime.create({systems:{terrain:{kind:'wear',config:{bounds,cell:.25}}}});
  run.schedule([{tick:1,action:'terrain/contact',args:{contacts}}]);
  run.step();
  const trace=run.query().trace('trail',[.375,0,1.125],{to:[3.875,0,1.125]}).value;
  assert.equal(trace.status,'ok');
  const result=W.history.trail(run.view().world,'shortcut',trace);
  assert.equal(result.world.entities.shortcut.kind,'path');
  assert.deepEqual(result.world.entities.shortcut.points,trace.points);
});

test('water sees the same obstruction as a clearance query and responds when it breaks', () => {
  const run=W.runtime.create({dt:.04,systems:{
    land:{kind:'mechanics',config:{bodies:{weir:{fixed:true,position:[2,.5,1.5],half:[.19,.7,1.5]}}}},
    river:{kind:'water',config:{width:4,height:3,obstacle:'land/clearance',
      initial:[{bounds:{min:[0,0],max:[2,3]},value:1}]}}
  }});
  run.advance(12);
  assert.equal(run.query().probe('river/water',[2.5,0,1.5]).status,'dry');
  assert.equal(run.query().probe('land/clearance',[2,.5,1.5]).body,'weir');
  run.schedule([{tick:13,action:'land/fracture',args:{body:'weir',axis:2,parts:2,omit:[0,1]}}]);
  run.advance(38);
  assert.equal(run.query().probe('river/water',[2.5,0,1.5]).status,'ok');
  assert(Math.abs(run.query().probe('mass').value.error)<1e-10);
});

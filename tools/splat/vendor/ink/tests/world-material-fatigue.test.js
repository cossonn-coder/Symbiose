const test=require('node:test');
const assert=require('node:assert/strict');
const kit=require('..').load();
const {KIT:{world:W}}=kit;
const workshop=require('../examples/world-material-fatigue.json');
const commands=require('../examples/world-material-fatigue.commands.json');

const probe=(run,args,point={})=>run.query().probe('rig/fatigue',point,args).value;
const input=(tick,port,value)=>({tick,action:'world/input',args:{port,value}});
const packed=value=>JSON.parse(JSON.stringify(value));
const close=(a,b,tolerance=1e-6)=>assert.ok(Math.abs(a-b)<=tolerance,`${a} differs from ${b}`);
const rig=(config,extra={})=>W.runtime.create({dt:.05,...extra,systems:{rig:{kind:'mechanics',config}}});
const support=(run,id,x,z)=>run.query().probe('rig/support',[x,1.5,z]).value.find(hit=>hit.id===id)?.y;

test('a real crate load leaves a permanent bend, with matching support, clearance and sockets after unloading',()=>{
  const run=W.runtime.create(workshop);
  const y=()=>support(run,'creep-beam',-1.38,1.05), baseline=y();
  run.schedule(commands);
  run.advance(44);
  const bent=y(), loaded=probe(run,{body:'creep-beam'});
  assert.ok(loaded.loads>0&&loaded.yielded&&bent<baseline-.45);
  assert.equal(loaded.hotspot.section,5);
  assert.ok(loaded.hotspot.stressMagnitude>loaded.plastic.yield);
  assert(run.dependencies().pending.some(write=>write.field==='rig/support'&&write.reason==='permanent-deformation'));
  assert.equal(run.query().probe('rig/clearance',[-1.38,bent-.02,1.05]).body,'creep-beam');
  run.advance(64);
  const result=probe(run,{body:'creep-beam'});
  assert.equal(result.loads,0);
  close(result.hotspot.stressMagnitude,0);
  close(y(),bent);
  close(run.query().target({entity:'creep-beam',socket:'crown'}).point[1],bent);
  close(support(run,'creep-beam',-3.66,1.05),baseline,.01);
  assert.deepEqual(packed(W.runtime.replay(packed(run.recording())).checkpoint()),packed(run.checkpoint()));
  const rendered=W.query.fromScene(W.visual(kit,run.view(),run.query()));
  assert.ok(rendered.select({entity:'creep-beam',material:'shop/malleable'}).length>0);
});

test('reversing loads accumulate localized fatigue while a constant load holds the same damage',()=>{
  const run=W.runtime.create(workshop), control=W.runtime.create(workshop);
  run.schedule(commands);
  run.advance(17);
  const early=probe(run,{body:'cycle-beam'});
  assert.equal(early.hotspot.section,6);
  assert.ok(early.hotspot.damage>.5&&early.hotspot.damage<1);
  assert.equal(early.sections[0].damage,0);
  assert.deepEqual(probe(run,{},early.hotspot.at),{body:'cycle-beam',...early.hotspot,distance:0});
  control.advance(41);
  assert.equal(probe(control,{body:'cycle-beam'}).hotspot.damage,0);
  run.advance(64);
  const final=probe(run,{body:'cycle-beam'});
  assert.equal(final.hotspot.damage,1);
  assert.equal(final.hotspot.section,6);
  assert.equal(final.hotspot.stressMagnitude,0);
  assert.equal(final.failed,true);
  assert.deepEqual(run.history.filter(e=>e.kind==='material-failure'&&e.body==='cycle-beam')
    .map(e=>[e.tick,e.section]),[[25,6]]);
});

test('worn hinges take up backlash on reversal and can detach at their fatigue limit',()=>{
  const run=W.runtime.create(workshop);
  run.schedule(commands);
  run.advance(18);
  const forward=probe(run,{joint:'hinge'});
  run.step();
  const reversal=probe(run,{joint:'hinge'});
  assert.ok(reversal.play>forward.play&&reversal.command<forward.command);
  close(reversal.actual,forward.actual);
  assert.equal(reversal.speed,0);
  const detached=packed(workshop);
  detached.systems.rig.config.joints.hinge.wear.failure='detach';
  const failure=W.runtime.create(detached);
  failure.schedule(commands);
  failure.advance(25);
  assert.equal(probe(failure,{joint:'hinge'}).active,false);
  assert.equal(probe(failure,{joint:'hinge'}).damage,1);
  assert(failure.events.some(event=>event.joint==='hinge'&&event.detached));
  assert.equal(failure.query().trace('rig/support',[2.42,1.99,-.14]).status,'ok');
});

test('surface charts follow bent geometry and its later fracture',()=>{
  const run=rig({gravity:[0,0,0],drag:0,bodies:{beam:{position:[0,1,0],fixed:true,half:[1,.14,.3],
    surfaceState:{faces:{'+y':[{channel:'paint',value:'#dc9130',brush:{kind:'rect',min:[0,0],max:[1,1]}}]}},
    structure:{plastic:{yield:90,creep:.08,limit:1}}}},
    forces:{press:{kind:'thrust',body:'beam',axis:[0,-1,0],magnitude:8,input:1}}});
  run.advance(12);
  const x=.35, before=support(run,'beam',x,0);
  const reading=(body,height)=>run.query().probe('rig/surface-state',[x,height,0],{body,face:'+y'}).value;
  const paint=reading('beam',before);
  assert.equal(paint.values.paint.coverage,1);
  run.schedule([input(13,'rig/force.press',0),{tick:13,action:'rig/fracture',args:{body:'beam',parts:2}}]);
  run.step();
  const after=support(run,'beam.1',x,0), fragment=reading('beam.1',after);
  close(after,before);
  assert.equal(fragment.chart,paint.chart);
  close(fragment.rest[0],paint.rest[0]);
  close(fragment.rest[1],paint.rest[1]);
  assert.deepEqual(fragment.values.paint,paint.values.paint);
  assert.equal(probe(run,{body:'beam'}).present,false);
  assert.doesNotThrow(()=>run.fork());
});

test('a cantilever keeps its anchored end and develops its peak stress at the root',()=>{
  const run=rig({bodies:{beam:{fixed:true,position:[0,1,0],half:[1,.14,.25],
    structure:{bearings:'fixed-start',plastic:{yield:200,creep:.1,limit:.8}}}},
    forces:{tip:{kind:'thrust',body:'beam',axis:[0,-1,0],at:[1,0,0],magnitude:8,input:1}}});
  run.advance(20);
  const {sections,hotspot}=probe(run,{body:'beam'});
  assert.equal(hotspot.section,0);
  assert.deepEqual(sections[0].at,[-1,1,0]);
  assert.ok(sections.at(-1).at[1]<.75);
});

test('portable laws interpolate with wetness and reject malformed structural definitions',()=>{
  const run=W.runtime.create(workshop), wet=run.query().probe('world/material',{}, {id:'shop/malleable',wetness:.5});
  assert.equal(wet.value.plastic.yield,525);
  assert.throws(()=>rig({bodies:{beam:{half:[1,.2,.2],structure:{fatigue:{endurance:2,life:0,exponent:2}}}}}),/fatigue/);
  assert.throws(()=>rig({bodies:{beam:{half:[1,.2,.2],structure:{}}}}),/needs a fatigue or plastic/);
});

const test=require('node:test');
const assert=require('node:assert/strict');
const studio=require('..'), kit=studio.load(), {KIT:{world:W}}=kit;
const example=require('../examples/world-cellar-flood.json');

const clone=value=>JSON.parse(JSON.stringify(value));
const near=(a,b,tolerance=1e-8)=>assert.ok(Math.abs(a-b)<=tolerance,`${a} differs from ${b}`);
const read=(run,name,at,args)=>run.query().probe('flood/'+name,at,args);
const chamber=(run,chamber)=>read(run,'chambers',{}, {chamber}).value;
const opening=(run,opening)=>read(run,'openings',{}, {opening}).value;
const box=(min,max,initial)=>({bounds:{min,max},...(initial!==undefined&&{initial})});
const input=(tick,pin,value)=>({tick,action:'world/input',args:{port:'flood/'+pin,value}});
const fixture=(config,options={})=>({dt:.1,systems:{flood:{kind:'enclosed-water',config,...options}}});

test('a live breach floods a tunnel, traps air under the street, then admits more water after venting',()=>{
  const run=W.runtime.create({...example,commands:example.commands.slice(0,1)});
  const street=[1.6,.8,.5], cellar=[1.6,-1.86,.5];
  assert.equal(read(run,'water',street).status,'dry');
  assert.equal(read(run,'water',cellar).status,'dry');
  assert.equal(read(run,'chambers',street).value.id,'street');
  assert.equal(read(run,'phase',[1.6,-.1,.5]).status,'outside');
  assert.equal(opening(run,'breach').opening,0);
  const trappedAir=chamber(run,'cellar').airAmount+chamber(run,'tunnel').airAmount;
  run.advance(6);
  assert.equal(opening(run,'breach').opening,1);
  assert.ok(opening(run,'breach').flow>2);
  assert.ok(run.dependencies().pending.some(row=>row.field==='flood/water'&&row.bounds.min[1]===-1.54));
  run.advance(77);
  const before=chamber(run,'cellar'), sealed=run.fork(), vented=run.fork();
  assert.ok(before.airPressure>114000);
  near(chamber(run,'tunnel').airPressure,before.airPressure);
  near(chamber(run,'tunnel').airAmount+before.airAmount,trappedAir);
  near(read(run,'mass').value.airExchange,7.2-chamber(run,'canal').water);
  vented.schedule(example.commands.slice(1));
  vented.advance(78);
  near(chamber(vented,'cellar').airPressure,101325);
  assert.equal(chamber(vented,'cellar').vented,true);
  assert.ok(opening(vented,'breach').flow>2);
  vented.advance(160);
  sealed.advance(160);
  assert.ok(chamber(vented,'cellar').water>6);
  assert.ok(chamber(sealed,'cellar').water<2.7);
  assert.equal(read(vented,'phase',street).value,'air');
  assert.equal(read(vented,'phase',cellar,{explain:true}).provenance.source.chamber,'cellar');
  assert.equal(read(vented,'water',cellar).status,'ok');
  assert.ok(read(vented,'pressure',cellar).value>101325);
  for(const branch of [sealed,vented]){
    const ledger=read(branch,'mass').value;
    near(ledger.volume,7.2);
    near(ledger.error,0);
    near(ledger.airError,0);
    assert.deepEqual(clone(W.runtime.replay(clone(branch.recording())).checkpoint()),clone(branch.checkpoint()));
  }
});

test('submerging an air opening isolates a chamber, and a full chamber can drain from an open roof',()=>{
  const source=fixture({
    chambers:{upper:box([0,1,0],[2,3,2],8),lower:box([0,-2,0],[2,0,2])},
    openings:{shaft:{from:'upper',to:'lower',fromSill:1,fromCrown:2,toSill:-2,toCrown:-1,
      conductance:3,maxFlow:2}},
    vents:{roof:{chamber:'upper'},snorkel:{chamber:'lower',height:-1.9}}
  });
  const run=W.runtime.create(source);
  assert.equal(chamber(run,'upper').vented,true);
  run.step();
  assert.ok(chamber(run,'upper').water<8);
  assert.equal(opening(run,'shaft').airConnected,false);
  run.advance(12);
  const vent=read(run,'vents',{}, {vent:'snorkel'}).value;
  assert.equal(vent.submerged,true);
  assert.equal(vent.active,false);
  assert.ok(chamber(run,'lower').airPressure>105000);
  run.schedule([input(13,'opening.shaft',0)]);
  run.step();
  near(opening(run,'shaft').flow,0);
  near(read(run,'mass').value.error,0);
});

test('a shared sill retains the water below it when two lower chambers compete for the same flow',()=>{
  const config={
    chambers:{top:box([0,1,0],[1,3,1],1.05),a:box([0,-2,0],[1,0,1]),b:box([1,-2,0],[2,0,1])},
    openings:{a:{from:'top',to:'a',fromSill:2,conductance:1e6},b:{from:'top',to:'b',fromSill:2,conductance:1e6}},
    vents:{top:{chamber:'top'},a:{chamber:'a'},b:{chamber:'b'}}
  };
  const run=W.runtime.create(fixture(config));
  run.advance(15);
  near(chamber(run,'top').water,1);
  near(chamber(run,'a').water,.025);
  near(chamber(run,'b').water,.025);
  near(read(run,'mass').value.error,0);
});

test('surface water accounts exchange with a chamber and publish a bounded revision',()=>{
  const source=fixture({
    chambers:{basement:box([0,-2,0],[1,-1,1])},vents:{roof:{chamber:'basement'}},
    boundaries:{intake:{chamber:'basement',account:'river/port',headField:'river/surface-height',
      at:[.5,0,.5],conductance:8,maxFlow:2,direction:'in'}}
  });
  source.systems.river={kind:'water',config:{width:1,height:1,cell:1,
    initial:[{bounds:{min:[0,0],max:[1,1]},value:.85}],accounts:{port:[.5,.5]}}};
  const run=W.runtime.create(source);
  run.step();
  near(chamber(run,'basement').water,.2);
  assert.equal(read(run,'boundaries',{}, {boundary:'intake'}).value.receipt.status,'full');
  assert.equal(run.events.find(row=>row.kind==='chamber-wet').chamber,'basement');
  assert.ok(run.dependencies().pending.some(row=>row.field==='flood/depth'&&row.bounds.max[1]===-1));
  run.advance(6);
  const river=run.query().probe('river/mass').value, flood=read(run,'mass').value;
  near(river.volume+flood.volume,.85);
  near(flood.imported,river.sent);
  near(flood.error,0);
  const malformed=clone(source);
  malformed.systems.flood.config.boundaries.intake.headField='river/flow';
  assert.throws(()=>W.runtime.create(malformed),/Boundary head must be a numeric field/);
});

test('stacked water renders as two disjoint ray intervals at one XZ, matching boxed phase queries',()=>{
  const source=fixture({chambers:{
    top:box([-1,0,-1],[1,2,1],4),bottom:box([-1,-3,-1],[1,-1,1],6)
  }});
  source.visual={enclosedWater:'flood',ground:-3};
  const run=W.runtime.create(source), query=run.query(), scene=W.visual(kit,run.view(),query);
  const intervals=scene.water.raySegments([0,3,0],[0,-1,0],9);
  assert.deepEqual(intervals.map(row=>row.slice(0,2)),[[2,3],[4.5,6]]);
  assert.equal(read(run,'phase',[0,.5,0]).value,'water');
  assert.equal(read(run,'phase',[0,-.4,0]).status,'outside');
  assert.equal(read(run,'phase',[0,-2.7,0]).value,'water');
  const overlap=clone(source);
  overlap.systems.flood.config.chambers.top.bounds.min[1]=-1.5;
  assert.throws(()=>W.runtime.create(overlap),/Water chambers overlap/);
});

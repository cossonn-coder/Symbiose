const test=require('node:test');
const assert=require('node:assert/strict');
const studio=require('..'), kit=studio.load(), {KIT:{world:W}}=kit;
const example=require('../examples/world-windmill-workshop.json');

const near=(a,b,eps=1e-8)=>assert.ok(Math.abs(a-b)<=eps,`${a} differs from ${b}`);
const copy=value=>JSON.parse(JSON.stringify(value));
const field=(run,name,args)=>run.query().probe(name,{},args).value;
const load=(run,load)=>field(run,'power/loads',{load});
const line=(run,line)=>field(run,'power/lines',{line});
const battery=(run,battery='cell')=>field(run,'power/batteries',{battery});
const energy=run=>field(run,'power/energy');
const rig=(run,key)=>field(run,'rig/joints')[key];
const net=config=>({dt:.1,systems:{power:{kind:'power-network',config}}});
const input=(tick,port,value)=>({tick,action:'world/input',args:{port,value}});
const reset=(tick,line)=>({tick,action:'power/reset',args:{line}});

test('generation serves priority loads, then efficient battery charge uses surplus',()=>{
  const run=W.runtime.create(net({
    buses:{supply:{},home:{}},lines:{feed:{from:'supply',to:'home'}},
    generators:{main:{bus:'supply',watts:5}},batteries:{cell:{bus:'supply',capacity:4,initial:2,
      chargeWatts:4,dischargeWatts:5,chargeEfficiency:.8,dischargeEfficiency:.75}},
    loads:{important:{bus:'home',watts:9,priority:3},other:{bus:'home',watts:9}}
  }));
  run.step();
  near(load(run,'important').delivered,9);
  near(load(run,'other').delivered,1);
  assert.equal(load(run,'other').status,'limited');
  near(battery(run).discharge,5);
  near(battery(run).energy,2-.5/.75);
  near(line(run,'feed').flow,10);
  run.schedule([input(2,'power/enable-load.important',false),input(2,'power/enable-load.other',false)]);
  run.step();
  near(battery(run).charge,4);
  near(battery(run).energy,2-.5/.75+.4*.8);
  near(energy(run).curtailed,.1);
  near(energy(run).error,0);
});

test('a tripped branch reroutes over a longer closed path and latches through a checkpoint',()=>{
  const run=W.runtime.create(net({
    buses:{a:{},b:{},c:{}},generators:{main:{bus:'a',watts:12}},loads:{machine:{bus:'c',watts:10}},
    lines:{direct:{from:'a',to:'c',breaker:{watts:6,delay:.2}},backupA:{from:'a',to:'b'},backupB:{from:'b',to:'c'}}
  }));
  run.step();
  near(line(run,'direct').flow,10);
  assert.equal(line(run,'direct').tripped,null);
  const saved=copy(run.checkpoint()), branch=W.runtime.create(saved.world,{checkpoint:saved});
  run.step();branch.step();
  assert.deepEqual(copy(run.checkpoint()),copy(branch.checkpoint()));
  near(line(run,'direct').tripped.watts,10);
  near(line(run,'direct').flow,0);
  near(line(run,'backupA').flow,10);
  assert.deepEqual(run.query().trace('power/power',{entity:'machine'}).value.deliveries[0].path.map(row=>row.line),
    ['backupA','backupB']);
  near(energy(run).consumed,2);
  run.schedule([input(3,'power/demand.machine',4),reset(3,'direct')]);
  run.step();
  near(line(run,'direct').flow,4);
  assert.equal(line(run,'direct').tripped,null);
  assert.deepEqual(run.history.filter(row=>row.kind.startsWith('breaker-')).map(row=>row.kind),['breaker-trip','breaker-reset']);
  near(energy(run).error,0);
});

test('a blocked feeder keeps its battery energy and a persistent overload can retrip after reset',()=>{
  const run=W.runtime.create(net({
    buses:{a:{},b:{}},batteries:{cell:{bus:'a',capacity:10,initial:10}},
    loads:{motor:{bus:'b',watts:16}},lines:{breaker:{from:'a',to:'b',breaker:{watts:8}}}
  }));
  run.step();
  assert.equal(line(run,'breaker').tripped.tick,1);
  near(battery(run).energy,10);
  assert.equal(load(run,'motor').status,'unpowered');
  run.schedule([reset(2,'breaker')]);run.step();
  assert.equal(line(run,'breaker').tripped.tick,2);
  assert.equal(run.query().trace('power/power',{}, {load:'motor'}).value.breakers[0].line,'breaker');
  near(energy(run).consumed,0);
  near(energy(run).error,0);
});

test('wind generation respects cut-in, rating and cut-out, and the battery exposes a J account',()=>{
  const definition=net({
    buses:{a:{}},generators:{mill:{bus:'a',watts:100,wind:{field:'weather/wind',at:[0,0,0],cutIn:2,rated:6,cutOut:10}}},
    batteries:{cell:{bus:'a',capacity:10,chargeWatts:8}}
  });
  definition.systems.weather={kind:'fields',config:{fields:{wind:{type:'vec2',axes:'xz',units:'world/s',default:[1,0]}}}};
  definition.systems.store={kind:'store',config:{accounts:{pack:{resource:'energy',units:'J',initial:5,max:5}}}};
  const run=W.runtime.create(definition);
  const wind=(tick,speed)=>({tick,action:'weather/set',args:{field:'wind',region:{bounds:{min:[-1,-1],max:[1,1]},value:[speed,0]}}});
  const generator=()=>field(run,'power/generators',{generator:'mill'});
  run.step();near(generator().available,0);
  run.schedule([wind(2,4),wind(3,7),wind(4,11),{tick:4,action:'world/transfer',
    args:{from:'store/pack',to:'power/cell',amount:3}}]);
  run.step();
  near(generator().available,100*(4**3-2**3)/(6**3-2**3));
  near(generator().generated,8);
  run.step();near(generator().available,100);
  run.step();near(generator().available,0);
  near(battery(run).energy,4.6);
  near(energy(run).imported,3);
  near(field(run,'world/account',{account:'power/cell'}).balance,4.6);
  near(energy(run).error,0);
});

test('a limited vertical motor requests the mounted mass and obeys its watt budget and travel limits',()=>{
  const r=W.runtime.create({dt:.1,systems:{rig:{kind:'mechanics',config:{bodies:{
    platform:{half:[.4,.1,.4],mass:2},crate:{half:[.17,.2,.17],mass:3}
  },joints:{lift:{kind:'slider',child:'platform',anchor:[0,.2,0],speed:1,range:[0,.2],
    powerLimited:true,gravityLoad:true,idlePower:2},cargo:{kind:'fixed',child:'crate',parent:'platform',anchor:[0,.3,0]}}}}}});
  r.step();
  near(rig(r,'lift').value,0);
  near(rig(r,'lift').power.demand,51.05);
  r.schedule([input(2,'rig/power.lift',26.525),input(5,'rig/power.lift',100)]);
  r.step();
  near(rig(r,'lift').value,.05);
  near(rig(r,'lift').power.draw,26.525);
  assert.equal(rig(r,'lift').power.limited,true);
  r.advance(6);
  near(rig(r,'lift').value,.2);
  near(rig(r,'lift').power.demand,0);
  near(rig(r,'lift').power.draw,0);
});

test('windmill demo charges, pauses a real lift after the grinder trips the branch, and replays',()=>{
  const run=W.runtime.create(example);
  run.advance(30);
  assert.ok(battery(run).energy>170);
  near(rig(run,'lift').value,0);
  run.advance(45);
  near(rig(run,'lift').power.gravity,9*9.81);
  near(rig(run,'lift').speed,.7);
  assert.ok(battery(run).discharge>0);
  run.advance(52);
  const fault=line(run,'workshop-breaker').tripped, paused=rig(run,'lift').value;
  assert.deepEqual(fault.loads,['lift','grinder']);
  assert.ok(fault.watts>140);
  near(rig(run,'lift').speed,0);
  near(rig(run,'grinder').speed,0);
  assert.equal(run.query().trace('power/power',{entity:'lift'}).value.breakers[0].tick,fault.tick);
  run.advance(77);
  near(rig(run,'lift').value,paused);
  assert.ok(W.query.fromScene(W.visual(kit,run.view(),run.query())).select({material:'power-line'}).length>0);
  run.advance(96);
  assert.equal(line(run,'workshop-breaker').tripped,null);
  near(rig(run,'lift').value,1.95);
  near(energy(run).error,0);
  assert.deepEqual(copy(W.runtime.replay(copy(run.recording())).checkpoint()),copy(run.checkpoint()));
});

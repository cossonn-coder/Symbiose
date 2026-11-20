const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT:{world:W}}=require('..').load();
const sluice=require('../examples/world-sediment-gate.json');
const ford=require('../examples/world-sediment-ford.json');

const packed=value=>JSON.parse(JSON.stringify(value));
const close=(a,b,tolerance=1e-9)=>assert.ok(Math.abs(a-b)<=tolerance,`${a} differs from ${b}`);
const probe=(run,name,at={},args={})=>run.query().probe('river/'+name,at,args).value;
const region=(min,max)=>({min,max});
const patch=(min,max,value)=>({bounds:region(min,max),value});
const water=(config,dt=.1)=>W.runtime.create({dt,systems:{river:{kind:'water',config}}});
const command=(tick,action,args)=>({tick,action:'river/'+action,args});

test('a stream erodes, moves material and silts a gate without losing water or sediment',()=>{
  const run=W.runtime.create(sluice), gate=()=>probe(run,'gates',{}, {gate:'sluice'});
  const open=gate();
  close(open.effective,.32);
  assert.equal(open.faces,3);
  run.advance(5);
  assert.ok(gate().effective>0&&gate().effective<open.effective);
  const fork=run.fork();
  run.advance(65);
  fork.advance(65);
  assert.deepEqual(packed(run.checkpoint()),packed(fork.checkpoint()));
  assert.equal(gate().clogged,true);
  close(gate().effective,0);
  close(gate().command,.32);
  const metric=probe(run,'sediment');
  assert.ok(metric.eroded>.1&&metric.advected>.1&&metric.deposited>.1);
  assert(probe(run,'bed-change',[-1.8,0,0])<-.02);
  assert(probe(run,'bed-change',[-.6,0,0])>.085);
  assert(probe(run,'erodible-depth',[-1.4,0,0])>=0);
  close(metric.error,0);
  close(probe(run,'mass').error,0);
  assert.equal(run.history.filter(event=>event.kind==='gate-silted').length,1);
  assert(run.history.find(event=>event.kind==='gate-silted').tick===7);
  assert.deepEqual(packed(W.runtime.replay(packed(run.recording())).checkpoint()),packed(run.checkpoint()));
  run.schedule([command(66,'bed',{bounds:region([-.81,-.61],[.01,.61]),height:.06})]);
  run.step();
  assert.equal(gate().clogged,false);
  assert(run.events.some(event=>event.kind==='gate-cleared'&&event.gate==='sluice'));
  close(probe(run,'sediment').error,0);
});

test('a settled shoal opens a ford and agents cross it using the live bed',()=>{
  const run=W.runtime.create(ford), dryControl=packed(ford);
  delete dryControl.systems.river.config.sediment.initial;
  const control=W.runtime.create(dryControl);
  const point=[3.6,0,1.25], start=[3.6,.43,.62], goal=[3.6,.43,1.88];
  const trace=run=>run.query().trace('nav/route',start,{to:goal,radius:.115,maxWade:.18,maxSlope:2.6}).value;
  assert.equal(trace(run).status,'unreachable');
  run.advance(24);
  assert.equal(trace(run).status,'ok');
  assert.ok(probe(run,'depth',point)<.18&&probe(run,'bed',point)>.3);
  assert(run.dependencies().pending.some(write=>write.field==='river/bed'&&write.reason==='sediment-transport'));
  assert(run.dependencies().affected.some(row=>row.system==='walk'||row.reader==='walk'));
  run.advance(65);control.advance(65);
  const walker=run.query().probe('walk/agents').value.porter;
  assert.equal(walker.mode,'rest');
  assert(walker.position[2]>1.75);
  assert.equal(trace(control).status,'unreachable');
  close(probe(run,'sediment').error,0);
  close(probe(run,'mass').volume,probe(control,'mass').volume);
});

test('closed faces block suspended sediment and an explicit pump carries it at donor concentration',()=>{
  const run=water({width:2,height:1,
    initial:[patch([0,0],[2,1],.4)],
    sediment:{erodibleDepth:0,settling:0,initial:[patch([0,0],[1,1],.2)]},
    gates:{dam:{axis:0,bounds:region([.999,0],[1.001,1]),opening:0}},
    pumps:{bypass:{from:[.5,.5],to:[1.5,.5],rate:0}}
  });
  const source=[.5,0,.5], target=[1.5,0,.5];
  run.step();
  close(probe(run,'suspended',target),0);
  close(probe(run,'sediment').advected,0);
  run.schedule([command(2,'pump',{pump:'bypass',rate:.5})]);
  run.step();
  close(probe(run,'suspended',target),.025);
  close(probe(run,'suspended',source),.175);
  close(probe(run,'sediment').pumped,.025);
  close(probe(run,'sediment').error,0);
  close(probe(run,'mass').error,0);
});

test('a dry pulse settles and live terrain cuts and fills appear in the sediment ledger',()=>{
  const run=water({width:2,height:1,cell:[2,.5],base:1,sediment:{erodibleDepth:.2,settling:0}});
  const left=region([0,0],[2,.5]), right=region([2,0],[4,.5]);
  run.schedule([command(1,'sediment-feed',{bounds:left,depth:.3}),
    command(2,'bed',{bounds:left,height:.7}),command(2,'bed',{bounds:right,height:1.12})]);
  run.step();
  close(probe(run,'bed',[1,0,.25]),1.3);
  close(probe(run,'sediment').fed,.3);
  close(probe(run,'sediment').deposited,.3);
  assert.equal(run.query().probe('river/water',[1,0,.25]).status,'dry');
  run.step();
  close(probe(run,'erodible-depth',[1,0,.25]),0);
  close(probe(run,'bed-change',[1,0,.25]),0);
  const metric=probe(run,'sediment');
  close(metric.editedIn,.12);close(metric.editedOut,.5);close(metric.error,0);
  assert.doesNotThrow(()=>run.fork());
});

test('drain export is accounted for and an exhausted bed does not erode',()=>{
  const run=water({width:1,height:1,initial:[patch([0,0],[1,1],.2)],drain:.5,
    sediment:{erodibleDepth:0,drainFraction:1,settling:0,initial:[patch([0,0],[1,1],.1)]}});
  run.step();
  const metric=probe(run,'sediment');
  close(metric.exported,.025);
  close(metric.suspended,.075);
  close(metric.eroded,0);
  close(metric.error,0);
  assert.throws(()=>water({width:1,height:1,sediment:{drainFraction:1.2}}),/sediment/);
});

test('a bound physical surface sets the erosion rate for live sediment',()=>{
  const bed={width:4,height:1,initial:[patch([0,0],[2,1],.8)],
    sediment:{capacity:.5,settling:.2,erosion:{threshold:0,rate:.4}}};
  const control=water(bed,.05);
  const run=W.runtime.create({dt:.05,assetPacks:[{
    format:'ink-studio/asset-pack',version:1,id:'banks',title:'Bank materials',revision:1,
    materials:[{id:'banks/hard',label:'Protected bank',erosion:{threshold:0,rate:0}}]
  }],systems:{soil:{kind:'materials',config:{grid:{width:4,height:1},material:'banks/hard'}},
    river:{kind:'water',config:{...bed,surface:'soil/surface'}}}});
  run.advance(8);control.advance(8);
  close(probe(run,'sediment').eroded,0);
  assert.ok(probe(control,'sediment').eroded>0);
  close(probe(control,'sediment').error,0);
});

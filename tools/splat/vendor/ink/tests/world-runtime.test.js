const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: { world: W } } = require('..').load();

test('world edits are atomic, validate attachments and keep untouched branches shared', () => {
  const before=W.manifest({entities:{stone:{position:[0,0,0]},lamp:{position:[1,0,0]}},metadata:{title:'a'}});
  const edits=[
    {op:'test',path:'/metadata/title',value:'a'},
    {op:'set',path:['entities','stone','position',0],value:3},
    {op:'merge',path:'/metadata',value:{title:'b'}}
  ];
  const result=W.apply(before,edits);
  assert.deepEqual(result.paths,[['entities','stone','position',0],['metadata']]);
  assert.strictEqual(result.world.entities.lamp,before.entities.lamp);
  assert.strictEqual(result.world.systems,before.systems);
  assert.deepEqual(before.entities.stone.position,[0,0,0]);
  assert.throws(()=>W.apply(before,[...edits,{op:'set',path:'/entities/lamp/parent',value:'unknown'}]),/Missing parent/);
  assert.throws(()=>W.apply(before,[{op:'set',path:'/__proto__/x',value:true}]),/Invalid edit path/);
  assert.equal(before.metadata.title,'a');
});

test('prefabs remap sockets, scoped systems and connections, and capture instance overrides', () => {
  const definition={
    params:{width:1},
    entities:{frame:{position:[.5,0,0],sockets:{upper:[0,1,0]}},
      panel:{anchor:{entity:'frame',socket:'upper'},position:[0,.2,0],width:{$param:'width'}}},
    systems:{switch:{kind:'control',config:{op:'not'}},counter:{kind:'control',config:{op:'timer',ticks:4}}},
    connections:[{from:'switch/value',to:'counter/enabled'}],ports:{enable:'switch/value',count:'counter/value'}
  };
  const source=W.manifest({prefabs:{gate:definition}});
  const stamped=W.stamp(source,'gate','east',{params:{width:2},position:[3,0,2]}).world;
  assert.equal(stamped.entities['east.panel'].width,2);
  assert.deepEqual(stamped.connections,[{from:'east.switch/value',to:'east.counter/enabled'}]);
  assert.deepEqual(W.runtime.create(stamped).query().probe('position',{entity:'east.panel'}).value,[3.5,1.2,2]);
  const captured=W.capture(stamped,'east','wide').world;
  const twice=W.stamp(captured,'wide','west').world;
  assert.equal(twice.entities['west.panel'].width,2);
  assert.equal(twice.entities.west.ports.count,'west.counter/value');
  assert(W.runtime.validate(twice));
  const remixed=W.remix(source,'gate','small',[{op:'set',path:'/params/width',value:.5}]).world;
  assert.equal(W.stamp(remixed,'small','door').world.entities['door.panel'].width,.5);
});

test('spatial queries include boundary positions and share field samples with line and grid exports', () => {
  const world=W.runtime.create({dt:.1,entities:{oak:{position:[4,3,0],kind:'tree'},pine:{position:[5,3,0],kind:'tree'}},
    systems:{climate:{kind:'fields',config:{fields:{temperature:{default:12,units:'C',
      regions:[{bounds:{min:[4,0,-1],max:[4,5,1]},value:17}]}}}}}});
  const query=world.query();
  assert.deepEqual(query.spatial({point:[0,3,0],radius:4}).map(row=>row.id),['oak']);
  assert.equal(query.inspect().fields.find(field=>field.name==='climate/temperature').units,'C');
  assert.deepEqual(query.probe('temperature',{entity:'oak'}),{status:'ok',value:17});
  assert.equal(query.probe('missing',[0,0,0]).status,'unavailable');
  const line=query.export('temperature',{line:{from:[3,3,0],to:[5,3,0],count:3}});
  assert.deepEqual(line.samples.map(row=>row.value),[12,17,12]);
  const grid=query.export('temperature',{grid:{min:[3,3,0],max:[5,3,1],counts:[3,1,2]}});
  assert.equal(grid.grid.order,'x-fastest');
  assert.deepEqual(grid.samples.map(row=>row.value),[12,17,12,12,17,12]);
});

test('typed circuits reject incompatible or instantaneous cycles and resume delayed feedback', () => {
  const systems={a:{kind:'control',config:{op:'not'}},b:{kind:'control',config:{op:'not'}}};
  const edges=[{from:'a/value',to:'b/value'},{from:'b/value',to:'a/value'}];
  assert.throws(()=>W.runtime.validate({systems,connections:edges}),/Instantaneous signal cycle/);
  assert.throws(()=>W.runtime.validate({systems:{...systems,n:{kind:'control'}},connections:[{from:'a/value',to:'n/value'}]}),
    /Incompatible/);
  const run=W.runtime.create({systems:{a:systems.a},connections:[{from:'a/value',to:'a/value',delay:1}]});
  run.step();
  assert.equal(run.query().probe('signal',{}, {port:'a/value'}).value,true);
  const fork=run.fork();
  fork.step();
  assert.equal(fork.query().probe('signal',{}, {port:'a/value'}).value,false);
  assert.equal(run.query().probe('signal',{}, {port:'a/value'}).value,true);
  assert.equal(fork.query().trace('signal',{}, {port:'a/value'}).value.status,'cycle');
  const restored=W.runtime.replay(JSON.parse(JSON.stringify(fork.recording())));
  assert.deepEqual(restored.checkpoint(),fork.checkpoint());
});

test('scheduled interventions are atomic and recording replay preserves pending actions and custom history', () => {
  const world={id:'study',dt:.1,seed:5,history:{where:{path:['kind'],op:'eq',value:'notable'}}};
  const run=W.runtime.create(world);
  run.schedule([
    {tick:1,action:'world/event',args:{kind:'draft',entity:'mill'}},
    {tick:2,action:'world/event',args:{kind:'notable',entity:'mill'}},
    {tick:9,action:'world/event',args:{kind:'notable',entity:'barn'}}
  ]);
  run.advance(2);
  assert.equal(run.checkpoint().pending.length,1);
  assert.equal(run.query().probe('history',{}, {entity:'mill'}).value.events[0].kind,'notable');
  const checkpoint=run.checkpoint(), record=JSON.parse(JSON.stringify(run.recording()));
  assert.deepEqual(W.runtime.replay(record).checkpoint(),checkpoint);
  const rejected=run.fork();
  rejected.schedule([{tick:3,action:'world/patch',args:{edits:[{op:'remove',path:'/entities/missing'}]}}]);
  const before=rejected.checkpoint();
  assert.throws(()=>rejected.step(),/missing path/);
  assert.deepEqual(rejected.checkpoint(),before);
  assert.equal(run.reset().view().tick,0);
});

test('user-defined seeded history creates permanent remains and shares the runtime event query', () => {
  const source=W.manifest({seed:198});
  const rules=[{id:'old-storm',start:-20,event:{kind:'ruin',place:'{id}',name:{$choose:['Old Weir','Flood Gate']}},
    edits:[{op:'set',path:['entities','{id}'],value:{kind:'ruin',position:[4,0,-2]}}]}];
  const first=W.history.generate(source,rules);
  assert.deepEqual(first,W.history.generate(source,rules));
  const run=W.runtime.create(first.world);
  assert.equal(run.query().probe('history').value.events[0].tick,-20);
  assert.deepEqual(run.query().probe('position',{entity:first.events[0].place}).value,[4,0,-2]);
});

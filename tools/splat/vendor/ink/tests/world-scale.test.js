const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: K } = require('..').load();
const W = K.world;

test('local bounds edits refit an existing tree and topology changes rebuild it', () => {
  const tree=W.spatial.create();
  function set(id,x) {
    tree.set(id,{min:[x,0,0],max:[x,0,0],rank:id,value:x});
  }
  function hits(x) {
    const found=[];
    tree.overlap([x,0,0],[x,0,0],row=>found.push(row.id));
    return found;
  }
  for(let i=0;i<40;i++)set(i,i*3);
  assert.deepEqual(hits(12),[4]);
  set(4,13);
  assert.deepEqual(hits(12),[]);
  assert.deepEqual(hits(13),[4]);
  assert.equal(tree.work().builds,1);
  assert.equal(tree.work().updates,1);
  assert(tree.work().refits>0&&tree.work().refits<8);
  tree.remove(4);
  assert.deepEqual(hits(13),[]);
  assert.equal(tree.work().builds,2);
});

test('batched edits preserve sequential array operations and roll back draft changes', () => {
  const source = W.manifest({metadata:{items:[{label:'old'},{label:'spare'}],stable:{a:1}}});
  const edits = [
    {op:'set',path:'/metadata/items/1/label',value:'next'},
    {op:'remove',path:'/metadata/items/0'},
    {op:'test',path:'/metadata/items/0/label',value:'next'},
    {op:'merge',path:'/metadata',value:{label:'ok'}},
    {op:'set',path:'/metadata/items/0/label',value:'new'},
    {op:'set',path:'/metadata/items/0/label',value:'new'}
  ];
  const {world,paths} = W.apply(source,edits);
  assert.deepEqual(world.metadata.items,[{label:'new'}]);
  assert.deepEqual(source.metadata.items,[{label:'old'},{label:'spare'}]);
  assert.strictEqual(world.metadata.stable,source.metadata.stable);
  assert(Object.isFrozen(world.metadata.items[0]));
  assert.equal(paths.length,4);
  assert.throws(()=>W.apply(source,[...edits,{op:'remove',path:'/metadata/items/1'}]),/missing path/);
  assert.equal(source.metadata.items[1].label,'spare');
});

test('spatial queries refit moved poses and descendants and can read an older snapshot', () => {
  const run = W.runtime.create({dt:.1,entities:{
    rover:{sockets:{deck:[0,.5,0]}}, box:{anchor:{entity:'rover',socket:'deck'},position:[1,0,0]},
    strap:{parent:'box',position:[0,1,0]}, '123':{position:[-5,0,0]}, sign:{parent:123,position:[0,9,0]}
  },systems:{shop:{kind:'mechanics',config:{gravity:[0,0,0],drag:0,bodies:{
    rover:{half:[.3,.3,.3],position:[0,1,0],velocity:[2,0,0]}
  }}}}});
  const first=run.query(), ids=(query,point,radius=1e-9)=>query.spatial({point,radius}).map(row=>row.id);
  assert.deepEqual(ids(first,[1,2.5,0]),['strap']);
  run.schedule([
    {tick:1,action:'world/patch',args:{edits:[{op:'set',path:['entities',123,'position',0],value:-2}]}},
    {tick:2,action:'shop/fracture',args:{body:'rover',parts:2}}
  ]);
  run.step();
  const second=run.query();
  assert.deepEqual(ids(second,[1.2,2.5,0]),['strap']);
  assert.deepEqual(ids(second,[-2,0,0]),['123']);
  assert.deepEqual(ids(second,[-2,9,0]),['sign']);
  assert.deepEqual(ids(first,[1,2.5,0]),['strap']);
  assert.deepEqual(ids(second,[1.2,2.5,0]),['strap']);
  const fork=run.fork();
  fork.step();
  assert.deepEqual(ids(fork.query(),[0,1,0],4),['123']);
  assert.deepEqual(ids(second,[1.2,2.5,0]),['strap']);
  run.step();
  assert.deepEqual(run.query().spatial({point:[0,1,0],radius:4}).map(row=>row.id),['123']);
});

test('spatial alterations remain isolated across whole-table edits and rejected ticks', () => {
  const source={entities:{a:{position:[1,0,0]},b:{position:[20,0,0]}}};
  const run=W.runtime.create(source);
  const original=run.query(), hits={point:[0,0,0],radius:2};
  assert.deepEqual(original.spatial(hits).map(row=>row.id),['a']);
  run.schedule([{tick:1,action:'world/patch',args:{edits:[{
    op:'set',path:'/entities',value:{c:{position:[2,0,0]}}
  }]}}]);
  run.step();
  assert.deepEqual(run.query().spatial(hits).map(row=>row.id),['c']);
  run.schedule([
    {tick:2,action:'world/patch',args:{edits:[{op:'set',path:'/entities/c/position/0',value:6}]}},
    {tick:2,action:'world/patch',args:{edits:[{op:'remove',path:'/entities/absent'}]}}
  ]);
  assert.throws(()=>run.step(),/missing path/);
  assert.deepEqual(run.query().spatial(hits).map(row=>row.id),['c']);
  assert.deepEqual(original.spatial(hits).map(row=>row.id),['a']);
});

test('custom pose providers still resolve spatial positions without a dependency declaration', () => {
  const run=W.runtime.create({entities:{p:{position:[6,0,0]}},systems:{moving:{kind:'test-pose'}}},{implementations:{
    'test-pose':()=>({initial:()=>0,step:n=>n+1,pose:(n,id)=>id==='p'?[n,0,0]:null})
  }});
  const hits={point:[0,0,0],radius:.1};
  assert.equal(run.query().spatial(hits).length,1);
  run.step();
  assert.equal(run.query().spatial(hits).length,0);
});

test('broad-phase corrections preserve later contacts and all mounted poses', () => {
  const bodies={a:{half:[.5,.5,.5],position:[0,2,0]},b:{half:[.5,.5,.5],position:[.6,2,0]},
    c:{half:[.5,.5,.5],position:[-1.08,2,0]}, child:{half:[.3,.3,.3]}, grandchild:{half:[.3,.3,.3]}};
  const joints={mount:{kind:'fixed',parent:'a',child:'child',offset:[0,0,.25]},
    hinge:{kind:'hinge',parent:'child',child:'grandchild',offset:[0,0,1.4],speed:.3}};
  const make=extra=>W.runtime.create({systems:{shop:{kind:'mechanics',config:{
    gravity:[0,0,0],bodies:{...bodies,...extra},joints
  }}}});
  const scan=make({});
  const distant=Object.fromEntries(Array.from({length:36},(_,i)=>[
    'distant'+i,{half:[.5,.5,.5],fixed:true,position:[100+i,2,0]}
  ]));
  const indexed=make(distant);
  for(let tick=1;tick<=8;tick++){
    scan.step();
    indexed.step();
    const a=scan.view().states.shop,b=indexed.view().states.shop;
    for(const key of Object.keys(bodies))assert.deepEqual(b.bodies[key],a.bodies[key]);
    assert.deepEqual(b.joints,a.joints);
    if(tick===1)assert(a.bodies.c.position[0]<-1.08);
  }
});

test('indexed support and signed clearance match scans after fracture and across old views', () => {
  const bodies={second:{half:[.7,.4,.6],position:[0,1,0],turn:.61,fixed:true},
    first:{half:[.7,.4,.6],position:[0,1,0],turn:.61,fixed:true},
    block:{half:[.3,.6,.5],position:[1.25,1,0],turn:.8,fixed:true}};
  const far=Object.fromEntries(Array.from({length:42},(_,i)=>[
    'extra'+i,{half:[.25,.5,1],position:[20+i,1,2],fixed:true}
  ]));
  const make=extra=>W.runtime.create({systems:{shop:{kind:'mechanics',config:{bodies:{...bodies,...extra}}}}});
  const scan=make({}), indexed=make(far);
  const a=scan.query(), b=indexed.query();
  assert.deepEqual(b.probe('clearance',[0,1,0]),{status:'ok',value:-.4,body:'second'});
  assert.equal(b.probe('clearance',[0,1,0],{exclude:'second'}).body,'first');
  function compare(left,right) {
    for(let i=0;i<33;i++){
      const point=[Math.sin(i)*2,.9+i/60,Math.cos(2*i)*1.5];
      assert.deepEqual(right.probe('clearance',point),left.probe('clearance',point));
      assert.deepEqual(right.probe('support',point,{high:2,low:0}),left.probe('support',point,{high:2,low:0}));
    }
  }
  compare(a,b);
  for(const run of [scan,indexed]){
    run.schedule([{tick:1,action:'shop/fracture',args:{body:'block',parts:3,impulse:[0,.1,0]}}]);
    run.advance(3);
  }
  compare(scan.query(),indexed.query());
  compare(a,b);
  compare(scan.query(),indexed.query());
  function sheared(run) {
    const checkpoint=JSON.parse(JSON.stringify(run.checkpoint()));
    checkpoint.states.shop.bodies.second.rotation=[1,.2,0,0,1,0,0,0,1];
    return W.runtime.create(checkpoint.world,{checkpoint}).query();
  }
  compare(sheared(scan),sheared(indexed));
});

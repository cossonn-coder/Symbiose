const test=require('node:test');
const assert=require('node:assert/strict');
const kit=require('..').load(), {KIT:{world:W}}=kit;
const yard=require('../examples/world-hydraulic-yard.json');
const commands=require('../examples/world-hydraulic-yard.commands.json');

const clone=value=>JSON.parse(JSON.stringify(value));
const near=(a,b,tolerance=1e-8)=>assert.ok(Math.abs(a-b)<=tolerance,`${a} differs from ${b}`);
const network=(nodes,pipes,extra={})=>({kind:'pipe-network',config:{nodes,pipes,...extra}});
const input=(tick,pin,value)=>({tick,action:'world/input',args:{port:'network/'+pin,value}});
const probe=(run,field,args={},target={})=>run.query().probe(field,target,args).value;
const stock=(run,node)=>probe(run,'network/nodes',{node}).volume;
const pipe=(run,pipe)=>probe(run,'network/pipes',{pipe});
const mass=run=>probe(run,'network/mass');

test('head drives gravity flow, a valve closes the edge, and boost can reverse it',()=>{
  const run=W.runtime.create({dt:.1,systems:{network:network({
    a:{capacity:3,elevation:2,initial:1},b:{capacity:3,elevation:0,initial:1}
  },{main:{from:'a',to:'b',conductance:2,maxFlow:.5}})}});
  run.schedule([input(2,'valve.main',0),input(3,'valve.main',1),input(3,'boost.main',-4)]);
  assert.equal(run.query().trace('network/flow',{entity:'a'},{to:'b'}).status,'blocked');
  run.step();
  near(stock(run,'a'),.95);
  near(stock(run,'b'),1.05);
  near(pipe(run,'main').flow,.5);
  near(probe(run,'network/nodes',{}, {entity:'a'}).pressure,.95/3*9810);
  assert.deepEqual(run.query().trace('network/flow',{entity:'a'},{to:'b'}).value.path,
    [{pipe:'main',from:'a',to:'b',flow:.5}]);
  run.step();
  near(stock(run,'a'),.95);
  near(pipe(run,'main').flow,0);
  run.step();
  near(stock(run,'a'),1);
  near(pipe(run,'main').flow,-.5);
  assert.equal(run.query().trace('network/flow',{entity:'b'},{to:'a'}).status,'ok');
  near(mass(run).error,0);
});

test('check valves, capacity limits and competing leaks conserve fluid under stiff flow',()=>{
  const run=W.runtime.create({dt:.2,systems:{network:network({
    source:{capacity:2,initial:1.7,elevation:5},small:{capacity:.3,initial:.26},
    large:{capacity:2,initial:.2},blocked:{capacity:1,initial:.4}
  },{
    full:{from:'source',to:'small',conductance:1e6,oneWay:true},
    open:{from:'source',to:'large',conductance:1e6,oneWay:true},
    reverse:{from:'blocked',to:'source',conductance:100,oneWay:true}
  },{leaks:{crack:{node:'source',conductance:1e6,outsideHead:0}}})}});
  run.step();
  assert.ok(pipe(run,'full').flow>0&&pipe(run,'open').flow>0);
  near(pipe(run,'reverse').flow,0);
  near(stock(run,'blocked'),.4);
  const loss=probe(run,'network/leaks',{leak:'crack'}).flow*.2;
  assert.ok(loss>0);
  near(mass(run).leaked,loss);
  assert.ok(run.events.some(row=>row.kind==='pipe-leak-start'&&row.leak==='crack'));
  run.schedule([input(2,'leak.crack',0)]);
  run.step();
  assert.ok(run.events.some(row=>row.kind==='pipe-leak-stop'));
  for(let i=0;i<30;i++)run.step();
  near(mass(run).leaked,loss);
  near(mass(run).volume+loss,2.56);
  near(mass(run).error,0);
  assert.ok(Object.values(probe(run,'network/nodes')).every(row=>row.volume>=0&&row.volume<=row.capacity));
});

test('a loaded piston stalls, then meters its swept volume in both directions',()=>{
  const run=W.runtime.create({dt:.1,systems:{network:network({
    high:{capacity:3,initial:2,precharge:2},low:{capacity:3}
  },{cylinder:{from:'high',to:'low',conductance:8,piston:{area:.5,stroke:.4,load:20000}}})}});
  run.schedule([input(2,'load.cylinder',0),input(6,'boost.cylinder',-6)]);
  run.step();
  near(pipe(run,'cylinder').piston.position,0);
  near(stock(run,'low'),0);
  run.step();
  near(pipe(run,'cylinder').piston.position,.4);
  near(pipe(run,'cylinder').piston.speed,4);
  near(stock(run,'low'),.2);
  run.advance(5);
  near(pipe(run,'cylinder').flow,0);
  run.step();
  near(pipe(run,'cylinder').piston.position,0);
  near(stock(run,'low'),0);
  near(mass(run).volume,2);
});

test('pond, network, lift and irrigation exchange actual volume and replay exactly',()=>{
  const run=W.runtime.create(yard);
  run.schedule(commands);
  assert.equal(probe(run,'river/surface-height',{},[2.6,0,.2]),.13);
  run.advance(48);
  near(pipe(run,'lift').piston.position,.94);
  near(run.view().states.rig.bodies['lift-platform'].position[1],1.92);
  const {intake,irrigation}=probe(run,'network/boundaries');
  assert.ok(intake.flow>0&&irrigation.flow<0);
  assert.ok(irrigation.receipt.applied>0&&probe(run,'river/depth',{},[2.6,0,.2])>.25);
  const pressure=probe(run,'network/nodes',{node:'header'}).pressure;
  const branch=run.fork();
  branch.schedule([input(71,'leak.gasket',0)]);
  run.advance(94);
  branch.advance(94);
  assert.ok(probe(run,'network/nodes',{node:'header'}).pressure<pressure);
  assert.ok(mass(run).leaked>.3);
  near(mass(branch).leaked,0);
  const river=probe(run,'river/mass');
  near(mass(run).volume+river.volume+mass(run).leaked,river.initial+mass(run).initial);
  near(mass(run).imported,river.sent);
  near(mass(run).exported,river.received);
  near(mass(run).error,0);
  assert.deepEqual(clone(W.runtime.replay(clone(run.recording())).checkpoint()),clone(run.checkpoint()));
  const checkpoint=clone(run.checkpoint()), resumed=W.runtime.create(checkpoint.world,{checkpoint});
  resumed.advance(110);
  run.advance(110);
  assert.deepEqual(clone(resumed.checkpoint()),clone(run.checkpoint()));
});

test('yard water renders from the solver cells and stays inside the banks',()=>{
  const run=W.runtime.create(yard);
  const column=(x,z)=>run.query().probe('river/water',[x,0,z]);
  const rays=(frame,x,z)=>frame.water.raySegments([x,2,z],[0,-1,0],4);
  const build=()=>W.visual(kit,run.view(),run.query());
  const before=build();
  assert.equal(column(-2.38,.2).status,'dry');
  assert.deepEqual(rays(before,-2.38,.2),[]);
  const inside=column(-2.42,.2).value;
  const [[enter,leave]]=rays(before,-2.42,.2);
  near(2-enter,inside.surface,1e-6);
  near(2-leave,inside.bed,1e-6);
  assert.deepEqual(rays(before,-4.12,.2),[]);
  assert.deepEqual(rays(before,2.61,.2),[]);
  run.advance(70);
  const running=build(), outlet=pipe(run,'irrigation').points.at(-1);
  assert.equal(column(outlet[0],outlet[2]).status,'ok');
  assert.ok(outlet[1]<column(outlet[0],outlet[2]).value.surface);
  assert.ok(rays(running,3.9,.2).length);
  assert.deepEqual(rays(running,4.05,.2),[]);
});

test('boundary receipts show partial, blocked and closed transfers on a slower schedule',()=>{
  const config={boundaries:{supply:{node:'tank',account:'source/header',head:10,conductance:10,maxFlow:8}}};
  const world={dt:.1,systems:{
    network:{...network({tank:{capacity:1}}, {},config),schedule:{every:3}},
    source:{kind:'store',config:{accounts:{header:{resource:'water',units:'world^3',initial:2}}}}
  }};
  const run=W.runtime.create(world);
  run.schedule([input(7,'boundary.supply',0)]);
  run.advance(2);
  assert.equal(probe(run,'network/boundaries',{boundary:'supply'}).receipt,null);
  run.step();
  const supply=()=>probe(run,'network/boundaries',{boundary:'supply'});
  assert.equal(supply().receipt.status,'partial');
  near(supply().flow,1/.3);
  near(stock(run,'tank'),1);
  near(probe(run,'world/account',{account:'source/header'}).balance,1);
  run.advance(6);
  assert.deepEqual(supply().receipt.limitedBy,['destination']);
  near(supply().flow,0);
  run.advance(9);
  assert.equal(supply().receipt,null);
  assert.equal(supply().opening,0);
  world.systems.source.config.accounts.header.units='J';
  assert.throws(()=>W.runtime.create(world),/Incompatible transfer accounts/);
});

test('invalid topology, piston and field bindings fail validation',()=>{
  assert.throws(()=>W.runtime.create({systems:{network:network({a:{capacity:2}},
    {bad:{from:'a',to:'a',conductance:1}})}}),/Invalid pipe bad/);
  assert.throws(()=>W.runtime.create({systems:{network:network({a:{capacity:2},b:{capacity:1}},
    {bad:{from:'a',to:'b',conductance:1,piston:{area:.1,stroke:1,position:2}}})}}),/Invalid hydraulic piston/);
  const wrong=clone(yard);
  wrong.systems.network.config.boundaries.intake.headField='river/flow';
  assert.throws(()=>W.runtime.create(wrong),/numeric head field/);
});

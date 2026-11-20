const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT:{world:W,V}}=require('..').load();
const workshop=require('../examples/world-routed-workshop.json');
const commands=require('../examples/world-routed-workshop.commands.json');

const packed=value=>JSON.parse(JSON.stringify(value));
const read=(run,link)=>run.query().probe('routes/links',{}, {link}).value;
const port=(run,port)=>run.query().probe('world/signal',{}, {port}).value;
const close=(a,b,tolerance=1e-7)=>assert.ok(Math.abs(a-b)<=tolerance,`${a} differs from ${b}`);
const routes=(links,schedule)=>({kind:'routed-links',config:{links},...(schedule&&{schedule})});
const input=(tick,port,value)=>({tick,action:'world/input',args:{port,value}});
const action=(tick,action,link,args={})=>({tick,action:'routes/'+action,args:{link,...args}});

test('a moving machine snaps its hose and belt while separate signals and energy still get through',()=>{
  const run=W.runtime.create(workshop);
  const installed=read(run,'hose');
  close(installed.length-installed.distance,.4);
  const long=installed.paths.flatMap(path=>path.slice(1).map((p,i)=>V.dist(p,path[i])))
    .reduce((sum,n)=>sum+n,0);
  close(long,installed.length,1e-6);
  const loop=read(run,'belt');
  assert.deepEqual(loop.points[0],loop.points.at(-1));
  run.schedule(commands);
  run.advance(21);
  assert.equal(read(run,'hose').status,'taut');
  assert.deepEqual(run.query().trace('routes/route',{entity:'hose'}).value,read(run,'hose'));
  close(port(run,'rig/speed.follower'),3.9);
  close(port(run,'rig/external-load.motor'),3.6);
  run.advance(22);
  const filled=run.view().states.trolley.coolant;
  close(read(run,'hose').transfer.applied,.045);
  run.step();
  assert.equal(read(run,'hose').broken.reason,'tension');
  assert.equal(read(run,'hose').transfer,undefined);
  const gap=read(run,'hose');
  assert.equal(gap.paths.length,3);
  assert.ok(V.dist(gap.paths[1].at(-1),gap.paths[2][0])>gap.radius*4);
  close(run.view().states.trolley.coolant,filled);
  run.advance(40);
  assert.equal(read(run,'belt').broken.tick,27);
  assert.equal(port(run,'rig/speed.follower'),0);
  assert.equal(port(run,'rig/external-load.motor'),0);
  assert.equal(port(run,'routes/out.signal'),true);
  close(run.view().states.trolley.charge,32);
  close(run.view().states.trolley.coolant+run.query().probe('basin/mass').value.volume,6.25);
  close(run.view().states.trolley.charge+run.view().states.battery.charge,88);
  assert.deepEqual(run.history.filter(e=>e.kind==='routed-link-break').map(e=>[e.link,e.tick]),[['hose',23],['belt',27]]);
  const saved=packed(run.checkpoint()), fork=run.fork();
  fork.schedule([action(41,'repair','hose',{length:8})]);
  fork.step();
  close(read(fork,'hose').transfer.applied,.045);
  assert.equal(read(run,'hose').status,'broken');
  assert.deepEqual(packed(W.runtime.replay(packed(run.recording())).checkpoint()),saved);
});

test('installed slack uses the original posed sockets even if the machine moves on the first tick',()=>{
  const source={dt:.1,entities:{cart:{sockets:{plug:[0,0,0]}}},systems:{
    rig:{kind:'mechanics',config:{bodies:{cart:{half:[.2,.2,.2]}},joints:{
      slide:{kind:'slider',child:'cart',anchor:[1,1,0],at:1,speed:10,mode:'position',axis:[1,0,0]}
    }}},
    routes:routes({wire:{from:[0,1,0],to:{entity:'cart',socket:'plug'},slack:.15,breakStrain:.2}})
  }};
  const run=W.runtime.create(source);
  close(read(run,'wire').length,2.15);
  run.schedule([input(1,'rig/drive.slide',2)]);
  run.step();
  assert.equal(read(run,'wire').status,'over-limit');
  run.step();
  assert.equal(read(run,'wire').broken.reason,'strain');
  assert.equal(read(run,'wire').broken.tick,2);
});

test('cut, repair, payout and rerouting control typed event delivery across checkpoints',()=>{
  const run=W.runtime.create({dt:.1,systems:{routes:routes({wire:{from:[0,2,0],to:[2,2,0],length:2.4,
    breakTension:120,carry:{kind:'signal',type:'event'}}})}});
  const pulse=[{type:'ping',sequence:1}];
  run.schedule([input(1,'routes/in.wire',pulse),action(2,'cut','wire',{segment:0,fraction:.25}),
    input(2,'routes/in.wire',pulse),action(3,'repair','wire'),action(3,'reroute','wire',{guides:[[1,3,0]]}),
    action(3,'pay-out','wire',{length:3.1}),input(3,'routes/in.wire',pulse),input(4,'routes/enable.wire',false)]);
  run.step();
  assert.deepEqual(port(run,'routes/out.wire'),pulse);
  run.step();
  assert.deepEqual(port(run,'routes/out.wire'),[]);
  assert.equal(read(run,'wire').broken.fraction,.25);
  assert.equal(read(run,'wire').paths.length,2);
  const saved=packed(run.checkpoint()), fork=W.runtime.create(saved.world,{checkpoint:saved});
  run.step();fork.step();
  assert.deepEqual(port(run,'routes/out.wire'),pulse);
  assert.deepEqual(read(run,'wire').points,[[0,2,0],[1,3,0],[2,2,0]]);
  assert.deepEqual(run.events.map(row=>row.kind),['routed-link-repair','routed-link-reroute','routed-link-length']);
  assert.deepEqual(packed(fork.checkpoint()),packed(run.checkpoint()));
  run.step();
  assert.deepEqual(port(run,'routes/out.wire'),[]);
  assert.equal(read(run,'wire').status,'disabled');
});

test('a taut route applies socket forces and moments, and a cut releases them',()=>{
  const run=W.runtime.create({dt:.1,entities:{cart:{sockets:{pull:[0,.4,0]}}},systems:{
    rig:{kind:'mechanics',config:{drag:0,ground:-5,gravity:[0,0,0],routedLoads:['routes/reactions'],bodies:{
      cart:{position:[2,1,0],half:[.3,.3,.3],mass:2}
    }}},routes:routes({tow:{from:[0,1,0],to:{entity:'cart',socket:'pull'},length:1,stiffness:20}})
  }});
  const [load]=run.query().probe('routes/reactions').value;
  assert.deepEqual(load.point,[2,1.4,0]);
  close(V.len(load.force),read(run,'tow').tension);
  run.step();
  const body=()=>run.view().states.rig.bodies.cart;
  assert.ok(body().velocity[0]<-.9&&body().angular[2]>0);
  const velocity=body().velocity;
  run.schedule([action(2,'cut','tow')]);
  run.step();
  assert.deepEqual(body().velocity,velocity);
  assert.deepEqual(run.query().probe('routes/reactions').value,[]);
});

test('drives reflect ratio-adjusted load and report excess torque or a loose belt',()=>{
  const belt={from:[0,1,0],to:[2,1,0],length:1.9,carry:{kind:'drive',ratio:-.5,capacity:3,engageTension:5}};
  const run=W.runtime.create({dt:.1,systems:{routes:routes({belt})}});
  run.schedule([input(1,'routes/speed.belt',8),input(1,'routes/load.belt',2),input(2,'routes/load.belt',4),
    action(3,'pay-out','belt',{length:2.1})]);
  run.step();
  close(port(run,'routes/speed-out.belt'),-4);
  close(port(run,'routes/load-out.belt'),1);
  run.step();
  assert.equal(port(run,'routes/speed-out.belt'),0);
  assert.equal(port(run,'routes/slipping.belt'),true);
  close(port(run,'routes/load-out.belt'),1.5);
  run.step();
  assert.equal(port(run,'routes/load-out.belt'),0);
  assert.equal(port(run,'routes/slipping.belt'),true);
});

test('slow routes post one capacity-limited transfer per solver update and validate binding types',()=>{
  const pack=(initial,max)=>({kind:'store',config:{accounts:{charge:{resource:'energy',units:'J',initial,max}}}});
  const power={from:[0,1,0],to:[2,1,0],carry:{kind:'transfer',from:'source/charge',to:'sink/charge',rate:2}};
  const world={dt:.1,systems:{source:pack(1,1),sink:pack(0,.4),routes:routes({power},{every:3})}};
  const run=W.runtime.create(world);
  run.advance(2);
  assert.equal(read(run,'power').transfer,undefined);
  run.step();
  const receipt=read(run,'power').transfer;
  assert.equal(receipt.status,'partial');
  close(receipt.requested,.6);close(receipt.applied,.4);
  close(run.view().states.source.charge+run.view().states.sink.charge,1);
  assert.throws(()=>W.runtime.validate({...world,systems:{...world.systems,routes:routes({power:{...power,
    from:{entity:'missing',socket:'plug'}}})}}),/Unknown routed socket/);
  assert.throws(()=>W.runtime.validate({...world,systems:{...world.systems,routes:routes({power:{...power,
    carry:{...power.carry,rate:'2'}}})}}),/numeric rate/);
});

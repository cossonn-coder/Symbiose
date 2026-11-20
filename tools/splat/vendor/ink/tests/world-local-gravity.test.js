const test=require('node:test');
const assert=require('node:assert/strict');
const studio=require('..'), kit=studio.load(), {KIT:K}=kit, {V,M,world:W}=K;
const moon=require('../examples/world-pocket-moon.json');
const dock=require('../examples/world-rotating-dock.json');
const copy=value=>JSON.parse(JSON.stringify(value));
const near=(a,b,eps=1e-7)=>assert.ok(Math.abs(a-b)<=eps,`${a} differs from ${b}`);
const close=(a,b,eps=1e-7)=>a.forEach((n,i)=>near(n,b[i],eps));
const read=(run,name,at,args)=>run.query().probe(name,at,args).value;

test('analytic zones and authored vector fields expose common gravity channels',()=>{
  const world={systems:{
    gravity:{kind:'gravity',config:{
      frame:{kind:'uniform',acceleration:[0,-4,0]},
      regions:[{bounds:{min:[9,-4,-4],max:[18,4,4]},frame:{kind:'radial',center:[10,0,0],
        referenceRadius:2,strength:8,falloff:'inverse-square',buoyancy:1.4}}],
      accelerationField:'author/accel',upField:'author/up',buoyancyField:'author/float'
    }},
    author:{kind:'fields',config:{fields:{
      accel:{type:'vec3',units:'world/s^2',bounds:{min:[-3,-3,-3],max:[3,3,3]},default:[2,0,0]},
      up:{type:'vec3',units:'1',bounds:{min:[-3,-3,-3],max:[3,3,3]},default:[-2,1,0]},
      float:{type:'number',units:'1',bounds:{min:[-3,-3,-3],max:[3,3,3]},default:.7}
    }}}
  }};
  const run=W.runtime.create(world);
  close(read(run,'gravity/acceleration',[0,0,0]),[2,0,0]);
  close(read(run,'gravity/up',[0,0,0]),V.norm([-2,1,0]));
  near(read(run,'gravity/buoyancy',[0,0,0]),.7);
  close(read(run,'gravity/acceleration',[14,0,0]),[-2,0,0]);
  close(read(run,'gravity/up',[14,0,0]),[1,0,0]);
  near(read(run,'gravity/buoyancy',[14,0,0]),1.4);
  close(read(run,'gravity/acceleration',[50,0,0]),[0,-4,0]);
  world.systems.author.config.fields.accel.units='world/s';
  assert.throws(()=>W.runtime.create(world),/Incompatible gravity field/);
});

test('a rotating frame applies centrifugal acceleration and bends inertial motion',()=>{
  const run=W.runtime.create({dt:.2,systems:{
    ring:{kind:'gravity',config:{frame:{kind:'rotation',axis:[0,0,1],omega:2}}},
    rig:{kind:'mechanics',config:{gravityField:'ring/frame',drag:0,bodies:{
      probe:{position:[0,0,0],half:[.05,.05,.05],velocity:[1,0,0]}
    }}}
  }});
  const at=read(run,'ring/frame',[3,4,2]);
  close(at.acceleration,[12,16,0]);close(at.up,[-.6,-.8,0]);close(at.angularVelocity,[0,0,2]);
  run.step();
  const probe=read(run,'rig/bodies').probe;
  close(probe.velocity,[Math.cos(.8),-Math.sin(.8),0]);
  near(V.len(probe.velocity),1);
  assert.ok(probe.position[1]<0);
});

test('the existing flat-bottom capsule walks on a wall, jumps along its normal, and lands again',()=>{
  const controller=W.characters.create({tuning:{radius:.2,height:1,flatBottom:true,walkSpeed:1.5,jumpSpeed:2}});
  const environment={gravityAt:()=>({up:[1,0,0],acceleration:[-8,0,0]}),clearance:([x])=>x};
  let actor=controller.state({position:[.5,0,0],forward:[0,1,0]});
  for(let i=0;i<24;i++)actor=controller.step(actor,{moveWorld:[0,1,0]},1/60,environment).actor;
  assert.equal(actor.mode,'ground');
  assert.ok(actor.position[1]>.49);
  close(actor.up,[1,0,0]);near(actor.position[0],.5,1e-5);
  const leap=controller.step(actor,{jump:true},1/60,environment);
  assert.ok(leap.events.some(e=>e.type==='jump'));
  assert.ok(leap.actor.velocity[0]>0);
  actor=leap.actor;
  let landed=false;
  for(let i=0;i<44;i++){
    const result=controller.step(actor,{},1/60,environment);
    actor=result.actor;landed ||= result.events.some(e=>e.type==='land');
  }
  assert.ok(landed);near(actor.position[0],.5,1e-5);
  assert.equal(controller.fits(environment,actor.position),true);
});

test('a character and rover traverse a planet using the same authored frame and collision surface',()=>{
  const run=W.runtime.create(moon);
  run.advance(80);
  const actor=()=>read(run,'crew/actors').surveyor, rover=()=>read(run,'rig/bodies').rover;
  assert.equal(actor().mode,'ground');
  assert.ok(actor().position[1]<-1);
  close(actor().up,V.norm(actor().position));
  near(V.len(actor().position),2.1+.785/2,.004);
  run.advance(102);
  assert.equal(actor().mode,'air');
  assert.ok(V.len(actor().position)>2.69);
  run.advance(190);
  const up=V.norm(rover().position);
  assert.ok(V.dot(up,[0,1,0])<.7&&V.dot(up,M.app(rover().rotation,[0,1,0]))>.99);
  assert.ok(read(run,'rig/contacts').some(row=>row.support==='terrain'&&row.wheel==='drive'));
  assert.equal(actor().mode,'ground');
  const ray=run.query().trace('rig/ray',[3,0,0],{direction:[-1,0,0],distance:1});
  assert.equal(ray.value.id,'terrain');close(ray.value.point,[2.1,0,0]);
  assert.deepEqual(run.history.filter(e=>['character-jump','character-land'].includes(e.kind)).map(e=>e.kind),
    ['character-jump','character-land']);
  const pose=run.query().frame({entity:'surveyor'});
  close(M.app(pose.rotation,[0,1,0]),actor().up);
  assert.ok(W.query.fromScene(W.visual(kit,run.view(),run.query())).select({material:'agent'}).length>0);
  assert.deepEqual(copy(W.runtime.replay(copy(run.recording())).checkpoint()),copy(run.checkpoint()));
});

test('displaced fluid holds a hull at equilibrium in a sideways rotating dock',()=>{
  const run=W.runtime.create(dock);
  run.advance(240);
  const hull=read(run,'rig/bodies').hull;
  near(hull.position[0],3+(.42*(1.4+.08)/2.1),.00001);
  near(read(run,'tank/depth',hull.position),.296,.00001);
  near(V.len(hull.velocity),0,.00001);
  close(M.app(hull.rotation,[0,1,0]),[-1,0,0]);
  assert.ok(hull.position[0]<3.4);
});

test('the follow camera transports its orbit with the actor’s up',()=>{
  const camera=W.cameras.follow({localUp:true,tuning:{distance:3,pitch:0,height:.3}});
  const start=camera.start({position:[0,2,0],up:[0,1,0],mode:'ground'});
  const side=camera.step(start,{position:[2,0,0],up:[1,0,0],mode:'ground'},3);
  close(side.reference,[1,0,0]);
  near(side.focus[0],2.3,.0001);
  near(V.dot(side.pose.up,[1,0,0]),1);
  near(V.dist(side.pose.eye,side.focus),3);
  near(V.dot(side.pose.back,side.pose.right),0);
});

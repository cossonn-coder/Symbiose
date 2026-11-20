const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: { world: W, M } } = require('..').load();
const workshop = require('../examples/world-continuous-colliders.json');

const rig = (bodies,config={}) => W.runtime.create({dt:.1,systems:{rig:{kind:'mechanics',config:{
  ground:-4,gravity:[0,0,0],drag:0,bodies,...config
}}}});
const state = run => run.checkpoint().states.rig;
const close = (actual,expected,tolerance=1e-6) => assert.ok(Math.abs(actual-expected)<=tolerance,
  `${actual} is not within ${tolerance} of ${expected}`);
const sphere = radius => ({kind:'capsule',a:[0,0,0],b:[0,0,0],radius});
const packed = value => JSON.parse(JSON.stringify(value));

test('the workshop hits a thin stop while the wheel crosses a convex compound opening', () => {
  const run=W.runtime.create(workshop);
  run.step();
  const {impacts,limited}=run.query().probe('rig/impacts').value;
  assert.equal(limited,false);
  const hit=impacts.find(hit=>hit.a==='parcel');
  assert.equal(hit.b,'thin-stop');
  assert.deepEqual(hit.parts,[0,0]);
  assert.deepEqual(hit.normal,[1,0,0]);
  close(hit.at,.415);
  close(hit.speed,90);
  close(state(run).bodies.parcel.position[0],-.265);
  close(state(run).bodies.parcel.velocity[0],0);
  close(state(run).bodies.wheel.position[0],3.42);
  assert.equal(impacts.some(hit=>[hit.a,hit.b].includes('gate')),false);
  assert.deepEqual(packed(W.runtime.replay(packed(run.recording())).checkpoint()),packed(run.checkpoint()));

  const discrete=packed(workshop);
  discrete.systems.rig.config.continuous=false;
  const control=W.runtime.create(discrete);
  control.step();
  close(state(control).bodies.parcel.position[0],5);
});

test('old boxes opt in to relative sweeps between moving bodies', () => {
  const bodies={left:{position:[-2,1,0],half:[.2,.2,.2],velocity:[30,0,0]},
    right:{position:[2,1,0],half:[.2,.2,.2],velocity:[-30,0,0]}};
  const run=rig(bodies,{continuous:true}), legacy=rig(bodies);
  run.step();
  legacy.step();
  const hit=state(run).impacts[0];
  close(hit.at,.6);
  close(hit.speed,60);
  close(state(run).bodies.left.position[0],-.2);
  close(state(run).bodies.right.position[0],.2);
  close(state(run).bodies.left.velocity[0],0);
  close(state(legacy).bodies.left.position[0],1);
});

test('capsules and compounds use the same geometry for clearance, support and sweeps', () => {
  const gate={fixed:true,collider:{kind:'compound',parts:[
    {kind:'box',at:[0,0,-.45],half:[.1,.7,.12]},
    {kind:'box',at:[0,0,.45],half:[.1,.7,.12]}
  ]}};
  const post={fixed:true,position:[0,1,2],collider:{kind:'capsule',a:[0,-.3,0],b:[0,.3,0],radius:.2}};
  const run=rig({gate,post,wide:{position:[-2,0,0],velocity:[40,0,0],collider:sphere(.36)}});
  close(run.query().probe('rig/clearance',[0,0,0]).value,.33);
  close(run.query().probe('rig/clearance',[.3,1,2]).value,.1);
  const support=run.query().probe('rig/support',[0,1.5,2]).value[0];
  assert.equal(support.id,'post');
  assert.equal(support.part,0);
  close(support.y,1.5);
  run.step();
  assert.ok(state(run).impacts.some(hit=>hit.a==='gate'&&hit.b==='wide'));
  assert.ok(state(run).bodies.wide.position[0]<0);
  assert.equal(state(run).impactLimited,false);
});

test('contact iterations keep stacks supported by the plane and by another collider', () => {
  for(const platform of [false,true]){
    const floor=platform?{platform:{fixed:true,position:[0,-.1,0],half:[2,.1,2]}}:{};
    const loads=Object.fromEntries(Array.from({length:4},(_,i)=>['load-'+i,{
      half:[.4,.2,.36],position:[0,.2+i*.4,0]
    }]));
    const run=rig({...floor,...loads},{continuous:true,ground:platform?-4:0,gravity:[0,-9.81,0]});
    run.advance(16);
    const result=state(run);
    for(const [id,load] of Object.entries(loads)){
      close(result.bodies[id].position[1],load.position[1]);
      close(result.bodies[id].velocity[1],0);
    }
    assert.equal(result.impactLimited,false);
  }
});

test('wheels drive on a raised collider and report its support', () => {
  const run=rig({deck:{fixed:true,position:[0,.5,0],half:[3,.5,1]},
    wheel:{position:[0,1.19,0],collider:{kind:'capsule',a:[0,0,-.14],b:[0,0,.14],radius:.19}}},
  {contactEvents:true,forces:{drive:{kind:'wheel',body:'wheel',axis:[1,0,0],radius:.19,magnitude:2,input:1}}});
  run.step();
  assert.ok(state(run).bodies.wheel.position[0]>0);
  const [contact]=state(run).contacts;
  assert.equal(contact.support,'deck');
  close(contact.point[1],1);
});

test('colliders require a valid capsule and a closed, ordered convex shell', () => {
  const tetrahedron={kind:'convex',vertices:[[0,0,0],[1,0,0],[0,1,0],[0,0,1]],
    faces:[[0,2,1],[0,1,3],[0,3,2],[1,2,3]]};
  assert.doesNotThrow(()=>rig({shape:{collider:tetrahedron}}));
  assert.throws(()=>rig({shape:{collider:{...tetrahedron,vertices:[...tetrahedron.vertices,[0,-1,0]],
    faces:[...tetrahedron.faces.slice(0,-1),[1,2,4]]}}}),/convex|planar/i);
  const gate=workshop.systems.rig.config.bodies.gate.collider.parts[3];
  assert.throws(()=>rig({shape:{collider:{...gate,faces:gate.faces.slice(0,-1)}}}),/closed shell/);
  assert.throws(()=>rig({shape:{collider:sphere(0)}}),/Invalid capsule/);
  assert.throws(()=>rig({shape:{collider:null}}),/Expected a collider/);
});

test('a flat-bottom capsule lands on its overhanging rim and survives replay', () => {
  const collider={kind:'capsule',a:[0,-.6,0],b:[0,.3,0],radius:.3,flatBottom:true};
  const run=rig({ledge:{fixed:true,position:[-.5,-.1,0],half:[.5,.1,1]},
    runner:{position:[.24,2,0],velocity:[0,-30,0],collider}});
  run.step();
  const [{a,b,normal,at}]=state(run).impacts;
  assert.deepEqual([a,b],['ledge','runner']);
  close(normal[1],1);
  close(at,1.4/3);
  const body=state(run).bodies.runner;
  close(body.position[1],.6);
  close(body.velocity[1],0);
  close(W.colliders.distance(body,[.24,1.2,0]),0);
  close(W.colliders.distance(body,[.24,-.04,0]),.04);
  assert.deepEqual(packed(W.runtime.replay(packed(run.recording())).checkpoint()),packed(run.checkpoint()));
  assert.throws(()=>rig({shape:{collider:{...sphere(.3),flatBottom:true}}}),/distinct endpoints/);
});

test('a rotated flat capsule exposes a planar support across its base', () => {
  const body={id:'sole',material:'rubber',position:[1,2,0],rotation:M.rot([0,0,1],Math.PI),
    collider:{kind:'capsule',a:[0,-.6,0],b:[0,.3,0],radius:.3,flatBottom:true}};
  const bounds=W.colliders.geometry(body);
  close(bounds.max[1],2.6);
  close(bounds.min[1],1.4);
  for(const x of [.75,1,1.25]){
    const [hit]=W.colliders.columns(body,x,0,1,4);
    close(hit.y,2.6);
    close(hit.normal[1],1);
  }
});

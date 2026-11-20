const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT:K}=require('..').load();
const {motion,surface}=K.procedural,V=K.V;
const near=(a,b,e=1e-6)=>assert(Math.abs(a-b)<=e,a+' differs from '+b);

test('adaptive RK4 traces a closed current and stops before signed barriers',()=>{
  const vortex=(x,y,z)=>[-z,0,x],
    ring=motion.streamline(vortex,[1,0,0],{step:0.21,closeDistance:0.034,maxLength:7,tolerance:0.0001});
  assert.equal(ring.status,'closed');
  assert(ring.points.length>25);
  assert(ring.points.every(p=>Math.abs(Math.hypot(p[0],p[2])-1)<0.0003));
  const barrier=(x,y,z)=>Math.hypot(x,z)-0.2,
    blocked=motion.streamline(()=>[1,0,0],[-0.95,0,0],{step:0.45,obstacle:barrier,clearance:0.05,normalize:false});
  assert.equal(blocked.status,'blocked');
  assert(blocked.points.every(p=>barrier(...p)>=0.05-1e-10));
  assert(blocked.points.at(-1)[0]>-0.29);
  assert.equal(motion.streamline(vortex,[1,0,0],{maxChecks:2}).status,'budget');
});

test('analytic wakes have nonzero downstream curl, loop continuously and respect obstacle interiors',()=>{
  const obstacle=(x,y,z)=>Math.hypot(x,z)-0.5,
    wake=motion.obstacleWake(obstacle,{radius:0.5,flow:[1.04,0,0],length:4,circulation:1.8,period:4.2});
  assert.deepEqual(wake.velocity(0,0,0),[0,0,0]);
  const p=[2.8,0.12,0.28], a=wake.velocity(...p,1.3),b=wake.velocity(...p,1.3+wake.period);
  assert(V.dist(a,b)<1e-12);
  assert(Math.abs(wake.vorticity(...p,1.3)[1])>0.09);
  assert(V.dist(wake.velocity(-7,0,0,1.3),[1.04,0,0])<0.0001);
  assert(V.dist(wake.velocity(...p,0),wake.velocity(...p,-0.000001))<0.0001);
});

test('closed trajectories agree on position and derivative across nonuniform knots and period seams',()=>{
  const loop=motion.loopTrajectory([
    {at:0,point:[1,0,0],velocity:[0,0,3]}, {at:0.18,point:[0,0,1]},
    {at:0.62,point:[-1,0,0]}, {at:0.84,point:[0,0,-1]}
  ],{period:2.3});
  assert.deepEqual(loop.sample(0),loop.sample(2.3));
  assert.deepEqual(loop.sample(0),loop.sample(-2.3));
  assert(V.dist(loop.sample(-1e-7).point,loop.sample(1e-7).point)<1e-5);
  assert(V.dist(loop.sample(-1e-7).velocity,loop.sample(1e-7).velocity)<0.00002);
  for(const k of loop.points)assert(V.dist(loop.sample(k.at*loop.period).point,k.point)<1e-10);
});

test('tangent transport moves UVs and carries them with an independently deforming surface',()=>{
  const carrier=t=>({sample:([u,v])=>({p:[2*u+t,v,0],n:[0,0,1],du:[2,0,0],dv:[0,1,0],tangent:[1,0,0]})}),
    source=motion.surfaceAdvection(carrier,[{id:'dab',uv:[0.15,0.23],data:{palette:4}}],{
      velocity:()=>[0.7,0.22,90],step:0.04
    }), one=source.advance(0.9).particles[0];
  near(one.uv[0],0.465);
  near(one.uv[1],0.428);
  near(one.position[0],1.83);
  near(one.position[2],0);
  assert.deepEqual(one.normal,[0,0,1]);
  assert.equal(source.reset().time,0);
});

test('surface advection wraps cylinder seams and fails transactionally on invalid callbacks',()=>{
  const cylinder=surface.cylinder({id:'tube',origin:[0,0,0],height:1,radius:1}),
    engine=motion.surfaceAdvection(cylinder,[[0.94,0.45]],{
      velocity:(x,y,z)=>[-z,0,x],step:0.024
    });
  const out=engine.advance(0.62).particles[0];
  near(out.uv[0],(0.94+0.62/(2*Math.PI))%1,0.00002);
  near(Math.hypot(out.position[0],out.position[2]),1);
  const broken=motion.surfaceAdvection(cylinder,[[0.2,0.6]],{
    velocity:(x,y,z,t)=>t>0.04?[NaN,0,0]:[-z,0,x]
  });
  const saved=broken.snapshot();
  assert.throws(()=>broken.advance(0.3),/velocities/);
  assert.deepEqual(broken.snapshot(),saved);
});

const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT:K}=require('..').load();
const {motion}=K.procedural;
const sum=a=>a.reduce((x,y)=>x+y,0);
const near=(a,b,e=1e-7)=>assert(Math.abs(a-b)<=e,a+' differs from '+b);

test('staggered stable fluid projection keeps flow nearly divergence-free in a walled basin',()=>{
  const config={width:28,height:22,cell:0.09,origin:[-1.26,-0.99],pressureIterations:62,
    mask:(x,z)=>Math.hypot(x+0.12,z+0.1)>0.22,
    initial:(x,z)=>({density:Math.exp(-((x+0.65)**2+(z-0.2)**2)*16),velocity:[-0.35*z,0.35*x]})};
  const engine=motion.stableFluid(config), before=engine.snapshot(),
    input={force:(x,z)=>[-z*0.17,x*0.17]},
    after=engine.step(0.42,input), repeat=motion.stableFluid(config).step(0.42,input);
  assert(after.divergence.every(v=>Math.abs(v)<0.017));
  assert(after.density.every(d=>Number.isFinite(d)&&d>=0));
  assert.notDeepEqual(before.density,after.density);
  assert.deepEqual(after.density,repeat.density);
  assert(after.sample(-0.7,0.2).density>0.2);
  assert.equal(after.sample(-0.12,-0.1),null);
  before.density.fill(9);
  assert(engine.snapshot().density.every(d=>d<2));
});

test('stable fluids cannot advect visible density through a disconnected mask',()=>{
  const engine=motion.stableFluid({width:19,height:13,cell:0.1,
    mask:(x)=>Math.abs(x-0.95)>0.025,initial:x=>({density:x<0.9?1:0,velocity:[1.2,0]})});
  const state=engine.step(0.68,{diffusion:0.015,force:()=>[1.8,0]});
  assert(state.density.every((v,i)=>i%19<10||v===0));
  const saved=engine.snapshot();
  assert.throws(()=>engine.step(0.2,{force:()=>[NaN,0]}),/finite/);
  assert.deepEqual(engine.snapshot().density,saved.density);
  near(engine.snapshot().time,saved.time);
});

test('hydrostatic reconstruction leaves constant water level over a sloped bed at rest',()=>{
  const engine=motion.shallowWater({
    width:34,height:25,cell:0.13,origin:[-2.21,-1.625],
    terrain:(x,z)=>0.15*Math.sin(x*1.3)+0.08*Math.cos(z*1.9),
    initial:(x,z,y)=>0.32-y
  }), state=engine.step(0.64);
  assert(state.substeps>20);
  assert(state.vx.every(v=>Math.abs(v)<1e-10));
  assert(state.vz.every(v=>Math.abs(v)<1e-10));
  assert(state.level.every(y=>Math.abs(y-0.32)<1e-10));
  near(state.mass.error,0);
});

test('conservative flux carries a dam break into dry cells and accounts for rain and drainage',()=>{
  const engine=motion.shallowWater({
    width:38,height:20,cell:0.11,origin:[-2,-1.1],
    terrain:(x)=>0.075*x,initial:(x)=>x<-1?0.45:0
  }), before=engine.snapshot(), after=engine.step(0.7,{rain:0.01,drain:(x)=>x<-1.4?0.015:0});
  assert(after.depth.every(v=>Number.isFinite(v)&&v>=0));
  assert(after.vx.some(v=>Math.abs(v)>0.4));
  assert(after.sample(-0.4,0).depth>=0.05);
  assert.equal(before.sample(-0.4,0).depth,0);
  assert(after.mass.added>0 && after.mass.drained>0);
  near(after.mass.error,0,1e-9);
  near(after.mass.volume,sum(after.depth)*0.11**2);
  assert.throws(()=>engine.step(0.3,{rain:()=>-0.1}),/finite/);
  assert.deepEqual(engine.snapshot().depth,after.depth);
});

const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT:K}=require('..').load();
const prism=K.procedural.geometry.heightPrismPlanes;
const plan=[[0,0],[2,0],[2,1],[0,1]];
const lower=plan.map(([x,z])=>[x,.2*x,z]),upper=plan.map(([x,z])=>[x,.6+.3*z+.45*x,z]);
const inside=(p,planes)=>planes.every(({normal,offset})=>K.V.dot(normal,p)<=offset+1e-8);

test('a sloped prism uses the actual upper and lower planes in either winding',()=>{
  for(const [lo,hi] of [[lower,upper],[lower.slice().reverse(),upper.slice().reverse()]]){
    const planes=prism({lower:lo,upper:hi});
    assert.equal(planes.length,6);
    assert(planes.slice(0,4).every((p,i)=>p.kind==='side'&&p.edge===i));
    assert(inside([1,.6,.9],planes)&&inside([1,1.3,.9],planes));
    assert(!inside([1,.1,.9],planes));
    assert(!inside([1,1.3,.1],planes));
    assert(!inside([2.1,.9,.9],planes));
  }
});
test('invalid caps and disconnected or folded footprints reject',()=>{
  assert.throws(()=>prism({lower,upper:upper.map((p,i)=>i===2?[p[0],p[1]+.1,p[2]]:p)}),/planar/);
  const indices=[0,2,1,3];
  assert.throws(()=>prism({lower:indices.map(i=>lower[i]),upper:indices.map(i=>upper[i])}),/convex/);
  assert.throws(()=>prism({lower:upper,upper:lower}),/ordered/);
});

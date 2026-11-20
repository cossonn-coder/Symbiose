const assert=require('node:assert/strict');
const test=require('node:test');
const ink=require('..');
const { KIT:K, makeBuilder }=ink.load();
const { density:D, routes }=K.procedural;
const extent={ min:[-4,-2,-4],max:[4,5,4] };

test('path density accepts Ink splines and terrain routes, and tapers along world distance', () => {
  const path=K.anim.path([[-3,0,-3],[-1,0,1],[1.3,0,2.8],[3,0,3]],{ steps:7 });
  const mist=D.fromPath({ path,radius:.72,aspect:.38,feather:.2 });
  for (const fraction of [.12,.42,.79]) {
    const [x,y,z]=path.at(path.length*fraction).p;
    assert(mist.sample(x,y,z)>.95);
    assert.equal(mist.sample(x,y+.5,z),0);
  }
  assert.equal(mist.sample(-3,0,3),0);
  const route=routes.polyline([[-4,0,0],[-3.7,0,0],[1,0,0],[5,0,0]]);
  const taper=D.fromPath({ path:route,radius:[.21,1.12],feather:.12 });
  assert.equal(taper.sample(-3.9,0,.51),0);
  assert(taper.sample(4.5,0,.63)>.8);
  assert.throws(()=>D.fromPath({ points:[[0,0,0],[0,0,0]] }), /route length/);
  assert.throws(()=>D.fromPath({ path,points:path.points }), /one path/);
});

test('terrain mist follows sampled ground and pools below an authored ceiling', () => {
  const terrain={ heightAt:x=>x*x*.4 };
  const field=D.fromTerrain({ bounds:extent,terrain,depth:2,ceiling:1.4,feather:.2 });
  assert(field.sample(0,.6,0)>.9);
  assert(field.sample(1,.9,0)>.9);
  assert.equal(field.sample(1,.3,0),0);
  assert.equal(field.sample(3,3.8,0),0);
  assert.equal(field.sample(0,1.5,0),0);
  const grid={ resolution:[3,2],values:[2,0,2,2,0,2] };
  const valley=D.fromTerrain({ bounds:extent,terrain:grid,depth:1,ceiling:1.8,feather:.18 });
  assert(valley.sample(2,1.5,0)>.9);
  assert.equal(valley.sample(2,.9,0),0);
  assert.equal(valley.sample(-4,2.1,0),0);
  assert.throws(()=>D.fromTerrain({ bounds:extent,terrain:{ ...grid,values:[0] } }), /height grid/);
  const watershed=D.fromTerrain({bounds:extent,terrain:{sample:()=>({ terrainHeight:1.25 })},depth:.8});
  assert(watershed.sample(0,1.6,0)>.9);
});

test('shaped atmosphere reuses the ordinary volume integrator and preserves ordinary fog when toggled', () => {
  const plume=K.atmosphere.shaped({source:{type:'sdf',bounds:extent,
    field:(x,y,z)=>Math.hypot(x,y-1,z)-1.15 },density:.65,color:'#a6b9ca',lit:false });
  const coast=K.atmosphere.box({ min:[-5,-5,-5],max:[5,5,5],density:.035,color:'#b69c90' });
  const full=K.atmosphere.prepare([coast,plume]), base=K.atmosphere.prepare([coast]);
  const hit=K.atmosphere.trace(full,[0,1,3],[0,0,-1],7);
  assert(hit[3]<K.atmosphere.trace(base,[0,1,3],[0,0,-1],7)[3]-.3);
  const miss=K.atmosphere.trace(full,[2,1,3],[0,0,-1],7), clear=K.atmosphere.trace(base,[2,1,3],[0,0,-1],7);
  assert(miss.every((value,i)=>Math.abs(value-clear[i])<1e-12));
  const B=makeBuilder(1,[0x2a4263]);
  const world=B.finish({ cam:{target:[0,1,0],dist:5,yaw:0,pitch:0}, atmosphere:[coast], shapedAtmosphere:[plume] });
  const view={w:84,h:52,px:1,raw:true};
  const on=ink.render(world,view).rgb, off=ink.render(world,{ ...view,shapedAtmosphere:false }).rgb;
  const cleared=ink.render(world,{...view,atmosphere:false}).rgb;
  assert.notDeepEqual(on,off);
  assert.notDeepEqual(off,cleared);
  assert.deepEqual(off,ink.render({...world,shapedAtmosphere:undefined},view).rgb);
  const replacement=[{source:{type:'path',points:[[-1,1,0],[1,1,0]],radius:.6},density:1.2,color:'#e9efe8'}];
  assert.notDeepEqual(ink.render(world,{...view,shapedAtmosphere:replacement}).rgb,on);
});

test('one 3D shape supplies cloud depth, projected shadows and all three baked views', () => {
  let active=true;
  const field=D.bounded({
    bounds:extent,
    sample:(x,y,z,time)=>active&&Math.hypot(x,y-(1+time),z)<1.2 ? 1 : 0
  });
  const cloud=K.clouds.asset({ field,density:1.6,bakeTime:1.25,velocity:[1,0],resolution:[20,20],
    densityResolution:[22,26,22],color:'#dee6ec' },{resolution:32});
  active=false;
  const sky=K.clouds.shadowSettings({ strength:1,softness:0,direction:[0,1,0] });
  const same=cloud.frame(0,sky), drift=cloud.frame(2,sky);
  assert(same.coverage(0,0)>.88 && same.shadow(0,-3,0)<.12);
  assert(drift.coverage(2,0)>.88 && drift.coverage(0,0)<.05);
  for (const mode of ['card','impostor','volume']) {
    const eye=[0,2.25,10];
    const view=cloud.frame(0,undefined,undefined,undefined,mode).view(eye);
    assert(view.trace(eye,[0,0,-1],0,18,[0,0,0,1])[3]<.25,mode);
    assert.equal(view.trace(eye,[0,0,-1],0,6,[0,0,0,1])[3],1);
  }
  const lower=cloud.frame(0,undefined,undefined,undefined,'volume').view([0,-.5,10]);
  assert.equal(lower.trace([0,-.5,10],[0,0,-1],0,18,[0,0,0,1])[3],1);
  assert.throws(()=>K.clouds.compile({ field, thickness:3 }),/derives/);
});

const {test}=require('node:test');
const assert=require('node:assert/strict');
const studio=require('..');
const {TexturedSurface:T,SpriteSurface:A,makeBuilder}=studio.load();

test('height queries and normals lie on the rendered triangles, including seams and clamped bounds',()=>{
  const h=T.heightfield({bounds:[2,6,-3,1],segments:[2,2],height:(x,z)=>x*z*.2});
  for(const [u,v] of [[0,0],[.25,.25],[.5,.5],[.75,.24],[1,1]]){
    const p=h.sample(u,v);
    assert(Math.abs(h.height(p.point[0],p.point[2])-p.point[1])<1e-6);
    assert(Math.abs(Math.hypot(...p.normal)-1)<1e-6);
    assert(p.normal[1]>0);
  }
  assert.equal(h.height(-100,100),h.height(2,1));
  assert.throws(()=>h.height(NaN,0),RangeError);
  assert.throws(()=>T.grid({segments:[1000,1000],point:()=>[0,0,0]}),/budget/);
  assert.throws(()=>T.heightfield({bounds:[0,1,0,1],height:()=>Infinity}),/finite/);
  const cached=T.heightfield({bounds:[0,1,0,1],segments:[1,1],height:Float32Array.of(1,2,3,4)});
  assert.equal(cached.height(0,1),1);
  assert.equal(cached.height(1,0),4);
});

test('profile sweeps join exactly and share piecewise triangle queries with attachments',()=>{
  const path={length:2*Math.PI,at:t=>({p:[Math.cos(t),.2*Math.sin(t),Math.sin(t)],tan:[-Math.sin(t),.2*Math.cos(t),Math.cos(t)]})};
  const s=T.sweep({path,closed:true,segments:32,profile:[[-.2,0],[0,.1],[.2,0]]});
  for(let k=0;k<9;k++)assert.equal(s.points[k],s.points[s.points.length-9+k]);
  assert(s.sample(.5,.25).normal.every(Number.isFinite));
  const flat=T.sweep({path:{length:2,at:d=>({p:[0,0,d],tan:[0,0,1]})},profile:[[-1,0],[1,0]]});
  assert(flat.sample(.5,.5).normal[1]>.99);
  const q=T.grid({segments:[1,1],point:(u,v)=>[u,u*v,v]});
  assert.deepEqual(q.sample(.5,.5).point,[.5,0,.5]);
  assert.throws(()=>T.sweep({path:{length:1,at:()=>({p:[0,0,0],tan:[0,1,0]})},profile:[[-1,0],[1,0]]}),/perpendicular/);
});

test('atlas meshes preserve legacy face UVs and paint failures never consume atlas space',()=>{
  const a=A.make(4,4);
  assert.throws(()=>a.face([0,0,0],[1,0,0],[0,1,0],4,4,()=>{throw Error('paint failed');}),/paint failed/);
  a.face([0,0,0],[1,0,0],[0,1,0],4,4,(i,j)=>i===j?0xff0000:undefined);
  const atlas=a.finish();
  assert.deepEqual([...atlas.vertices.slice(0,5)],[0,1,0,.5,.5]);
  assert.deepEqual([...atlas.vertices.slice(5,10)],[1,1,0,3.5,.5]);
  assert.equal(atlas.height,4);
  assert.equal(atlas.pixels[3],255);assert.equal(atlas.pixels[7],0);
  assert.throws(()=>a.mesh({points:[0,0,0],uvs:[0,2],triangles:[0,0,0]},1,1,()=>0),/UVs/);
});

test('CPU render supports entirely textured scenes, transparent cutouts and mixed splat occlusion',()=>{
  const a=A.make(32),b=makeBuilder(3,[0x101010,0x0000ff]);
  a.face([-1,-1,0],[2,0,0],[0,2,0],16,16,()=>0xff0000);
  const world=b.finish({spriteSurfaces:a.finish(),cam:{target:[0,0,0],dist:5,yaw:0,pitch:0},radius:4});
  const at=frame=>Array.from(frame.rgb.slice((Math.floor(frame.h/2)*frame.w+Math.floor(frame.w/2))*3,(Math.floor(frame.h/2)*frame.w+Math.floor(frame.w/2))*3+3));
  assert.deepEqual(at(studio.render(world,{w:80,h:80,raw:true,px:1})),[255,0,0]);
  assert.deepEqual(at(studio.render(world,{w:80,h:80,raw:true,px:1,spriteSurfaces:false})),[16,16,16]);
  b.iso(0,0,-.5,.15,b.P[1],4);
  const behind=b.finish({spriteSurfaces:world.spriteSurfaces,cam:world.cam,radius:world.radius});
  assert.deepEqual(at(studio.render(behind,{w:80,h:80,raw:true,px:1})),[255,0,0]);
  behind.data[2]=.5;
  const front=at(studio.render(behind,{w:80,h:80,raw:true,px:1}));
  assert(front[2]>150&&front[0]<80);
  const hole=A.make(32);hole.face([-1,-1,0],[2,0,0],[0,2,0],16,16,(x,y)=>x>5&&x<11&&y>5&&y<11?undefined:0xff0000);
  behind.spriteSurfaces=hole.finish();behind.data[2]=-.5;
  assert(at(studio.render(behind,{w:80,h:80,raw:true,px:1}))[2]>150);
});

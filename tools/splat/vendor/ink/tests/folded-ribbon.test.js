const test=require('node:test'),assert=require('node:assert/strict'),{KIT:K}=require('..').load();
const P=K.procedural||K.authoring,V=K.V;
const ring=[[-1,0,1],[1,0,1],[1,0,-1],[-1,0,-1]];
const frames=ring.map((a,i)=>{
  const b=ring[(i+1)%ring.length],up=[0,1,0],normal=V.norm(V.cross(V.sub(b,a),up));
  return{key:String(i),a,b,up,normal};
});
const near=(a,b)=>assert(V.dist(a,b)<1e-6,`[${a}] differs from [${b}]`);

test('folded ribbon meets exactly at corners and inverts an offset raised strip',()=>{
  const ribbon=P.foldedRibbon.compile(frames,{origin:1.9,offset:.12}),patch=ribbon.region(-.85,1.15);
  assert.equal(ribbon.length,8);
  assert(ribbon.inset>.75);
  assert.deepEqual(patch.bands.map(b=>b.key),['0','1']);
  const [left,right]=patch.bands,seam=left.max;
  for(const z of [-.5,0,.3])near(left.map([seam,.8,z]),right.map([seam,.8,z]));
  for(const x of [-.7,-.1,.1,.5,1])for(const z of [-.55,-.1,.5]){
    const q=[x,1.2,z],p=patch.map(q);
    near(patch.project(p).q,q);
    const b=patch.bandAt(x),result=b.normal(q,[0,0,1]),axis=b.basis(q);
    assert(Math.abs(V.dot(result,axis.run))<1e-7);
  }
  assert.throws(()=>ribbon.region(-5,5),/perimeter/);
});

test('mesh faces crossing a fold clip onto both charts with interpolated UV and ownership',()=>{
  const patch=P.foldedRibbon.compile(frames,{origin:2}).region(-.9,.9);
  const b=P.geometry.builder();
  b.quad([-.75,0,0],[.75,0,0],[.75,1,0],[-.75,1,0],
    {owner:'part',surface:'trim',material:'wood'},[[0,0],[1,0],[1,1],[0,1]]);
  const mesh=patch.mesh(b.finish());
  assert(mesh.positions.length>18);
  assert.equal(mesh.groups[0].owner,'part');
  let seam=0;
  for(let i=0;i<mesh.positions.length;i+=9){
    const points=[0,3,6].map(j=>Array.from(mesh.positions.slice(i+j,i+j+3)));
    assert(points.every(p=>p[0]===1)||points.every(p=>p[2]===1));
    for(const [j,p] of points.entries())if(p[0]===1&&p[2]===1){
      assert.equal(mesh.uv[(i/3+j)*2],.5);
      seam++;
    }
  }
  assert(seam>2);
  assert.deepEqual(mesh.bounds,patch.bounds({min:[-.75,0,0],max:[.75,1,0]}));
});

test('a mirrored affine contour retains winding, mapped normals, and a stable inverse',()=>{
  const {M}=K,R=[-1.6,.3,.1,0,1.1,0,.24,.15,.79],t=[2,-.4,3],
    map=q=>V.add(M.app(R,q),t),normal=n=>V.norm(M.app(M.tr(M.inv(R)),n));
  const contour=frames.map(f=>({key:f.key,a:map(f.a),b:map(f.b),up:M.app(R,f.up),normal:normal(f.normal)}));
  const center=V.dist(contour[0].a,contour[0].b);
  const patch=P.foldedRibbon.compile(contour,{origin:center}).region(-.8,.8);
  for(const q of [[-.6,.43,-.22],[.4,.28,.12]])near(patch.project(patch.map(q)).q,q);
  const b=P.geometry.builder();
  b.quad([-.7,0,0],[.7,0,0],[.7,1,0],[-.7,1,0],{surface:'front'});
  const mesh=patch.mesh(b.finish());
  for(let i=0;i<mesh.positions.length;i+=9){
    const [a,b,c]=[0,3,6].map(j=>[...mesh.positions.slice(i+j,i+j+3)]);
    const cross=V.norm(V.cross(V.sub(b,a),V.sub(c,a)));
    assert(V.dot(cross,[...mesh.normals.slice(i,i+3)])>.999);
  }
});

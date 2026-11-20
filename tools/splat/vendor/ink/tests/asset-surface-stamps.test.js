const test=require('node:test');
const assert=require('node:assert/strict');
const studio=require('..');
const {KIT:K}=studio.load();
const raw={
  type:'triangle-mesh',positions:[-1,-1,0,1,-1,0,1,1,0,-1,1,0, -1,-1,-.3,1,-1,-.3,1,1,-.3,-1,1,-.3],
  triangles:[0,1,2,0,2,3,4,5,6,4,6,7],colors:[[1,0,0],[0,0,1]],faceColors:[0,0,1,1],
  texture:{uv:[0,1,1,1,1,0,0,0,0,1,1,1,1,0,0,0],
    images:[{width:2,height:1,rgb:Buffer.from([255,0,0,255,0,0]).toString('base64'),alpha:'AP8='}],
    maps:[{image:0,wrap:['clamp','clamp'],filter:'nearest',factor:[1,1,1],alphaMode:'MASK',alphaCutoff:.5}],
    faces:[0,0,-1,-1]}
};
test('UV stamps resolve cutouts per art pixel at both coarse and fine splat spacing',()=>{
  for(const res of [.10,.19]){
    const w=K.authoring.assetSurfaces.world(raw,{res,size:3,palette:[0,0xff0000,0x0000ff],
      ambient:1,cam:{target:[0,1.5,0],dist:5,pitch:0,yaw:0}});
    const image=studio.render(w,{w:96,h:96,px:1,ortho:true});
    const at=(x,y)=>Array.from(image.rgb.slice((y*96+x)*3,(y*96+x)*3+3));
    assert.deepEqual(at(35,48),[0,0,255]);
    assert.deepEqual(at(61,48),[255,0,0]);
  }
  assert.throws(()=>K.authoring.assetSurfaces.world(raw,{res:.0001,maxSplats:20}),/budget/);
});
test('alpha-aware fields omit invisible faces and round trip through the SDF reader',()=>{
  const clear={...raw,triangles:raw.triangles.slice(0,6),faceColors:[0,0],
    texture:{...raw.texture,faces:[0,0],images:[{width:1,height:1,rgb:'////',alpha:'AA=='}]}};
  assert.throws(()=>K.authoring.assetSurfaces.field(clear,{cells:16}),/no visible surface/);
  const field=K.authoring.assetSurfaces.field(raw,{cells:24,thick:.08});
  assert(field.sd(.6,1,.15)<0);
  assert(field.sd(-.6,1,.15)>0);
  assert(field.sd(-.6,1,-.15)<0);
  const saved={format:'ink-studio-sdf-grid-v1',origin:field.lo,dimensions:field.n,spacing:field.h,values:Array.from(field.D)};
  assert.equal(K.depth.readField(saved).sd(-.6,1,-.15),field.sd(-.6,1,-.15));
});

test('SDF splats transfer source UVs and cutouts onto reconstructed geometry', () => {
  const options={size:3,cells:48,thick:.12,res:.065,palette:[0,0xff0000,0x0000ff],ambient:1,
    cam:{target:[0,1.5,0],dist:5,pitch:0,yaw:0}};
  const grid=K.authoring.assetSurfaces.field(raw,options);
  const w=K.authoring.assetSurfaces.world(raw,{...options,geometry:'sdf',field:grid});
  assert.equal(w.mesh.geometry,'sdf');
  assert.equal(w.sdf.sourceTriangles,4);
  assert(w.sdf.reconstructedTriangles>4);
  assert.equal(w.sdf.spacing,grid.h);
  const image=studio.render(w,{w:96,h:96,px:1,ortho:true});
  const at=(im,x,y)=>Array.from(im.rgb.slice((y*96+x)*3,(y*96+x)*3+3));
  assert.deepEqual(at(image,35,48),[0,0,255]);
  assert.deepEqual(at(image,61,48),[255,0,0]);
  const refit=K.authoring.assetSurfaces.world(raw,{...options,size:6,geometry:'sdf',field:grid});
  const refitImage=studio.render(refit,{w:96,h:96,px:1,ortho:true});
  assert.deepEqual(at(refitImage,61,48),[255,0,0]);
  assert.deepEqual(at(refitImage,35,48),[0,0,255]);

  const carved={...grid,sd(x,y,z) {
    return Math.max(grid.sd(x,y,z),.57-Math.hypot(x-.6,y-1.5,z));
  }};
  const cut=K.authoring.assetSurfaces.world(raw,{...options,geometry:'sdf',field:carved});
  const cutImage=studio.render(cut,{w:96,h:96,px:1,ortho:true});
  assert.deepEqual(at(cutImage,61,48),[0,0,0]);
  assert.deepEqual(at(cutImage,35,48),[0,0,255]);
  assert.throws(()=>K.authoring.assetSurfaces.world(raw,{...options,geometry:'sdf',field:grid,maxSplats:1}),/budget/);
  assert.throws(()=>K.authoring.assetSurfaces.world(raw,{...options,geometry:'wrong'}),/geometry mode/);
});

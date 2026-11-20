const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const assert=require('node:assert/strict');
const test=require('node:test');
const ink=require('..');
const { KIT:K,makeBuilder,makeSculpt }=ink.load();
const { writeAtlas }=require('../cli/sprite-atlas.js');
const pixel=(image,x,y)=>[...image.rgb.subarray((y*image.w+x)*3,(y*image.w+x)*3+3)];
const close=(value,expected,eps=.015)=>assert(Math.abs(value-expected)<eps,value+' vs '+expected);
function atlas(colors,options={}) {
  const { width=colors.length, height=1, frames=[{rect:{x:0,y:0,width,height}}],
    depth, normal, emission, ...encoding }=options;
  return { metadata:{width,height,frames,unitsPerPixel:.75,...encoding},
    images:{color:Uint8Array.from(colors.flat()),...(depth&&{depth:Uint8Array.from(depth.flat())}),
      ...(normal&&{normal:Uint8Array.from(normal.flat())}),...(emission&&{emission:Uint8Array.from(emission.flat())})} };
}
const view={w:96,h:72,raw:true,px:1};
const cam={target:[0,0,0],dist:5,pitch:0,yaw:0,sway:0};
function world(placement,geometry) {
  const B=makeBuilder(4,[0x122033,0x246aec]);
  if (geometry) {
    const S=K.sculpt(makeSculpt(B));
    S.box([0,0,.03],[1,.47,.087],{r:[1],em:true},{res:.057});
    S.bake();
  }
  return B.finish({cam,radius:5,dither:0,spriteAtlases:placement?[K.sprite.placeAtlas(placement)]:[]});
}

test('directional sprites select authored yaw and elevation, and a card holds the first view', () => {
  const color=[[246,37,18,255],[30,243,19,255],[12,23,237,255]];
  const entries=[
    {yaw:0,pitch:0},{yaw:Math.PI/2,pitch:0},{yaw:Math.PI/2,pitch:.72}
  ].map((entry,x)=>({...entry,rect:{x,y:0,width:1,height:1}}));
  const source=K.sprite.atlas(atlas(color,{frames:entries}));
  const scene=world({atlas:source,at:[0,0,0]});
  for (const [i,{yaw,pitch}] of entries.entries())
    assert.deepEqual(pixel(ink.render(scene,{...view,yaw,pitch}),48,36),color[i].slice(0,3));
  assert.deepEqual(pixel(ink.render(scene,{...view,yaw:Math.PI/2,pitch:.72,spriteAtlasMode:'card'}),48,36),color[0].slice(0,3));
  assert.deepEqual(ink.render(scene,{...view,spriteAtlases:false}).rgb,ink.render(world(),view).rgb);
  const turned=world({atlas:source,at:[0,0,0],yaw:Math.PI/2});
  assert.deepEqual(pixel(ink.render(turned,{...view,yaw:Math.PI/2}),48,36),color[0].slice(0,3));
});

test('per-texel depth interleaves the atlas with opaque geometry in both projections', () => {
  const source=atlas([[250,24,24,255],[24,242,32,255]],{
    depth:[[0,0,0,255],[255,255,255,255]],depthRange:[-.42,.52]
  });
  const scene=world({atlas:source,at:[0,0,0]},true);
  for (const ortho of [false,true]) for (const settings of [
    {},{splatOrder:'surface'},{splatOrder:'surface',fragmentBudget:1}
  ]) {
    const opts={...view,...settings,ortho,passes:['depth','coverage','position','splatId']};
    const image=ink.render(scene,opts);
    assert.deepEqual(pixel(image,40,36),[250,24,24]);
    assert(pixel(image,55,36)[2]>180);
    const clear=ink.render(world({atlas:source,at:[0,0,0],depth:false},true),opts);
    assert(pixel(clear,40,36)[2]>180);
    const p=36*image.w+40;
    close(image.passes.position[p*3+2],.42,.02);
    assert.equal(image.passes.splatId[p],0);
  }
});

test('map-based normals relight the atlas and emission is separately captured with color alpha', () => {
  const source=atlas([[132,92,44,255],[132,92,44,255]],{
    normal:[[127,127,255,255],[127,127,0,255]],
    emission:[[25,57,114,255],[25,57,114,255]]
  });
  const scene=world({atlas:source,at:[0,0,0]});
  const options={...view,transparent:true,passes:['normal','emission','depth','coverage'],
    liveSun:{direction:[0,0,1],ambient:.16,intensity:.82,shadows:false}};
  const image=ink.render(scene,options);
  const lit=pixel(image,40,36), dim=pixel(image,55,36);
  assert(lit[0]>dim[0]+85 && dim[2]>110);
  const p=36*image.w+40;
  close(image.passes.normal[p*3+2],1);
  close(image.passes.emission[p*3+2],114/255);
  assert.equal(image.alpha[p],255);
  assert.equal(image.alpha[0],0);
  const authored=ink.render(world({atlas:source,at:[0,0,0],lighting:false,emission:false}),options);
  assert.deepEqual(pixel(authored,40,36),[132,92,44]);
  assert.equal(authored.passes.emission[p*3+2],0);
  close(authored.passes.normal[p*3+2],1);
});

test('exported multi-elevation PNG atlases can be imported and placed without extra calibration', () => {
  const source=world(undefined,true), exported=ink.spriteAtlas(source,{
    width:40,height:32,directions:2,pitches:[0,.6],view:{raw:true},maps:['depth','normal','emission']
  });
  assert.deepEqual(exported.metadata.frames.map(entry=>entry.pitch),[0,0,.6,.6]);
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'ink-sprite-input-'));
  try {
    writeAtlas(directory,exported);
    const read=ink.readSpriteAtlas(directory);
    assert(read.hasDepth);
    const selected=read.select(0,'impostor',[0,Math.sin(.6),Math.cos(.6)]);
    assert.equal(selected.pitch,.6);
    assert(selected.unitsPerPixel>0 && selected.depthOrigin>source.cam.dist);
    const scene=world({atlas:read,at:[0,0,0]});
    const render=ink.render(scene,{...view,ortho:true,transparent:true,passes:['depth','emission']});
    const p=36*render.w+48;
    assert(render.alpha[p]>240);
    close(render.passes.depth[p],selected.depthOrigin-.12,.17);
    assert(render.passes.emission[p*3+2]>.7);
    assert(pixel(render,48,36)[2]>180);
  } finally {
    fs.rmSync(directory,{recursive:true,force:true});
  }
  assert.throws(()=>K.sprite.atlas(atlas([[1,2,3,255]],{depth:[[0,0,0,255]]})),/depth needs/);
  assert.throws(()=>K.sprite.atlas(atlas([[1,2,3,255]],{frames:[{rect:{x:1,y:0,width:1,height:1}}]})),/rectangle/);
});

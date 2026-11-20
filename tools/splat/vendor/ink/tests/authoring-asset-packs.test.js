const test = require('node:test');
const assert = require('node:assert/strict');
const { mesh, authoring: A } = require('..').load().KIT;
const family = (id, fields = {}) => ({
  id, kind: 'prop', version: 1, bounds: {min:[-.1,0,-.1],max:[.1,.3,.1]},
  sockets: {base:{p:[0,0,0],dir:[0,1,0]}}, requiredSockets:['base'],
  variants:[{id:'one',recipe:{type:'example',size:1}}], ...fields
});
const extension = (id, replacements, families = [family(id+'/lamp')]) => ({
  format:'ink-studio/asset-pack',version:1,revision:1,id,title:id,families,replacements
});

test('asset catalogs expose additions and resolve ordered compatible replacements per scene',()=>{
  const base=family('lamp'), first=extension('blue',{lamp:'blue/lamp'}), second=extension('clay',{lamp:'clay/lamp'});
  const catalog=A.assetPacks.create({families:[base],packs:[first,second]});
  assert.equal(catalog.get('blue/lamp').id,'blue/lamp');
  assert.equal(catalog.compile().resolve('lamp').id,'lamp');
  assert.equal(catalog.compile(['blue','clay']).resolve('lamp').id,'clay/lamp');
  assert.equal(catalog.compile(['clay','blue']).resolve('lamp').id,'blue/lamp');
  assert.equal(catalog.compile(['blue']).choose('lamp','slot',3).recipe.size,1);
  assert.deepEqual(catalog.compile(['missing']).missing,['missing']);
  assert.equal(catalog.compile(['missing']).resolve('lamp').id,'lamp');
  assert.throws(()=>A.assetPacks.create({families:[base],packs:[extension('loose',{lamp:'loose/lamp'},[
    family('loose/lamp',{sockets:{},requiredSockets:[]})
  ])]}),/Incompatible/);
  const left=extension('blue',{'clay/lamp':'blue/lamp'}),right=extension('clay',{'blue/lamp':'clay/lamp'});
  const cyclic=A.assetPacks.create({packs:[left,right]});
  assert.throws(()=>cyclic.compile(['blue','clay']),/Cyclic/);
  assert.throws(()=>A.assetPacks.create({packs:[first,first]}),/Duplicate/);
});

test('source revisions keep identity and replacement order, and skip identical content',()=>{
  const base=family('lamp'), blue=extension('blue',{lamp:'blue/lamp'});
  const next=A.assetPacks.reviseFamily(blue,'blue/lamp',{variants:[{id:'one',recipe:{type:'example',size:2}}]});
  assert.equal(next.id,blue.id);
  assert.equal(next.revision,2);
  assert.equal(next.families[0].id,blue.families[0].id);
  assert.equal(next.families[0].version,2);
  const catalog=A.assetPacks.create({families:[base],packs:[next,extension('clay',{lamp:'clay/lamp'})]});
  assert.equal(catalog.compile(['clay','blue']).choose('lamp','slot',3).recipe.size,2);
  assert.deepEqual(A.assetPacks.reviseFamily(next,'blue/lamp',{
    variants:[{recipe:{size:2,type:'example'},id:'one',weight:1}]
  }),next);
  assert.equal(blue.families[0].variants[0].recipe.size,1);
  assert.throws(()=>A.assetPacks.reviseFamily(next,'blue/lamp',{id:'blue/new'}),/editable/);
  assert.throws(()=>A.assetPacks.reviseFamily(next,'blue/lamp',{sockets:{}}),/required socket/);
});

test('portable bundles walk replacement dependencies and merge an entire revision set without downgrades',()=>{
  const root=extension('root',{lamp:'root/lamp'}), middle=extension('middle',{'root/lamp':'middle/lamp'});
  const end=extension('end',{'middle/lamp':'end/lamp'}), unused=extension('unused',{});
  const payload=A.assetPacks.bundle([end,unused,root,middle],['end']);
  assert.deepEqual(payload.packs.map(p=>p.id),['end','root','middle']);
  const newer=A.assetPacks.reviseFamily(root,'root/lamp',{label:'Revised root'});
  const install=A.assetPacks.merge([unused,newer],JSON.stringify(payload));
  assert.deepEqual(install.packs.map(p=>p.id),['unused','root','end','middle']);
  assert.deepEqual(install.added,['end','middle']);
  assert.deepEqual(install.keptNewer,['root']);
  const catalog=A.assetPacks.create({families:[family('lamp')],packs:install.packs});
  assert.equal(catalog.compile().resolve('lamp').id,'lamp');
  assert.equal(catalog.compile(['root','middle','end']).resolve('lamp').id,'end/lamp');
  assert.deepEqual(A.assetPacks.merge(install.packs,payload).unchanged,['end','middle']);
  assert.deepEqual(A.assetPacks.merge([root,unused],newer).updated,['root']);
  assert.equal(root.revision,1);
  assert.throws(()=>A.assetPacks.merge([root],{...payload,packs:[end,{...root,title:'Conflicting title'}]}),/Conflicting/);
  assert.throws(()=>A.assetPacks.merge([],{...payload,packs:[end,end]}),/Duplicate/);
  assert.throws(()=>A.assetPacks.bundle([root],['missing']),/installed pack IDs/);
});

function makeGLB(nodes=[{mesh:0}]) {
  const positions=[-1,0,0,1,0,0,0,1,0];
  const bin=Buffer.alloc(36);
  positions.forEach((v,i)=>bin.writeFloatLE(v,i*4));
  const scene={asset:{version:'2.0'},scenes:[{nodes:[0]}],nodes,
    meshes:[{primitives:[{attributes:{POSITION:0},material:0}]}],
    materials:[{pbrMetallicRoughness:{baseColorFactor:[1,0,0,1]}}],
    buffers:[{byteLength:bin.length}],bufferViews:[{buffer:0,byteLength:bin.length}],
    accessors:[{bufferView:0,componentType:5126,type:'VEC3',count:3}]};
  const raw=Buffer.from(JSON.stringify(scene)), json=Buffer.alloc((raw.length+3)&~3,32);
  raw.copy(json);
  const head=Buffer.alloc(12), jt=Buffer.alloc(8),bt=Buffer.alloc(8);
  head.writeUInt32LE(0x46546c67);head.writeUInt32LE(2,4);head.writeUInt32LE(28+json.length+bin.length,8);
  jt.writeUInt32LE(json.length);jt.writeUInt32LE(0x4e4f534a,4);
  bt.writeUInt32LE(bin.length);bt.writeUInt32LE(0x004e4942,4);
  return Buffer.concat([head,jt,json,bt,bin]);
}

test('GLB imports a fitted mesh and preserves face color in a self-contained recipe',()=>{
  const raw=makeGLB(), recipe = A.assetMeshes.fromGLB(raw,{size:1});
  assert.deepEqual(recipe.triangles,[0,1,2]);
  assert.deepEqual(recipe.colors[recipe.faceColors[0]],[1,0,0]);
  assert.deepEqual(recipe.positions,[-.5,0,0,.5,0,0,0,.5,0]);
  assert.deepEqual(A.assetMeshes.validate(JSON.parse(JSON.stringify(recipe))),recipe);
  assert.throws(()=>A.assetMeshes.fromGLB(raw.subarray(0,-1)),/complete/);
  const invalid = {...recipe,triangles:[0,1,9]};
  assert.throws(()=>A.assetMeshes.validate(invalid),/Invalid triangle/);
  assert.throws(()=>A.assetMeshes.recipe(mesh.make([0,0,0,0,0,0,0,0,0],[0,1,2])),/area/);
});

test('mesh thumbnails fit the visible asset, resolve occlusion and retain transparent pixels',()=>{
  const recipe = A.assetMeshes.fromGLB(makeGLB());
  const positions = [...recipe.positions,...recipe.positions.map((v,i)=>i%3===2?v-.4:v)];
  const back = {...recipe, positions, triangles:[0,1,2,3,4,5], colors:[[1,0,0],[0,0,1]], faceColors:[0,1]};
  const frame = A.assetMeshes.thumbnail(back,{size:32,yaw:0,pitch:0,light:[0,0,1]});
  assert.equal(frame.width,32);
  assert.equal(frame.height,32);
  assert.deepEqual(Array.from(frame.pixels.slice(0,4)),[0,0,0,0]);
  const center = (16*32+16)*4;
  assert.deepEqual(Array.from(frame.pixels.slice(center,center+4)),[255,0,0,255]);
  assert.deepEqual(frame,A.assetMeshes.thumbnail(back,{size:32,yaw:0,pitch:0,light:[0,0,1]}));
});

function texturedGLB(filter=9728, configure) {
  const source=makeGLB(), size=source.readUInt32LE(12);
  const document=JSON.parse(source.subarray(20,20+size));
  const coordinates=Buffer.alloc(24);
  [0,0,1,0,0,1].forEach((n,i)=>coordinates.writeFloatLE(n,i*4));
  const tint=Buffer.from([255,255,255,255,64,255,255,255,255,0,0,0]);
  const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2nGQAAAAASUVORK5CYII=','base64');
  let bin=Buffer.concat([source.subarray(28+size),coordinates,tint,png,Buffer.alloc((4-png.length%4)%4)]);
  document.bufferViews.push({buffer:0,byteOffset:36,byteLength:24},{buffer:0,byteOffset:60,byteLength:9},
    {buffer:0,byteOffset:72,byteLength:png.length});
  document.accessors.push({bufferView:1,componentType:5126,type:'VEC2',count:3},
    {bufferView:2,componentType:5121,normalized:true,type:'VEC3',count:3});
  Object.assign(document.meshes[0].primitives[0].attributes,{TEXCOORD_1:1,COLOR_0:2});
  document.materials[0].pbrMetallicRoughness={baseColorFactor:[.5,1,1,1],baseColorTexture:{index:0,
    extensions:{KHR_texture_transform:{texCoord:1}}}};
  document.images=[{bufferView:3,mimeType:'image/png'}];
  document.textures=[{source:0,sampler:0}];
  document.samplers=[{wrapS:33071,wrapT:33071,magFilter:filter}];
  if(configure) configure(document,(type,values)=>{
    const bytes=Buffer.alloc(values.length*4);
    values.forEach((v,i)=>bytes.writeFloatLE(v,i*4));
    const index=document.accessors.length;
    document.accessors.push({bufferView:document.bufferViews.length,componentType:5126,type,count:3});
    document.bufferViews.push({buffer:0,byteOffset:bin.length,byteLength:bytes.length});
    bin=Buffer.concat([bin,bytes]);
    return index;
  });
  document.buffers[0].byteLength=bin.length;
  const raw=Buffer.from(JSON.stringify(document)),json=Buffer.alloc((raw.length+3)&~3,32);
  raw.copy(json);
  const header=Buffer.alloc(20), binHeader=Buffer.alloc(8);
  [0x46546c67,2,28+json.length+bin.length,json.length,0x4e4f534a].forEach((n,i)=>header.writeUInt32LE(n,i*4));
  binHeader.writeUInt32LE(bin.length);binHeader.writeUInt32LE(0x004e4942,4);
  return Buffer.concat([header,json,binHeader,bin]);
}

test('textured GLB imports decode once and produce portable, UV-addressable base color',async()=>{
  let decoded=0;
  const decodeImage=(bytes,mime,{width,height})=>{
    decoded++;
    assert(bytes.length>24);
    assert.equal(mime,'image/png');
    assert.deepEqual([width,height],[1,1]);
    return {width:2,height:2,pixels:Uint8Array.from([255,0,0,255,0,255,0,255,0,0,255,255,255,255,0,255])};
  };
  const bytes=texturedGLB(), imported=await A.assetMeshes.importGLB(bytes,{decodeImage,size:1});
  assert.equal(decoded,1);
  assert.equal(A.assetMeshes.fromGLB(bytes).texture,undefined);
  await assert.rejects(A.assetMeshes.importGLB(bytes),/need an image decoder/);
  const portable=A.assetMeshes.validate(JSON.parse(JSON.stringify(imported)));
  const sampler=A.assetMeshes.colorSampler(portable);
  const near=(a,b)=>assert(Math.abs(a-b)<.002,[a,b].join(' vs '));
  const expected=q=>1.055*q**(1/2.4)-.055;
  near(sampler.at(0,0,0)[0],expected(.5));
  near(sampler.at(0,1,0)[1],expected(64/255));
  near(sampler.atPoint(0,...portable.positions.slice(6,9))[2],1);
  const icon=A.assetMeshes.thumbnail(portable,{size:24,yaw:0,pitch:0,light:[0,0,1]});
  assert(icon.pixels.some((v,i)=>i%4===0&&v>155));
  assert(icon.pixels.some((v,i)=>i%4===2&&v>230));
  const filtered=A.assetMeshes.colorSampler(await A.assetMeshes.importGLB(texturedGLB(9729),{decodeImage}));
  near(filtered.at(0,.5,.25)[0],expected(.25));
  near(filtered.at(0,.5,.25)[1],expected(.5*(255+64)/510));
});

test('material channels share embedded images and retain tangent normals, roughness and emission',async()=>{
  const raw=texturedGLB(9728,(g,attribute)=>{
    const m=g.materials[0], attrs=g.meshes[0].primitives[0].attributes;
    m.normalTexture={index:0,texCoord:1,scale:.5};
    m.pbrMetallicRoughness.roughnessFactor=.8;
    m.pbrMetallicRoughness.metallicRoughnessTexture={index:0,texCoord:1};
    m.emissiveTexture={index:0,texCoord:1};
    m.emissiveFactor=[.4,0,.1];
    m.extensions={KHR_materials_emissive_strength:{emissiveStrength:2}};
    attrs.NORMAL=attribute('VEC3',[0,0,1,0,0,1,0,0,1]);
    attrs.TANGENT=attribute('VEC4',[0,1,0,1,0,1,0,1,0,1,0,1]);
  });
  let decodes=0;
  const asset=await A.assetMeshes.importGLB(raw,{decodeImage(){
    decodes++;
    return {width:1,height:1,pixels:Uint8Array.from([255,128,255,255])};
  }});
  assert.equal(decodes,1);
  assert.equal(asset.texture.images.length,1);
  const sample=A.assetMeshes.colorSampler(JSON.parse(JSON.stringify(asset))).materialAt(0,.2,.3);
  assert(sample.normal[1]>.44&&sample.normal[2]>.89&&Math.abs(sample.normal[0])<.01);
  assert(Math.abs(sample.roughness-128/255*.8)<1e-8);
  assert.deepEqual(sample.emission,[.8,0,.2]);
  const dark=A.assetMeshes.shadeMaterial(sample,{irradiance:0});
  assert(dark[0]>.9&&dark[1]===0&&dark[2]>.45);
  const matte=A.assetMeshes.shadeMaterial({...sample,emission:[0,0,0],roughness:1},
    {irradiance:.2,light:sample.normal,view:sample.normal});
  const glossy=A.assetMeshes.shadeMaterial({...sample,emission:[0,0,0]},
    {irradiance:.2,light:sample.normal,view:sample.normal});
  assert(glossy.every((value,i)=>value>matte[i]));
  const {normal,roughness}=sample;
  const aligned=A.assetMeshes.highlight(normal,roughness,normal,normal);
  assert(Math.abs(aligned-.20*(1-roughness))<1e-8);
  assert(A.assetMeshes.highlight(normal,roughness,normal,[1,0,0])<aligned);
  assert.equal(A.assetMeshes.highlight(normal,roughness,normal,normal.map(v=>-v)),0);
  assert.equal(A.assetMeshes.highlight(normal,1,normal,normal),0);
});

test('GLB sockets preserve nested node positions and forward axes when fitted',()=>{
  const seat={name:'Ride Seat',translation:[.5,.4,-2],rotation:[0,Math.SQRT1_2,0,Math.SQRT1_2]};
  const hook={name:'Hook',matrix:[1,0,0,0,0,1,0,0,0,0,1,0,-.5,1,2,1]};
  const body={mesh:0,translation:[10,2,3],scale:[2,1,1],children:[1,2]};
  const bytes=makeGLB([body,seat,hook]);
  const recipe=A.assetMeshes.fromGLB(bytes,{size:1,socketNodes:{seat:'Ride Seat',hook:'Hook',missing:'Absent'}});
  assert.deepEqual(Object.keys(recipe.sockets),['seat','hook']);
  assert.deepEqual(recipe.sockets.seat.p,[.25,.10,-.5]);
  assert(recipe.sockets.seat.dir[0]>.999999 && Math.abs(recipe.sockets.seat.dir[2])<1e-8);
  assert.deepEqual(recipe.sockets.hook,{p:[-.25,.25,.5],dir:[0,0,1]});
  assert.deepEqual(A.assetMeshes.validate(JSON.parse(JSON.stringify(recipe))),recipe);
  assert.equal(A.assetMeshes.fromGLB(bytes,{size:1}).sockets,undefined);
  assert.deepEqual(A.assetMeshes.fromGLB(bytes,{size:1}).positions,recipe.positions);
  assert.throws(()=>A.assetMeshes.fromGLB(makeGLB([body,seat,seat]),{socketNodes:{seat:'Ride Seat'}}),/Ambiguous/);
  assert.throws(()=>A.assetMeshes.validate({...recipe,sockets:{seat:{p:[0,0,0],dir:[0,0,0]}}}),/socket/);
});

test('GLB alpha survives portable round trips with mask cutoff, blending, factors and legacy defaults', async () => {
  const decodeImage = () => ({ width: 2, height: 1,
    pixels: Uint8Array.from([255,0,0,0, 0,255,0,128]) });
  async function sampler(mode, filter = 9728) {
    const glb = texturedGLB(filter, g => {
      g.materials[0].alphaMode = mode;
      g.materials[0].alphaCutoff = .5;
      g.materials[0].pbrMetallicRoughness.baseColorFactor = [1,1,1,.5];
    });
    const imported = await A.assetMeshes.importGLB(glb, { decodeImage });
    return A.assetMeshes.colorSampler(A.assetMeshes.validate(JSON.parse(JSON.stringify(imported))));
  }
  const opaque = await sampler('OPAQUE');
  assert.equal(opaque.opacityAt(0,0,0),1);
  const mask = await sampler('MASK');
  assert.equal(mask.opacityAt(0,0,0),0);
  assert.equal(mask.opacityAt(0,1,0),0);
  const blend = await sampler('BLEND');
  assert.equal(blend.materialAt(0,0,0).opacity,0);
  assert(Math.abs(blend.opacityAt(0,1,0)-64/255)<1e-6);
  const linear = await sampler('BLEND',9729);
  assert(Math.abs(linear.opacityAt(0,.5,0)-32/255)<1e-6);

  const legacy = A.assetMeshes.fromGLB(makeGLB());
  assert.equal(A.assetMeshes.colorSampler(legacy).opacityAt(0,.2,.3),1);
  const malformed = JSON.parse(JSON.stringify(await A.assetMeshes.importGLB(texturedGLB(), {decodeImage})));
  malformed.texture.images[0].alpha = 'AA==';
  assert.throws(() => A.assetMeshes.validate(malformed),/texture image/);
  await assert.rejects(A.assetMeshes.importGLB(texturedGLB(9728,g=>{g.materials[0].alphaMode='UNKNOWN';}),
    {decodeImage}),/alpha material/);
});

test('vertex alpha and factor-only materials retain coverage without an image decoder', async () => {
  const glb = texturedGLB(9728,(g,attribute) => {
    g.meshes[0].primitives[0].attributes.COLOR_0 = attribute('VEC4',[1,1,1,0, 1,1,1,.5, 1,1,1,1]);
    g.materials[0].alphaMode='BLEND';
    g.materials[0].pbrMetallicRoughness={baseColorFactor:[1,0,0,.5]};
  });
  const asset=await A.assetMeshes.importGLB(glb);
  const sample=A.assetMeshes.colorSampler(asset);
  assert.equal(sample.opacityAt(0,0,0),0);
  assert(Math.abs(sample.opacityAt(0,1,0)-.25)<.002);
  assert.equal(sample.opacityAt(0,0,1),.5);
  assert(Math.abs(sample.at(0,.2,.2)[0]-1)<1e-12);
});

test('transparent front layers reveal underlying thumbnail geometry, regardless of face order', () => {
  const base=A.assetMeshes.fromGLB(makeGLB());
  const p=[...base.positions,...base.positions.map((v,i)=>i%3===2?v-.3:v)];
  const texture={uv:Array(12).fill(0),images:[{width:1,height:1,rgb:'////',alpha:'AA=='}],
    maps:[{image:0,wrap:['clamp','clamp'],filter:'nearest',factor:[1,0,0],alphaMode:'MASK'}],faces:[0,-1]};
  const raw={...base,positions:p,triangles:[0,1,2,3,4,5],colors:[[1,0,0],[0,0,1]],faceColors:[0,1],texture};
  const render=a=>A.assetMeshes.thumbnail(a,{size:32,yaw:0,pitch:0,light:[0,0,1]});
  const center=(16*32+16)*4;
  assert.deepEqual(Array.from(render(raw).pixels.slice(center,center+4)),[0,0,255,255]);
  const reverse={...raw,triangles:[3,4,5,0,1,2],faceColors:[1,0],texture:{...texture,faces:[-1,0]}};
  assert.deepEqual(render(raw),render(reverse));
  const translucent={...raw,texture:{...texture,images:[{width:1,height:1,rgb:'////',alpha:'gA=='}],
    maps:[{...texture.maps[0],alphaMode:'BLEND'}]}};
  const mixed=render(translucent).pixels.slice(center,center+4);
  assert(mixed[0]>100&&mixed[2]>100&&mixed[3]===255);
});

test('single pixel atlases retain 128px detail while multiple images preserve existing texel budgets', async () => {
  const decodeImage=()=>({width:128,height:128,pixels:new Uint8Array(128*128*4).fill(255)});
  const single=await A.assetMeshes.importGLB(texturedGLB(),{decodeImage});
  assert.equal(single.texture.images[0].width,128);
  const two=texturedGLB(9728,g=>{
    g.images.push({...g.images[0]});
    g.textures.push({...g.textures[0],source:1});
    g.materials[0].pbrMetallicRoughness.metallicRoughnessTexture={index:1,texCoord:1};
  });
  const multiple=await A.assetMeshes.importGLB(two,{decodeImage});
  assert.deepEqual(multiple.texture.images.map(image=>image.width),[64,64]);
  assert.equal(A.assetMeshes.validate(JSON.parse(JSON.stringify(multiple))).texture.images.length,2);
});

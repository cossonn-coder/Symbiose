const { test } = require('node:test');
const assert = require('node:assert/strict');

const packed = (x,y,z,color = 0x332211) =>
  Float32Array.of(x,y,z,3,.06,0,0,color,.02,0,.04,0,0,0,0,0);
const world = (...positions) => ({
  data:Float32Array.from(positions.flatMap(p=>[...packed(...p)])), count:positions.length, pal:[0,0x112233]
});

test('instances share immutable geometry while authored edits keep per-splat ownership', async () => {
  const { createSplatInstances } = await import('../webgl.mjs');
  const source=world([0,0,0],[1,0,0]), base=world([0,-1,0]);
  const group=createSplatInstances({door:source,gate:source},[
    {id:'first',prototype:'door',position:[2,1,3]},
    {id:'second',prototype:'gate',position:[4,1,3],rotation:[0,0,1,0,1,0,-1,0,0],scale:2}
  ]);
  source.data[0]=10;
  assert.equal(group.sharedSplats,2);
  assert.equal(group.splats,4);
  assert.deepEqual(group.owner(4,1),{id:'second',prototype:'gate',splat:1});
  assert.equal(group.owner(0,1),undefined);
  const old=group.get('second');
  assert.throws(()=>group.update('second',{prototype:'door'}),/editable/);
  assert.throws(()=>group.update('second',{scale:0}),/Invalid/);
  assert.strictEqual(group.get('second'),old);
  group.update('first',{palette:{'#112233':'#42657b'},damage:{center:[1,0,0],radius:.1}});
  const out=group.flatten(base);
  assert.deepEqual([...out.data.subarray(16,20)],[2,1,3,3]);
  assert.equal(out.data[16+7],0x7b6542);
  assert.equal(out.data[32+3],0);
  assert.deepEqual([...out.data.subarray(64,68)],[4,1,1,3]);
  assert(Math.abs(out.data[64+4]-.16)<1e-6);
  assert(Math.abs(out.data[64+10]-.24)<1e-6);
  assert.deepEqual(out.renderMetadata.objects,[null,'first','second']);
  assert.deepEqual([...out.renderMetadata.objectIds],[0,1,1,2,2]);
  assert.deepEqual(group.owner(2,1),{id:'first',prototype:'door',splat:1});
  group.update('first',{visible:false});
  assert.equal(group.flatten(base).data[16+3],0);
  assert.equal(group.flatten(base).data[64+3],3);
});

test('instance culling preserves expanded ordering for interleaved splats and wide near-edge dabs', async () => {
  const { createSplatInstances,instancePlan } = await import('../src/webgl/instances.mjs');
  const { makeCamera,createDepthSorter } = await import('../src/webgl/view.mjs');
  const { groupVisibility } = await import('../src/webgl/instance-draw.mjs');
  const prototype=world([0,0,0],[0,0,-4]), base=world([0,0,-2]);
  const group=createSplatInstances({model:prototype},[
    {id:'a',prototype:'model'}, {id:'b',prototype:'model',position:[0,0,-1]},
    {id:'outside',prototype:'model',position:[100,0,0]}
  ]);
  const plan=instancePlan(group);
  for(const ortho of [false,true]){
    const camera=makeCamera(base,{camera:{ortho}},200,200);
    const visible=groupVisibility(plan,camera,200,200,1);
    assert.deepEqual(visible.map(row=>row.authored.id),['a','b']);
    const sort=createDepthSorter();
    const order=sort(base,camera.view,0,visible);
    assert.deepEqual([...order],[4,2,2,1,0,0,3,2,1,1]);
    assert.deepEqual([...sort(group.flatten(base),camera.view,0)].filter(i=>i<5),[4,2,0,3,1]);
    // The center is beyond the viewport at the near end of this asset,
    // but a much wider drawn covariance can still reach it.
    assert(groupVisibility(plan,camera,200,200,200).some(row=>row.authored.id==='outside'));
  }
});

test('dirty base rows and placement edits stay separate even across renderer path switches', async () => {
  const { createSplatInstances } = await import('../webgl.mjs');
  const { createInstanceDraw } = await import('../src/webgl/instance-draw.mjs');
  const calls=[];
  const table=(width,unit)=>({upload:(x,_,rows)=>calls.push({unit,copy:x.slice(),rows}),bind:()=>{}});
  const packedGeometry=table(2048,0);
  const draw=createInstanceDraw(table,packedGeometry,4096);
  const base=world([1,0,0]), asset=world([2,0,0]);
  const group=createSplatInstances({asset},[{id:'one',prototype:'asset'}]);
  draw.bind(group,base,[],true);
  assert.deepEqual(calls.map(row=>row.unit),[0,15]);
  assert.deepEqual([calls[0].copy[0],calls[0].copy[16]],[1,2]);
  calls.length=0;
  base.data[0]=4;
  draw.bind(group,base,[0],false);
  assert.equal(calls.length,1);
  assert.deepEqual([calls[0].copy[0],calls[0].copy[16]],[4,2]);
  assert.deepEqual(calls[0].rows,[0]);
  calls.length=0;
  group.update('one',{position:[22,0,0]});
  draw.bind(group,base,[],false);
  assert.deepEqual(calls.map(row=>[row.unit,row.rows]),[[0,[]],[15,[0]]]);
  assert.equal(calls[1].copy[67],22);
  calls.length=0;
  base.data[0]=5;
  draw.bind(group,base,undefined,true);
  assert.deepEqual([calls[0].copy[0],calls[0].copy[16]],[5,2]);
  assert.equal(calls[0].rows,undefined);
});

test('prototype validation keeps unsupported baked animation and per-pixel surfaces explicit', async () => {
  const { createSplatInstances } = await import('../webgl.mjs');
  const asset=world([0,0,0]), row={id:'first',prototype:'asset'};
  assert.throws(()=>createSplatInstances({asset},[row,row]),/Duplicate/);
  assert.throws(()=>createSplatInstances({asset},[{...row,rotation:[1,0,0,0,0,0,0,0,1]}]),/orthonormal/);
  assert.throws(()=>createSplatInstances({asset},[{...row,palette:{'#123':'#456'}}]),/replacements/);
  assert.throws(()=>createSplatInstances({asset:{...asset,pix:new Float32Array(8)}},[row]),/stationary/);
  asset.data[11]=11;
  assert.throws(()=>createSplatInstances({asset},[row]),/stationary/);
});

test('the expanded compatibility path preserves render state and changes only affected rows', async () => {
  const { createSplatInstances } = await import('../webgl.mjs');
  const { createExpandedInstances } = await import('../src/webgl/instance-draw.mjs');
  const base = {...world([1,0,0]),pix:new Float32Array(8).fill(1)};
  const asset = world([0,0,0]);
  const group = createSplatInstances({asset},[
    {id:'a',prototype:'asset'}, {id:'b',prototype:'asset'}
  ]);
  const expand = createExpandedInstances();
  const initial = expand(base,group,[]).world;
  assert.equal(initial.pix.length,24);
  assert.deepEqual([...initial.pix.subarray(8)],[...new Float32Array(16)]);
  group.update('a',{position:[3,0,0]});
  base.data[0]=6;
  const next=expand(base,group,[0]);
  assert.strictEqual(next.world,initial);
  assert.deepEqual(next.changedRows,[0]);
  assert.deepEqual([next.world.data[0],next.world.data[16],next.world.data[32]],[6,3,0]);
  assert.deepEqual(expand(base,group,[]).changedRows,[]);
  base.pix = new Float32Array(8).fill(2);
  const refreshed = expand(base,group,[]).world;
  assert.notStrictEqual(refreshed,initial);
  assert.equal(refreshed.pix[0],2);
});

function browserParity(createRenderer,createSplatInstances) {
  const pal=[0x101421,0x808080,0xe09259], options={width:128,height:80,outline:false,dither:0,changedRows:[]};
  const baseBuilder=makeBuilder(7,pal), assetBuilder=makeBuilder(8,pal);
  baseBuilder.disc(0,-.6,0,[0,1,0],1.8,.08,baseBuilder.P[1],3);
  assetBuilder.disc(0,0,0,[0,0,1],.35,.035,assetBuilder.P[2],1.4);
  const base=baseBuilder.finish({cam:{target:[0,0,0],dist:5,yaw:.15,pitch:.2,ortho:true}});
  const copies=createSplatInstances({asset:assetBuilder.finish()},[
    {id:'left',prototype:'asset',position:[-.6,-.12,0]},
    {id:'right',prototype:'asset',position:[.6,.05,0]}
  ]);
  const canvas=document.createElement('canvas'), renderer=createRenderer(canvas,{toolkit:{KIT,PixelLook}});
  const gl=canvas.getContext('webgl2');
  const draw=(world,frame)=>{
    renderer.render(world,{...options,...frame});
    const image=new Uint8Array(options.width*options.height*4);
    gl.readPixels(0,0,options.width,options.height,gl.RGBA,gl.UNSIGNED_BYTE,image);
    if(gl.getError()!==gl.NO_ERROR)throw Error('WebGL reported an instance error');
    return image;
  };
  const same=(a,b)=>a.every((v,i)=>v===b[i]);
  const pair=(frame,world=base)=>{
    const image=draw(world,{...frame,instances:copies});
    if(!same(image,draw(copies.flatten(world),frame)))throw Error('Shared and expanded pixels differ');
    return image;
  };
  const remembered=pair({raw:true});
  copies.update('right',{position:[.17,.05,0],palette:{'#e09259':'#238544'}});
  const updated=pair({raw:true});
  if(same(remembered,updated))throw Error('Authored edits did not change the frame');
  const { waterBodies }=KIT.procedural;
  const water=waterBodies.scene([waterBodies.create({
    id:'pond',bounds:{min:[-2,-2],max:[2,2]},resolution:[2,2],sample:()=>({bed:-1.4,surface:0})
  })]);
  pair({raw:true},{...base,water});
  pair({order:Int32Array.of(0,2,1),raw:true});
  pair({paletteConstraints:{targets:[{object:'left',palette:['#127844']}]}});
  renderer.dispose();
}

test('WebGL shares edited splats and matches expanded rendering with water and compatibility passes', {
  skip:!process.env.INK_TEST_CHROME
}, () => {
  const fs=require('node:fs'), os=require('node:os'), path=require('node:path');
  const { execFileSync }=require('node:child_process'), { pathToFileURL }=require('node:url');
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'ink-instance-parity-'));
  try {
    const moduleURL=pathToFileURL(path.resolve(__dirname,'../webgl.mjs')).href;
    const page=path.join(temp,'parity.html');
    fs.writeFileSync(path.join(temp,'bundle.js'),require('..').bundle());
    fs.writeFileSync(page,`<!doctype html><pre id="result">pending</pre>
<script src="bundle.js"></script><script type="module">
import { createRenderer, createSplatInstances } from ${JSON.stringify(moduleURL)};
try {
  (${browserParity.toString()})(createRenderer,createSplatInstances);
  document.querySelector('#result').textContent='pass';
} catch(error) { document.querySelector('#result').textContent=encodeURIComponent(error.stack); }
</script>`);
    const html=execFileSync(process.env.INK_TEST_CHROME,['--headless','--no-first-run','--disable-background-networking',
      '--allow-file-access-from-files','--enable-unsafe-swiftshader','--use-angle=swiftshader',
      '--user-data-dir='+path.join(temp,'profile'),'--dump-dom',pathToFileURL(page).href],
    {timeout:60000,encoding:'utf8',stdio:['ignore','pipe','ignore']});
    assert.equal(decodeURIComponent(/<pre id="result">([^<]*)<\/pre>/.exec(html)?.[1]??''),'pass');
  } finally {
    fs.rmSync(temp,{recursive:true,force:true});
  }
});

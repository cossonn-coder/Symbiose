#!/usr/bin/env node
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { execFileSync } = require('node:child_process');
const studio = require('..');

const hardware = !process.argv.includes('--software');
const quick = process.argv.includes('--quick');
const executable = process.env.INK_TEST_CHROME || [
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium'
].find(file => fs.existsSync(file)) || 'google-chrome';
const encode = ({ data, count, pal, cam, radius, fog, moving, back }) => ({
  packed:Buffer.from(data.buffer,data.byteOffset,count*64).toString('base64'), count, pal, cam, radius, fog,
  moving:Array.from(moving??[]), back:Array.from(back??[])
});

function fixture(kit, source, base, object, placements, camera) {
  const { makeBuilder, makeSculpt, KIT:K } = kit;
  const B = makeBuilder(81,base.pal), S = K.sculpt(makeSculpt(B));
  object(S);
  S.bake();
  return { source, base:encode(base), prototype:encode(B.finish()), placements, camera };
}

function scenes() {
  const kit = studio.load(), { KIT:K, makeBuilder, makeSculpt } = kit;
  const streets = require('../examples/street-layouts.js')(kit).build(0);
  const district = makeBuilder(11,streets.pal), D = K.sculpt(makeSculpt(district));
  D.box([0,-.14,11.2],[14,.15,9.16],{r:[1,2,3,4]},{res:.18,rd:.32});
  for (let z=0; z<10; z++)
    D.box([0,.024,2.54+z*1.95],[13.8,.022,.19],{r:[5,6,7,8]},{res:.145,rd:.023});
  for (const x of [-9.32,-4.48,.34,5.19,10.03])
    D.box([x,.045,11.2],[.16,.024,8.72],{r:[5,6,7,8]},{res:.145,rd:.023});
  D.bake();
  const town = kit.SplatProvenance.join([streets,district.finish()],{cam:streets.cam,radius:21,fog:streets.fog});
  const houses = [];
  for (let z=0; z<9; z++) for (let x=0; x<17; x++) {
    const sign = z % 2 ? -1 : 1;
    houses.push({ id:'house-'+z+'-'+x, prototype:'model',
      position:[(x-8)*1.6+(z%2)*.55, .04, 3.4+z*1.95],
      rotation:[sign,0,0,0,1,0,0,0,sign], scale:.91+.18*K.hash(x,z,2) });
  }
  const garden = makeBuilder(31, [
    0x1d2936,0x303830,0x444a37,0x576043,0x65734c,0x848557,0xad9a6a,
    0x3f5743,0x658256,0xa1a468,0x3b302b,0x574338,0x826750,0xc0a477
  ]);
  const H = K.sculpt(makeSculpt(garden));
  const height = (x,z) => .54*garden.fbm(x*.083+2,z*.084,1.5,2)-.16;
  H.ground({r:[1,2,3,4,5,6]}, {rad:20,zs:1.1,edge:.028,res:.23,h:height});
  H.bake();
  const forest = [];
  for (let z=0; z<11; z++) for (let x=0; x<13; x++) {
    const px=(x-6)*2.7+.64*(K.hash(x,z,21)-.5), pz=(z-5)*2.65+.6*(K.hash(z,x,50)-.5);
    if (Math.abs(px)<1.3) continue;
    const yaw = Math.floor(K.hash(x,z,8)*4)*Math.PI/2, c=Math.cos(yaw), s=Math.sin(yaw);
    forest.push({ id:'tree-'+z+'-'+x, prototype:'model', position:[px,height(px,pz)-.055,pz],
      scale:.68+.35*K.hash(x,z,15), rotation:[c,0,s,0,1,0,-s,0,c] });
  }
  return {
    woodland:fixture(kit,'Burn diorama tree recipe, on a larger terrain',garden.finish({radius:22}),S=>{
      S.tree(0,0,0,{h:3.4,r:.155,lean:[.12,.045],nb:4,spread:1.51,cr:.82,cl:3,
        bark:{r:[10,11,12,13]},leaf:{r:[7,7,8,9],leaf:{},still:true},roots:0,lres:.15});
    },forest,{target:[.7,1.35,0],dist:13.2,yaw:.12,pitch:.17}),
    town:fixture(kit,'Street fields and house lots, extended with its baked houses',town,S=>{
      S.box([0,.23,0],[.28,.26,.31],{r:[10,11,12,13]},{rd:.029,res:.07});
      S.box([0,.515,0],[.34,.077,.38],{r:[14,15,16,17]},{rd:.033,res:.069});
      S.box([0,.17,.316],[.078,.158,.015],{r:[14,15,16]},{rd:.012,res:.027});
    },houses,{target:[.35,.46,8],dist:9.2,yaw:.07,pitch:.47})
  };
}

function browser(fixtures, createRenderer, createSplatInstances, instancePlan, transformed, groupVisibility, makeCamera, quick, previews) {
  const kit = { KIT, PixelLook };
  const width = 320, height = 200;
  const unpack = ({packed,...world}) => {
    const bytes=Uint8Array.from(atob(packed),c=>c.charCodeAt(0));
    return {...world, data:new Float32Array(bytes.buffer)};
  };
  const sizes = values => {
    const ordered = values.slice().sort((a,b)=>a-b);
    const quantile = q => ordered[Math.floor((ordered.length - 1) * q)];
    return { median:quantile(.5), p95:quantile(.95), min:ordered[0], samples:values.length };
  };
  const rows = {}, images = {};
  let driver;
  for (const [name,{source,base:packed,prototype:baked,placements,camera}] of Object.entries(fixtures)) {
    const base=unpack(packed), prototype=unpack(baked);
    const group=createSplatInstances({model:prototype},placements);
    const authored=placements.find(row=>Math.abs(row.position[0])<3 && Math.abs(row.position[2]-camera.target[2])<2) ?? placements[0];
    const plan=instancePlan(group), initial=group.get(authored.id);
    const expanded=group.flatten(base);
    const canvas=document.createElement('canvas');
    const renderer=createRenderer(canvas,{toolkit:kit});
    const gl=canvas.getContext('webgl2');
    const info=gl.getExtension('WEBGL_debug_renderer_info');
    driver=gl.getParameter(info?info.UNMASKED_RENDERER_WEBGL:gl.RENDERER);
    const options={width,height,changedRows:[]};
    const all={...camera,target:name==='woodland'?[0,0,0]:[0,0,9],dist:56,pitch:.9};
    const at=base.count+plan.rows[placements.indexOf(authored)].start;
    const change=Array.from({length:Math.ceil((at+prototype.count)/512)-Math.floor(at/512)},(_,i)=>Math.floor(at/512)+i);
    let transferBytes=0, drawn=0;
    const upload=gl.texSubImage2D.bind(gl), draw=gl.drawArraysInstanced.bind(gl);
    gl.texSubImage2D=(...args)=>{
      if(args[7]===gl.FLOAT)transferBytes+=args[4]*args[5]*16;
      return upload(...args);
    };
    gl.drawArraysInstanced=(...args)=>{drawn+=args[3];return draw(...args);};
    const samples=quick?8:24, frameCounts=quick?1:2;
    const syncPixel=new Uint8Array(4);
    const synchronize=()=>gl.readPixels(width>>1,height>>1,1,1,gl.RGBA,gl.UNSIGNED_BYTE,syncPixel);
    const drawFrame=(mode,view,dirty=[])=>{
      renderer.render(mode==='shared'?base:expanded,{...options,camera:view,changedRows:dirty,
        ...(mode==='shared'&&{instances:group})});
    };
    const read=()=>{
      const result=new Uint8Array(width*height*4);
      gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,result);
      if(gl.getError()!==gl.NO_ERROR)throw Error('WebGL readback failed');
      return result;
    };
    function parity(view) {
      drawFrame('expanded',view); const a=read();
      drawFrame('shared',view); const b=read();
      let mismatch=0, major=0, total=0, max=0;
      for(let i=0;i<a.length;i+=4){
        const err=Math.max(...[0,1,2].map(j=>Math.abs(a[i+j]-b[i+j])));
        mismatch+=+(err>0);major+=+(err>8);total+=err;max=Math.max(max,err);
      }
      return {mismatch,major,mean:total/(width*height),max};
    }
    const parityBefore=parity(camera), unedited=read();
    const patch = (i, move = true) => ({
      ...(move && { position:[initial.position[0]+.02+Math.sin(i*.41)*.12,initial.position[1],initial.position[2]] }),
      damage:i%2?{center:[0,name==='woodland'?1.6:.5,0],radius:name==='woodland'?.66:.25}:null,
      palette:i%2?{['#'+prototype.pal[name==='woodland'?8:16].toString(16).padStart(6,'0')]:'#dd9648'}:{}
    });
    group.update(authored.id,patch(1));
    transformed(expanded.data,plan.rows[placements.indexOf(authored)],at);
    const parityAfter=parity(camera), edited=read();
    let changedPixels=0;
    for(let i=0;i<edited.length;i+=4)
      changedPixels+=+(edited[i]!==unedited[i]||edited[i+1]!==unedited[i+1]||edited[i+2]!==unedited[i+2]);
    if (!changedPixels || parityBefore.major>8 || parityAfter.major>8)
      throw Error('Unexpected render parity for '+name+' '+JSON.stringify({parityBefore,parityAfter,changedPixels}));
    if (previews) {
      drawFrame('shared',camera);
      images[name]=canvas.toDataURL('image/png').split(',')[1];
    }
    const results={};
    for(const kind of ['static','orbit','edit','surfaceEdit','overview']){
      const editing=kind==='edit'||kind==='surfaceEdit';
      const modes={expanded:[],shared:[]}, metrics={};
      const drawBatch=(mode,i,collect)=>{
        const view=kind==='overview'?all:kind==='orbit'?{...camera,yaw:camera.yaw+.21*Math.sin(i*.23)}:camera;
        synchronize();transferBytes=drawn=0;
        const start=performance.now();
        for(let k=0;k<frameCounts;k++){
          if(editing){
            group.update(authored.id,patch(i*frameCounts+k,kind==='edit'));
            if(mode==='expanded')transformed(expanded.data,plan.rows[placements.indexOf(authored)],at);
          }
          drawFrame(mode,kind==='orbit'?{...view,yaw:view.yaw+.006*k}:view,editing&&mode==='expanded'?change:[]);
        }
        const submitted=performance.now();
        synchronize();
        const elapsed=performance.now()-start;
        if(collect)modes[mode].push({elapsed:elapsed/frameCounts,submit:(submitted-start)/frameCounts,
          drawn:drawn/frameCounts,upload:transferBytes/frameCounts});
      };
      for(let warm=0;warm<6;warm++)for(const mode of ['expanded','shared'])drawBatch(mode,warm,false);
      // Warm each representation after switching. Switching itself can upload the scene.
      for(let round=0;round<4;round++)for(const mode of round%2?['shared','expanded']:['expanded','shared']){
        drawBatch(mode,round*samples,false);
        for(let i=0;i<samples/4;i++)drawBatch(mode,round*samples+i,true);
      }
      for(const [mode,values] of Object.entries(modes))metrics[mode]={
        frameMs:sizes(values.map(row=>row.elapsed)),submitMs:sizes(values.map(row=>row.submit)),
        orderedDraws:sizes(values.map(row=>row.drawn)).median,textureUploadBytes:sizes(values.map(row=>row.upload)).median
      };
      results[kind]=metrics;
    }
    const cameraState=makeCamera(base,{camera},width,height);
    const visible=groupVisibility(plan,cameraState,width,height,1).length;
    const geometryBytes = count => Math.max(1,Math.ceil(count/512))*512*64;
    rows[name]={source, placements:placements.length, visible, canvas:[width,height], baseSplats:base.count,
      sharedSplats:group.sharedSplats, expandedSplats:expanded.count,
      residentTextureBytes:{expanded:geometryBytes(expanded.count),
        shared:geometryBytes(base.count+group.sharedSplats)+Math.ceil((group.count+1)/16)*4096},
      parityBefore,parityAfter,changedPixels,results};
    renderer.dispose();
    gl.getExtension('WEBGL_lose_context')?.loseContext();
  }
  return { driver, browser:navigator.userAgent, fixtures:rows, ...(previews&&{images}) };
}

const previews = process.env.INK_BENCHMARK_PREVIEW_DIR;
const temp = fs.mkdtempSync(path.join(os.tmpdir(),'ink-instances-'));
try {
  const url = file => pathToFileURL(path.resolve(__dirname,'..',file)).href;
  fs.writeFileSync(path.join(temp,'bundle.js'),studio.bundle());
  fs.writeFileSync(path.join(temp,'fixture.js'),'const scenes = '+JSON.stringify(scenes())+';');
  const page=path.join(temp,'fixture.html');
  fs.writeFileSync(page,`<!doctype html><pre id="result">pending</pre><script src="bundle.js"></script><script src="fixture.js"></script><script type="module">
import {createRenderer,createSplatInstances} from ${JSON.stringify(url('webgl.mjs'))};
import {instancePlan,transformed} from ${JSON.stringify(url('src/webgl/instances.mjs'))};
import {groupVisibility} from ${JSON.stringify(url('src/webgl/instance-draw.mjs'))};
import {makeCamera} from ${JSON.stringify(url('src/webgl/view.mjs'))};
try {
  const report=(${browser.toString()})(scenes,createRenderer,createSplatInstances,instancePlan,transformed,groupVisibility,makeCamera,${quick},${!!previews});
  document.querySelector('#result').textContent=encodeURIComponent(JSON.stringify(report));
} catch(error){document.querySelector('#result').textContent=encodeURIComponent(JSON.stringify({error:error.stack}));}
</script>`);
  const options=hardware?[]:['--use-angle=swiftshader','--enable-unsafe-swiftshader'];
  const html=execFileSync(executable,['--headless','--no-first-run','--disable-background-networking',
    '--allow-file-access-from-files',...options,'--user-data-dir='+path.join(temp,'profile'),'--dump-dom',pathToFileURL(page).href],
    {timeout:300000,maxBuffer:12*1024*1024,encoding:'utf8',stdio:['ignore','pipe','ignore']});
  const text=/<pre id="result">([^<]*)<\/pre>/.exec(html)?.[1];
  if(!text || text==='pending')throw Error('Chrome did not complete the instance benchmark');
  const result=JSON.parse(decodeURIComponent(text));
  if(result.error)throw Error(result.error);
  if(result.images){
    fs.mkdirSync(previews,{recursive:true});
    for(const [name,encoded] of Object.entries(result.images))
      fs.writeFileSync(path.join(previews,'gpu-instancing-'+name+'.png'),Buffer.from(encoded,'base64'));
    delete result.images;
  }
  process.stdout.write(JSON.stringify(result,null,2)+'\n');
} finally {
  fs.rmSync(temp,{recursive:true,force:true});
}

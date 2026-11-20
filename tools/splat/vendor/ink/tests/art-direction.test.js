const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('..');
const { KIT: K, ArtDirection, makeBuilder } = ink.load();
const clouds = require('../src/cloud-field.js');
const { traceMedia } = require('../cli/scene-optics.js');
const cam = {target:[0,0,0],dist:6,pitch:0,yaw:0};
const opts = {w:71,h:49,px:1,raw:true};
const pal = [0x182d42,0x948c81,0xffaf57];
const sample = (f,x,y) => [...f.rgb.subarray((y*f.w+x)*3,(y*f.w+x)*3+3)];
const hasChange = (a,b) => a.rgb.some((n,i)=>n!==b.rgb[i]);

test('art direction prepares validated presets with independent optical and cadence overrides',()=>{
  assert.deepEqual(ArtDirection.presets,['painted-pixel','storm-silhouette','soft-dawn']);
  const config=ArtDirection.prepare('soft-dawn',{preset:'storm-silhouette',atmosphereBands:0,cadence:{environment:16},foreground:false});
  assert.equal(config.bands,null);
  assert.equal(config.foreground,null);
  assert.equal(ArtDirection.time(config,.24),.125);
  assert.equal(ArtDirection.time(config,.24,'environment'),.1875);
  assert.equal(ArtDirection.time(config,1/8),.125);
  assert.equal(ArtDirection.prepare('soft-dawn',false),null);
  assert.throws(()=>ArtDirection.prepare({atmosphereBands:1}),/integer from 2 to 64/);
  assert.throws(()=>ArtDirection.prepare({foreground:{near:4,far:3}}),/Foreground far/);
  assert.throws(()=>ArtDirection.prepare({cadence:{scene:-1}}),/Scene cadence/);
});

test('cloud edges remap visible coverage across sheets and volumetric LOD without changing the cloud lighting color',()=>{
  const lo=ArtDirection.prepare({cloudEdge:0}).cloudEdge, hi=ArtDirection.prepare({cloudEdge:1}).cloudEdge;
  const src={bounds:{min:[-5,-5],max:[5,5]},resolution:[14,14],height:2,opacity:.75,color:'#75869b',coverage:()=>.28};
  const origin=[0,-1,0], ray=[0,1,0];
  for (const [asset,mode] of [[clouds.compile(src),'off'],[clouds.asset({...src,thickness:2},{resolution:24}),'volume'],
    [clouds.asset({...src,thickness:2},{resolution:24}),'impostor']]) {
    function read(curve) {
      const frame=asset.frame(0,undefined,undefined,undefined,mode,undefined,undefined,curve);
      if (mode==='off') {
        const signal=[0], rgb=frame.paint(origin,ray,[0,0,0],null,signal);
        return [...rgb,1-signal[0]];
      }
      return frame.view(origin).trace(origin,ray,0,10,[0,0,0,1]);
    }
    const plain=read(null), soft=read(lo), hard=read(hi);
    assert(soft[3]<plain[3] && hard[3]>plain[3],mode);
    for (const data of [soft,hard]) if (data[3]<1)
      assert(Math.abs(data[0]/(1-data[3])-plain[0]/(1-plain[3]))<1e-7);
  }
});

test('banding steps sky and aerial/fog sampling while leaving the water and cloud channels distinct',()=>{
  const B=makeBuilder(1,pal);
  const world=B.finish({cam,skyEnvironment:{defaults:{zenith:'#14285f',horizon:'#a6c1c9',ground:'#142a2f',sunStrength:0}}});
  const plain=ink.render(world,opts), stepped=ink.render(world,{...opts,artDirection:{atmosphereBands:3}});
  const count=f=>new Set(Array.from({length:f.w*f.h},(_,p)=>f.rgb.slice(p*3,p*3+3).join(','))).size;
  assert(count(plain)>count(stepped)*3);
  const bands=ArtDirection.prepare({atmosphereBands:4}).bands;
  const fog=require('../src/scene-optics.js').prepareVolumes([K.atmosphere.fog({density:.18,color:'#aaccdd'})],pal);
  const fogRay=traceMedia(fog,[],[0,0,0],[1,0,0],4,new Float64Array(8),[0,0,0,1],{bands});
  assert(Math.abs(fogRay[6]-2/3)<1e-8);
  assert.equal(fogRay[7],0);
  const water={extinction:[.2,.3,.4],tint:[.15,.27,.53],deepTint:[.09,.17,.31],depthRange:[0,5]};
  const base=[[],[[1,3,water,0]],[0,0,0],[1,0,0],4];
  assert.deepEqual(traceMedia(...base,new Float64Array(8),[0,0,0,1],{bands}),
    traceMedia(...base,new Float64Array(8),[0,0,0,1],{}));
});

test('foreground contrast changes nearby geometry and preserves sky, far geometry and emissive colors',()=>{
  const B=makeBuilder(1,pal);
  B.disc(-1.32,0,1,[0,0,1],.25,.06,B.P[1],3);
  B.disc(1.32,0,1,[0,0,1],.25,.06,B.P[2],3,{em:true});
  B.disc(0,0,-6,[0,0,1],.21,.06,B.P[1],3);
  const world=B.finish({cam});
  for (const ortho of [true,false]) {
    const view={...opts,ortho,passes:['splatId']};
    const plain=ink.render(world,view);
    const contrast=ink.render(world,{...view,artDirection:{foreground:{contrast:2,pivot:.9,near:6,far:10}}});
    let samples=0;
    for (let p=0;p<plain.w*plain.h;p++) {
      const id=plain.passes.splatId[p];
      const before=sample(plain,p%plain.w,Math.floor(p/plain.w)), after=sample(contrast,p%plain.w,Math.floor(p/plain.w));
      if (id===1) { assert(after[0]<before[0]); samples++; }
      if (id===3||id===2) assert.deepEqual(after,before);
    }
    assert(samples>15);
    assert.deepEqual(sample(contrast,0,0),sample(plain,0,0));
  }
});

test('held scenes and environments can run at separate cadences while the camera continues moving',()=>{
  const B=makeBuilder(1,pal);
  B.disc(0,0,0,[0,0,1],.35,.04,B.P[1],3,{k:6,rg:1,sp:4});
  const sky={profiles:{a:{horizon:'#6b7c9a'},b:{horizon:'#cd7450'}},
    sequences:{change:{duration:2,loop:false,keys:[{at:0,profile:'a',ease:'linear'},{at:1,profile:'b'}]}},
    tracks:[{id:'sky',sequence:'change'}],defaults:{sunStrength:0}};
  const world=B.finish({cam,skyEnvironment:sky,look:{artDirection:{cadence:{scene:4,environment:2}}}});
  const a=ink.render(world,{...opts,t:.02}), b=ink.render(world,{...opts,t:.22});
  assert(!hasChange(a,b));
  assert(hasChange(a,ink.render(world,{...opts,t:.22,artDirection:false})));
  assert(hasChange(a,ink.render(world,{...opts,t:.22,yaw:.17})));
  assert(hasChange(a,ink.render(world,{...opts,t:.22,skyTime:.64})));
  const smooth=ink.render(world,{...opts,t:.22,artDirection:{cadence:{scene:4,environment:0}}});
  assert(hasChange(a,smooth));
  assert.deepEqual(sample(a,36,24),sample(smooth,36,24));
});

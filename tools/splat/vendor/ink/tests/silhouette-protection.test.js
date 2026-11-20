const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('..');
const { KIT:K, makeBuilder, SilhouetteProtection, SceneOptics }=ink.load();
const {traceMedia}=require('../cli/scene-optics.js');
const camera={target:[0,0,0],dist:6,pitch:0,yaw:0};
const view={w:88,h:60,px:1,raw:true,captureSilhouetteProtection:true,captureFog:true,passes:['objectId']};
const pal=[0x203042,0xb9653b,0x4e6680,0xdcb87c];
const protectedRule={targets:[{id:'hero',select:{object:'actor'},fogScale:.12,contrast:1.6,pivot:.45}]};
const rgb=(frame,p)=>Array.from(frame.rgb.subarray(p*3,p*3+3));

function scene({cover=false, aerial=false, fog=true}={}) {
  const B=makeBuilder(1,pal);
  function disc(x,z,color,object) {
    const start=B.count();
    B.disc(x,0,z,[0,0,1],.31,.04,B.P[color],3);
    B.describeSplats(start,B.count(),{object,material:object});
  }
  disc(-.98,0,1,'actor');
  disc(.98,0,2,'prop');
  if (cover) disc(-.98,.5,3,'wall');
  return B.finish({
    cam:camera,radius:7,atmosphere:fog?[K.atmosphere.fog({density:.31,color:'#a7bfcb'})]:[],
    aerialPerspective:aerial && {start:.05,density:.12,contrast:.1},
    skyEnvironment:{defaults:{zenith:'#576885',horizon:'#9cb7c8',ground:'#354659',sunStrength:0}},
    look:{silhouetteProtection:protectedRule},volumeQuality:{scale:3}
  });
}

test('named protection clears only the selected visible subject on both volume render paths',()=>{
  for (const aerial of [false,true]) {
    const w=scene({aerial});
    const off=ink.render(w,{...view,silhouetteProtection:false});
    const on=ink.render(w,view);
    let changed=0, compared=0;
    for(let p=0;p<on.w*on.h;p++) {
      const name=on.passes.objects[on.passes.objectId[p]];
      if (on.silhouetteMask[p]===1) {
        assert.equal(name,'actor');
        assert(on.fog[p]<off.fog[p]);
        if (rgb(on,p).some((v,i)=>v!==rgb(off,p)[i])) changed++;
      } else if (name==='prop') {
        assert.deepEqual(rgb(on,p),rgb(off,p));
        assert.equal(on.fog[p],off.fog[p]);
        compared++;
      }
    }
    assert(changed>40 && compared>40);
    assert.deepEqual(rgb(on,0),rgb(off,0));
  }
});

test('protection follows depth ownership and can change contrast without fog',()=>{
  const w=scene({cover:true,fog:false});
  const config={targets:[{select:{object:'actor'},contrast:2,pivot:.68}]};
  const opts={...view,silhouetteProtection:config};
  for (const splatOrder of ['center','surface']) {
    const on=ink.render(w,{...opts,splatOrder});
    const off=ink.render(w,{...opts,splatOrder,silhouetteProtection:false});
    let checked=0;
    for(let p=0;p<on.w*on.h;p++) {
      const name=on.passes.objects[on.passes.objectId[p]];
      if(name==='wall') {assert.equal(on.silhouetteMask[p],0);checked++;}
    }
    assert(checked>40);
    const behind=30*88+29;
    assert(rgb(on,behind).every((value,i)=>Math.abs(value-rgb(off,behind)[i])<=2));
  }
  const visible=scene({fog:false});
  const on=ink.render(visible,opts),off=ink.render(visible,{...opts,silhouetteProtection:false});
  assert(on.silhouetteMask.some((id,p)=>id && rgb(on,p)[0]!==rgb(off,p)[0]));
});

test('fog scale preserves independent water, cloud, and solid occlusion',()=>{
  const volume=K.atmosphere.field({field:K.procedural.density.bounded({
    bounds:{min:[-1,-1,-1],max:[6,1,1]},sample:()=>1}),density:.5,lit:false,color:'#bcd6ca'});
  const fog=SceneOptics.prepareVolumes([volume]);
  const thin=SceneOptics.trace(fog,[0,0,0],[1,0,0],4,[0,0,0,1],{fogScale:.25});
  assert(Math.abs(thin[3]-Math.exp(-.5))<1e-9);
  const water={extinction:[.22,.35,.49],tint:[.11,.23,.31],deepTint:[.08,.16,.25],depthRange:[0,3]};
  const cloud={trace(_o,_d,_start,_stop,out){out[0]=.07;out[1]=.12;out[2]=.19;out[3]=.64;}};
  const sample=(volumes,scale)=>traceMedia(volumes,[[1,3,water,0]],[0,0,0],[1,0,0],5,new Float64Array(8),
    [0,0,0,1],{cloud,fogScale:scale},{start:0,density:.18,contrast:.2,color:[.3,.5,.7]});
  const clear=sample(fog,0);
  assert.equal(clear[6],0);
  assert(clear[7]>.05 && clear[3]<.6);
  assert(sample(fog,1)[6]>.3);
  assert.deepEqual(clear,sample([],0));
});

test('named atlas placements can use the same protected silhouette lookup',()=>{
  const B=makeBuilder(1,pal);
  const atlas={metadata:{width:1,height:1,unitsPerPixel:1,frames:[{rect:{x:0,y:0,width:1,height:1}}]},
    images:{color:Uint8Array.of(195,96,44,255)}};
  const w=B.finish({cam:camera,atmosphere:[K.atmosphere.fog({density:.57,color:'#afc4d2'})],
    spriteAtlases:[K.sprite.placeAtlas({atlas,objectId:'actor',at:[0,0,0]})]});
  const p=30*88+44;
  const on=ink.render(w,{...view,silhouetteProtection:protectedRule});
  const off=ink.render(w,{...view,silhouetteProtection:false});
  assert.equal(on.silhouetteMask[p],1);
  assert(on.fog[p]<off.fog[p]);
  assert.notDeepEqual(rgb(on,p),rgb(off,p));
});

test('review uses every sprite export heading and pitch and measures visible edge contrast at native size',()=>{
  const w=scene();
  const width=36,height=34,directions=4,pitches=[.06,.25];
  const {image,report}=ink.silhouetteReview(w,{width,height,directions,pitches,view:{raw:true}});
  const exported=require('../cli/sprite-atlas.js').spriteAtlas(w,{width,height,directions,pitches});
  assert.equal(report.views.length,8);
  assert.deepEqual(report.views.map(({yaw,pitch})=>[yaw,pitch]),exported.metadata.frames.map(({yaw,pitch})=>[yaw,pitch]));
  assert.equal(report.width,width);
  assert.equal(report.height,height);
  assert(report.views.some(({targets:[row]})=>row.edgeSamples>0&&row.protected>row.before));
  assert(image.rgb.some(Boolean));
  assert.throws(()=>SilhouetteProtection.prepare({targets:[{select:{medium:'fog'}}]}),/scene subject/);
  assert.throws(()=>SilhouetteProtection.prepare({targets:[{select:{object:'actor'},fogScale:-1}]}),/fog scale/);
});

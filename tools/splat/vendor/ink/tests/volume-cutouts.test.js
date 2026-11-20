const assert=require('node:assert/strict');
const test=require('node:test');
const ink=require('..');
const { KIT:K, makeBuilder, makeSculpt }=ink.load();
const close=(value,expected,tolerance=1e-10)=>assert(Math.abs(value-expected)<tolerance,value+' vs '+expected);

test('boxes, routes and animated face pockets keep clear cores and feather outward', () => {
  let samples=0;
  const setup=K.atmosphere.cutouts({zones:[
    {type:'box',min:[-1,-1,-1],max:[1,1,1],feather:.5,affects:'fog'},
    {type:'sphere',at:t=>{ samples++;return [4+t,2,0]; },radius:.42,feather:.4},
    {type:'path',path:K.anim.path([[-3,0,4],[0,0,5],[3,0,4]]),radius:.6,aspect:.5,feather:.4,retain:.2},
    {type:'sdf',bounds:{min:[-5,-2,-5],max:[-3,2,-3]},
      field:(x,y,z)=>Math.hypot(x+4,y,z+4)-.7,feather:.2}
  ]});
  const state=setup.frame(0);
  assert.equal(samples,1);
  assert.equal(state.fog.gain(0,0,0),0);
  assert.equal(state.cloud.gain(0,0,0),1);
  close(state.fog.gain(1.25,0,0),.5);
  assert.equal(state.fog.gain(1.51,0,0),1);
  close(state.fog.gain(0,0,5),.2);
  assert(state.fog.gain(0,.38,5)>.2 && state.fog.gain(0,.38,5)<1);
  assert.equal(state.fog.gain(-4,0,-4),0);
  assert.equal(state.fog.gain(4,2,0),0);
  assert.equal(setup.frame(2).fog.gain(4,2,0),1);
  assert.equal(setup.frame(2).fog.gain(6,2,0),0);
  assert.equal(setup.frame(0).fog.gain(4,2,0),0);
  assert.throws(()=>K.atmosphere.cutouts({zones:[{type:'sphere',at:[0,0,0],radius:-1}]}),/radius/);
  assert.throws(()=>K.atmosphere.cutouts({zones:[{type:'box',min:[0,0,0],max:[1,1,1],feather:-1}]}),/feather/);
});

test('thin cutouts affect analytic fog and coarse marched extinction and compose with shelter', () => {
  const bounds={min:[-10,-1,-1],max:[10,1,1]};
  const fog=K.atmosphere.prepare([K.atmosphere.box({...bounds,density:.3})]);
  const field=K.procedural.density.bounded({bounds,sample:()=>1});
  const fieldFog=K.atmosphere.prepare([K.atmosphere.field({ field,density:.3,lit:false })]);
  const cutouts=K.atmosphere.cutouts({zones:[
    {type:'box',min:[-.02,-.8,-.8],max:[.02,.8,.8],feather:.10,affects:'fog'}
  ]}).frame();
  const origin=[-10,0,0], direction=[1,0,0];
  const uncut=K.atmosphere.trace(fog,origin,direction,20);
  for (const volumes of [fog,fieldFog]) {
    const cleared=K.atmosphere.trace(volumes,origin,direction,20,undefined,{cutouts,maxSteps:1});
    close(cleared[3],Math.exp(-.3*19.86));
    assert(cleared[3]>uncut[3]);
  }
  const exposure=K.weather.exposure({zones:[{min:[-11,-2,-2],max:[11,2,2],fade:0,fog:.5}]});
  close(K.atmosphere.trace(fog,origin,direction,20,undefined,{cutouts,exposure})[3],Math.exp(-.15*19.86));
  const path=K.atmosphere.cutouts({zones:[{type:'path',
    points:[[-8,0,0],[-3,0,0],[1,0,0],[8,0,0]],radius:.17,feather:0}]}).frame().fog;
  const ray=path.ray([5,0,2],[0,0,-1],0,4);
  close(ray.distance(0,4),3.66);
});

test('cloud volume, impostor, card, backdrop and shadow sample the same clear pocket', () => {
  const cutouts=K.atmosphere.cutouts({zones:[
    {type:'box',min:[-.65,-3,-4],max:[.65,3,4],feather:.15,affects:'cloud'}
  ]}).frame();
  const bounds={min:[-3,-3],max:[3,3]};
  const layer=K.clouds.asset({bounds,coverage:()=>1,thickness:2,height:0,opacity:1,resolution:[24,24]},
    {resolution:48});
  const eye=[0,0,16], direction=[0,0,-1];
  for (const mode of ['card','impostor','volume']) {
    const bare=layer.frame(0,undefined,undefined,undefined,mode).view(eye);
    const masked=layer.frame(0,undefined,undefined,undefined,mode,undefined,cutouts.cloud).view(eye);
    assert(bare.trace(eye,direction,0,25,[0,0,0,1])[3]<.5);
    const clear=masked.trace(eye,direction,0,25,[0,0,0,1]);
    close(clear[3],1);
    assert(masked.trace([1.65,0,16],direction,0,25,[0,0,0,1])[3]<.5,mode);
  }
  const deck=K.clouds.compile({bounds,coverage:()=>1,opacity:1,height:0});
  const shadow=K.clouds.shadowSettings({strength:1,softness:0,direction:[0,1,0]});
  const painted=deck.frame(0,shadow,undefined,undefined,undefined,undefined,cutouts.cloud);
  assert.deepEqual(painted.paint([0,-1,0],[0,1,0],[0,0,0]),[0,0,0]);
  assert(painted.paint([1.6,-1,0],[0,1,0],[0,0,0])[0]>.6);
  assert.equal(painted.shadow(0,-1,0),1);
  assert.equal(painted.shadow(1.6,-1,0),0);
});

test('headless cutouts clear a moving face through shaped fog without changing the surrounding fog', () => {
  const B=makeBuilder(6,[0x171229,0xc37635,0x8d643b]);
  const S=K.sculpt(makeSculpt(B));
  S.box([-.7,0,0],[.17,.27,.08],{r:[1],em:true,materialId:'face'},{res:.047});
  S.box([1.3,0,0],[.17,.27,.08],{r:[2],em:true,materialId:'marker'},{res:.047});
  S.bake();
  const pocket=K.atmosphere.cutouts({zones:[
    {type:'path',points:[[-.7,0,1],[-.7,0,5]],radius:.48,feather:.14,affects:'fog'},
    {type:'sphere',at:t=>[-.7+3*t,0,.47],radius:.83,feather:.18,affects:'fog'}
  ]});
  const world=B.finish({
    cam:{target:[0,0,0],dist:5,yaw:0,pitch:0},dither:0,
    shapedAtmosphere:[K.atmosphere.shaped({source:{type:'sdf',bounds:{min:[-3,-2,-2],max:[3,2,4]},
      field:()=>-1 },density:1,color:'#b8c9e3',lit:false})], volumeCutouts:pocket
  });
  const settings={w:112,h:68,px:1,raw:true,passes:['coverage','materialId']};
  const mist=ink.render(world,{...settings,volumeCutouts:false}), open=ink.render(world,settings);
  const moved=ink.render(world,{...settings,t:1});
  const {coverage,materialId,materials}=open.passes;
  let clearFace=0, calmMarker=0;
  for(let p=0;p<coverage.length;p++){
    if(coverage[p]<.98) continue;
    const site=materials[materialId[p]],j=p*3+2;
    if(site==='face'&&mist.rgb[j]-open.rgb[j]>90&&moved.rgb[j]-open.rgb[j]>30) clearFace++;
    if(site==='marker'&&Math.abs(mist.rgb[j]-open.rgb[j])<=1) calmMarker++;
  }
  assert(clearFace>10 && calmMarker>10,clearFace+' '+calmMarker);
  const quality={...settings,volumeQuality:{jitter:'spatiotemporal'}}, history=K.atmosphere.history();
  ink.render(world,{...quality,t:0,volumeHistory:history});
  assert.deepEqual(ink.render(world,{...quality,t:.09,volumeHistory:history}).rgb,
    ink.render(world,{...quality,t:.09}).rgb);
});

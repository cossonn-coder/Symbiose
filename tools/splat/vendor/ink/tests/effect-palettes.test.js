const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('..');
const { KIT: K, makeBuilder, EffectPalettes } = ink.load();
const { traceMedia } = require('../cli/scene-optics.js');
const view = { w: 72, h: 48, px: 1, captureEffectPalettes: true };
const cam = { target:[0, .2, 0], dist:6, yaw:0, pitch:-.20 };
const palette = [0x1b2540,0x4b5e6c,0x987866,0xffcf75];
const sky = { defaults:{zenith:'#080e32',horizon:'#617da4',ground:'#425a6d',sunStrength:0,daylight:.15} };
const colors = (frame,p) => {
  const q=p*3, {rgb}=frame;
  return (rgb[q]<<16)|(rgb[q+1]<<8)|rgb[q+2];
};
const selected = frame => new Set(frame.effectPaletteMask);
const different = (a,b) => a.rgb.some((v,i)=>v!==b.rgb[i]);

test('night sky palettes use native shaded tone steps in both standard and colored resolve', () => {
  const B=makeBuilder(1,palette);
  B.disc(0,.2,0,[0,0,1],.46,.05,B.P[2],3);
  const ramp=['#0b0d2c','#192c74','#476db7','#aac4eb'];
  const world=B.finish({cam,skyEnvironment:sky,look:{effectPalettes:{
    sky:{colors:ramp,range:[.08,.57],when:{channel:'daylight',max:.3}}
  }}});
  for (const colored of [false,true]) {
    const off=ink.render(world,{...view,colored,effectPalettes:false});
    const frame=ink.render(world,{...view,colored});
    assert.deepEqual([...selected(frame)].sort(),[0,3]);
    const painted=new Set();
    for (let p=0;p<frame.w*frame.h;p++) {
      if (frame.effectPaletteMask[p]) painted.add(colors(frame,p));
      else assert.equal(colors(frame,p),colors(off,p));
    }
    assert(painted.size>=2);
    assert([...painted].every(color=>ramp.includes('#'+color.toString(16).padStart(6,'0'))));
    assert.equal(frame.use.reduce((sum,n)=>sum+n,0),frame.w*frame.h);
  }
  const day=ink.render(world,{...view,skyEnvironment:{defaults:{...sky.defaults,daylight:.8}}});
  assert.equal(day.effectPaletteMask,undefined);
  const raw=ink.render(world,{...view,raw:true});
  assert(!different(raw,ink.render(world,{...view,raw:true,effectPalettes:false})));
});

test('cloud and fog attribution stays separate in sheets, cloud volumes, and impostors', () => {
  const cloud = { bounds:{min:[-5,-34],max:[5,-2]}, height:2.4, thickness:1.25, steps:18,
    resolution:[12,12], coverage:() => .92, color:'#8d7e9b', opacity:.88 };
  for (const [source,representation] of [[K.clouds.compile(cloud),'off'],[K.clouds.asset(cloud,{resolution:32}),'volume'],
    [K.clouds.asset(cloud,{resolution:32}),'impostor']]) {
    const world=makeBuilder(1,palette).finish({cam,skyEnvironment:sky,cloudField:source,cloudRepresentation:representation});
    const frame=ink.render(world,{...view,effectPalettes:{
      sky:['#130f36'],fog:{colors:['#ff2200'],threshold:.03},clouds:{colors:['#9684c2'],threshold:.06}
    }});
    assert(selected(frame).has(2),representation+' produces cloud pixels');
    assert(!selected(frame).has(1));
    assert(selected(frame).has(3),representation+' leaves openings for the sky palette');
  }
  const water={extinction:[.8,.4,.2],tint:[.1,.4,.7],deepTint:[.07,.1,.3],depthRange:[0,4]};
  const depths=traceMedia([],[[1,3,water,0]],[0,0,0],[1,0,0],4,new Float64Array(8),[0,0,0,1],{});
  assert(depths[3]<.5);
  assert.equal(depths[6],0);
  assert.equal(depths[7],0);
});

test('fog can band distant geometry while named subjects and their rendered colours stay intact', () => {
  const B=makeBuilder(1,palette);
  for (const [x,id,material] of [[-1.35,'courier','canvas'],[0,'crate','prop'],[1.35,'sign','waypoint']]) {
    const first=B.count();
    B.disc(x,.2,0,[0,0,1],.45,.05,B.P[2],3);
    B.describeSplats(first,B.count(),{object:id,material});
  }
  const world=B.finish({cam,skyEnvironment:sky,atmosphere:[K.atmosphere.fog({density:.8,color:'#6199ae',near:2,far:14})]});
  const config={protect:{objects:['courier'],materials:['waypoint']},
    fog:{colors:['#198eb0'],geometry:true,threshold:.3}};
  const settings={...view,passes:['objectId','materialId']};
  const off=ink.render(world,{...settings,effectPalettes:false});
  const on=ink.render(world,{...settings,effectPalettes:config});
  let protectedCount=0, foggedCount=0;
  for (let p=0;p<on.w*on.h;p++) {
    const object=on.passes.objects[on.passes.objectId[p]];
    if (object==='courier' || object==='sign') {
      assert.equal(colors(off,p),colors(on,p));
      assert.equal(on.effectPaletteMask[p],0);
      protectedCount++;
    } else if (object==='crate' && on.effectPaletteMask[p]===1) foggedCount++;
  }
  assert(protectedCount>30 && foggedCount>10);
  const bg=ink.render(world,{...settings,effectPalettes:{fog:['#198eb0']}});
  assert(bg.effectPaletteMask.some((id,p)=>id===1 && !bg.passes.objectId[p]));
  assert(!bg.effectPaletteMask.some((id,p)=>id===1 && bg.passes.objectId[p]));
});

test('emission claims visible lights ahead of fog using their rendered intensity', () => {
  const B=makeBuilder(1,palette);
  B.disc(0,.2,0,[0,0,1],.46,.04,B.P[3],3,{em:true});
  B.disc(0,.2,.35,[0,0,1],.16,.03,B.P[1],3);
  const world=B.finish({cam,atmosphere:[K.atmosphere.fog({density:.26,color:'#a7bbc4'})]});
  const frame=ink.render(world,{...view,effectPalettes:{
    fog:{colors:['#286285'],geometry:true,threshold:.2},
    emission:{colors:['#f76a37','#fff0b6'],range:[.45,.9],threshold:.23}
  }});
  const center=24*frame.w+36;
  assert(frame.effectPaletteMask.some((kind,p)=>kind===4 && [0xf76a37,0xfff0b6].includes(colors(frame,p))));
  assert.equal(frame.effectPaletteMask[center],1);
  const disabled=ink.render(world,{...view,effectPalettes:false});
  assert.equal(disabled.effectPaletteMask,undefined);
});

test('legacy baked haze participates only when the fog ramp can recolor a surface', () => {
  const B=makeBuilder(1,palette);
  B.disc(0,0,-3,[0,0,1],1,.05,B.P[2],3);
  const world=B.finish({cam, radius:8, fog:{c:1,start:0,max:1}});
  const base=ink.render(world,{...view,effectPalettes:{fog:{colors:['#63a9ba'],threshold:.12}}});
  const tinted=ink.render(world,{...view,effectPalettes:{fog:{colors:['#63a9ba'],threshold:.12,geometry:true}}});
  assert(!base.effectPaletteMask.some(id=>id===1));
  assert(tinted.effectPaletteMask.some(id=>id===1));
  assert.throws(()=>EffectPalettes.prepare({cloud:['#ffffff']},palette),/Invalid effect palette/);
  assert.throws(()=>EffectPalettes.prepare({sky:{colors:[9]}},palette),/scene palette index/);
});

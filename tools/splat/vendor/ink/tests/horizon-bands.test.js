const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const ink = require('..');
const { HorizonBands, makeBuilder } = ink.load();
const PNG = require('../cli/png.js');

const image = { width: 2, height: 1, pixels: [255,0,0,255, 0,255,0,255] };
const band = { id:'ridge', radius:20, height:[-30,30], image };
const config = { camera:{yaw:[0,360],pitch:[-90,90]}, bands:[band] };
const radians = n => n * Math.PI / 180;
const ray = (degrees, y = 0) => [Math.sin(radians(degrees)), y, Math.cos(radians(degrees))];
const at = (paint, degrees, y) => paint(ray(degrees, y), [0,0,0]);
const view = { eye:[0,0,0], yaw:0, pitch:0, distance:5 };
const red = [1,0,0], green = [0,1,0], black = [0,0,0];

test('horizon artwork tiles only within its authored arc and wraps world azimuth continuously', () => {
  const panorama = HorizonBands.compile({ ...config, bands:[{ ...band, azimuth:[312,402], repeat:3 }] }).frame(view);
  assert.deepEqual(at(panorama,320), red);
  assert.deepEqual(at(panorama,335), green);
  assert.deepEqual(at(panorama,350), red);
  assert.deepEqual(at(panorama,365), green);
  assert.deepEqual(at(panorama,380), red);
  assert.deepEqual(at(panorama,395), green);
  assert.deepEqual(at(panorama,309), black);
  assert.deepEqual(at(panorama,48), black);
  assert.deepEqual(at(panorama,350,2), black);
  assert.deepEqual(at(panorama,359.999), at(panorama,.001));
  const full = HorizonBands.compile(config);
  assert.deepEqual(at(full.frame(view), 70), at(full.frame({ ...view, yaw:radians(360) }), 70));
  assert.deepEqual(at(full.frame(view), 180 - .01), red);
  assert.deepEqual(at(full.frame({ ...view, eye:[3,0,0] }), 180 - .01), red);
  const shifted = { ...view, eye:[-3,0,0] };
  assert.deepEqual(at(full.frame(shifted), 175), green);
  const far = HorizonBands.compile({ ...config, bands:[{ ...band, radius:100 }] });
  assert.deepEqual(at(far.frame(shifted), 175), red);
});

test('camera bounds handle seam-crossing yaw, fades, pitch, dolly and the cylinder rim', () => {
  const art = HorizonBands.compile({ ...config, camera:{
    yaw:[345,385], pitch:[-10,24], distance:[4,20], fade:{yaw:10,pitch:4,distance:4}
  } });
  assert.equal(art.frame({ ...view, yaw:radians(30) }), null);
  assert.equal(art.frame({ ...view, pitch:radians(-11) }), null);
  assert.equal(art.frame({ ...view, distance:21 }), null);
  assert.equal(art.frame({ ...view, eye:[20,0,0] }), null);
  const paint = art.frame({ ...view, yaw:radians(-10), pitch:radians(-8), distance:6 });
  assert(Math.abs(at(paint,10)[0] - .125) < 1e-10);
  assert.deepEqual(at(art.frame({ ...view, yaw:radians(370), distance:10 }),10), red);
  const rim = HorizonBands.compile(config).frame({ ...view, eye:[19,0,0] });
  assert(Math.abs(at(rim,90)[0] - .5) < 1e-10);
});

test('overlap composites far to near and accepts sky gain and tint channels', () => {
  const layer = (id,radius,color,alpha) => ({
    ...band,id,radius,image:{width:1,height:1,pixels:[...color,alpha]}
  });
  const near = { ...layer('near',16,[0,255,0],255), gain:'ridgeGain', tint:'ridgeTint' };
  const far = layer('far',34,[255,0,0],255);
  const art = HorizonBands.compile({ ...config, bands:[near,far] });
  assert.deepEqual(at(art.frame({ ...view, parameters:{ridgeGain:.5,ridgeTint:[1,.75,1]} }), 0), [.5,.375,0]);
  assert.deepEqual(at(art.frame(view), 0), green);
  assert.throws(() => art.frame({ ...view, parameters:{} }), /ridgeGain/);
  assert.throws(() => HorizonBands.compile({ ...config, bands:[band,band] }), /unique names/);
  assert.throws(() => HorizonBands.compile({ ...config, bands:[{...band,repeat:0}] }), /repeat/);
  assert.throws(() => HorizonBands.compile({ ...config, camera:{ ...config.camera,pitch:[30,-30] } }), /Camera pitch/);
});

test('perspective and orthographic orbit retain foreground and animated world-space effect registration', () => {
  const B = makeBuilder(1,[0x101a2e,0xd5b786,0xfac865]);
  B.disc(.3,.15,0,[0,0,1],.18,.08,B.P[1],3);
  const world = B.finish({ cam:{target:[0,0,0],dist:5,pitch:0,yaw:0}, look:{horizonBands:config},
    splatFields:{fields:[{
      id:'sparks', shape:{at:[.8,.5,0],size:[.2,.2,.15]},
      life:{start:0,end:1,rate:8,lifetime:[2,2]}, motion:{velocity:[.05,.12,0]},
      style:{color:0xf6a737,size:.085,emissive:true}
    }]}
  });
  for (const ortho of [false,true]) {
    const frames = [];
    for (const yaw of [-.7,0,.5]) {
      const opts = { w:55,h:35,raw:true,px:1,yaw,ortho,t:.75,passes:['depth','splatId','emission'],
        captureMotion:true };
      const plain = ink.render(world,{ ...opts,horizonBands:false });
      const painted = ink.render(world,{ ...opts,horizonBands:true });
      assert.notDeepEqual(plain.rgb, painted.rgb);
      assert.deepEqual(plain.passes, painted.passes);
      assert.deepEqual(plain.motionReference, painted.motionReference);
      assert(plain.motionReference.centers.length>2);
      assert(plain.passes.emission.some(value=>value>0));
      const transparent = ink.render(world,{ ...opts,transparent:true });
      assert.deepEqual(transparent.rgb,ink.render(world,{ ...opts,transparent:true,horizonBands:false }).rgb);
      frames.push(painted.motionReference.centers[0]);
    }
    assert.equal(new Set(frames).size, 3);
  }
});

test('sky sequence drives band opacity and tint and can be disabled independently', () => {
  const B = makeBuilder(1,[0x000000]);
  const layer = { ...band, gain:'vistaGain', tint:'vistaTint',
    image:{width:1,height:1,pixels:[255,255,255,255]} };
  const skyEnvironment = {
    sky:false,
    profiles:{ dawn:{vistaGain:1,vistaTint:'#ffc386'}, night:{vistaGain:.35,vistaTint:'#4563ae'} },
    sequences:{ crossing:{duration:3,loop:false,keys:[{at:0,profile:'dawn',ease:'linear'},{at:2,profile:'night'}]} },
    tracks:[{id:'clock',sequence:'crossing'}]
  };
  const world = B.finish({cam:{target:[0,0,0],dist:5,pitch:0,yaw:0},
    look:{horizonBands:{ ...config, bands:[layer] }}, skyEnvironment});
  const opts = {w:9,h:9,px:1,raw:true};
  const sample = view => [...ink.render(world,{ ...opts,...view }).rgb.subarray(120,123)];
  const a = sample({t:0}), b = sample({t:1}), c = sample({t:2});
  assert.deepEqual(a,[255,195,134]);
  assert(a[0]>b[0] && b[0]>c[0]);
  assert.deepEqual(sample({t:1,skyProfiles:{clock:'night'}}),c);
  assert.deepEqual(sample({t:1,skyEnvironment:false}),[255,255,255]);
});

test('PNG profile resolves relative to its file and works through the CLI', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-horizon-'));
  t.after(() => fs.rmSync(dir,{recursive:true,force:true}));
  PNG.write(path.join(dir,'ridge.png'),1,1,Uint8Array.of(255,0,0));
  const profile = path.join(dir,'profile.json');
  fs.writeFileSync(profile,JSON.stringify({ ...config, bands:[{...band,image:'ridge.png'}] }));
  assert.deepEqual(at(ink.readHorizonBands(profile).frame(view),10),red);
  const scene=path.join(dir,'scenic.js'), baseline=path.join(dir,'base.png'), rendered=path.join(dir,'painted.png');
  fs.writeFileSync(scene,`module.exports=({makeBuilder})=>({
    id:'scenic', name:'Scenic', build:()=>makeBuilder(1,[0x101a2e]).finish({cam:{target:[0,0,0],dist:5,yaw:0,pitch:0}})
  });`);
  const cli=path.resolve(__dirname,'../cli/ink-studio.js');
  const { execFileSync }=require('node:child_process');
  for (const [setting,output] of [['off',baseline],[profile,rendered]])
    execFileSync(process.execPath,[cli,'render',scene,'--w','11','--h','9','--px','1','--raw','--horizon-bands',setting,'--out',output],{cwd:dir});
  assert.notDeepEqual(PNG.read(rendered).rgb,PNG.read(baseline).rgb);
  assert.deepEqual([...PNG.read(rendered).rgb.subarray(0,3)],[255,0,0]);
});

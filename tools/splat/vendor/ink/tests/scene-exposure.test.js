const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('..');
const { KIT: K, makeBuilder, makeSculpt, SceneExposure } = ink.load();
const { traceMedia } = require('../cli/scene-optics.js');
const { frame } = require('../cli/precipitation.js');

const zone = { min:[0,-4,-4], max:[6,4,4], fade:2, rain:0, fog:0, light:.2, wind:.1 };
const exposure = K.weather.exposure({ zones:[zone] });
const close = (value, expected) => assert(Math.abs(value - expected) < 1e-10, value + ' vs ' + expected);
const open = { rain:1, fog:1, light:1, wind:1 };

test('the shelter boundary stops rain and transitions other channels as a function of depth', () => {
  assert.deepEqual(exposure.sample(-.01,0,0), open);
  assert.deepEqual(exposure.sample(0,0,0), { ...open, rain:0 });
  assert.deepEqual(exposure.sample(1,0,0), { rain:0, fog:.5, light:.6, wind:.55 });
  close(exposure.wind(3,0,0), .1);
  assert.deepEqual(exposure.sample(1,4.01,0), open);
  assert(exposure.rainBlocked([-1,0,0],[7,0,0]), 'rain cannot tunnel through or emerge behind a dry zone');
  assert(!exposure.rainBlocked([-1,4.1,0],[7,4.1,0]));
  assert(!exposure.rainBlocked([-.8,0,0],[-.01,0,0]));
  const overlap = K.weather.exposure({ zones:[zone,{ ...zone, min:[2,-4,-4], max:[8,4,4], fade:0, light:.5 }] });
  close(overlap.light(3,0,0), .2);
  close(overlap.light(5,0,0), .5);
  assert.equal(SceneExposure.settings(exposure,true), exposure);
  assert.equal(SceneExposure.settings(exposure,false), null);
  for (const patch of [{ min:[9,-4,-4] }, { wind:-.2 }, { fog:2 }, { fade:-1 }])
    assert.throws(() => K.weather.exposure({ zones:[{...zone,...patch}] }), /Exposure/);
});

test('fog and aerial perspective integrate the sheltered distance and preserve exterior air', () => {
  const from = [-2,0,0], dir = [1,0,0], stop = 10;
  // Two open units on each side and one equivalent unit through each fade.
  close(exposure.fogDistance(from,dir,0,stop), 6);
  close(exposure.fogDistance([3,0,0],dir,0,1), 0);
  const thin = K.weather.exposure({ zones:[{...zone,min:[1,-4,-4],max:[1.02,4,4],fade:0}] });
  close(thin.fogDistance(from,dir,0,stop),9.98);
  const mist = K.atmosphere.prepare([K.atmosphere.box({
    min:[-4,-4,-4], max:[10,4,4], density:.4, color:'#898fb2'
  })]);
  const sampled = K.atmosphere.trace(mist,from,dir,stop,undefined,{ exposure });
  close(sampled[3], Math.exp(-.4*6));
  const aerial = { density:.35, contrast:.2, start:0, color:[.3,.4,.5] };
  const result = traceMedia([],[],from,dir,stop,new Float64Array(6),[0,0,0,1],{ exposure },aerial);
  close(result[3], .2+.8*Math.exp(-.35*6));
  const indoors = traceMedia([],[],[3,0,0],dir,1,new Float64Array(6),[0,0,0,1],{ exposure },aerial);
  close(indoors[3],1);
});

test('wind samples, travel and volume advection agree at the same point, while clouds stay in open air', () => {
  const wind = K.procedural.airflow.field({ velocity:[4,2] },{ exposure });
  const offset = wind.frame(2).windOffset;
  for (const x of [-.1,0,.77,1,3,5.7,6.1]) {
    const expected = exposure.wind(x,0,0);
    const velocity = wind.sample(x,0,0,2), travel = wind.travel(x,0,0,0,2);
    close(velocity[0], 4 * expected);
    close(velocity[1], 2 * expected);
    close(travel[0], 8 * expected);
    close(offset(x,0,0)[0], travel[0]);
  }
  assert.deepEqual(wind.cloudTravel(0,2),[8,4]);
});

test('world precipitation and impact history both respect the rain boundary', () => {
  const B = makeBuilder(1,[0x203141,0xccddff]);
  const first = B.count();
  for (const x of [-1,1,3])
    B.stick(x,5,0,[0,-1,0],.10,.026,B.P[1],1,{k:2,ph:0,sp:2,rg:6,nd:true});
  B.describePrecipitation(first,B.count(),false);
  const world = B.finish({ precipitation:{ occlusion:false } });
  const receiver = { id:'ground', kind:'paving', min:[-2,-1], max:[4,1], y:0 };
  const options = { time:2, wind:[0,0], lamps:[], localLighting:()=>null,
    impacts:{ receivers:[receiver], lookback:3 }, exposure };
  const covered = frame(world,undefined,options), off = frame(world,undefined,{...options,exposure:null});
  assert(covered.pose(0,-1,5,0,2,0,2,6,0,1));
  assert.equal(covered.pose(1,1,5,0,2,0,2,6,0,1),null);
  assert(off.pose(1,1,5,0,2,0,2,6,0,1));
  assert(covered.contacts.some(event=>event.at[0]===-1));
  assert(covered.contacts.every(event=>event.at[0]<0));
  assert(off.contacts.some(event=>event.at[0]===1));
});

test('covered surfaces lose outdoor light in both camera modes and emissive surfaces keep their own light', () => {
  const B = makeBuilder(21,[0x142033,0x82877f,0xe78e4d,0xffd175]);
  const S = K.sculpt(makeSculpt(B));
  S.captureAlbedo = true;
  for (const x of [-1,1,3])
    S.box([x,.06,0],[.65,.06,.64],{ r:[1], materialId:'stone' },{res:.11});
  S.ball([3,.52,.02],.16,{r:[3],em:true,materialId:'lamp'},{res:.05});
  S.bake();
  const world = B.finish({ sceneExposure:exposure, cam:{target:[1,.2,0],dist:8,pitch:.56,yaw:0,sway:0},
    liveSun:{ direction:[0,1,0],ambient:.2,intensity:.75,shadows:false } });
  for (const ortho of [true,false]) for (const liveSun of [true,false]) {
    const view={ ortho, liveSun, w:132,h:85,px:1,raw:true,passes:['materialId','coverage','position'] };
    const on = ink.render(world,view), off = ink.render(world,{ ...view, sceneExposure:false });
    const { materialId, materials, position, coverage } = on.passes;
    const totals=[0,0,0], counts=[0,0,0];
    let lamp = 0;
    for (let p=0;p<coverage.length;p++) {
      if (coverage[p]<.985) continue;
      const i=p*3, material=materials[materialId[p]], x=position[i];
      const d = off.rgb[i] - on.rgb[i];
      if (material==='lamp' && Math.abs(d)<=1) lamp++;
      if (material!=='stone') continue;
      const index = Math.round((x+1)/2);
      totals[index] += d;
      counts[index]++;
    }
    const change=totals.map((n,i)=>n/counts[i]);
    assert(counts.every(n=>n>10) && lamp>8);
    assert(Math.abs(change[0]) < 1 && change[1] > 15 && change[2] > change[1]+10, change.join(', '));
  }
});

test('shelter attenuates sunlight in lit fog while preserving local lights and density', () => {
  const field = { bounds:{min:[2,-1,-1],max:[4,1,1]}, sample:()=>1 };
  const volumes = K.atmosphere.prepare([K.atmosphere.field({ field, density:.5, step:.15, anisotropy:0 })]);
  const shelter = K.weather.exposure({ zones:[{ ...zone, light:0, fog:1 }] });
  const point = { at:[3,0,.6], color:'#ffc376', radius:3, intensity:3 };
  const outside = K.atmosphere.lighting({ ambient:.1, sun:{ direction:[0,1,0], intensity:2 }, point });
  const inside = K.atmosphere.lighting({ ambient:.1, point });
  const trace = (media, exposure) => K.atmosphere.trace(volumes,[1,0,0],[1,0,0],4,undefined,{ media, exposure });
  const lit = trace(outside), shaded = trace(outside,shelter), local = trace(inside);
  assert.deepEqual(shaded,local);
  assert(lit[0] > shaded[0] + .05);
  assert.equal(lit[3],shaded[3]);
});

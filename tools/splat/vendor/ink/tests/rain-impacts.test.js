const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('../index.js');
const { KIT: K, makeBuilder, makeSculpt } = ink.load();
const Precipitation = require('../cli/precipitation.js');
const Rain = require('../cli/rain-impacts.js');

const pal = [0x152438, 0x6d6152, 0x98c3cc, 0xffdcc6];
const receivers = [
  { id:'pool', kind:'water', y:.27, min:[.3,-1.2], max:[2.6,1.4] },
  { id:'court', kind:'paving', y:.24, min:[-2.6,-1.6], max:[.25,1.8] },
  { id:'awning', kind:'roof', y:2.1, min:[-1.8,-.8], max:[-.79,.68],
    drains:[{ from:[-1.2,.24,.85], to:[-1.1,.24,1.55], width:.17, delay:.05, travel:.1 }] }
];
const config = Rain.settings({ receivers, ripple:{ lifetime:.55 },
  paving:{ lifetime:.39 }, runoff:{ strength:1, lifetime:1.3 } });
const motion = { k:2, nd:true, ph:0, sp:3, rg:3 };
const camera = { target:[0,.45,0], dist:7, yaw:0, pitch:.56, sway:0 };
function drop(B, x, z, profile = false) {
  const first = B.count();
  B.stick(x,3,z,[0,-1,0],.13,.022,B.P[2],1,motion);
  B.describePrecipitation(first, B.count(), profile);
}
function sample(world, time, options = {}) {
  return Precipitation.frame(world, options.precipitation, { time, wind:[0,0], lamps:[],
    localLighting:() => undefined, impacts:config, ...options }).contacts;
}

test('flight deposits at the first receiver, using the same wind and roof cover as the drops', () => {
  const B = makeBuilder(5, pal);
  drop(B,1.1,0);
  drop(B,-.2,0);
  drop(B,-1.15,0);
  const world = B.finish({ cam:camera });
  const contacts = sample(world, 1);
  const current = contacts.filter(event => event.time > 0);
  assert.deepEqual(current.map(event => event.receiver.id), ['pool','court','awning']);
  assert(Math.abs(current[0].at[0] - 1.1) < 1e-6);
  assert.deepEqual(current[0].at.slice(1), [.27,0]);
  assert(Math.abs(current[2].time - .3) < 1e-8);
  const drifting = sample(world, 1, { wind:[1,0] });
  assert(Math.abs(drifting.find(event => event.time > 0 && event.receiver.id === 'pool').at[0] - 2.01) < 1e-5);
  const roof = K.atmosphere.occluder((x,y,z) => Math.max(Math.abs(x-1.1)-.4, Math.abs(y-1.5)-.08, Math.abs(z)-.4),
    { bias:.005, step:.01, steps:48 });
  assert(!sample({ ...world, precipitation:{ occluder:roof } }, 1).some(event => event.receiver.id === 'pool'));
  assert(sample({ ...world, precipitation:{ occluder:roof } }, 1, { precipitation:{ occlusion:false } })
    .some(event => event.receiver.id === 'pool'));
});

test('ripples spread, splashes fade and runoff reaches its path after the rain stops', () => {
  const B = makeBuilder(5, pal);
  drop(B,1.1,0,true);
  drop(B,-.2,0,true);
  drop(B,-1.15,0,true);
  const world = B.finish({ cam:camera });
  const weather = { rainGain:0, rainAt: t => t >= 0 && t <= .97 ? 1 : 0 };
  const impacts = time => Rain.frame(config, sample(world,time,{ weather }),time);
  const current = impacts(1.01);
  const x = 1.1 + .1 * config.ripple.speed + .04;
  assert(Math.abs(current.normal('pool',[x,.27,0],0)[0]) > .03);
  assert(current.mask('court','splash',[-.189,.24,0]) > .5);
  assert(current.mask('awning','runoff',[-1.1,.24,1.55]) > .2);
  assert.equal(current.mask('awning','runoff',[-.6,.24,1.55]), 0);
  assert.equal(impacts(1.42).mask('court','splash',[-.2,.24,0]), 0);
  assert(impacts(1.42).mask('awning','runoff',[-1.1,.24,1.55]) > 0);
  assert.equal(impacts(3), null);
});

test('the CPU render applies pool, paving and runoff marks to opted-in materials', () => {
  const B = makeBuilder(8, pal), S = K.sculpt(makeSculpt(B));
  const mask = (receiver, channel) => ({ type:'rainImpact', receiver, channel });
  const coat = (color, mask) => ({ type:'directionalColor', color, crossColor:color, mask });
  const water = K.surface.material({ r:[2], materialId:'pool' }, { rainRipple:'pool', layers:{
    shine:{ type:'reflection', strength:1, f0:1, sky:'#ffda99', horizon:'#5d7395', ground:'#233442' }
  } });
  const paving = K.surface.material({ r:[1], materialId:'paving' }, { layers:{
    splash:coat('#ffffff', mask('court','splash')), wet:coat('#16313f', mask('awning','runoff'))
  } });
  S.box([1.45,.21,.10],[1.15,.06,1.3],water,{res:.11});
  S.box([-1.18,.18,.12],[1.42,.06,1.62],paving,{res:.105});
  S.bake();
  drop(B,1.1,0);
  drop(B,-.2,0);
  drop(B,-1.15,0);
  const world = B.finish({ cam:camera, rainImpacts:{ receivers, runoff:{strength:2} } });
  for (const ortho of [false,true]) {
    const options = { w:122, h:86, px:1, raw:true, t:1.01, ortho, passes:['materialId'] };
    const on = ink.render(world,options);
    const off = ink.render(world,{ ...options, rainImpacts:false });
    const { materialId, materials } = on.passes;
    const counts = { pool:0, paving:0 };
    for (let i=0;i<materialId.length;i++) {
      const id = materials[materialId[i]], j=i*3;
      if (id in counts && Math.abs(on.rgb[j] - off.rgb[j]) > 15) counts[id]++;
    }
    assert(counts.pool > 5);
    assert(counts.paving > 8);
    ink.render(world,{ ...options, t:.15 });
    assert.deepEqual(ink.render(world,options).rgb,on.rgb);
    assert.deepEqual(ink.render(world,{ ...options, precipitation:false }).rgb,
      ink.render(world,{ ...options, precipitation:false, rainImpacts:false }).rgb);
  }
});

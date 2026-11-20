const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('../index.js');
const { KIT: K, makeBuilder, makeSculpt } = ink.load();
const precipitation = require('../cli/precipitation.js');

const camera = { target:[0,1,0], dist:7, yaw:0, pitch:0, sway:0 };
const view = { w:103, h:75, px:1, raw:true, captureMotion:true };
const setup = () => makeBuilder(5, [0x081023,0x667a93,0xccccbf,0xffffff]);
function drop(B, { x=0, z=0, kind=2, phase=.25, profile=false, speed=2, height=4 } = {}) {
  const row = B.count();
  const motion = { k:kind, ph:phase, sp:speed, rg:height, ex:0, nd:true };
  if (kind === 2) B.stick(x,3,z,[0,-1,0],.16,.033,B.P[1],1,motion);
  else B.disc(x,3,z,[0,0,1],.09,.09,B.P[1],1,motion);
  B.describePrecipitation(row, B.count(), profile);
  return row;
}

test('the same profile history advects falling rain and snow through changing wind', () => {
  const B = setup();
  drop(B, { phase:.5, profile:true });
  drop(B, { phase:.5, kind:15, profile:true });
  const world = B.finish({ cam:camera });
  const profile = K.skyEnvironment.compile({ sky:false,
    profiles:{ calm:{ windX:0, rain:.5, snowfall:.25 }, gust:{ windX:2, rain:.5, snowfall:.25 } },
    sequences:{ wind:{ duration:3, loop:false, keys:[
      { at:0, profile:'calm', ease:'linear' }, { at:2, profile:'gust' }
    ] } }, tracks:[{ id:'wind', sequence:'wind' }] });
  const signals = K.weather.bind(profile, { rainFull:.5, snowFull:.5 });
  const weather = signals.frame(2);
  const options = { time:2, wind:weather.wind, windAt:weather.windAt, weather, lamps:[], localLighting:() => undefined };
  const falling = precipitation.frame(world, undefined, options);
  const rain = falling.pose(0,0,3,0,2,.5,2,4,0,1);
  const snow = falling.pose(1,0,3,0,15,.5,2,4,0,1);
  // During the last second the wind rose linearly from 1 to 2 units per second.
  assert(Math.abs(rain[0] - 1.5) < 1e-10);
  assert.deepEqual(rain.slice(1), [1,0,.75]);
  assert.deepEqual(snow, [rain[0],1,0,.5]);
  const calm = precipitation.frame(world, undefined, { ...options, wind:[0,0], windAt:undefined });
  assert.equal(calm.pose(0,0,3,0,2,.5,2,4,0,1)[0], 0);
  assert.equal(precipitation.frame(world, undefined, { ...options, weather:undefined }).pose(0,0,3,0,2,.5,2,4,0,1), null);
});

test('angled paths stop on real roof geometry and uncovered rain survives', () => {
  const B = setup(), S = K.sculpt(makeSculpt(B));
  S.box([0,1.85,0],[.72,.085,.48],{ r:[2] },{res:.075});
  const occluder = K.atmosphere.occluder(S.modelSource().field.sdf,{ bias:.005, step:.01, steps:48 });
  S.bake();
  // The first particle crosses the roof while drifting and ends beyond its footprint.
  const blocked = drop(B, { x:-.57, phase:.22 });
  const outside = drop(B, { x:1.45, phase:.22, kind:15 });
  const above = drop(B, { x:-.57, phase:0 });
  const world = B.finish({ cam:camera, precipitation:{ occluder }, anim:{ wind:[1.4,0] } });
  for (const ortho of [false,true]) {
    const options = { ...view, ortho, t:.52 };
    const clipped = ink.render(world, options);
    const unblocked = ink.render(world, { ...options, precipitation:{ occlusion:false } });
    const off = ink.render(world, { ...options, precipitation:false });
    assert(Number.isNaN(clipped.motionReference.centers[blocked * 2]));
    assert(Number.isFinite(unblocked.motionReference.centers[blocked * 2]));
    assert(Number.isFinite(clipped.motionReference.centers[outside * 2]));
    assert(Number.isFinite(clipped.motionReference.centers[above * 2]));
    assert(Number.isNaN(off.motionReference.centers[outside * 2]));
    assert.notDeepEqual(clipped.rgb, off.rgb);
  }
});

test('lanterns illuminate particles and opaque geometry hides farther ones', () => {
  const B = setup(), S = K.sculpt(makeSculpt(B));
  S.box([-.68,1,1.2],[.25,.6,.19],{ r:[2] },{res:.07});
  S.bake();
  const behind = drop(B,{ x:-.68, z:0, phase:.5 });
  const front = drop(B,{ x:.62, z:1, phase:.5, kind:15 });
  const world = B.finish({ cam:camera,
    lights:[{ p:[.63,1.09,1.15], radius:.67, color:[1,.35,.13], intensity:1.9 }],
    volumeLighting:{ points:[{ at:[.62,1,1.2], color:'#ffae48', intensity:.6, radius:1 }] }
  });
  const options = { ...view, t:0, ortho:true };
  const lit = ink.render(world, options);
  const off = ink.render(world, { ...options, precipitation:false });
  const unlit = ink.render(world, { ...options, precipitation:{ lightStrength:0 } });
  const pixel = index => {
    const [x,y] = lit.motionReference.centers.slice(index*2,index*2+2);
    return (Math.floor(y)*lit.w + Math.floor(x))*3;
  };
  assert.deepEqual(lit.rgb.slice(pixel(behind),pixel(behind)+3),off.rgb.slice(pixel(behind),pixel(behind)+3));
  assert(lit.rgb[pixel(front)] > unlit.rgb[pixel(front)] + 39);
  assert(lit.rgb[pixel(front)] > lit.rgb[pixel(front)+2]);
  assert.notDeepEqual(unlit.rgb, off.rgb);
});

test('weather fall tags only opt-in rain and snow ranges', () => {
  const B = setup();
  const rain = K.weather.fall(B,{ kind:'rain', worldSpace:true, box:[-1,1,-1,1], n:6 });
  K.weather.fall(B,{ kind:'leaf', worldSpace:true, n:5 });
  const snow = K.weather.fall(B,{ kind:'snow', worldSpace:true, profile:true, n:4 });
  K.weather.fall(B,{ kind:'rain', n:2 });
  const world = B.finish({ cam:camera });
  assert.deepEqual(world.precipitationRanges, [
    { first:0, end:rain, profile:false }, { first:rain+5, end:rain+5+snow, profile:true }
  ]);
  B.take();
  assert.equal(B.finish({ cam:camera }).precipitationRanges, undefined);
});

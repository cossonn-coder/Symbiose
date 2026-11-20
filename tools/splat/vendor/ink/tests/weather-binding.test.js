const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('../index.js');
const { KIT: K, makeBuilder, makeSculpt } = ink.load();

const clear = { rain:0, humidity:.28, windX:0, windZ:0, airTemperature:11, fogDensity:0 };
const storm = { rain:.55, humidity:.96, windX:2.4, windZ:-.5, airTemperature:7, fogDensity:2 };
const environment = K.skyEnvironment.compile({
  sky:false, profiles:{ clear, storm }, sequences:{ passing:{ duration:10, loop:false, keys:[
    { at:0, profile:'clear', ease:'hold' }, { at:1, profile:'storm', ease:'hold' }, { at:3, profile:'clear' }
  ] } }, tracks:[{ id:'weather', sequence:'passing' }]
});

const surface = { width:4, height:4, cell:1, origin:[-2,-2], step:.125, evaporation:.48, maxRunoff:0 };

test('a shared profile feeds retained wetness, rain, fog and wind, including after a seek', () => {
  const covered = { ...surface, forcing:x => ({ precipitationExposure:x < 0 ? 1 : 0 }) };
  const binding = K.weather.bind(environment, { rainFull:.6, fogVolumes:['mist'], surface:covered });
  const dry = binding.frame(0);
  const wet = binding.frame(2.5);
  const after = binding.frame(4);
  const later = binding.frame(8);
  assert.equal(dry.surface(-1,0).wetness, 0);
  assert.equal(dry.rainGain, 0);
  assert(wet.rainGain > .90);
  assert.deepEqual(wet.wind, [2.4,-.5]);
  assert.equal(wet.humidity, .96);
  assert.equal(wet.fogGain({ id:'mist' }), 2);
  assert.equal(wet.fogGain({ id:'steam' }), 1);
  assert(wet.surface(-1,0).wetness > .75);
  assert(wet.surface(1,0).wetness < .04);
  assert.equal(after.rainGain, 0);
  assert.equal(after.fogGain({ id:'mist' }), 0);
  assert(after.surface(-1,0).wetness > .76);
  assert(later.surface(-1,0).wetness < after.surface(-1,0).wetness * .65);
  assert.deepEqual(binding.frame(2.5).surface(-1,0), wet.surface(-1,0));
  assert.deepEqual(K.weather.bind(environment, { surface:covered }).frame(4).surface(-1,0), after.surface(-1,0));
  assert.equal(binding.frame(0).surface(99,99), null);

  const solver = K.procedural.motion.surfaceWeather(surface);
  const input = binding.forcing();
  assert.equal(input(0,0,2,{}).wind, Math.hypot(2.4,-.5) / 5);
  assert(solver.step(2.5,{ forcing:input }).sample(0,0).wetness > .7);
});

test('channel aliases, track pins, and direct wetness can be authored independently', () => {
  const changed = K.skyEnvironment.compile({ defaults:{ showers:.66, xWind:-2, cold:-9,
    snow:.6, damp:.35 }, sky:false });
  const binding = K.weather.bind(changed, {
    channels:{ rain:'showers', windX:'xWind', air:'cold', snowfall:'snow', wetness:'damp' },
    surface:{ ...surface, initial:() => ({ temperature:-7 }) }
  });
  assert.deepEqual(binding.sample(1).wind, [-2,0]);
  const snowy = binding.frame(2).surface(0,0);
  assert(snowy.snow > 1 && snowy.frost > .5);
  assert(snowy.wetness >= .35);
  const pinned = K.weather.bind(environment, true, { profiles:{ weather:'storm' } });
  assert.equal(pinned.frame(0).rain, .55);
  assert.throws(() => K.weather.bind(changed, { channels:{ rain:'typo' } }), /Missing weather channel/);
  assert.throws(() => K.weather.bind({ defaults:{ humidity:2 } }), /Weather humidity/);
});

test('rendered wind, rain, local fog and wet finishes follow the scene binding', () => {
  const B = makeBuilder(12, [0x162131, 0xc1a37a, 0x91c0e7, 0x647662]);
  const S = K.sculpt(makeSculpt(B));
  const stone = K.surface.material({ r:[1] }, { layers:{
    wet:{ type:'directionalColor', color:'#2d414b', crossColor:'#2d414b',
      mask:{ type:'weather', high:.75 } }
  } });
  S.box([-1,0,0],[1,.09,1],stone,{res:.14});
  S.bake();
  const flap = B.count();
  B.disc(0,1,0,[0,0,1],.24,.018,B.P[3],3,K.procedural.airflow.pinned({ reach:.7 })(1));
  const first = B.count();
  K.weather.fall(B,{ kind:'rain', profile:true, box:[-1.5,1.5,-.75,1.5], top:2.5, n:40, cols:[2], len:.12 });
  const world = B.finish({ cam:{ target:[-.15,.48,0], dist:5.8, pitch:.47, yaw:0, sway:0 }, radius:5, detail:18,
    skyEnvironment:environment, weatherBinding:{ surface },
    atmosphere:[K.atmosphere.fog({ bottom:.2, top:2.8, density:.14, far:8, color:'#668f9c' })] });
  const view = { w:84, h:66, px:1, raw:true, t:.48, captureMotion:true, captureFog:true };
  const clear = ink.render(world,{ ...view, skyTime:0 });
  const rainy = ink.render(world,{ ...view, skyTime:2.5 });
  const post = ink.render(world,{ ...view, skyTime:4 });
  const off = ink.render(world,{ ...view, skyTime:2.5, weatherBinding:false });
  assert(Number.isNaN(clear.motionReference.centers[first * 2]));
  assert(Number.isFinite(rainy.motionReference.centers[first * 2]));
  assert(Number.isNaN(post.motionReference.centers[first * 2]));
  assert(Number.isNaN(off.motionReference.centers[first * 2]));
  assert(rainy.motionReference.centers[flap * 2] > clear.motionReference.centers[flap * 2] + 1);
  assert.equal(off.motionReference.centers[flap * 2], clear.motionReference.centers[flap * 2]);
  assert(rainy.fog.some(alpha => alpha > .5));
  assert.equal(clear.fog, undefined);
  assert.equal(post.fog, undefined);
  const retained = post.rgb.filter((red, i) => i%3 === 0 && red < clear.rgb[i] - 20);
  assert(retained.length > 50, 'paving remains wet once the storm ends');
  assert.deepEqual(rainy.rgb, ink.render(world,{ ...view, skyTime:2.5 }).rgb);
  const sunny = ink.render(world,{ ...view, skyTime:2.5, skyProfiles:{ weather:'clear' } });
  assert.deepEqual(sunny.rgb, clear.rgb);
});

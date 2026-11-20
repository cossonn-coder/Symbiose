const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('..');
const { KIT: K, makeBuilder } = ink.load();
const SceneOptics = require('../src/scene-optics.js');
const Precipitation = require('../cli/precipitation.js');
const RainImpacts = require('../cli/rain-impacts.js');

const environment = K.skyEnvironment.compile({
  sky:false, defaults:{ rain:0, snowfall:0, windX:0, windZ:0, fogDensity:0, humidity:.35, airTemperature:11 },
  profiles:{ squall:{ rain:.85, snowfall:.22, windX:.7, humidity:.96, airTemperature:5, fogDensity:2 },
    break:{ rain:0 } }
});
const front = { id:'crossing', profile:'squall', radius:[2.6,2.8], feather:.5,
  route:[{ at:0, xz:[-4,0] }, { at:8, xz:[4,0] }] };
const config = { fronts:[front], surface:{
  width:24, height:8, cell:.5, origin:[-6,-2], step:.125, maxRunoff:0, wetDiffusion:0
} };

test('a timed weather front blends locally, leaving wet ground behind on its route', () => {
  const binding = K.weather.bind(environment,config);
  assert.equal(binding.sample(1).rain,0);
  assert.equal(binding.sample(0,-4,0).rain,.85);
  assert.equal(binding.sample(0,4,0).rain,0);
  assert(Math.abs(binding.sample(0,-4+2.6*.75,0).rain-.425) < 1e-10);
  const sample = binding.sample(8,4,0);
  assert.equal(sample.rain,.85);
  assert.equal(sample.humidity,.96);
  assert.deepEqual(sample.wind,[.7,0]);
  assert.equal(sample.air,5);
  assert.equal(binding.sample(8,-4,0).rain,0);
  const later = binding.frame(8);
  assert.equal(later.rainHere(-4,0),0);
  assert(later.surface(-4,0).wetness > .15);
  assert(later.surface(4,0).wetness > .45);
  binding.frame(1);
  assert.deepEqual(binding.frame(8).surface(-4,0),later.surface(-4,0));

  const windows = K.weather.bind(environment, { fronts:[front,
    { ...front, id:'gap', profile:'break', radius:1 }] });
  assert.equal(windows.sample(2,-2,0).rain,0);
  assert.equal(windows.sample(2,-2,0).humidity,.96);
  assert.throws(() => K.weather.bind(environment,{ fronts:[{ ...front, profile:'bad' }] }), /Unknown sky profile/);
  assert.throws(() => K.weather.bind(environment,{ fronts:[{ ...front, loop:true }] }), /matching endpoints/);
});

test('local fog and old rain impacts use spatial weather at their own locations and times', () => {
  const binding = K.weather.bind(environment,{ fronts:[front], fogVolumes:['fog'] });
  const fog = [K.atmosphere.fog({ id:'fog', density:.6, top:2, bottom:-.5, far:6 })];
  function transmission(at, x) {
    const weather = binding.frame(at);
    return SceneOptics.trace(SceneOptics.prepareVolumes(fog,[],null, weather.fogGain), [x,1,3], [0,0,-1],6)[3];
  }
  assert(transmission(0,-4) < .08);
  assert.equal(transmission(0,4),1);
  assert(transmission(8,4) < .08);
  assert.equal(transmission(8,-4),1);

  const B = makeBuilder(1,[0x0d2548,0xe2e9ef]);
  for (const x of [-4,4]) {
    const start = B.count();
    B.stick(x,3,0,[0,-1,0],.11,.021,B.P[1],1,{ k:2, ph:0, sp:3, rg:3, nd:true });
    B.describePrecipitation(start,B.count(),true);
  }
  const impacts = RainImpacts.settings({ receivers:[
    { id:'left', kind:'paving', y:.1, min:[-5,-1], max:[-3,1] },
    { id:'right', kind:'paving', y:.1, min:[3,-1], max:[5,1] }
  ] });
  const world = B.finish();
  const weather = binding.frame(1.1);
  const frame = Precipitation.frame(world,undefined,{ time:1.1, wind:weather.wind,
    localWind:weather.windHere, windAt:weather.windAt, weather, lamps:[], localLighting:() => undefined, impacts });
  assert(frame.contacts.length > 0);
  assert(frame.contacts.every(event => event.receiver.id === 'left' && event.at[0] > -4));
});

test('the CLI renderer moves rain and fog between the headland and valley and can toggle the front', () => {
  const B = makeBuilder(8,[0x172539,0xb4daec]);
  const first = B.count();
  K.weather.fall(B,{ kind:'rain', worldSpace:true, profile:true, n:40, box:[-4.5,-3.5,-.3,.3], top:2.5,cols:[1] });
  const second = B.count();
  K.weather.fall(B,{ kind:'rain', worldSpace:true, profile:true, n:40, box:[3.5,4.5,-.3,.3], top:2.5,cols:[1] });
  const world = B.finish({ cam:{ target:[0,1,0], dist:11, yaw:0, pitch:.06, sway:0 }, radius:14,
    weatherBinding:{ fronts:[front] }, skyEnvironment:environment,
    atmosphere:[K.atmosphere.fog({ id:'fog', bottom:0, top:3, density:.65, near:9, far:14 })] });
  const view = { w:156, h:88, px:1, raw:true, captureFog:true, captureMotion:true };
  const early = ink.render(world,{ ...view, skyTime:0 }), late = ink.render(world,{ ...view, skyTime:8 });
  const turnedOff = ink.render(world,{ ...view, skyTime:8, weatherFronts:false });
  const colors = frame => [...frame.motionReference.centers];
  const left = frame => colors(frame).slice(first*2,second*2).some(Number.isFinite);
  const right = frame => colors(frame).slice(second*2).some(Number.isFinite);
  assert(left(early) && !right(early));
  assert(right(late) && !left(late));
  assert(!left(turnedOff) && !right(turnedOff));
  assert(early.fog[44*156+30] > early.fog[44*156+125]+.5);
  assert(late.fog[44*156+125] > late.fog[44*156+30]+.5);
  assert.equal(turnedOff.fog,undefined);
});

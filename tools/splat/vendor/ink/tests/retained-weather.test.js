const test = require('node:test');
const assert = require('node:assert/strict');
const ink = require('..');
const { KIT: K, makeBuilder, makeSculpt } = ink.load();
const { motion, overheadCover } = K.procedural;

const grid = { width:4, height:2, cell:1, capacity:.25, maxDt:.05, exchange:1.8, maxRunoff:0,
  wetDiffusion:0, heatDiffusion:0 };
const total = ({ wetness, standingWater, snow, frost }) => wetness + standingWater + snow + frost;

test('standing water is optional, fits local basins, and exchanges water with the stone and frost', () => {
  const legacy = motion.surfaceWeather(grid);
  assert(!Object.hasOwn(legacy.step(1).sample(.5,.5), 'standingWater'));
  const solver = motion.surfaceWeather({ ...grid, evaporation:0, freezeRate:.5,
    standingWater:{ capacity:x => x < 2 ? .4 : 0, drainage:0, evaporation:0 } });
  const rain = solver.step(1,{ forcing:() => ({ rain:.58, air:10 }) });
  const basin = rain.sample(.5,.5), stone = rain.sample(3.5,.5);
  assert(basin.standingWater > .32);
  assert.equal(basin.wetness,.25);
  assert.equal(stone.standingWater,0);
  assert.equal(stone.wetness,.25);
  assert(Math.abs(total(basin)-.58) < 1e-10);
  const frozen = solver.step(2,{ forcing:() => ({ air:-10 }) }).sample(.5,.5);
  assert.equal(frozen.standingWater,0);
  assert(frozen.frost > .57);
  const thawed = solver.step(3,{ forcing:() => ({ air:14, light:1 }) }).sample(.5,.5);
  assert.equal(thawed.frost,0);
  assert(Math.abs(thawed.standingWater-basin.standingWater) < 1e-9);
  assert(Math.abs(total(thawed)-total(basin)) < 1e-10);
  const before = solver.snapshot();
  assert.throws(() => solver.step(.5,{ forcing:() => ({ humidity:NaN }) }), /forcing values/);
  assert.deepEqual(solver.snapshot().standingWater,before.standingWater);
  assert.throws(() => motion.surfaceWeather({ ...grid, standingWater:{ capacity:.01 },
    initial:() => ({ standingWater:.02 }) }), /basin capacity/);
});

test('shelter and sunlight change pooled water, snow, and frost independently of air temperature', () => {
  const cover = overheadCover.rasterize({ surfaces:[{ min:[3,0], max:[4,2], heightAt:() => 1.5 }] });
  const solver = motion.surfaceWeather({ ...grid, evaporation:.42, freezeRate:.4,
    standingWater:{ capacity:.45, drainage:.018, evaporation:.72 } });
  const exposed = (x,z) => overheadCover.exposure(cover, [x,0,z]);
  const storm = solver.step(1.5,{ forcing:(x,z) => ({
    rain:.37, humidity:1, light:.08, air:6, precipitationExposure:exposed(x,z)
  }) });
  assert(storm.sample(.5,.5).standingWater > .30);
  assert.equal(storm.sample(3.5,.5).standingWater,0);
  assert.equal(storm.sample(3.5,.5).wetness,0);
  const cold = solver.step(2.0,{ forcing:(x,z) => ({
    air:-8, snowfall:.29, light:0, humidity:.97, precipitationExposure:exposed(x,z)
  }) });
  assert(cold.sample(.5,.5).frost > .24);
  assert(cold.sample(.5,.5).snow > .45);
  assert.equal(cold.sample(3.5,.5).snow,0);
  const thaw = solver.step(2.2,{ forcing:x => ({
    air:-2, light:1, humidity:.63, wind:.5, shelter:x < 1 ? .92 : 0
  }) });
  const shaded = thaw.sample(.5,.5), sunny = thaw.sample(1.5,.5);
  assert(sunny.temperature > 5);
  assert(shaded.temperature < 0);
  assert(sunny.snow < shaded.snow);
  assert(sunny.frost < shaded.frost);
  assert(sunny.standingWater > shaded.standingWater);
  const dry = solver.step(5,{ forcing:() => ({ air:18, light:1, humidity:.18, wind:.8 }) }).sample(1.5,.5);
  assert(dry.wetness < sunny.wetness);
  assert(dry.standingWater < sunny.standingWater);
});

test('the retained-weather render toggle keeps profile rain and independently reveals puddle finishes', () => {
  const B = makeBuilder(6,[0x132337,0xa88762,0xcfe2ef]);
  const S = K.sculpt(makeSculpt(B));
  const stone = K.surface.material({ r:[1] }, { layers:{
    pooled:{ type:'directionalColor', color:'#407dba', crossColor:'#407dba',
      mask:{ type:'weather', channel:'standingWater', low:.02, high:.12 } }
  } });
  S.box([0,.05,0],[1.8,.09,.9],stone,{ res:.12 });
  S.bake();
  const first = B.count();
  K.weather.fall(B,{ kind:'rain', profile:true, n:48, cols:[2], box:[-1.4,1.4,-.5,1.4],top:2 });
  const environment = K.skyEnvironment.compile({
    sky:false, profiles:{ shower:{rain:.47}, clear:{rain:0} },
    sequences:{ weather:{ duration:5, loop:false, keys:[
      { at:0, profile:'shower', ease:'hold' }, { at:1, profile:'clear' }
    ] } }, tracks:[{ id:'weather', sequence:'weather' }]
  });
  const world = B.finish({
    cam:{ target:[0,.36,0], dist:6, yaw:0, pitch:.52, sway:0 }, radius:5,
    skyEnvironment:environment, weatherBinding:{ surface:{ ...grid, width:16, height:8, cell:.25,
      origin:[-2,-1], step:.125, standingWater:{ capacity:x => x > 0 ? .3 : 0 },
      evaporation:.17
    } }
  });
  const view = { w:106, h:77, px:1, raw:true, captureMotion:true };
  const during = { ...view, t:.91 };
  assert(Number.isFinite(ink.render(world,during).motionReference.centers[first*2]));
  const duringOff = ink.render(world,{ ...during, retainedWeather:false });
  assert(Number.isFinite(duringOff.motionReference.centers[first*2]));
  const later = { ...view, t:1.65 };
  const on = ink.render(world,later), off = ink.render(world,{ ...later, retainedWeather:false });
  assert(Number.isNaN(on.motionReference.centers[first*2]));
  let left = 0, right = 0;
  for (let y=0;y<on.h;y++) for (let x=0;x<on.w;x++) {
    const i = (y*on.w+x)*3;
    if (on.rgb[i+2] - off.rgb[i+2] > 40) {
      if (x < on.w / 2 - 5) left++;
      if (x > on.w / 2 + 5) right++;
    }
  }
  assert.equal(left,0);
  assert(right > 100);
  ink.render(world,{ ...view, t:0 });
  assert.deepEqual(ink.render(world,later).rgb,on.rgb);
  const noBasins = ink.render(world,{ ...later, weatherBinding:{ surface:{ standingWater:{ capacity:0 } } } });
  assert.deepEqual(noBasins.rgb,off.rgb);
});

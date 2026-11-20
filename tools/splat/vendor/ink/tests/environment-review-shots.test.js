const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('../index.js');

const kit = ink.load();
const view = {w:88,h:60,px:1,raw:true};
const scene = id => {
  const shot = require('../examples/review-'+id+'.js')(kit);
  return {world:shot.animate(shot.build(shot.seed)),checkpoints:shot.review.checkpoints};
};
const changed = (a,b,threshold) =>
  a.reduce((count,value,i)=>count+(Math.abs(value-b[i])>threshold),0);

test('beacon paving reflects retained wetness while the cast shadow moves',()=>{
  const {world,checkpoints:[start,sheen,end]} = scene('beacon');
  const sample = (t,options) => ink.render(world,{...view,t,passes:['reflections'],...options});
  const shadowAt = t => {
    const lit=sample(t), noShadow=sample(t,{liveSun:{shadows:false}});
    return lit.rgb.map((value,i)=>Number(noShadow.rgb[i]-value>9));
  };
  const early=shadowAt(start), late=shadowAt(end);
  assert(early.some(Boolean) && late.some(Boolean));
  assert(changed(early,late,0)>80);
  const wet=sample(sheen), dry=sample(sheen,{retainedWeather:false});
  assert(changed(wet.passes.reflections,dry.passes.reflections,.03)>200);
});

test('cliff path shows camera parallax and enters and exits the authored fog bank',()=>{
  const {world,checkpoints:[start,inside,exit]} = scene('cliff-path');
  const crossing = world.atmosphere[0];
  const eye = t => {
    world.anim.update(0,t);
    const {target,dist,yaw,pitch} = world.cam;
    const offset = [Math.cos(pitch)*Math.sin(yaw),Math.sin(pitch),Math.cos(pitch)*Math.cos(yaw)];
    return target.map((value,i)=>value+dist*offset[i]);
  };
  assert(eye(start)[2]>crossing.max[2]);
  assert(eye(inside).every((value,i)=>value>crossing.min[i] && value<crossing.max[i]));
  assert(eye(exit)[2]<crossing.min[2]);

  // Freeze the sky clock so this isolates parallax from cloud drift.
  eye(start);
  const camera = {...world.cam};
  const card = target => {
    const settings = {...view,t:start,...camera,target,passes:['sky']};
    const withCloud=ink.render(world,settings).passes.sky;
    const clear=ink.render(world,{...settings,cloudField:false}).passes.sky;
    return withCloud.map((value,i)=>value-clear[i]);
  };
  const original=card(camera.target);
  const moved=card(camera.target.map((value,i)=>value+(i===0 ? 2 : 0)));
  assert(original.some(value=>Math.abs(value)>.08));
  assert(changed(original,moved,.03)>150);

  const fog = t => {
    eye(t);
    return ink.render({...world,atmosphere:[crossing]},{...view,t,passes:['fogTransmittance']}).passes.fogTransmittance;
  };
  assert(fog(inside).some(value=>value<.45));
  assert(fog(exit).every(value=>value===1));
});

test('the market overrides local rain and exports precipitation and planar reflections',()=>{
  const {world,checkpoints:[,t]} = scene('sheltered-market');
  world.anim.update(0,t);
  const covered=ink.inspectEnvironment(world,{t,at:[-2.70,1,-.84]});
  const aisle=ink.inspectEnvironment(world,{t,at:[1.91,1,.88]});
  assert.equal(covered.exposure.gains.rain,0);
  assert.equal(covered.exposure.zones[0].id,'west awning');
  assert.equal(aisle.exposure.gains.rain,1);
  assert(aisle.weather.local.rain>aisle.weather.global.rain);
  const sample = options => ink.render(world,{...view,t,passes:['precipitation','reflections'],...options}).passes;
  const frame=sample(), withoutShelter=sample({sceneExposure:false}), withoutMirror=sample({reflections:false});
  assert(frame.precipitation.some((value,i)=>i%4===3 && value>.1));
  assert(changed(frame.precipitation,withoutShelter.precipitation,.03)>100);
  assert(changed(frame.reflections,withoutMirror.reflections,.03)>100);
});

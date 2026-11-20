const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('..');
const { KIT: K, makeBuilder } = ink.load();
const { traceMedia } = require('../cli/scene-optics.js');

const finish = tint => ({ zenith:tint, horizon:tint, ground:tint, sunStrength:0 });
const profiles = K.skyEnvironment.compile({
  profiles: {
    clear: { ...finish('#ee9c68'), aerialDensity:.10 },
    blue: { ...finish('#598bdf'), aerialDensity:.21 }
  },
  sequences:{ air:{ duration:9, keys:[{at:0,profile:'clear'},{at:4,profile:'blue'}] } },
  tracks:[{id:'air',sequence:'air'}]
});
const settings = { start:6, density:.10, contrast:.25 };
const shot = { w:117, h:69, px:1, raw:true, passes:['objectId','coverage'], captureFog:true };

function scene(ortho, material = '#171c29') {
  const B = makeBuilder(3, [0x283c54, parseInt(material.slice(1),16)]);
  for (const [i, depth] of [3,11,41].entries()) {
    const x = ortho ? (i - 1) * 1.25 : (i - 1) * depth*.22;
    const r = ortho ? .31 : depth*.038;
    B.disc(x, 0, 6 - depth, [0,0,1], r, .012, B.P[1], 3);
    B.describeSplats(i, i+1, {object:['near','middle','far'][i]});
  }
  return B.finish({
    cam:{target:[0,0,0],dist:6,yaw:0,pitch:0},detail:18,radius:4,dither:0,
    skyEnvironment:profiles, aerialPerspective:{start:6,contrast:.25}
  });
}

function position(frame, name) {
  const { coverage, objects, objectId } = frame.passes;
  let best = 0, found = -1;
  for (let i=0;i<objectId.length;i++) if (objects[objectId[i]] === name && coverage[i] > best) {
    found = i;
    best = coverage[i];
  }
  assert(best > .90, name + ' has visible samples');
  return found;
}
const rgb = (frame, i) => [...frame.rgb.subarray(i*3,i*3+3)];
const close = (a,b,tolerance = 1e-6) => assert(Math.abs(a-b) < tolerance, a + ' vs ' + b);

test('aerial perspective starts at a scene distance and follows sky while retaining far contrast', () => {
  for (const ortho of [false,true]) {
    const world = scene(ortho), options = { ...shot, ortho };
    const warm = ink.render(world, options);
    const base = ink.render(world,{ ...options, aerialPerspective:false });
    const blue = ink.render(world,{ ...options, skyProfiles:{air:'blue'} });
    const [near,middle,far] = ['near','middle','far'].map(name=>position(warm,name));
    assert.deepEqual(rgb(warm,near),rgb(base,near));
    assert.deepEqual(rgb(warm,0),rgb(base,0));
    assert.equal(warm.fog[0],0);
    assert.equal(warm.fog[near],0);
    assert(warm.fog[middle] > .23 && warm.fog[middle] < .38);
    assert(warm.fog[far] > .69 && warm.fog[far] < .75);
    assert(rgb(warm,middle)[0] > rgb(base,middle)[0] + 45);
    assert(rgb(warm,far)[0] > rgb(warm,middle)[0] + 55);
    assert(rgb(blue,far)[2] > rgb(warm,far)[2] + 75);
    assert(blue.fog[middle] > warm.fog[middle] + .15);
    const clear = ink.render(world,{ ...options, aerialPerspective:{ start:45 } });
    assert.deepEqual(rgb(clear,far),rgb(base,far));
    const none = ink.render(world,{ ...options, aerialPerspective:{ contrast:1 } });
    assert.deepEqual(none.rgb,base.rgb);
    const zeroDensity = ink.render(world,{ ...options, aerialPerspective:{ density:0 } });
    assert.deepEqual(zeroDensity.rgb,base.rgb);
    const transparent = ink.render(world,{ ...options, transparent:true });
    const cutout = ink.render(world,{ ...options, transparent:true, aerialPerspective:false });
    assert.deepEqual(transparent.alpha,cutout.alpha);
    assert(rgb(transparent,far)[0] > rgb(cutout,far)[0] + 80);
  }
});

test('aerial extinction follows cumulative dry distance and keeps its contrast floor through water', () => {
  const water = { depthRange:[0,1], extinction:[.4,.4,.4], tint:[0,0,0], deepTint:[0,0,0] };
  const medium = { ...settings, start:1.5, color:[1,.35,.15] };
  const out = traceMedia([], [[1,3,water,0]], [0,0,0], [1,0,0], 5,
    new Float64Array(6), [], {}, medium);
  const waterThrough = Math.exp(-.4*2), airThrough = K.skyEnvironment.airTransmission(medium,2);
  close(out[3],waterThrough*airThrough);
  close(out[0],waterThrough*(1-airThrough));
  close(out[4],out[3]);
  close(K.skyEnvironment.airTransmission(medium,1e6),settings.contrast);
  assert.throws(() => K.skyEnvironment.aerial({contrast:1.01}), /Aerial contrast/);
  assert.throws(() => K.skyEnvironment.aerial({start:-1}), /Aerial start/);
});

test('aerial scatter matches directional sky glow and excludes discrete sky objects', () => {
  const profile = K.skyEnvironment.compile({ defaults:{sunAzimuth:0,sunAltitude:0},
    sky:{splats:[{id:'mark',at:[0,0],size:[.04,.04],color:'#ee00ff'}]} }).frame(0).sky;
  const ray = [0,0,1];
  const air = K.skyEnvironment.scattering(profile,ray);
  assert.notDeepEqual(air,K.skyEnvironment.shade(profile,ray));
  assert.deepEqual(air,K.skyEnvironment.scattering(profile,[0,-.2,Math.sqrt(.96)]));
  assert(air.every(Number.isFinite));
});

test('deep haze does not wash over a nearer translucent splat', () => {
  function layers(front, back) {
    const B = makeBuilder(8, [0,0xde3232,0x0c1118]);
    if (back) B.disc(0,0,-20,[0,0,1],1.3,.025,B.P[2],3);
    if (front) B.disc(0,0,3,[0,0,1],.45,.025,B.P[1],.55,{nd:true});
    return B.finish({cam:{target:[0,0,0],dist:6,yaw:0,pitch:0},detail:18,radius:4,
      aerialPerspective:settings, skyEnvironment:profiles});
  }
  const center = 34*117+58;
  const front = ink.render(layers(true,false),{ ...shot, transparent:true });
  const rear = ink.render(layers(false,true),shot);
  const combined = ink.render(layers(true,true),shot);
  const alpha = front.alpha[center] / 255;
  assert(alpha > .5 && alpha < .6);
  for (const [channel, value] of rgb(combined,center).entries()) {
    const expected = alpha * rgb(front,center)[channel] + (1-alpha) * rgb(rear,center)[channel];
    close(value,expected,2.5);
  }
});

test('aerial perspective composes with a bounded local atmosphere', () => {
  const world = scene(false);
  const field = K.procedural.density.bounded({
    bounds:{ min:[-1,-1,-4.5],max:[1,1,-2] },
    sample:() => 1
  });
  const mist = { ...world, atmosphere:[K.atmosphere.field({field,density:.4,color:'#75c8a5'})] };
  const dry = ink.render(world, shot);
  const layered = ink.render(mist, { ...shot, volumeQuality:{ samples:2, jitter:'blue-noise' } });
  const middle = position(layered, 'middle');
  assert(layered.fog[middle] > dry.fog[middle] + .2);
  assert(rgb(layered,middle)[1] > rgb(dry,middle)[1] + 25);
  assert.deepEqual(rgb(layered,position(layered,'near')),rgb(dry,position(dry,'near')));
});

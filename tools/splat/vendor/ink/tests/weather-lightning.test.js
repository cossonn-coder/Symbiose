const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('..');
const { KIT: K, makeBuilder, makeSculpt } = ink.load();

const event = { id:'west', at:[0,2.8,-5], cue:'thunder', duration:.5, radius:2.5, falloff:2,
  attack:0, color:'#80a0ff', intensity:2 };
const cues = [K.anim.cue('thunder','sound',2)];

test('lightning resolves authored cues and samples independent of playback order', () => {
  const track = K.weather.lightning({ cues, events:[
    { ...event, id:'earlier', cue:undefined, time:.8 },
    event,
    { ...event, id:'later', cue:undefined, time:4, attack:.2, duration:1 }
  ] });
  assert.deepEqual(track.eventsBetween(1,2), [
    { id:'west', type:'lightning', time:2, duration:.5, at:[0,2.8,-5], cue:'thunder' }
  ]);
  assert.deepEqual(track.eventsBetween(2,2.6), []);
  assert.equal(track.frame(1.99), null);
  assert.equal(track.frame(2.5), null);
  assert.equal(track.frame(4), null);
  const colorAt = time => track.frame(time).light(...event.at);
  const after = colorAt(2.25);
  assert.equal(colorAt(2)[2], 2);
  assert.equal(after[2], .5);
  assert(Math.abs(colorAt(4.2)[2] - 2) < 1e-12);
  assert(colorAt(4.1)[2] < colorAt(4.2)[2]);
  assert.deepEqual(colorAt(2.25), after);
  assert.throws(() => K.weather.lightning({ events:[event] }), /Unknown lightning cue/);
  assert.throws(() => K.weather.lightning({ cues:[...cues,[3,'thunder']], events:[event] }), /Ambiguous lightning cue/);
  assert.throws(() => K.weather.lightning({ cues, events:[event,event] }), /unique event ids/);
  assert.throws(() => K.weather.lightning({ cues, events:[{ ...event, time:3 }] }), /either time or cue/);
  for (const change of [{ radius:0 }, { duration:0 }, { falloff:-1 }, { attack:1 }, { at:[0,0,Infinity] }])
    assert.throws(() => K.weather.lightning({ cues, events:[{ ...event, ...change }] }), /Lightning west/);
});

test('lightning adds overlapping local light with configurable range and falloff', () => {
  const sample = (events, x, normal) => K.weather.lightning({ cues, events }).frame(2).light(x,2.8,-5,normal);
  assert.equal(sample([event],2.5), undefined);
  assert.equal(sample([event],1.25)[2], .5);
  assert.equal(sample([{ ...event, falloff:1 }],1.25)[2], 1);
  assert.equal(sample([event],1.25,[-1,0,0])[2], .5);
  assert.equal(sample([event],1.25,[1,0,0])[2], .06);
  assert.deepEqual(sample([event,{...event,id:'overlap'}],1.25), sample([event],1.25).map(c => c*2));

  const mist = K.atmosphere.prepare([K.atmosphere.box({
    min:[-1,2,-6], max:[1,3,-4], color:'#252535', density:.42
  })]);
  const flash = K.weather.lightning({ cues, events:[event] }).frame(2);
  const origin = [0,2.8,1], direction = [0,0,-1];
  const quiet = K.atmosphere.trace(mist, origin, direction, 12);
  const lit = K.atmosphere.trace(mist, origin, direction, 12, undefined, { flash });
  assert(lit[2] > quiet[2] + .15);
  assert(Math.abs(lit[3] - quiet[3]) < 1e-12);
});

function build(pixel) {
  const B = makeBuilder(23, [0x162132,0x202c3e,0x374558,0xf7c342]);
  const S = K.sculpt(makeSculpt(B));
  S.pixel = pixel;
  const water = K.surface.material({ r:[1], materialId:'water' }, {
    layers:{ sky:{ type:'reflection', source:'scene', f0:1 } }
  });
  S.box([0,-.06,-.5],[3.1,.06,5.4],water,{res:.16});
  S.box([-.87,.77,-.84],[.20,.77,.16],{r:[2],materialId:'stone'},{res:.075});
  S.ball([-.87,1.69,-.76],.13,{r:[3],em:true,materialId:'lantern'},{res:.05});
  S.bake();
  return B.finish({
    cam:{ target:[0,.75,-1.5], dist:7.8, yaw:0, pitch:.37, sway:0 }, dither:0,
    skyEnvironment:{ defaults:{ zenith:'#20273a',horizon:'#20273a',ground:'#20273a',sunStrength:0 } },
    cloudField:K.clouds.compile({ bounds:{ min:[-9,-15],max:[9,9] }, coverage:()=>1,
      height:2.8, color:'#25273e', opacity:1 }),
    lightning:K.weather.lightning({ cues, events:[
      event,
      { id:'nearby', at:[-.44,1.3,.67], time:3, attack:0, duration:.3, radius:2.8, intensity:4 }
    ] })
  });
}

test('one world flash lights the cloud deck and appears in water through the scene reflection finish', () => {
  const world = build(false), opts = { w:128,h:84,px:1,raw:true,passes:['coverage','materialId'] };
  for (const ortho of [false,true]) {
    const view = { ...opts, ortho, t:2 };
    const off = ink.render(world, { ...view, lightning:false });
    const on = ink.render(world, { ...view, lightning:true });
    const noReflection = ink.render(world, { ...view, skyReflections:'material' });
    const staticReflection = ink.render(world, { ...view, skyReflections:'material', lightning:false });
    const cloudless = ink.render(world, { ...view, cloudField:false });
    const { coverage, materialId, materials } = on.passes;
    let sky = 0, clouds = 0, water = 0, stone = 0;
    for (let p=0; p<coverage.length; p++) {
      const blue = p*3+2, diff = on.rgb[blue] - off.rgb[blue];
      if (coverage[p] < .01 && diff > 12) {
        sky++;
        if (on.rgb[blue] > cloudless.rgb[blue]+20) clouds++;
      }
      if (coverage[p] < .98) continue;
      const material = materials[materialId[p]];
      if (material === 'water' && diff > 12 && Math.abs(noReflection.rgb[blue] - staticReflection.rgb[blue]) <= 2) water++;
      if (material === 'stone' && Math.abs(diff) <= 2) stone++;
    }
    assert(sky > 30 && clouds > 20, 'nearby clouds receive a stronger local flash than the sky halo');
    assert(water > 30, 'the water receives the flash even outside its direct lighting radius');
    assert(stone > 10, 'foreground geometry outside the light remains shaded');
    assert.deepEqual(ink.render(world, { ...view, t:2.5 }).rgb, off.rgb);
  }
});

test('a near flash reveals geometry including palette-painted surfaces and preserves emissive splats', () => {
  for (const pixel of [false,true]) {
    const world = build(pixel), view = { w:128,h:84,px:1,raw:true,t:3,passes:['coverage','materialId'] };
    const on = ink.render(world, view);
    const off = ink.render(world, { ...view, lightning:false });
    const { coverage, materialId, materials } = on.passes;
    let stone = 0, lantern = 0;
    for (let p=0; p<coverage.length; p++) {
      if (coverage[p] < .98) continue;
      const material = materials[materialId[p]], j = p*3;
      if (material === 'stone' && on.rgb[j+2] > off.rgb[j+2]+18) stone++;
      if (material === 'lantern' && Math.abs(on.rgb[j]-off.rgb[j]) <= 2) lantern++;
    }
    assert(stone > 10 && lantern > 0);
  }
});

test('an isolated flash preserves the existing material reflection away from the halo', () => {
  const world = build(false);
  const view = { w:128,h:84,px:1,raw:true,t:2,skyEnvironment:false,cloudField:false,passes:['materialId','coverage'] };
  const off = ink.render(world, { ...view, lightning:false });
  const behind = ink.render(world, { ...view, lightning:{ cues, events:[{ ...event, at:[0,2.8,30] }] } });
  const inFront = ink.render(world, view);
  assert(behind.rgb.every((value, i) => value === off.rgb[i]), 'an out-of-view flash leaves the frame identical');
  const { coverage, materialId, materials } = inFront.passes;
  const water = materials.indexOf('water');
  assert(materialId.some((id, p) => id === water && coverage[p] > .98 &&
    inFront.rgb[p*3] > off.rgb[p*3]+5), 'a flash appears over the material sky');
});

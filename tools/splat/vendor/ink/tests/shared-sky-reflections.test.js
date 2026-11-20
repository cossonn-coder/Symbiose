const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('..');
const { KIT: K, makeBuilder, makeSculpt, SurfaceLook } = ink.load();

const view = { w: 100, h: 80, px: 1, raw: true, passes: ['materialId', 'coverage', 'reflections'] };
const fill = color => ({ zenith: color, horizon: color, ground: color, sunStrength: 0 });
const profiles = K.skyEnvironment.compile({
  profiles: { day: fill('#2548ce'), dusk: fill('#de6333') },
  sequences: { cycle: { duration: 8, keys: [{ at: 0, profile: 'day' }, { at: 4, profile: 'dusk' }] } },
  tracks: [{ id: 'light', sequence: 'cycle' }]
});
const rgb = (frame, p) => [...frame.rgb.subarray(p * 3, p * 3 + 3)];
const rgbFromPass = (frame,p) => [...frame.passes.reflections.subarray(p*3,p*3+3)].map(v=>Math.round(v*255));

function scene({ planar = false, pixel = false } = {}) {
  const B = makeBuilder(4, [0x182332, 0x294854, 0xf2d22b]);
  const S = K.sculpt(makeSculpt(B));
  S.pixel = pixel;
  const material = source => K.surface.material({ r:[1], materialId: source }, {
    layers: { sky: { type:'reflection', source, sky:'#329068', horizon:'#329068', ground:'#329068', f0:1 } }
  });
  const plane = K.reflection.plane({ id:'water' });
  const env = material('scene');
  const water = planar ? K.reflection.material(env, 'water', { strength:1, f0:1 }) : env;
  S.box([0,-.055,0],[2,.055,1.68],water,{res:.10});
  if (planar) S.box([.4,.43,-.68],[.15,.39,.13],{r:[2],em:true,materialId:'post'},{res:.08});
  else S.box([0,.70,-.79],[.42,.065,.38],material('material'),{res:.085});
  S.bake();
  return B.finish({ cam:{target:[0,.2,0],dist:5.5,yaw:0,pitch:.57},detail:17,radius:4,dither:0,
    look:{pixel}, skyEnvironment:profiles, reflections:planar ? [plane] : [] });
}

function site(frame, name) {
  const { materialId, materials, coverage } = frame.passes, id = materials.indexOf(name);
  let p = -1, best = .985;
  for (let i = 0; i < materialId.length; i++) {
    if (materialId[i] !== id || coverage[i] <= best) continue;
    p = i;
    best = coverage[i];
  }
  assert(p >= 0, 'visible material ' + name);
  return p;
}
function close(a,b,tolerance=6) {
  assert(a.every((n, i) => Math.abs(n - b[i]) <= tolerance), a + ' vs ' + b);
}

test('backdrop and bound material share one sky profile in both projections', () => {
  for (const ortho of [false,true]) {
    const world = scene({ pixel:ortho }), settings = { ...view, ortho, raw:!ortho, coverageAware:ortho };
    const day = ink.render(world, { ...settings, t:0 });
    const dusk = ink.render(world, { ...settings, t:4 });
    const pixel = site(dusk, 'scene'), local = site(dusk, 'material');
    close(rgb(day,pixel),rgb(day,0));
    close(rgb(dusk,pixel),rgb(dusk,0));
    close(rgbFromPass(dusk,pixel),rgb(dusk,0),10);
    close(rgbFromPass(day,pixel),rgb(day,0),10);
    assert.deepEqual(rgbFromPass(dusk,0),[0,0,0]);
    assert(rgb(day,pixel)[2] > rgb(day,pixel)[0] + 90);
    assert(rgb(dusk,pixel)[0] > rgb(dusk,pixel)[2] + 120);
    close(rgb(day,local), rgb(dusk,local));
    const switched = ink.render(world, { ...settings, t:4, skyReflections:'material' });
    const [r,g,b] = rgb(switched,pixel);
    assert(g > r + 55 && g > b + 23, 'switching sources restores the material finish');
    assert.deepEqual(rgb(switched,0), rgb(dusk,0));
    const forced = ink.render(world, { ...settings, t:0, skyProfiles:{light:'dusk'}, skyReflections:'scene' });
    close(rgb(forced,local), rgb(forced,0));
    const unbound = ink.render(world, { ...settings, t:4, skyEnvironment:false });
    close(rgb(unbound,pixel),rgb(switched,pixel));
    const transparent = ink.render(world, { ...settings, t:4, transparent:true });
    assert.equal(transparent.alpha[0],0);
    close(rgb(transparent,pixel),rgb(dusk,pixel));
  }
});

test('planar captures still show local geometry over the shared sky', () => {
  const world = scene({planar:true});
  const options = { ...view, t:4 };
  const layered = ink.render(world, options), sky = ink.render(world, { ...options, reflections:false });
  const { materialId, materials, coverage } = layered.passes, water = materials.indexOf('scene');
  let capturePixels = 0, skyPixels = 0;
  for (let p = 0; p < materialId.length; p++) {
    if (materialId[p] !== water || coverage[p] < .985) continue;
    const delta = rgb(layered,p).reduce((diff, n, i) => diff + Math.abs(n - rgb(sky,p)[i]),0);
    if (delta > 30) {
      capturePixels++;
      assert.notDeepEqual(rgbFromPass(layered,p),rgbFromPass(sky,p));
    }
    if (delta <= 3 && Math.abs(rgb(sky,p)[0] - rgb(layered,0)[0]) < 3) skyPixels++;
  }
  assert(capturePixels > 10, 'reflected local geometry remains visible');
  assert(skyPixels > 100, 'sky stays visible through empty capture pixels');
});

test('scene reflection sends a world-space reflected direction to the sky sampler', () => {
  const prepared = SurfaceLook.prepare({ layers:{ sky:{type:'reflection',source:'scene',f0:1} } });
  let reflected;
  const sample = {
    position:[0,0,0], normal:[0,1,0], view:[0,1,0],
    skyNormal:() => [0,0,2], skyView:[1,0,1],
    sky(direction, rgb) { reflected = direction; rgb[0]=.92; rgb[1]=.25; rgb[2]=.1; }
  };
  const result = SurfaceLook.shade(prepared,sample,[.1,.1,.1]);
  assert.deepEqual(result.slice(0,3),[.92,.25,.1]);
  assert(reflected.every((v,i) => Math.abs(v - [-Math.SQRT1_2,0,Math.SQRT1_2][i]) < 1e-12));
  assert.throws(() => SurfaceLook.prepare({ layers:{ sky:{type:'reflection',source:'typo'} } }), /source must be/);
});

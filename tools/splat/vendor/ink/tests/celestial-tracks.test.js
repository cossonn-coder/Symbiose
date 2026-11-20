const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('..');
const { KIT: K, SkyEnvironment, makeBuilder, makeSculpt } = ink.load();
const tracks = K.celestialTracks;
const { PI } = Math;
const key = (at, azimuth, elevation = .12, extra) => ({ at, azimuth, elevation, ...extra });
const direction = (az, el) => [Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el)];
const at = (id, kind, az = 0, extra) => ({ id, kind, keys: [key(0, az)], ...extra });
const cam = { target: [0, 0, 0], yaw: 0, pitch: -.12, dist: 5 };
const view = { w: 81, h: 61, px: 1, raw: true };
const pixel = (f, x, y) => [...f.rgb.subarray((y * f.w + x) * 3, (y * f.w + x) * 3 + 3)];

test('celestial keys hold through beats, wrap azimuth and can repeat unwrapped paths', () => {
  const hold = tracks.compile({ primarySun: 'sun', bodies: [
    at('sun', 'sun', 0, { keys: [key(0, 0, .01, { ease: 'hold' }), key(3, 0, .12), key(5, 1, .32)] }),
    at('wrapped', 'star', 0, { keys: [key(0, .05, .12), key(2, 2*PI - .05)] }),
    at('orbit', 'moon', 0, {
      azimuthMode: 'unwrapped', period: 4, keys: [key(0, 0, .12, { ease: 'linear' }), key(4, 2*PI)]
    })
  ] });
  assert.deepEqual(hold.frame(2).sun.direction, hold.frame(0).sun.direction);
  assert.notDeepEqual(hold.frame(3).sun.direction, hold.frame(0).sun.direction);
  assert(Math.abs(hold.frame(1).body('wrapped').direction[0]) < 1e-10);
  assert(hold.frame(1).body('orbit').direction[0] > .99);
  assert.deepEqual(hold.frame(5).body('orbit'), hold.frame(1).body('orbit'));
  assert.deepEqual(hold.frame(-3).body('orbit'), hold.frame(1).body('orbit'));
  assert.throws(() => tracks.compile({ primarySun: 'x', bodies: [at('x', 'moon')] }), /must name a sun/);
  assert.throws(() => tracks.compile({ bodies: [at('x', 'eclipse', 0, { target: 'missing' })] }), /target/);
  assert.throws(() => tracks.compile({ bodies: [at('x', 'star', 0, { keys: [key(1, 0), key(1, 1)] })] }), /increase/);
  assert.throws(() => tracks.compile({ bodies: [at('x', 'star'), at('x', 'moon')] }), /unique/);
});

test('eclipses mask their named disk, retain its surrounding glow and attenuate primary sunlight', () => {
  const track = tracks.compile({ primarySun: 'sun', bodies: [
    at('far', 'moon', 0, { radius: .12, color: '#4468ff', distance: 1000 }),
    at('sun', 'sun', 0, { radius: .1, color: '#ff8040' }),
    at('transit', 'eclipse', 0, { target: 'sun', radius: .12, start: 1, end: 3 }),
    at('other', 'sun', -.24, { radius: .04, color: '#80ff40' })
  ] });
  const center = direction(0, .12);
  assert.deepEqual(track.frame(0).shade(center), [1,128/255,64/255]);
  assert.deepEqual(track.frame(2).shade(center), [68/255,104/255,1]);
  assert.deepEqual(track.frame(2).shade(direction(-.24,.12)), [128/255,1,64/255]);
  assert.equal(track.frame(2).sun.gain, 0);
  assert.equal(track.frame(3).sun.gain, 1);
  const corona = tracks.compile({ primarySun:'sun', bodies:[
    at('sun','sun',0,{radius:.1,glow:.6,glowRadius:.3}), at('transit','eclipse',0,{target:'sun',radius:.05})
  ] }).frame(0);
  assert.equal(corona.sun.gain,.75);
  assert(corona.shade(center)[0] < .7 && corona.shade(center)[0] > .4);
  assert(corona.shade(direction(.08,.12))[0] > .9);
});

test('lunar phase changes which half lights up, and keyed size and opacity can hide a body', () => {
  const moon = tracks.compile({ bodies: [at('moon', 'moon', 0, { color: '#ffffff', darkColor: '#000000',
    radius:.12, keys:[key(0,0,.12,{phase:.5}),key(2,0,.12,{phase:-.5}),key(4,0,.12,{radius:.025,opacity:.4})]
  })] });
  const left = direction(-.06,.12), right = direction(.06,.12);
  assert.equal(moon.frame(0).shade(left)[0], 0);
  assert.equal(moon.frame(0).shade(right)[0], 1);
  assert.equal(moon.frame(2).shade(left)[0], 1);
  assert.equal(moon.frame(2).shade(right)[0], 0);
  assert.equal(moon.frame(4).shade(right)[0], 0);
  assert.equal(moon.frame(4).body('moon').opacity,.4);
  assert.deepEqual(moon.frame(0).shade([0,-1,0],[.1,.2,.3]), [.1,.2,.3]);
});

test('headless rendering shares the sky clock and accepts scene switches and JSON-shaped overrides', () => {
  const world = makeBuilder(1,[0x162033]).finish({ cam, celestialTracks: {
    bodies: [at('moving','sun',PI,{ radius: .06, keys:[key(0,PI),key(2,PI-.22)] })]
  } });
  const on = opts => ink.render(world, { ...view, ...opts });
  const off = on({ t: 0, celestialTracks: false }), center = [40,30];
  assert.deepEqual(pixel(off,...center),[22,32,51]);
  assert(pixel(on({t:0}),...center)[0] > 200);
  assert.deepEqual(pixel(on({t:2}),...center),pixel(off,...center));
  assert.deepEqual(on({t:2,skyTime:0,celestialTracks:true}).rgb,on({t:0}).rgb);
  assert.deepEqual(on({t:0,target:[3,2,-9]}).rgb,on({t:0}).rgb);
  assert.deepEqual(on({t:0,celestialTracks:{bodies:[]}}).rgb,off.rgb);
  assert.deepEqual(on({t:0,transparent:true}).alpha,on({t:0,transparent:true,celestialTracks:false}).alpha);
});

test('primary tracks drive configured lights while celestial silhouettes stay out of aerial scattering', () => {
  const celestial = tracks.compile({ primarySun:'sun', bodies:[at('sun','sun',0,{radius:.08}),
    at('mask','eclipse',0,{target:'sun',radius:.04})] }).frame(0);
  const legacy = SkyEnvironment.compile({defaults:{sunAzimuth:1.8}}).frame(0).sky;
  const sky = SkyEnvironment.withCelestials(legacy,celestial);
  const center = celestial.sun.direction;
  assert.deepEqual(sky.sun,center);
  assert.equal(sky.sunStrength,legacy.sunStrength * .75);
  assert.notDeepEqual(SkyEnvironment.shade(sky,direction(.06,.12)),SkyEnvironment.scattering(sky,direction(.06,.12)));
  const { prepare } = require('../cli/live-sun.js');
  const live = prepare({direction:[0,1,0],intensity:2},undefined,0,celestial.sun);
  assert.deepEqual(live.direction,center);
  assert.equal(live.intensity,1.5);
  const volume = require('../src/scene-optics.js').lighting({sun:{direction:[0,1,0], intensity:2}},[0],
    {celestialSun:celestial.sun});
  assert.deepEqual(volume.sun.direction,center);
  assert.equal(volume.sun.intensity,1.5);
  const setting = tracks.compile({primarySun:'sun', bodies:[at('sun','sun',0,{
    radius:.09, keys:[key(0,0,.1),key(1,0,0),key(2,0,-.1)]
  })]});
  assert.deepEqual([0,1,2].map(t=>setting.frame(t).sun.gain),[1,.5,0]);
});

test('reflective surfaces sample the authored celestial disks through the active sky', () => {
  const builder = makeBuilder(1,[0x141d32,0x263746]);
  const sculpt = K.sculpt(makeSculpt(builder));
  const water = K.surface.material({ r:[1] }, {
    layers: { sky:{ type:'reflection', source:'scene', sky:'#141d32', horizon:'#141d32', ground:'#141d32', f0:1 } }
  });
  sculpt.box([0,-.056,0],[2.3,.06,2.3],water,{res:.096});
  sculpt.bake();
  const world = builder.finish({
    cam:{target:[0,.25,0],yaw:0,pitch:.46,dist:5.8},skyReflections:'scene',
    celestialTracks:{bodies:[at('moon','moon',PI,{radius:.18,keys:[key(0,PI,.42)]})]}
  });
  const render = settings => ink.render(world,{...view,...settings,passes:['coverage']});
  const bright = render({}), off = render({celestialTracks:false});
  let changed = 0;
  for (let p=0;p<bright.passes.coverage.length;p++) {
    if (bright.passes.coverage[p]>.8 && bright.rgb[p*3]>off.rgb[p*3]+30) changed++;
  }
  assert(changed > 25,'disks contribute to shaded pixels on the water');
});

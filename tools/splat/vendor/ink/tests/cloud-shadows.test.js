const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('../index.js');
const { traceMedia } = require('../cli/scene-optics.js');
const { KIT: K, makeBuilder, makeSculpt } = ink.load();

const field = {
  bounds: { min: [-5, -4], max: [5, 4] }, resolution: [40, 32],
  coverage: (x, z) => Number(Math.abs(x + 2) < 1 && Math.abs(z) < 2),
  height: 2, velocity: [2, 0], color: '#ffffff', opacity: 1
};
const sharp = K.clouds.shadowSettings({ strength: 1, softness: 0, direction: [0, 1, 0] });

test('cloud coverage, visible cloud and projected shadow move together', () => {
  const grid = K.clouds.compile(field);
  for (const [t, x] of [[0, -2], [2, 2]]) {
    const frame = grid.frame(t, sharp);
    assert.equal(frame.coverage(x, 0), 1);
    assert.deepEqual(frame.paint([x, 0, 0], [0, 1, 0], [0, 0, 0]), [1, 1, 1]);
    assert.equal(frame.shadow(x, 0, 0), 0);
    assert.equal(frame.shadow(-x, 0, 0), 1);
    assert.equal(frame.shadow(x, 2, 0), 1);
  }
  const angled = grid.frame(0, { ...sharp, direction: [1, 1, 0] });
  assert.equal(angled.shadow(-4, 0, 0), 0);
  assert.equal(angled.shadow(-3, 1, 0), 0);
  assert.equal(grid.frame(0, { ...sharp, direction: [0, -1, 0] }).shadow, null);
  assert.equal(grid.frame(0, K.clouds.shadowSettings(sharp, false)).shadow, null);
  assert.equal(K.clouds.shadowSettings(true, undefined, { cloudShadowStrength: 0 }), null);
  assert.equal(K.clouds.shadowSettings(true, { strength:.5 }, { cloudShadowStrength: 0 }).strength, .5);
  assert.throws(() => K.clouds.shadowSettings({ softness: -1 }), /softness/);
  assert.throws(() => K.clouds.compile({ ...field, coverage: [1] }), /row-major/);
  const repeating = K.clouds.compile({ ...field, repeat: true }).frame(0, sharp);
  assert.equal(repeating.shadow(8, 0, 0), 0);
  const blurred = grid.frame(0, { ...sharp, softness: .65 });
  assert(blurred.shadow(-2, 0, 0) > 0);
  assert(blurred.shadow(-.7, 0, 0) < 1);
  assert.equal(blurred.coverage(-2, 0), 1);
});

test('clouds dim the scattering in fog and water while preserving their transmittance', () => {
  const cloudShadow = K.clouds.compile(field).frame(0, sharp).shadow;
  const fog = K.atmosphere.prepare([K.atmosphere.box({
    min: [-3, 0, -2], max: [-1, .5, 2], color: '#f0f0f0', density: .5
  })]);
  const origin = [-2, .25, 3], direction = [0, 0, -1];
  const fogOpen = K.atmosphere.trace(fog, origin, direction, 5);
  const fogShadow = K.atmosphere.trace(fog, origin, direction, 5, undefined, { cloudShadow });
  assert(fogShadow[0] < .65 * fogOpen[0]);
  assert(Math.abs(fogShadow[3] - fogOpen[3]) < 1e-12);

  const density = { bounds: { min: [-3, 0, -1], max: [-1, .5, 1] }, sample: () => 1 };
  const lit = K.atmosphere.prepare([K.atmosphere.field({ field: density, anisotropy: 0, density: .5,
    color: '#202020', emissive: '#150900', emissiveGain: 1 })]);
  const ambient = K.atmosphere.lighting({ ambient: .2, point: { at: [-2, .3, .5], radius: 1 } });
  const media = K.atmosphere.lighting({ ambient: .2, point: { at: [-2, .3, .5], radius: 1 },
    sun: { direction: [0, 1, 0] } });
  const atmospheric = options => K.atmosphere.trace(lit, origin, direction, 5, undefined, options);
  assert.deepEqual(atmospheric({ media, cloudShadow }), atmospheric({ media: ambient }));
  assert(atmospheric({ media })[0] > atmospheric({ media, cloudShadow })[0]);

  const style = { tint: [.4, .7, .8], deepTint: [.1, .3, .4], depthRange: [0, 1], extinction: [1, .4, .2] };
  const water = options => traceMedia([], [[2, 4, style, .5]], origin, direction, 5,
    new Float64Array(6), [0, 0, 0, 1], options);
  const openWater = water(), shadedWater = water({ cloudShadow });
  assert(shadedWater[1] < .5 * openWater[1]);
  assert.deepEqual(shadedWater.slice(3), openWater.slice(3));
});

test('the renderer can toggle moving shadows on sculpted materials in both camera modes', () => {
  const B = makeBuilder(5, [0x273243, 0x68635a, 0xd9c7a1, 0xffd751]);
  const S = K.sculpt(makeSculpt(B));
  S.captureAlbedo = true;
  S.box([0, -.15, 0], [3.5, .15, 2], { r:[1, 2], materialId:'ground' }, { res:.16 });
  S.ball([-2, .35, 0], .24, { r:[3], materialId:'lamp', em:true }, { res:.06 });
  S.bake();
  const world = B.finish({ cam:{ target:[0,0,0], dist:10, pitch:.6, yaw:0, sway:0 },
    cloudField: K.clouds.compile(field), cloudShadows: sharp,
    liveSun:{ direction:[0,1,0], intensity:.8, ambient:.2, shadows:false } });
  for (const ortho of [false, true]) for (const liveSun of [false, undefined]) {
    const options = { w:111, h:77, px:1, raw:true, ortho, liveSun, passes:['materialId', 'position', 'coverage'] };
    const clear = ink.render(world, { ...options, cloudShadows:false });
    const left = ink.render(world, options);
    const right = ink.render(world, { ...options, skyTime:2 });
    const { materials, materialId, position, coverage } = left.passes;
    let count = [0,0], lamps = 0;
    for (let p = 0; p < materialId.length; p++) {
      if (coverage[p] < .98) continue;
      const j = p * 3, x = position[j];
      if (materials[materialId[p]] === 'lamp') {
        if (left.rgb[j] > 247 && clear.rgb[j] > 247 && Math.abs(left.rgb[j] - clear.rgb[j]) <= 2) lamps++;
      }
      if (materials[materialId[p]] !== 'ground' || Math.abs(position[j + 2]) > 1) continue;
      if (x < -1.3 && x > -2.7 && clear.rgb[j] - left.rgb[j] > 50 && Math.abs(right.rgb[j] - clear.rgb[j]) <= 2) count[0]++;
      if (x > 1.3 && x < 2.7 && clear.rgb[j] - right.rgb[j] > 50 && Math.abs(left.rgb[j] - clear.rgb[j]) <= 2) count[1]++;
    }
    assert(count.every(n => n > 10), 'the shadow leaves the first patch and reaches the second');
    assert(lamps > 0);
    assert.deepEqual(clear.rgb, ink.render(world, { ...options, cloudShadows:{ strength:0 } }).rgb);
    assert.throws(() => ink.render({ ...world, cloudField:undefined }, options), /need a cloud field/);
  }
});

const assert = require('node:assert/strict');
const test = require('node:test');
const studio = require('../index.js');
const { KIT: K, makeBuilder, SceneOptics: optics } = studio.load();

const span = { min: [-1, -1, -1], max: [1, 1, 1] };
const near = (actual, expected, epsilon = 1e-5) => assert(Math.abs(actual - expected) < epsilon, actual + ' vs ' + expected);

test('bounded varying density integrates depth and lights with occlusion', () => {
  const density = K.procedural.density.bounded({ bounds: span, sample: () => .5 });
  const volume = K.atmosphere.field({ field: density, density: 2, color: '#808080', step: .11, anisotropy: 0 });
  const list = optics.prepareVolumes([volume]);
  const origin = [0, 0, 2], ray = [0, 0, -1];
  const result = optics.trace(list, origin, ray, 6);
  near(result[3], Math.exp(-2));
  near(result[0], 128 / 255 * (1 - result[3]));
  const blocked = optics.trace(list, origin, ray, 1.5);
  near(blocked[3], Math.exp(-.5));
  const media = optics.lighting({
    ambient: .15, sun: { direction: [0, 1, 0], color: '#ffffff', intensity: .7 },
    point: { at: [0, .3, 0], color: '#ff0000', radius: 4, intensity: .8 }
  });
  const lit = optics.trace(list, origin, ray, 6, undefined, { media });
  assert(lit[0] > lit[1]);
  const shadow = optics.occluder((x, y, z) => Math.hypot(x, y - .9, z) - .7);
  const shade = optics.trace(list, origin, ray, 6, undefined, { media: { ...media, shadow } });
  assert(shade[1] < lit[1]);
  near(shade[3], lit[3]);
  const emit = optics.prepareVolumes([K.atmosphere.field({ field: density, density: 2, color: '#000000',
    emissive: '#22ccff', emissiveGain: .5 })]);
  assert(optics.trace(emit, origin, ray, 6)[2] > .4);
});

test('sparse density supports empty-space skipping, meshing and deterministic placements', () => {
  const D = K.procedural.density;
  const extent = { min: [-3, -3, -3], max: [3, 3, 3] };
  const sphere = D.fromSdf({ bounds: extent, field: (x, y, z) => Math.hypot(x, y, z) - .85, feather: .2 });
  const compact = D.sparse(sphere, { resolution: [40, 40, 40], brick: 4 });
  assert(compact.bricks < 60);
  assert(compact.skip(0, 0, 2.9, [0, 0, -1]) > .4);
  const volume = optics.prepareVolumes([K.atmosphere.field({ field: compact, density: 1, step: .08 })]);
  const dense = optics.trace(volume, [0, 0, 3.2], [0, 0, -1], 7, undefined, { skip: false, maxSteps: 128 });
  const sparse = optics.trace(volume, [0, 0, 3.2], [0, 0, -1], 7, undefined, { skip: true, maxSteps: 128 });
  for (let c = 0; c < 4; c++) near(sparse[c], dense[c]);
  const mesh = D.toMesh(sphere, { resolution: .23, maxCells: 40000 });
  assert(K.mesh.info(mesh).tris > 20);
  assert.equal(K.mesh.info(mesh).open, 0);
  const a = D.scatter(sphere, { radius: .24, maxPoints: 18, seed: 4, reseed: 40 });
  assert(a.samples.length > 5);
  assert.deepEqual(a, D.scatter(sphere, { radius: .24, maxPoints: 18, seed: 4, reseed: 40 }));
});

test('low-resolution volumes reuse rays and respect opaque depth boundaries', () => {
  const B = makeBuilder(2, [0, 0xffffff, 0x778899, 0x334455]);
  B.disc(0, 0, 1, [0, 0, 1], .41, .04, B.P[2], 3);
  const field = K.procedural.density.bounded({ bounds: { min: [-3, -3, -2], max: [3, 3, 0] }, sample: () => 1 });
  const world = B.finish({ cam: { target: [0, 0, 0], dist: 5, yaw: 0, pitch: 0 },
    atmosphere: [K.atmosphere.field({ field, density: 1, color: '#ffffff' })] });
  const options = { w: 64, h: 64, px: 1, ortho: true, captureFog: true };
  const fine = studio.render(world, { ...options, volumeQuality: { stats: true } });
  const low = studio.render(world, { ...options, volumeQuality: { stats: true, scale: 2 } });
  assert(low.volumeStats.rays < fine.volumeStats.rays * .68);
  near(low.fog[32 * 64 + 32], 0);
  assert(low.fog[0] > .8);
  assert.deepEqual(low.rgb.slice((32 * 64 + 32) * 3, (32 * 64 + 32) * 3 + 3),
    fine.rgb.slice((32 * 64 + 32) * 3, (32 * 64 + 32) * 3 + 3));
  const disabled = studio.render(world, { ...options, atmosphere: false });
  assert.notDeepEqual(low.rgb, disabled.rgb);
  assert.equal(disabled.fog, undefined);
});

test('volume history combines compatible frames and rejects a depth break or camera cut', () => {
  const history = K.atmosphere.history({ weight: .5, maxGap: .2 });
  const depths = new Float32Array([3, 3]);
  const first = new Float32Array([.4, .2, 0, .6, .1, .1, .1, 1]);
  history.filter(first, depths, 0, 'a');
  const next = new Float32Array([.2, 0, 0, .6, .6, 0, .1, 1]);
  history.filter(next, new Float32Array([3, 4]), .1, 'a');
  near(next[0], .3);
  near(next[4], .6);
  const cut = new Float32Array([.1, 0, 0, .6, .2, 0, .1, 1]);
  history.filter(cut, depths, .2, 'b');
  near(cut[0], .1);
  const D = K.procedural.density;
  const drift = D.fromSdf({ bounds: span, field: () => -1, noise: x => .5 + x * .4, breakup: 1, windInfluence: 1 });
  near(drift.sample(0, 0, 0, 1, { wind: [.5, 0] }), .3);
});

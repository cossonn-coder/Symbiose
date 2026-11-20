const assert = require('node:assert/strict');
const test = require('node:test');
const studio = require('../index.js');
const { ArtInk, ArtStability, makeBuilder } = studio.load();

test('ink distinguishes silhouettes, creases, boundaries and protected palettes', () => {
  const palette = [0, 0x445566, 0x8e9fa4];
  const settings = ArtInk.prepare({
    silhouette: { color: '#110000' }, crease: { color: '#001100' }, boundary: { color: '#000011' },
    materials: { vapor: { palette: 'fog' } },
    reserved: { emission: ['#ffff00'], fog: ['#44ddff'] }
  }, palette);
  const w = 7, h = 5, size = w * h;
  const depth = new Float32Array(size).fill(3);
  const normal = new Float32Array(size * 3);
  const emission = new Float32Array(size * 3);
  const objectId = new Uint32Array(size).fill(1), materialId = new Uint32Array(size).fill(1);
  const splatId = Uint32Array.from(depth, (_, i) => i + 1);
  for (let i = 0; i < size; i++) normal[i * 3 + 1] = 1;
  const crease = 2 * w + 1, boundary = 2 * w + 3, sameMaterial = 1 * w + 1;
  normal.fill(0, (crease + 1) * 3, (crease + 2) * 3);
  normal[(crease + 1) * 3] = 1;
  objectId[boundary + 1] = 2;
  materialId[boundary + 1] = 2;
  objectId[sameMaterial + 1] = 2;
  materialId[3 * w + 2] = 3;
  emission[(3 * w + 5) * 3] = .9;
  const frame = ArtInk.apply({ w, h, rgb: new Uint8Array(size * 3).fill(89) },
    { depth, normal, emission, objectId, materialId, splatId, materials: [null, 'stone', 'metal', 'vapor'] },
    settings, palette);
  assert.equal(frame.inkMask[0], 1);
  assert.equal(frame.inkMask[crease], 2);
  assert.equal(frame.inkMask[boundary], 3);
  assert.equal(frame.inkMask[sameMaterial], 0);
  assert.equal(frame.inkMask[3 * w + 2], 4);
  assert.equal(frame.inkMask[3 * w + 5], 4);
  assert(frame.palette.includes(0xffff00));
  assert.equal(frame.use.reduce((a, b) => a + b), size);
});

test('orthographic snap is optional and anchored positions follow analytic motion', () => {
  const b = makeBuilder(1, [0, 0x445566, 0x8e9fa4]);
  b.disc(0, 0, 0, [0, 0, 1], .18, .04, b.P[1], 3, { k: 6, rg: .45, sp: 1 });
  b.describeSplats(0, 1, { object: 'eye', material: 'detail' });
  const world = b.finish({ cam: { target: [0, 0, 0], yaw: 0, pitch: 0, dist: 5 } });
  const options = { w: 64, h: 64, px: 1, ortho: true };
  const snap = { ...options, stable: { snap: true } };
  const atOrigin = studio.render(world, snap).rgb;
  assert.deepEqual(studio.render(world, { ...snap, target: [.015, .01, 0] }).rgb, atOrigin);
  assert.notDeepEqual(studio.render(world, { ...snap, target: [.1, .07, 0] }).rgb, atOrigin);

  const passes = ['splatId', 'position', 'objectPosition'];
  const frame = studio.render(world, { ...options, t: Math.PI / 2, passes });
  const hit = frame.passes.splatId.indexOf(1), p = hit * 3;
  assert(hit >= 0);
  assert(Math.abs(frame.passes.position[p + 1] - frame.passes.objectPosition[p + 1] - .45) < 1e-6);
  const anchored = ArtStability.prepare({ dither: 'object', spacing: .1 });
  assert.notDeepEqual(ArtStability.ditherCoordinates(anchored, frame.passes, hit, 10, 9), [10, 9]);

  const clusters = studio.render(world, { ...options, stable: { resolve: 'clusters', protect: ['eye'] } });
  assert(clusters.detail.some(Boolean));
  assert(clusters.rgb.some(Boolean));
  assert.equal(clusters.rgb.length, 64 * 64 * 3);
});

test('glow and haze use emissive sources and protect nearer surfaces', () => {
  const { ArtEffects } = studio.load();
  const w = 11, h = 7, size = w * h, palette = [0x001122, 0x112233, 0x405060];
  const rgb = Uint8Array.from({ length: size * 3 }, (_, j) => 16 + 6 * (Math.floor(j / 3) % w));
  const depth = new Float32Array(size).fill(6);
  const emission = new Float32Array(size * 3);
  const emissionDepth = new Float32Array(size).fill(Infinity);
  const source = w * 4 + 5;
  emission[source * 3] = .9;
  emissionDepth[source] = 4;
  depth[source - 1] = 2;
  const passes = { w, h, depth, emission, emissionDepth, materialId: new Uint32Array(size), materials: [null] };
  const setup = ArtEffects.prepare({ heat: { radius: 4, up: 2, pixels: 2 },
    glow: { colors: ['#993322', '#ee8844'], radius: 2 }, emitter: { colors: ['#ffff00'] } }, palette);
  const frame = ArtEffects.apply({ w, h, rgb: rgb.slice() }, passes, setup, .31, { palette });
  assert.deepEqual(frame.rgb.slice((source - 1) * 3, source * 3), rgb.slice((source - 1) * 3, source * 3));
  assert.equal(frame.effectsMask[source - 1], 0);
  assert.equal(frame.effectsMask[source], 4);
  assert(frame.effectsMask.includes(1));
  assert(frame.effectsMask.includes(2));
  assert(!frame.effectsMask[0]);
});

test('motion, trails and stepped smears consume an explicit render history', () => {
  const { ArtEffects } = studio.load();
  const palette = [0, 0xcc6655, 0xffdd99];
  const b = makeBuilder(1, palette);
  b.disc(0, 0, 0, [0, 0, 1], .11, .03, b.P[2], 1.5, { em: true, k: 6, rg: .80, sp: 5 });
  const world = b.finish({ cam: { target: [0, 0, 0], yaw: 0, pitch: 0, dist: 5 }, look: {
    effects: { trail: { duration: .6 }, smear: { duration: .6, reach: 36 } }
  } });
  const artHistory = ArtEffects.history();
  const opts = { w: 56, h: 56, px: 1, ortho: true, captureMotion: true,
    passes: ['motion', 'emissionMotion'], artHistory };
  const first = studio.render(world, { ...opts, t: 0 });
  assert(!first.effectsMask.some(Boolean));
  const second = studio.render(world, { ...opts, t: .3, motionFrom: first.motionReference });
  assert(second.passes.motion.some(value => value < -5));
  assert(second.passes.emissionMotion.some(value => value < -5));
  assert(second.effectsMask.includes(3));
  const withoutHistory = studio.render(world, { ...opts, t: .3, artHistory: null });
  assert(!withoutHistory.effectsMask.some(Boolean));
  assert.notDeepEqual(second.rgb, withoutHistory.rgb);
});

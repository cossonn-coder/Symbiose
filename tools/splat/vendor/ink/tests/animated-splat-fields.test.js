const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('..');
const { KIT: K, makeBuilder, makeSculpt } = ink.load();
const cam = { target: [0, 0, 0], dist: 5, yaw: 0, pitch: 0 };
const view = { w: 41, h: 41, px: 1, raw: true, ortho: true };
const center = 20 * 41 + 20;
const rgb = (f, p = center) => Array.from(f.rgb.subarray(p * 3, p * 3 + 3));
const asset = edits => ({
  fields: [{
    id: 'test',
    shape: { type: 'box', size: [0, 0, 0] },
    life: { rate: 1, lifetime: [1, 1], fadeIn: 0, fadeOut: 0 },
    style: { color: 0xff2000, size: 0.2, opacity: 0.8, emissive: true },
    ...edits
  }]
});
const visible = buffer => {
  const rows = [];
  for (let q = 0; q < buffer.length; q += 16)
    if (buffer[q + 3] > 0) rows.push(Array.from(buffer.subarray(q, q + 16)));
  return rows;
};
const rowsAt = (source, time, options) => visible(K.splatFields.compile(source).frame(time, options));

test('all presets seek independently of playback order and respect emission windows', () => {
  for (const preset of K.splatFields.presets) {
    const field = K.splatFields.compile({ fields: [{ id: preset, preset }] });
    const atTwo = field.frame(2);
    assert(visible(atTwo).length > 0);
    field.frame(18);
    field.frame(-1);
    assert.deepEqual(field.frame(2), atTwo);
    assert.notDeepEqual(field.frame(2.5), atTwo);
  }
  const finite = asset({ life: { start: 2, end: 2.5, rate: 4, lifetime: [1, 1] } });
  assert.equal(rowsAt(finite, 1.9).length, 0);
  assert.equal(rowsAt(finite, 2.6).length, 3);
  assert.equal(rowsAt(finite, 3.6).length, 0);
  const { fields: [field] } = asset();
  assert.throws(() => K.splatFields.compile({ fields: [field, field] }), /unique/);
  assert.throws(() => K.splatFields.compile(asset({ life: { rate: 4096 } })), /budget/);
  assert.throws(() => K.splatFields.compile(asset({ shape: { type: 'ribbon', points: [[0,0,0],[1,0,0]], depth: -1 } })), /depth/);
});

test('a ribbon has authored depth and a wake remembers where each splat was born', () => {
  const shape = { type: 'ribbon', points: [[-1,0,0],[1,0,0]], height: 2, depth: 3 };
  const ribbon = rowsAt(asset({ shape, life: { rate: 25, lifetime: [1, 1] } }), 0.9);
  assert(ribbon.every(([x,y,z]) => Math.abs(x) <= 1 && y >= 0 && y <= 2 && Math.abs(z) <= 1.5));
  assert(ribbon.some(row => Math.abs(row[2]) > 1));
  const wake = asset({
    shape: { type: 'path', points: [[0,0,0],[6,0,0]], duration: 3, height: 0, depth: 0 },
    life: { rate: 2, lifetime: [1, 1], fadeIn: 0, fadeOut: 0 },
    motion: { wind: 0.5, velocity: [0,1,0] }
  });
  const still = rowsAt(wake, 1.25);
  assert.deepEqual(still.map(row => row.slice(0,3)), [[1,.75,0],[2,.25,0]]);
  const moving = rowsAt(wake, 1.25, { travel: (_at, from, to) => [0, 4*(to-from)] });
  assert.deepEqual(moving.map(row => row.slice(0,3)), [[1,.75,1.5],[2,.25,.5]]);
  assert.equal(rowsAt(wake, 5).length, 0);
});

test('native fields sort on both sides of opaque objects in perspective and orthographic rendering', () => {
  const B = makeBuilder(1, [0, 0x204099]);
  B.disc(0, 0, 0, [0,0,1], 0.6, 0.05, B.P[1], 3);
  const p = z => asset({ shape: { type: 'box', at: [0,0,z], size: [0,0,0] } });
  const world = B.finish({ cam, splatFields: p(1) });
  const original = world.data.slice();
  for (const ortho of [false, true]) {
    const settings = { ...view, ortho, t: 0.5, passes: ['emission', 'depth'] };
    const off = ink.render(world, { ...settings, splatFields: false });
    const far = ink.render(world, { ...settings, splatFields: p(-1) });
    const near = ink.render(world, settings);
    assert(rgb(far).every((value, i) => Math.abs(value - rgb(off)[i]) <= 3));
    assert(rgb(near)[0] > rgb(off)[0] + 100);
    assert(far.passes.emission[center * 3] < 0.01);
    assert(near.passes.emission[center * 3] > 0.5);
    assert.equal(near.passes.depth[center], off.passes.depth[center]);
  }
  assert.equal(world.count, 1);
  assert.deepEqual(world.data, original);
});

test('shared scene wind moves particles and motion passes reject recycled slots', () => {
  const moving = asset({ motion: { wind: 1 } });
  const world = makeBuilder(1, [0]).finish({ cam, splatFields: moving, windField: { velocity: [1, 0] } });
  const opts = { ...view, captureMotion: true, passes: ['emissionMotion'] };
  const a = ink.render(world, { ...opts, t: .2 });
  const b = ink.render(world, { ...opts, t: .4, motionFrom: a.motionReference });
  const recycled = ink.render(world, { ...opts, t: 2.4, motionFrom: a.motionReference });
  assert(b.passes.emissionMotion.some(n => n > 1));
  assert(recycled.motionReference.centers.some(Number.isFinite));
  assert(!recycled.passes.emissionMotion.some(Boolean));
});

test('fields appear in the existing planar capture and can be toggled independently', () => {
  const B = makeBuilder(1, [0, 0x102d57]);
  const S = K.sculpt(makeSculpt(B));
  const mirror = K.reflection.material({ r: [1] }, 'lake', { strength: 1, f0: 1 });
  S.box([0,-.06,0], [2,.06,1.8], mirror, { res: .08 });
  S.bake();
  const world = B.finish({
    cam: { ...cam, target: [0,.3,0], pitch: .52 }, reflections: [K.reflection.plane({ id: 'lake' })],
    splatFields: asset({ shape: { type: 'box', at: [0,.6,0], size: [0,0,0] } })
  });
  const opts = { ...view, w: 91, h: 91, ortho: false, t: .3 };
  const reflected = ink.render(world, opts);
  const direct = ink.render(world, { ...opts, reflections: false });
  let gained = 0;
  for (let i = 0; i < reflected.rgb.length; i += 3)
    if (reflected.rgb[i] > direct.rgb[i] + 30) gained++;
  assert(gained > 10);
  const off = ink.render(world, { ...opts, splatFields: false });
  assert.notDeepEqual(reflected.rgb, off.rgb);
});

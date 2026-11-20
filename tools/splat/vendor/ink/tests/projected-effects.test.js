const test = require('node:test');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { KIT: K, makeBuilder, makeSculpt, SurfaceLook, SplatEffects } = require('..').load();
const { render } = require('../cli/render');
const FX = K.splatEffects;

test('field stamps and strokes spread, drift, decay and can be sampled out of order', () => {
  const field = FX.field({
    width: 80, height: 80, cell: 0.05, origin: [-1.5, -2],
    channels: { reveal: {}, wake: { decay: 1 }, velocity: { combine: 'sum' } }
  });
  field.stroke({ keys: [[0, 0, 0], [1, 1, 0]], spacing: 0.1, radius: 0.19, values: { reveal: 1 } });
  field.stamp({ at: [0, 0], time: 0, radius: 0.16, shape: 'ring', speed: 0.8, width: 0.15, lifetime: 2,
    velocity: [0.7, 0], values: { wake: 1, velocity: -0.4 } });
  const first = field.frame(0.3), later = field.frame(0.9);
  assert(first.sample('reveal', 0.2, 0) > 0.8);
  assert.equal(first.sample('reveal', 0.9, 0), 0);
  assert(later.sample('reveal', 0.9, 0) > 0.8);
  assert(later.sample('wake', 0.63, 0.88) > 0.3);
  assert(later.sample('velocity', 0.63, 0.88) < -0.3);
  assert.equal(field.frame(2.1).sample('wake', 0.63, 0.88), 0);
  assert.deepEqual(field.frame(0.3).data('wake'), first.data('wake'));
  const before = field.revision;
  assert.throws(() => field.stroke({
    keys: [[0, 0, 0], [1, 1, 0]], radius: 0.2, values: { missing: 1 }
  }), /Unknown field channel/);
  assert.equal(field.revision, before);
  field.stamp({ at: [1, -1], values: { reveal: 1 }, radius: 0.2 });
  assert(field.frame(0.3).sample('reveal', 1, -1) > 0.85);
  assert.equal(first.sample('reveal', 1, -1), 0);
});

test('plane, cylinder and curved ribbon projections use stable surface coordinates', () => {
  const plane = SplatEffects.project({ origin: [1, 0, 1] });
  assert.deepEqual(plane([2, 9, -1]), [1, -2]);
  const cylinder = FX.project({ type: 'cylinder', radius: 2 });
  assert.deepEqual(cylinder([2, 4, 0]), [0, 4]);
  assert(Math.abs(cylinder([0, 4, -2])[0] - Math.PI) < 1e-9);
  const ribbon = FX.project({ type: 'ribbon', points: [[0, 0, 0], [2, 0, 0], [2, 0, 2]] });
  assert.deepEqual(ribbon([1, 0, 0.25]), [1, 0.25]);
  assert.deepEqual(ribbon([2.25, 0, 1]), [3, -0.25]);
  assert.deepEqual(ribbon([-0.7, 0, 0.1]), [-0.7, 0.1]);
  assert.throws(() => FX.project({ type: 'ribbon', points: [[0, 0, 0], [0, 0, 0]] }), /axes/);
});

test('projected raster frames and registered shaders compose with alpha, ink and local colors', () => {
  const prepared = SurfaceLook.prepare({ layers: {
    raster: { type: 'projected', pattern: 'raster', ink: true, outputPalette: ['#ff0000', '#00ff22'],
      raster: { width: 1, height: 1, fps: 2, repeat: true, frames: [[255, 0, 0, 255], [0, 255, 34, 255]] } },
    custom: { type: 'projected', pattern: 'fade' }
  } }, [], undefined, FX.context({
    shaders: { fade({ time, base }, out) { assert(base[0] + base[1] > 0.9); out[3] = 0; out[4] = time > 0.4 ? 0.5 : 1; } }
  }));
  const sample = { position: [0.4, 0, 0.4], normal: [0, 1, 0], view: [0, 1, 0] };
  const first = SurfaceLook.shade(prepared, { ...sample, time: 0 }, [0, 0, 0]);
  const next = SurfaceLook.shade(prepared, { ...sample, time: 0.6 }, [0, 0, 0]);
  assert.deepEqual(first.slice(0, 5), [1, 0, 0, 1, 1]);
  assert.deepEqual(next.slice(0, 5), [0, 1, 34 / 255, 0.5, 1]);
  assert.deepEqual(next[5], [[1, 0, 0], [0, 1, 34 / 255]]);
  assert.throws(() => SurfaceLook.prepare({ layers: { bad: { type: 'projected', pattern: 'unknown' } } }), /Unknown projected pattern/);
});

test('a JSON field reveals an actual surface and its local palette reaches stipple, colored and ASCII', () => {
  const spec = {
    id: 'surface-field-test', camera: { target: [0, 0, 0], dist: 4, yaw: 0.2, pitch: 1.12 },
    finish: {
      look: { pixelSize: 2, tone: 'stipple', pixel: true },
      surfaceEffects: { fields: {
        scene: { width: 32, height: 32, cell: 0.1, origin: [-1.6, -1.6], channels: { show: {} },
          stamps: [{ at: [0, 0], time: 0.5, radius: 2, values: { show: 1.6 } }] }
      } }
    },
    solids: [{ kind: 'ball', at: [0, 0, 0], r: [0.65, 0.15, 0.44], res: 0.05, mat: {
      role: 'dark', surface: { layers: {
        luminous: { type: 'projected', pattern: 'solid', field: 'scene', revealChannel: 'show',
          range: [0.1, 0.5], color: '#65f033', outputPalette: ['#65f033'], ink: true }
      } }
    } }]
  };
  assert.deepEqual(K.diorama.check(spec).filter(p => p.level === 'error'), []);
  const world = K.diorama.build(spec);
  const view = { w: 120, h: 100 };
  const black = render(world, { ...view, t: 0 });
  const on = render(world, { ...view, t: 1 });
  const styled = render(world, { ...view, t: 1, tone: false, colored: true });
  assert(black.rgb.every(v => v === 0));
  for (const image of [on, styled]) {
    assert(image.palette.includes(0x65f033));
    assert(image.use[image.palette.indexOf(0x65f033)] > 40);
    assert(image.detail.some(Boolean));
    const ascii = K.ascii.draw(image, { set: 'braille', g: 1 });
    assert(ascii.fg.some(i => image.palette[i] === 0x65f033));
    assert(ascii.text.trim().length > 0);
  }
  const bad = structuredClone(spec);
  bad.solids[0].mat.surface.layers.luminous.revealChannel = 'absent';
  assert(K.diorama.check(bad).some(entry => /Unknown field channel/.test(entry.problem)));
});

test('emission is deterministic across seeks, accepts birth positions and inherits source colors', () => {
  const B = makeBuilder(2, [0x000000, 0xffffff]);
  const emitted = FX.emitter(B, {
    source: t => ({ position: [t * 0.1, 0, 0], normal: [0, 1, 0], rgb: [0, 1, 0] }),
    rate: 30, lifetime: [0.3, 0.6], drift: [0.1, 0, 0], seed: 4
  });
  const world = B.finish({ cam: { target: [0, 0, 0], dist: 2.1, yaw: 0, pitch: 0 }, detail: 40 });
  const stage = K.stage(world);
  stage.add(emitted);
  stage.update(0, 0);
  stage.update(0.04, 0.39);
  const data = world.data.slice();
  assert(data.some((value, i) => i % 16 === 3 && value > 0.35));
  assert(data.some((value, i) => i % 16 === 7 && value === 0x00ff00));
  stage.update(0.04, 0.85);
  assert.notDeepEqual(world.data, data);
  stage.update(0.04, 0.39);
  // Hidden rows are pool storage. Compare surviving visible splats.
  const active = d => Array.from({ length: world.count }, (_, i) => Array.from(d.subarray(i * 16, i * 16 + 12)))
    .filter(row => row[3] > 0);
  assert.deepEqual(active(world.data), active(data));
  assert.equal(world.effectParticles[0].count, emitted.count);
  const img = render(world, { w: 100, h: 100, t: 0.39, raw: true });
  assert(img.detail.some(Boolean));
});

test('ASCII retains a marked isolated palette pixel between shape samples', () => {
  const picture = { w: 12, h: 16, rgb: new Uint8Array(576), palette: [0, 0x4477ff] };
  const i = 1; // outside the standard five sample points
  picture.rgb.set([68, 119, 255], i * 3);
  const options = { set: 'braille', g: 2 };
  const ordinary = K.ascii.draw(picture, options);
  const detail = new Uint8Array(192);
  detail[i] = 1;
  const projected = K.ascii.draw({ ...picture, detail }, options);
  assert.notEqual(projected.text, ordinary.text);
  assert(projected.rgb.includes(255));
});

test('the clip entry point exports animated ASCII, palette pixels and a text sidecar', () => {
  const root = path.join(__dirname, '..');
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-ascii-fx-'));
  try {
    const file = path.join(tmp, 'effect.png');
    execFileSync(process.execPath, ['cli/ink-studio.js', 'clip', 'examples/surface-effects.js',
      '--from', '0.3', '--to', '1.7', '--fps', '4', '--w', '160', '--h', '120', '--tg', '1',
      '--text', 'braille', '--out', file], { cwd: root, stdio: 'pipe' });
    assert(fs.readFileSync(file).includes(Buffer.from('acTL')));
    const frames = fs.readFileSync(path.join(tmp, 'effect.txt'), 'utf8').split('\f');
    assert.equal(frames.length, 6);
    assert(new Set(frames).size > 3);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

test('a shared field animates projected pattern coordinates and gates a normal finish', () => {
  const field = FX.field({ width: 10, height: 10, cell: 0.1, origin: [-0.5, -0.5],
    channels: { gate: {}, u: { combine: 'sum' }, v: { combine: 'sum' } } });
  field.stamp({ at: [0, 0], time: 1, radius: 5, values: { u: 0, v: 0.21, gate: 1.2 } });
  const context = FX.context({ fields: { water: field } });
  const prepared = SurfaceLook.prepare({ layers: {
    pattern: { type: 'projected', field: 'water', warpChannels: ['u', 'v'], pattern: 'stripes',
      width: 0.1, color: '#00ff00' },
    rim: { type: 'specular', color: '#ffffff', roughness: 0.1, shadow: false,
      mask: { type: 'field', field: 'water', channel: 'gate' } }
  } }, [], [0, 1, 0], context);
  const sample = { position: [0, 0, 0], normal: [0, 1, 0], view: [0, 1, 0] };
  assert.deepEqual(SurfaceLook.shade(prepared, sample, [0, 0, 0]).slice(0, 3), [0, 1, 0]);
  assert.deepEqual(SurfaceLook.shade(prepared, { ...sample, time: 1.1 }, [0, 0, 0]).slice(0, 3), [1, 1, 1]);
  // Turning off the finish light exposes the warped-off stripe on the same sample.
  assert.deepEqual(SurfaceLook.shade(prepared, { ...sample, time: 1.1, lightDirection: [1, 0, 0] },
    [0, 0, 0]).slice(0, 3).map(value => Math.round(value)), [0, 0, 0]);
});

test('a moving rigid part keeps rest-space raster paint while world projection stays fixed', () => {
  function widthForPaint(space) {
    const B = makeBuilder(2, [0, 0x242424]);
    const S = K.sculpt(makeSculpt(B));
    const rig = K.rig(B, S);
    const mat = K.surface.material({ r: [1, 1] }, { layers: {
      raster: { type: 'projected', pattern: 'raster', space, scale: 0.5, outputPalette: ['#22ffaa'],
        projection: { origin: [-0.25, 0, -0.25] }, raster: { width: 1, height: 1, frames: [[34, 255, 170, 255]] } }
    } });
    S.ball([0, 0, 0], [0.25, 0.065, 0.25], mat, { tag: 'tile', res: 0.046 });
    S.bake();
    const world = B.finish({ cam: { target: [0, 0, 0], dist: 4, pitch: 1.1, yaw: 0 }, detail: 20 });
    const stage = K.stage(world);
    rig.bind(stage);
    const view = { w: 140, h: 100, px: 1 };
    const initial = render(world, view);
    rig.set('tile', K.M.rot([0, 1, 0], 0.4), [0, 0, 0], [0.65, 0, 0.05]);
    rig.apply();
    const after = render(world, view);
    return [initial, after].map(image => image.use[image.palette.indexOf(0x22ffaa)]);
  }
  const [atRest, moved] = widthForPaint('rest');
  const [visible, unpainted] = widthForPaint('world');
  assert(atRest > 40 && moved > 40 && visible > 40);
  assert.equal(unpainted, 0);
});

test('surface sources select a named, visible material and inherit lit color', () => {
  const B = makeBuilder(2, [0, 0x222222]);
  const S = K.sculpt(makeSculpt(B));
  S.ball([0, 0, 0], 0.55, K.surface.material({ r: [1, 1] }, { name: 'rim', layers: {
    over: { type: 'projected', color: '#aabbee' }
  } }), { res: 0.05 });
  S.bake();
  const world = B.finish();
  assert.throws(() => FX.surfaceSource(world, { material: 'absent' }), /selected no splats/);
  const select = FX.surfaceSource(world, { material: 'rim', eye: [0, 0, 4], grazing: 0.5,
    lit: true, minLuma: 0.45, attempts: 100 });
  const random = K.grow.dice(13);
  const hit = select(0, 3, random);
  assert(hit && hit.luma > 0.6);
  assert.deepEqual(hit.rgb, [170 / 255, 187 / 255, 238 / 255]);
  const incidence = K.V.dot(K.V.norm(K.V.sub([0, 0, 4], hit.position)), hit.normal);
  assert(incidence > 0 && incidence < 0.5);
});

test('the browser script bundle exposes the same surface shader and field sampler', () => {
  const vm = require('node:vm');
  const source = require('..').bundle();
  const value = vm.runInNewContext(source + `
    const field = KIT.splatEffects.field({ width: 8, height: 8, origin: [-1, -1], cell: 0.25, channels: { show: {} } });
    field.stamp({ at: [0, 0], time: 1, radius: 1, values: { show: 1.5 } });
    const painted = SurfaceLook.prepare({ layers: {
      ink: { type: 'projected', color: '#00ff00', field: 'one', revealChannel: 'show' }
    } }, [], [0, 1, 0], KIT.splatEffects.context({ fields: { one: field } }));
    const hit = { position: [0, 0, 0], normal: [0, 1, 0], view: [0, 1, 0], time: 2 };
    JSON.stringify(SurfaceLook.shade(painted, hit, [0, 0, 0]).slice(0, 5));
  `);
  assert.equal(value, '[0,1,0,1,0]');
});

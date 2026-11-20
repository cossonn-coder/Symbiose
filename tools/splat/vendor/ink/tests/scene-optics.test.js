const assert = require('node:assert/strict');
const test = require('node:test');
const vm = require('node:vm');
const library = require('..');
const { KIT: K, makeBuilder, makeSculpt, SceneOptics: Optics } = library.load();
const { render } = require('../cli/render.js');

const close = (a, b, epsilon = 1e-7) => a.forEach((v, i) => assert(Math.abs(v - b[i]) < epsilon, a + ' differs from ' + b));
const identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
const mapPoint = (m, p) => [0, 1, 2].map(i => m[i] * p[0] + m[4 + i] * p[1] + m[8 + i] * p[2] + m[12 + i]);

test('a tilted reflection fixes the plane and reflects the signed distance around it', () => {
  const plane = K.reflection.plane({ id: 'mirror', at: [2, 4, 8], normal: [1, 0, 1] });
  const matrix = K.reflection.reflectedView(identity, plane);
  close(mapPoint(matrix, plane.at), plane.at);
  close(mapPoint(matrix, [3, 4, 9]), [1, 4, 7]);
  close(K.reflection.reflectedView(matrix, plane), identity);
  const capture = K.reflection.captureView(identity, plane, [3, 4, 9]);
  close(capture.view, matrix);
  close(capture.equation, [Math.SQRT1_2, 0, Math.SQRT1_2, -10 * Math.SQRT1_2]);
  assert.equal(capture.bias, plane.bias);
  assert.equal(K.reflection.captureView(identity, plane, [1, 4, 7]), null);
  assert.equal(K.reflection.captureView(identity, plane, plane.at), null);
  assert.throws(() => K.reflection.plane({ id: 'bad', normal: [0, 0, 0] }), /nonzero/);
});

test('ripple sources can be added and removed after their normal has been bound', () => {
  const field = K.ripple.field({ scale: 0.45, width: 0.6 });
  const p = [1, 0, 0], sample = t => field.sample(p, t), still = [0, 0, 0];
  const handle = field.add({ at: [0, 0, 0], start: 0.5 });
  close(sample(0.3), still);
  close(sample(0.7), still);
  assert(Math.abs(sample(1.4)[0]) > 0.1);
  close(field.sample(p, 1.4, 2), still);
  assert(field.remove(handle));
  close(sample(1.4), still);
  field.add({ at: [0, 0, 0], repeat: 3 });
  field.add({ at: [0, 0, 0] });
  assert.equal(field.prune(5, 2), 1);
  close(sample(0.9), sample(3.9));
  field.clear();
  close(field.normal.sample(p, 0.9), still);
});

function waterScene({ type = 'clear', pixel = false, select, above = true } = {}) {
  const B = makeBuilder(5, [0x11121a, 0x0d304c, 0xff4b20]);
  const S = K.sculpt(makeSculpt(B));
  S.pixel = pixel;
  const rings = K.ripple.field({ scale: 0.38, width: 0.95, amplitude: 0.55 });
  const plane = K.reflection.plane({ id: 'pool', select });
  const wet = K.surface.material({ r: [1], em: true, a: type === 'clear' ? 0.55 : 1 }, { normal: rings.normal });
  S.box([0, -0.035, 0], [1.8, 0.035, 1.5], K.reflection.material(wet, 'pool', {
    f0: 1, distortion: 45
  }), { res: 0.1, ghost: type === 'clear' });
  S.box([0.3, above ? 0.45 : -0.45, -0.6], [0.12, 0.4, 0.12], { r: [2], em: true }, { res: 0.09 });
  S.bake();
  const w = B.finish({ cam: { target: [0, 0, 0], dist: 5.6, yaw: 0, pitch: 0.65 },
    detail: 20, radius: 3, dither: 0, look: { pixel }, reflections: [plane] });
  return { w, rings };
}

const camera = { w: 100, h: 92, px: 1, ortho: true, samples: true };
function changed(a, b) {
  let count = 0;
  for (let i = 0; i < a.length; i += 3) {
    if (Math.abs(a[i] - b[i]) + Math.abs(a[i + 1] - b[i + 1]) + Math.abs(a[i + 2] - b[i + 2]) > 16) count++;
  }
  return count;
}

test('the scene reflects into translucent splats and opaque per-pixel receivers', () => {
  for (const [type, pixel] of [['clear', false], ['solid', true]]) {
    const { w, rings } = waterScene({ type, pixel });
    const enabled = render(w, camera), disabled = render(w, { ...camera, reflections: false });
    assert(changed(enabled.color, disabled.color) > 12, type);
    assert.deepEqual(render(w, { ...camera, t: 0.85 }).color, enabled.color);
    rings.add({ at: [0.3, 0, 0.3], start: 0.25 });
    assert(changed(render(w, { ...camera, t: 0.85 }).color, enabled.color) > 15, type);
    assert.deepEqual(render(w, { ...camera, t: 0.85, reflections: false }).color, disabled.color);
  }
});

test('planes clip source geometry and can further filter what gets reflected', () => {
  for (const options of [{ above: false }, { select: () => false }]) {
    const { w } = waterScene(options);
    assert.deepEqual(render(w, camera).color, render(w, { ...camera, reflections: false }).color);
  }
  const { w } = waterScene();
  const underside = { ...camera, pitch: -0.6 };
  assert.deepEqual(render(w, underside).color, render(w, { ...underside, reflections: false }).color);
});

test('overlapping volumes are depth ordered and stop at the supplied distance', () => {
  const volumes = K.atmosphere.prepare([
    K.atmosphere.sphere({ at: [0, 0, 0], radius: 2, density: 0.4, color: '#bf8245' }),
    K.atmosphere.box({ min: [-1, -1, -1], max: [1, 1, 1], density: 0.7, color: '#1536ac' }),
    K.atmosphere.shaft({ from: [0, -1, 0], to: [0, 1, 0], radius: 0.6, color: '#eddca3' })
  ]);
  const origin = [0, 0, 5], direction = [0, 0, -1];
  close(K.atmosphere.trace(volumes, origin, direction, 2.8), [0, 0, 0, 1]);
  const partial = K.atmosphere.trace(volumes, origin, direction, 3.5);
  assert(Math.abs(partial[3] - Math.exp(-0.2)) < 1e-7);
  const all = K.atmosphere.trace(volumes, origin, direction, 10);
  close(all, K.atmosphere.trace(volumes.slice().reverse(), origin, direction, 10));
  assert(all[3] < partial[3]);
  const fog = K.atmosphere.prepare([K.atmosphere.fog({ top: 0, density: 1, near: 1, far: 3 })]);
  assert.equal(K.atmosphere.trace(fog, [0, 1, 5], direction, 10)[3], 1);
  assert(Math.abs(K.atmosphere.trace(fog, [0, -1, 5], direction, 10)[3] - Math.exp(-2)) < 1e-7);
  assert.throws(() => K.atmosphere.shaft({ from: origin, to: origin, radius: 1 }), /nonzero/);
});

test('the renderer shows local mist in open space and stops it at opaque surfaces', () => {
  const B = makeBuilder(7, [0, 0x4b4b4b]);
  const S = makeSculpt(B);
  S.box([0, 0, 0.85], [0.48, 0.5, 0.13], { r: [1], em: true }, { res: 0.075 });
  S.bake();
  const w = B.finish({
    cam: { target: [0, 0, 0], dist: 5, pitch: 0, yaw: 0 },
    detail: 20, dither: 0, radius: 4,
    atmosphere: [K.atmosphere.sphere({ at: [0, 0, -0.5], radius: 1.22, density: 2, color: '#ffffff' })]
  });
  const hazy = render(w, camera), clear = render(w, { ...camera, atmosphere: false });
  const center = (Math.floor(hazy.h / 2) * hazy.w + Math.floor(hazy.w / 2)) * 3;
  assert.equal(hazy.color[center], clear.color[center]);
  assert(changed(hazy.color, clear.color) > 200);
});

test('analytic and grid fields can move through the mesh and splat APIs', () => {
  const sd = (x, y, z) => Math.hypot(x, y, z) - 0.9;
  const bounds = { min: [-1.1, -1.1, -1.1], max: [1.1, 1.1, 1.1] };
  const mesh = K.sdf.toMesh(sd, { bounds, resolution: 0.18, color: [0.2, 0.5, 0.8] });
  assert.equal(K.mesh.info(mesh).open, 0);
  assert.deepEqual(mesh.mats[0].rgb, [0.2, 0.5, 0.8]);
  const field = K.mesh.field(mesh, { cells: 16, thick: 0 });
  assert(field.sd(0, 0, 0) < -0.65);
  assert.equal(K.mesh.info(K.sdf.toMesh(field)).open, 0);
  const w = K.sdf.toSplats(sd, { bounds, resolution: 0.18, res: 0.13, seed: 11 });
  assert(w.count > 200);
  assert(render(w, camera).color.some(v => v > 90));
  const B = makeBuilder(5), S = makeSculpt(B);
  assert.equal(K.sdf.solid(S, sd, [1, 2, 3], { bounds }).sd(0, 0, 0), -0.9);
  assert.throws(() => K.sdf.toMesh(() => 1, { bounds }), /zero surface/);
});

test('bundle hosts receive the reflection, ripple, volume and mesh tools', () => {
  assert.equal(vm.runInNewContext(library.bundle() + `
    [KIT.reflection.plane, KIT.ripple.field, KIT.atmosphere.trace, KIT.sdf.toMesh, SceneOptics.reflectedView]
      .every(x => typeof x === 'function')
  `), true);
  assert.equal(Optics.plane, K.reflection.plane);
});

test('packed ripple frames agree with surface normals on tilted planes and respect source times', () => {
  const ripple = K.ripple.field({ axis: 'z', cross: [1, 1, 0], capacity: 3, scale: .42 });
  const a = ripple.add({ at: [1, 2, 3], start: .2, repeat: 2.5, strength: 1.2 });
  ripple.add({ at: [.2, .5, .3], start: 1 });
  ripple.add({ at: [0, 0, 0], start: 5 });
  const point = [1.4, 2.3, 3.1], storage = new Float32Array(12), out = [0, 0, 0];
  for (const time of [0, .2, .48, 1.8, 3.1, 5.1]) {
    const frame = ripple.frame(time, storage);
    assert.equal(frame.drops, storage);
    for (const footprint of [0, .23, .5]) {
      assert.equal(K.ripple.sampleFrame(frame, point, footprint, out), out);
      close(out, ripple.sample(point, time, footprint), 1e-6);
    }
  }
  assert.equal(ripple.frame(.2, storage).count, 0);
  assert.equal(ripple.frame(.48, storage).count, 1);
  assert.throws(() => ripple.frame(.48, new Float32Array(0)), /storage/);
  assert.throws(() => ripple.add({ at: [0, 0, 0] }), /up to 3/);
  ripple.remove(a);
  assert.equal(ripple.frame(.48, storage).count, 0);
});

const assert = require('node:assert/strict');
const test = require('node:test');
const vm = require('node:vm');
const Surface = require('../src/surface-look.js');
const studio = require('..').load();
const { render } = require('../cli/render.js');
const gallery = require('../examples/surface-gallery.js');

const { KIT, makeBuilder, makeSculpt } = studio;
const base = [0.13, 0.17, 0.21];
const front = { position: [0.5, 0.5, 0.5], normal: [0, 0, 1], view: [0, 0, 1] };
const neutralSun = [0, 0, 1];
const prepare = settings => Surface.prepare(settings, [], neutralSun);

test('directional roughness turns the reflection when the tangent rotates', () => {
  const finish = direction => prepare({ direction, layers: { brush: { type: 'specular', roughness: [0.11, 0.58] } } });
  const x = { ...front, view: [0.48, 0, 0.877] };
  const y = { ...front, view: [0, 0.48, 0.877] };
  const alongX = finish('x'), alongY = finish('y');
  assert(Surface.shade(alongX, x, base)[0] + 0.5 < Surface.shade(alongX, y, base)[0]);
  assert(Surface.shade(alongY, y, base)[0] + 0.5 < Surface.shade(alongY, x, base)[0]);
  assert.deepEqual(Surface.shade(alongX, { ...x, visibility: 0 }, base).slice(0, 3), base);
});

test('grazing reflection, coverage and thin-film colour respond independently to the view', () => {
  const grazing = { ...front, view: [0.96, 0, 0.28] };
  const reflection = prepare({
    opacity: { facing: 0.15, grazing: 1, power: 2 },
    layers: { reflect: { type: 'reflection', f0: 0 } }
  });
  const a = Surface.shade(reflection, front, base), b = Surface.shade(reflection, grazing, base);
  assert.equal(a[3], 0.15);
  assert(b[3] > a[3] + 0.4);
  assert(b[2] > a[2]);
  const film = prepare({ layers: { tint: { type: 'film', thickness: 580, f0: 1 } } });
  assert.notDeepEqual(Surface.shade(film, front, base).slice(0, 3), Surface.shade(film, grazing, base).slice(0, 3));
});

test('ripple fronts move from fixed sources and only affect samples they pass', () => {
  const water = Surface.prepare({
    direction: 'x',
    normal: { type: 'rings', amplitude: 0.55, speed: 1, scale: 0.45, width: 0.6, drops: [{ at: [0, 0, 0], start: 0.5 }] },
    layers: { highlight: { type: 'specular', roughness: 0.12 } }
  }, [], [0, 1, 0]);
  const sample = { position: [1.0, 0, 0], normal: [0, 1, 0], view: [0, 1, 0] };
  const still = Surface.shade(water, { ...sample, time: 0.3 }, base);
  assert.deepEqual(Surface.shade(water, { ...sample, time: 0.7 }, base), still);
  assert.notDeepEqual(Surface.shade(water, { ...sample, time: 1.40 }, base), still);
  assert.deepEqual(Surface.shade(water, { ...sample, time: 2.4 }, base), still);
});

test('glints stay anchored, respond to the angle, and fade once they are subpixel', () => {
  const shader = prepare({
    seed: 7, layers: { flakes: { type: 'glints', scale: 1, density: 1, tilt: 0, roughness: 0.08 } }
  });
  const on = Surface.shade(shader, front, base);
  assert(on[4] > 0.9);
  assert.deepEqual(on, Surface.shade(shader, front, base));
  assert(Surface.shade(shader, { ...front, view: [0.5, 0.3, 0.8] }, base)[4] < 0.01);
  assert(Surface.shade(shader, { ...front, position: [0.01, 0.01, 0.01] }, base)[4] === 0);
  assert(Surface.shade(shader, { ...front, footprint: 4 }, base)[4] < 0.08);
});

test('all 40 presets compile and have a usable response across a surface-angle sweep', () => {
  const names = gallery.groups.flatMap(group => group.swatches.map(([name]) => name));
  assert.equal(new Set(names).size, 40);
  assert.deepEqual(KIT.surface.presets.slice().sort(), names.slice().sort());
  for (const name of names) {
    const mat = KIT.surface.preset(name, { r: [1, 2] });
    const shader = prepare(mat.surface);
    let effect = 0;
    for (let row = 0; row < 9; row++) for (let col = 0; col < 14; col++) {
      const a = col * 0.49, e = row * 0.17;
      const sample = {
        ...front,
        position: [0.09 + row * 0.117, 0.24 + col * 0.129, 0.61 - row * 0.065],
        view: [Math.cos(a) * Math.sin(e), Math.sin(a) * Math.sin(e), Math.cos(e)]
      };
      const result = Surface.shade(shader, sample, base);
      assert(result.every(value => Number.isFinite(value) && value >= 0 && value <= 1), name);
      effect = Math.max(effect, ...base.map((value, i) => Math.abs(value - result[i])));
    }
    assert(effect > 0.06, name + ' should visibly shade at least one sample');
  }
});

test('presets extend an existing material, disable named layers, and isolate overrides', () => {
  const existing = KIT.surface.material({ r: [2, 3], a: 0.8 }, { layers: { polish: { type: 'sheen', strength: 0.2 } } });
  const custom = KIT.surface.preset('brushed-steel', existing, { direction: 'z', layers: { brush: { roughness: [0.22, 0.37] }, polish: false } });
  assert.equal(custom.a, 0.8);
  assert.deepEqual(custom.r, [2, 3]);
  assert.equal(custom.surface.layers.brush.type, 'specular');
  assert.equal(custom.surface.layers.polish, false);
  assert.equal(prepare(custom.surface).layers.length, 1);
  assert.equal(existing.surface.layers.polish.strength, 0.2);
  assert.deepEqual(KIT.surface.preset('brushed-steel').surface.layers.brush.roughness, [0.09, 0.58]);
  assert.throws(() => KIT.surface.preset('missing'), RangeError);
});

function makeWorld(coloredBase, addCoat) {
  const B = makeBuilder(17, [0x0c0f1a, 0x2d2633, 0x6a3845, 0xb46768, 0x7fbbe3, 0xeff9fc]);
  const S = KIT.sculpt(makeSculpt(B));
  S.pixel = true;
  S.sun = [0.06, 0.41, 0.91];
  if (coloredBase) {
    S.ball([0, 0, 0], 0.9, KIT.surface.preset('brushed-steel', { r: [1, 2, 3] }, {
      layers: { brush: { color: 5, roughness: [0.18, 0.66] } }
    }));
  } else {
    S.box([0, 0, -0.41], [1, 1, 0.08], { r: [2, 3] }, { res: 0.09 });
  }
  if (addCoat) {
    const layer = KIT.surface.material({ r: [1], a: 0.42 }, {
      layers: { clear: { type: 'reflection', f0: 1, sky: 4, ground: 4, horizon: 4 } }
    });
    S.box([0, 0, 0.36], [0.75, 0.75, 0.012], layer, { res: 0.11 });
  }
  S.bake();
  return B.finish({
    cam: { target: [0, 0, 0], dist: 4.5, yaw: 0, pitch: 0.19 },
    detail: 20, radius: 3, dither: 0, look: { pixel: true }
  });
}

test('the normal render path shades splats after bake, with an opt-out and the scene palette', () => {
  const plain = makeWorld(false, false), world = makeWorld(true, false);
  assert.equal(plain.surfaceData, undefined);
  assert.equal(world.surfaceData.length, Surface.STRIDE * world.count);
  assert.equal(world.surfaces.length, 1);
  const view = { w: 96, h: 80 };
  const a = render(world, view);
  const b = render(world, { ...view, surface: false });
  const c = render(world, { ...view, yaw: 0.65 });
  assert.notDeepEqual(a.rgb, b.rgb);
  assert.notDeepEqual(a.rgb, c.rgb);
  const palette = new Set(world.pal);
  for (let i = 0; i < a.rgb.length; i += 3) {
    const color = (a.rgb[i] << 16) | (a.rgb[i + 1] << 8) | a.rgb[i + 2];
    assert(palette.has(color));
  }
});

test('a translucent finish composites over existing per-pixel materials', () => {
  const world = makeWorld(false, true), view = { w: 100, h: 92, ortho: true };
  const mixed = render(world, view), unshaded = render(world, { ...view, surface: false });
  const center = ((mixed.h >> 1) * mixed.w + (mixed.w >> 1)) * 3;
  assert(mixed.rgb[center + 2] > unshaded.rgb[center + 2] + 40);
  assert.notDeepEqual(mixed.rgb, render(makeWorld(false, false), view).rgb);
});

test('JSON scenes resolve preset IDs and report a bad layer at its material path', () => {
  const spec = {
    id: 'test-surface', finish: { look: { pixel: true } },
    solids: [{ kind: 'ball', at: [0, 1, 0], r: 0.7, mat: { role: 'metal', surface: 'brushed-steel' } }]
  };
  const world = KIT.diorama.build(spec);
  assert(world.pix.length > 0);
  assert.equal(world.surfaces[0].settings.layers.brush.type, 'specular');
  spec.solids[0].mat.surface = {
    preset: 'brushed-steel', layers: { brush: { roughness: [0.14, 0.47] }, rim: { type: 'sheen', color: '#eceade' } }
  };
  assert.equal(KIT.diorama.build(spec).surfaces[0].settings.layers.brush.roughness[0], 0.14);
  spec.solids[0].mat.surface.layers.rim.mask = { type: 'missing' };
  const issue = KIT.diorama.check(spec).find(item => item.level === 'error' && item.path === 'solids[0].mat.surface');
  assert.match(issue.problem, /Unknown surface mask/);
});

test('the plain script bundle exposes the same sampler and presets to hosts', () => {
  const script = require('..').bundle() + `
    const mat = KIT.surface.preset('brushed-steel', [1, 2]);
    const prepared = SurfaceLook.prepare(mat.surface, [], [0, 0, 1]);
    SurfaceLook.shade(prepared, { position: [0, 0, 0], normal: [0, 0, 1], view: [0, 0, 1] }, [0, 0, 0])[0];
  `;
  assert(vm.runInNewContext(script) > 0.8);
});

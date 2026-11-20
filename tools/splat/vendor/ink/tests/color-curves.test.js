const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT, ColorCurves, PixelLook, SurfaceLook, makeBuilder, makeSculpt } = require('..').load();
const { render } = require('../cli/render.js');

test('scalar and RGB ramps support clamped physical units and exact authored stops', () => {
  const stops = [[-20, 0], [20, 1], [40, .2]];
  const linear = ColorCurves.scalar({ stops });
  const smooth = ColorCurves.scalar({ stops, interpolation: 'smooth' });
  const stepped = ColorCurves.scalar({ stops, interpolation: 'step' });
  assert.deepEqual([-200, -20, -10, 20, 21, 40, 57].map(stepped), [0, 0, 0, 1, 1, .2, .2]);
  assert.equal(linear(-10), .25);
  assert.equal(smooth(-10), .15625);
  assert.throws(() => linear(Infinity), /finite/);
  assert.throws(() => ColorCurves.scalar({ stops: [[0, 1], [0, 2]] }), /strictly increasing/);
  assert.throws(() => ColorCurves.ramp({ stops: [[0, '#000'], [1, '#ffffff']] }), /Ramp colors/);
  assert.throws(() => ColorCurves.prepare({ channels: { green: { stops: [[0, 0], [1, 2]] } } }), /outputs/);

  const ramp = ColorCurves.ramp({ stops: [[20, '#000000'], [80, '#ff8000']] });
  const out = new Float32Array(3);
  assert.equal(ramp(50, out), out);
  assert.deepEqual(Array.from(out), [.5, Math.fround(64 / 255), 0]);
  const { materials } = KIT.procedural;
  assert.equal(materials.colorCurves, ColorCurves);
  const perceptual = materials.ramp(['#112233', '#c0ffee'], { interpolation: 'step', steps: 3 });
  assert.deepEqual(perceptual.hex, [0x112233, 0x112233, 0xc0ffee]);
  const even = materials.ramp(['#112233', '#c0ffee']);
  const eased = materials.ramp(['#112233', '#c0ffee'], { interpolation: 'smooth' });
  assert.deepEqual(eased.sample(.25), even.sample(.15625));
});

test('scene channel curves compose with a luminance ramp and preserve protected remaps', () => {
  const palette = [0, 0x4488cc, 0xaaaaaa, 0xffffff];
  const channels = {
    red: { stops: [[0, 1], [1, 0]] },
    blue: { stops: [[0, 0], [1, .5]] }
  };
  assert.deepEqual(ColorCurves.prepare({ channels })([.25, .75, .5]), [.75, .75, .25]);
  const curve = { ramp: { stops: [[0, '#000000'], [.5, '#cccccc'], [1, '#ffffff']], interpolation: 'step' }, channels };
  const remap = { rules: [{ from: 1, to: '#00ffff' }], protect: [0, 3] };
  assert.deepEqual(PixelLook.gradePalette(PixelLook.colorGrade(palette, {}, null, remap, curve)),
    [0, 0x00ffff, 0x33cc66, 0xffffff]);
  const spec = { id: 'curves-check', solids: [], finish: { look: { colorCurves: { channels: { alpha: {} } } } } };
  assert.equal(KIT.diorama.check(spec).find(row => row.path === 'finish.look.colorCurves')?.level, 'error');
});

test('surface curves sample world-space query properties and keep missing values distinct from zero', () => {
  const source = { field: 'river/water', path: ['depth'] };
  const layer = { type: 'colorCurve', source, ramp: { stops: [[0, '#005000'], [2, '#00f000']] } };
  const sample = { position: [-7, 0, 0], worldPosition: [1, 0, 0], normal: [0, 1, 0], view: [0, 1, 0] };
  const query = { probe(name, p) {
    assert.equal(name, 'river/water');
    assert.equal(p, sample.worldPosition);
    return p[0] < 0 ? { status: 'dry' } : { status: 'ok', value: { depth: p[0] } };
  } };
  const prepare = value => SurfaceLook.prepare({ layers: { tint: value } }, [], undefined, { query });
  const base = [.8, .2, .5], withQuery = prepare(layer);
  const read = (compiled, site = sample) => SurfaceLook.shade(compiled, site, base).slice(0, 3);
  assert.deepEqual(read(withQuery), [0, 160 / 255, 0]);
  sample.worldPosition[0] = 0;
  assert.deepEqual(read(withQuery), [0, 80 / 255, 0]);
  sample.worldPosition[0] = -1;
  assert.deepEqual(read(withQuery), base);
  assert.deepEqual(read(prepare({ ...layer, source: { ...source, fallback: 0 } })), [0, 80 / 255, 0]);
  const depth = SurfaceLook.prepare({ layers: { tint: { ...layer, source: 'depth' } } });
  assert.equal(depth.depth, true);
  assert.deepEqual(read(depth, { ...sample, depth: 2 }), [0, 240 / 255, 0]);
});

test('projected field channel curves follow the sampled frame and keep their local palette', () => {
  const field = { channels: ['wet'], revision: 1, frame: time => ({ sample: () => time }) };
  const material = SurfaceLook.prepare({ layers: { glaze: {
    type: 'colorCurve', source: { field: 'glaze', channel: 'wet' },
    ramp: { stops: [[0, '#112233'], [1, '#bbccdd']], interpolation: 'step' },
    outputPalette: ['#112233', '#bbccdd']
  } } }, [], undefined, { fields: { glaze: field } });
  const sample = { position: [0, 0, 0], normal: [0, 1, 0], view: [0, 1, 0] };
  for (const [time, color] of [[0, 0x112233], [1, 0xbbccdd], [.5, 0x112233]]) {
    const shade = SurfaceLook.shade(material, { ...sample, time }, [0, 0, 0]);
    assert.equal(PixelLook.gradePalette(shade.slice(0, 3))[0], color);
    assert.deepEqual(shade[5].map(rgb => PixelLook.gradePalette(rgb)[0]), [0x112233, 0xbbccdd]);
  }
});

test('simulation visual samples its tick and headless rendering can bypass the curves', () => {
  const W = KIT.world;
  const tint = {
    type: 'colorCurve', source: { field: 'climate/moisture' },
    ramp: { stops: [[0, '#442011'], [1, '#65b5ff']] },
    outputPalette: ['#442011', '#65b5ff']
  };
  const bounds = { min: [-1.1, -.3, -1], max: [1.1, .8, 1] };
  const run = W.runtime.create({
    systems: { climate: { kind: 'fields', config: { fields: { moisture: { default: 0 } } } } },
    visual: { bounds, resolution: .12, terrainSurface: { layers: { tint } }, look: { pixelSize: 2 } },
    commands: [{ tick: 1, action: 'climate/set', args: { field: 'moisture', region: { bounds, value: 1 } } }]
  });
  const images = [];
  for (const tick of [0, 1]) {
    run.advance(tick);
    const world = W.visual({ makeBuilder, makeSculpt }, run.view(), run.query());
    images.push(render(world, { w: 112, h: 96 }));
    assert.equal(render(world, { w: 112, h: 96, colorCurves: false }).palette, undefined);
  }
  assert(images[0].use[images[0].palette.indexOf(0x442011)] > 0);
  assert(images[1].use[images[1].palette.indexOf(0x65b5ff)] > 0);
  assert.notDeepEqual(images[0].rgb, images[1].rgb);
});

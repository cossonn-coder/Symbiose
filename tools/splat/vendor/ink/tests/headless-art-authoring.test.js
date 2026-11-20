const assert = require('node:assert/strict');
const test = require('node:test');
const studio = require('../index.js');
const { KIT: K, makeBuilder } = studio.load(), P = K.procedural;

test('weighted mesh paths prefer a seam and expose distances from stable sources', () => {
  const mesh = { points: [[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1], [3, 3, 3]],
    faces: [[0, 1, 2], [0, 2, 3]] };
  const route = P.geometry.meshPaths(mesh, { sources: [0], edgeCost: e => e.a === 0 && e.b === 2 ? Infinity : e.length });
  assert.deepEqual(route.path(2).indices, [0, 1, 2]);
  assert.equal(route.distances[2], 2);
  assert.equal(route.distanceAt([.5, 0, .5]), 1);
  assert.equal(route.path(4), null);
  assert.deepEqual(route.curves([4, 2]).map(c => c.cost), [2]);
});

test('attribute sampling interpolates numbers but preserves labels through multiple domains', () => {
  const mesh = { points: [[0, 0, 0], [1, 0, 0], [0, 0, 1]], faces: [[0, 1, 2]] };
  const source = P.attributes.mesh(mesh, {
    vertex: { wetness: { type: 'number', values: [0, 1, 0] }, id: { values: ['a', 'b', 'c'] } },
    face: { surface: { values: ['roof'] } }
  });
  const result = source.sample([.75, 1, .12]);
  assert(Math.abs(result.values.wetness - .75) < 1e-6);
  assert.equal(result.values.id, 'b');
  assert.equal(result.values.surface, 'roof');
  assert.deepEqual(P.attributes.transfer(source, 'instance', [{ id: 'grass', point: [.75, 0, .12] }])[0].attributes, result.values);
  const sdf = P.attributes.sdf((x, y, z) => Math.hypot(x, y, z) - 1, (at, normal) => ({ wetness: at[1], normal }));
  assert.deepEqual(sdf.sample([0, 1.2, 0]).values.normal, [0, 1, 0]);
  const carrier = P.surface.plane({ id: 'ledge', origin: [0, 0, 0], u: [1, 0, 0], v: [0, 0, 1] });
  assert.equal(P.attributes.carrier(carrier, () => ({ moss: true })).sample([.2, .4, .3]).values.moss, true);
});

test('headless groups expose inputs, keyframe parameters, and keep stable preview results', () => {
  const operations = { scale: { inputs: { n: 'number', factor: 'number' }, outputs: { value: 'number', label: 'string' },
    run({ n, factor }) { return { value: n * factor, label: 'scaled' }; } } };
  const spec = {
    inputs: { level: { type: 'number', default: 2 } },
    nodes: { animated: { op: 'scale', inputs: { n: { input: 'level' },
      factor: { keys: [{ time: 0, value: 1, ease: 'linear' }, { time: 1, value: 3 }] } } } },
    outputs: { value: { node: 'animated' }, status: { node: 'animated', port: 'label' } }
  };
  const group = P.graph.group(spec, { operations, outputs: { value: 'number', status: 'string' } });
  const parent = P.graph.create({ nodes: { a: { op: 'reusable', params: { level: 4 } } }, outputs: { out: { node: 'a' } } },
    { groups: { reusable: group } });
  const first = parent.evaluate({}, { time: .5 });
  assert.deepEqual(first.outputs, { out: 8 });
  assert.equal(parent.evaluate({}, { time: .5 }).status.a, 'cached');
  assert.equal(parent.evaluate({}, { time: 1 }).outputs.out, 12);
  assert.equal(first.preview('a'), 8);
  assert.equal(first.preview('a/animated'), 8);
  assert.throws(() => P.graph.create({
    nodes: { a: { op: 'scale', inputs: { n: { node: 'a' }, factor: 2 } } }, outputs: {}
  }, { operations }), /cycle/);
});

test('repeat, stable per-element seeding and cached fixed-step simulation work out of order', () => {
  const G = P.graph;
  assert.equal(G.repeat(1, 4, value => value * 2), 16);
  const ids = [{ id: 'b' }, { id: 'c' }], inspect = (_, info) => info.seed;
  assert.equal(G.each(ids, inspect)[0], G.each(ids.slice().reverse(), inspect)[1]);
  const sim = G.simulation({ initial: { frost: 0 }, dt: .1, checkpoint: 2,
    step(value, { inputs }) { value.frost += inputs; return value; } });
  assert.equal(sim.sample(.7, { inputs: 2 }).state.frost, 14);
  assert.equal(sim.sample(.4, { inputs: 2 }).steps, 0);
  assert.equal(sim.sample(.7, { inputs: 3, version: 1 }).state.frost, 21);
});

test('generic raster tags, multi-output material and field-driven tiles', () => {
  const png = P.graph.raster({ width: 1, height: 1, fps: 2, layers: {
    base: { frames: [[10, 20, 30, 255]] }, top: { frames: [[200, 0, 0, 0], [200, 0, 0, 128]] }
  }, tags: { active: { start: 1, end: 2 } } });
  assert.deepEqual(Array.from(png.layer('top', 0, 'active').data), [200, 0, 0, 128]);
  assert.deepEqual(Array.from(png.composite(0, { tag: 'active' }).data), [105, 10, 15, 255]);
  const art = P.graph.material({ height: u => u, palette: 'copper', wetness: .4, ink: .63 }).sample(.3, .2);
  assert.equal(art.palette, 'copper');
  assert(Math.abs(art.normal[0] + Math.SQRT1_2) < 1e-9);
  const tileSpec = { bounds: { min: [-2, -2], max: [2, 2] }, seed: 5,
    mask: u => Number(u > 0), vector: () => [0, 2], scale: (u, v) => 1 + u * .2 };
  const tiles = P.graph.tiles(tileSpec);
  assert.equal(tiles.length, 8);
  assert(tiles.every(t => t.point[0] > 0 && t.rotation === Math.PI / 2 && t.scale > 1));
  assert.deepEqual(tiles, P.graph.tiles(tileSpec));
});

test('state inputs, animation timing, triggers, transition blending and cues', () => {
  const clip = (start, end, cue) => ({ schema: { heat: 'number' }, keys: [
    { time: 0, value: { heat: start }, ease: 'linear' }, { time: 1, value: { heat: end } }
  ], cues: [{ time: .25, name: cue }] });
  const machine = K.anim.stateGraph.create({
    initial: 'idle', input: { fuel: 1 }, triggers: ['start'],
    states: { idle: clip(0, 0, 'idling'), ignite: clip(.5, 1, 'spark'), extinguish: clip(.3, 0, 'smoke') },
    transitions: [{ from: 'idle', to: 'ignite', trigger: 'start', blend: .5 },
      { from: 'ignite', to: 'extinguish', when: [{ property: 'fuel', op: 'lt', value: .2 }] }]
  }).instantiate();
  machine.trigger('start');
  assert.equal(machine.advance(.1).values.heat, 0);
  const live = machine.advance(.36);
  assert.equal(live.state, 'ignite');
  assert(live.values.heat > 0 && live.values.heat < .63);
  assert.deepEqual(live.events.map(e => e.name), ['spark']);
  assert.equal(machine.advance(.6, { fuel: 0 }).state, 'extinguish');
});

test('shrine regeneration keeps pins, overrides and stable candidate IDs', () => {
  const site = P.floodedShrine.create({ seed: 19 });
  const original = site.document.entities().find(entity => entity.type === 'wall');
  site.pin('entrance', [.37, .08, 2.7]);
  site.document.update(original.id, { parameters: { wear: .99 } });
  site.setControls({ age: .9, waterline: .4 });
  site.regenerate(91);
  assert.equal(site.document.get(original.id).parameters.wear, .99);
  assert.deepEqual(site.describe().anchors[0].point, [.37, .08, 2.7]);
  assert.equal(site.describe().controls.layoutSeed, 91);
  assert.equal(site.describe().controls.waterline, .4);
  const restored = P.floodedShrine.create({ snapshot: site.document.serialize() });
  assert.deepEqual(restored.describe(), site.describe());
});

test('atlas exports eight registered directions and aligned relighting maps', () => {
  const b = makeBuilder(8, [0x202030, 0xffb090]);
  b.disc(0, 0, 0, [0, 0, 1], .29, .03, b.P[1], 3, { em: true });
  const world = b.finish({ cam: { target: [0, 0, 0], yaw: 0, pitch: 0, dist: 4 } });
  const atlas = studio.spriteAtlas(world, { width: 24, height: 20, times: [0, .2], maps: ['depth', 'normal', 'emission'] });
  assert.equal(atlas.metadata.frames.length, 16);
  assert(atlas.metadata.frames.every(frame => frame.pivot.x === 12 && frame.pivot.y === 10));
  assert.equal(atlas.images.color[3], 0);
  for (const name of ['color', 'depth', 'normal', 'emission']) {
    assert.equal(atlas.images[name].length, atlas.metadata.width * atlas.metadata.height * 4);
    assert(atlas.images[name].some((value, index) => index % 4 === 3 && value > 0));
  }
});

test('built-in graph operators and generic PNG manifests work through public entry points', () => {
  const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-raster-'));
  try {
    const png = require('../cli/png.js');
    fs.writeFileSync(path.join(folder, 'mark.png'), png.encode(1, 1, new Uint8Array([45, 85, 125, 230]), 4));
    const manifest = path.join(folder, 'mark.json');
    fs.writeFileSync(manifest, JSON.stringify({ width: 1, height: 1, layers: { mark: { frames: ['mark.png'] } } }));
    const asset = studio.readRasterAsset(manifest);
    const graph = P.graph.create({
      inputs: { asset: 'any' },
      nodes: { tile: { op: 'rasterLayer', inputs: { source: { input: 'asset' }, layer: 'mark' } } },
      outputs: { image: { node: 'tile' } }
    });
    assert.deepEqual(Array.from(graph.evaluate({ asset }).outputs.image.data), [45, 85, 125, 230]);
  } finally {
    fs.rmSync(folder, { recursive: true });
  }
});

const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const example = require('../examples/biome-recipes');
const { biomeRecipes } = KIT.procedural;

test('alpine slope, tidal marsh, kelp bed and flooded cave exercise one recipe model', () => {
  const { view } = example(KIT);
  const world = view();
  const cases = [
    [[-10, 6, 3], 'alpine', 'air', 'ridge', 'walk', 'ridge-wind', 'lichen'],
    [[-3, 0.5, 3], 'marsh', 'air', 'tidal-flat', 'wade', 'reed-rustle', 'reed'],
    [[3, -2, 3], 'kelp-bed', 'water', 'shelf', 'swim', 'inlet-flow', 'kelp'],
    [[3, -9, 3], 'flooded-cave', 'water', 'chamber', 'low-visibility', 'cave-reverb', 'glow-moss']
  ];
  for (const [point, biome, medium, landform, tag, cue, species] of cases) {
    const result = world.inspect(...point);
    assert.equal(result.biome, biome);
    assert.equal(result.medium.kind, medium);
    assert.equal(result.landform.kind, landform);
    assert(result.traversal.includes(tag));
    assert(result.ambient.some(row => row.id === cue && row.gain > 0));
    assert(result.populations.some(row => row.species === species && row.density > 0));
  }
  const marsh = world.inspect(-3, 0.5, 3);
  assert.deepEqual(marsh.base.weights, [{ id: 'marsh', weight: 0.85 }, { id: 'alpine', weight: 0.15000000000000002 }]);
  assert(marsh.base.regions[0].checks.some(row => row.field === 'moisture' && row.value === 0.86 && row.weight === 1));
  const strata = world.appearanceAt(-10, 5, 3, { surfaceY: 6 });
  assert.equal(strata.stratum.material, 'slate');
  assert.deepEqual(strata.ramp, [KIT.procedural.styles.rgb('#272f3e'), KIT.procedural.styles.rgb('#5d6877')]);
  const turbid = world.inspect(7, -2, 3, { species: 'kelp' });
  assert.equal(turbid.biome, 'kelp-bed');
  assert.equal(turbid.populations[0].density, 0);
  assert(turbid.populations[0].checks.some(row => row.field === 'clarity' && row.value === 0.24 && row.weight === 0));
  const tooDeep = world.inspect(3, -3.75, 3, { species: 'kelp' });
  assert(tooDeep.populations[0].checks.some(row => row.field === 'depth' && row.weight === 0));
});

test('ordered biome and population paint blends, erases, and respects vertical bands', () => {
  const scene = example(KIT), initial = scene.view();
  const xy = [3, -2, 3], below = [3, -9, 3];
  const shape = { points: [[2.5, 3], [3.5, 3]], width: 1, softness: 0.2, height: [-3, -1] };
  scene.paint({ ...shape, id: 'mix', channel: 'biome', target: 'marsh', strength: 0.6 });
  const painted = scene.view();
  assert.deepEqual(painted.sample(...xy).weights, [{ id: 'marsh', weight: 0.6 }, { id: 'kelp-bed', weight: 0.4 }]);
  assert.deepEqual(painted.sample(...below), initial.sample(...below));
  assert.deepEqual(painted.inspect(...xy).strokes.map(dab => dab.id), ['mix']);
  const feathered = painted.inspect(3, -2, 3.5);
  assert(feathered.weights.find(row => row.id === 'marsh').weight < 0.6);
  const dryMask = painted.inspect(4.05, -2, 3.55);
  assert.equal(dryMask.strokes.length, 0);
  scene.paint({ ...shape, id: 'restore', channel: 'biome', operation: 'erase' });
  assert.deepEqual(scene.view().sample(...xy), initial.sample(...xy));

  scene.paint({ ...shape, id: 'no-kelp', channel: 'population', target: 'kelp' });
  const covered = scene.view().inspect(...xy, { species: 'kelp' });
  assert.deepEqual(covered.exclusions, [{ target: 'kelp', weight: 1 }]);
  assert.equal(covered.populations[0].density, 0);
  scene.paint({ ...shape, id: 'restore-kelp', channel: 'population', target: 'kelp', operation: 'erase', strength: 0.5 });
  const thinned = scene.view().inspect(...xy, { species: 'kelp' });
  assert.equal(thinned.populations[0].density, 0.465);
  scene.paint({ ...shape, id: 'no-kelp', channel: 'population', target: 'kelp', strength: 0.6 });
  assert.deepEqual(scene.view().inspect(...xy).strokes.map(row => row.id), ['mix', 'restore', 'no-kelp', 'restore-kelp']);
  assert(Math.abs(scene.view().inspect(...xy, { species: 'kelp' }).populations[0].exclusion - 0.3) < 1e-12);
  assert.equal(initial.inspect(...xy, { species: 'kelp' }).populations[0].density, 0.93);
  assert.deepEqual(example(KIT, scene.document.serialize()).view().inspect(...xy), scene.view().inspect(...xy));
});

test('seeded spatial fields can vary biome weights and keep earlier revisions readable', () => {
  const scene = example(KIT);
  scene.setRegion({
    id: 'patch', biome: 'marsh', bounds: { min: [-13, 0, 0], max: [-10, 1, 5] },
    field: { type: 'add', inputs: [0.5, { type: 'simplex', scale: 3 }] }
  });
  const a = scene.view();
  const field = view => view.inspect(-11, 0.5, 2.8).base.regions.find(row => row.id === 'patch').fieldWeight;
  const before = field(a);
  scene.setSeed(96);
  assert.notEqual(field(scene.view()), before);
  assert.equal(field(a), before);
  assert.equal(field(example(KIT, scene.document.serialize()).view()), field(scene.view()));
  assert.equal(a.inspect(-11, 0.5, 2.8).base.regions[0].checks.find(check => check.field === 'moisture').weight, 0);
});

test('seeded, layered population IDs agree across chunk splits and include every example species', () => {
  const world = example(KIT).view();
  const spans = [
    { min: [-15, 6, 0], max: [-7.5, 6, 8], layer: 'ridge-top', species: 'lichen' },
    { min: [-6.5, 0.5, 0], max: [-0.2, 0.5, 8], layer: 'mudflat', species: 'reed' },
    { min: [0, -2, 0], max: [8, -2, 6], layer: 'shelf', species: 'kelp' },
    { min: [0, -9, 0], max: [8, -9, 6], layer: 'deep', species: 'glow-moss' }
  ];
  for (const { min, max, layer, species } of spans) {
    const opts = { height: () => min[1], layer, spacing: 0.7, exclusion: { distance: 0.4 } };
    const whole = world.populate({ min, max }, opts).instances;
    assert(whole.length > 0 && whole.every(row => row.sample.species === species));
    const mid = (min[0] + max[0]) / 2;
    const left = world.populate({ min, max: [mid, max[1], max[2]] }, opts).instances;
    const right = world.populate({ min: [mid, min[1], min[2]], max }, opts).instances;
    const joined = new Map([...left, ...right].map(row => [row.id, row]));
    assert.deepEqual(new Map(whole.map(row => [row.id, row])), joined);
    assert.deepEqual(world.populate({ min, max }, opts).instances, whole);
    if (species === 'kelp') assert(whole.every(row => row.sample.position[0] < 6));
  }
  assert.equal(world.populate({ min: [0, -8.5, 0], max: [8, -8, 6] },
    { height: () => -9, maxInstances: 1 }).instances.length, 0);
  const bed = { min: [1, -4, 1], max: [5, -4, 5] };
  const anchored = world.populate(bed, { height: () => -4, habitatOffset: 0.75, layer: 'reef-bed' }).instances;
  assert(anchored.length > 0 && anchored.every(row => row.sample.species === 'kelp' && row.sample.position[1] === -4));
  assert.equal(world.inspect(3, -4, 3, { habitatOffset: 0.75, species: 'kelp' }).medium.depth, 3.25);
});

test('route and landmark pins survive reseeding and saved snapshots and reserve local population clearance', () => {
  const scene = example(KIT), before = scene.view();
  const beacon = view => view.layout.landmarks.find(row => row.id === 'beacon');
  const ascent = view => view.layout.routes.find(row => row.id === 'ascent');
  const pin = [-9, 6, 4], route = [[-15, 6, 1], [-8, 6, 1]];
  scene.pinLandmark('ridge', 'beacon', pin);
  assert.deepEqual(ascent(scene.view()).points.at(-1), pin);
  scene.pinRoute('ridge', 'ascent', route);
  scene.setSeed(99);
  assert.notDeepEqual(beacon(before).point, pin);
  assert.equal(beacon(scene.view()).pinned, true);
  assert.deepEqual(beacon(scene.view()).point, pin);
  assert.deepEqual(ascent(scene.view()).points, route);
  const near = scene.view().inspect(-11, 6, 1);
  assert(near.reservations.some(hit => hit.kind === 'route' && hit.id === 'ascent'));
  assert.equal(near.populations[0].density, 0);
  assert.equal(scene.view().inspect(-11, 6, 2).reservations.length, 0);
  const restored = example(KIT, scene.document.serialize());
  assert.deepEqual(restored.view().layout, scene.view().layout);
  assert.equal(scene.document.undo(), true);
  assert.equal(scene.view().seed, 26);
  assert.deepEqual(ascent(scene.view()).points, route);
  assert.equal(scene.document.redo(), true);
  assert.equal(scene.view().seed, 99);
  scene.unpinRoute('ridge', 'ascent');
  assert.deepEqual(ascent(scene.view()).points.at(-1), pin);
});

test('retained edits group into one undo and invalid recipes or strokes leave the snapshot intact', () => {
  const scene = biomeRecipes.create({ fallback: 'plain', recipes: [{ id: 'plain', materials: { soil: [0x334433] } }] });
  assert.equal(scene.document.undo(), false);
  const original = scene.view();
  assert.throws(() => scene.setRecipe({ id: 'plain', materials: { soil: ['not a color'] } }), /color/);
  assert.throws(() => scene.paint({ id: 'typo', channel: 'biome', target: 'unknown', points: [[0, 0]] }), /Unknown paint/);
  assert.deepEqual(scene.document.snapshot(), original.snapshot);
  scene.document.transact('Paint a ridge', () => {
    scene.setRecipe({ id: 'ridge', materials: { rock: [0xeeeeee] } });
    scene.paint({ id: 'ridge-top', channel: 'biome', target: 'ridge', points: [[0, 0]] });
  });
  assert.equal(scene.view().sample(0, 0, 0).biome, 'ridge');
  assert.equal(scene.document.undo(), true);
  assert.deepEqual(scene.view().snapshot, original.snapshot);
  assert.equal(scene.document.redo(), true);
  assert.equal(scene.view().sample(0, 0, 0).biome, 'ridge');
});

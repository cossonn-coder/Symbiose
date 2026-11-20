const test = require('node:test');
const assert = require('node:assert/strict');
const { biomes } = require('..').load().KIT.procedural;

test('biome weights blend into the fallback and overlapping regions of the same biome do not stack', () => {
  const bounds = { min: [-1, -1, -1], max: [1, 1, 1] };
  const regions = [
    { id: 'marsh-edge', biome: 'marsh', bounds, weight: (x, y, z, time, local) => local.moisture },
    { id: 'marsh-bank', biome: 'marsh', bounds, weight: 0.25 },
    { id: 'meadow', bounds, weight: (x, y, z, time) => time }
  ];
  const options = { fallback: 'forest', conditions: x => ({ moisture: (x + 1) / 2 }), regions };
  const world = biomes.create(options);
  assert.deepEqual(world.sample(-1, 0, 0).weights, [{ id: 'forest', weight: 0.75 }, { id: 'marsh', weight: 0.25 }]);
  assert.deepEqual(world.sample(0, 0, 0).weights, [{ id: 'forest', weight: 0.5 }, { id: 'marsh', weight: 0.5 }]);
  assert.deepEqual(world.sample(1, 0, 0, 1).weights, [{ id: 'marsh', weight: 0.5 }, { id: 'meadow', weight: 0.5 }]);
  assert.equal(world.sample(1, 0, 0, 1).biome, 'marsh');
  assert.deepEqual(world.sample(1, 0, 0, 1), biomes.create({ ...options, regions: regions.slice().reverse() }).sample(1, 0, 0, 1));
  assert.deepEqual(world.sample(2, 0, 0).weights, [{ id: 'forest', weight: 1 }]);
  assert.deepEqual(
    biomes.create({ fallback: 'marsh', regions: regions.slice(0, 2), conditions: options.conditions }).sample(0, 0, 0).weights,
    [{ id: 'marsh', weight: 1 }]
  );
});

test('surface forest, solid rock, flooded cave and an air pocket can share the same XZ', () => {
  const bounds = { min: [-2, -6, -2], max: [2, -2, 2] };
  const cave = (x, y, z) => Math.hypot(x, y + 4, z) - 2;
  let conditionCalls = 0;
  const world = biomes.create({
    fallback: 'forest',
    solid: (x, y, z) => Math.max(y, -cave(x, y, z)),
    conditions(x, y, z, time, medium) {
      conditionCalls++;
      return { moisture: medium.kind === 'water' ? 1 : 0.3, exposure: y >= 0 ? 1 : 0 };
    },
    regions: [{ id: 'cavern', bounds, weight: (x, y, z) => Number(cave(x, y, z) < 0) }],
    media: [
      { id: 'aquifer', kind: 'water', bounds, sdf: cave, surface: (x, z, time) => -3 + time / 2,
        current: (x, y, z, time) => [0.4, time, 0] },
      { id: 'air-pocket', kind: 'air', priority: 1, bounds, sdf: (x, y, z) => Math.hypot(x, y + 3.5, z) - 0.25 }
    ]
  });
  assert.equal(world.mediumAt(0, -3, 0).kind, 'air');
  assert.equal(world.mediumAt(0, -3, 0, 1).depth, 0.5);
  assert.equal(world.mediumAt(0, -3.5, 0).id, 'air-pocket');
  assert.equal(world.mediumAt(0, -3.75, 0).id, 'aquifer');
  assert.equal(world.mediumAt(2, -4, 1).kind, 'solid');
  assert.equal(conditionCalls, 0);
  assert.equal(world.sample(0, 1, 0).biome, 'forest');
  assert.equal(world.sample(0, -3.5, 0).biome, 'cavern');
  assert.deepEqual(world.sample(0, -4, 0, 1), {
    biome: 'cavern',
    weights: [{ id: 'cavern', weight: 1 }],
    medium: { kind: 'water', id: 'aquifer', surface: -2.5, depth: 1.5, current: [0.4, 1, 0] },
    conditions: { moisture: 1, exposure: 0 }
  });
});

test('indexed biome and water samples match a direct scan, including inclusive box boundaries', () => {
  const boxes = Array.from({ length: 50 }, (_, i) => {
    const min = [(i * 5) % 13 - 6, (i * 11) % 9 - 6, (i * 7) % 17 - 8];
    return { min, max: min.map((n, axis) => n + (i + axis) % 5) };
  });
  const regions = boxes.map((bounds, i) => ({ id: 'region-' + i, biome: 'biome-' + i % 7, bounds, weight: (i % 4 + 1) / 4 }));
  const media = boxes.map((bounds, i) => ({ id: 'water-' + i, priority: i % 3, bounds, kind: 'water', surface: i % 5 - 2 }));
  const world = biomes.create({ regions, media });
  const reversed = biomes.create({ regions: regions.slice().reverse(), media: media.slice().reverse() });
  const byId = (a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
  for (let x = -7; x <= 7; x++) for (let y = -7; y <= 3; y++) for (let z = -9; z <= 9; z++) {
    const contains = ({ bounds }) => [x, y, z].every((n, axis) => n >= bounds.min[axis] && n <= bounds.max[axis]);
    const eligible = regions.filter(contains);
    const ids = new Set(eligible.map(region => region.biome));
    const expected = Array.from(ids, id => ({
      id, weight: Math.max(...eligible.filter(region => region.biome === id).map(region => region.weight))
    }));
    const total = expected.reduce((sum, match) => sum + match.weight, 0);
    if (total < 1) expected.push({ id: 'default', weight: 1 - total });
    else for (const row of expected) row.weight /= total;
    expected.sort((a, b) => b.weight - a.weight || byId(a, b));

    const winner = media.filter(row => contains(row) && y < row.surface)
      .sort((a, b) => b.priority - a.priority || byId(a, b))[0];
    const sample = world.sample(x, y, z);
    assert.deepEqual(sample.weights, expected);
    assert.equal(sample.medium.id, winner?.id ?? null);
    assert.equal(sample.medium.depth, winner ? winner.surface - y : 0);
    assert.deepEqual(sample, reversed.sample(x, y, z));
  }
});

test('prepared queries capture bounds and constant currents and skip out-of-bounds fields', () => {
  const bounds = { min: [-1, -1, -1], max: [1, 1, 1] }, current = [1, 2, 3];
  let evaluated = 0;
  const world = biomes.create({
    regions: [{ id: 'reef', bounds, weight: () => (evaluated++, 1) }],
    media: [{ id: 'bay', kind: 'water', bounds, surface: 1, current }]
  });
  bounds.min[0] = 0;
  current[0] = 999;
  assert.equal(world.sample(3, 0, 0).biome, 'default');
  assert.equal(evaluated, 0);
  const first = world.sample(-1, 0, 0);
  assert.deepEqual(first.medium.current, [1, 2, 3]);
  first.weights[0].weight = 0;
  assert.equal(world.sample(-1, 0, 0).weights[0].weight, 1);
});

test('malformed definitions and nonfinite sampler outputs fail explicitly', () => {
  const bounds = { min: [-1, -1, -1], max: [1, 1, 1] }, region = { id: 'reef', bounds };
  const water = { id: 'bay', kind: 'water', bounds, surface: 1 };
  assert.throws(() => biomes.create({ regions: [region, region] }), /unique/);
  assert.throws(() => biomes.create({ regions: [{ ...region, bounds: { min: Array(3), max: [1, 1, 1] } }] }), /bounds/);
  assert.throws(() => biomes.create({ media: [{ ...water, surface: Infinity }] }), /surface/);
  assert.throws(() => biomes.create().sample(0, 0, 0, NaN), /finite/);
  assert.throws(() => biomes.create({ solid: () => NaN }).mediumAt(0, 0, 0), /SDF/);
  assert.throws(() => biomes.create({ conditions: () => ({ exposure: Infinity }) }).sample(0, 0, 0), /conditions/);
  assert.throws(() => biomes.create({ regions: [{ ...region, weight: () => -1 }] }).sample(0, 0, 0), /weight/);
  assert.throws(() => biomes.create({ media: [{ ...water, current: () => [0, 0] }] }).mediumAt(0, 0, 0), /current/);
});

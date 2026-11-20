const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const { hydrology, routes } = KIT.procedural;
const bounds = { min: [0, -3, 0], max: [8, 20, 8] };
const threshold = 1e-9;

function near(a, b) {
  assert(Math.abs(a - b) < threshold, a + ' differs from ' + b);
}

test('Priority-Flood drains a depression through its low saddle while retaining an authored lake bed', () => {
  const elevation = (x, z) => Math.min(x, z, 8 - x, 8 - z) <= 1
    ? (x === 4 && z <= 1 ? 1.5 : 4)
    : x === 4 && z === 4 ? -2 : 0;
  const h = hydrology.analyze(elevation, {
    bounds, cell: 1, channelArea: 2,
    lakeAt: (x, z) => x === 4 && z >= 3 && z <= 5 ? { id: 'pool', level: 1.25 } : null
  });
  const lake = h.sample(4, 4);
  assert.equal(lake.elevation, -2);
  assert.equal(lake.terrainHeight, -2);
  assert.equal(lake.drainageHeight, 1.5);
  assert.equal(lake.lakeLevel, 1.25);
  assert.equal(lake.lakeId, 'pool');
  assert.equal(h.sample(3, 4).terrainHeight, 1.5);
  assert.equal(h.sample(4, 4).catchmentId, 'catchment:4:0');
  assert.equal(h.wetness(4, 4), 1);
  assert.deepEqual(h.lakes, [{ id: 'pool', level: 1.25, samples: 3 }]);
  assert(h.nodes.some(node => node.lake === 'pool' && node.incoming.length));
  const submergedXZ = point => point[0] === 4 && point[2] >= 3 && point[2] <= 5;
  assert(h.reaches.every(reach => !reach.route.points.slice(1, -1).some(submergedXZ)));
});

test('D8 flow routes flats without cycles and conserves nonuniform rainfall over all outlets', () => {
  const rain = (x, z) => 0.5 + x * 0.1 + z * 0.15,
    h = hydrology.analyze((x, z) => x + Math.abs(z - 4), { bounds, cell: 1, rain, channelArea: 2 });
  const { receiver, drainageHeight, outlet, accumulation } = h.fields;
  let rainTotal = 0;
  for (let i = 0; i < receiver.length; i++) {
    rainTotal += rain(i % 9, Math.floor(i / 9));
    let next = i, steps = 0;
    while (receiver[next] >= 0) {
      assert(drainageHeight[receiver[next]] <= drainageHeight[next]);
      next = receiver[next];
      assert(++steps <= receiver.length);
    }
    assert.equal(next, outlet[i]);
    assert(accumulation[i] <= accumulation[next]);
  }
  near(h.catchments.reduce((sum, entry) => sum + entry.accumulation, 0), rainTotal);
  const flat = hydrology.analyze(() => 0, { bounds, cell: 1, channelArea: 2 });
  assert(flat.fields.receiver[4 + 4 * 9] >= 0);
  near(flat.catchments.reduce((sum, entry) => sum + entry.accumulation, 0), 81);
});

test('channel reaches remain connected to stable world IDs and can drive route fitting', () => {
  const height = (x, z) => x + Math.abs(z - 4),
    spec = { bounds, cell: 1, channelArea: 3 },
    h = hydrology.analyze(height, spec),
    rebuilt = hydrology.analyze(height, { ...spec, rain: (x, z) => x === 8 && z === 8 ? 1.01 : 1 });
  assert(h.reaches.length > 1);
  assert.deepEqual(h.reaches.map(reach => reach.id), rebuilt.reaches.map(reach => reach.id));
  const records = new Map(h.nodes.map(node => [node.id, node]));
  for (const reach of h.reaches) {
    const a = records.get(reach.from),
      b = records.get(reach.to);
    assert(a.outgoing.includes(reach.id));
    assert(b.incoming.includes(reach.id));
    assert.deepEqual(a.point, reach.route.sample(0).point);
    assert.deepEqual(b.point, reach.route.sample(1).point);
    assert(routes.layout(reach.route, { pitch: 1 }).length > 0);
  }
  assert(Math.max(...h.fields.streamOrder) >= 2);
  assert.equal(h.sample(2, 4).catchmentId, h.sample(8, 4).catchmentId);
  assert.equal(h.sample(-1, 4), null);
  assert.equal(h.wetness(10, 10), 0);
});

test('D-infinity splits flow proportionally on slanted terrain and also conserves rainfall', () => {
  const angle = Math.PI / 8,
    h = hydrology.analyze((x, z) => 10 + x * Math.cos(angle) + z * Math.sin(angle), {
      bounds, cell: 1, distributed: true
    }),
    i = 4 + 4 * 9,
    { receiver, secondary, secondaryShare, accumulation } = h.distributed;
  assert.deepEqual([receiver[i], secondary[i]], [i - 1, i - 10]);
  near(secondaryShare[i], 0.5);
  near(accumulation.reduce((sum, area, index) => sum + (receiver[index] < 0 ? area : 0), 0), 81);
  assert.equal(hydrology.analyze(() => 0, { bounds }).distributed, null);
});

test('watershed validates budgets, fields and inconsistent artist-lake levels', () => {
  assert.throws(() => hydrology.analyze(() => 0, { bounds, cell: 0.01, maxCells: 100 }), /budget/);
  assert.throws(() => hydrology.analyze(() => NaN, { bounds }), /finite/);
  assert.throws(() => hydrology.analyze(() => 0, { bounds, rain: () => -1 }), /rainfall/);
  assert.throws(() => hydrology.analyze(() => 0, { bounds, lakeAt: x => ({ id: 'lake', level: x }) }), /one level/);
});

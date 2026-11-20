const test = require('node:test');
const assert = require('node:assert/strict');
const P = require('..').load().KIT.procedural;
const H = P.hydrology;
const bounds = { min: [0, -4, 0], max: [8, 5, 8] };

test('depression breaching lowers a spill path in a steady grade and applies no partial cut on failure', () => {
  const height = (x, z) => Math.min(x, z, 8 - x, 8 - z) <= 1
    ? (x === 4 && z <= 1 ? 1.5 : 4) : (x === 4 && z === 4 ? -0.4 : 0),
    basin = H.analyze(height, { bounds, cell: 1, lakeAt: (x, z) => x === 6 && z === 5 ? { id: 'pin', level: 0.2 } : null }),
    blocked = H.breach(basin, { maxDepth: 0.3 }),
    edit = H.breach(basin, { maxDepth: 2.1, grade: 0.01 });
  assert.equal(blocked.channels[0].reason, 'depth');
  assert.deepEqual(blocked.elevation, basin.fields.elevation);
  assert.equal(edit.channels[0].status, 'ok');
  assert(edit.channels[0].volume > 3);
  assert.equal(edit.height(6, 5), height(6, 5));
  const route = edit.channels[0].route.points;
  assert(route.every((p, i) => !i || p[1] < route[i - 1][1]));
  const flowed = H.analyze(edit.height, { bounds, cell: 1 });
  assert.equal(flowed.sample(4, 4).drainageHeight, edit.height(4, 4));
});

test('stream-power incision responds to accumulated area and grade while retaining masked cells and lakes', () => {
  const a = H.analyze((x, z) => x * 0.4 + Math.abs(z - 4) * 0.55, {
      bounds, cell: 1, lakeAt: (x, z) => x === 5 && z === 4 ? { id: 'pond', level: 2.2 } : null
    }),
    edit = H.incise(a, { strength: 0.22, minArea: 2, maxDepth: 0.28, steps: 6, allow: (x, z) => z !== 0 });
  assert(edit.incision(2, 4) > 0.06);
  assert.equal(edit.incision(5, 4), 0);
  assert.equal(edit.incision(2, 0), 0);
  assert(edit.depth.every(d => d >= 0 && d <= 0.28000001));
  for (let i = 0; i < edit.elevation.length; i++) {
    const other = a.fields.receiver[i];
    if (other >= 0 && a.fields.terrainHeight[i] > a.fields.terrainHeight[other])
      assert(edit.elevation[i] + 1e-10 >= edit.elevation[other]);
  }
});

test('meander migration is seeded and bounded with exact pins, and necks detach as cutoff routes', () => {
  const start = [-4, 0.8, 0], end = [4, 0.2, 0],
    baseline = P.routes.polyline([start, end]),
    opts = { curvatureGain: 0.01, seed: 14, amplitude: 0.4, maxShift: 0.75, spacing: 0.21 },
    meander = H.meander(baseline, opts).route;
  assert.deepEqual(meander.points[0], start);
  assert.deepEqual(meander.points.at(-1), end);
  assert(meander.points.some(p => Math.abs(p[2]) > 0.1));
  assert(meander.points.every(p => Math.abs(p[2]) <= 0.7500001));
  assert.deepEqual(meander.points, H.meander(baseline, opts).route.points);
  const curl = P.routes.polyline([[0,0,0],[2,0,0],[2,0,2],[0,0,2],[0,0,0.10],[-1,0,0.10]]),
    cut = H.meander(curl, { spacing: 0.11, cutoffDistance: 0.18, minLoop: 2, iterations: 0 });
  assert.equal(cut.cutoffs.length, 1);
  assert(cut.route.length < curl.length * 0.3);
});

test('corridor controls expose floodplain and levee while excluding high or steep banks', () => {
  const line = P.routes.polyline([[-4, 0, 0], [4, 0, 0]]),
    options = { channelWidth: 0.32, floodWidth: 1.4, leveeWidth: 0.42, leveeHeight: 0.18 },
    flat = H.corridor([line], () => 0.12, options),
    steep = H.corridor([line], (x, z) => z * 0.9, options);
  assert(flat.floodplain(0, 0.38) > 0.5);
  assert(flat.levee(0, 0.53) > 0.1);
  assert.equal(flat.levee(0, 0.03), 0);
  assert.equal(flat.floodplain(0, 2), 0);
  assert.equal(steep.floodplain(0, 0.38), 0);
  assert.equal(steep.levee(0, 0.53), 0);
});

test('climate fields distinguish windward slopes, rain shadows, cooling and proximity to water', () => {
  const ridge = x => Math.max(0, 1 - Math.abs(x - 4) / 3) * 2.1,
    a = H.analyze(ridge, { bounds, cell: 0.5 }),
    climate = H.habitat(a, { wind: [1, 0], humidity: 0.82, uplift: 1.1, lapse: 0.12,
      insolation: 0, waterDistance: (x, z) => Math.abs(z - 7) });
  const upstream = climate.sample(3, 2),
    crest = climate.sample(4, 2),
    lee = climate.sample(5, 2);
  assert(upstream.precipitation > lee.precipitation * 3);
  assert(lee.vapor < climate.sample(1, 2).vapor * 0.65);
  assert(crest.temperature < climate.sample(0, 2).temperature);
  assert(climate.sample(5, 7).waterProximity > lee.waterProximity);
  assert(climate.sample(5, 7).moisture > lee.moisture);
  assert.equal(climate.sample(-1, 0), null);
});

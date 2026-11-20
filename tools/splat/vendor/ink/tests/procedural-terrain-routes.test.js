const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const { routes } = KIT.procedural;
const flat = { bounds: { min: [0, -3, -4], max: [10, 3, 4] }, height: () => 0, cell: 0.5, sampleStep: 0.08 };

function along(route, sample) {
  const n = Math.ceil(route.length / 0.02);
  for (let i = 0; i <= n; i++) sample(...route.sample(i / n).point);
}

test('terrain routing preserves exact off-grid pins, clears a solid and an authored exclusion, and fits pieces', () => {
  const start = [0.17, 0.12, 0.12],
    end = [9.81, 0.18, -0.15],
    clearance = (x, y, z) => Math.hypot(x - 3, y, z - 0.16) - 0.8,
    keepOut = (x, z) => x >= 5.8 && x <= 7.5 && Math.abs(z + 0.2) < 0.86,
    spec = { ...flat, clearance, keepOut, minClearance: 0.4, maxSlope: 0.4, maxDeviation: 0.2, turnCost: 0.25 };
  const result = routes.terrain(start, end, spec);
  assert.equal(result.status, 'ok');
  assert.deepEqual(result.route.points, routes.terrain(start, end, spec).route.points);
  assert.deepEqual(result.route.sample(0).point, start);
  assert.deepEqual(result.route.sample(1).point, end);
  assert(result.gridPoints > result.route.points.length);
  along(result.route, (x, y, z) => {
    assert(clearance(x, y, z) >= 0.39);
    assert(!keepOut(x, z));
  });
  const pieces = routes.layout(result.route, { pitch: 0.55, gap: 0.025 });
  assert(pieces.length > 12);
  assert(pieces.every(p => p.length > 0 && p.frame.point.every(Number.isFinite)));
});

test('terrain routing avoids sampled cliffs and preserves a soft keep-out cost during simplification', () => {
  const height = (x, z) => 0.99 * Math.max(0, 1 - Math.hypot((x - 3.8) * 1.7, z)),
    cost = (x, y, z) => x >= 6 && x <= 9 && Math.abs(z) < 0.72 ? 30 : 0,
    result = routes.terrain([0.13, 0, 0], [9.9, 0, 0], { ...flat, height, cost, maxSlope: 0.28, maxDeviation: 0.1 });
  assert.equal(result.status, 'ok');
  assert(result.cost < 15);
  along(result.route, (x, y, z) => {
    assert(Math.abs(height(x, z) - y) <= 0.101);
    assert.equal(cost(x, y, z), 0);
  });
});

test('turn costs select a smoother route through alternative corridors', () => {
  // The low-cost route can use a zigzag made of four openings. The top route has fewer changes in heading.
  const walls = (x, z) => [2, 4, 6, 8].some((wx, i) => {
    if (Math.abs(x - wx) > 0.21) return false;
    return Math.abs(z - (i % 2 ? 0.65 : -0.65)) > 0.55 && Math.abs(z - 2.65) > 0.55;
  });
  const spec = { ...flat, keepOut: walls, lookAhead: 0 },
    run = turnCost => routes.terrain([0.2, 0, 0], [9.8, 0, 0], { ...spec, turnCost }),
    measure = points => {
      const angles = points.slice(1).map((p, i) => Math.atan2(p[2] - points[i][2], p[0] - points[i][0]));
      return angles.slice(1).reduce((sum, a, i) => {
        const d = Math.abs(a - angles[i]);
        return sum + Math.min(d, 2 * Math.PI - d);
      }, 0);
    };
  const shortest = run(0), smoother = run(5);
  assert.equal(shortest.status, 'ok');
  assert.equal(smoother.status, 'ok');
  assert(shortest.route.length < smoother.route.length);
  assert(measure(smoother.route.points) < measure(shortest.route.points));
});

test('blocked pins, disconnected regions, and work budgets report distinct outcomes', () => {
  const start = [0.1, 0, 0],
    end = [9.9, 0, 0];
  assert.equal(routes.terrain(start, end, { ...flat, keepOut: x => x < 1 }).status, 'blocked-pin');
  assert.equal(routes.terrain(start, end, { ...flat, keepOut: x => Math.abs(x - 5) < 0.5 }).status, 'unreachable');
  for (const [option, reason] of [['maxCells', 'cells'], ['maxVisits', 'visits'], ['maxSamples', 'samples']]) {
    const result = routes.terrain(start, end, { ...flat, [option]: 1 });
    assert.equal(result.status, 'budget');
    assert.equal(result.reason, reason);
  }
  assert.throws(() => routes.terrain(start, end, { ...flat, cost: () => -1 }), /nonnegative/);
  assert.throws(() => routes.terrain(start, end, { ...flat, cell: 0 }), /Invalid/);
});

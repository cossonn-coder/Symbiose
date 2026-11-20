const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: K } = require('..').load();
const { growth } = K.procedural;

test('stochastic parametric growth reads local turtle frames and retains persistent token IDs', () => {
  const axiom = [{ symbol: 'F', args: [0.5, 0.07] }, { symbol: 'B', args: [0.8] }],
    shoot = { symbol: 'F', args: [{ arg: 0, scale: 0.5 }, 0.02] },
    rules = [
      { from: 'B', when: (_, c) => c.environment.light > 0, weight: 3, to: ['[', '+', shoot, 'L', ']'] },
      { from: 'B', when: (_, c) => c.environment.light > 0, to: ['[', '-', shoot, 'L', ']'] },
      { from: 'B', when: (_, c) => c.environment.light <= 0, to: ['L'] }
    ],
    options = { generations: 2, seed: 9,
      environment(_, { frame }) { return { light: frame.p[1] - 0.25 }; }
    },
    result = growth.lsystem(axiom, rules, options), shape = growth.turtle(result.tokens);
  assert.deepEqual(result, growth.lsystem(axiom, rules, options));
  assert.equal(shape.limbs[0].id, 'axiom/0');
  assert.equal(shape.limbs.length, 2);
  assert(shape.marks[0].p[1] > 0.5);
  assert(Math.abs(K.V.len(K.V.sub(...shape.limbs[1].pts)) - 0.4) < 1e-8);
  assert.equal(growth.lsystem(axiom, rules, { ...options, environment: () => ({ light: 0 }) }).tokens.length, 2);
  assert.throws(() => growth.lsystem(axiom, rules, { ...options, maxSymbols: 3 }), /tape budget/);
});

test('venation grows towards interior attractors and preserves pipe widths across forks', () => {
  const outline = [[0,-1],[0.92,-0.35],[0.87,0.45],[0,1],[-0.87,0.45],[-0.92,-0.35]],
    leaf = growth.venation(outline, { root: [0,-1], toward: [0,1], seed: 9 });
  assert(leaf.sources.length > 18);
  assert(leaf.limbs.length > 13);
  assert(leaf.nodes.every(({ p }) => Math.abs(p[2]) < 1e-8 && p[1] >= -1));
  const radius = growth.pipe([{ parent: -1 }, { parent: 0 }, { parent: 0 }, { parent: 2 }],
    { tipRadius: 0.1, exponent: 2 });
  assert(Math.abs(radius[0] ** 2 - radius[1] ** 2 - radius[2] ** 2) < 1e-8);
  assert.equal(radius[2], radius[3]);
});

test('moisture bias bends roots while accepted segments stay clear of an obstacle', () => {
  const obstacle = (x, y) => Math.hypot(x, y + 0.62) - 0.25,
    config = { obstacle, clearance: 0.045, step: 0.12, length: 1.7, branchChance: 0.3, seed: 8 },
    a = growth.roots([[0,0,0]], { ...config, moisture: x => x + 2 }),
    b = growth.roots([[0,0,0]], { ...config, moisture: x => 2 - x });
  assert(a.nodes.length > 14);
  assert(a.nodes.at(-1).p[0] > 0.6);
  assert(b.nodes.at(-1).p[0] < -0.6);
  for (const { pts: [p, q] } of a.limbs) for (const t of [0, 0.25, 0.5, 0.75, 1])
    assert(obstacle(...K.V.mad(p, K.V.sub(q, p), t)) >= config.clearance);
});

test('aggregate walkers attach to existing lattice neighbors and honor masks and budgets', () => {
  const options = { width: 41, height: 41, target: 128, seed: 7, mask: (x, z) => x > 5 && z < 35 },
    cluster = growth.aggregate(options);
  assert.equal(cluster.status, 'ok');
  assert.deepEqual(cluster, growth.aggregate(options));
  assert.equal(cluster.nodes.length, 128);
  for (const [i, { x, z, parent }] of cluster.nodes.entries()) {
    assert(options.mask(x, z));
    assert.equal(cluster.cells[z * cluster.width + x], i + 1);
    if (parent < 0) continue;
    const p = cluster.nodes[parent];
    assert(parent < i && Math.abs(p.x - x) + Math.abs(p.z - z) === 1);
  }
  assert.equal(growth.aggregate({ ...options, maxChecks: 1 }).status, 'budget');
});

test('Gray–Scott evolves a grid and cannot cross disconnected surface components', () => {
  const grid = growth.grayScottGrid({ width: 33, height: 35, steps: 180, seed: 6, mask: x => x !== 26 });
  assert(Math.max(...grid.v) > 0.2);
  assert.equal(grid.sample(27, 18).v, 0);
  assert.equal(grid.sample(-1, 18), null);
  const surface = growth.grayScottSurface([[0,0,0],[1,1,0],[2,2,0],[3,3,0]], [[0,1],[1,2,2]], {
    steps: 5, spots: [0]
  });
  assert(surface.v[1] > 0);
  assert(surface.v[2] > 0);
  assert.equal(surface.v[3], 0);
});

test('kernel drift is directional and succession applies habitat, competition, and complete year budgets', () => {
  const kernel = growth.dispersal({ drift: [2,0], radius: 5, spread: 1.5, aspect: 1.6 }),
    mass = kernel.reduce((sum, p) => sum + p.weight, 0),
    expectedX = kernel.reduce((sum, p) => sum + p.x * p.weight, 0);
  assert(Math.abs(mass - 1) < 1e-12);
  assert(expectedX > 0.9);
  assert(growth.dispersal({ radius: 20, drift: [20,20], spread: 0.15 }).length > 0);
  const species = [
      { id: 'pioneer', maturity: 0, immigration: 0.15, competition: 0.6, survival: 0.94 },
      { id: 'shrub', competition: 3, habitat: x => Number(x > 20), immigration: 0.04, survival: 0.98 }
    ],
    options = { width: 38, height: 12, years: 16, seed: 2, species, mask: x => x !== 20 },
    model = growth.succession(options), repeat = growth.succession(options);
  assert.deepEqual(model.cells, repeat.cells);
  assert.deepEqual(model.timeline, repeat.timeline);
  assert(model.timeline.at(-1).shrub > model.timeline[2].shrub * 2);
  assert.equal(model.sample(20, 3), null);
  assert(model.cells.every((n, i) => n !== 2 || i % 38 > 20));
  assert.equal(growth.succession({ ...options, maxWork: 1200 }).timeline.length, 1);
});

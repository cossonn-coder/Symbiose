const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: K, makeBuilder, makeSculpt } = require('..').load();
const { forms, fracture } = K.procedural;

test('power weights move the actual fragment boundary and a gap separates the fields', () => {
  const host = forms.superquadric({ radii: [1,0.5,1] }),
    result = fracture.power({ host, gap: 0.048, seeds: [
      { id: 'heavy', point: [-0.45,0,0], weight: 0.27 }, { id: 'light', point: [0.45,0,0] }
    ] }),
    [heavy, light] = result.cells, [bond] = result.bonds;
  assert(heavy.volume > light.volume);
  assert.equal(result.owner(0.14,0,0), 'heavy');
  assert.equal(result.owner(0.16,0,0), 'light');
  assert.equal(result.owner(2,0,0), null);
  assert(heavy.form.sd(0.11,0,0) < 0);
  assert(light.form.sd(0.19,0,0) < 0);
  assert(heavy.form.sd(0.15,0,0) > 0 && light.form.sd(0.15,0,0) > 0);
  assert(Math.abs(bond.point[0] - 0.15) < 1e-8);
  assert(bond.capacity > 1 && bond.capacity < 1.7);
  const B = makeBuilder(9), S = K.sculpt(makeSculpt(B));
  for (const { form } of result.cells) S.implicitForm(form, { r: [1,2,3] }, { res: 0.08, maxWork: 32000000 });
  S.bake();
  assert(B.finish({}).count > 300);
});

test('a directional metric rotates partition planes and preserves exclusive ownership', () => {
  const host = forms.superquadric({ radii: [1,0.8,1] }),
    seeds = [{ id: 'a', point: [-0.3,-0.32,0] }, { id: 'b', point: [0.3,0.32,0] }],
    base = fracture.power({ host, seeds }),
    grain = fracture.power({ host, seeds, stretch: [0.2, 1.8, 1], rotation: [0,0,0.2] });
  assert(base.bonds[0].normal[1] > 0.7);
  assert(grain.bonds[0].normal[0] > 0.94 && grain.bonds[0].normal[1] < 0.28);
  assert.equal(base.owner(0.19,-0.31,0.24), 'a');
  assert.equal(grain.owner(0.19,-0.31,0.24), 'b');
  for (const point of [[-0.15,0,0], [0.12,0,0.18], [0.6,-0.23,0], [-0.5,0.27,0]]) {
    assert.deepEqual(grain.cells.filter(c => c.form.sd(...point) < 0).map(c => c.id), [grain.owner(...point)]);
  }
  assert.throws(() => fracture.power({ host, seeds, maxWork: 100 }), /budget/);
});

test('bond loads accumulate across calls and detach the affected components', () => {
  const host = forms.superquadric({ radii: [1,0.65,0.5], exponents: [8,8] }),
    graph = fracture.power({ host, seeds: [
      { id: 'a', point: [-0.6,0,0] }, { id: 'b', point: [0,0,0] }, { id: 'c', point: [0.6,0,0] }
    ], bond: edge => edge.a === 'a' ? 1 : 2 }),
    a = JSON.stringify(['a','b']), b = JSON.stringify(['b','c']);
  assert.deepEqual(graph.bonds.map(edge => edge.id), [a,b]);
  const first = fracture.separate(graph, { loads: { [a]: 0.7, [b]: 0.5 } });
  assert.deepEqual(first.components, [['a','b','c']]);
  const second = fracture.separate(graph, { previous: first, loads: { [a]: 0.4, [b]: 0.1 } });
  assert.deepEqual(second.components, [['a'],['b','c']]);
  assert.deepEqual(second.broken, [a]);
  assert.equal(second.remaining[b], 1.4);
  assert.equal(graph.bonds[0].capacity, 1);
});

test('stress fronts follow the loaded region, branch deterministically and respect hard voids', () => {
  const options = { width: 42, height: 28, starts: [{ at: [3,9], energy: 1, angle: 0.3 }], seed: 28,
    stress: (x,z) => ({ load: Math.abs(z - (8 + x * 0.23)) < 3 ? 0.92 : 0.22, direction: [1,0.23] }),
    toughness: (x,z) => Math.abs(z - (8 + x * 0.23)) < 3 ? 0.16 : 1.5,
    mask: (x,z) => x < 32 && x > 1 && z > 1 && z < 26,
    branching: 0.7, maxBranches: 5
  }, out = fracture.crack(options);
  assert.deepEqual(out, fracture.crack(options));
  assert(out.nodes.length > 28);
  assert(out.work.branches >= 2 && out.work.branches <= 5);
  assert(out.nodes.every(({ x,z }) => options.mask(x,z)));
  for (const { from, to } of out.edges) {
    assert.equal(out.nodes[to].parent, from);
    assert(from < to);
  }
  assert.equal(fracture.crack({ ...options, maxChecks: 8 }).status, 'budget');
});

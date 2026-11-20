const test = require('node:test');
const assert = require('node:assert/strict');
const { tiles } = require('..').load().KIT.procedural;

test('socket tiling respects pinned cells, authored network ports, masked cells, and seeded weights', () => {
  const model = tiles.compile([
    { id: 'blank', weight: 3 },
    { id: 'blank-2', weight: 1 },
    { id: 'street', sockets: { east: 'road', west: 'road' } },
    { id: 'bend-es', sockets: { east: 'road', south: 'road' } },
    { id: 'bend-nw', sockets: { north: 'road', west: 'road' } },
    { id: 'end-e', sockets: { east: 'road' } },
    { id: 'end-w', sockets: { west: 'road' } }
  ]),
    pins = [{ x: 0, z: 1, tile: 'end-e' }, { x: 3, z: 1, tile: 'end-w' }],
    ports = [0, 1, 2].map(x => ({ x, z: 1, direction: 'east', socket: 'road' })),
    options = {
      width: 4, height: 3, seed: 10, pins, ports,
      mask: (x, z) => x + z !== 0, boundary: { north: null, east: null, south: null, west: null }
    },
    result = tiles.solve(model, options);
  assert.equal(result.status, 'ok');
  assert.deepEqual(result.tiles, tiles.solve(model, options).tiles);
  assert.deepEqual(result.tiles.slice(4, 8), ['end-e', 'street', 'street', 'end-w']);
  assert.equal(result.at(0, 0), null);
  assert.equal(result.at(-1, 0), null);
  const byId = new Map(model.tiles.map(tile => [tile.id, tile]));
  for (let z = 0; z < result.height; z++)
    for (let x = 0; x < result.width - 1; x++) {
      const a = byId.get(result.at(x, z)), b = byId.get(result.at(x + 1, z));
      if (a && b) assert.equal(a.sockets.east, b.sockets.west);
    }
});

test('bounded backtracking escapes arc-consistent dead ends and distinguishes contradictions from budgets', () => {
  const a = { id: 'a', weight: 1e6, sockets: { east: 1, west: 0 } },
    b = { id: 'b', weight: 1e6, sockets: { east: 0, west: 1 } },
    c = { id: 'c', sockets: { east: 2, west: 2 } },
    opts = { width: 3, height: 1, wrap: [true, false] },
    model = tiles.compile([a, b, c]);
  const result = tiles.solve(model, opts);
  assert.equal(result.status, 'ok');
  assert.deepEqual(result.tiles, ['c', 'c', 'c']);
  assert(result.work.backtracks >= 1);
  assert.equal(tiles.solve(tiles.compile([a, b]), opts).status, 'contradiction');
  assert.equal(tiles.solve(model, { ...opts, maxBacktracks: 0 }).reason, 'backtracks');
  assert.equal(tiles.solve(model, { ...opts, maxWork: 1 }).reason, 'work');
  assert.equal(tiles.solve(model, { ...opts, width: 1 }).at(0, 0), 'c');
  const conflict = tiles.solve(model, { ...opts, pins: [{ x: 1, z: 0, tile: 'a' }, { x: 1, z: 0, tile: 'b' }] });
  assert.deepEqual(conflict.conflict, { x: 1, z: 0 });
});

test('overlapping synthesis reproduces every local swatch constraint, including pins at the output border', () => {
  const bank = tiles.learn(['ABAB', 'BABA', 'ABAB', 'BABA'], { size: 2, periodic: true, symmetry: true }),
    output = tiles.overlap(bank, { width: 10, height: 7, pins: [{ x: 9, z: 6, value: 'A' }] });
  assert.equal(output.status, 'ok');
  assert.equal(output.at(9, 6), 'A');
  const originals = new Set(bank.patterns.map(p => JSON.stringify(p.patch)));
  for (let z = 0; z < output.height - 1; z++)
    for (let x = 0; x < output.width - 1; x++) {
      const patch = [[output.at(x, z), output.at(x + 1, z)], [output.at(x, z + 1), output.at(x + 1, z + 1)]];
      assert(originals.has(JSON.stringify(patch)));
    }
  assert.equal(tiles.overlap(bank, { width: 5, height: 5, wrap: true }).status, 'contradiction');
});

test('world-aligned Wang tiles join across independent regions and report insufficient vocabularies', () => {
  const input = Array.from({ length: 16 }, (_, i) => ({
    id: String(i), sockets: { north: i & 1, east: (i >> 1) & 1, south: (i >> 2) & 1, west: (i >> 3) & 1 }
  }));
  const model = tiles.compile(input), setup = { height: 6, labels: [0, 1], seed: 12 },
    a = tiles.wang(model, { ...setup, origin: [-4, -2], width: 4 }),
    b = tiles.wang(model, { ...setup, origin: [0, -2], width: 5 }),
    full = tiles.wang(model, { ...setup, origin: [-4, -2], width: 9 });
  assert.equal(full.status, 'ok');
  for (let z = -2; z < 4; z++) {
    for (let x = -4; x < 5; x++) assert.equal(full.at(x, z), (x < 0 ? a : b).at(x, z));
    assert.equal(input[a.at(-1, z)].sockets.east, input[b.at(0, z)].sockets.west);
  }
  assert.equal(tiles.wang(tiles.compile(input.slice(0, 1)), { ...setup, width: 9 }).status, 'missing');
});

test('hierarchical tiling honors coarse motifs and solves remaining fine cells across their joins', () => {
  const coarse = tiles.solve(tiles.compile([{ id: 'house' }, { id: 'yard' }]), {
    width: 3, height: 1, mask: x => x !== 2, pins: [{ x: 0, z: 0, tile: 'house' }, { x: 1, z: 0, tile: 'yard' }]
  });
  const fine = tiles.compile([{ id: 'a' }, { id: 'b' }, { id: 'c' }]),
    result = tiles.refine(coarse, fine, {
      size: 2, template: id => id === 'house' ? ['a', ['b', 'c'], null, 'a'] : [null, 'b', 'b', null]
    });
  assert.equal(result.status, 'ok');
  assert.equal(result.width, 6);
  assert.equal(result.at(0, 0), 'a');
  assert.equal(result.at(1, 1), 'a');
  assert.equal(result.at(2, 1), 'b');
  assert.equal(result.at(4, 0), null);
});

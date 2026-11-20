const test = require('node:test');
const assert = require('node:assert/strict');
const { grammar, layouts } = require('..').load().KIT.procedural;

function reachable(cells, width, height) {
  const start = cells.findIndex(v => v === 1), found = new Set(start >= 0 ? [start] : []), queue = [...found];
  for (let i = 0; i < queue.length; i++) {
    const id = queue[i], x = id % width, z = Math.floor(id / width);
    for (const [u, v] of [[x-1,z],[x+1,z],[x,z-1],[x,z+1]]) {
      const p = v * width + u;
      if (u < 0 || v < 0 || u >= width || v >= height || !cells[p] || found.has(p)) continue;
      found.add(p);
      queue.push(p);
    }
  }
  return found.size;
}

test('probabilistic grid rewrites respect pins, wildcard matching, and reproducible seeds', () => {
  const rules = [
      { id: 'expand', find: ['a.'], replace: ['=a'], weight: 3 },
      { id: 'mark', find: ['a*'], replace: ['b='], weight: 1 }
    ],
    input = ['a........', 'a........'],
    opts = { seed: 11, steps: 30, pinned: [[2, 0]] },
    output = grammar.rewriteGrid(input, rules, opts);
  assert.deepEqual(output, grammar.rewriteGrid(input, rules, opts));
  assert.equal(output.rows[0][2], '.');
  assert(output.rows.flat().some(v => v === 'b'));
  assert(output.history.length > 2);
  assert.equal(grammar.rewriteGrid(input, rules, { ...opts, maxChecks: 1 }).status, 'budget');
});

test('graph rewrites match directed labeled edges and retain authored identities and external links', () => {
  const graph = { nodes: [{ id: 'a', type: 'port' }, { id: 'b', type: 'end' }, { id: 'c', type: 'service' }],
      edges: [{ from: 'a', to: 'b', type: 'rough' }, { from: 'a', to: 'c', type: 'outside' }] },
    rule = { id: 'vestibule', find: {
      nodes: [{ key: 'entry', type: 'port' }, { key: 'end', type: 'end' }],
      edges: [{ from: 'entry', to: 'end', type: 'rough' }]
    }, replace: {
      nodes: [{ key: 'entry' }, { key: 'end' }, { key: 'new', type: 'hall' }],
      edges: [{ from: 'entry', to: 'new', type: 'path' }, { from: 'new', to: 'end', type: 'path' }]
    } }, out = grammar.rewriteGraph(graph, [rule]);
  assert.equal(out.status, 'complete');
  assert.equal(out.work.steps, 1);
  assert.deepEqual(out, grammar.rewriteGraph(graph, [rule]));
  assert(out.nodes.some(v => v.id === 'a' && v.type === 'port'));
  assert(out.edges.some(e => e.type === 'outside' && e.from === 'a' && e.to === 'c'));
  assert(!out.edges.some(e => e.type === 'rough'));
  assert(out.edges.length === 3);
  assert(graph.edges.length === 2);
});

test('BSP rooms have disjoint footprints and a walkable connection to every room', () => {
  const map = layouts.bsp({ width: 42, height: 29, seed: 33, corridorWidth: 2 });
  assert(map.rooms.length > 7);
  assert.equal(map.corridors.length, map.rooms.length - 1);
  assert.equal(reachable(map.cells, map.width, map.height), map.cells.reduce((sum, v) => sum + v, 0));
  for (const [i, room] of map.rooms.entries()) for (const other of map.rooms.slice(i + 1))
    assert(room.bounds.max.some((v, axis) => v <= other.bounds.min[axis] || other.bounds.max[axis] <= room.bounds.min[axis]));
});

test('cave repair joins pinned cells and reports when a fixed barrier makes joining impossible', () => {
  const options = { width: 17, height: 11, seed: 7, minArea: 2, steps: 0, openChance: 0, open: [[3, 4], [14, 7]] },
    joined = layouts.cave(options),
    separate = layouts.cave({ ...options, mask: x => x !== 8 });
  assert.equal(joined.components, 1);
  assert.equal(joined.connections.length, 1);
  assert.equal(reachable(joined.cells, joined.width, joined.height), joined.cells.reduce((sum, v) => sum + v, 0));
  assert.equal(separate.status, 'disconnected');
  assert.equal(separate.components, 2);
  assert.equal(separate.cells[4 * separate.width + 3], 1);
  assert.equal(separate.cells[7 * separate.width + 14], 1);
});

test('adjacency floor plans produce real shared walls and respect pinned rooms', () => {
  const rooms = [{ id: 'lobby', size: [4, 3] }, { id: 'lab', size: [3, 2], rotate: true }, { id: 'store', size: [2, 2] }],
    pins = [{ id: 'lobby', at: [3, 2] }],
    layout = layouts.floorPlan(rooms, { width: 10, height: 8, pins,
      adjacencies: [{ a: 'lobby', b: 'lab', span: 2 }, { a: 'lab', b: 'store', span: 1 }]
    });
  assert.equal(layout.status, 'ok');
  assert.deepEqual(layout.rooms[0].bounds.min, [3, 2]);
  for (const { wall: [a, b], span } of layout.doors) assert(Math.hypot(a[0]-b[0], a[1]-b[1]) >= span);
  const impossible = layouts.floorPlan(rooms, { width: 10, height: 8, pins, adjacencies: [{ a: 'lobby', b: 'store', span: 4 }] });
  assert.equal(impossible.status, 'contradiction');
});

test('packing rotates an item to fit remaining space and respects keep-outs', () => {
  const packed = layouts.pack([{ id:'cabinet', size:[3,1], rotate:true }, { id:'bench', size:[2,2] }], {
    width: 3, height: 3, blocked: (x,z) => z === 2 && x > 0
  });
  assert.equal(packed.status, 'ok');
  assert.equal(packed.placements[0].rotated, true);
  assert.deepEqual(packed.placements[0].bounds, { min:[0,0], max:[1,3] });
  assert.equal(layouts.pack([{ id:'a',size:[2,2] }], { width:3,height:3,blocked:()=>true }).status, 'contradiction');
});

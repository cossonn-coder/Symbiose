const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const { grammar } = KIT.procedural;
const box = (width = 6) => ({ min: [-width / 2, 0, 0], max: [width / 2, 3, 1] });
const emit = role => ({ op: 'emit', role });

test('shape grammar fits fixed and flexible splits, insets, and named sockets into the scope', () => {
  const rules = {
    top: { op: 'split', axis: 'y', parts: [
      { key: 'base', size: 0.4, use: emit('base') },
      { key: 'body', weight: 2, use: { op: 'inset', margin: [0.2, 0, 0.1], use: 'piece' } },
      { key: 'trim', size: 0.2, use: emit('trim') }
    ] },
    piece: { op: 'group', children: [
      { key: 'block', use: emit('wall') },
      { key: 'anchor', use: { op: 'socket', name: 'hanger', axis: 'z', side: 'min', at: [0.75, 0.25, 1] } }
    ] }
  };
  const result = grammar.expand({ id: 'front', symbol: 'top', bounds: box() }, rules);
  assert.deepEqual(result.parts.map(p => p.role), ['base', 'wall', 'trim']);
  assert.deepEqual(result.parts[1].bounds.min, [-2.8, 0.4, 0.1]);
  assert.deepEqual(result.parts[1].bounds.max, [2.8, 2.8, 0.9]);
  assert.deepEqual(result.sockets[0].normal, [0, 0, -1]);
  assert(Math.abs(result.sockets[0].point[0] - 1.4) < 1e-10);
  assert.equal(result.sockets[0].point[2], 0.1);
  assert(!Object.isFrozen(rules));
});

test('pinned openings keep exact spans and edited bays retain identity across adding more bays', () => {
  const rules = {
    wall: { op: 'repeat', axis: 'x', pitch: 1.25, gap: 0.035, pinSet: 'doors', use: 'bay', pinUse: 'door' },
    bay: emit('window'),
    door: emit('door')
  };
  const doc = KIT.authoring.document(),
    owner = doc.create('front'),
    door = { id: 'red-door', at: -0.13, span: 1.2 };
  function setWidth(width) {
    const layout = grammar.expand({ id: 'front', symbol: 'wall', bounds: box(width) }, rules, { pinSets: { doors: [door] } });
    doc.derive(owner, 'layout', grammar.children(layout));
    return layout;
  }
  const a = setWidth(5.4),
    oldDoor = doc.entities('grammarPart').find(e => e.parameters.role === 'door'),
    oldBay = doc.entities('grammarPart').filter(e => e.parameters.role === 'window' && e.parameters.center[0] < door.at).at(-1);
  doc.update(oldBay.id, { parameters: { paint: 'teal' } });
  const b = setWidth(9.8);
  assert(b.parts.length > a.parts.length);
  assert.deepEqual(doc.get(oldDoor.id).parameters.bounds, oldDoor.parameters.bounds);
  assert.equal(doc.get(oldBay.id).parameters.paint, 'teal');
  assert.notDeepEqual(doc.get(oldBay.id).parameters.bounds, oldBay.parameters.bounds);
  assert.equal(doc.get(oldBay.id).seed, oldBay.seed);
  const start = door.at - door.span / 2,
    end = door.at + door.span / 2;
  for (const p of b.parts.filter(p => p.role === 'window')) {
    assert(p.bounds.max[0] <= start || p.bounds.min[0] >= end);
  }
  assert.equal(KIT.authoring.document(doc.serialize()).get(oldBay.id).parameters.paint, 'teal');
});

test('weighted grammar choices repeat deterministically and infeasible scopes fail promptly', () => {
  const scope = { id: 'sample', symbol: 'main', bounds: box() },
    choices = { main: { op: 'choice', options: [
      { key: 'wood', weight: 1, use: emit('wood') },
      { key: 'stone', weight: 2, use: emit('stone') }
    ] } };
  assert.deepEqual(grammar.expand(scope, choices, { seed: 19 }), grammar.expand(scope, choices, { seed: 19 }));
  assert.throws(() => grammar.expand(scope, { main: 'main' }, { maxDepth: 5 }), /depth budget/);
  assert.throws(() => grammar.expand(scope, { main: { op: 'split', axis: 'x', parts: [{ key: 'bad', size: 7, use: emit('wall') }] } }), /do not fit/);
  assert.throws(() => grammar.expand(scope, { main: {
    op: 'repeat', axis: 'x', pitch: 1, pins: [{ id: 'a', at: 0, span: 2 }, { id: 'b', at: 0.5, span: 2 }], use: emit('wall')
  } }), /overlap/);
});

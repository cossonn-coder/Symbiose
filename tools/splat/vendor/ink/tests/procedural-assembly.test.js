const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: K } = require('..').load();
const { construct, routes, grammar } = K.procedural;
const near = (a, b) => assert(Math.abs(a - b) < 1e-8, a + ' differs from ' + b);

test('socket assembly honors oriented compatibility and stretches modules to exactly meet pins', () => {
  const carrier = routes.polyline([[0,0,0],[5.1,0,0],[5.1,0,4.2]]),
    catalog = [
      { id: 'entry', length: 1, in: 'landing', out: 'track' },
      { id: 'bay', length: 2, min: 1.6, max: 2.4, in: 'groove', out: 'track' },
      { id: 'upper', length: 1, in: 'terminal', out: 'track', reversible: true }
    ],
    opts = { start: 'landing', end: 'terminal', joins: [['track','groove']],
      pins: [{ id: 'angle', at: 5.1 / carrier.length, in: 'track', out: 'track' }], seed: 3
    },
    result = grammar.assemble(carrier, catalog, opts);
  assert.equal(result.status, 'ok');
  assert.deepEqual(result.parts.map(x => x.module), ['entry','bay','bay','bay','bay','upper']);
  near(result.parts[2].t1, opts.pins[0].at);
  near(result.parts[2].end.point[0], 5.1);
  assert.equal(result.parts.at(-1).reversed, true);
  assert.deepEqual(result.parts.at(-1).end.point, [5.1,0,4.2]);
  assert.deepEqual(grammar.assemble(carrier, catalog, opts), result);
  assert.equal(grammar.assemble(carrier, catalog, { ...opts, joins: [] }).status, 'contradiction');
  assert.equal(grammar.assemble(carrier, catalog, { ...opts, maxChecks: 1 }).status, 'budget');
});

test('pinned spans reserve enough modules for later mandatory pieces', () => {
  const carrier = routes.polyline([[0,0,0],[8,0,0]]);
  const result = grammar.assemble(carrier, [
    { id: 'cheap', length: 2, in: 'west', out: 'west', cost: 0.1 },
    { id: 'west-cap', length: 2, in: 'west', out: 'pin', cost: 0.1 },
    { id: 'longer', length: 4, in: 'west', out: 'pin', cost: 10 },
    { id: 'first-east', length: 2, in: 'east', out: 'east-next' },
    { id: 'second-east', length: 2, in: 'east-next', out: 'end' }
  ], { start: 'west', end: 'end', maxParts: 3, pins: [{ id: 'passage', at: 0.5, in: 'pin', out: 'east' }] });
  assert.equal(result.status, 'ok');
  assert.deepEqual(result.parts.map(p => p.module), ['longer','first-east','second-east']);
});

test('load paths fit between ground keep-outs, share a post, and preserve total line load', () => {
  const sockets = [{ id: 'left', point: [0,2.2,0], bearing: true }, { id: 'joint', point: [4,2.2,0] },
      { id: 'right', point: [8,2.2,0], bearing: true }],
    spans = [{ id: 'west', a: 'left', b: 'joint', load: 1 }, { id: 'east', a: 'joint', b: 'right', load: 1.9 }],
    result = construct.loadPaths(sockets, spans, { ground: x => x > 2.42 && x < 3.34 ? null : 0,
      maxSpan: 2.6, postStep: 0.25
    });
  assert.equal(result.status, 'ok');
  assert(result.braces.length >= 3);
  const joint = result.bearings.find(b => b.key === '["socket","joint"]');
  assert.deepEqual(joint.spans, ['west','east']);
  assert(result.bearings.filter(b => b.column).every(b => !(b.base[0] > 2.42 && b.base[0] < 3.34)));
  near(result.bearings.reduce((sum, b) => sum + b.load, 0), 4 * 1 + 4 * 1.9);
  const impossible = construct.loadPaths(sockets, spans, { ground: () => null });
  assert.equal(impossible.status, 'unsupported');
  assert.equal(impossible.beams.length, 0);
});

test('damage cascades through missing support and keeps pinned part identity', () => {
  const input = [
    { key: 'column', role: 'support' }, { key: 'wall', role: 'infill' },
    { key: 'window', role: 'glazing' }, { key: 'flag', role: 'accent' }
  ], config = {
    rules: [{ id: 'lose-base', role: 'support', to: 'missing' }, { id: 'chip', role: 'accent', to: 'patched' }],
    supports: [{ child: 'wall', by: ['column'] }, { child: 'window', by: ['wall'] }],
    pins: [{ key: 'window' }], steps: 2, seed: 4
  }, result = construct.damage(input, config), byKey = Object.fromEntries(result.states.map(s => [s.key,s]));
  assert.deepEqual(result, construct.damage(input, config));
  assert.equal(byKey.column.state, 'missing');
  assert.equal(byKey.wall.state, 'collapsed');
  assert.equal(byKey.window.state, 'intact');
  assert.equal(byKey.window.supported, false);
  assert.equal(byKey.flag.state, 'patched');
  assert.equal(result.events.find(event => event.key === 'wall').cause, 'support');
  const cycle = [{ child: 'wall', by: ['column'] }, { child: 'column', by: ['wall'] }];
  assert.throws(() => construct.damage(input, { ...config, supports: cycle }), /acyclic/);
});

test('shape grammars build multi-volume massing around an authored courtyard opening', () => {
  const emit = role => ({ op: 'emit', role }),
    outer = grammar.expand({ id: 'quad', symbol: 'quad', bounds: { min: [0,0,0], max: [8,4,6] } }, {
      quad: { op: 'split', axis: 'z', parts: [
        { key: 'south', size: 1, use: emit('arcade') },
        { key: 'middle', use: 'wings' },
        { key: 'north', size: 1, use: emit('gallery') }
      ] },
      wings: { op: 'split', axis: 'x', parts: [
        { key: 'west', size: 1.5, use: emit('tower') },
        { key: 'open', use: { op: 'socket', name: 'court', axis: 'y', side: 'min' } },
        { key: 'east', size: 1.5, use: emit('tower') }
      ] }
    });
  assert.equal(outer.parts.length, 4);
  assert(!outer.parts.some(p => K.procedural.spatial.contains(p.bounds, [4,1,3])));
  assert.deepEqual(outer.sockets[0].point, [4,0,3]);
});

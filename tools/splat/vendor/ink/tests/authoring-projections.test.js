const test = require('node:test'),
  assert = require('node:assert/strict'),
  A = require('..').load().KIT.authoring;
const spec = (height = 1) => [
    { key: 'kept', type: 'piece', parameters: { height, color: 'red' } },
    { key: 'other', type: 'piece', parameters: { height: 2 } }
  ],
  job = specs => [{ owner: 'root', rule: 'parts', specs }];
function setup() {
  const d = A.document();
  d.create('group', { id: 'root' });
  d.create('group', { id: 'unrelated' });
  d.transact('Generate', () => d.derive('root', 'parts', spec()));
  return d;
}
function compare(d, specs) {
  const source = d.snapshot(),
    serialized = d.serialize(),
    expected = A.document(source);
  expected.transact('Project', () => expected.derive('root', 'parts', specs));
  const out = A.projectDerived(source, job(specs));
  assert.deepEqual(out, expected.snapshot());
  assert.equal(d.serialize(), serialized);
  return out;
}
test('pure derivation preserves overrides, original seeds and document transaction results', () => {
  const d = setup(),
    id = A.data.derivedId('root', 'parts', 'kept');
  d.update(id, { parameters: { color: 'blue', extra: true } });
  const old = d.get(id);
  const out = compare(d, spec(4));
  assert.equal(out.entities[id].parameters.height, 4);
  assert.equal(out.entities[id].parameters.color, 'blue');
  assert.equal(out.entities[id].parameters.extra, true);
  assert.equal(out.entities[id].seed, old.seed);
  assert.deepEqual(out.entities[id].overrides, old.overrides);
});
test('projection preserves promoted and suppressed slots and prunes obsolete attachment closures', () => {
  const d = setup(),
    kept = A.data.derivedId('root', 'parts', 'kept'),
    other = A.data.derivedId('root', 'parts', 'other');
  d.create('piece', { id: 'child', anchor: { host: other, surface: 'front', uv: [0.5, 0.5] } });
  let out = compare(d, [spec()[0]]);
  assert(!out.entities.other && !out.entities[other] && !out.entities.child);
  d.promote(kept);
  d.remove(other);
  out = compare(d, spec(9));
  assert(!out.entities[kept].derived);
  assert.equal(out.entities[kept].parameters.height, 1);
  assert(!out.entities[other]);
});
test('unchanged projections retain identity and changed projections share unaffected immutable records', () => {
  const d = setup(),
    s = d.snapshot();
  assert.equal(A.projectDerived(s, job(spec())), s);
  assert.equal(A.projectDerived(s, []), s);
  const p = A.projectDerived(s, job(spec(3))),
    id = A.data.derivedId('root', 'parts', 'kept');
  assert.equal(p.entities.root, s.entities.root);
  assert.equal(p.entities.unrelated, s.entities.unrelated);
  assert.equal(p.styles, s.styles);
  assert.notEqual(p.entities[id], s.entities[id]);
  assert(Object.isFrozen(p) && Object.isFrozen(p.entities) && Object.isFrozen(p.entities[id].parameters));
  assert.equal(s.entities[id].parameters.height, 1);
  assert.equal(A.data.documentView(p), p);
});
test('validated document views detach external data and reject malformed pending snapshots', () => {
  const d = setup(),
    raw = JSON.parse(d.serialize()),
    view = A.data.documentView(raw);
  raw.entities.root.parameters.changed = true;
  assert(!view.entities.root.parameters.changed);
  assert(Object.isFrozen(view.entities.root.parameters));
  assert.equal(A.data.documentView(d.snapshot()), d.snapshot());
  d.begin('Invalid parent');
  d.update('root', { parent: 'missing' });
  assert.throws(() => A.data.documentView(d.snapshot()), /Missing or self parent/);
  d.cancel();
  assert.doesNotThrow(() => A.data.documentView(d.snapshot()));
  raw.entities.root.parameters.value = NaN;
  assert.throws(() => A.data.documentView(raw), /finite JSON/);
});
test('failed projection jobs are atomic and apply the same graph and key validation as documents', () => {
  const d = setup(),
    s = d.snapshot(),
    serial = d.serialize();
  for (const jobs of [
    [{ owner: 'missing', rule: 'parts', specs: [] }],
    [{ owner: 'root', rule: 'parts', specs: [{ key: 'a', type: 'piece', parent: 'missing' }] }],
    job([
      { key: 'a', type: 'piece' },
      { key: 'a', type: 'piece' }
    ]),
    [...job(spec(6)), { owner: 'missing', rule: 'parts', specs: [] }],
    Array(257).fill(job([])[0])
  ]) {
    assert.throws(() => A.projectDerived(s, jobs));
    assert.equal(d.serialize(), serial);
    assert.equal(s.entities[A.data.derivedId('root', 'parts', 'kept')].parameters.height, 1);
  }
  assert.deepEqual(A.projectDerived(s, job(spec(5))), A.projectDerived(JSON.parse(serial), job(spec(5))));
});

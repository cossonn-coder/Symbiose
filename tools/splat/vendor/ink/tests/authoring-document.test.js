const test = require('node:test');
const assert = require('node:assert/strict');
const { authoring: A, procedural: P } = require('..').load().KIT;

test('a drag, generated consequences, undo, redo and reload preserve exact choices', () => {
  const d = A.document();
  const wall = d.create('envelope', { parameters: { width: 4, height: 3 } });
  d.beforeCommit(doc => {
    const w = doc.get(wall);
    if (w)
      doc.derive(wall, 'opening', [
        {
          key: 'route-crossing',
          type: 'opening',
          anchor: { host: wall, surface: 'facade', uv: [0.5, 0.4] },
          parameters: { width: w.parameters.width / 3, variant: 'paired' }
        }
      ]);
  });
  const before = d.serialize();
  d.begin('Resize building');
  for (let i = 5; i <= 8; i++) d.update(wall, { parameters: { width: i } });
  const preview = d.preview();
  assert.equal(Object.keys(preview.entities).length, 2);
  assert.equal(d.history().undo.length, 1);
  d.commit();
  const after = d.serialize(),
    opening = d.entities('opening')[0];
  assert.equal(opening.parameters.width, 8 / 3);
  assert.equal(d.history().undo.at(-1), 'Resize building');
  d.undo();
  assert.equal(d.serialize(), before);
  d.redo();
  assert.equal(d.serialize(), after);
  const loaded = A.document(d.serialize());
  assert.equal(loaded.serialize(), after);
  assert.equal(loaded.get(opening.id).seed, opening.seed);
  d.update(wall, { parameters: { height: 5 } });
  assert.equal(d.entities('opening')[0].id, opening.id);
});

test('generated overrides, promotion and suppression survive repeated generation and history', () => {
  const d = A.document(),
    host = d.create('envelope');
  const generate = () =>
    d.derive(host, 'clutter', [{ key: 'sill/left', type: 'prop', parameters: { asset: 'planter', scale: 1 } }])[0];
  const id = generate();
  d.update(id, { parameters: { asset: 'urn', scale: 2 } });
  generate();
  assert.deepEqual(d.get(id).parameters, { asset: 'urn', scale: 2 });
  d.promote(id);
  assert.equal(d.get(id).derived, undefined);
  assert.equal(generate(), undefined);
  assert.equal(d.entities('prop').length, 1);
  d.remove(id);
  assert.equal(generate(), undefined);
  d.allow(host, 'clutter', 'sill/left');
  assert.equal(generate(), id);
  d.suppress(id);
  generate();
  assert.equal(d.get(id), null);
  d.undo();
  assert(d.get(id));
});

test('removing a host deletes anchored, parented and generated dependents atomically', () => {
  const d = A.document(),
    host = d.create('envelope');
  const opening = d.create('opening', { anchor: { host, surface: 'side', uv: [0.25, 0.5] } });
  const [prop] = d.derive(opening, 'props', [{ key: 'sill', type: 'prop' }]);
  const before = d.serialize();
  assert.deepEqual(new Set(d.remove(host)), new Set([host, opening, prop]));
  assert.equal(d.entities().length, 0);
  d.undo();
  assert.equal(d.serialize(), before);
});

test('invalid references, cycles and non-JSON values roll back the whole transaction', () => {
  const d = A.document(),
    a = d.create('group'),
    b = d.create('group', { parent: a });
  const before = d.serialize();
  for (const fn of [
    () => d.update(a, { parent: b }),
    () => d.update(b, { styleRef: 'missing' }),
    () => d.create('opening', { anchor: { host: a, surface: 'side', uv: [NaN, 0] } }),
    () => d.update(a, { parameters: { fn() {} } }),
    () => d.update(a, JSON.parse('{"parameters":{"__proto__":{"oops":true}}}')),
    () => d.update(a, { id: 'renamed' }),
    () => d.transact('async', async () => {}),
    () =>
      d.transact('mixed', () => {
        d.update(a, { parameters: { changed: true } });
        d.create('prop', { parent: 'absent' });
      })
  ]) {
    assert.throws(fn);
    assert.equal(d.serialize(), before);
    assert.equal(d.pending(), false);
  }
  const snap = JSON.parse(before);
  snap.version = 9;
  assert.throws(() => A.document(snap), /version/);
});

test('getters are immutable, cancellation restores previews, no-op edits do not consume history', () => {
  const d = A.document(),
    id = d.create('envelope', { parameters: { width: 3 } });
  const history = d.history().undo.length;
  const obj = d.get(id);
  assert(Object.isFrozen(obj.parameters));
  obj.parameters.width = 99;
  assert.equal(d.get(id).parameters.width, 3);
  d.update(id, { parameters: { width: 3 } });
  assert.equal(d.history().undo.length, history);
  const seen = [];
  d.onPreview(e => seen.push(e.type));
  d.begin('Drag');
  d.update(id, { parameters: { width: 9 } });
  d.preview();
  d.cancel();
  assert.equal(d.get(id).parameters.width, 3);
  assert.deepEqual(seen, ['preview', 'cancel']);
  assert.equal(d.history().undo.length, history);
  d.undo();
  d.create('tree');
  assert.equal(d.redo(), false);
});

test('bounded autosave journals recover reversibly and storage failure does not lose edits', () => {
  const memory = new Map(),
    storage = { getItem: key => memory.get(key) || null, setItem: (key, value) => memory.set(key, value) };
  const d = A.document().autosave(storage, 'test', { backups: 2 });
  const id = d.create('envelope', { parameters: { width: 1 } });
  for (let width = 2; width <= 5; width++) d.update(id, { parameters: { width } });
  assert.equal(d.backups().length, 3);
  const reopened = A.document().autosave(storage, 'test', { backups: 2 });
  const oldest = reopened.backups()[0].id;
  reopened.recover(2);
  assert.equal(reopened.get(id).parameters.width, 5);
  reopened.recover(oldest);
  assert.equal(reopened.get(id).parameters.width, 3);
  reopened.undo();
  assert.equal(reopened.get(id).parameters.width, 5);
  const quota = A.document().autosave(
    {
      getItem: () => null,
      setItem() {
        throw new Error('quota');
      }
    },
    'q'
  );
  const kept = quota.create('tree');
  assert(quota.get(kept));
  assert.match(quota.storageError.message, /quota/);
  assert.throws(() => A.document().autosave({ getItem: () => '{bad', setItem() {} }, 'corrupt'));
});

test('seeds and generated ids are independent of traversal order and encoded slot punctuation', () => {
  const a = A.document(),
    b = A.document();
  a.create('group', { id: 'x/y' });
  a.create('group', { id: 'x' });
  b.create('group', { id: 'x' });
  b.create('group', { id: 'x/y' });
  assert.equal(a.get('x').seed, b.get('x').seed);
  const [one] = a.derive('x/y', 'a', [{ key: 'b', type: 'prop' }]);
  const [two] = a.derive('x', 'y/a', [{ key: 'b', type: 'prop' }]);
  assert.notEqual(one, two);
  assert.equal(A.data.derivedId('x/y', 'a', 'b'), one);
});

test('failed resolvers roll back author intent and all partially generated children', () => {
  const d = A.document(),
    host = d.create('envelope'),
    before = d.serialize();
  d.beforeCommit(doc => {
    doc.derive(host, 'rule', [{ key: 'one', type: 'prop' }]);
    throw new Error('bad rule');
  });
  assert.throws(() => d.update(host, { parameters: { width: 99 } }), /bad rule/);
  assert.equal(d.serialize(), before);
  assert.equal(d.history().undo.length, 1);
});

test('immutable read views reuse unchanged values and isolate every pending edit', () => {
  const input = { height: 3, shape: { width: 4 } },
    d = A.document();
  d.setStyle('garden', { materials: { stone: '#abcabc' } });
  const a = d.create('mass', { id: 'a', parameters: input }),
    b = d.create('mass', { id: 'b' });
  const original = d.snapshot(),
    saved = JSON.stringify(original);
  input.shape.width = 99;
  assert.strictEqual(d.snapshot(), original);
  assert.strictEqual(d.get(a), original.entities[a]);
  assert.strictEqual(d.entities()[0], original.entities[a]);
  assert(Object.isFrozen(original.entities[a].parameters.shape));
  assert(Object.isFrozen(d.entities()));
  d.begin('Drag');
  d.update(a, { parameters: { height: 6 } });
  const first = d.snapshot();
  assert.notStrictEqual(first, original);
  assert.strictEqual(first.entities[b], original.entities[b]);
  assert.strictEqual(first.styles.garden, original.styles.garden);
  assert.strictEqual(first.environment, original.environment);
  assert.equal(first.entities[a].parameters.shape.width, 4);
  assert.equal(first.entities[a].parameters.height, 6);
  assert.strictEqual(d.snapshot(), first);
  d.update(a, { parameters: { height: 6 } });
  assert.strictEqual(d.snapshot(), first, 'equal writes do not discard field caches');
  d.update(a, { parameters: { height: 7 } });
  const second = d.snapshot();
  assert.equal(first.entities[a].parameters.height, 6);
  assert.equal(second.entities[a].parameters.height, 7);
  assert.equal(JSON.stringify(original), saved);
  d.cancel();
  assert.deepEqual(d.snapshot(), original);
  assert.strictEqual(d.snapshot(), d.snapshot());
});

test('generated suppression, restoration and promotion never mutate an earlier view', () => {
  const d = A.document(),
    host = d.create('mass', { id: 'host' });
  const specs = [{ key: 'left', type: 'detail', parameters: { chosen: 'urn' } }];
  const [child] = d.derive(host, 'decor', specs),
    start = d.snapshot();
  d.begin('Generated editing');
  d.remove(child);
  const removed = d.snapshot();
  assert(removed.entities[host].overrides.suppressed);
  assert.equal(removed.entities[child], undefined);
  assert.equal(start.entities[host].overrides.suppressed, undefined);
  assert(start.entities[child].derived);
  d.allow(host, 'decor', 'left');
  const allowed = d.snapshot();
  assert.deepEqual(allowed.entities[host].overrides.suppressed, {});
  assert.equal(Object.keys(removed.entities[host].overrides.suppressed).length, 1);
  d.derive(host, 'decor', specs);
  const regenerated = d.snapshot();
  d.derive(host, 'decor', specs);
  assert.strictEqual(d.snapshot(), regenerated);
  d.promote(child, { parameters: { chosen: 'vase' } });
  const promoted = d.snapshot();
  assert.equal(promoted.entities[child].derived, undefined);
  assert.equal(promoted.entities[child].parameters.chosen, 'vase');
  assert.equal(regenerated.entities[child].parameters.chosen, 'urn');
  assert(regenerated.entities[child].derived);
  assert.deepEqual(regenerated.entities[host].overrides.suppressed, {});
  d.commit();
  assert.strictEqual(d.snapshot(), promoted);
  d.undo();
  assert.deepEqual(d.snapshot(), start);
  d.redo();
  assert.deepEqual(d.snapshot(), promoted);
});

test('style maps, environment, restores and failed resolution invalidate read views before observers run', () => {
  const d = A.document(),
    id = d.create('mass'),
    original = d.snapshot();
  const seen = [];
  d.onChange(() => seen.push(d.snapshot()));
  d.setStyle('temp', { materials: { stone: '#abcabc' } });
  const styled = d.snapshot();
  assert.strictEqual(seen.at(-1), styled);
  assert.equal(original.styles.temp, undefined);
  d.setStyle('temp', { materials: { stone: '#abcabc' } });
  assert.strictEqual(d.snapshot(), styled);
  d.removeStyle('temp');
  const removed = d.snapshot();
  assert.equal(removed.styles.temp, undefined);
  assert(styled.styles.temp);
  d.setEnvironment({ weather: { wind: 2 } });
  const windy = d.snapshot();
  assert.equal(windy.environment.weather.wind, 2);
  assert.equal(removed.environment.weather, undefined);
  d.restore(original);
  assert.deepEqual(d.snapshot(), original);
  const stop = d.beforeCommit(doc => {
    doc.update(id, { parameters: { failed: true } });
    doc.snapshot();
    throw new Error('bad hook');
  });
  assert.throws(() => d.update(id, { parameters: { width: 9 } }), /bad hook/);
  assert.deepEqual(d.snapshot(), original);
  stop();
  const stopPreview = d.beforeCommit(doc => {
    doc.update(id, { parameters: { failed: true } });
    doc.snapshot();
    throw new Error('bad preview');
  });
  d.begin('Preview');
  d.update(id, { parameters: { width: 7 } });
  assert.throws(() => d.preview(), /bad preview/);
  assert.deepEqual(d.snapshot(), original);
  stopPreview();
  d.begin('Create draft');
  const beforeCreate = d.snapshot();
  const created = d.create('detail');
  assert.equal(d.snapshot().nextId, beforeCreate.nextId + 1);
  assert(d.snapshot().entities[created]);
  assert.equal(beforeCreate.entities[created], undefined);
  d.cancel();
});


test('history reuses untouched records and preserves version-one recovery bytes', () => {
  let stored = null;
  const d = A.document().autosave({
    getItem: () => stored,
    setItem(_, value) {
      stored = value;
    }
  }, 'glade', { backups: 3 });
  const untouched = d.create('mesh', { parameters: { vertices: [[0, 0, 0], [1, 0, 0]] } });
  const edited = d.create('mass', { parameters: { width: 2 } });
  const initial = d.snapshot(), events = [];
  d.onChange(event => events.push(event.changed));

  d.begin('Resize');
  d.update(edited, { parameters: { width: 8 } });
  d.preview();
  d.cancel();
  assert.strictEqual(d.get(untouched), initial.entities[untouched]);
  assert.strictEqual(d.get(edited), initial.entities[edited]);

  d.update(edited, { parameters: { width: 3 } });
  const committed = d.snapshot();
  d.undo();
  assert.strictEqual(d.get(untouched), initial.entities[untouched]);
  assert.strictEqual(d.get(edited), initial.entities[edited]);
  d.redo();
  assert.strictEqual(d.get(edited), committed.entities[edited]);
  d.update(untouched, { parameters: { vertices: [[7, 0, 0]] } });
  assert.deepEqual(initial.entities[untouched].parameters.vertices, [[0, 0, 0], [1, 0, 0]]);
  assert.deepEqual(events, [[edited], [edited], [edited], [untouched]]);

  const journal = JSON.parse(stored);
  assert.equal(journal.version, 1);
  assert.deepEqual(journal.entries, d.backups());
  const previous = journal.entries.map(entry => JSON.stringify(entry));
  d.flush();
  assert.equal(stored, JSON.stringify(journal));
  d.update(edited, { parameters: { width: 4 } });
  assert.deepEqual(JSON.parse(stored).entries.slice(0, -1).map(entry => JSON.stringify(entry)), previous.slice(1));

  const beforeRestore = d.serialize(),
    reordered = JSON.parse(beforeRestore);
  reordered.entities = Object.fromEntries(Object.entries(reordered.entities).reverse());
  d.restore(reordered);
  assert.equal(d.serialize(), JSON.stringify(reordered));
  assert(d.undo());
  assert.equal(d.serialize(), beforeRestore);
});

test('scheduled resolution publishes one retained revision and preserves undo and autosave',async()=>{
  const d=A.document(),saved=new Map(),resolve=draft=>{
    const worker=A.document(draft);
    worker.derive('host','roofs',[{key:'cover',type:'roof'}]);
    return worker.snapshot();
  };
  d.create('house',{id:'host'});
  d.create('house',{id:'neighbor'});
  d.autosave({getItem:key=>saved.get(key),setItem:(key,value)=>saved.set(key,value)},'world');
  const before=d.snapshot(),revision=d.revision(),changes=[];
  d.onChange(event=>changes.push(event));
  d.begin('Resize house');
  d.update('host',{parameters:{width:7}});
  let finish;
  const pending=d.scheduleCommit(draft=>new Promise(done=>{finish=()=>done(resolve(draft));}));
  assert.equal(d.revision(),revision);
  assert.equal(d.get('host').parameters.width,7);
  assert.equal(saved.size,0);
  finish();
  assert.equal(await pending,true);
  assert.equal(d.revision(),revision+1);
  assert.equal(d.get('neighbor'),before.entities.neighbor);
  assert.deepEqual(changes.map(event=>event.type),['commit']);
  assert.equal(d.entities('roof').length,1);
  assert.equal(JSON.parse(saved.get('world')).entries.at(-1).snapshot.entities.host.parameters.width,7);
  d.undo();
  assert.deepEqual(d.snapshot(),before);
  d.redo();
  assert.equal(d.entities('roof').length,1);
});

test('new writes, cancellation and worker failure settle pending edits without accepting stale replies',async()=>{
  const d=A.document();
  d.create('item',{id:'item',parameters:{value:1}});
  d.beforeCommit(doc=>{
    const value=doc.get('item').parameters.value;
    doc.derive('item','label',[{key:'label',type:'label',parameters:{value}}]);
  });
  const set=value=>{d.begin('Set value');d.update('item',{parameters:{value}});};
  let complete;
  set(2);
  const old=d.scheduleCommit(draft=>new Promise(done=>{complete=()=>done(draft);}));
  set(3);
  complete();
  assert.equal(await old,false);
  d.cancel();
  assert.equal(d.entities('label')[0].parameters.value,2);
  assert.equal(d.get('item').parameters.value,2);
  set(4);
  const cancelled=d.scheduleCommit(draft=>new Promise(done=>{complete=()=>done(draft);}));
  d.cancel();
  complete();
  assert.equal(await cancelled,false);
  assert.equal(d.get('item').parameters.value,2);
  set(5);
  assert.equal(await d.scheduleCommit(async()=>{throw Error('worker stopped');}),true);
  assert.equal(d.entities('label')[0].parameters.value,5);
});

test('patches validate references and retain unchanged document records', () => {
  const doc = A.document();
  const host = doc.create('envelope', { id: 'tower' });
  const door = doc.create('opening', { id: 'door', parent: host, parameters: { width: 1 } });
  const before = A.data.documentView(doc.snapshot());
  const update = { ...before.entities[door], parameters: { width: 2 } };
  const after = A.data.patchDocumentView(before, { upserts: { [door]: update }, metadata: { nextId: 3 } });
  update.parameters.width = 10;
  assert.equal(after.entities[door].parameters.width, 2);
  assert.equal(before.entities[door].parameters.width, 1);
  assert.equal(after.entities[host], before.entities[host]);
  assert.equal(after.styles, before.styles);
  assert.equal(after.nextId, 3);
  assert.equal(A.data.documentView(after), after);
  assert.throws(() => A.data.patchDocumentView(after, { removed: [host] }), /Missing or self parent/);
  assert.throws(() => A.data.patchDocumentView(before, { metadata: { entities: {} } }), /Invalid document view patch/);
  assert.deepEqual(Object.keys(A.data.patchDocumentView(after, { removed: [door] }).entities), [host]);
});

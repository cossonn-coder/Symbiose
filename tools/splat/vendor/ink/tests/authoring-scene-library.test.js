const test = require('node:test');
const assert = require('node:assert/strict');
const A = require('..').load().KIT.authoring;

function memory() {
  const values = new Map();
  const getItem = key => values.get(key) ?? null;
  return {
    getItem,
    setItem: (key, value) => values.set(key, value),
    removeItem: key => values.delete(key),
    compareAndSet(key, before, value) {
      if (getItem(key) !== before) return false;
      values.set(key, value);
      return true;
    }
  };
}
const library = storage => A.sceneLibrary.create(storage, { key: 'gallery', backups: 4 });

test('adopt a prior journal, open separate glades, archive, restore and recover per scene', () => {
  const storage = memory();
  const old = A.document().autosave(storage, 'legacy');
  old.create('tree', { id: 'first' });
  old.create('tree', { id: 'second' });
  const raw = storage.getItem('legacy');
  const shelf = library(storage);
  const original = shelf.adopt({ id: 'courtyard', name: 'Courtyard', journal: 'legacy' });
  assert.equal(shelf.state().active, 'courtyard');
  assert.equal(storage.getItem('legacy'), raw);
  assert.equal(original.doc.entities().length, 2);

  const blank = shelf.create(' Meadow ', A.document().snapshot());
  blank.doc.create('wall', { id: 'fence' });
  assert.equal(blank.slot.name, 'Meadow');
  assert.equal(shelf.state().active, blank.slot.id);
  assert.throws(() => shelf.archive(blank.slot.id), /Open another scene/);
  shelf.open(original.slot.id);
  shelf.rename(blank.slot.id, 'Water meadow');
  shelf.archive(blank.slot.id);
  assert.throws(() => shelf.open(blank.slot.id), /archive/);
  shelf.unarchive(blank.slot.id);
  const reopened = library(storage).open(blank.slot.id);
  assert.equal(reopened.slot.name, 'Water meadow');
  assert.ok(reopened.doc.get('fence'));
  reopened.doc.recover(reopened.doc.backups()[0].id);
  assert.equal(reopened.doc.entities().length, 0);
  reopened.doc.undo();
  assert.ok(reopened.doc.get('fence'));
  assert.equal(library(storage).open('courtyard').doc.entities().length, 2);
});

test('stale saves and failed gallery writes preserve the latest readable document', () => {
  const storage = memory(), shelf = library(storage);
  const first = shelf.create('Cabin', A.document().snapshot());
  const second = library(storage).open(first.slot.id);
  first.doc.create('tree', { id: 'outside' });
  second.doc.create('tree', { id: 'pending' });
  assert.match(second.doc.storageError.message, /another session/);
  assert.ok(second.doc.get('pending'));
  assert.deepEqual(shelf.open(first.slot.id).doc.entities().map(e => e.id), ['outside']);

  const before = shelf.state();
  const compare = storage.compareAndSet;
  storage.compareAndSet = (key, ...args) => key === 'gallery' ? false : compare(key, ...args);
  assert.throws(() => shelf.create('Second cabin', A.document().snapshot()), /another session/);
  assert.deepEqual(shelf.state(), before);
  assert.equal(storage.getItem('gallery/scene-2'), null);
  storage.compareAndSet = compare;
  assert.equal(shelf.create('Second cabin', A.document().snapshot()).slot.name, 'Second cabin');
});

test('prepare saved and recovered snapshots before edits without rewriting the journal on open',()=>{
  const storage=memory(),legacy=A.document().autosave(storage,'legacy');
  legacy.create('tree',{id:'oak',parameters:{old:true}});
  legacy.update('oak',{parameters:{height:3}});
  const originalJournal=storage.getItem('legacy');
  const prepareSnapshot=snapshot=>{
    assert(Object.isFrozen(snapshot));
    const tree=snapshot.entities.oak;
    if(!tree?.parameters.old||tree.parameters.upgraded)return snapshot;
    const upgraded=A.data.merge(tree,{parameters:{upgraded:true}});
    return A.data.patchDocumentView(snapshot,{upserts:{oak:upgraded}});
  };
  const library=A.sceneLibrary.create(storage,{key:'gallery',prepareSnapshot});
  library.adopt({id:'orig',name:'Original',journal:'legacy'});
  const doc=library.open('orig').doc;
  assert.equal(storage.getItem('legacy'),originalJournal);
  assert.deepEqual(doc.history(),{undo:[],redo:[]});
  assert.equal(doc.get('oak').parameters.upgraded,true);
  doc.recover('save-1');
  assert.deepEqual(doc.get('oak').parameters,{old:true,upgraded:true});
  assert.deepEqual(doc.history().undo,['Restore document']);
  assert(doc.undo());
  assert.equal(doc.get('oak').parameters.height,3);
  assert.equal(library.open('orig').doc.get('oak').parameters.upgraded,true);
  assert.throws(()=>doc.restore({}),/version|document/i);
  assert.equal(doc.get('oak').parameters.height,3);
});

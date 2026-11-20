const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const A = KIT.authoring, T = KIT.procedural.transforms, G = A.groups;
const near = (a,b) => a.forEach((v,i)=>assert(Math.abs(v-b[i])<1e-8,`${v} != ${b[i]}`));

function scene() {
  const doc=A.document();
  const house=doc.create('volume',{id:'home',parameters:{transform:{position:[-2,.1,0],rotation:[.2,.3,.4],scale:[1.3,.8,1]}}});
  doc.create('fence',{id:'fence',parameters:{transform:{position:[2,0,0]}}});
  const [roof]=doc.derive(house,'cover',[{key:'slope',type:'cover',parameters:{host:house,tiles:10}}]);
  doc.create('lamp',{id:'lamp',anchor:{host:roof,surface:'edge',uv:[.2,.8]},parameters:{binding:roof}});
  doc.update(roof,{parameters:{tiles:14}});
  return {doc,roof};
}

test('group capture transforms only independent roots and supports exact cancel, commit and undo',()=>{
  const {doc,roof}=scene(), before=doc.serialize();
  const ids=['lamp','home',roof,'fence'], graph=G.select(doc,ids);
  assert.deepEqual(graph.roots,['home','fence']);
  const plan=G.capture(doc,ids,{pivot:[0,0,0]}), change={yaw:Math.PI/2,translate:[0,1,0]};
  const desired=T.combine(G.delta(plan,change),T.local(doc.get('home').parameters.transform));
  doc.begin('Drag set');
  G.apply(doc,plan,change);
  near(T.local(doc.get('home').parameters.transform).R,desired.R);
  near(doc.get('home').parameters.transform.position,[0,1.1,2]);
  assert.equal(doc.get('lamp').anchor.host,roof);
  assert.equal(doc.get(roof).parameters.tiles,14);
  doc.cancel();
  assert.equal(doc.serialize(),before);
  G.apply(doc,plan,change);
  assert.equal(doc.history().undo.at(-1),'Transform group');
  doc.undo();
  assert.equal(doc.serialize(),before);
});

test('copy copies nested generated ownership, anchors, seeds and overrides with one undo',()=>{
  const {doc,roof}=scene(), before=doc.serialize(), plan=G.capture(doc,['home']);
  const copied=G.copy(doc,['home'],{
    plan,change:{translate:[4,0,0]},
    remap(fields,ref){
      for(const key of ['host','binding'])if(fields.parameters[key])fields.parameters[key]=ref(fields.parameters[key]);
      return fields;
    }
  });
  const {home,lamp}=copied.ids, cover=copied.ids[roof];
  assert.notEqual(home,'home');
  assert.equal(cover,A.data.derivedId(home,'cover','slope'));
  assert.equal(doc.get(cover).parameters.host,home);
  assert.equal(doc.get(cover).seed,doc.get(roof).seed);
  assert.equal(doc.get(cover).overrides.parameters.tiles,14);
  assert.equal(doc.get(lamp).anchor.host,cover);
  assert.equal(doc.get(lamp).parameters.binding,cover);
  assert.deepEqual(doc.get(home).parameters.transform.position,[2,.1,0]);
  doc.undo();
  assert.equal(doc.serialize(),before);
  assert.throws(()=>G.copy(doc,[roof]),/owner/);
  assert.throws(()=>G.copy(doc,['home'],{remap(){throw Error('bad copy');}}),/bad copy/);
  assert.equal(doc.serialize(),before);
});

test('bookmarks keep missing memberships through removal, undo and serialization',()=>{
  const {doc,roof}=scene();
  G.remember(doc,['home','fence','home'],{id:'yard',name:'Yard'});
  assert.deepEqual(G.bookmarks(A.document(doc.serialize()))[0].active,['home','fence']);
  assert(G.remove(doc,['home']).includes(roof));
  assert.deepEqual(G.bookmarks(doc)[0].active,['fence']);
  assert.deepEqual(G.bookmarks(doc)[0].members,['home','fence']);
  doc.undo();
  assert.deepEqual(G.bookmarks(doc)[0].active,['home','fence']);
  assert(G.forget(doc,'yard'));
  assert.deepEqual(G.bookmarks(doc),[]);
});

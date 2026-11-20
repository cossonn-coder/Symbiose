const test=require('node:test'),assert=require('node:assert/strict');
const {authoring:A}=require('..').load().KIT;
function catalog(){
  return A.environmentProfiles.create({key:'biome',defaultId:'soil',defaults:{air:{mix:.2,wind:[1,0]}},
    profiles:[{id:'soil',label:'Soil',values:{}},{id:'shore',label:'Shore',values:{air:{mix:.4}}}],
    validate(value){if(value.air.mix<0||value.air.mix>1)throw Error('Invalid mix');}});
}
test('environment selection retains independent overrides and never mutates authored entities',()=>{
  const modes=catalog(), doc=A.document(), id=doc.create('tree',{parameters:{position:[1,2,3]}});
  doc.setEnvironment({presentation:{grade:2},ground:{height:1}});
  const before=doc.get(id);
  assert.equal(modes.resolve(doc).id,'soil');
  modes.select(doc,'shore');
  modes.edit(doc,{air:{wind:[0,2],mix:.7}});
  modes.select(doc,'soil');
  assert.deepEqual(modes.resolve(doc).values.air,{mix:.2,wind:[1,0]});
  modes.select(doc,'shore');
  assert.equal(doc.get(id),before);
  assert.deepEqual(modes.resolve(doc).values.air,{mix:.7,wind:[0,2]});
  assert.equal(doc.snapshot().environment.presentation.grade,2);
  assert.equal(doc.snapshot().environment.ground.height,1);
  modes.reset(doc);
  assert.equal(modes.resolve(doc).values.air.mix,.4);
  doc.undo();
  assert.equal(modes.resolve(doc).values.air.mix,.7);
  const reopened=A.document(doc.serialize());
  assert.deepEqual(catalog().resolve(reopened).values.air,{mix:.7,wind:[0,2]});
});
test('validation precedes edits, and missing profile IDs resolve to the default',()=>{
  const modes=catalog(), doc=A.document();
  const before=doc.serialize();
  assert.throws(()=>modes.edit(doc,{air:{mix:2}}),/Invalid mix/);
  assert.throws(()=>modes.select(doc,'other'),/Unknown/);
  assert.equal(doc.serialize(),before);
  doc.setEnvironment({presentation:{profiles:{biome:{active:'other'}}}});
  assert.equal(modes.resolve(doc).id,'soil');
  assert.equal(modes.resolve(doc).missing,true);
  modes.select(doc,'shore');
  assert.equal(modes.resolve(doc).missing,false);
});

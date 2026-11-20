const test=require('node:test');
const assert=require('node:assert/strict');
const {assetCatalog}=require('..').load().KIT.procedural;

test('asset searches rank labels ahead of metadata and filter through accents, categories and pages',()=>{
  const catalog=assetCatalog.create([
    {id:'catalog/planter',label:'Fern planter',subtitle:'Cobalt urn',categories:['Containers'],keywords:['Kiln garden']},
    {id:'catalog/urn',label:'Cóbalt urn',categories:['Kiln garden'],keywords:['Ceramics']},
    {id:'catalog/lamp',label:'Porcelain lamp',categories:['Kiln garden'],keywords:['Ceramics']}
  ]);
  const ids=options=>catalog.search(options).items.map(item=>item.id);
  assert.deepEqual(catalog.categories,['Containers','Kiln garden']);
  assert.deepEqual(ids({query:'COBALT-URN'}),['catalog/urn','catalog/planter']);
  assert.deepEqual(ids({query:'céRam'}),['catalog/urn','catalog/lamp']);
  assert.deepEqual(ids({query:'kiln cobalt',category:'Containers'}),['catalog/planter']);
  assert.deepEqual(ids({query:'cobalt',offset:1,limit:1}),['catalog/planter']);
  assert.equal(catalog.search({query:'cobalt',offset:1,limit:1}).total,2);
  assert.deepEqual(ids({query:'wooden'}),[]);
  assert.equal(catalog.get('catalog/planter').label,'Fern planter');
});

test('asset catalog snapshots only metadata, with one entry per stable identity',()=>{
  const entry={id:'part',label:'Part',categories:['Bench'],keywords:['Garden'],recipe:{triangles:[0,1,2]}};
  const catalog=assetCatalog.create([entry]);
  entry.categories.push('Chairs');
  assert.deepEqual(catalog.categories,['Bench']);
  assert.equal(catalog.get('part').recipe,undefined);
  assert.throws(()=>assetCatalog.create([entry,entry]),/unique IDs/);
  assert.throws(()=>catalog.search({limit:0}),/bounded page/);
});

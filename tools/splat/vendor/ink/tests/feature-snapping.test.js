const test=require('node:test'),assert=require('node:assert/strict');
const {snapping}=require('..').load().KIT.procedural;

test('feature snapping uses finite rotated segments and selected coordinates',()=>{
  const feature={id:'edge',owner:'terrace',from:[0,5,0],to:[2,7,2]};
  const options={axes:[0,2],tolerance:.18};
  const hit=snapping.resolve([1.1,-3,.9],[feature],options);
  assert.equal(hit.feature,feature);
  assert.deepEqual(hit.point,[1,-3,1]);
  assert.equal(hit.t,.5);
  assert.equal(snapping.resolve([2.2,-3,2.2],[feature],options),null);
  assert.equal(snapping.resolve([1.1,-3,.9],[feature]),null);
  assert.deepEqual(snapping.resolve([2.1,-3,2.1],[feature],options).point,[2,-3,2]);
});

test('feature priorities and stable ties select a single source',()=>{
  const corner={id:'a',from:[.15,0,.1],priority:1},edge={id:'b',from:[.03,0,0]},
    other={...corner,id:'c'};
  for(const order of [[corner,edge,other],[other,edge,corner]])
    assert.equal(snapping.resolve([0,0,0],order).feature,corner);
  assert.equal(snapping.resolve([0,0,0],[corner,edge],{tolerance:.12}).feature,edge);
  assert.throws(()=>snapping.resolve([0,0,0],[corner,corner]),/unique/);
});

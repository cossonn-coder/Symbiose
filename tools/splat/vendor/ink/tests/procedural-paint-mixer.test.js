const test=require('node:test'),assert=require('node:assert/strict');
const {paintMixer}=require('..').load().KIT.procedural.materials;

test('ordered paint and erasure leave the correct contributions and background',()=>{
 const layers=[
  {id:'base',coverage:()=>1},
  {id:'detail',coverage:()=>.5},
  {id:'erase',operation:'erase',coverage:(x,y)=>x>0?.5:1},
  {id:'refill',coverage:()=>.25}
 ];
 const field=paintMixer(layers);
 assert.deepEqual(field.sample(1,0),{
  contributions:[{id:'refill',weight:.25},{id:'detail',weight:.1875},{id:'base',weight:.1875}],background:.375
 });
 assert.deepEqual([.1,.51,.7,.9].map(rank=>field.pick(1,0,rank)),['refill',null,'detail','base']);
 assert.deepEqual(field.sample(-1,0),{contributions:[{id:'refill',weight:.25}],background:.75});
 assert.deepEqual(paintMixer(layers.slice(0,2).reverse()).sample(1,0),{contributions:[{id:'base',weight:1}],background:0});
});

test('opaque paint short-circuits earlier masks and invalid coverage is rejected',()=>{
 const field=paintMixer([{id:'old',coverage:()=>{throw Error('read hidden mask');}},{id:'top',coverage:()=>1}]);
 assert.equal(field.pick(2,4,.99),'top');
 assert.deepEqual(field.sample(2,4),{contributions:[{id:'top',weight:1}],background:0});
 assert.equal(paintMixer([]).pick(0,0,.5),null);
 assert.throws(()=>field.pick(1,2,1),/rank/);
 assert.throws(()=>paintMixer([{id:'a',coverage:()=>1.1}]).sample(1,2),/coverage/);
 assert.throws(()=>paintMixer([{id:'a',coverage:()=>1},{id:'a',coverage:()=>1}]),/unique/);
});

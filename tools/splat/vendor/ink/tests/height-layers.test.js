const test = require('node:test');
const assert = require('node:assert/strict');
const { heightLayers, procedural } = require('..').load().KIT;

function layer(id, operation, height, width, point = [0, 0]) {
  const shape = procedural.masks.stroke({ id, points:[point], width, softness:0 });
  const bounds = {
    min:[shape.bounds.min[0] - 1, 0, shape.bounds.min[2] - 1],
    max:[shape.bounds.max[0] + 1, 0, shape.bounds.max[2] + 1]
  };
  const feather = operation === 'erase' ? 0 : 1;
  return {
    entity:{ id }, parameters:{ operation, height }, bounds,
    weight:(x,z) => Math.max(0, 1 - Math.max(0, shape.distance([x,z]))),
    support:(x,z) => shape.distance([x,z]) - feather
  };
}

test('ordered height layers feather down to the base and permit a later contribution inside an erase', () => {
  const hill = layer('hill', 'add', 4, 10);
  const cut = layer('cut', 'min', -2, 10);
  const erase = layer('erase', 'erase', 0, 2);
  const layers = [hill, cut, erase];
  assert.deepEqual(heightLayers.sample(layers, 0, 0), { delta:0, owner:null, coverage:0 });
  assert.deepEqual(heightLayers.sample(layers, 1.5, 0), { delta:-1, owner:'cut', coverage:0.5 });
  assert.deepEqual(heightLayers.sample(layers, 4, 0), { delta:-2, owner:'cut', coverage:1 });
  assert(heightLayers.distance(layers, 0, 0) > 0);
  assert(heightLayers.distance(layers, 0, 0, 'cut') > 0);
  assert(heightLayers.distance(layers, 1.5, 0, 'cut') < 0);
  assert.equal(heightLayers.distance(layers, 0, 0, 'erase'), Infinity);
  layers.push(layer('paint', 'add', 1, 0.5));
  assert.deepEqual(heightLayers.sample(layers, 0, 0), { delta:1, owner:'paint', coverage:1 });
  assert(heightLayers.distance(layers, 0, 0) < 0);
  assert(heightLayers.distance(layers, 0, 0, 'paint') < 0);
  assert.equal(heightLayers.sample(layers, 5.5, 0).delta, -1);
});

test('composition reorder uses free ranks and preserves unrelated layers',()=>{
  const records=Object.freeze([{id:'hill',order:0},{id:'restore',order:1},{id:'far',order:2}].map(Object.freeze));
  const patch=heightLayers.reorder(records,'restore',0);
  assert.deepEqual(patch,[{id:'restore',order:0},{id:'hill',order:1}]);
  const ranks=new Map(patch.map(p=>[p.id,p.order]));
  assert.deepEqual(records.map(p=>({...p,order:ranks.get(p.id)??p.order})).sort(heightLayers.compareOrder)
    .map(p=>p.id),['restore','hill','far']);
  assert.deepEqual(heightLayers.reorder(records,'hill',0),[]);
  assert.deepEqual(heightLayers.reorder([{id:'hill',order:2},{id:'restore',order:5}],'restore',0),
    [{id:'restore',order:1}]);
});

test('legacy tied ranks and safe integer boundaries still produce the requested order',()=>{
  const cases=[
    [{id:'a',order:0},{id:'b',order:0},{id:'c',order:0}],
    [{id:'a',order:0},{id:'b',order:Number.MAX_SAFE_INTEGER},{id:'c',order:Number.MAX_SAFE_INTEGER}]
  ];
  for(const input of cases) for(const record of input) for(let index=0;index<input.length;index++){
    const patch=heightLayers.reorder(input,record.id,index);
    const ranks=new Map(patch.map(p=>[p.id,p.order]));
    const actual=input.map(p=>({...p,order:ranks.get(p.id)??p.order})).sort(heightLayers.compareOrder);
    const expected=input.filter(p=>p.id!==record.id);
    expected.splice(index,0,record);
    assert.deepEqual(actual.map(p=>p.id),expected.map(p=>p.id));
    assert(patch.every(p=>Number.isSafeInteger(p.order)&&p.order>=0));
  }
  assert.throws(()=>heightLayers.reorder([{id:'a',order:0}],'missing',0),/existing ID/);
});

test('ordered masks edit an individual replacement before the stack is composed', () => {
  const lower=layer('lower','add',2,8),upper=layer('upper','replace',5,8);
  const eraser=layer('eraser','erase',0,2),repair=layer('repair','add',0,.5);
  const cut=heightLayers.mask(upper,[{operation:'cut',weight:eraser.weight,support:eraser.support}]);
  assert.equal(heightLayers.mask(upper,[]),upper);
  assert.deepEqual(heightLayers.sample([lower,cut],0,0),{delta:2,coverage:1,owner:'lower'});
  assert.equal(heightLayers.sample([lower,cut],1.5,0).delta,3.5);
  assert(heightLayers.distance([lower,cut],0,0,'upper')>0);
  const restored=heightLayers.mask(upper,[
    {operation:'cut',weight:eraser.weight,support:eraser.support},
    {operation:'repair',weight:repair.weight,support:repair.support}
  ]);
  assert.equal(heightLayers.sample([lower,restored],0,0).delta,5);
  assert(heightLayers.distance([lower,restored],0,0,'upper')<0);
  assert.equal(upper.weight(0,0),1);
  assert.throws(()=>heightLayers.mask(upper,[{operation:'unsupported'}]),/cut or repair fields/);
});

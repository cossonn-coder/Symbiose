const test=require('node:test');
const assert=require('node:assert/strict');
const {clipPaintDomain}=require('..').load().KIT.procedural;

const field={
  bounds:{min:[-3,2,-3],max:[3,4,3]},
  distanceAt:(x,z)=>Math.hypot(x,z)-3,
  owner:()=> 'stroke',
  weight:()=>.75,
  visibleDistance:(_id,[x,z])=>Math.hypot(x,z)-3,
  sample:([x,z])=>({distance:Math.hypot(x,z)-3,owner:'stroke',weight:.75})
};
const domain={bounds:{min:[-8,0,-6],max:[1,0,6]},distanceAt:x=>x-1};

test('intersection bounds paint queries while retaining original data and height bounds',()=>{
  const paint=clipPaintDomain(field,domain);
  assert.equal(paint.raw,field);
  assert.deepEqual(paint.bounds,{min:[-3,2,-3],max:[1,4,3]});
  assert.deepEqual(paint.sample([0,0]),{distance:-1,owner:'stroke',weight:.75});
  assert.deepEqual(paint.sample([2,0]),{distance:1,owner:null,weight:0});
  assert.equal(paint.visibleDistance('stroke',[2,0]),1);
  assert.equal(paint.owner([2,0]),null);
  assert.equal(paint.weight([2,0]),0);
  assert.equal(paint.contains([2,0]),false);
  assert.equal(paint.contains([0,0]),true);
  assert.equal(paint.distanceAt(2,0,0),0);
  assert.equal(paint.distanceAt(.75,0,-.5),-.5);
  const far={bounds:{min:[4,0,-1],max:[6,0,1]},distanceAt:x=>Math.max(4-x,x-6)};
  assert.equal(clipPaintDomain(field,far).bounds,null);
  assert.equal(field.owner([2,0]),'stroke');
});

test('gate keeps the original profile inside and caps queries outside',()=>{
  const paint=clipPaintDomain(field,domain,{mode:'gate'});
  assert.equal(paint.distance([.75,0]),-2.25);
  assert.equal(paint.distanceAt(.75,0,-2.5),-2.5);
  assert.equal(paint.distanceAt(2,0,0),0);
  assert.equal(paint.distanceAt(2,0),Infinity);
  assert.equal(paint.visibleDistance('stroke',[2,0]),Infinity);
  assert.deepEqual(paint.sample([2,0]),{distance:Infinity,owner:null,weight:0});
});

const test=require('node:test');
const assert=require('node:assert/strict');
const {procedural:P}=require('..').load().KIT;

test('probe footprints cover nearby and overflow reads while excluding distant space',()=>{
  const record=P.spatial.probeFootprint({cell:.5,budget:2});
  for(const x of [0,.1,2,4,5])record.record([x,0,0],.2);
  const footprint=record.seal();
  const box=(x,y,z)=>({min:[x,y,z],max:[x,y,z]});
  assert.equal(footprint.regions.length,3);
  assert(footprint.intersects(box(.29,.1,0)));
  assert(footprint.intersects(box(4.5,0,0)));
  assert(!footprint.intersects(box(7,0,0)));
  assert(!footprint.intersects(box(0,4,0)));
  record.record([9,0,0]);
  assert(!footprint.intersects(box(9,0,0)));
  assert(record.seal().intersects(box(9,0,0)));
  assert.throws(()=>record.record([0,0,0],-1),/radius/);
});

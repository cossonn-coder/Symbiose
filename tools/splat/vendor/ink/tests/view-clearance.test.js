const test=require('node:test'),assert=require('node:assert/strict');
const {viewClearance}=require('..').load().KIT.procedural;

test('the view corridor falls off radially and at the focus, and leaves geometry behind it intact',()=>{
  const f=viewClearance.compile({eye:[0,2,8],target:[0,2,0],radius:1,feather:1,endFade:2});
  assert.equal(f.opacityAt([0,2,4]),0);
  assert.equal(f.opacityAt([1.5,2,4]),.5);
  assert.equal(f.opacityAt([0,2,1]),.5);
  for(const point of [[0,2,9],[0,2,0],[0,2,-2],[2,2,4]])assert.equal(f.opacityAt(point),1);
});

test('orientation, finite reach and minimum opacity are independent of the renderer',()=>{
  const f=viewClearance.compile({eye:[0,0,0],target:[1,0,0],reach:6,opacity:.3});
  assert.deepEqual(f.axis,[1,0,0]);
  assert(Math.abs(f.opacityAt([4,0,0])-.3)<1e-9);
  assert.equal(f.opacityAt([7,0,0]),1);
  assert.throws(()=>viewClearance.compile({eye:[0,0,0],target:[0,0,0]}),/direction/);
  assert.throws(()=>f.opacityAt([0,0,Infinity]),/finite/);
});

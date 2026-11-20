const test=require('node:test'),assert=require('node:assert/strict');
const F=require('..').load().KIT.boundedFields;
test('convex query returns an exact max or a proof beyond its limit',()=>{
  const f=F.halfspaces([{normal:[1,0,0],offset:1},{normal:[0,1,0],offset:1},{normal:[0,0,-1],offset:0}]);
  assert.equal(f(2,3,0,.5),1);
  assert.equal(f(2,3,0),2);
  assert.equal(f(2,3,0,0),2);
  assert.equal(f(0,0,1),-1);
});
test('height masks skip heights only when the mask determines the exact maximum',()=>{
  let calls=0;
  const field=F.heightMask({height:(x,z)=>{calls++;return 1+x*x+z*z;},mask:(x,z)=>x-z,scale:()=>.4,minimumHeight:1,minimumScale:.4});
  assert.equal(field(1,1.9,0),1);
  assert.equal(field(0,-.1,0),0);
  assert.equal(calls,0);
  assert.equal(field(0,3,0),.8);
  assert.equal(field(0,-1,2),-2);
  assert.equal(calls,2);
});

test('sculpt probes use world-space bounds and preserve smooth-union distances',()=>{
  const { makeBuilder, makeSculpt }=require('..').load();
  const fields=[false,true].map(bounded=>{
    const S=makeSculpt(makeBuilder(3,[0,0xcccccc]));
    const opts=S.grp(.35);
    S.ball([0,0,0],[1,1,1],{r:[1]},opts);
    S.ball([1,0,0],[1,1,1],{r:[1]},{...opts,...(bounded?{lowerBound:(x,y,z,limit)=>{
      assert.equal(typeof limit,'number');
      return Math.max(Math.abs(x-1),Math.abs(y),Math.abs(z))-1;
    }}:{})});
    S.ready();
    return S.sdf;
  });
  for(let x=-3;x<=3;x+=.13)for(let y=-2;y<=2;y+=.21)
    assert.equal(fields[0](x,y,.34),fields[1](x,y,.34));
});
test('a floored union can skip the second distance without changing the answer', () => {
  const { boundedFields } = require('..').load().KIT;
  let probes = 0;
  const a = ([x]) => x;
  const b = ([x]) => { probes++; return 4 - x; };
  const field = boundedFields.unionFloor(a, b);
  assert.equal(field([1], 2), 2);
  assert.equal(probes, 0);
  assert.equal(field([4], 2), 2);
  assert.equal(field([1]), 1);
  assert.equal(probes, 2);
});

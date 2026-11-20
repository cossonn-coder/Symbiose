const {test}=require('node:test'),assert=require('node:assert/strict');
const {planSnapping:S}=require('..').load().KIT.procedural;

const box=(x=0,y=0,w=2,h=2)=>[[x,y],[x+w,y],[x+w,y+h],[x,y+h]];
const square=S.compile(box()),targets=[{id:'stationary',plan:square}];
const near=(actual,expected)=>actual.forEach((value,i)=>assert(Math.abs(value-expected[i])<1e-8));

test('translated plans meet at the full face and at finite corners',()=>{
  const face=S.align(square,[2.13,.4],targets);
  near(face.position,[2,.4]);
  near(face.guide[0],[2,.4]);near(face.guide[1],[2,2]);
  near(S.align(square,[1.89,.4],targets).position,[2,.4]);
  const corner=S.align(square,[2.12,2.1],targets);
  near(corner.position,[2,2]);
  near(corner.guide[0],[2,2]);near(corner.guide[1],[2,2]);
  assert.equal(S.align(square,[2.12,2.45],targets),null);
  assert.equal(S.align(square,[.65,.2],targets),null);
});

test('a selected constraint has its own release distance and deterministic ties',()=>{
  const lateral={id:'a',plan:S.compile(box(0,3.95))};
  const first=S.align(square,[2.1,.1],targets);
  const next=[2.28,.08];
  assert.equal(S.align(square,next,targets),null);
  near(S.align(square,next,targets,{latch:first.latch}).position,[2,.08]);
  assert.equal(S.align(square,[2.34,.08],targets,{latch:first.latch}),null);
  near(S.align(square,[2.17,1.88],[...targets,lateral],{latch:first.latch}).position,[2,1.88]);
  for(const order of [[targets[0],{id:'a',plan:square}],[{id:'a',plan:square},targets[0]]])
    assert.equal(S.align(square,[2.15,0],order).id,'a');
});

test('scaled and rotated plans align along their real projected carriers',()=>{
  const angle=.63,c=Math.cos(angle),s=Math.sin(angle),R=([x,y])=>[x*c-y*s,x*s+y*c],
    target=S.compile(box().map(R)),moving=S.compile(box(0,0,1,1.5).reverse().map(R));
  const hit=S.align(moving,R([2.095,-.3]),[{id:'rotated',plan:target}]);
  near(hit.position,R([2,-.3]));
  near(hit.guide[1],R([2,1.2]));
  const circle=S.compile(Array.from({length:48},(_,i)=>[Math.cos(i*Math.PI/24),Math.sin(i*Math.PI/24)]));
  const tangent=S.align(circle,[3.16,1],targets);
  near(tangent.position,[3,1]);
  near(tangent.guide[0],[2,1]);near(tangent.guide[1],[2,1]);
  assert.throws(()=>S.compile([[0,0],[4,0],[2,1],[4,2],[0,2]]),/convex/);
  assert.throws(()=>S.align(square,[0,0],[...targets,...targets]),/unique/);
});

test('one-parameter resizing aligns a face and keeps its fixed edge at the original coordinates',()=>{
  const moving=S.compileMotion(square,([x])=>[x/2,0]),
    fixed=[{id:'stop',plan:S.compile(box(3,.25,2,2))}];
  const hit=S.alignMotion(moving,.88,fixed);
  near([hit.value],[1]);
  const guide=hit.guide.slice().sort((a,b)=>a[1]-b[1]);
  near(guide[0],[3,.25]);near(guide[1],[3,2]);
  assert.equal(S.alignMotion(moving,1.29,fixed),null);
  near([S.alignMotion(moving,1.29,fixed,{latch:hit.latch}).value],[1]);
  assert.equal(S.alignMotion(moving,.88,fixed,{max:.95}),null);
  assert.equal(S.alignMotion(moving,.88,[{id:'past',plan:S.compile(box(3,2.3))}]),null);
  assert.equal(S.alignMotion(moving,.88,[{id:'fixed',plan:S.compile(box(-2,0))}]),null);
});

test('a rotating separating edge can meet a stationary corner during a resize',()=>{
  const trapezoid=S.compile([[0,0],[2,0],[2,2],[0,1]]),
    moving=S.compileMotion(trapezoid,([x])=>[x/2,0]),
    jewel=S.compile([[1,1.45],[1.1,1.7],[1,1.9],[.9,1.7]]);
  const hit=S.alignMotion(moving,.16,[{id:'jewel',plan:jewel}]);
  assert.equal(hit.latch.side,'moving');
  near([hit.value],[1/.45-2]);
  near(hit.guide[0],[1,1.45]);near(hit.guide[1],hit.guide[0]);
});

test('the nearer contact root wins when both the position and direction of a face change',()=>{
  const moving=S.compileMotion(square,([x,y])=>[.2*y,.35*x]),
    jewel=S.compile([[1.4,2.35],[1.55,2.7],[1.4,2.9],[1.25,2.7]]);
  const hit=S.alignMotion(moving,.93,[{id:'jewel',plan:jewel}],{min:0,max:2.7});
  assert.equal(hit.latch.side,'moving');
  near([hit.value],[1]);
  near(hit.guide[0],[1.4,2.35]);
});

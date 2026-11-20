const test = require('node:test');
const assert = require('node:assert/strict');
const P = require('..').load().KIT.procedural;
const square = [[-1,-1],[1,-1],[1,1],[-1,1]];
const pose = {R:[1,.35,0,0,1,0,0,0,1],t:[0,0,0]};
const near = (a,b) => assert(Math.abs(a-b)<1e-8, `${a} != ${b}`);

test('an inclined perimeter includes the horizontal sweep of the upper and lower section', () => {
  for (const outline of [square,square.slice().reverse()]) {
    const perimeter = P.geometry.inclinedPerimeter(outline,pose,{offset:.3,below:.21,above:.7});
    const xs = perimeter.poly.map(p=>p[0]), zs = perimeter.poly.map(p=>p[2]);
    near(Math.min(...xs),-1.3735);
    near(Math.max(...xs),1.545);
    near(Math.max(...zs),1.3);
    const trace = perimeter.poly.map((p,i)=>perimeter.lift(p,i*.31));
    assert(perimeter.allows(trace));
    for (const [i,p] of trace.entries()) perimeter.project(p).forEach((q,k)=>near(q,perimeter.poly[i][k]));
    // The same XZ position clears at the lower guide point and penetrates above it.
    assert.equal(perimeter.allows([[1.545,0,0],[1.545,1,0]]),false);
    // Two individually clear endpoints can still cross the intervening interior.
    assert.equal(perimeter.allows([[2,0,0],[-2,0,0]]),false);
  }
});

test('inclined perimeters accept tilted horizontal sections but reject an almost horizontal axis', () => {
  const tilt = P.transforms.local({position:[3,2,1],rotation:[.41,.2,-.29],scale:[1.25,.91,.76]});
  const perimeter = P.geometry.inclinedPerimeter(square,tilt,{offset:.5,above:.6,below:.2});
  assert(perimeter.allows(perimeter.poly.map((p,i)=>perimeter.lift(p,i*.46+1))));
  assert.throws(()=>P.geometry.inclinedPerimeter(square,P.transforms.local({rotation:[Math.PI/2,0,0]})),/horizontal/);
});

test('a tangent bounds an acute perimeter while retaining clearance and source edge identities',()=>{
  const tip=[6,0],outline=[[0,-.1],tip,[0,.1]],offset=.65;
  for(const ring of [outline,outline.slice().reverse()]){
    const {poly,sections}=P.geometry.convexPerimeter(ring,{offset,miterLimit:2});
    const index=sections.findIndex(span=>span.bevel);
    assert.equal(poly.length,4);
    assert.equal(sections[index].edge,ring.indexOf(tip));
    const a=poly[index],b=poly[(index+1)%poly.length];
    near(a[0],tip[0]+offset);
    near(b[0],tip[0]+offset);
    const field=P.geometry.profileDistance(ring);
    for(let i=0;i<poly.length;i++)for(let j=0;j<=8;j++){
      const f=j/8,p=poly[i],q=poly[(i+1)%poly.length];
      assert(field(p[0]+(q[0]-p[0])*f,p[1]+(q[1]-p[1])*f)>=offset-1e-8);
    }
  }
  const swept=P.geometry.inclinedPerimeter(outline,pose,{offset,below:.2,above:.7,miterLimit:2});
  assert(swept.sections.some(span=>span.bevel));
  assert(swept.allows(swept.poly.map((p,i)=>swept.lift(p,.31*i))));
  assert.equal(swept.allows([[6.35,0,0]]),false);
});

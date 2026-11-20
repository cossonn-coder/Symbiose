const test=require('node:test'),assert=require('node:assert/strict');
const {panelRelief}=require('..').load().KIT.procedural;
const rect=(l,b,r,t)=>[[l,b],[r,b],[r,t],[l,t]];
const ring={key:'rim',material:'metal',polygon:rect(.15,.1,.85,.9),
  holes:[rect(.3,.3,.7,.7)],levels:[-.01,.03]};

test('closed panel relief fits normalized motifs and clips their recesses to a shaped outline',()=>{
  const outline=[[-1,-2],[1,-2],[1,.6],[0,2],[-1,.6]];
  const pieces=panelRelief({outline,layers:[ring],base:.2,depthScale:2});
  assert(pieces.length>=4);
  for (const [i,part] of pieces.entries()) {
    assert.equal(part.fragment,i);
    assert.equal(part.key,'rim');
    assert.equal(part.material,'metal');
    assert(Math.abs(part.lo-.18)<1e-9&&Math.abs(part.hi-.26)<1e-9);
    assert(part.outer.every(([x,y])=>Math.abs(x)<=.700001&&y<=2-Math.abs(x)*1.4+1e-8));
    assert(part.outer.every(([x,y])=>Math.abs(x)>=.399999||Math.abs(y)>=.799999));
  }
  assert(Object.isFrozen(pieces[0].outer));
  const scaled=panelRelief({outline:outline.map(([x,y])=>[x*2,y*2]),layers:[ring],base:.2,depthScale:2});
  assert.deepEqual(scaled.map(part=>[part.key,part.fragment,part.outer]),
    pieces.map(part=>[part.key,part.fragment,part.outer.map(([x,y])=>[x*2,y*2])]));
});

test('panel relief rejects invalid depths, duplicate keys and unbounded fragments',()=>{
  const setup={outline:rect(-1,-1,1,1)};
  assert.throws(()=>panelRelief({...setup,layers:[ring,ring]}),/unique/);
  assert.throws(()=>panelRelief({...setup,layers:[{...ring,levels:[1,0]}]}),/ordered levels/);
  assert.throws(()=>panelRelief({...setup,layers:[ring],budget:1}),/budget/);
});

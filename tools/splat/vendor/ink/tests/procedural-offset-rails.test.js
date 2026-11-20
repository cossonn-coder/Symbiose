const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT}=require('..').load(),{offsetRails,fittedRailBand}=KIT.procedural;

test('miters can share the length of a span without narrowing the whole entrance',()=>{
  const path=[[0,0,0],[1.56,0,0],[1.56,0,3.06],[-4,0,3.06],[-4,0,0],[-2.44,0,0]],halfWidth=1.44;
  const fitted=offsetRails({path,halfWidth,shareSpan:true});
  assert(fitted.contracted.every(value=>value===false));
  assert(offsetRails({path,halfWidth}).contracted[1]);
  for(let i=1;i<path.length;i++){
    const tangent=KIT.V.sub(path[i],path[i-1]);
    for(const rail of [fitted.left,fitted.right])
      assert(KIT.V.dot(KIT.V.sub(rail[i],rail[i-1]),tangent)>0);
  }
  const short=[[0,0,0],[1,0,0],[1,0,1],[-2,0,1]];
  const capped=offsetRails({path:short,halfWidth,shareSpan:true});
  assert(capped.contracted[1]&&capped.contracted[2]);
  assert(capped.right[2][2]>capped.right[1][2]);
});
const near=(a,b)=>assert(Math.abs(a-b)<1e-6,`${a} differs from ${b}`);

test('offset rails share a true miter while retaining independently tapered endpoints',()=>{
  const path=[[0,1,0],[3,1.2,0],[3,1.5,3]];
  const result=offsetRails({path,halfWidth:[.25,.52,.35]});
  assert.deepEqual(result.contracted,[false,false,false]);
  assert.deepEqual(result.left[0],[0,1,-.25]);
  assert.deepEqual(result.right[2],[2.65,1.5,3]);
  near(result.left[1][0],3.52);
  near(result.left[1][2],-.52);
  near(result.right[1][0],2.48);
  near(result.right[1][2],.52);
  near(result.left[1][1],1.2);
});

test('closed runs use the same first and last joint and acute stations remain bounded',()=>{
  const loop=[[0,0,0],[3,0,0],[3,.6,3],[0,0,3]],halfWidth=.4;
  const rails=offsetRails({path:loop,halfWidth,closed:true});
  near(rails.left[0][0],-.4);
  near(rails.left[0][2],-.4);
  const band=fittedRailBand({inner:rails.left,outer:rails.right,closed:true,
    measure:loop,pitch:20,direction:()=>[0,1,0],depth:[-.02,.14]});
  assert(band.pieces().every(part=>part.mesh.positions.every(Number.isFinite)));
  const capped=offsetRails({path:[[0,0,0],[1,0,0],[.005,0,.025]],halfWidth:1,miterLimit:1.5});
  assert(capped.contracted[1]);
  assert(KIT.V.dist(capped.left[1],[1,0,0])<=1.5);
  const cusp=offsetRails({path:[[0,0,0],[2,0,0],[0,0,0]],halfWidth:.25});
  assert.deepEqual(cusp.reversals,[1]);
  assert.throws(()=>offsetRails({path:[[0,0,0],[0,1,0]],halfWidth:.3}),/up plane/);
});

test('ribbon cuts use the measuring spine instead of the longer cap edge',()=>{
  const path=[[0,0,0],[2,0,0],[2,0,2]],rails=offsetRails({path,halfWidth:.5});
  const band=fittedRailBand({inner:rails.left,outer:rails.right,measure:path,pitch:1.3,
    depth:[0,.1],direction:()=>[0,1,0]});
  assert.equal(band.layout.length,4);
  assert.equal(band.layout.cells.length,3);
  assert(band.layout.cells[1].fragments.length===2);
  const railsOnly=fittedRailBand({inner:rails.left,outer:rails.right,pitch:1.3,
    depth:[0,.1],direction:()=>[0,1,0]});
  assert.equal(railsOnly.layout.length,5);
  assert.equal(railsOnly.layout.cells.length,4);
});

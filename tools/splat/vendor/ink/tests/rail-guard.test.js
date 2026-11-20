const test=require('node:test'),assert=require('node:assert/strict');
const {KIT}=require('..').load(),{railGuard,pieces,geometry}=KIT.procedural;

test('upright spans keep their height along a grade and cap at the supplied ends',()=>{
  const band=pieces.uprightSpan([0,1,0],[4,3,0],{width:.4,height:.8},{material:'stone'});
  const hit=band.intersections([.1,5,0],[0,-1,0]).map(hit=>hit.p[1]);
  assert(Math.abs(hit[0]-1.85)<1e-8);
  assert(Math.abs(hit[1]-1.05)<1e-8);
  assert(band.distance([.1,1.1,0])<0);
  assert(band.distance([-.01,1.1,0])>0);
  assert.equal(KIT.mesh.info(geometry.toKitMesh(band.mesh,()=>[.5,.5,.5])).open,0);
  const oriented=pieces.uprightSpan([0,0,1],[4,0,3],{width:.4,height:.8,up:[0,0,2],extension:.1});
  assert(oriented.distance([-.05,0,1.1])<0);
  assert(oriented.distance([-.15,0,1.1])>0);
  assert.throws(()=>pieces.uprightSpan([0,0,0],[0,1,0],{width:1,height:1}),/nonzero run/);
});

test('rail guards fit sloping runs, share corner posts and leave physical gaps between bars',()=>{
  const path=[[0,0,0],[.4,.2,0],[1,.5,0],[1,.5,1]],pieces=railGuard({path,postSpacing:.46},
    {key:'fence',material:'wood'});
  const bars=pieces.filter(p=>p.key.includes('/bar/')),posts=pieces.filter(p=>p.key.includes('/post/'));
  assert.equal(bars.length,4);
  assert.equal(posts.length,7);
  assert(pieces.every(p=>p.material==='wood'&&p.mesh.positions.every(Number.isFinite)));
  assert(posts.filter(p=>p.distance([1,.8,0])<0).length===1);
  assert(bars.some(p=>p.distance([.5,.89,0])<0));
  assert(!pieces.some(p=>p.distance([.53,.67,0])<0));
  assert.throws(()=>railGuard({path,maxPieces:4}),/piece budget/);
});

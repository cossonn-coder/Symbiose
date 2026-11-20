const { test } = require('node:test');
const assert = require('node:assert/strict');
const { fittedRailBand, pieces, offsetRails } = require('..').load().KIT.procedural;

test('a prepared face occlusion query preserves the union point test',()=>{
  const identity=[1,0,0,0,1,0,0,0,1],deck=pieces.box([0,0,0],[2,.1,1],identity,{key:'deck'}),
    cover=pieces.box([.45,.1,.2],[.7,.28,.5],[.8,0,.6,0,1,0,-.6,0,.8],{key:'cover'}),
    outside=pieces.box([4,.1,0],[.2,.2,.2],identity,{key:'outside'});
  const union=pieces.union([deck,cover,outside]),face=[[-2,.1,-1],[2,.1,-1],[2,.1,1],[-2,.1,1]];
  for(const depth of [0,.002,.12]){
    const hidden=union.faceOcclusion(deck.key,face,depth);
    assert.equal(typeof hidden,'function');
    for(let x=-1.97;x<2;x+=.069)for(let z=-.94;z<1;z+=.09){
      const point=[x,.1,z];
      assert.equal(hidden(point),union.hidden(deck.key,point,depth));
    }
  }
  const onlyDeck=pieces.union([deck,outside]);
  assert.equal(onlyDeck.faceOcclusion(deck.key,face),null);
});

test('bounded clearance ignores distant thin wedges without changing interior signs',()=>{
  const blade=pieces.convex([[0,0,0],[2,0,-.1],[2,0,.1],[0,.1,0],[2,.1,-.1],[2,.1,.1]],
    [[0,1,2],[3,4,5],[0,1,4,3],[1,2,5,4],[2,0,3,5]],{key:'blade'});
  const hull=pieces.union([blade]),outside=[-1,.05,0];
  assert(hull.distance(outside)<.1);
  assert.equal(hull.clearanceWithin(outside,.18),Infinity);
  assert.equal(hull.clearanceWithin(outside,2),1);
  const center=[1.8,.05,0];
  assert.equal(hull.clearanceWithin(center,.18),hull.distance(center));
  assert(hull.clearanceWithin(center,0)<0);
});

const spec = {
  inner: [[0, 0, 0], [2, 0, 0]],
  outer: [[0, 1, 0], [2, 1, 0]],
  pitch: 1,
  gap: 0.2,
  depth: [-0.1, 0.2],
  direction: () => [0, 0, 1]
};

test('fitted bands leave a real joint and make closed solids with stable cell ownership', () => {
  const band = fittedRailBand(spec);
  const parts = band.pieces({ owner: 'run', key: 'courses', material: 'trim' });
  assert.equal(parts.length, 2);
  assert.deepEqual(parts.map(p => p.cell), band.layout.cells.map(c => c.key));
  assert.deepEqual(parts.map(p => p.key), band.pieces({ key: 'courses' }).map(p => p.key));
  assert(parts.every(p => p.owner === 'run' && p.mesh.groups.every(g => g.material === 'trim')));
  const solid = pieces.union(parts);
  assert(solid.distance([0.4, 0.5, 0]) < 0);
  assert(solid.distance([1, 0.5, 0]) > 0);
  assert.equal(solid.raycast([1, 0.5, 1], [0, 0, -1]), null);
  assert(Math.abs(solid.raycast([0.4, 0.5, 1], [0, 0, -1]).distance - 0.8) < 1e-6);
});

test('warped paired rails produce finite prisms with a shared cell key', () => {
  const band = fittedRailBand({ ...spec, outer: [[0, 1, 0], [2, 1, 0.4]], pitch: 2 });
  const parts = band.pieces();
  assert.equal(parts.length, 2);
  assert.equal(parts[0].cell, parts[1].cell);
  assert.notEqual(parts[0].key, parts[1].key);
  assert(parts.every(p => p.mesh.positions.every(Number.isFinite)));
  assert.throws(() => fittedRailBand({ ...spec, direction: () => [0, 0, 0] }).pieces(), /direction/);
});

test('a band cell can override material and depth across all of its fragments', () => {
  const band = fittedRailBand({
    inner:[[0,0,0],[2,0,0],[4,0,0]],outer:[[0,1,0],[2,1,0],[4,1,0]],
    pitch:.5,depth:[-.06,.12],gap:.03,direction:()=>[0,0,1],
    sections:[{id:'first',end:.4},{id:'feature',end:.6,count:1},{id:'last',end:1}],
    cellStyle:cell=>cell.section==='feature'?{material:'polished',depth:[-.06,.26]}:null
  });
  const parts=band.pieces({owner:'test',material:'rough'});
  const featured=parts.filter(p=>p.section==='feature');
  assert.equal(featured.length,2);
  assert(featured.every(p=>p.cell==='feature/0'&&p.material==='polished'&&Math.abs(p.bounds.max[2]-.26)<1e-6));
  assert(parts.filter(p=>p.section!=='feature').every(p=>p.material==='rough'&&p.bounds.max[2]<.121));
});

test('profiled rail bands follow rising tapered corners with closed contact and physical picks',()=>{
  const path=[[0,0,0],[2,.5,0],[2,1.1,2]],width=[.7,.46,.8];
  const rails=offsetRails({path,halfWidth:width}),profile=[[0,-.05],[1,-.05],[1,.15],[.5,.51],[0,.15]];
  const band=fittedRailBand({inner:rails.left,outer:rails.right,measure:path,pitch:10,profile,direction:()=>[0,1,0]});
  const solids=band.pieces({key:'crest',owner:'wall'}),solid=pieces.union(solids);
  assert.equal(solids.length,2);
  assert(solids.every(part=>part.owner==='wall'&&part.cell==='0'&&part.mesh.positions.every(Number.isFinite)));
  const corner=path[1];
  for(const p of [[1.999,.78,0],corner.map((n,i)=>n+(i===1?.28:0)),[2,.78,.001]]){
    const hit=solid.raycast([p[0],4,p[2]],[0,-1,0]);
    assert(hit&&Math.abs(hit.p[1]-1.01)<.002);
  }
  const slope=solid.raycast([1,4,-.32],[0,-1,0]);
  assert(slope&&slope.p[1]>.40&&slope.p[1]<.75&&Math.abs(slope.n[2])>.12);
  assert.equal(solid.raycast([1,4,-.85],[0,-1,0]),null);
});

test('profile cells can vary independently and fitted joints remain open around a closed strip',()=>{
  const path=[[0,0,0],[2,.2,0],[2,.4,2],[0,.3,2]],
    rails=offsetRails({path,halfWidth:.32,closed:true}),
    base={inner:rails.left,outer:rails.right,measure:path,closed:true,pitch:1,
      gap:.1,direction:()=>[0,1,0],depth:[0,.16]},
    profile=[[0,0],[1,0],[1,.1],[.45,.37],[0,.1]];
  const band=fittedRailBand({...base,
    cellStyle:cell=>cell.index===1?{profile,material:'feature'}:null});
  const solids=band.pieces({material:'band'}),solid=pieces.union(solids);
  assert(solids.some(part=>part.material==='feature'&&part.bounds.max[1]>.43));
  assert.equal(solid.raycast([0,4,0],[0,-1,0]),null);
  assert(solid.raycast([1.5,4,0],[0,-1,0]).p[1]>.43);
  assert.throws(()=>fittedRailBand({...base,profile:[[0,0],[1,0],[.5,.1],[1,.6],[0,.6]]}),/convex/);
});

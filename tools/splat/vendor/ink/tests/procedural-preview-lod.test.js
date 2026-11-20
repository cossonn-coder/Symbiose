const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT:K}=require('..').load();
const {geometry,lod}=K.procedural;
const near=(a,b,e=1e-7)=>assert(Math.abs(a-b)<=e,a+' differs from '+b);

test('quadric simplification reduces a closed sphere and keeps its topology and pins',()=>{
  const field=(x,y,z)=>Math.hypot(x,y,z)-1,
    source=geometry.dualContour(field,{min:[-1.4,-1.4,-1.4],max:[1.4,1.4,1.4]},{cell:0.17}),
    result=geometry.simplifyQEM(source,{ratio:0.28,maxError:0.06,locked:[4,50]});
  assert.equal(result.status,'ok');
  assert(result.triangles.length<=source.triangles.length*0.28);
  assert(result.work.maxError<0.03);
  for(const i of [4,50])for(let axis=0;axis<3;axis++)
    near(result.points[result.pointMap[i]][axis],source.points[i][axis]);
  const edges=new Map();
  for(const face of result.triangles)for(let i=0;i<3;i++){
    const key=[face[i],face[(i+1)%3]].sort((a,b)=>a-b).join('/');
    edges.set(key,(edges.get(key)??0)+1);
  }
  assert([...edges.values()].every(n=>n===2));
  assert.equal(result.points.length-edges.size+result.triangles.length,2);
});

test('material seams and open borders retain their vertex positions during preview reduction',()=>{
  const size=7, points=Array.from({length:size*size},(_,i)=>[i%size,0,Math.floor(i/size)]), triangles=[],groups=[];
  for(let z=0;z<size-1;z++)for(let x=0;x<size-1;x++){
    const i=z*size+x;
    triangles.push([i,i+size,i+size+1],[i,i+size+1,i+1]);
    const material=x<3?'tile':'inlay';
    groups.push({owner:'floor',material},{owner:'floor',material});
  }
  const reduced=geometry.simplifyQEM({points,triangles},{ratio:0.68,groups});
  assert(reduced.work.collapsed>1);
  for(const [i,[x,_,z]] of points.entries()){
    if(x===3||x===0||z===0||x===6||z===6)assert.deepEqual(reduced.points[reduced.pointMap[i]],points[i]);
  }
  assert.deepEqual(new Set(reduced.mesh().groups.map(g=>g.material)),new Set(['tile','inlay']));
});

test('two Gaussian splats merge by moments and preserve their static representation',()=>{
  const field=(id,x)=>({id,position:[x,0,0],normal:[0,0,1],radius:0.045,opacity:0.43,color:[0.5,0.25,0.1]}),
    result=lod.mergeSplats([field('a',-0.05),field('b',0.05)],{target:1,maxDistance:0.21});
  assert.equal(result.status,'ok');
  assert.equal(result.splats.length,1);
  assert.deepEqual(result.splats[0].members,['a','b']);
  near(result.splats[0].position[0],0);
  near(result.splats[0].covariance[0],0.045**2+0.05**2);
  near(result.splats[0].covariance[3],0.045**2);
  const packed=lod.packSplats(result);
  assert(packed.data instanceof Float32Array);
  assert.equal(packed.data.length,16);
  near(packed.data[4],result.splats[0].covariance[0]);
});

test('Gaussian LOD locks silhouettes, owner edges, material seams and authored marks',()=>{
  const record=(id,x,extra={})=>({id,position:[x,0,0],normal:[0,0,1],radius:0.043,opacity:0.81,color:[0.46,0.5,0.55],
    owner:'a',material:'paint',...extra});
  const originals=[
    record('edge-a',0),record('edge-b',0.07,{owner:'b'}),
    record('paint-a',0.35),record('paint-b',0.42,{material:'brass'}),
    record('special',0.69,{protect:true}),record('rim',0.89,{normal:[0,1,0]}),
    record('interior-a',1.24),record('interior-b',1.32)
  ],options={ratio:0.1,maxDistance:0.12,viewDirections:[[0,0,1]]},
  result=lod.mergeSplats(originals,options),byId=new Map(result.splats.map(s=>[s.id,s]));
  assert.equal(result.work.protected,6);
  assert.equal(result.work.merged,1);
  for(const p of originals.slice(0,6)){
    assert.deepEqual(byId.get(p.id).position,p.position);
    assert.deepEqual(byId.get(p.id).members,[p.id]);
  }
  assert.equal(result.status,'constrained');
  assert.deepEqual(result,lod.mergeSplats(originals,options));
  assert.equal(lod.mergeSplats(originals,{...options,maxPairs:1}).status,'budget');
});

test('dense single-material surfaces stay inside the pair budget', () => {
  const samples = Array.from({ length: 2000 }, (_, i) => ({
    id: String(i), position: [(i % 50) * 0.001, 0, Math.floor(i / 50) * 0.001],
    normal: [0, 1, 0], color: [0.5, 0.5, 0.5], radius: 0.005
  }));
  const reduced = lod.mergeSplats(samples, { ratio: 0.25, maxPairs: 20000 });
  assert.equal(reduced.status, 'ok');
  assert.equal(reduced.splats.length, 500);
  assert.equal(new Set(reduced.splats.flatMap(splat => splat.members)).size, samples.length);
});

test('screen coverage can reject a reduction while keeping the full authored splats', () => {
  const samples = [0, 0.04].map(x => ({
    position: [x, 0, 0], normal: [0, 0, 1], color: [0.3, 0.5, 0.7], radius: 0.065
  }));
  const reference = Float32Array.of(0, 0.9, 0.9, 0.1);
  const preview = Float32Array.of(0, 0.9, 0.49, 0.8);
  const comparison = lod.compareCoverage(reference, preview);
  assert.equal(comparison.missingFraction, 0.5);
  assert.equal(comparison.extraFraction, 0.5);
  const rejected = lod.mergeSplats(samples, { target: 1, guard: rows => {
    assert.equal(rows.length, 1);
    return comparison.accepted;
  } });
  assert.equal(rejected.status, 'coverage');
  assert.equal(rejected.splats.length, 2);
  assert.equal(rejected.work.merged, 0);
  assert.equal(rejected.work.attemptedMerges, 1);
});

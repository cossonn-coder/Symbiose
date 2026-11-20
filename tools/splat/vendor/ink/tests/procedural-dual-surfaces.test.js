const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: K, makeBuilder, makeSculpt } = require('..').load();
const { geometry } = K.procedural;
const V=K.V;

test('both dual extractors produce outward, closed indexed surfaces across exact lattice crossings', () => {
  const bounds = { min:[-1.4,-1.4,-1.4],max:[1.4,1.4,1.4] },
    ball = (x,y,z)=>Math.hypot(x,y,z)-1;
  for (const method of ['surfaceNets','dualContour']) {
    const result = geometry[method](ball,bounds,{cell:0.2}), edges=new Map();
    assert(result.points.length>350);
    for (const face of result.triangles) {
      const [a,b,c]=face.map(i=>result.points[i]), n=V.cross(V.sub(b,a),V.sub(c,a));
      assert(V.dot(n,V.add(a,V.add(b,c)))>0);
      for(let i=0;i<3;i++){
        const key=[face[i],face[(i+1)%3]].sort((a,b)=>a-b).join('/');
        edges.set(key,(edges.get(key)??0)+1);
      }
    }
    assert([...edges.values()].every(n=>n===2));
    assert.equal(result.points.length-edges.size+result.triangles.length,2);
    const mesh=result.mesh({owner:'sphere',material:'paint'});
    assert.equal(mesh.positions.length,result.triangles.length*9);
    assert.equal(mesh.groups[0].owner,'sphere');
  }
});

test('cell-constrained Hermite fitting retains sharp corners with lower error than Surface Nets', () => {
  const box = (x,y,z)=>Math.max(Math.abs(x-0.05)-0.65,Math.abs(y+0.06)-0.68,Math.abs(z-0.02)-0.62),
    bounds={min:[-1.25,-1.25,-1.1],max:[1.25,1.25,1.1]},
    dual=geometry.dualContour(box,bounds,{cell:0.18}),
    nets=geometry.surfaceNets(box,bounds,{cell:0.18}),
    fieldError=result=>result.points.reduce((sum,p)=>sum+Math.abs(box(...p)),0);
  assert.equal(dual.points.length,nets.points.length);
  assert(fieldError(dual)<fieldError(nets)*0.12);
  for(const [i,p] of dual.points.entries()){
    const b=dual.active[i].bounds;
    assert(p.every((v,j)=>v>=b.min[j]-1e-10&&v<=b.max[j]+1e-10));
  }
  assert.throws(()=>geometry.dualContour(box,bounds,{cell:0.01,maxCells:100}),/budget/);
});

test('subcell fast sweeping preserves a zero crossing and restores physical distance for scaled fields', () => {
  const g=K.sdfgrid(x=>19*(x-0.17),[-1,-1,-1],[1,1,1],0.1).reinitialize(),
    empty=K.sdfgrid(()=>2,[0,0,0],[1,1,1],0.25).reinitialize();
  for(const x of [-0.75,-0.17,0.03,0.14,0.17,0.38,0.73])
    assert(Math.abs(g.at(x,0.13,0.27)-(x-0.17))<2e-6);
  assert.equal(empty.at(0.5,0.5,0.5),2);
  assert.throws(()=>g.reinitialize({passes:0}),/sweep passes/);
  const B=makeBuilder(7),S=K.sculpt(makeSculpt(B)),
    a=S.ball([0,0,0],0.8,{r:[1,2,3]},{hold:true,res:0.09});
  const b=S.displace(a,()=>0.8,0.07,{hold:true,k:0.25}),
    rebuilt=S.smooth(b,{reinitialize:true,cell:0.09,res:0.085});
  assert(Math.abs(rebuilt.sd(0.90,0,0)-0.058)<0.022);
  S.bake();
  assert(B.finish({}).count>200);
});

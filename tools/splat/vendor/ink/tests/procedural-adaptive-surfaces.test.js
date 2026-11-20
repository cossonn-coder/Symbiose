const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT:K}=require('..').load();
const G=K.procedural.geometry;

test('signed octrees prune certified distant cells and balance neighboring depth', () => {
  const field=(x,y,z)=>Math.hypot(x,y,z)-0.57,
    box={min:[-2,-2,-2],max:[2,2,2]},
    result=G.octree(field,box,{
      minDepth:2,maxDepth:6,tolerance:0.021,surfaceDepth:([x])=>x<0?5:3
    });
  assert(result.work.nodes<6000);
  assert(result.at(0,0,0)<0 && result.at(1,1,1)>0);
  assert.equal(result.at(2.1,0,0),null);
  assert(result.leaves.some(n=>n.depth<=3));
  assert(result.leaves.some(n=>n.depth>=5));
  for(const n of result.leaves){
    const mid=n.origin.map(v=>v+n.width/2);
    for(let axis=0;axis<3;axis++)for(const dir of [-1,1]){
      const p=mid.slice();
      p[axis]=n.origin[axis]+(dir<0?-0.25:n.width+0.25);
      const neighbor=result.grid.find(...p);
      if(neighbor)assert(Math.abs(neighbor.depth-n.depth)<=1);
    }
  }
  assert.throws(()=>G.octree(field,box,{maxNodes:20,maxDepth:6}),/node budget/);
});

test('mixed-resolution contouring stitches fine and coarse cells without open edges on a ring', () => {
  const sd=(x,y,z)=>Math.hypot(Math.hypot(x,z)-0.81,y)-0.32,
    box={min:[-1.4,-0.75,-1.4],max:[1.4,0.75,1.4]},
    result=G.adaptiveSurface(sd,box,{
      minDepth:2,maxDepth:6,surfaceDepth:([x])=>x<0?5:3
    }), incidences=new Map();
  assert(result.work.transitionFaces>30);
  assert(result.faces.some(f=>f.transition && f.indices.length===3));
  for(const face of result.triangles)for(let i=0;i<3;i++){
    const key=[face[i],face[(i+1)%3]].sort((a,b)=>a-b).join('/');
    incidences.set(key,(incidences.get(key)??0)+1);
  }
  assert([...incidences.values()].every(n=>n===2));
  assert.equal(result.points.length-incidences.size+result.triangles.length,0);
  const mesh=result.mesh({owner:'ring',material:'paint'});
  assert(mesh.positions.length>10000);
  assert.equal(mesh.groups[0].owner,'ring');
});

test('finest adaptive and regular dual grids have equivalent topology away from bounds', () => {
  const bounds={min:[-1.1,-1.1,-1.1],max:[1.1,1.1,1.1]},
    field=(x,y,z)=>Math.hypot(x-0.03,y+0.04,z)-0.63,
    uniform=G.dualContour(field,bounds,{cell:2.2/16}),
    adaptive=G.adaptiveSurface(field,bounds,{minDepth:4,maxDepth:4,method:'dualContour'});
  assert.equal(adaptive.points.length,uniform.points.length);
  assert.equal(adaptive.triangles.length,uniform.triangles.length);
  assert.equal(adaptive.work.transitionFaces,0);
});

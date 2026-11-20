const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT}=require('..').load();
const subtract=KIT.procedural.geometry.subtractConvexFaces;
const {V}=KIT;
function cube(lo,hi){
  const vertices=[
    [lo,lo,lo],[hi,lo,lo],[hi,hi,lo],[lo,hi,lo],
    [lo,lo,hi],[hi,lo,hi],[hi,hi,hi],[lo,hi,hi]
  ];
  return [[0,3,2,1],[4,5,6,7],[0,4,7,3],[1,2,6,5],[0,1,5,4],[3,7,6,2]]
    .map(indices=>({tag:'body',points:indices.map(i=>vertices[i])}));
}
function planes(lo,hi){
  return [0,1,2].flatMap(axis=>[-1,1].map(sign=>({
    normal:[0,1,2].map(i=>i===axis?sign:0),offset:sign<0?-lo:hi
  })));
}
function volume(faces){
  let value=0;
  for(const {points} of faces)for(let i=1;i<points.length-1;i++)
    value+=V.dot(points[0],V.cross(points[i],points[i+1]))/6;
  return Math.abs(value);
}
const near=(a,b)=>assert(Math.abs(a-b)<1e-6,`${a} differs from ${b}`);

test('subtracting an enclosed solid keeps six closed slices and exact volume',()=>{
  const source=cube(-2,2);
  const result=subtract(source,planes(-1,1),{capTag:'cut'});
  assert.equal(result.length,6);
  near(result.reduce((sum,cell)=>sum+volume(cell),0),56);
  assert(result.every(cell=>cell.some(face=>face.tag==='cut')));
  assert(result.every(cell=>cell.flatMap(face=>face.points).every(point=>point.every(Number.isFinite))));
  assert.throws(()=>subtract(source,planes(-1,1),{budget:4}),RangeError);
});
test('touching, missed, empty and completely covered inputs preserve their topology',()=>{
  const source=cube(-1,1);
  assert.equal(subtract(source,[])[0],source);
  assert.equal(subtract(source,planes(1,3))[0],source);
  assert.equal(subtract(source,planes(4,5))[0],source);
  assert.deepEqual(subtract(source,planes(-2,2)),[]);
  const partial=subtract(source,planes(0,2),{capTag:'trim'});
  near(partial.reduce((sum,cell)=>sum+volume(cell),0),7);
});

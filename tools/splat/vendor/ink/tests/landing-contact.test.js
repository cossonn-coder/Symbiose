const test=require('node:test');
const assert=require('node:assert/strict');
const {landingContact}=require('..').load().KIT.procedural;

test('a landing must support the full approach and stay near the requested sill',()=>{
  const q=landingContact.create({sill:[0,1.5,1],facing:[0,0,2],width:1});
  assert.equal(q.points.length,6);
  assert(q.bounds.min[2]>1&&q.bounds.max[2]<1.28);
  const candidates=[
    {id:'narrow',height:(x,z)=>Math.abs(x)<.18?1.5:null},
    {id:'edge',height:(x,z)=>z<1.18?1.5:null},
    {id:'sloped',height:(x,z)=>1.5+x*.2},
    {id:'below',height:()=>.8},
    {id:'deck',height:()=>1.53}
  ];
  assert.deepEqual(q.match(candidates),{id:'deck',height:1.53,range:[1.53,1.53]});
  assert.equal(q.match(candidates.slice(0,4)),null);
  assert.throws(()=>q.match([{id:'invalid',height:()=>Infinity}]),/finite/);
});

test('a landing rotates with the opening and ties resolve by retained identity',()=>{
  const q=landingContact.create({sill:[2,2,3],facing:[-1,0,0],width:2,
    near:.1,far:.6,fraction:.5,verticalTolerance:.25,elevationSpread:.12});
  assert.deepEqual(q.bounds,{min:[1.4,1.75,2.5],max:[1.9,2.25,3.5]});
  const candidates=[{id:'wider',height:(x,z)=>2+z/100},{id:'first',height:(x,z)=>2+z/100}];
  assert.deepEqual(q.match(candidates),{id:'first',height:2.035,range:[2.025,2.035]});
  assert.deepEqual(q.match(candidates.slice().reverse()),q.match(candidates));
  assert.throws(()=>landingContact.create({sill:[0,0,0],facing:[0,1,0],width:1}),/horizontal/);
});

test('level landing patches cover a continuous seam at compatible heights',()=>{
  const q=landingContact.create({sill:[0,1.5,1],facing:[0,0,1],width:1});
  const patch=(id,lo,hi,height=1.5)=>({id,height,footprint:[[lo,1],[hi,1],[hi,1.4],[lo,1.4]]});
  const left=patch('stone',-.9,.12),right=patch('wood',.12,.9,1.53);
  const fit={id:'stone',ids:['stone','wood'],height:1.53,range:[1.5,1.53]};
  assert.deepEqual(q.matchPatches([left,right]),fit);
  assert.deepEqual(q.matchPatches([right,left]),fit);
  assert.equal(q.matchPatches([left,patch('wood',.121,.9)]),null);
  assert.equal(q.matchPatches([left,{...right,height:1.58}]),null);
});

test('a rotated approach sees interior cutouts and another patch can fill them',()=>{
  const q=landingContact.create({sill:[2,2,3],facing:[-1,0,0],width:1});
  const hole=[[1.8,3.11],[1.9,3.11],[1.9,3.18],[1.8,3.18]];
  const roof={id:'roof',height:2,footprint:[[1.2,2.1],[2,2.1],[2,3.9],[1.2,3.9]],holes:[hole]};
  assert.equal(q.matchPatches([roof]),null);
  assert.deepEqual(q.matchPatches([roof,{id:'inlay',height:1.99,footprint:hole}]),
    {id:'inlay',ids:['inlay','roof'],height:2,range:[1.99,2]});
  assert.throws(()=>q.matchPatches([{...roof,height:Infinity}]),/finite/);
});

test('clipping a full-size outline may add vertices without invalidating the floor',()=>{
  const q=landingContact.create({sill:[0,1.5,1],facing:[0,0,1],width:1});
  const footprint=Array.from({length:128},(_,i)=>{
    const angle=i/128*2*Math.PI;
    return [.025*Math.sin(angle),1.06999-.025*Math.cos(angle)];
  });
  assert.equal(q.matchPatches([{id:'partial-disk',height:1.5,footprint}]),null);
});

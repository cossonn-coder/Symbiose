const {test}=require('node:test');
const assert=require('node:assert/strict');
const {profileBand}=require('..').load().KIT.procedural;

test('profile bands fit one-sided borders around corners and leave real joints',()=>{
  const profile=[[0,0],[2,0],[2,2],[0,2]];
  const band=profileBand({profile,width:.2,pitch:1.5,gap:.1});
  assert.deepEqual(band.outer,[[-.2,-.2],[2.2,-.2],[2.2,2.2],[-.2,2.2]]);
  assert.equal(band.cells.length,5);
  for(const cell of band.cells){
    const covered=cell.fragments.reduce((n,f)=>n+f.to-f.from,0);
    assert(Math.abs(covered-(band.unit-.1))<1e-8);
  }
  assert(Object.isFrozen(band));
  assert(!Object.isFrozen(profile));
});

test('a tapered open band can give a corner its own fitted piece',()=>{
  const profile=[[0,0],[2,0],[2,2]],sections=[
    {id:'first',end:.375,count:2},{id:'accent',end:.625,count:1},{id:'last',end:1,count:2}
  ];
  const band=profileBand({profile,width:[.1,.2,.3],closed:false,side:'left',pitch:.65,gap:.04,sections});
  assert.deepEqual(band.outer,[[0,.1],[1.8,.2],[1.7,2]]);
  const feature=band.cells.find(cell=>cell.section==='accent');
  assert.equal(feature.fragments.length,2);
  assert.deepEqual(feature.fragments[0].points[1],feature.fragments[1].points[0]);
  assert.deepEqual(feature.fragments[0].points[2],feature.fragments[1].points[3]);
  assert.throws(()=>profileBand({profile:[[0,0],[1,0],[0,0]],closed:false,width:.1,pitch:1}),/reverse/);
  assert.throws(()=>profileBand({profile,width:.1,pitch:1,budget:1}),/budget/);
});

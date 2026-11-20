const test=require('node:test'),assert=require('node:assert/strict');
const {fitHeightBands}=require('..').load().KIT.procedural.routes;

test('height bands raise only the needed part of a grade-limited guide and retain its bends',()=>{
  const samples=[
    {at:0,min:.3,max:.3},{at:1,min:0,max:1.4,preferred:.3},
    {at:2,min:1.05,max:1.4,keep:true},{at:2.8,min:.35,max:1.4,preferred:.4},
    {at:4,min:.3,max:.3}
  ];
  const fit=fitHeightBands(samples,{maxGrade:.65,maxPoints:5});
  assert(fit.indices.includes(2));
  for(let j=1;j<fit.indices.length;j++){
    const [a,b]=[fit.indices[j-1],fit.indices[j]],y=fit.elevations[j-1],z=fit.elevations[j];
    const grade=(z-y)/(samples[b].at-samples[a].at);
    assert(Math.abs(grade)<=.65+1e-9);
    for(let i=a;i<=b;i++){
      const v=y+grade*(samples[i].at-samples[a].at);
      assert(v>=samples[i].min-1e-9&&v<=samples[i].max+1e-9);
    }
  }
  assert.equal(fitHeightBands(samples,{maxGrade:.35}),null);
  assert.equal(fitHeightBands(samples,{maxGrade:.65,maxPoints:2}),null);
});

test('height bands retain level fits and reject malformed station or target data',()=>{
  const samples=[{at:0,min:.5,max:2,preferred:1},{at:1,min:.8,max:.9}];
  assert.deepEqual(fitHeightBands(samples,{maxGrade:0}),{indices:[0,1],elevations:[.9,.9]});
  assert.throws(()=>fitHeightBands(samples.slice().reverse(),{maxGrade:1}),/increasing/);
  assert.throws(()=>fitHeightBands([{...samples[0],preferred:Infinity},samples[1]],{maxGrade:1}),/finite/);
});

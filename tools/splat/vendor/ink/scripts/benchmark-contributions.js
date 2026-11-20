#!/usr/bin/env node
const os = require('node:os');
const ink = require('..');
const workshop = require('../examples/coverage-aware-glass.js');
const webgl = require('../cli/look-webgl.js');

const width=320,height=192;
function measureScene(kit,factory,open,{width,height}) {
  const entry=factory(kit), base=entry.build(entry.seed);
  const solid={...base,refract:0}, masked={...solid,look:{...solid.look,paletteConstraints:{
    targets:solid.look.paletteConstraints.targets.map(({select,...row})=>({select,...row,
      ...(select.surface==='glass'&&{mask:{type:'axis',axis:'y',space:'world',range:[.35,1.75]}})}))
  }}};
  const backend=open(width,height,{outline:false,dither:0,colored:false});
  const variants=[
    {id:'owner-resolve',world:solid,frame:{coverageAware:false}},
    {id:'layered-palette',world:solid,frame:{}},
    {id:'layered-axis-mask',world:masked,frame:{}},
    {id:'layered-refraction',world:base,frame:{}}
  ];
  const sample = variant => {
    const start=performance.now();
    for(let i=0;i<3;i++)backend.draw(variant.world,variant.frame);
    backend.fence();
    return (performance.now()-start)/3;
  };
  try {
    const suites=new Map(variants.map(row=>[row.id,[]]));
    for(let round=0;round<6;round++){
      const order=round%2?variants.slice().reverse():variants;
      for(const variant of order){
        sample(variant);
        for(let i=0;i<4;i++)suites.get(variant.id).push(sample(variant));
      }
    }
    return {driver:backend.driver,width,height,splats:base.count,framesPerSample:3,cases:[...suites].map(([id,samples])=>{
      const sorted=samples.slice().sort((a,b)=>a-b), mid=sorted.length>>1;
      return {id,medianMs:(sorted[mid-1]+sorted[mid])/2,p95Ms:sorted[Math.ceil(.95*sorted.length)-1],samplesMs:samples};
    })};
  } finally { backend.close(); }
}
const kit=ink.load(), scene=workshop(kit), world=scene.build(scene.seed);
const begin=performance.now(), picker=ink.createSplatPicker(world), indexMs=performance.now()-begin;
const pickSamples=[], candidates=[];
for(let batch=0;batch<40;batch++){
  const start=performance.now();
  for(let i=0;i<80;i++){
    const ray={origin:[-1.65+(i%47)*.069,.34+(i%13)*.107,6],direction:[.08,0,-1],maxDistance:16};
    const result=picker.ray(ray);
    candidates.push(result.visited);
  }
  if(batch>=3)pickSamples.push((performance.now()-start)/80);
}
pickSamples.sort((a,b)=>a-b);
const gpu=webgl({hardware:!process.argv.includes('--software')},workshop,measureScene,{width,height});
console.log(JSON.stringify({
  environment:{cpu:os.cpus()[0]?.model,node:process.version,platform:process.platform,arch:process.arch},
  scene:scene.id, gpu, picking:{indexMs,splats:world.count,rays:candidates.length,
    meanCandidates:candidates.reduce((n,v)=>n+v,0)/candidates.length,maxCandidates:Math.max(...candidates),
    medianMs:pickSamples[pickSamples.length>>1],p95Ms:pickSamples[Math.ceil(.95*pickSamples.length)-1]}
},null,2));

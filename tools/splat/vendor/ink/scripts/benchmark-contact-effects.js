#!/usr/bin/env node
const os=require('node:os');
const {performance}=require('node:perf_hooks');
const ink=require('..'), kit=ink.load(), {world:W}=kit.KIT;
const example=require('../examples/world-contact-effects.json');
const runs=12, ticks=36;

const {feedback,...withoutFeedback}=example.systems;
const baseline={...example,systems:withoutFeedback,connections:[],visual:{}};
const normal=[
  {id:'wheel-contacts',world:baseline},
  {id:'all-contact-effects',world:example}
];
const batchSize=256;
const stressInputs=Array.from({length:batchSize},(_,i)=>({
  point:[(i%16)*.4,0,(i>>4)*.4],entity:'wheel-'+i,material:'trackside/clay',
  interaction:'roll',speed:2.6,load:12,weight:.03,surface:{wetness:i%4===0?0:1}
}));
const pulse=()=>({
  initial:()=>[],outputs:{contacts:'event'},output:state=>({contacts:state}),step:()=>stressInputs
});
const stress={dt:1/60,assetPacks:example.assetPacks,systems:{
  drive:{kind:'benchmark-contacts'},
  feedback:{kind:'contact-effects',config:{maxParticles:256,soundEvents:false}}
},connections:[{from:'drive/contacts',to:'feedback/contacts'}]};

function stats(samples) {
  const sorted=samples.slice().sort((a,b)=>a-b);
  return { medianMs:sorted[Math.ceil(samples.length*.5)-1],p95Ms:sorted[Math.ceil(samples.length*.95)-1] };
}

function time(run,tickCount) {
  const start=performance.now();
  run.advance(tickCount);
  return (performance.now()-start)/tickCount;
}

const samples=new Map(normal.map(({id})=>[id,[]]));
for(let i=0;i<runs+3;i++){
  const order=i%2===0?normal:normal.slice().reverse();
  for(const {id,world} of order){
    const elapsed=time(W.runtime.create(world),ticks);
    if(i>=3)samples.get(id).push(elapsed);
  }
}
const sceneRuns=[...samples].map(([id,ms])=>({id,...stats(ms),samplesMs:ms}));
const pressure=[];
for(let i=0;i<8;i++){
  const run=W.runtime.create(stress,{implementations:{'benchmark-contacts':pulse}});
  const elapsed=time(run,60);
  if(i>=2)pressure.push(elapsed);
}
const report=W.runtime.create(stress,{implementations:{'benchmark-contacts':pulse},profile:true});
report.advance(60);
const profile=report.profile().feedback;
const frame=[];
for(let i=0;i<80;i++){
  const start=performance.now();
  report.query().probe('feedback/frame');
  if(i>=10)frame.push(performance.now()-start);
}
console.log(JSON.stringify({
  machine:{cpu:os.cpus()[0]?.model,node:process.version},
  scene:{id:example.id,ticks,runs,cases:sceneRuns},
  stress:{recordsPerTick:batchSize,ticks:60,...stats(pressure),meanEffectsMs:profile.ms/profile.calls,
    particles:report.query().probe('feedback/frame').value.particles.length,frameSample:stats(frame),
    dropped:report.query().probe('feedback/dropped').value}
},null,2));

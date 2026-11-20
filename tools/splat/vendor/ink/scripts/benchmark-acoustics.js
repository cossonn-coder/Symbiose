#!/usr/bin/env node
const os=require('node:os');
const {performance}=require('node:perf_hooks');
const {KIT:{world:W}}=require('..').load();

const cols=8, rows=6, size=4, rooms={}, openings={};
for(let z=0;z<rows;z++)for(let x=0;x<cols;x++){
  const name='r'+x+'_'+z;
  rooms[name]={bounds:{min:[x*size,0,z*size],max:[(x+1)*size,3,(z+1)*size]}};
  if(x)openings['x'+x+'_'+z]={from:'r'+(x-1)+'_'+z,to:name,at:[x*size,1,(z+.5)*size]};
  if(z)openings['z'+x+'_'+z]={from:'r'+x+'_'+(z-1),to:name,at:[(x+.5)*size,1,z*size]};
}
const world={systems:{air:{kind:'ventilation',config:{rooms,openings}},
  sound:{kind:'acoustics',config:{layout:'air/acoustic-layout'}}}};
const listener=[1.4,1.1,2.2];
const emitters=Array.from({length:256},(_,i)=>({
  from:[size+.11+((i*29)%270)*.1,1.2,.11+((i*53)%230)*.1]
}));
function stats(samples){
  const sorted=samples.slice().sort((a,b)=>a-b);
  return {medianMs:sorted[Math.ceil(samples.length*.5)-1],p95Ms:sorted[Math.ceil(samples.length*.95)-1]};
}
function probe(query,to,source){
  const result=query.probe('sound/audible',to,source);
  if(result.status!=='ok'||!(result.value.gain>0))throw Error('Benchmark must resolve a nonzero acoustic path');
  return result.value.gain;
}
const cold=[];
for(let i=0;i<14;i++){
  const query=W.runtime.create(world).query(), start=performance.now();
  probe(query,listener,emitters[130]);
  if(i>=4)cold.push(performance.now()-start);
}
const run=W.runtime.create(world), query=run.query(), mixes=[];
for(let i=0;i<64;i++){
  const start=performance.now();
  for(const source of emitters)probe(query,listener,source);
  if(i>=12)mixes.push(performance.now()-start);
}
const motion=[];
for(let i=0;i<120;i++){
  const to=[1.4+i*.045,1.1,2.2], start=performance.now();
  probe(query,to,emitters[(i*23)%emitters.length]);
  if(i>=12)motion.push(performance.now()-start);
}
const revisions=[];
for(let i=1;i<=44;i++){
  run.schedule([{tick:i,action:'world/input',args:{port:'air/opening.x1_0',value:i%2}}]);
  run.advance(i);
  const revision=run.query(), start=performance.now();
  probe(revision,listener,emitters[130]);
  if(i>8)revisions.push(performance.now()-start);
}
console.log(JSON.stringify({
  machine:{cpu:os.cpus()[0]?.model,node:process.version},
  scene:{rooms:Object.keys(rooms).length,openings:Object.keys(openings).length},
  coldFirstQuery:stats(cold),
  warmMix:{emitters:emitters.length,batches:mixes.length,...stats(mixes),
    perQuery:stats(mixes.map(ms=>ms/emitters.length))},
  movingListener:stats(motion),
  changedOpening:stats(revisions)
},null,2));

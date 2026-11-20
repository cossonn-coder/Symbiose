#!/usr/bin/env node
const assert = require('node:assert/strict');
const os = require('node:os');
const { performance } = require('node:perf_hooks');
const { KIT:{world:W} } = require('..').load();
const workshop = require('../examples/world-lightwell-workshop.json');
const quarry = require('../examples/world-live-volumes.json');
const runs = Number(process.argv[2] ?? 9);
assert(Number.isInteger(runs) && runs>=3 && runs<=50,'Pass a sample count between 3 and 50');

function quarryLighting() {
  const scene = JSON.parse(JSON.stringify(quarry));
  scene.systems.quarry.config.lighting = {
    ambient:.12,sun:{direction:[.38,1,.29],intensity:1.2},sky:{intensity:.24},
    indirect:{distance:1.35,probeSize:.45,strength:.62},
    lamps:{lamp:{at:[2.1,1.35,1],range:3.4,color:'#ff7f48',intensity:4.1}}
  };
  scene.commands = [
    scene.commands[0],
    {tick:3,action:'quarry/set-light',args:{id:'lamp',at:[3.1,1.58,.3]}}
  ];
  return scene;
}
const scenarios = [
  {scene:workshop,id:'workshop',point:[0,0,0],phases:{skylight:2,lantern:4}},
  {scene:quarryLighting(),id:'quarry',point:[0,1,0],phases:{spillway:2,lamp:3}}
];
const timed = fn => {
  const start = performance.now(), result = fn();
  return { result, ms:performance.now()-start };
};
function stats(samples) {
  const data=samples.slice().sort((a,b)=>a-b), mid=data.length>>1;
  const median=data.length%2?data[mid]:(data[mid-1]+data[mid])/2;
  return {medianMs:+median.toFixed(2),p95Ms:+data[Math.ceil(.95*data.length)-1].toFixed(2)};
}
function measure(query,id) {
  const frame=timed(()=>query.renderVolume(id)), {lamps,...work}=query.probe(id+'/lighting').value;
  return {...frame,work:{...work,relitChunks:work.relitChunks.length}};
}
function equal(a,b) {
  assert.equal(a.parts.length,b.parts.length);
  for (const [i,part] of a.parts.entries()){
    assert.deepEqual(part.splatIds,b.parts[i].splatIds);
    assert.deepEqual(part.data,b.parts[i].data);
  }
}
function benchmark({scene,id,point,phases}) {
  const result=Object.fromEntries(Object.keys(phases).map(key=>[key,{
    incremental:[], full:[], advance:[], work:null, splats:0
  }]));
  for(let i=-2;i<runs;i++){
    const run=W.runtime.create(scene);
    run.query().renderVolume(id);
    for(const [phase,tick] of Object.entries(phases)){
      const advanced=timed(()=>run.advance(tick));
      const cold=W.runtime.create(scene,{checkpoint:JSON.parse(JSON.stringify(run.checkpoint()))});
      cold.query().probe(id+'/clearance',point);
      // Both lighting measurements start with baked geometry. Only the incremental
      // lane has an earlier lighting snapshot. Alternate their measurement order.
      const pair=i%2===0?['incremental','full']:['full','incremental'], frames={};
      for(const lane of pair)frames[lane]=measure((lane==='incremental'?run:cold).query(),id);
      equal(frames.incremental.result,frames.full.result);
      if(i<0)continue;
      const entry=result[phase];
      entry.advance.push(advanced.ms);
      for(const lane of pair)entry[lane].push(frames[lane].ms);
      entry.work=Object.fromEntries(pair.map(lane=>[lane,frames[lane].work]));
      entry.splats=frames.incremental.result.parts.reduce((sum,part)=>sum+part.count,0);
    }
  }
  return Object.fromEntries(Object.entries(result).map(([phase,row])=>[phase,{
    splats:row.splats, identicalToFull:true,
    incremental:stats(row.incremental),full:stats(row.full),simulationAdvance:stats(row.advance),
    work:row.work,samplesMs:{incremental:row.incremental,full:row.full,simulationAdvance:row.advance}
  }]));
}
console.log(JSON.stringify({
  runs,warmupPairs:2,environment:{cpu:os.cpus()[0]?.model,node:process.version,platform:os.platform(),arch:os.arch()},
  method:'Lighting-only time after the volume mesh is prepared. A restored snapshot provides a full-lighting reference.',
  scenes:Object.fromEntries(scenarios.map(spec=>[spec.scene.id,benchmark(spec)]))
},null,2));

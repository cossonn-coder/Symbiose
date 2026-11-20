#!/usr/bin/env node
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const os = require('node:os');
const { performance } = require('node:perf_hooks');
const ink = require('..');

const runs = Number(process.argv[2] ?? 7), warmup = 2;
assert(Number.isSafeInteger(runs) && runs >= 3 && runs <= 60,'Pass a run count from 3 to 60');
const kit = ink.load(), { KIT: K } = kit;
const view = {w:128,h:80,px:1,raw:true};
const read = name => {
  const scene = require('../examples/'+name+'.js')(kit);
  return {scene,world:scene.build(scene.seed)};
};
const observatory = read('environment-test-scene');
const ravine = read('shaped-mist-ravine');
const workshop = read('coverage-aware-glass');

function sparseMist(world) {
  const density = K.procedural.density;
  const field = density.fromSdf({ bounds:{min:[-5,-1,-6],max:[5,5,6]}, feather:.38,
    field:(x,y,z) => Math.min(Math.hypot(x-.6,y-.66,z-1.4)-1.05,Math.hypot(x+1.45,y-1.15,z+1.5)-.82)
  });
  return {...world,cloudField:false,atmosphere:[K.atmosphere.field({
    id:'sparse pockets',field:density.sparse(field,{resolution:[48,32,48]}),density:.55,color:'#93afcf',step:.11
  })], volumeLighting:{ambient:.5,sun:{direction:[-.36,.82,.44],intensity:.54}}};
}

const cases = [
  {id:'observatory',world:observatory.world, options:{...view,...observatory.scene.camera(0),t:0}, diagnostic:'uncached'},
  {id:'ravine',world:ravine.world,options:{...view,t:1.2}, diagnostic:'uncached'},
  {id:'sparse-mist',world:sparseMist(observatory.world),options:{...view,t:1.0},diagnostic:'dense'},
  {id:'lens-workshop',world:workshop.world,options:{...view,raw:false,t:0}}
];
const compareOptions = name => name==='uncached' ? {cacheBounds:false} : {skip:false};
const rounded = value => Number(value.toFixed(3));
function timing(values) {
  const sorted = values.slice().sort((a,b)=>a-b);
  const mid = Math.floor(sorted.length/2);
  return {medianMs:rounded(sorted.length%2 ? sorted[mid] : (sorted[mid-1]+sorted[mid])/2),
    p95Ms:rounded(sorted[Math.ceil(sorted.length*.95)-1]),samplesMs:values.map(rounded)};
}
function benchmark({ id,world,options,diagnostic }) {
  const lanes = [{name:'default',options}];
  if (diagnostic) lanes.push({name:diagnostic,options:{...options,volumeQuality:{
    ...options.volumeQuality,...compareOptions(diagnostic)
  }}});
  for (const lane of lanes) lane.times = [];
  for (let run=-warmup;run<runs;run++) {
    const ordered = run%2===0 ? lanes : lanes.slice().reverse();
    const results = {};
    for (const lane of ordered) {
      const start = performance.now();
      results[lane.name] = ink.render(world,lane.options).rgb;
      if (run>=0) lane.times.push(performance.now()-start);
    }
    if (diagnostic) assert.deepEqual(results.default,results[diagnostic],id+' changes pixels in '+diagnostic+' mode');
  }
  const profiles = Object.fromEntries(lanes.map(lane=>{
    const frame = ink.render(world,{...lane.options,renderStats:true});
    const {frameMs,...work} = frame.renderStats;
    return [lane.name,{...timing(lane.times),work,instrumentedMs:rounded(frameMs),
      sha256:createHash('sha256').update(frame.rgb).digest('hex')}];
  }));
  return {id,splats:world.count,width:options.w,height:options.h,time:options.t,lanes:profiles};
}

console.log(JSON.stringify({runs,warmup,renderer:'headless CPU',environment:{
  cpu:os.cpus()[0]?.model,node:process.version,platform:os.platform(),arch:os.arch()
},scenes:cases.map(benchmark)},null,2));

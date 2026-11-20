/* Whole-workload comparisons with generated, deterministic scenes. */
const assert = require('node:assert/strict');
const path = require('node:path');
const os = require('node:os');
const { performance } = require('node:perf_hooks');
const { createHash } = require('node:crypto');

const options = Object.fromEntries(process.argv.slice(2).map(arg => arg.slice(2).split('=')));
const repetitions = Number(options.runs ?? 7);
const selected = options.only?.split(',');
if (!options.baseline || !Number.isSafeInteger(repetitions) || repetitions < 3 || repetitions > 100)
  throw Error('Use --baseline=/path/to/checkout [--runs=7] [--only=case,case]');
const candidate = require('..').load().KIT.world;
const baseline = require(path.resolve(options.baseline)).load().KIT.world;
const quarry = require('../examples/world-crossing.json');
const watershed = require('../examples/world-watershed.json');

function mechanics(count, fixed, spacing, ticks, probeCount) {
  const bodies = {};
  for (let i = 0; i < count; i++) {
    const x = (i % 32) * spacing, z = Math.floor(i / 32) * spacing;
    bodies['b' + String(i).padStart(4,'0')] = {
      position:[x,.26+(i % 3)*.013,z], half:[.25,.25,.25], fixed:i < fixed,
      velocity:[((i % 5)-2)*.16,0,((i % 7)-3)*.06], turn:i % 4 * .13
    };
  }
  const world = {dt:.03,systems:{shop:{kind:'mechanics',config:{bodies}}}};
  return W => {
    const run = W.runtime.create(world), samples = [];
    for(let tick=1;tick<=ticks;tick++){
      run.step();
      if(!probeCount) continue;
      const query=run.query();
      for(let k=0;k<probeCount;k++){
        const point=[(k*7.373+tick*.07)%(Math.min(count,32)*spacing),.29,(k*3.163)%(Math.ceil(count/32)*spacing)];
        const reading=query.probe('shop/clearance',point);
        const support=query.probe('shop/support',point);
        samples.push(reading,support);
      }
    }
    return [run.checkpoint(),samples];
  };
}

function spatial(size, moving, ticks, queries, {mixed = false, radius} = {}) {
  const entities={}, bodies={};
  for(let i=0;i<size;i++) entities['p'+i]={kind:i%5?'prop':'resource',position:[i%80,0,Math.floor(i/80)]};
  if(mixed)for(let i=0;i<64;i++){
    const name='vehicle'+i;
    entities[name]={position:[i,0,0],sockets:{deck:[0,.3,0]}};
    entities['cargo'+i]={position:[.2,0,0],anchor:{entity:name,socket:'deck'}};
    bodies[name]={half:[.25,.25,.25],position:[i,.3,(i%8)*3],velocity:[.2,0,.35],angular:[0,.1,0]};
  }
  const commands=Array.from({length:ticks},(_,i)=>({
    tick:i+1,action:'world/patch',args:{edits:Array.from({length:moving},(_,j)=>({
      op:'set',path:['entities','p'+j,'position'],value:[j+(i%4)*.06,0,0]
    }))}
  })).filter(command=>command.args.edits.length);
  const world={entities,commands,...(mixed?{systems:{traffic:{kind:'mechanics',config:{bodies}}}}:{})};
  return W => {
    const run=W.runtime.create(world), reads=[];
    for(let i=0;i<ticks;i++){
      run.step();
      const query=run.query();
      for(let j=0;j<queries;j++)
        reads.push(query.spatial({point:[(8*j+.11*i)%80,0,(1.47*j)%50],radius:radius??(j%2?2:5)}).map(row=>row.id));
    }
    return [run.checkpoint(),reads];
  };
}

function namedQueries() {
  const fields=Object.fromEntries(Array.from({length:256},(_,i)=>['field'+i,{default:i}]));
  return W=>{
    const run=W.runtime.create({systems:{terrain:{kind:'fields',config:{fields}}}}), samples=[];
    for(let i=0;i<20;i++){
      run.step();
      const query=run.query();
      for(let j=0;j<240;j++)samples.push(query.probe('field'+(j+i)%256,[j,0,i]));
    }
    return [run.checkpoint(),samples];
  };
}

function routes() {
  const bodies={wall:{fixed:true,half:[.2,1,2],position:[0,1,0]}};
  for(let i=0;i<255;i++)bodies['obstacle'+i]={fixed:true,half:[.28,.22,.28],
    position:[(i%32)*.6-10,.22,(i%2?1:-1)*(2.6+Math.floor(i/32)*.8)]};
  const world={systems:{shop:{kind:'mechanics',config:{bodies}},navigation:{kind:'navigation',config:{
    bounds:{min:[-10,-1,-7],max:[10,3,7]},support:'shop/support',clearance:'shop/clearance',cell:.5
  }}}};
  return W=>{
    const run=W.runtime.create(world),query=run.query(),samples=[];
    for(let i=0;i<3;i++)samples.push(query.trace('navigation/route',[-8,0,1.1*i],{to:[8,0,-1.1*i]}));
    return [run.checkpoint(),samples];
  };
}

function scene(world,ticks,commands) {
  return W => {
    const run=W.runtime.create(world);
    if(commands)run.schedule(commands);
    run.advance(ticks);
    return run.checkpoint();
  };
}

function edits(size, count) {
  const world={entities:{}};
  for(let i=0;i<size;i++)world.entities['p'+i]={kind:'prop',position:[i,0,0]};
  const changes=Array.from({length:count},(_,i)=>({
    op:'set',path:['entities','p'+i,'position',1],value:i+1
  }));
  return W => {
    const source=W.manifest(world), result=W.apply(source,changes);
    return [result.world,W.query.keyedChanges(source,result.world)];
  };
}

const cases={
  'tiny-motion':mechanics(12,4,1.6,24,0),
  'static-town':mechanics(512,512,1.7,12,0),
  'sparse-moving-128':mechanics(128,32,2.1,12,0),
  'sparse-moving':mechanics(512,128,2.1,12,0),
  'dense-contact':mechanics(192,0,.39,12,0),
  'packed-contact':mechanics(256,0,.07,4,0),
  'clearance-support':mechanics(512,480,1.25,8,120),
  'spatial-cold':spatial(3500,0,1,1),
  'spatial-unbounded':spatial(3500,0,4,2,{radius:1000}),
  'spatial-mostly-static':spatial(3500,8,16,40),
  'spatial-static':spatial(3500,0,18,40),
  'spatial-moving-attachments':spatial(3500,8,16,40,{mixed:true}),
  'large-edit-batch':edits(4000,120),
  'bare-field-names':namedQueries(),
  'navigation-routes':routes(),
  'quarry-scenario':scene(quarry,105),
  'watershed-simulation':scene(watershed,120,[{tick:31,action:'river/bed',args:{
    bounds:{min:[-1.55,-.75],max:[-.55,.75]},height:-.25
  }}])
};
if(selected?.some(name=>!Object.hasOwn(cases,name)))throw Error('Unknown benchmark case in --only');
function digest(value) {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}
function summarize(times) {
  const sorted=times.slice().sort((a,b)=>a-b), mid=sorted.length>>1;
  return {median: sorted.length%2?sorted[mid]:(sorted[mid-1]+sorted[mid])/2,p95:sorted[Math.ceil(sorted.length*.95)-1]};
}
function timed(bench,W) {
  const start=performance.now(), value=bench(W), elapsed=performance.now()-start;
  return {elapsed,digest:digest(value)};
}
const rows={};
for(const [name,bench] of Object.entries(cases)){
  if(selected&&!selected.includes(name))continue;
  const a=[],b=[];
  const expected=timed(bench,baseline).digest;
  assert.equal(timed(bench,candidate).digest,expected,name+' warmup differs from baseline');
  for(let i=0;i<repetitions;i++){
    const first=i%2?candidate:baseline, second=i%2?baseline:candidate;
    const left=timed(bench,first), right=timed(bench,second);
    assert.equal(left.digest,expected,name+' differs from baseline');
    assert.equal(right.digest,expected,name+' differs from baseline');
    a.push(i%2?right.elapsed:left.elapsed);
    b.push(i%2?left.elapsed:right.elapsed);
  }
  rows[name]={baseline:summarize(a),candidate:summarize(b),samples:{baseline:a,candidate:b},digest:expected};
  if(!('json' in options))console.log(name,rows[name].baseline.median.toFixed(2)+' ms → '+rows[name].candidate.median.toFixed(2)+' ms');
}
if('json' in options)console.log(JSON.stringify({repetitions,environment:{
  node:process.version,os:os.platform()+' '+os.release(),arch:os.arch(),cpu:os.cpus()[0]?.model
},cases:rows},null,2));

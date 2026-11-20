const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: { world: W } } = require('..').load();
const manifest = require('../examples/world-multi-rate.json');
const near = (a,b) => assert(Math.abs(a-b)<1e-12, String(a)+' differs from '+b);
const signal = (run,port) => run.query().probe('world/signal',{}, {port}).value;

test('incommensurate fast rates share a deterministic grid with ordinary and slow solvers', () => {
  const counter = () => ({initial:()=>({times:[],duration:0,seen:0,random:[]}),
    step(state,ctx) {
      return {times:[...state.times,ctx.time],duration:state.duration+ctx.dt,
        seen:ctx.states.four.times.length,random:[...state.random,ctx.random('turn')]};
    }});
  const run = W.runtime.create({dt:.12,systems:{
    four:{kind:'counter',schedule:{substeps:4}},
    three:{kind:'counter',schedule:{substeps:3}},
    ordinary:{kind:'counter'},slow:{kind:'counter',schedule:{every:3}}
  }},{implementations:{counter},profile:true});
  run.advance(3);
  const {four,three,ordinary,slow} = run.view().states;
  assert.equal(run.rates().subdivision,12);
  assert.deepEqual(Object.fromEntries(Object.entries(run.profile()).map(([key,row])=>[key,row.calls])),
    {four:12,three:9,ordinary:3,slow:1});
  assert.deepEqual(four.times.slice(0,4),[.03,.06,.09,.12]);
  [.04,.08,.12].forEach((time,i)=>near(three.times[i],time));
  assert.equal(new Set(four.random).size,12);
  for (const lane of [four,three,ordinary,slow]) near(lane.duration,.36);
  assert.equal(ordinary.seen,11);
  assert.equal(slow.seen,11);
});

test('hold, weighted average and sum read distinct boundaries and replay a partially filled window', () => {
  const source = () => ({initial:()=>0,step:state=>state+1,outputs:{value:'number'},
    output:state=>({value:state})});
  const sink = () => ({initial:()=>({}),inputs:{hold:'number',mean:'number',sum:'number'},
    step:(_,ctx)=>({...ctx.input,queried:ctx.query.probe('world/signal',{}, {port:'fast/value'}).value})});
  const world = {dt:.25,systems:{fast:{kind:'source',schedule:{substeps:4}},slow:{kind:'sink',schedule:{every:2}}},
    connections:[
      {from:'fast/value',to:'slow/hold'},
      {from:'fast/value',to:'slow/mean',sample:'average'},
      {from:'fast/value',to:'slow/sum',sample:'sum'}
    ]};
  const options = {implementations:{source,sink}};
  const run = W.runtime.create(world,options);
  run.step();
  assert.deepEqual(run.view().states.slow,{});
  assert.deepEqual(run.checkpoint().sampling['slow/mean'],{value:6,quanta:4});
  assert.equal(run.checkpoint().sampling['slow/sum'],10);
  const checkpoint = JSON.parse(JSON.stringify(run.checkpoint()));
  const restored = W.runtime.create(checkpoint.world,{...options,checkpoint});
  restored.step();
  assert.deepEqual(restored.view().states.slow,{hold:7,mean:3.5,sum:28,queried:7});
  assert.equal(restored.checkpoint().sampling['slow/sum'],8);
  run.step();
  assert.deepEqual(run.checkpoint(),restored.checkpoint());
  const replay = W.runtime.replay(JSON.parse(JSON.stringify(restored.recording())),options);
  assert.deepEqual(replay.checkpoint(),restored.checkpoint());
  assert.throws(()=>W.runtime.create(checkpoint.world,{...options,checkpoint:{...checkpoint,
    sampling:{...checkpoint.sampling,'slow/mean':{value:6,quanta:0}}}}),/Invalid saved average window/);
});

test('delays carry whole per-tick pulse and vector batches while manual events wait for their consumer', () => {
  const source = () => ({initial:()=>0,step:state=>state+1,
    outputs:{notify:'event',vector:'vec3',level:'number'},output:state=>({
      notify:state?[state]:[],vector:[state,-state,1],level:state
    })});
  const consumer = () => ({initial:()=>({}),inputs:{wire:'event',manual:'event',vector:'vec3',level:'number'},
    step:(_,ctx)=>ctx.input});
  const run = W.runtime.create({systems:{
    fast:{kind:'source',schedule:{substeps:3}},slow:{kind:'consumer',schedule:{every:2}}
  },connections:[
    {from:'fast/notify',to:'slow/wire',delay:1},
    {from:'fast/vector',to:'slow/vector',sample:'sum',delay:1},
    {from:'fast/level',to:'slow/level',delay:1}
  ],commands:[
    {tick:1,action:'world/input',args:{port:'slow/manual',value:['first']}},
    {tick:1,action:'world/input',args:{port:'slow/manual',value:['second']}},
    {tick:2,action:'world/input',args:{port:'slow/manual',value:['later']}}
  ]},{implementations:{source,consumer}});
  run.step();
  assert.deepEqual(signal(run,'fast/notify'),[1,2,3]);
  assert.deepEqual(signal(run,'slow/manual'),[]);
  run.step();
  assert.deepEqual(run.view().states.slow,{wire:[1,2,3],manual:['first','second','later'],vector:[6,-6,3],level:3});
  assert.deepEqual(signal(run,'slow/wire'),[1,2,3]);
  run.step();
  assert.deepEqual(signal(run,'slow/wire'),[]);
  run.step();
  assert.deepEqual(run.view().states.slow.wire,[4,5,6,7,8,9]);
  assert.deepEqual(run.view().states.slow.manual,[]);
});

test('combinational events reach a downstream solver at a shared boundary', () => {
  const source = () => ({initial:()=>0,step:state=>state+1,combinational:true,
    outputs:{events:'event'},output:state=>({events:state?[state]:[]})});
  const consumer = () => ({initial:()=>[],inputs:{events:'event'},step:(state,ctx)=>state.concat(ctx.input.events)});
  const run = W.runtime.create({systems:{
    fast:{kind:'source',schedule:{substeps:4}},consumer:{kind:'consumer'}
  },connections:[{from:'fast/events',to:'consumer/events'}]},{implementations:{source,consumer}});
  run.step();
  assert.deepEqual(run.view().states.consumer,[1,2,3,4]);
  run.step();
  assert.deepEqual(run.view().states.consumer,[1,2,3,4,5,6,7,8]);
});

test('a failed substep rolls back the tick, event buffers, commands and profiler counts', () => {
  let fail = true;
  const source = () => ({initial:()=>0,outputs:{value:'event'},output:state=>({value:state?[state]:[]}),
    step(state,ctx) {
      ctx.emit('worked',{substep:ctx.substep});
      if (fail && ctx.substep===2) throw Error('rejected substep');
      return state+1;
    }});
  const sink = () => ({initial:()=>[],inputs:{value:'event'},step:(state,ctx)=>state.concat(ctx.input.value)});
  const run = W.runtime.create({systems:{fast:{kind:'source',schedule:{substeps:2}},slow:{kind:'sink'}},
    connections:[{from:'fast/value',to:'slow/value'}]},{implementations:{source,sink},profile:true});
  const before = run.checkpoint();
  assert.throws(()=>run.step(),/rejected substep/);
  assert.deepEqual(run.checkpoint(),before);
  assert(Object.values(run.profile()).every(row=>row.calls===0 && row.ms===0));
  fail=false;
  run.step();
  assert.equal(run.profile().fast.calls,2);
  assert.deepEqual(run.view().states.slow,[1]);
  assert.deepEqual(run.checkpoint().sampling['slow/value'],[2]);
  assert.deepEqual(run.events.map(row=>row.substep),[1,2]);
});

test('the native yard keeps all fast wheel contacts until the slow wear update can consume them', () => {
  const run = W.runtime.create(manifest,{profile:true});
  run.advance(3);
  assert.equal(run.checkpoint().sampling['trail/contacts'].length,12);
  assert.deepEqual(run.view().states.trail.cells,{});
  const branch = run.fork();
  branch.step();
  run.step();
  assert.deepEqual(run.checkpoint(),branch.checkpoint());
  assert.equal(signal(run,'trail/contacts').length,15);
  assert.equal(run.checkpoint().sampling['trail/contacts'].length,1);
  assert.equal(signal(run,'cart/contacts').length,4);
  assert.equal(signal(run,'mean-temperature/value'),10.5);
  assert.equal(signal(run,'heater/value'),true);
  assert.equal(run.profile().cart.calls,16);
  assert.equal(run.profile().heater.calls,4);
  assert.equal(run.profile().trail.calls,1);
});

test('a slow spatial reader resumes with edits that arrived while it was skipped', () => {
  const reader = () => ({initial:()=>null,dependencies:{reads:['land/height']},
    step(_,ctx) {
      const changes = ctx.spatial.changes();
      return {height:ctx.query.probe('land/height',[0,0,0]).value,
        notices:changes.map(row=>row.reason)};
    }});
  const run = W.runtime.create({systems:{
    land:{kind:'fields',config:{fields:{height:{default:0}}}},
    ordinary:{kind:'reader'},slow:{kind:'reader',schedule:{every:3}}
  },commands:[{tick:1,action:'land/set',args:{field:'height',region:{
    bounds:{min:[-1,-1,-1],max:[1,1,1]},value:5
  }}}]},{implementations:{reader}});
  run.step();
  assert.equal(run.view().states.slow,null);
  assert.equal(run.checkpoint().spatialSampling.slow.length,1);
  const branch=run.fork();
  branch.advance(3);
  assert.deepEqual(branch.view().states.slow,{height:5,notices:['field-region-edited']});
  assert.deepEqual(branch.view().states.ordinary,{height:5,notices:[]});
  assert.equal(branch.dependencies().changes[0].deliveredTo,'slow');
  assert.equal(branch.checkpoint().spatialSampling,undefined);
});

test('invalid schedules and incompatible samplers fail world validation', () => {
  const lane = schedule => ({kind:'control',schedule});
  assert.throws(()=>W.runtime.validate({systems:{bad:lane({substeps:2,every:2})}}),/A schedule needs/);
  assert.throws(()=>W.runtime.validate({systems:{a:lane({substeps:7}),b:lane({substeps:11})}}),/exceed 64 substeps/);
  assert.throws(()=>W.runtime.validate({systems:{a:lane({every:1.5})}}),/A schedule needs/);
  assert.throws(()=>W.runtime.validate({systems:{a:{kind:'control',config:{op:'not'}},b:{kind:'control',config:{op:'not'}}},
    connections:[{from:'a/value',to:'b/value',sample:'average'}]}),/Invalid sampling/);
});

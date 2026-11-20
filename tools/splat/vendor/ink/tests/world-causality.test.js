const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const {KIT:{world:W}} = require('..').load();
const mill = require('../examples/world-causal-mill.json');
const trace = (run,args,entity) => run.query().trace('world/cause',entity?{entity}:{},args);

test('the mill trace follows actual delayed samples back to the overload and survives replay', () => {
  const run=W.runtime.create(mill);
  run.advance(8);
  const result=trace(run,{kind:'machine-stop'},'mill-wheel');
  const {nodes,edges,root}=result.value;
  assert.equal(result.value.status,'complete');
  assert.equal(nodes[0].id,root);
  assert.deepEqual(nodes.filter(row=>row.type==='event'||row.type==='decision'||row.type==='command')
    .map(row=>[row.tick,row.system,row.kind]),[
    [6,'mill','machine-stop'],[6,'mill','shaft-stopped'],[5,'motor','branch-selected'],
    [4,'breaker','threshold-crossed'],[3,'world','scheduled-command']
  ]);
  const threshold=nodes.find(row=>row.kind==='threshold-crossed');
  assert.deepEqual(threshold.data,{reading:12,threshold:8,comparison:'>=',result:true});
  const samples=nodes.filter(row=>row.type==='input'&&row.data.delay===1);
  assert.deepEqual(samples.map(row=>row.tick),[6,5,4]);
  for (const row of samples) {
    const parent=nodes.find(node=>node.id===row.parents[0]);
    assert.equal(parent.tick,row.tick-1);
    assert.equal(parent.port,row.data.source);
    assert(edges.some(edge=>edge.effect===row.id&&edge.cause===parent.id));
  }
  assert.equal(trace(run,{event:'6.0',atTick:5}).status,'missing');
  assert.equal(trace(run,{port:'mill/speed.shaft'}).value.nodes[0].data.value,0);
  assert.equal(trace(run,{port:'mill/speed.shaft',atTick:5}).value.nodes[0].data.value>0,true);
  assert.deepEqual(trace(W.runtime.replay(JSON.parse(JSON.stringify(run.recording()))),{event:'6.0'}),
    trace(run,{event:'6.0'}));
});

test('a native shaft stall reports its measured load and mechanical capacity', () => {
  const run=W.runtime.create({...mill,connections:[],commands:[],systems:{
    pressure:{kind:'fields',config:{fields:{load:{units:'N',default:7}}}},
    mill:{kind:'mechanics',config:{...mill.systems.mill.config,joints:{
      shaft:{...mill.systems.mill.config.joints.shaft,speed:3,load:2,loadField:'pressure/load',capacity:8}
    }}}
  }});
  run.step();
  const result=trace(run,{kind:'machine-stall'}).value;
  assert.equal(result.status,'complete');
  assert.equal(result.nodes[0].basis,'declared');
  const reason=result.nodes.find(row=>row.kind==='load-exceeded').data;
  assert.equal(reason.load,9);
  assert.equal(reason.capacity,8);
  assert.deepEqual(reason.contributors,[{joint:'shaft',ratio:1,staticLoad:2,field:'pressure/load',
    status:'ok',reading:7,load:9}]);
});

test('a system can attach a field reading and the selected signal without implying other inputs caused a decision', () => {
  const gauge = () => ({initial:()=>false,inputs:{armed:'bool',unused:'number'},outputs:{trip:'bool'},
    step(state,ctx) {
      const {result,cause}=ctx.causal.read('air/temperature',[0,0,0]);
      const trip=ctx.input.armed&&result.value>35;
      if (trip && !state) {
        const why=ctx.causal.record('high-temperature',{temperature:result.value,threshold:35},
          {inputs:['armed'],causes:[cause],outputs:['trip']});
        ctx.emit('alarm',{entity:'room'},[why]);
      }
      return trip;
    },output:state=>({trip:state})});
  const run=W.runtime.create({causality:true,history:{enabled:false},systems:{
    air:{kind:'fields',config:{fields:{temperature:{units:'degC',default:41}}}},gauge:{kind:'gauge'}
  },commands:[
    {tick:1,action:'world/input',args:{port:'gauge/armed',value:true}},
    {tick:1,action:'world/input',args:{port:'gauge/unused',value:1234}}
  ]},{implementations:{gauge}});
  run.step();
  const result=trace(run,{kind:'alarm'},'room').value;
  assert.equal(result.status,'complete');
  assert.equal(run.history.length,0);
  assert.equal(result.nodes.find(row=>row.type==='reading').data.result.provenance.units,'degC');
  assert.equal(result.nodes.find(row=>row.type==='reading').data.result.value,41);
  assert(!result.nodes.some(row=>row.port==='gauge/unused'||row.data.args?.port==='gauge/unused'));
  assert.deepEqual(trace(run,{port:'gauge/trip'}).value.nodes[0].parents,[result.nodes.find(row=>row.kind==='high-temperature').id]);
});

test('cross-rate sums, averages and delayed events link to the publications actually consumed', () => {
  const source=()=>({initial:()=>0,step:n=>n+1,outputs:{count:'number',events:'event'},
    output:n=>({count:n?1:0,events:n?[n]:[]})});
  const reader=()=>({initial:()=>null,inputs:{total:'number',mean:'number',notice:'event'},step:(_,ctx)=>{
    ctx.causal.record('batch-read',{...ctx.input},{inputs:['total','mean','notice']});
    return ctx.input;
  }});
  const opts={implementations:{source,reader}};
  const run=W.runtime.create({causality:true,systems:{
    fast:{kind:'source',schedule:{substeps:3}},slow:{kind:'reader',schedule:{every:2}}
  },connections:[
    {from:'fast/count',to:'slow/total',sample:'sum'},
    {from:'fast/count',to:'slow/mean',sample:'average'},
    {from:'fast/events',to:'slow/notice',delay:1}
  ]},opts);
  run.step();
  const fork=run.fork();
  fork.step();
  run.step();
  assert.deepEqual(run.checkpoint(),fork.checkpoint());
  const result=trace(fork,{kind:'batch-read'}).value;
  assert.deepEqual(result.nodes[0].data,{total:5,mean:5/6,notice:[1,2,3]});
  const byId=new Map(result.nodes.map(row=>[row.id,row]));
  const total=result.nodes.find(row=>row.port==='slow/total');
  assert.equal(total.parents.length,5);
  assert.deepEqual(total.parents.map(parent=>[byId.get(parent).tick,byId.get(parent).substep]),
    [[1,1],[1,2],[1,3],[2,1],[2,2]]);
  const notices=result.nodes.find(row=>row.port==='slow/notice');
  assert.deepEqual(notices.parents.map(parent=>byId.get(parent).data.value),[[1],[2],[3]]);
  assert.deepEqual(W.runtime.replay(JSON.parse(JSON.stringify(run.recording())),opts).checkpoint(),run.checkpoint());
});

test('bounded retention and traversal report missing ancestors', () => {
  const world={causality:{limit:2},systems:{breaker:{kind:'control',config:{op:'threshold',threshold:8}}},
    commands:[12,13,14].map((value,i)=>({tick:i+1,action:'world/input',args:{port:'breaker/value',value}}))};
  const run=W.runtime.create(world);
  run.step();
  const result=trace(run,{port:'breaker/value'}).value;
  assert.equal(result.nodes.length,2);
  assert.equal(result.status,'partial');
  assert(result.gaps.some(gap=>gap.reason==='retention'));
  assert.equal(run.checkpoint().causality.nodes.length,2);
  assert.equal(result.dropped,4);
  run.step();
  run.step();
  const held=trace(run,{port:'breaker/value'}).value;
  assert.equal(held.nodes[0].basis,'held');
  assert.equal(held.nodes[0].data.value,true);
  assert.equal(held.status,'partial');
  const full=W.runtime.create({...world,causality:true});
  full.advance(3);
  assert.equal(trace(full,{port:'breaker/value',maxDepth:0}).value.gaps[0].reason,'depth');
  assert.equal(trace(full,{port:'breaker/value'}).value.nodes[0].tick,1);
  assert.equal(trace(full,{port:'breaker/value',direction:'input'}).value.nodes[0].data.value,14);
  assert.equal(W.runtime.create({...world,causality:false}).checkpoint().causality,undefined);
  assert.throws(()=>W.runtime.validate({...world,causality:{limit:0}}),/Causality limit/);
});

test('a failed tick publishes no causal nodes and can retry with deterministic ids', () => {
  let fail=true;
  const system=()=>({initial:()=>0,step:(n,ctx)=>{
    const decision=ctx.causal.record('work',{n});
    ctx.emit('worked',{n},[decision]);
    if (fail) throw Error('rejected step');
    return n+1;
  }});
  const run=W.runtime.create({causality:true,systems:{job:{kind:'system'}}},{implementations:{system}});
  const before=run.checkpoint();
  assert.throws(()=>run.step(),/rejected step/);
  assert.deepEqual(run.checkpoint(),before);
  fail=false;
  run.step();
  assert.deepEqual(trace(run,{event:'1.0'}).value.nodes.map(row=>row.id),['c.1.1','c.1.0']);
});

test('the CLI traces an event in a portable mill recording', () => {
  const cwd=path.join(__dirname,'..'), dir=fs.mkdtempSync(path.join(os.tmpdir(),'ink-mill-cause-'));
  function cli(...args) {
    const proc=spawnSync(process.execPath,['cli/ink-studio.js',...args,'--json'],{cwd,encoding:'utf8'});
    assert.equal(proc.status,0,proc.stderr);
    return JSON.parse(proc.stdout);
  }
  try {
    const file=path.join(dir,'mill.run.json');
    cli('sim','run','examples/world-causal-mill.json','--ticks','8','--record',file);
    const outcome=cli('trace',file,'world/cause','--args','{"event":"6.0"}');
    assert.equal(outcome.value.status,'complete');
    assert.equal(outcome.value.nodes.at(-1).data.commandId,'pump-overload');
    assert.equal(cli('sim','replay',file).tick,8);
  } finally {
    fs.rmSync(dir,{recursive:true,force:true});
  }
});

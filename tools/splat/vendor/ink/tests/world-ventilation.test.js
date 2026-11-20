const test=require('node:test');
const assert=require('node:assert/strict');
const studio=require('..'), kit=studio.load(), {KIT:{world:W}}=kit;
const example=require('../examples/world-ventilated-shelter.json');

const near=(a,b,eps=1e-8)=>assert.ok(Math.abs(a-b)<=eps,`${a} differs from ${b}`);
const clone=value=>JSON.parse(JSON.stringify(value));
const read=(run,key,target,args)=>run.query().probe('air/'+key,target,args).value;
const examplePosition=[-1.33,.15,.17];
const room=(run,room)=>read(run,'rooms',{}, {room});
const edge=(run,opening)=>read(run,'openings',{}, {opening});
const box=(x,concentrations={},temperature=20)=>({bounds:{min:[x,0,0],max:[x+1,1,1]},concentrations,temperature});
const scene=config=>({dt:.1,systems:{air:{kind:'ventilation',config}}});
const input=(tick,pin,value)=>({tick,action:'world/input',args:{port:'air/'+pin,value}});
const balanced=run=>{
  for(const row of Object.values(read(run,'budget')))
    near(row.error,0,1e-8*Math.max(1,row.initial+row.imported+row.emitted));
};

test('a fan needs a balanced air path and an opened return permits circulation',()=>{
  const run=W.runtime.create(scene({
    rooms:{workshop:box(0,{smoke:1})},
    openings:{
      supply:{from:'outside',to:'workshop',fan:2,mixing:0},
      return:{from:'workshop',to:'outside',opening:0,mixing:0}
    }
  }));
  run.step();
  near(room(run,'workshop').airQuality,.5);
  near(room(run,'workshop').pressure,2);
  near(edge(run,'supply').flow,0);
  run.schedule([input(2,'opening.return',1)]);
  run.step();
  near(edge(run,'supply').flow,1);
  near(edge(run,'return').flow,1);
  near(room(run,'workshop').concentrations.smoke,1/1.1);
  near(room(run,'workshop').temperature,20);
  near(read(run,'budget').smoke.exported,.1/1.1);
  balanced(run);
});

test('a passive opening mixes heat, vapor and arbitrary tracers in a sealed pair',()=>{
  const run=W.runtime.create(scene({
    tracers:{dust:{units:'g'}},rooms:{a:box(0,{smoke:1,dust:.8,humidity:.01},30),b:box(1,{humidity:0},10)},
    openings:{door:{from:'a',to:'b',mixing:1,opening:0}}
  }));
  run.schedule([input(2,'opening.door',1),input(3,'opening.door',0)]);
  run.step();
  near(room(run,'b').concentrations.dust,0);
  run.step();
  assert.equal(edge(run,'door').flow,0);
  near(room(run,'b').concentrations.smoke,1/12);
  near(room(run,'b').concentrations.dust,.8/12);
  near(room(run,'b').concentrations.humidity,.01/12);
  near(room(run,'b').temperature,10+20/12);
  run.step();
  near(room(run,'b').concentrations.smoke,1/12);
  assert.deepEqual(run.history.map(row=>row.kind),['air-opening-opened','air-opening-closed']);
  assert.equal(run.query().field('air/dust').units,'g/world^3');
  assert.equal(read(run,'budget').dust.units,'g');
  balanced(run);
});

test('local wind reverses a directed loop and tracks exterior exchange, sources and settling',()=>{
  const fixture=scene({
    windField:'climate/wind',tracers:{dust:{units:'g',decay:.5}},rooms:{bay:box(0),shed:box(1)},
    exterior:{yard:{temperature:25,concentrations:{humidity:.016}},alley:{temperature:15}},
    sources:{tool:{room:'bay',rates:{dust:.6,heat:300}}},
    openings:{
      inlet:{from:'yard',to:'bay',mixing:0,wind:{at:[0,.5,.5],direction:[1,0,0]}},
      hatch:{from:'bay',to:'shed',mixing:0},outlet:{from:'shed',to:'alley',mixing:0}
    }
  });
  fixture.systems.climate={kind:'fields',config:{fields:{
    wind:{type:'vec2',axes:'xz',units:'world/s',default:[3,0]}
  }}};
  const run=W.runtime.create(fixture);
  run.step();
  near(edge(run,'inlet').windDrive,3);
  for(const key of ['inlet','hatch','outlet'])near(edge(run,key).flow,1);
  const ahead=run.query().trace('air/airflow',{}, {from:'yard',to:'alley'});
  assert.deepEqual(ahead.value.path.map(row=>row.opening),['inlet','hatch','outlet']);
  assert.ok(room(run,'shed').concentrations.dust>0);
  assert.ok(room(run,'bay').temperature>20&&room(run,'bay').concentrations.humidity>.008);
  near(read(run,'budget').heat.emitted,30);
  near(read(run,'budget').dust.emitted,.06);
  assert.ok(read(run,'budget').dust.removed>0&&read(run,'budget').dust.exported>0);
  run.schedule([{tick:2,action:'climate/set',args:{field:'wind',region:{
    bounds:{min:[-1,-1],max:[1,1]},value:[-3,0]
  }}}]);
  run.step();
  for(const key of ['inlet','hatch','outlet'])near(edge(run,key).flow,-1);
  assert.equal(run.query().trace('air/airflow',{}, {from:'yard',to:'alley'}).status,'blocked');
  assert.equal(run.query().trace('air/airflow',{}, {from:'alley',to:'yard'}).status,'ok');
  assert.ok(run.dependencies().affected.some(row=>row.system==='air'));
  balanced(run);
});

test('a fan recirculates in a sealed loop without losing suspended material',()=>{
  const run=W.runtime.create(scene({
    rooms:{a:box(0,{smoke:.84}),b:box(1),c:box(2)},
    openings:{ab:{from:'a',to:'b',fan:6,mixing:0},
      bc:{from:'b',to:'c',mixing:0},ca:{from:'c',to:'a',mixing:0}}
  }));
  run.advance(10);
  for(const key of ['ab','bc','ca'])near(edge(run,key).flow,2);
  assert.ok(room(run,'b').concentrations.smoke>.1&&room(run,'c').concentrations.smoke>.1);
  near(read(run,'budget').smoke.amount,.84);
  near(read(run,'budget').smoke.exported,0);
  balanced(run);
});

test('clearance gates use the current revision and invalid field bindings fail validation',()=>{
  const fixture=scene({rooms:{a:box(0,{smoke:1}),b:box(1)},openings:{
    path:{from:'a',to:'b',mixing:2,gate:{field:'slab/clearance',points:[[1,.5,.5]],radius:.04}}
  }});
  fixture.systems.slab={kind:'volume',config:{bounds:{min:[0,0,0],max:[2,1,1]},cell:.25,
    materials:{stone:[0x606671]},initial:[{op:'fill',material:'stone',
      shape:{kind:'box',at:[1,.5,.5],half:[.15,.4,.4]}}]}};
  const run=W.runtime.create(fixture);
  run.step();
  near(edge(run,'path').opening,0);
  near(room(run,'b').concentrations.smoke,0);
  run.schedule([{tick:2,action:'slab/cut',args:{shape:{kind:'box',at:[1,.5,.5],half:[.3,.2,.2]}}}]);
  run.step();
  near(edge(run,'path').opening,1);
  assert.ok(room(run,'b').concentrations.smoke>.1);
  balanced(run);
  const bad=clone(fixture);
  bad.systems.air.config.openings.path.gate.field='air/smoke';
  assert.throws(()=>W.runtime.create(bad),/numeric clearance field/);
});

test('opening the smoky shelter clears it and a creature chooses the newly suitable room',()=>{
  const closed=W.runtime.create({...example,commands:example.commands.slice(0,1)});
  closed.advance(20);
  const open=closed.fork();
  open.schedule(example.commands.slice(1));
  const probe=run=>run.query().probe('home/suitability',examplePosition,{species:'helper'}).value;
  const agent=run=>run.query().probe('scout/agents').value.helper;
  assert.equal(probe(closed).suitable,false);
  assert.ok(agent(closed).position[0]>0);
  const render=run=>W.visual(kit,run.view(),run.query()).shapedAtmosphere[0].field;
  const dense=render(closed).sample(-1.7,.7,0);
  assert.ok(dense>.5);
  assert.equal(render(closed).sample(2.9,.7,0),0);
  open.advance(120);closed.advance(120);
  assert.equal(probe(open).suitable,true);
  assert.equal(probe(closed).suitable,false);
  assert.ok(agent(open).position[0]<-1&&agent(closed).position[0]>0);
  assert.ok(room(open,'shelter').concentrations.smoke<.02);
  assert.ok(room(open,'shelter').temperature<room(closed,'shelter').temperature);
  assert.ok(render(open).sample(-1.7,.7,0)<dense*.1);
  const field=open.query().probe('air/air-quality',examplePosition,{explain:true});
  assert.equal(field.provenance.source.room,'shelter');
  balanced(open);balanced(closed);
  assert.deepEqual(clone(W.runtime.replay(clone(open.recording())).checkpoint()),clone(open.checkpoint()));
});

const test=require('node:test');
const assert=require('node:assert/strict');
const studio=require('..'), kit=studio.load(), {KIT:{world:W}}=kit;
const example=require('../examples/world-thawing-ford.json');
const tolerance=(a,b,eps=1e-8)=>assert.ok(Math.abs(a-b)<=eps,`${a} differs from ${b}`);
const json=value=>JSON.parse(JSON.stringify(value));
const area={min:[0,0],max:[1,1]}, at=[.5,0,.5];
const phase=(run,point=at)=>run.query().probe('river/phase-state',point).value;
const read=(run,field,args)=>run.query().probe('river/'+field,{},args).value;
const patch=(bounds,value)=>({bounds,value});
const fixture=(thermal,config={})=>({dt:.1,systems:{river:{kind:'water',config:{
  width:1,height:1,initial:[patch(area,1)],
  thermal:{ambientTemperature:0,heatCapacity:10,waterHeatCapacity:4,latentFusion:20,latentVaporization:100,
    conductance:0,conductivity:0,evaporation:0,condensation:0,vaporDiffusivity:0,...thermal},...config
}}}});
const heat=(tick,energy,bounds=area)=>({tick,action:'river/heat',args:{bounds,energy}});
const balance=run=>{
  tolerance(read(run,'mass').error,0);
  tolerance(read(run,'heat').error,0);
};

test('latent heat keeps a melting cell at the freezing point and conserves water',()=>{
  const run=W.runtime.create(fixture({ambientTemperature:-1}));
  assert.equal(phase(run).phase,'ice');
  tolerance(phase(run).ice,1);
  tolerance(run.query().probe('river/surface-height',at).value,1);
  tolerance(run.query().probe('river/bed',at).value,0);
  run.schedule([heat(1,24),heat(2,10)]);
  run.step();
  assert.equal(phase(run).phase,'mixed');
  tolerance(phase(run).temperature,0);
  tolerance(phase(run).liquid,.5);
  tolerance(phase(run).ice,.5);
  run.step();
  assert.equal(phase(run).phase,'liquid');
  tolerance(phase(run).liquid,1);
  tolerance(read(run,'heat').appliedEnergy,34);
  balance(run);
  const saved=json(run.checkpoint());
  assert.deepEqual(json(W.runtime.replay(json(run.recording())).checkpoint()),saved);
});

test('a dry air pocket evaporates liquid and cooling drives condensation',()=>{
  const run=W.runtime.create(fixture({ambientTemperature:20,saturation:.18,evaporation:3,condensation:4}));
  run.advance(12);
  const warm=phase(run);
  assert.ok(warm.liquid<.85&&warm.vapor>.15&&warm.temperature<20);
  run.schedule([heat(13,-330)]);
  run.advance(26);
  const cooled=phase(run);
  assert.ok(cooled.vapor<warm.vapor&&cooled.ice>0);
  assert.ok(read(run,'heat').evaporated>0&&read(run,'heat').condensed>0);
  balance(run);
});

test('vapor diffusion and water currents transport moisture and heat conservatively',()=>{
  const vaporOnly=W.runtime.create(fixture({initialVapor:[patch(area,.7)],vaporDiffusivity:1},{width:2,initial:[]}));
  vaporOnly.advance(4);
  assert.ok(phase(vaporOnly,[1.5,0,.5]).vapor>.1);
  tolerance(read(vaporOnly,'mass').vapor,.7);
  balance(vaporOnly);
  const run=W.runtime.create(fixture({initialTemperature:[patch(area,20)]},{width:2,
    sediment:{erodibleDepth:.01,initial:[patch(area,.03)]}}));
  run.advance(8);
  assert.ok(phase(run,[1.5,0,.5]).liquid>.15&&phase(run,[1.5,0,.5]).temperature>1);
  assert.ok(phase(run).liquid<1);
  balance(run);
  tolerance(read(run,'sediment').error,0);
});

test('rain and account transfers credit incoming heat and export the donor enthalpy',()=>{
  const scene=fixture({sourceTemperature:10},{initial:[],rain:.2,drain:.05,accounts:{cell:[.5,.5]}});
  scene.systems.source={kind:'store',config:{accounts:{tank:{resource:'water',units:'world^3',initial:.4}}}};
  const run=W.runtime.create(scene);
  run.schedule([
    {tick:1,action:'world/transfer',args:{from:'source/tank',to:'river/cell',amount:.2}},
    {tick:2,action:'world/transfer',args:{from:'river/cell',to:'source/tank',amount:.1}}
  ]);
  run.advance(2);
  const h=read(run,'heat');
  tolerance(h.sourceEnergy,.24*(20+4*10));
  assert.ok(h.exportedEnergy>2);
  balance(run);
});

test('the ford becomes unsafe after the frozen gate thaws and admits water',()=>{
  const run=W.runtime.create(example);
  const route=()=>run.query().trace('nav/route',[1.7,.66,-1.25],
    {to:[1.7,.66,1.25],radius:.1,maxWade:.18,maxSlope:10}).value;
  const gate=()=>read(run,'gates',{gate:'sluice'});
  run.advance(35);
  assert.equal(route().status,'ok');
  assert.equal(gate().jammed,true);
  assert.equal(gate().effective,0);
  assert.equal(gate().command,.88);
  assert.equal(phase(run,[-.2,0,.2]).material,'winter-ford/cold-stone');
  const ice=W.visual(kit,run.view(),run.query());
  assert.ok(W.query.fromScene(ice).select({material:'ice'}).length>0);
  run.advance(140);
  assert.equal(gate().jammed,false);
  assert.equal(gate().effective,.88);
  assert.equal(route().blocked.kind,'water');
  assert.ok(read(run,'heat').condensed>0);
  assert.deepEqual(run.history.filter(e=>e.kind.startsWith('gate-')).map(e=>e.kind),['gate-frozen','gate-thawed']);
  balance(run);
  assert.deepEqual(json(W.runtime.replay(json(run.recording())).checkpoint()),json(run.checkpoint()));
});

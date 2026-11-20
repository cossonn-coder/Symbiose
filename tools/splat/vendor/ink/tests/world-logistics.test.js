const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: { world: W } } = require('..').load();
const example = require('../examples/world-harvest-logistics.json');
const grain = { type:'integer',units:'sack' };
const water = { type:'number',units:'world^3' };
const get = (run,field,args) => run.query().probe('flow/'+field,undefined,args).value;
const stock = (run,container,resource) => get(run,'stocks',{container,resource}).stock;
const stage = (run,process) => get(run,'processes',{process});
const link = (run,id) => get(run,'links',{link:id});
const supply = (run,args) => run.query().trace('flow/supply',undefined,args).value;
const transfer = (tick,from,to,amount) => ({tick,action:'world/transfer',args:{from,to,amount}});
const input = (tick,port,value) => ({tick,action:'world/input',args:{port:'flow/'+port,value}});
const simulate = (config,options={}) => W.runtime.create({dt:.1,...options,systems:{
  flow:{kind:'logistics',config},...options.systems
}});
const roundtrip = value => JSON.parse(JSON.stringify(value));

test('multi-resource reservations and output commits are atomic, including across restores', () => {
  const run = simulate({
    resources:{grain,water,meal:{type:'integer',units:'item'}},
    containers:{
      larder:{stocks:{grain:{initial:4,max:8},water:{max:2}}},
      kitchen:{stocks:{meal:{initial:2,max:2},water:{max:2}}}
    },
    recipes:{cook:{duration:.2,inputs:{grain:2,water:.3},outputs:{meal:1,water:.1}}},
    processes:{cook:{recipe:'cook',inputs:{grain:'larder',water:'larder'},outputs:{meal:'kitchen',water:'kitchen'}}}
  },{systems:{external:{kind:'store',config:{accounts:{
    water:{resource:'water',...water,initial:2},meals:{resource:'meal',type:'integer',units:'item',initial:0}
  }}}}});
  run.step();
  assert.equal(stock(run,'larder','grain'),4);
  assert.deepEqual(stage(run,'cook').blocked,[{account:'flow/larder.water',amount:.3,available:0,reason:'missing-stock'}]);
  run.schedule([transfer(2,'external/water','flow/larder.water',.6),transfer(5,'flow/kitchen.meal','external/meals',1)]);
  run.advance(2);
  assert.equal(get(run,'ledger').grain.inProgress,2);
  assert.equal(get(run,'ledger').water.received,.6);
  const checkpoint = roundtrip(run.checkpoint());
  const branch = W.runtime.create(checkpoint.world,{checkpoint});
  branch.advance(4);
  assert.equal(stage(branch,'cook').remaining,0);
  assert.equal(stage(branch,'cook').completed,0);
  assert.equal(stock(branch,'kitchen','water'),0);
  assert.equal(supply(branch,{process:'cook'}).bottlenecks[0].reason,'output-full');
  branch.advance(5);
  assert.equal(stage(branch,'cook').completed,1);
  assert.equal(stock(branch,'kitchen','water'),.1);
  assert.equal(get(branch,'ledger').meal.sent,1);
  assert.equal(branch.view().signals['flow/completed.cook'],1);
  for (const account of Object.values(get(branch,'ledger'))) assert(Math.abs(account.error)<1e-12);
  assert.deepEqual(W.runtime.replay(roundtrip(branch.recording())).checkpoint(),branch.checkpoint());
  assert.equal(run.view().tick,2);
});

test('shipments retain stock in transit, partly unload, and complete with dispatch disabled', () => {
  const run = simulate({resources:{grain},containers:{
    source:{position:[0,0,0],stocks:{grain:{initial:8}}},
    sink:{position:[2,0,0],stocks:{grain:{initial:2,max:4}}}
  },links:{cart:{resource:'grain',from:'source',to:'sink',amount:4,travel:.2,slots:1,guides:[[0,0,1]]}}},
  {systems:{external:{kind:'store',config:{accounts:{grain:{resource:'grain',...grain,initial:0}}}}}});
  run.schedule([input(2,'enable-link.cart',false),transfer(4,'flow/sink.grain','external/grain',2)]);
  run.advance(2);
  assert.equal(link(run,'cart').inTransit,4);
  assert.equal(stock(run,'sink','grain'),2);
  const body = Object.values(get(run,'cargo'))[0];
  assert(body.position[0]>0 && body.position[0]<2 && body.position[2]>0);
  run.advance(3);
  assert.equal(stock(run,'sink','grain'),4);
  assert.equal(link(run,'cart').arrived,2);
  assert.equal(link(run,'cart').inTransit,2);
  assert.equal(link(run,'cart').reason,'destination-full');
  run.advance(4);
  assert.equal(link(run,'cart').status,'disabled');
  assert.equal(link(run,'cart').arrived,2);
  assert.equal(link(run,'cart').inTransit,0);
  assert.equal(stock(run,'source','grain'),4);
  assert.equal(get(run,'ledger').grain.error,0);
  assert.deepEqual(run.query().inspect().accounts.map(row=>row.name),['external/grain','flow/sink.grain','flow/source.grain']);
});

test('exact, rate-driven and competing operations use stable priorities and preserve integer stocks', () => {
  const run = simulate({resources:{grain},containers:{
    field:{stocks:{grain:{initial:8}}}, west:{stocks:{grain:{max:1}}}, east:{stocks:{grain:{max:10}}}
  },links:{
    fast:{resource:'grain',from:'field',to:'west',amount:2,priority:10,mode:'exact'},
    meter:{resource:'grain',from:'field',to:'east',rate:1}
  }});
  run.advance(39);
  assert.equal(link(run,'fast').reason,'destination-full');
  assert.equal(stock(run,'west','grain'),0);
  assert.equal(stock(run,'east','grain'),3);
  run.advance(40);
  assert.equal(stock(run,'east','grain'),4);
  assert.equal(get(run,'ledger').grain.error,0);

  const contested = simulate({
    resources:{grain},containers:{field:{stocks:{grain:{initial:1}}}},
    recipes:{use:{duration:.1,inputs:{grain:1}}},
    processes:{first:{recipe:'use',inputs:{grain:'field'}},second:{recipe:'use',inputs:{grain:'field'},priority:1}}
  });
  contested.step();
  assert.equal(stage(contested,'second').completed,1);
  assert.equal(stage(contested,'first').completed,0);
});

test('substeps use the simulation clock for arrivals and preserve cargo across checkpoints', () => {
  const config = {resources:{grain},containers:{
    source:{stocks:{grain:{initial:4}}}, sink:{stocks:{grain:{}}}
  },links:{cart:{resource:'grain',from:'source',to:'sink',amount:1,travel:.15}}};
  const run = W.runtime.create({dt:.1,systems:{flow:{kind:'logistics',schedule:{substeps:4},config}}});
  run.schedule([input(2,'enable-link.cart',false)]);
  run.advance(2);
  assert.equal(stock(run,'sink','grain'),2);
  assert.equal(link(run,'cart').inTransit,2);
  const resumed = run.fork();
  resumed.advance(3);
  assert.equal(stock(resumed,'sink','grain'),4);
  assert.equal(link(resumed,'cart').inTransit,0);
  assert.equal(get(resumed,'ledger').grain.error,0);
  assert.deepEqual(W.runtime.replay(roundtrip(resumed.recording())).checkpoint(),resumed.checkpoint());
});

test('a looping supply graph terminates, and validation rejects invalid stock bindings and trace names', () => {
  const config = {resources:{grain},containers:{a:{stocks:{grain:{}}},b:{stocks:{grain:{}}}},
    links:{out:{resource:'grain',from:'a',to:'b',amount:1},back:{resource:'grain',from:'b',to:'a',amount:1}}};
  const run = simulate(config);
  run.step();
  const trace = supply(run,{account:'flow/a.grain'});
  assert.equal(trace.nodes.length,4);
  assert.equal(trace.edges.length,4);
  assert.equal(trace.truncated,false);
  assert.equal(supply(run,{container:'a',resource:'grain',limit:2}).truncated,true);
  const missing = roundtrip(config);
  missing.links.out.to='missing';
  assert.throws(()=>simulate(missing),/Unknown logistics stock/);
  const fractional = roundtrip(config);
  fractional.links.out.amount=.5;
  assert.throws(()=>simulate(fractional),/Invalid quantity/);
  const route = roundtrip(config);
  route.links.out.route={trace:'missing/route',at:[0,0,0],to:[1,0,0]};
  assert.throws(()=>simulate(route),/Unknown, ambiguous or recursive logistics route/);
});

test('the market traces its shortage to the closed gate and recovers on the same replay', () => {
  const run = W.runtime.create(example);
  run.advance(150);
  const trace = supply(run,{process:'market'});
  const bottleneck = trace.bottlenecks.find(row=>row.reason==='route-closed');
  assert.equal(bottleneck.node,'link/grain-cart');
  assert.equal(bottleneck.obstruction.body,'gate-arm');
  assert(trace.nodes.some(row=>row.id==='process/mill'));
  assert(trace.nodes.some(row=>row.id==='process/bakery'));
  const served = stage(run,'market').completed;
  const branch = run.fork();
  branch.advance(250);
  assert(stage(branch,'market').completed>served);
  assert.equal(stage(run,'market').completed,served);
  assert.equal(stage(branch,'market').status,'working');
  for (const row of Object.values(get(branch,'ledger'))) assert.equal(row.error,0);
  assert.deepEqual(W.runtime.replay(roundtrip(branch.recording())).checkpoint(),branch.checkpoint());
});

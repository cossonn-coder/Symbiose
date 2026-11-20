const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { KIT: { world: W } } = require('..').load();
const example = require('../examples/world-transfers.json');
const number = (initial,max,extra={}) => ({resource:'water',units:'world^3',initial,max,...extra});
const store = accounts => ({kind:'store',config:{accounts}});
const amount = (run,account) => run.query().probe('world/account',{}, {account}).value.balance;
const receipts = run => run.query().probe('world/transfers').value.receipts;
const command = (tick,from,to,amount,mode='partial') => ({tick,action:'world/transfer',args:{from,to,amount,mode}});

test('water exchanges with a capped store and heat, stock and momentum share receipts', () => {
  const run = W.runtime.create(example), before = run.query();
  run.advance(1);
  const tick = receipts(run);
  assert.deepEqual(tick.map(row=>[row.requestId,row.requested,row.applied,row.status,row.limitedBy]),[
    ['heat',8,5,'partial',['destination']],
    ['bolts-full',3,0,'blocked',['destination']],
    ['brake',[2,-1,0],[2,-1,0],'full',[]],
    ['fill',5,2,'partial',['destination']]
  ]);
  assert.equal(amount(run,'basin/outlet'),6);
  assert.equal(amount(run,'cistern/water'),10);
  const mass = run.query().probe('basin/mass').value;
  assert.equal(mass.volume,6);
  assert.equal(mass.sent,2);
  assert.equal(mass.error,0);
  assert.equal(amount(run,'workshop/heat')+amount(run,'cistern/heat'),65);
  assert.deepEqual(amount(run,'dock/cart'),[3,2,0]);
  assert.deepEqual(amount(run,'dock/brake'),[2,-1,0]);
  assert.equal(before.probe('world/account',{}, {account:'basin/outlet'}).value.balance,8);
  const original = JSON.parse(JSON.stringify(run.checkpoint()));
  const resumed = W.runtime.create(original.world,{checkpoint:original});
  assert.deepEqual(receipts(resumed),tick);
  resumed.advance(2);
  assert.deepEqual(receipts(resumed).map(row=>[row.requestId,row.applied,row.status]),[
    ['bolts-partial',1,'partial'],['fill',0,'blocked']
  ]);
  assert.equal(amount(resumed,'cistern/bolts'),4);
  assert.equal(amount(resumed,'workshop/bolts'),6);
  assert.equal(amount(resumed,'basin/outlet')+amount(resumed,'cistern/water'),16);
  assert.deepEqual(W.runtime.replay(JSON.parse(JSON.stringify(resumed.recording()))).checkpoint(),resumed.checkpoint());
  const restored = run.fork();
  assert.deepEqual(receipts(restored),tick);
});

test('water accounts settle volume across grids with different cell areas', () => {
  const basin = (cell,depth) => ({kind:'water',config:{width:1,height:1,cell,
    initial:[{bounds:{min:[0,0],max:cell},value:depth}],accounts:{port:cell.map(n=>n/2)}}});
  const run = W.runtime.create({systems:{source:basin([2,.75],2),sink:basin([.7,.2],1)}});
  run.schedule([command(1,'source/port','sink/port',.48)]);
  run.step();
  const source = run.query().probe('source/mass').value, sink = run.query().probe('sink/mass').value;
  assert(Math.abs(source.volume-2.52)<1e-12);
  assert(Math.abs(sink.volume-.62)<1e-12);
  assert(Math.abs(source.volume+sink.volume-3.14)<1e-12);
  assert(Math.abs(source.error)+Math.abs(sink.error)<1e-12);
  assert.equal(receipts(run)[0].applied,.48);
});

test('scheduled requests settle before ordered links and the solver sees the settled snapshot', () => {
  const watch = () => ({initial:()=>({taken:0}),
    step(state,{query}) {
      const rows = query.probe('world/transfers').value;
      return {taken:rows.receipts.reduce((n,row)=>n+row.applied,0),tick:rows.tick,
        left:query.probe('world/account',{}, {account:'tank/stock'}).value.balance};
    }});
  const run = W.runtime.create({dt:.5,history:{enabled:false},systems:{
    tank:store({stock:number(5,10)}), a:store({stock:number(0,10)}), b:store({stock:number(0,3)}),
    relay:{kind:'exchange',config:{links:{first:{from:'tank/stock',to:'b/stock',rate:6},
      second:{from:'tank/stock',to:'a/stock',amount:3}}}},
    watch:{kind:'watch'}
  }},{implementations:{watch}});
  run.schedule([command(1,'tank/stock','a/stock',2)]);
  run.step();
  assert.deepEqual(receipts(run).map(row=>row.applied),[2,3,0]);
  assert.deepEqual(receipts(run)[2].limitedBy,['source']);
  assert.deepEqual(run.view().states.watch,{taken:5,tick:1,left:0});
  assert.deepEqual(run.history,[]);
  assert.deepEqual(run.query().inspect().accounts.map(row=>row.name),['a/stock','b/stock','tank/stock']);
  run.schedule([{tick:2,action:'world/input',args:{port:'relay/second',value:false}}]);
  run.step();
  assert.equal(receipts(run).length,1);
});

test('vectors share a clipping factor and integer moves remain integral', () => {
  const momentum = (initial,min,max) => ({resource:'momentum',units:'kg*m/s',type:'vec3',initial,min,max});
  const run = W.runtime.create({systems:{
    source:store({p:momentum([2,-2,0],[0,-10,null],[5,5,null])}),
    sink:store({p:momentum([0,2,0],[-10,1,null],[10,10,null])}),
    items:store({from:number(9,10,{type:'integer'}),to:number(7,10,{type:'integer'})})
  }});
  run.schedule([command(1,'source/p','sink/p',[4,-4,0]),command(1,'items/from','items/to',7)]);
  run.step();
  assert.deepEqual(receipts(run)[0].applied,[1,-1,0]);
  assert.deepEqual(amount(run,'source/p'),[1,-1,0]);
  assert.deepEqual(amount(run,'sink/p'),[1,1,0]);
  assert.equal(receipts(run)[1].applied,3);
  assert.equal(amount(run,'items/from'),6);
  assert.equal(amount(run,'items/to'),10);
  assert.throws(()=>run.schedule([command(2,'items/from','items/to',.5)]),/Invalid integer transfer quantity/);
  assert.throws(()=>run.schedule([command(2,'source/p','items/to',[1,2,3])]),/Incompatible transfer accounts/);
});

test('unrepresentable movements leave both balances intact', () => {
  const run = W.runtime.create({systems:{tank:store({source:number(1,2),sink:number(1e20,1e21)})}});
  run.schedule([command(1,'tank/source','tank/sink',1)]);
  run.step();
  assert.deepEqual(receipts(run)[0].limitedBy,['precision']);
  assert.equal(amount(run,'tank/source'),1);
  assert.equal(amount(run,'tank/sink'),1e20);
});

test('a writer that fails to settle rolls back the tick and its command can be retried', () => {
  let reject = true;
  const faulty = () => ({initial:()=>({balance:0}),accounts:{stock:{
    resource:'water',units:'world^3',type:'number',read:state=>({balance:state.balance}),
    write:(state,balance)=>reject?state:{balance}
  }}});
  const run = W.runtime.create({systems:{source:store({stock:number(8,10)}), a:store({stock:number(0,10)}),
    b:{kind:'faulty'}}},{implementations:{faulty}});
  run.schedule([command(1,'source/stock','a/stock',2),command(1,'source/stock','b/stock',3)]);
  const before = run.checkpoint();
  assert.throws(()=>run.step(),/did not post the agreed balance/);
  assert.deepEqual(run.checkpoint(),before);
  reject = false;
  run.step();
  assert.deepEqual([amount(run,'source/stock'),amount(run,'a/stock'),amount(run,'b/stock')],[3,2,3]);
});

test('a producer and solver can exchange a quantity through registered accounts', () => {
  const regulator = () => ({initial:()=>({rate:4}),
    requestTransfers(state,{query,dt}) {
      const sink = query.probe('world/account',{}, {account:'sink/stock'}).value;
      return sink.balance<sink.max ? [{from:'source/stock',to:'sink/stock',amount:state.rate*dt}] : [];
    }});
  const run = W.runtime.create({dt:.5,systems:{source:store({stock:number(4,4)}),
    sink:store({stock:number(4,5)}),regulator:{kind:'regulator'}}},{implementations:{regulator}});
  run.step();
  assert.equal(receipts(run)[0].applied,1);
  assert.equal(receipts(run)[0].requester,'regulator');
  run.step();
  assert.equal(receipts(run).length,0);
  assert.equal(amount(run,'source/stock'),3);
});

test('CLI probes and validates transfer accounts and their matching units', () => {
  const repo = path.join(__dirname,'..'), file = 'examples/world-transfers.json';
  const cli = (args) => {
    const result = spawnSync(process.execPath,['cli/ink-studio.js',...args,'--json'],{cwd:repo,encoding:'utf8'});
    assert.equal(result.status,0,result.stderr);
    return JSON.parse(result.stdout);
  };
  const info = cli(['inspect',file]);
  assert(info.actions.includes('world/transfer'));
  assert(info.accounts.some(row=>row.name==='basin/outlet' && row.units==='world^3'));
  assert.equal(cli(['probe',file,'--ticks','1','--field','world/transfers']).value.receipts.at(-1).applied,2);
  assert.throws(()=>W.runtime.validate({systems:{a:store({stock:number(1,10)}),b:store({stock:number(1,10,{units:'L'})})},
    commands:[command(1,'a/stock','b/stock',1)]}),/Incompatible transfer accounts/);
  assert.throws(()=>W.runtime.validate({systems:{bad:{kind:'water',config:{width:1,height:1,
    accounts:{a:[.3,.3],b:[.7,.7]}}}}}),/distinct cells/);
});

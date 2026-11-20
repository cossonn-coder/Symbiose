const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { KIT } = require('..').load();
const { world: W, procedural: P } = KIT;
const a = {axes:'xz',min:[0,0],max:[1,1]};
const away = {axes:'xz',min:[8,8],max:[9,9]};

test('the tracker matches fields and shared axes, including read halos and staged causes', () => {
  const plan = P.spatialDependencies.create({
    terrain:{writes:[{field:'terrain/bed',bounds:{axes:'xz',min:[0,0],max:[4,4]}},'terrain/color']},
    water:{reads:[{field:'terrain/bed',bounds:{min:[1.2,100,.2],max:[2,110,.8]},padding:.25}],writes:['water/edge']},
    graph:{reads:[{field:'water/edge',bounds:a}]}
  });
  const tx = plan.begin();
  tx.change('terrain','terrain/color',a,'paint');
  const edit = tx.change('terrain','terrain/bed',a,'cut');
  assert.deepEqual(tx.affected('water').map(row=>row.id),[edit.id]);
  assert.deepEqual(tx.affected('water',away),[]);
  assert.throws(()=>tx.change('terrain','terrain/bed',away,'out-of-domain'),/Undeclared spatial write/);
  const edge = tx.change('water','water/edge',a,'edge-changed',[edit.id]);
  tx.recordWork('graph','links',{rebuilt:['tile-1']},a);
  const report = tx.report();
  assert.deepEqual(report.changes[2].because,[edit.id]);
  assert.deepEqual(report.work[0].because,[edge.id]);
  assert.deepEqual(report.affected.map(row=>row.system),['graph','water']);
});

test('step writes survive checkpoints and become visible on the next stable snapshot', () => {
  const producer = () => ({initial:()=>({level:0}),dependencies:{writes:['value']},
    fields:{value:{type:'number',read:({state})=>W.query.ok(state.level)}},
    step(state,ctx) {
      if (ctx.tick!==1) return state;
      ctx.spatial.write('value',a,'moved');
      return {level:5};
    }});
  const watcher = () => ({initial:()=>({seen:0}),dependencies:{reads:[{field:'level/value',bounds:a}]},
    step(state,ctx) {
      if (!ctx.spatial.changes().length) return state;
      ctx.spatial.rebuilt('sample',{count:1},a);
      return {seen:ctx.query.probe('level/value').value};
    }});
  const run = W.runtime.create({systems:{level:{kind:'producer'},sensor:{kind:'watcher'}}},
    {implementations:{producer,watcher}});
  run.step();
  assert.equal(run.view().states.sensor.seen,0);
  assert.equal(run.checkpoint().dependencyWrites[0].field,'level/value');
  const fork = run.fork();
  fork.step();
  assert.equal(fork.view().states.sensor.seen,5);
  assert.deepEqual(fork.dependencies().work[0].because,[1]);
  run.step();
  assert.deepEqual(run.checkpoint(),fork.checkpoint());
  assert.equal(run.checkpoint().dependencyWrites,undefined);
});

test('a rejecting system leaves the spatial report and pending writes on the published tick', () => {
  const writer = () => ({initial:()=>0,dependencies:{writes:['flag']},
    step(state,ctx) {
      ctx.spatial.write('flag',a,'change');
      if (ctx.tick===2) throw Error('step rejected');
      return state+1;
    }});
  const run = W.runtime.create({systems:{writer:{kind:'writer'}}},{implementations:{writer}});
  run.step();
  const checkpoint = run.checkpoint(), report = run.dependencies();
  assert.throws(()=>run.step(),/step rejected/);
  assert.deepEqual(run.checkpoint(),checkpoint);
  assert.deepEqual(run.dependencies(),report);
});

test('a localized bed edit changes one water cell and only replans the nearby active route', () => {
  const bounds = {min:[0,-1,0],max:[8,3,8]};
  const world = {dt:.05,systems:{
    river:{kind:'water',config:{width:16,height:16,cell:.5}},
    walkers:{kind:'agents',config:{bounds,bed:'bed',cell:.5,replanTicks:60,
      species:{crew:{mode:'walk',speed:.2}},agents:{
        near:{species:'crew',position:[.75,0,1.25],goal:[6,0,1.25]},
        far:{species:'crew',position:[.75,0,6.25],goal:[6,0,6.25]}
      }}}
  }};
  const run = W.runtime.create(world);
  run.step();
  run.schedule([{tick:2,action:'river/bed',args:{bounds:{min:[3.22,1.22],max:[3.28,1.28]},height:.1}}]);
  run.step();
  const {work,changes} = run.dependencies();
  assert.deepEqual(work.map(row=>[row.kind,row.detail]),[
    ['water-bed',{sampled:1,changed:1,total:256}],['agent-route',{entity:'near',status:'ok'}]
  ]);
  assert.equal(changes[0].field,'river/bed');
  assert.equal(run.query().probe('river/bed',[3.25,0,1.25]).value,.1);
  assert.deepEqual(work.map(row=>row.because),[[1],[1]]);
  assert.equal(run.view().states.walkers.agents.far.retry,61);
});

test('paint skips physical rebuilds, and removing sparse terrain invalidates retained geometry', async () => {
  const {biomeWorld,biomeRecipes,biomeRevisions} = P;
  const author = biomeRecipes.create({fallback:'land',recipes:[{id:'land',materials:{stone:[0x56626d]}}]});
  const compiler = biomeWorld.create({height:()=>0,cell:.25,chunkCells:4,verticalCells:[-4,4],
    materialRamps:{marker:[0xe6856a]}});
  const indices = [[0,0],[3,0]], tiles = indices.map(([x,z])=>({id:String(x),resolution:[2,2],
    bounds:{min:[x,-1,z],max:[x+1,1,z+1]}}));
  const revisions = biomeRevisions.create({compiler,tiles,indices,
    brushGrid:{cell:.25,brickSize:4},agent:{radius:.08,height:.2}});
  const before = await revisions.commit({view:author.view()});
  const region = {min:[.25,0,.25],max:[.75,0,.75]};
  const painted = await revisions.sculpt({operation:'paint',bounds:region,material:'marker'});
  assert.deepEqual(painted.spans.work.rebuilt,[]);
  assert.deepEqual(painted.flood.work.topologyTiles,[]);
  assert.deepEqual(painted.graph.work.relinked,[]);
  assert.deepEqual(painted.dependencies.work.at(-1).detail.rebuilt,['0/0']);
  assert.deepEqual(painted.dependencies.work.at(-1).detail.reusedSurface,['0/0']);
  assert.equal(painted.chunks[1],before.chunks[1]);
  const cut = await revisions.sculpt({operation:'subtract',bounds:region,sdf:()=>-.18});
  assert(cut.spans.work.rebuilt.includes('0'));
  const erased = await revisions.commit({bricks:null});
  assert(erased.dependencies.changes.some(row=>row.field==='terrain/solid'));
  assert.deepEqual(erased.world.data,before.world.data);
});

test('the CLI emits a retained dependency report with real reused and rebuilt work', () => {
  const cwd = path.resolve(__dirname,'..');
  const result = spawnSync(process.execPath,['cli/ink-studio.js','sim','dependencies','examples/spatial-rebuild.js','--json'],
    {cwd,encoding:'utf8',timeout:30000});
  assert.equal(result.status,0,result.stderr);
  const report = JSON.parse(result.stdout);
  const work = Object.fromEntries(report.work.map(row=>[row.system,row.detail]));
  assert.equal(report.format,'ink-studio/spatial-dependencies');
  assert(work.spans.rebuilt.length>0 && work.spans.rebuilt.length<report.totals.spanTiles);
  assert(work.water.rebuilt.length>0);
  assert(work.routes.relinked.length>0);
  assert.equal(work.splats.rebuilt.length+work.splats.reused.length,report.totals.splatChunks);
  assert(report.work.every(row=>row.because.length));
});

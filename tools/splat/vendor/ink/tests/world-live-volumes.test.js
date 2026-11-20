const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const kit = require('..').load();
const {KIT:{world:W}} = kit;
const demo = require('../examples/world-live-volumes.json');
const pack = require('../examples/physical-materials.pack.json');
const left = [-3.1,1,0], right = [3.1,1,0], gate = [0,1,0], seam = [0,.40,0];
const value = (run,field,at,args) => run.query().probe('quarry/'+field,at,args).value;
const passage = run => run.query().trace('quarry/segment',left,{to:right,radius:.12}).value.status;
const flyRoute = run => run.query().trace('nav/route',left,{to:right,radius:.12,mode:'fly'}).value.status;
const serialized = data => JSON.parse(JSON.stringify(data));

test('a live cut exposes the interior, opens collision and wets an isolated basin', () => {
  const run=W.runtime.create(demo);
  assert.equal(passage(run),'blocked');
  assert.equal(flyRoute(run),'unreachable');
  assert.equal(value(run,'medium',right).kind,'air');
  assert.equal(value(run,'medium',left).kind,'water');
  assert(value(run,'clearance',gate)<0);
  run.advance(2);
  assert.equal(passage(run),'clear');
  assert.equal(flyRoute(run),'ok');
  assert(value(run,'clearance',gate)>.5);
  assert.equal(value(run,'material',seam),'copper-seam');
  assert.equal(value(run,'medium',right).kind,'water');
  const floor=value(run,'support',gate,{low:0,high:1})[0];
  assert.equal(floor.material,'copper-seam');
  assert(Math.abs(floor.y-.42)<.002);
  const stage=run.dependencies();
  assert(stage.changes.some(change=>change.field==='quarry/clearance'));
  assert(stage.changes.some(change=>change.field==='quarry/water'&&change.bounds.max[0]>3));
  assert.equal(run.query().probe('quarry/clearance',gate,{explain:true}).provenance.source.revision,1);
});

test('local chunk reuse matches a cold bake through a cut, a material layer and a fill', () => {
  const run=W.runtime.create(demo);
  let old=run.query().renderVolume('quarry');
  for(const tick of [2,4,6]){
    run.advance(tick);
    const query=run.query(), current=query.renderVolume('quarry'), changed=value(run,'work').lastEdit;
    assert.equal(changed.splatChunks.length+changed.reusedChunks,current.parts.length);
    assert(changed.splatChunks.length>0&&changed.reusedChunks>changed.splatChunks.length);
    assert.equal(current.parts.filter((part,i)=>part===old.parts[i]).length,changed.reusedChunks);
    const cold=W.runtime.create(demo,{checkpoint:serialized(run.checkpoint())});
    const warmImage=W.visual(kit,run.view(),query), coldImage=W.visual(kit,cold.view(),cold.query());
    assert.deepEqual(warmImage.data,coldImage.data);
    assert.deepEqual(warmImage.splatIds,coldImage.splatIds);
    assert.equal(new Set(warmImage.splatIds).size,warmImage.count);
    assert.deepEqual(warmImage.renderMetadata,coldImage.renderMetadata);
    if(tick===2){
      assert(W.query.fromScene(warmImage).select({material:'copper-seam'}).length);
    }else if(tick===4){
      assert.equal(current.water,old.water);
      assert.equal(changed.sampledChunks,0);
      assert.deepEqual(changed.spanTiles,[]);
      assert.deepEqual(changed.waterTiles,[]);
      assert.equal(value(run,'material',seam),'limestone');
    }else{
      assert.equal(passage(run),'blocked');
      assert.equal(flyRoute(run),'unreachable');
      assert.equal(value(run,'material',gate),'bulkhead');
      assert.equal(value(run,'medium',right).kind,'air');
      assert.equal(value(run,'medium',left).kind,'water');
    }
    old=current;
  }
  assert.deepEqual(W.runtime.replay(serialized(run.recording())).checkpoint(),run.checkpoint());
});

test('a failed edit batch leaves the previous volume and retained render unchanged', () => {
  const config={...demo.systems.quarry.config,maxEdits:1};
  const world={...demo,systems:{quarry:{kind:'volume',config}},commands:demo.commands.slice(0,2).map(row=>({...row,tick:1}))};
  const run=W.runtime.create(world), saved=run.checkpoint(), render=run.query().renderVolume('quarry');
  assert.throws(()=>run.step(),/Volume edit budget exceeded/);
  assert.deepEqual(run.checkpoint(),saved);
  assert.equal(run.query().renderVolume('quarry'),render);
  assert.equal(passage(run),'blocked');
  assert.equal(value(run,'medium',right).kind,'air');
});

test('sphere and capsule edits can bring a portable physical material into an empty volume', () => {
  const run=W.runtime.create({assetPacks:[pack],systems:{quarry:{kind:'volume',config:{
    bounds:{min:[-2,-2,-2],max:[2,2,2]},cell:.25,chunkCells:8,
    materials:{stone:[0x39414c,0x637585]},
    initial:[{op:'fill',shape:{kind:'sphere',at:[0,0,0],radius:1},material:'stone'}]
  }}}});
  run.schedule([
    {tick:1,action:'quarry/cut',args:{shape:{kind:'capsule',from:[-1.5,0,0],to:[1.5,0,0],radius:.45}}},
    {tick:2,action:'quarry/fill',args:{shape:{kind:'sphere',at:[0,0,0],radius:.30},material:'earthworks/clay'}}
  ]);
  assert.equal(value(run,'material',[0,0,0]),'stone');
  run.step();
  assert.equal(value(run,'medium',[0,0,0]).kind,'air');
  run.step();
  assert.equal(value(run,'material',[0,0,0]),'earthworks/clay');
  assert.equal(value(run,'material',[0,.7,0]),'stone');
  assert.throws(()=>run.schedule([{tick:3,action:'quarry/fill',args:{shape:{kind:'sphere',at:[0,0,0],radius:1},material:'missing'}}]),
    /Unknown physical material/);
  assert.throws(()=>run.schedule([{tick:3,action:'quarry/cut',args:{shape:{kind:'sphere',at:[10,0,0],radius:1}}}]),
    /intersect the editable bounds/);
});

test('the CLI traces a clear route through the edited volume', () => {
  const processResult=spawnSync(process.execPath,['cli/ink-studio.js','trace','examples/world-live-volumes.json',
    'quarry/segment','--at',left.join(','),'--args',JSON.stringify({to:right,radius:.12}),'--ticks','2','--json'],
    {cwd:path.join(__dirname,'..'),encoding:'utf8'});
  assert.equal(processResult.status,0,processResult.stderr);
  assert.equal(JSON.parse(processResult.stdout).value.status,'clear');
});

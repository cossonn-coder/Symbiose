const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const kit = require('..').load();
const {KIT:K}=kit, W=K.world, P=K.procedural;
const demo = require('../examples/world-surface-state.json');
const probe=(run,body,face,uv)=>run.query().probe('rig/surface-state',{},{body,face,uv}).value;
const packed=value=>JSON.parse(JSON.stringify(value));
const entire={kind:'rect',min:[0,0],max:[1,1]};

test('chart channels sample through known remesh correspondences and preserve their types',()=>{
  const schema=P.surfaceState.channels({moisture:{type:'number',default:.1,min:0,max:1,units:'1'}});
  const atlas=P.surfaceState.prepare([
    {channel:'paint',value:'#ffffff',brush:entire},
    {channel:'moisture',value:2,mode:'add',brush:entire},
    {channel:'heat',value:72,brush:{kind:'rect',min:[.25,.25],max:[.75,.75]}},
    {channel:'paint',mode:'clear',strength:.25,brush:{kind:'rect',min:[0,0],max:[.25,1]}}
  ],{size:[4,2],definitions:schema});
  const corners=[[0,0],[1,0],[0,1]].map(uv=>({chart:'face',uv}));
  const remeshed=P.surfaceState.correspondence(corners,[.2,.4,.4]);
  assert.deepEqual(remeshed,{chart:'face',uv:[.4,.4]});
  const squash=K.deform.squash([0,0,0],[1,0,0],2,false);
  const vertices=corners.map(corner=>squash([...corner.uv,0]));
  assert.equal(vertices[1][0],2);
  assert.equal(atlas.sample(remeshed.uv).heat,72);
  assert.equal(atlas.sample(remeshed.uv).moisture,1);
  assert.equal(atlas.sample([.1,.4]).paint.coverage,.75);
  assert.equal(P.surfaceState.correspondence([corners[0],corners[1],{...corners[2],chart:'other'}],[.2,.4,.4]),null);
  assert.throws(()=>P.surfaceState.correspondence(corners,[.4,.4,.4]),/barycentric/);
});

test('heat, paint, grime, scars and wear stay at their rest coordinates through reshaping and fracture',()=>{
  const run=W.runtime.create(demo);
  run.advance(1);
  const samples=[[.22,.5],[.3,.12],[.65,.67],[.81,.27]];
  const original=samples.map(uv=>probe(run,'sign','+z',uv));
  assert.equal(original[0].values.heat,60);
  assert.equal(original[0].values.paint.coverage,1);
  assert.equal(original[1].values.grime,.26);
  assert(original[2].values.scar>.3);
  assert.equal(original[3].values.wear,.38);
  run.advance(2);
  assert.equal(run.query().probe('rig/bodies').value.sign.half[0],2.38);
  assert.deepEqual(samples.map(uv=>probe(run,'sign','+z',uv)),original);
  const fork=run.fork();
  run.advance(11);
  fork.advance(11);
  assert.deepEqual(fork.checkpoint(),run.checkpoint());
  const bodies=run.query().probe('rig/bodies').value;
  for(const [i,[u,v]] of samples.entries()){
    const part=u<.5?0:1, body=bodies['sign.'+part], uv=[u*2-part,v];
    const after=probe(run,body.id,'+z',uv);
    assert.equal(after.chart,'sign/+z');
    assert.deepEqual(after.rest,[u,v]);
    assert.deepEqual(after.values,original[i].values);
    const point=K.V.add(body.position,K.M.app(body.rotation,[(uv[0]-.5)*body.half[0]*2,(v-.5)*body.half[1]*2,body.half[2]]));
    const world=run.query().probe('rig/surface-state',point,{body:body.id}).value;
    assert.equal(world.face,'+z');
    assert(Math.abs(world.rest[0]-u)<1e-9&&Math.abs(world.rest[1]-v)<1e-9);
    assert.deepEqual(world.values,after.values);
  }
  const edges=[probe(run,'sign.0','+x',[.5,.5]),probe(run,'sign.1','-x',[.5,.5])];
  assert.notEqual(edges[0].chart,edges[1].chart);
  for(const edge of edges){
    assert.equal(edge.fresh,true);
    assert.deepEqual(edge.values,{paint:null,heat:20,grime:0,scar:0,wear:0});
  }
  const replay=W.runtime.replay(packed(run.recording()));
  assert.deepEqual(replay.checkpoint(),run.checkpoint());
});

test('post-fracture stamps stay on a single piece, including its edge, and survive a later split',()=>{
  const run=W.runtime.create(demo);
  run.advance(4);
  const left=probe(run,'sign.0','+z',[1,.5]), right=probe(run,'sign.1','+z',[0,.5]);
  assert.deepEqual(left.rest,right.rest);
  run.schedule([
    {tick:5,action:'rig/surface-stamp',args:{body:'sign.1',face:'+z',stamp:{channel:'paint',value:'#ff0000',brush:entire}}},
    {tick:5,action:'rig/surface-stamp',args:{body:'sign.1',face:'+z',stamp:{channel:'heat',value:85,brush:entire}}},
    {tick:6,action:'rig/fracture',args:{body:'sign.1',axis:1,parts:2}}
  ]);
  run.advance(5);
  assert.deepEqual(probe(run,'sign.0','+z',[1,.5]),left);
  assert.deepEqual(probe(run,'sign.1','+z',[0,.5]).values.paint,{color:[1,0,0],coverage:1});
  assert.equal(probe(run,'sign.1','+z',[0,.5]).values.heat,85);
  run.advance(6);
  assert.deepEqual(probe(run,'sign.1.1','+z',[.6,.5]).values.paint,{color:[1,0,0],coverage:1});
  assert.equal(probe(run,'sign.1.1','+z',[.6,.5]).chart,'sign/+z');
  assert.equal(probe(run,'sign.1.1','+z',[.6,.5]).values.heat,85);
  assert.equal(probe(run,'sign.1.1','-y',[.6,.5]).values.paint,null);
  assert.throws(()=>run.schedule([{tick:7,action:'rig/surface-stamp',args:{body:'sign.0',face:'+z',
    stamp:{channel:'wear',value:5,brush:entire}}}]),/scalar surface stamp/);
});

test('both render resolutions retain the original front chart and label the newly exposed wood',()=>{
  const run=W.runtime.create(demo);
  run.advance(11);
  const view=run.view();
  for(const resolution of [.068,.11]){
    const world=W.visual(kit,{...view,world:{...view.world,visual:{...view.world.visual,resolution}}},run.query());
    const query=W.query.fromScene(world);
    for(const entity of ['sign.0','sign.1']) assert(query.select({entity,surface:'sign/+z',material:'stained-wood'}).length);
    const exposed=query.select({material:'fresh-wood'});
    assert(exposed.some(row=>row.surface==='sign.0/+x'));
    assert(exposed.some(row=>row.surface==='sign.1/-x'));
  }
});

test('the CLI reports the initialized states of fresh surfaces',()=>{
  const result=spawnSync(process.execPath,['cli/ink-studio.js','probe','examples/world-surface-state.json','--field','rig/surface-state',
    '--ticks','11','--args',JSON.stringify({body:'sign.0',face:'+x',uv:[.5,.5]}),'--json'],
    {cwd:path.join(__dirname,'..'),encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);
  const sample=JSON.parse(result.stdout).value;
  assert.equal(sample.fresh,true);
  assert.equal(sample.values.paint,null);
});

test('mechanics leaves the physical material surface alias available',()=>{
  const yard=require('../examples/world-physical-materials.json');
  const rig={...yard.systems.rig,config:{...yard.systems.rig.config,surface:'surface'}};
  const run=W.runtime.create({...yard,systems:{...yard.systems,rig},
    assetPacks:[require('../examples/physical-materials.pack.json')]});
  assert.equal(run.query().probe('surface',[-1.15,0,-2]).value.id,'earthworks/clay');
});

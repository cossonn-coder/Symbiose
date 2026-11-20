const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { KIT } = require('..').load();
const { world: W } = KIT;
const manifest = require('../examples/world-spatial-fields.json');
const bounds = {min:[0,0,0],max:[2,2,2]};
const fields = definitions => ({weather:{kind:'fields',config:{fields:definitions}}});

test('typed grids export values, native axes, units and interpolation weights', () => {
  const q = W.runtime.create({systems:fields({
    heat:{type:'number',units:'degC',bounds,grid:{counts:[2,2,2],values:[0,2,4,6,8,10,12,14]}},
    cover:{type:'category',axes:'xy',categories:['soil','canopy'],bounds:{min:[0,0],max:[2,2]},
      grid:{counts:[2,1],values:['soil','canopy']}}
  })}).query();
  const heat = q.probe('heat',[1,1,1],{explain:true});
  assert.equal(heat.value,7);
  assert.equal(heat.provenance.field,'weather/heat');
  assert.equal(heat.provenance.units,'degC');
  assert.equal(heat.provenance.source.nodes.length,8);
  assert(heat.provenance.source.nodes.every(node => node.weight===.125));
  assert.equal(q.probe('heat',[2,2,2]).value,14);
  assert.equal(q.probe('heat',[3,1,1],{explain:true}).status,'outside');
  assert.equal(q.probe('cover',[1,1,100]).value,'canopy');
  assert.equal(q.probe('cover',[0,1,-100]).value,'soil');
  const exported = q.export('cover',{points:[[0,1,0],[1,1,0],[3,1,0]]});
  assert.equal(exported.type,'category');
  assert.deepEqual(exported.spatial.categories,['soil','canopy']);
  assert.equal(exported.spatial.sampling,'nearest');
  assert.deepEqual(exported.samples.map(row=>row.status),['ok','ok','outside']);
  assert.throws(()=>q.probe('heat',[1,,1]),/Spatial field needs a finite XYZ point/);
});

test('attached fields follow a moving and rotating socket and report world-space vectors', () => {
  const turn = KIT.M.rot([0,1,0],Math.PI/2);
  const host = () => ({
    initial:()=>({offset:0}),
    step:state=>({offset:state.offset+1}),
    pose:(state,id)=>id==='mast'?{position:[5+state.offset,0,3],rotation:turn}:null
  });
  const run = W.runtime.create({
    entities:{mast:{sockets:{tip:[1,0,0]}}},
    systems:{...fields({draft:{type:'vec3',units:'world/s',space:{entity:'mast',socket:'tip'},
      bounds:{min:[0,0,-1],max:[2,2,1]},default:[1,0,0]}}),mover:{kind:'mover'}}
  },{implementations:{mover:host}});
  const old = run.query(), read = old.probe('draft',[5,1,1],{explain:true});
  assert(Math.abs(read.value[0])<1e-12);
  assert.deepEqual(read.value.slice(1),[0,-1]);
  assert.equal(read.provenance.source.kind,'default');
  assert.deepEqual(read.provenance.frame.point,[5,0,2]);
  assert.deepEqual(read.provenance.point.slice(0,2),[1,1]);
  run.advance(3);
  assert.equal(run.query().probe('draft',[5,1,1]).status,'outside');
  assert.equal(run.query().probe('draft',[8,1,1]).status,'ok');
  assert.equal(old.probe('draft',[5,1,1]).status,'ok');
});

test('a reusable sampler enforces a consumer contract and supports bounded custom providers', () => {
  const defined = W.spatialFields.define({type:'vec2',components:'xy',units:'m/s',axes:'xy',
    bounds:{min:[0,0],max:[1,1]}},({point,explain})=>({
    status:'ok',value:point,...(explain && {source:{kind:'formula',name:'gradient'}})
  }));
  const q = W.runtime.create({systems:{model:{kind:'model'}}},
    {implementations:{model:()=>({initial:()=>({}),fields:{current:defined}})}}).query();
  assert.deepEqual(q.probe('current',[.25,.5,10],{explain:true}).provenance.source,{kind:'formula',name:'gradient'});
  const sample = q.sampler('current',{type:'vec2',units:'m/s',fallback:[0,0]});
  assert.deepEqual(sample(.25,.5,10),[.25,.5]);
  assert.deepEqual(sample(2,.5,10),[0,0]);
  assert.throws(()=>q.sampler('current',{type:'vec3'}),/Unexpected spatial field type/);
  assert.throws(()=>q.sampler('current',{units:'km/h'}),/Unexpected spatial field units/);
  assert.throws(()=>q.sampler('current',{fallback:[1]}),/Invalid spatial field fallback/);
  assert.throws(()=>q.sampler('world/history'),/Unknown or non-spatial field/);
});

test('typed field definitions and scheduled region updates reject incompatible data', () => {
  const degree = {type:'number',units:'degC',default:3};
  assert.throws(()=>W.runtime.validate({systems:fields({
    bad:{type:'category',categories:['open','roof'],sampling:'linear',bounds,
      grid:{counts:[1,1,1],values:['roof']}}
  })}),/Invalid sampling/);
  assert.throws(()=>W.runtime.validate({systems:fields({
    bad:{...degree,grid:{counts:[2,1,1],values:[1]},bounds}
  })}),/A grid needs bounds/);
  assert.throws(()=>W.runtime.validate({systems:fields({
    bad:{type:'vec3',bounds,grid:{counts:[2,1,1],values:[[0,0,0],3]}}
  })}),/Invalid spatial field grid values/);
  const run = W.runtime.create({systems:fields({degree})});
  assert.throws(()=>run.schedule([{tick:1,action:'weather/set',args:{field:'degree',region:{bounds,value:[0,0,0]}}}]),
    /Invalid spatial field region value/);
});

test('wind overlays drive a sail, survive checkpoints, and are discoverable through the CLI', () => {
  const run = W.runtime.create(manifest);
  const wind = run.query().probe('wind',[-4,1,-3],{explain:true});
  assert.equal(wind.provenance.source.id,'lee');
  const before = run.query();
  run.advance(59);
  const at59 = run.query().probe('position',{entity:'raft'}).value;
  assert(at59[0]>-1);
  run.advance(60);
  const shifted = run.query().probe('wind',[-4,1,-3],{explain:true});
  assert.equal(shifted.provenance.source.id,'wind-shift');
  assert.equal(shifted.provenance.tick,60);
  assert.equal(shifted.value[0],-4.5);
  assert.deepEqual(before.probe('wind',[-4,1,-3]).value,[.25,0,0]);
  run.advance(119);
  assert(run.query().probe('position',{entity:'raft'}).value[0]<at59[0]);
  assert.deepEqual(W.runtime.replay(JSON.parse(JSON.stringify(run.recording()))).checkpoint(),run.checkpoint());
  assert.throws(()=>W.runtime.validate({...manifest,systems:{...manifest.systems,
    weather:fields({wind:{type:'vec3',units:'km/h'}}).weather}}),/Unexpected spatial field units/);

  const repo = path.join(__dirname,'..');
  const cli = (...args) => {
    const result = spawnSync(process.execPath,['cli/ink-studio.js',...args,'--json'],{cwd:repo,encoding:'utf8'});
    assert.equal(result.status,0,result.stderr);
    return JSON.parse(result.stdout);
  };
  const file = 'examples/world-spatial-fields.json';
  const exported = cli('field',file,'weather/wind','--spec','examples/spatial-wind-transect.json','--explain');
  assert.equal(exported.samples.length,5);
  assert.equal(exported.samples[2].provenance.source.kind,'grid');
  assert.equal(cli('probe',file,'--field','weather/cover','--entity','station','--socket','vane','--explain')
    .provenance.source.id,'station-roof');
});

test('water scalar and vector channels use the same typed contract and keep dry values distinct from outside', () => {
  const q = W.runtime.create({systems:{water:{kind:'water',config:{width:2,height:1}}}}).query();
  const flow = q.probe('water/flow',[1.5,10,.5],{explain:true});
  assert.deepEqual(flow.value,[0,0]);
  assert.deepEqual(flow.provenance.source,{kind:'cell',cell:[1,0]});
  assert.equal(flow.provenance.components,'xz');
  assert.equal(q.probe('water/water',[1.5,10,.5]).status,'dry');
  assert.equal(q.probe('water/depth',[2,10,.5]).status,'outside');
});

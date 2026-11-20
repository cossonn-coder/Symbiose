const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const kit = require('..').load();
const {KIT:{world:W,authoring:A}} = kit;
const pack = require('../examples/physical-materials.pack.json');
const yard = require('../examples/world-physical-materials.json');
const world = {...yard,assetPacks:[pack]};
const clay = 'earthworks/clay', gravel = 'earthworks/gravel';
const point = [-1.15,0,-2];

test('physical materials round-trip in versioned packs and resolve wet coefficients by asset ID', () => {
  const bundle=JSON.parse(JSON.stringify(A.assetPacks.bundle([pack],['earthworks'])));
  const installed=A.assetPacks.merge([],bundle).packs;
  const catalog=A.assetPacks.create({packs:installed});
  assert.equal(catalog.getMaterial(clay).revision,1);
  assert.equal(catalog.getMaterial(gravel).material.friction,.95);
  assert.equal(catalog.getMaterial('earthworks/unknown'),null);
  assert.throws(()=>A.assetPacks.manifest({...pack,materials:[...pack.materials,pack.materials[0]]}),/Duplicate physical material/);
  assert.throws(()=>A.assetPacks.manifest({...pack,materials:[{...pack.materials[0],friction:{dry:.5}}]}),/friction/);
  assert.throws(()=>A.assetPacks.manifest({...pack,materials:[{...pack.materials[0],thermal:{heatCapacity:0,conductance:1}}]}),/heatCapacity/);
  const run=W.runtime.create(world);
  const material=run.query().probe('world/material',{},{id:clay,wetness:.5});
  assert.equal(material.value.thermal.heatCapacity,1050);
  assert.equal(material.value.fracture.energy,5.5);
  assert(Math.abs(material.value.friction-.46)<1e-12);
  assert.equal(run.query().probe('world/material',{},{id:clay,wetness:1}).value.friction,.10);
  assert.deepEqual(run.query().inspect().physicalMaterials.map(item=>item.id),[clay,gravel]);
  assert.throws(()=>W.runtime.validate({...world,entities:{missing:{materialAsset:'earthworks/unavailable'}}}),/Unknown physical material/);
  assert.throws(()=>W.runtime.validate({...world,visual:{fields:{surface:'soil/moisture'}}}),/physical surface field/);
});

test('a single surface binding drives drying, heat response, traction, water losses and erosion', () => {
  const run=W.runtime.create(world);
  const before=run.query().probe('soil/surface',point,{explain:true});
  const beforeY=run.query().probe('runoff/bed',[-3.75,0,1.25]).value;
  assert.equal(before.value.wetness,1);
  assert.equal(before.value.temperature,12);
  assert.deepEqual(before.source,{kind:'material-cell',cell:[5,2],asset:clay,pack:'earthworks',revision:1});
  assert.equal(run.query().probe('soil/material',[0,0,2.75]).value,gravel);
  assert.equal(run.query().probe('soil/wetness',[4,0,0]).status,'outside');
  run.advance(22);
  const query=run.query();
  const current=query.probe('soil/surface',point).value;
  assert(current.wetness<.7&&current.friction>before.value.friction);
  assert(current.temperature>12&&current.temperature<35);
  assert.equal(query.probe('soil/temperature',point,{explain:true}).provenance.units,'degC');
  const {value:bodies}=query.probe('rig/bodies');
  assert(bodies['dry-cart'].position[2]-bodies['wet-cart'].position[2]>.7);
  const contacts=query.probe('rig/contacts').value;
  assert.equal(contacts.length,2);
  assert(contacts.every(contact=>contact.material===clay&&contact.cue==='earthworks/clay.roll'));
  const water=query.probe('runoff/mass').value;
  assert(water.drained>.1);
  assert(Math.abs(water.error)<1e-10);
  assert(query.probe('runoff/eroded').value>.1);
  assert(query.probe('runoff/bed',[-3.75,0,1.25]).value<beforeY);
});

test('fracture uses the resolved threshold and preserves material, cue and state through replay', () => {
  const run=W.runtime.create(world);
  run.advance(6);
  const fork=run.fork();
  run.advance(22);
  fork.advance(22);
  assert.deepEqual(run.checkpoint(),fork.checkpoint());
  assert.deepEqual(W.runtime.replay(JSON.parse(JSON.stringify(run.recording()))).checkpoint(),run.checkpoint());
  const query=run.query(), {value:bodies}=query.probe('rig/bodies'), [resisted,fractured]=run.history;
  assert.equal(resisted.kind,'fracture-resisted');
  assert.equal(resisted.threshold,8);
  assert.equal(fractured.threshold,3);
  assert.equal(fractured.cue,'earthworks/clay.crack');
  assert.equal(fractured.fragments.length,3);
  assert(bodies['wet-block']);
  assert(!bodies['dry-block']);
  assert(fractured.fragments.every(id=>bodies[id].materialAsset===clay));
  assert.equal(query.probe('world/material',{entity:fractured.fragments[0]}).value.id,clay);
});

test('foot contacts and hard landings identify their material sound cue', () => {
  const run=W.runtime.create({...world,entities:{},commands:[],systems:{
    soil:yard.systems.soil,
    runoff:yard.systems.runoff,
    rig:{kind:'mechanics',config:{surface:'soil/surface',
      bodies:{crate:{half:[.2,.2,.2],position:[1,.7,0],velocity:[0,-1,0]}}}},
    walk:{kind:'agents',config:{
      bounds:{min:[-3,-1,-2],max:[3,2,2]},support:'rig/support',
      species:{person:{mode:'walk',speed:2,stride:.08}},
      agents:{walker:{species:'person',position:[-2,0,-1],goal:[-2,0,1]}}
    }}
  }});
  run.advance(12);
  const steps=run.query().probe('walk/contacts').value;
  assert.equal(steps[0]?.cue,'earthworks/clay.step');
  assert.equal(steps[0]?.material,clay);
  const impact=run.history.find(row=>row.kind==='material-sound');
  assert.equal(impact?.cue,'earthworks/clay.impact');
  assert.equal(impact?.interaction,'impact');
});

test('rendered splats retain the material IDs sampled at the ground and fragment surfaces', () => {
  const run=W.runtime.create(world);
  run.advance(8);
  const rendered=W.visual(kit,run.view(),run.query());
  const query=W.query.fromScene(rendered);
  const clayTargets=query.select({material:clay});
  const gravelTargets=query.select({material:gravel});
  assert(clayTargets.some(target=>target.surface==='terrain'));
  assert(clayTargets.some(target=>target.entity==='dry-block.0'));
  assert(gravelTargets.some(target=>target.surface==='terrain'));
});

test('the CLI installs the same material pack for world validation and point probes', () => {
  const cwd=path.join(__dirname,'..'), document='examples/world-physical-materials.json';
  function cli(...args) {
    const proc=spawnSync(process.execPath,['cli/ink-studio.js',...args,
      '--asset-pack','examples/physical-materials.pack.json','--json'],{cwd,encoding:'utf8'});
    assert.equal(proc.status,0,proc.stderr);
    return JSON.parse(proc.stdout);
  }
  assert.equal(cli('validate',document).valid,true);
  const result=cli('probe',document,'--field','soil/surface','--at','-1.15,0,-2','--ticks','22');
  assert.equal(result.value.id,clay);
  assert.equal(result.value.revision,1);
});

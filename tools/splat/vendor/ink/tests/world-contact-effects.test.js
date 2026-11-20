const test=require('node:test');
const assert=require('node:assert/strict');
const ink=require('..');
const kit=ink.load(), {world:W}=kit.KIT;
const source=require('../examples/world-contact-effects.json');
const read=(run,name,at,args)=>run.query().probe(name,at,args).value;

test('existing boolean contact streams keep their original records',()=>{
  const {ground,drive,tracks}=source.systems;
  const run=W.runtime.create({assetPacks:source.assetPacks,systems:{ground,tracks,
    drive:{...drive,config:{...drive.config,contactEvents:true}}}});
  run.advance(3);
  const [row]=read(run,'drive/contacts');
  assert.deepEqual(Object.keys(row).sort(),['cue','entity','material','point','support','weight','wheel']);
});

test('one wheel contact drives a loaded rut, spray, sound and shake from its original surface reading',()=>{
  const run=W.runtime.create(source);
  run.advance(22);
  const wet=read(run,'feedback/contacts',{entity:'wet-cart'});
  const dry=read(run,'feedback/contacts',{entity:'dry-cart'});
  assert.equal(wet.length,2);
  assert.equal(dry.length,2);
  for(const row of wet){
    assert.equal(row.tick,21);
    assert.equal(row.appliedTick,22);
    assert.equal(row.load,9.81);
    assert(row.speed>2);
    assert.equal(row.surface.wetness,1);
    assert.equal(row.surface.revision,1);
    assert(row.reaction.rut>dry[0].reaction.rut*10);
    assert(row.reaction.spray>0 && row.reaction.shake>0);
    assert.equal(row.reaction.sound,'trackside/clay.roll');
  }
  assert(dry.every(row=>row.surface.wetness===0&&row.reaction.spray===undefined));
  const frame=read(run,'feedback/frame');
  assert(frame.particles.some(row=>row.contact===wet[0].id));
  assert(frame.particles.every(row=>row.entity==='wet-cart'));
  assert(frame.kick.some(Boolean));
  assert(Math.hypot(...frame.kick)<=.1200000001);
  assert(run.events.some(row=>row.kind==='material-sound'&&row.contact===wet[0].id&&row.gain>.7));
  const dep=run.dependencies().pending;
  assert(dep.some(row=>row.field==='tracks/ruttedBed'));
  const bed=read(run,'tracks/ruttedBed',[-1.08,0,-1.55]);
  assert(bed<-.01);
  assert(read(run,'tracks/ruttedBed',[.62,0,-1.55])>bed);
});

test('live, replayed and forked contact frames and terrain are identical at a saved tick',()=>{
  const run=W.runtime.create(source);
  run.advance(10);
  const fork=run.fork(), saved=JSON.parse(JSON.stringify(run.checkpoint()));
  const restored=W.runtime.create(saved.world,{checkpoint:saved});
  for(const branch of [run,fork,restored])branch.advance(22);
  const replay=W.runtime.replay(JSON.parse(JSON.stringify(run.recording())));
  for(const branch of [fork,restored,replay]){
    assert.deepEqual(branch.checkpoint(),run.checkpoint());
    assert.deepEqual(read(branch,'feedback/frame'),read(run,'feedback/frame'));
  }
  const view=run.view();
  const baked=W.visual(kit,{...view,world:{...view.world,visual:{...view.world.visual,resolution:.12}}},run.query());
  const targets=W.query.fromScene(baked).select({material:'contact-spray'});
  assert(targets.some(row=>row.entity==='wet-cart'));
  const frame=read(run,'feedback/frame',baked.cam.target);
  assert.deepEqual(baked.anim.kick,frame.kick);
  assert(Math.hypot(...baked.anim.kick)<Math.hypot(...read(run,'feedback/frame').kick));
});

test('substepped wheel contacts keep distinct IDs and a slower consumer receives each once',()=>{
  const run=W.runtime.create({...source,systems:{...source.systems,
    drive:{...source.systems.drive,schedule:{substeps:2}},
    feedback:{...source.systems.feedback,schedule:{every:3},config:{soundEvents:false}}
  }});
  run.advance(6);
  const first=read(run,'feedback/contacts');
  assert(first.some(row=>row.id.split('.')[2]==='1'));
  assert(first.some(row=>row.id.split('.')[2]==='2'));
  assert.equal(first.length,new Set(first.map(row=>row.id)).size);
  run.advance(9);
  const second=read(run,'feedback/contacts');
  assert(second.length>0);
  assert(!second.some(row=>first.some(prior=>prior.id===row.id)));
  assert.equal(run.history.filter(row=>row.kind==='material-sound').length,0);
});

test('scripted contacts respect budgets and emit bounded, time-decaying feedback',()=>{
  const row={id:'manual.1',interaction:'impact',point:[0,0,0],normal:[0,1,0],speed:3,load:16,cue:'audio/thud'};
  const command=(tick,value)=>({tick,action:'world/input',args:{port:'fx/contacts',value}});
  const run=W.runtime.create({dt:.05,systems:{fx:{kind:'contact-effects',config:{
    maxContacts:3,maxParticles:2,maxBursts:1,maxShakes:1,channels:['additional'],
    fallback:{rut:.5,spray:{count:9,life:.2},sound:{interval:.2},shake:{strength:.2,life:.2}}
  }}},commands:[command(1,[row,row,{...row,id:'rest',speed:0},{...row,id:'dropped'}]),
    command(2,[{...row,id:'new'}])]});
  run.advance(1);
  assert.equal(read(run,'fx/dropped'),1);
  assert.equal(read(run,'fx/contacts').length,2);
  assert.deepEqual(read(run,'fx/contacts')[1].reaction,{});
  assert.equal(read(run,'fx/frame').particles.length,2);
  assert.equal(run.events.length,1);
  run.advance(2);
  assert.equal(run.events.length,0);
  assert(read(run,'fx/frame').particles.every(row=>row.contact==='new'));
  assert.deepEqual(read(run,'fx/frame',[100,0,0]).kick,[0,0,0]);
  run.advance(8);
  assert.deepEqual(read(run,'fx/frame'),{particles:[],kick:[0,0,0]});
});

test('footsteps can share the contact stream and leave strength proportional to authored load',()=>{
  const run=W.runtime.create({...source,visual:{},systems:{
    ground:source.systems.ground,
    walk:{kind:'agents',config:{bounds:{min:[-2,-1,-3],max:[2,2,3]},surface:'ground/surface',contactEvents:'material',
      species:{walker:{mode:'walk',stride:.07,speed:2,contactLoad:17}},
      agents:{foot:{species:'walker',position:[-1,0,-2],goal:[-1,0,2]}}}},
    feedback:source.systems.feedback
  },connections:[{from:'walk/contacts',to:'feedback/contacts'}]});
  run.advance(14);
  const feet=run.history.filter(row=>row.interaction==='step');
  assert(feet.length>2);
  const [row]=read(run,'feedback/contacts');
  assert.equal(row.interaction,'step');
  assert.equal(row.surface.wetness,1);
  assert.equal(row.load,17);
  assert.equal(row.cue,'trackside/clay.step');
  assert(feet.every(event=>event.cue==='trackside/clay.step'&&event.contact.startsWith('walk.')));
});

test('validation catches invalid material recipes, unresolved visual bindings and malformed input',()=>{
  const base=source.assetPacks[0], material=base.materials[0];
  assert.throws(()=>W.runtime.validate({...source,assetPacks:[{...base,materials:[{...material,
    contactEffects:{spray:{count:{dry:0}}}}]}]}),/contact effects spray/);
  assert.throws(()=>W.runtime.validate({...source,visual:{fields:{contactEffects:'tracks/wear'}}}),/contact-effects frame/);
  const run=W.runtime.create({systems:{fx:{kind:'contact-effects'}},
    commands:[{tick:1,action:'world/input',args:{port:'fx/contacts',value:[{point:[0,0,0],speed:-2}]}}]});
  assert.throws(()=>run.step(),/Invalid material contact/);
  assert.equal(run.view().tick,0);
});

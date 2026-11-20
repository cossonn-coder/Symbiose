const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const ink = require('..');
const kit = ink.load(), { KIT:K, makeBuilder } = kit, A = K.authoring;
const asset = 'shore/watch', texture = 'art/headland';
const cam = { target:[0,.35,0],dist:7,pitch:.05,yaw:0 };
const view = { w:40,h:25,px:1,raw:true };
const start = { horizon:'#7bb1b9',zenith:'#486780',ground:'#21495e',sunStrength:0,rain:0,windX:.2,fogDensity:0 };
const dusk = { horizon:'#d38a73',zenith:'#503b61',ground:'#283246',sunStrength:0,rain:.16,windX:.5,fogDensity:.8 };
const skyEnvironment = { profiles:{ dawn:start,dusk,squall:{rain:1,windX:1.5,fogDensity:2} },
  sequences:{ crossing:{duration:4,keys:[{at:0,profile:'dawn'},{at:2,profile:'dusk'}]} },
  tracks:[{id:'clock',sequence:'crossing'}] };
const settings = { skyEnvironment, weatherBinding:{ fogVolumes:['haze'],fronts:[{
  id:'squall',profile:'squall',radius:5,route:[{at:0,xz:[-9,0]},{at:2,xz:[0,0]}]
}] }, atmosphere:[{id:'haze',type:'fog',color:'#b5c0bb',density:.09,near:2,far:15,bottom:-2,top:.08}],
  cloudField:{recipe:'coastal-stratus',resolution:[6,6],bounds:{min:[-30,-32],max:[30,-6]}},
  liveSun:false, skyReflections:'scene',
  look:{horizonBands:{camera:{yaw:[0,360],pitch:[-90,90]},bands:[{id:'coast',radius:70,height:[-19,4],
    image:{asset:texture,revision:1}}]},artDirection:{atmosphereBands:5}}
};
const pack = (id, payload) => ({format:'ink-studio/asset-pack',version:1,id,revision:1,title:id,...payload});
const shore = pack('shore',{environments:[{id:asset,label:'Shore',settings}]});
const art = pack('art',{environmentImages:[{id:texture,width:2,height:1,pixels:[72,106,128,255,104,138,154,255]}]});
const installed = [shore,art];

test('environment packs round-trip bundles with image dependencies and the existing revision rules', () => {
  const bundle = A.assetPacks.bundle([art,shore,pack('unused',{environmentImages:[{...art.environmentImages[0],id:'unused/ridge'}]})],['shore']);
  assert.deepEqual(bundle.packs.map(entry=>entry.id),['art','shore']);
  assert.deepEqual(A.assetPacks.merge([],JSON.stringify(bundle)).added,['art','shore']);
  const catalog = A.assetPacks.create({packs:JSON.parse(JSON.stringify(bundle)).packs});
  assert.equal(catalog.getEnvironment(asset).revision,1);
  assert.equal(catalog.getEnvironmentImage(texture).revision,1);
  assert.equal(A.environments.bind(asset,catalog).settings.look.horizonBands.bands[0].image.pixels[0],72);
  assert.throws(()=>A.assetPacks.bundle([shore],['shore']),/Unknown environment image/);
  assert.throws(()=>A.assetPacks.create({packs:[shore]}),/Unknown environment image/);
  assert.throws(()=>A.assetPacks.create({packs:[shore,{...art,revision:2}]}),/requires pack revision 1, installed 2/);
  assert.throws(()=>A.assetPacks.bundle([shore,{...art,revision:2}],['shore']),/requires pack revision 1/);
  assert.throws(()=>A.assetPacks.merge([shore],{...shore,environments:[{...shore.environments[0],label:'conflict'}]}),/Conflicting/);
  const same = A.assetPacks.reviseEnvironment(shore,asset,{label:'Shore'});
  assert.equal(same.revision,1);
  const bump = A.assetPacks.reviseEnvironment(shore,asset,{label:'Salt shallows'});
  assert.equal(bump.revision,2);
  assert.deepEqual(A.assetPacks.merge([shore],bump).updated,['shore']);
  assert.deepEqual(A.assetPacks.merge([bump],shore).keptNewer,['shore']);
  const newer = A.assetPacks.create({packs:[bump,art]});
  assert.equal(A.environments.bind(asset,newer).revision,2);
  assert.throws(()=>A.environments.bind({asset,revision:1},newer),/requires pack revision 1, installed 2/);
});

test('portable overrides merge maps, replace lists and remain local through rendering', () => {
  const catalog = A.assetPacks.create({packs:installed});
  const patch = { asset,revision:1,overrides:{skyEnvironment:{profiles:{dusk:{horizon:'#ab5169'}}},
    atmosphere:[],weatherBinding:{fronts:[]},cloudField:false,look:{artDirection:{atmosphereBands:3}}} };
  const initial = A.environments.bind(asset,catalog), changed = A.environments.bind(patch,catalog);
  assert.equal(initial.settings.skyEnvironment.profiles.dusk.horizon,dusk.horizon);
  assert.equal(changed.settings.skyEnvironment.profiles.dusk.horizon,'#ab5169');
  assert.deepEqual(changed.settings.skyEnvironment.tracks,skyEnvironment.tracks);
  assert.deepEqual(changed.settings.atmosphere,[]);
  assert.equal(changed.settings.weatherBinding.fronts.length,0);
  assert.equal(changed.settings.look.artDirection.atmosphereBands,3);
  assert(Object.isFrozen(initial.settings.skyEnvironment.profiles));
  assert.equal(K.weather.bind(initial.settings.skyEnvironment,initial.settings.weatherBinding).sample(2,0,0).rain,1);
  const world=makeBuilder(1,[0]).finish({cam,detail:24,environmentPreset:patch,assetPacks:installed,skyReflections:'material'});
  const reference=makeBuilder(1,[0]).finish({ cam,detail:24,...changed.settings,skyReflections:'material' });
  assert.deepEqual(world.environmentSource,{id:asset,pack:'shore',revision:1,images:[{id:texture,pack:'art',revision:1}]});
  assert.deepEqual(ink.render(world,{...view,t:2}).rgb,ink.render(reference,{...view,t:2}).rgb);
  assert.notDeepEqual(ink.render(world,{...view,t:2}).rgb,ink.render(world,{...view,t:2,horizonBands:false}).rgb);
  assert.throws(()=>A.environments.bind({asset,overrides:{skyEnvironment:{tracks:[{id:'x',sequence:'missing'}]}}},catalog),/missing sequence/i);
  assert.throws(()=>A.assetPacks.create({packs:[pack('bad',{environments:[{id:'outside/watch',label:'x',settings}]}),art]}),/namespaced/);
});

test('both diorama and simulation rebuild from pinned portable data', () => {
  const scene = {id:'coast',name:'Coast',camera:cam,assetPacks:installed,environmentPreset:{asset,revision:1},
    finish:{cloudField:false},solids:[{kind:'box',at:[0,0,0],half:[.3,.3,.3],mat:'stone'}]};
  assert(!K.diorama.check(scene).some(row=>row.level==='error'));
  const diorama = K.diorama.build(scene);
  assert.equal(diorama.cloudField,false);
  assert.equal(diorama.environmentSource.revision,1);
  const empty = { id:'coast-sim',assetPacks:installed,visual:{camera:cam,environmentPreset:{asset,revision:1},
    look:{horizonBands:false},cloudShadows:false} };
  const run = K.world.runtime.create(empty);
  const rendered = K.world.visual(kit,run.view(),run.query());
  assert.equal(rendered.look.horizonBands,false);
  assert.equal(rendered.skyReflections,'scene');
  assert.deepEqual(rendered.environmentSource.images,[]);
  assert.equal(rendered.environmentSource.pack,'shore');
  const checkpoint = JSON.parse(JSON.stringify(run.checkpoint()));
  const resumed = K.world.runtime.create(checkpoint.world,{checkpoint});
  const after = K.world.visual(kit,resumed.view(),resumed.query());
  assert.deepEqual(after.environmentSource,rendered.environmentSource);
  assert.deepEqual(ink.render(after,{...view,t:1}).rgb,ink.render(rendered,{...view,t:1}).rgb);
  assert.throws(()=>K.world.runtime.create({...empty,assetPacks:[{...shore,revision:2},art]}),/requires pack revision 1/);
});

test('CLI installs the same environment bundle for distinct scenes', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(),'ink-environment-'));
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const bundle = path.join(dir,'coast.json'), png = path.join(dir,'ridge.png');
  require('../cli/png.js').write(png,2,1,Uint8Array.of(72,106,128,104,138,154));
  assert.deepEqual(ink.readEnvironmentImage(texture,png),art.environmentImages[0]);
  fs.writeFileSync(bundle,JSON.stringify(A.assetPacks.bundle(installed,['shore'])));
  const cli = path.join(__dirname,'../cli/ink-studio.js');
  const draw = (id, horizon) => {
    const scene = path.join(dir,id+'.json'), out = path.join(dir,id+'.png');
    fs.writeFileSync(scene,JSON.stringify({id,name:id,camera:cam,
      environmentPreset:{asset,revision:1,overrides:{look:{horizonBands:horizon}}},
      solids:[{kind:'ball',at:[0,0,0],r:.36,mat:'stone'}]}));
    execFileSync(process.execPath,[cli,'render',scene,'--asset-pack',bundle,'--raw','--px','1','--w','40','--h','25','--out',out],{cwd:dir});
    return fs.readFileSync(out);
  };
  assert.notDeepEqual(draw('draw-a',{camera:{fade:{pitch:5}}}),draw('draw-b',false));
});

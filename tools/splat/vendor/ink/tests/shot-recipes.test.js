const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync, spawnSync } = require('node:child_process');
const { KIT } = require('..').load();

const repo = path.join(__dirname,'..'), cli = path.join(repo,'cli/ink-studio.js');
const run = (cwd,...args) => execFileSync(process.execPath,[cli,...args],{cwd,encoding:'utf8'});
const read = file => JSON.parse(fs.readFileSync(file,'utf8'));
function folders(t) {
  const base = fs.mkdtempSync(path.join(os.tmpdir(),'ink-shot-test-'));
  t.after(()=>fs.rmSync(base,{recursive:true,force:true}));
  const project = path.join(base,'project'), files = name => path.join(base,name);
  fs.mkdirSync(project);
  return {base,project,files};
}

const profiles = {
  profiles:{ dry:{zenith:'#3b4f72',horizon:'#9a7255',ground:'#364744',rain:0,humidity:.45},
    rain:{zenith:'#395365',horizon:'#92a3ad',ground:'#263a44',rain:.42,humidity:.78} },
  sequences:{ stand:{duration:4,loop:false,keys:[{at:0,profile:'dry'}]} },
  tracks:[{id:'weather',sequence:'stand'}]
};
const source = `({makeBuilder}) => ({
  id:'shore', name:'Shore', seed:37,
  build(seed) {
    const B = makeBuilder(seed,[0x102030,0x93aba3]);
    return B.finish({
      cam:{target:[0,0,0],dist:5,pitch:.15,yaw:0}, radius:3, detail:12,
      weatherBinding:{surface:{width:4,height:3,cell:1,step:.125,standingWater:true}}
    });
  }
})`;

test('a shot recipe captures a moving clip and restores weather across project locations',t=>{
  const {base,project,files}=folders(t);
  const scene = path.join(project,'shore.js'), environment = path.join(project,'sky.json');
  fs.writeFileSync(scene,'module.exports = '+source);
  fs.writeFileSync(environment,JSON.stringify(profiles));
  const original=files('original.png'), recipeFile=files('shot.json'), replay=files('replay.png');
  run(project,'clip',scene,'--sky-environment',environment,'--sky-profile','weather=rain',
    '--from','2','--to','2.75','--fps','4','--camera-orbit','35','--camera-pan','0.3,0,0',
    '--w','48','--h','30','--px','2','--out',original,'--recipe',recipeFile);
  const recipe=read(recipeFile);
  assert.equal(recipe.format,'ink-studio/shot-recipe');
  assert.equal(recipe.scene,'shore.js');
  assert.equal(recipe.options['sky-environment'],'sky.json');
  assert.equal(recipe.seed,37);
  assert.deepEqual(recipe.profileOverrides,{weather:'rain'});
  assert.deepEqual(recipe.frames.map(frame=>frame.time),[2,2.25,2.5]);
  assert.deepEqual(recipe.frames.map(frame=>frame.skyTime),[2,2.25,2.5]);
  assert.deepEqual(recipe.frames[0].art,{width:24,height:15,pixelSize:2});
  assert.deepEqual(recipe.frames.at(-1).camera.target,[.3,0,0]);
  assert(recipe.frames.at(-1).camera.yaw > recipe.frames[0].camera.yaw);
  assert.equal(recipe.weather.tick,16);
  assert(recipe.weather.state.fields.wetness.some(wet=>wet>.2));
  run(base,'shot','replay',recipeFile,'--out',replay);
  assert.deepEqual(fs.readFileSync(replay),fs.readFileSync(original));

  const moved=files('moved');
  fs.renameSync(project,moved);
  run(base,'shot','replay',recipeFile,'--root',moved,'--out',replay);
  assert.deepEqual(fs.readFileSync(replay),fs.readFileSync(original));

  const nudge=structuredClone(recipe);
  nudge.options['sky-profile']='weather=dry';
  const changedRecipe=files('changed.json');
  fs.writeFileSync(changedRecipe,JSON.stringify(nudge));
  const diverged=spawnSync(process.execPath,[cli,'shot','replay',changedRecipe,'--root',moved,'--out',replay],
    {cwd:base,encoding:'utf8'});
  assert.notEqual(diverged.status,0);
  assert.match(diverged.stderr,/diverged from the saved image hash/);
  assert.deepEqual(fs.readFileSync(replay),fs.readFileSync(original));

  fs.appendFileSync(path.join(moved,'sky.json'),'\n');
  const changed=spawnSync(process.execPath,[cli,'shot','replay',recipeFile,'--root',moved,'--out',replay],
    {cwd:base,encoding:'utf8'});
  assert.notEqual(changed.status,0);
  assert.match(changed.stderr,/missing or changed: sky\.json/);
  assert.deepEqual(fs.readFileSync(replay),fs.readFileSync(original));
});

test('a still recipe verifies diagnostic passes and updates their manifest for the replay name',t=>{
  const {base,project,files}=folders(t);
  fs.writeFileSync(path.join(project,'shore.js'),'module.exports = '+source);
  // Disable weather so this also exercises recipes without a surface checkpoint.
  run(project,'render','shore.js','--weather-binding','off','--passes','coverage',
    '--w','32','--h','24','--out',files('still.png'),'--recipe',files('shot.json'));
  assert.equal(read(files('shot.json')).weather,undefined);
  run(base,'shot','replay',files('shot.json'),'--out',files('replayed.png'));
  for (const ext of ['.png','-coverage.png'])
    assert.deepEqual(fs.readFileSync(files('replayed'+ext)),fs.readFileSync(files('still'+ext)));
  assert.equal(read(files('replayed-passes.json')).files.coverage,'replayed-coverage.png');
});

test('a transition review preserves the matched cameras and metrics sidecar',t=>{
  const {base,project,files}=folders(t);
  fs.writeFileSync(path.join(project,'shore.js'),'module.exports = '+source);
  fs.writeFileSync(path.join(project,'sky.json'),JSON.stringify(profiles));
  fs.writeFileSync(path.join(project,'plan.json'),JSON.stringify({
    fps:8,neighbors:2,preroll:1,events:[{id:'Cut',kind:'cut',at:2,incomingCamera:{yaw:.3}}]
  }));
  run(project,'transition-review','shore.js','--sky-environment','sky.json','--sky-profile','weather=rain',
    '--plan','plan.json','--w','32','--h','24','--out',files('review.png'),'--recipe',files('shot.json'));
  const original=read(files('shot.json'));
  assert.equal(original.frames[0].art.pixelSize,1);
  assert(new Set(original.frames.map(frame=>frame.camera.yaw)).size>1);
  assert(original.output.sidecars['.json']);
  run(base,'shot','replay',files('shot.json'),'--out',files('replayed.png'));
  for (const ext of ['png','json'])
    assert.deepEqual(fs.readFileSync(files('replayed.'+ext)),fs.readFileSync(files('review.'+ext)));
});

test('a simulation recipe embeds checkpoint history and replays scheduled weather cues',t=>{
  const {base,files}=folders(t);
  fs.writeFileSync(files('commands.json'),JSON.stringify([{tick:4,action:'world/event',args:{kind:'cue',cue:'warning-bell'}}]));
  run(repo,'sim','render','examples/world-conditional-weather.json','--asset-pack','examples/coastal-environment-pack.json',
    '--actions',files('commands.json'),'--ticks','20','--w','60','--h','40','--passes','environment',
    '--out',files('sim.png'),'--recipe',files('sim-shot.json'));
  const shot=read(files('sim-shot.json'));
  assert.equal(shot.runtime.origin.tick,0);
  assert.equal(shot.runtime.end.tick,20);
  assert.equal(shot.runtime.commands[0].tick,4);
  assert(shot.runtime.end.weatherTrackState.firings.some(event=>event.id==='warning-bell' && event.at===1));
  run(base,'shot','replay',files('sim-shot.json'),'--out',files('replayed.png'));
  for (const suffix of ['.png','-sky.png','-precipitation.png','-fogTransmittance.png','-reflections.png','-foregroundCoverage.png'])
    assert.deepEqual(fs.readFileSync(files('replayed'+suffix)),fs.readFileSync(files('sim'+suffix)));
});

test('surface weather can resume from a portable checkpoint and reject incompatible grids',()=>{
  const config = {width:4,height:3,cell:.5,standingWater:true};
  const create = options => KIT.procedural.motion.surfaceWeather(options);
  const original = create(config), resumed = create(config);
  original.step(3,{forcing:()=>({rain:.65,air:6,light:.4})});
  const checkpoint = JSON.parse(JSON.stringify(original.checkpoint()));
  assert.throws(()=>create({...config,cell:.6}).restore(checkpoint),/checkpoint for this grid/);
  assert.throws(()=>create({...config,mask:x=>x<1}).restore(checkpoint),/checkpoint for this grid/);
  resumed.restore(checkpoint);
  assert.deepEqual(resumed.checkpoint(),checkpoint);
  const forcing = (x,z,time) => ({air:-5+x+z,light:.3,snowfall:time/20});
  original.step(2,{forcing});
  resumed.step(2,{forcing});
  assert.deepEqual(resumed.checkpoint(),original.checkpoint());
});

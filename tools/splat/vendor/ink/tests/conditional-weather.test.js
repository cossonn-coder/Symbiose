const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const { execFileSync } = require('node:child_process');
const ink = require('..');
const kit = ink.load(), { KIT:K, makeBuilder } = kit, W = K.world;
const color = (horizon,rain,fogDensity) => ({horizon,zenith:horizon,ground:horizon,sunStrength:0,rain,fogDensity});
const skyEnvironment = {defaults:color('#946243',0,.28),profiles:{
  dawn:color('#d89a58',0,.10), squall:color('#44719a',.9,1.5), mist:{fogDensity:2.2}, easing:{rain:.04}
}, transitions:[{at:0,profile:'dawn',duration:4,ease:'linear'}]};
const timeOf = at => ({at,profile:'squall',duration:1,ease:'linear'});
const cueRule = {id:'storm',trigger:{cue:'storm-bell'},transition:{profile:'squall',duration:1,ease:'linear'}};
const cam = {target:[0,.5,0],dist:6,pitch:.08,yaw:0};
const fog = {id:'mist',type:'fog',bottom:-1,top:3,density:.2,far:9,color:'#87b5b9'};
const view = {w:48,h:32,px:1,raw:true,captureFog:true};
const patch = (tick,value) => ({tick,action:'world/patch',args:{edits:[{op:'set',path:'/entities/courier/position',value:[value,0,0]}]}});
const pressure = (tick,value) => ({tick,action:'station/set',args:{
  field:'pressure',region:{bounds:{min:[-1,-1,-1],max:[1,1,1]},value}
}});

test('scene markers fire at exact authored times on a seek, including native timeline cues', () => {
  const rules = [cueRule];
  const B = makeBuilder(3,[0x080d12]);
  const world = B.finish({cam,detail:18,skyEnvironment,weatherTracks:{rules,cues:[[2.345,'storm-bell']]},
    weatherBinding:true,atmosphere:[fog]});
  const after = ink.render(world,{...view,t:3.2});
  const manual = ink.render(world,{...view,t:3.2,weatherTracks:false,skyTransitions:[...skyEnvironment.transitions,timeOf(2.345)]});
  assert.deepEqual(after.rgb,manual.rgb);
  assert.deepEqual(after.fog,manual.fog);
  const at = ink.render(world,{...view,t:2.345});
  const off = ink.render(world,{...view,t:2.345,weatherTracks:false});
  assert.deepEqual(at.rgb,off.rgb);
  assert.deepEqual(at.fog,off.fog);
  assert.notDeepEqual(after.rgb,ink.render(world,{...view,t:3.2,weatherTracks:false}).rgb);

  world.weatherTracks = {rules};
  world.animationTimeline = {cues:()=>[{id:'storm-bell',time:2.345},{id:'storm-bell',time:1.6,enabled:false}]};
  assert.deepEqual(ink.render(world,{...view,t:3.2}).rgb,after.rgb);
  assert.deepEqual(ink.render(world,{...view,t:1.8}).rgb,ink.render(world,{...view,t:1.8,weatherTracks:false}).rgb);
  assert.notDeepEqual(ink.render(world,{...view,t:3.2,skyTransitions:false}).rgb,after.rgb);
});

test('cue, entry and condition firings use settled simulation ticks and survive replay', () => {
  const config = {rules:[
    cueRule,
    {id:'inside',trigger:{enter:{entity:'courier',socket:'eye',bounds:{min:[2,-1,-1],max:[3,2,1]}}},
      transition:{profile:'mist',duration:.8},repeat:true},
    {id:'pressure',trigger:{condition:{field:'station/pressure',at:[0,0,0],when:{op:'lt',value:1}}},
      transition:{profile:'easing',duration:.5},repeat:true},
    {id:'armed',trigger:{condition:{when:{path:['tick'],op:'eq',value:0}}},transition:{profile:'easing',duration:.1}}
  ]};
  const manifest = {id:'shore',dt:.25,history:{enabled:false},
    entities:{courier:{position:[0,0,0],sockets:{eye:[.25,.5,0]}}},
    systems:{station:{kind:'fields',config:{fields:{pressure:{default:2}}}}},
    visual:{camera:cam,skyEnvironment,weatherTracks:config,weatherBinding:true,atmosphere:[fog]}};
  const run = W.runtime.create(manifest);
  assert.deepEqual(run.view().weatherTrackState.firings,[{id:'armed',at:0}]);
  const cue = {kind:'cue',cue:'storm-bell'};
  run.schedule([{tick:1,action:'world/event',args:cue},{tick:5,action:'world/event',args:cue},
    patch(2,1.8), pressure(3,.8), patch(4,.5), patch(5,2), pressure(6,2), pressure(7,.9)]);
  run.advance(3);
  assert.deepEqual(run.view().weatherTrackState.firings,[{id:'armed',at:0},{id:'storm',at:.25},{id:'inside',at:.5},{id:'pressure',at:.75}]);
  const disk = JSON.parse(JSON.stringify(run.checkpoint()));
  const resumed = W.runtime.create(disk.world,{checkpoint:disk});
  const fork = run.fork();
  for (const branch of [run,resumed,fork]) branch.advance(9);
  const firings = [...disk.weatherTrackState.firings,{id:'inside',at:1.25},{id:'pressure',at:1.75}];
  assert.deepEqual(run.view().weatherTrackState.firings,firings);
  assert.deepEqual(run.query().probe('world/weather-tracks').value.firings,firings);
  assert.deepEqual(run.history,[]);
  assert.deepEqual(run.checkpoint(),resumed.checkpoint());
  assert.deepEqual(run.checkpoint(),fork.checkpoint());
  assert.deepEqual(run.checkpoint(),W.runtime.replay(JSON.parse(JSON.stringify(run.recording()))).checkpoint());
  const visual = W.visual(kit,run.view(),run.query());
  const image = ink.render(visual,view);
  assert.notDeepEqual(image.rgb,ink.render(visual,{...view,weatherTracks:false}).rgb);
});

test('initial membership is baselined, repeat means re-entry, and disabled or unmatched cues stay silent', () => {
  const rules = [
    {id:'inside',trigger:{enter:{entity:'runner',bounds:{min:[0,0,0],max:[1,1,1]}}},
      transition:{profile:'mist',duration:.6},repeat:true},
    {...cueRule,repeat:true,trigger:{cue:'storm-bell',where:{path:['take'],value:'A'}}}
  ];
  const p = K.weather.tracks.compile(skyEnvironment,{rules,cues:[[2,'other']]});
  const query = x=>({frame:()=>({point:[x,0,0]})});
  let state = p.step(undefined,{time:0,query:query(.5)});
  state = p.step(state,{time:.25,query:query(.5),cues:[{id:'storm-bell',take:'A',enabled:false}]});
  assert.deepEqual(state.firings,[]);
  state = p.step(state,{time:.5,query:query(2),cues:[{id:'storm-bell',take:'B'}]});
  state = p.step(state,{time:.75,query:query(1),cues:[{id:'storm-bell',take:'A'},{id:'storm-bell',take:'A'}]});
  assert.deepEqual(state.firings,[{id:'inside',at:.75},{id:'storm',at:.75}]);
  assert.throws(()=>p.step(state,{time:.2}),/nondecreasing/);
  assert.throws(()=>p.validate({...state,firings:[{id:'unknown',at:.75}]},.75),/Invalid saved/);
  assert.equal(K.weather.tracks.compile(false,{rules}),null);
  assert.throws(()=>K.weather.tracks.compile(undefined,{rules}),/needs a sky environment/);
  assert.throws(()=>K.weather.tracks.compile(skyEnvironment,{rules:[{
    ...cueRule,transition:{profile:'absent',duration:1}
  }]}),/Unknown/);
  assert.throws(()=>K.weather.tracks.compile(skyEnvironment,{rules:[{
    ...cueRule,trigger:{cue:'bell',condition:{}}
  }]}),/exactly one/);
});

test('conditional weather is optional in the CLI and fixed shots still export', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(),'ink-weather-tracks-'));
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const pack = {format:'ink-studio/asset-pack',version:1,id:'shore',title:'Shore',revision:1,
    environments:[{id:'shore/coast',label:'Coast',settings:{skyEnvironment,weatherTracks:{rules:[cueRule],cues:[[.5,'storm-bell']]}}}]};
  const scene = {id:'deck',name:'Deck',camera:cam,environmentPreset:{asset:'shore/coast',revision:1},
    solids:[{kind:'box',at:[0,0,0],half:[.3,.3,.3],mat:'stone'}]};
  const file = x=>path.join(dir,x);
  fs.writeFileSync(file('coast.json'),JSON.stringify(pack));
  fs.writeFileSync(file('deck.json'),JSON.stringify(scene));
  fs.writeFileSync(file('shot.json'),JSON.stringify([timeOf(.5)]));
  const cli = path.join(__dirname,'../cli/ink-studio.js');
  function draw(name, flags = []) {
    execFileSync(process.execPath,[cli,'render',file('deck.json'),'--asset-pack',file('coast.json'),
      '--t','2','--w','36','--h','24','--px','1','--raw','--out',file(name),...flags],{cwd:dir});
    return fs.readFileSync(file(name));
  }
  const conditional = draw('conditional.png');
  const off = draw('off.png',['--weather-tracks','off']);
  const authored = draw('authored.png',['--weather-tracks','off','--sky-transitions',file('shot.json')]);
  assert.notDeepEqual(conditional,off);
  assert.deepEqual(conditional,authored);
});

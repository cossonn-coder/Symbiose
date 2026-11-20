const assert = require('node:assert/strict');
const { execFileSync, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const ink = require('..');
const { KIT:K, makeBuilder } = ink.load();
const packed = {tone:'#9e684d',rain:.12,windX:.4};
const skyEnvironment = {
  defaults:{rain:0, fogDensity:.3, windZ:0},
  profiles:{
    warm:packed, cool:{tone:'#405182',rain:.42,windX:1.1}, drizzle:{rain:.18}, dry:{rain:0},
    storm:{tone:'#202946',rain:1}, clearing:{rain:.2}
  },
  sequences:{
    light:{duration:4,keys:[{at:0,profile:'warm',ease:'linear'},{at:2,profile:'cool'}]},
    wash:{duration:4,keys:[{at:0,profile:'drizzle',ease:'hold'},{at:2,profile:'dry'}]}
  },
  tracks:[{id:'sky',sequence:'light'},{id:'weather',sequence:'wash',speed:2,offset:.5}],
  transitions:[{at:1,profile:'storm',duration:2,ease:'linear'},{at:1.75,profile:'clearing',duration:1}]
};

test('reports exact sky key brackets, precedence, pins, and what an interruption captured', () => {
  const sky=K.skyEnvironment.compile(skyEnvironment);
  const report=sky.inspect(2.1);
  assert.deepEqual(report.values,sky.sample(2.1));
  assert.deepEqual(report.tracks[0].keys,[{at:2,profile:'cool'},{at:4,profile:'warm'}]);
  assert.equal(report.tracks[1].trackTime,3.7);
  assert.deepEqual(report.source.rain,{kind:'transition',index:1});
  const [storm,clear]=report.transitions;
  assert.equal(storm.state,'blending');
  assert.equal(storm.channels.rain,undefined);
  assert.equal(storm.channels.tone.fromSource.id,'sky');
  assert.deepEqual(storm.channels.tone.fromSource.keys,[{at:0,profile:'warm'},{at:2,profile:'cool'}]);
  assert.equal(storm.channels.tone.fromSource.weight,.5);
  assert.deepEqual(clear.channels.rain.fromSource,{kind:'transition',index:0});
  assert.equal(clear.channels.rain.from,sky.withTransitions(skyEnvironment.transitions.slice(0,1)).sample(1.75).rain);
  const pinned=sky.inspect(.75,{weather:'dry'});
  assert.equal(pinned.tracks[1].pinnedProfile,'dry');
  assert.deepEqual(pinned.source.rain,{kind:'track',id:'weather'});
  assert.equal(pinned.values.rain,0);
  assert.equal(pinned.transitions.length,0);
  assert.deepEqual(sky.withTransitions([{at:0,profile:'clearing',duration:1},{at:1,profile:'clearing',duration:1}])
    .inspect(2).transitions.map(row=>row.state),['superseded','holding']);
});

test('front route weights explain local values in authored order alongside exposure, cutouts and wind', () => {
  const at=[3,.75,0], t=1.5;
  const sky={...skyEnvironment,profiles:{...skyEnvironment.profiles, first:{rain:.8,windX:2,fogDensity:2},
    second:{rain:.3,windX:-.4,fogDensity:.85}},transitions:[]};
  const weatherBinding={rainFull:.9,fogVolumes:['sea-mist'],surface:{width:8,height:8,cell:1,origin:[-4,-4]},fronts:[
    {id:'sea',profile:'first',radius:6,feather:.8,route:[{at:0,xz:[-1,0]},{at:3,xz:[1,0]}]},
    {id:'headland',profile:'second',radius:8,feather:.85,route:[{at:0,xz:[-.5,0]},{at:3,xz:[2.5,0]}]}
  ]};
  const sceneExposure={zones:[
    {id:'arch',min:[1,0,-2],max:[6,3,2],fade:1,wind:.45,fog:.3},
    {id:'lintel',min:[2,0,-1],max:[4,2,1],fade:0,wind:.25,rain:.4}
  ]};
  const volumeCutouts={zones:[{id:'path',type:'sphere',at:[3,.75,0],radius:1,retain:.15,affects:'fog'}]};
  const cloudField={bounds:{min:[-8,-8],max:[8,8]},resolution:[3,3],coverage:Array(9).fill(.8),height:3};
  const celestialTracks={primarySun:'sun',bodies:[{id:'sun',kind:'sun',keys:[
    {at:0,azimuth:0,elevation:.4,ease:'linear'},{at:3,azimuth:.2,elevation:.5}
  ]}]};
  const world=makeBuilder(1,[0x233641]).finish({skyEnvironment:sky,weatherBinding,sceneExposure,volumeCutouts,
    windField:{gust:{amplitude:.2,period:3}},cloudField,cloudShadows:{direction:[0,1,0]},celestialTracks,
    atmosphere:[K.atmosphere.fog({id:'sea-mist'}),K.atmosphere.fog({id:'steam'})]});
  const report=ink.inspectEnvironment(world,{at,t});
  const binding=K.weather.bind(sky,weatherBinding);
  assert.deepEqual(report.weather.local,binding.sample(t,at[0],at[2]));
  const [a,b]=report.weather.fronts;
  assert.equal(a.profile,'first');
  assert.equal(a.route.progress,.5);
  assert.deepEqual(a.route.keys,[{at:0,xz:[-1,0]},{at:3,xz:[1,0]}]);
  assert(a.weight>0 && a.weight<1 && b.weight>0 && b.weight<=1);
  assert.equal(a.channels.rain.from,report.weather.global.rain);
  assert.equal(b.channels.rain.from,a.channels.rain.value);
  assert.equal(b.channels.rain.value,report.weather.local.rain);
  assert(report.weather.surface.wetness>0);
  assert.deepEqual(report.exposure.zones.map(zone=>zone.id),['arch','lintel']);
  assert.equal(report.exposure.gains.wind,.25);
  assert.equal(report.wind.exposureGain,.25);
  assert.equal(report.wind.velocity[0],report.weather.local.windX*.25);
  assert.equal(report.cutouts.fog,.15);
  assert.equal(report.cutouts.cloud,1);
  assert.equal(report.cutouts.zones[0].id,'path');
  assert.equal(report.atmosphere.volumes[0].weatherDensityScale,report.weather.local.fogDensity);
  assert.equal(report.atmosphere.volumes[1].weatherDensityScale,1);
  assert(report.lighting.cloud.shadowVisibility<1);
  assert.equal(report.lighting.celestial.tracks[0].weight,.5);
  assert.deepEqual(report.lighting.celestial.tracks[0].keys.map(key=>key.at),[0,3]);

  const isolated=ink.inspectEnvironment(world,{at,t,weatherFronts:false,sceneExposure:false,volumeCutouts:false});
  assert.deepEqual(isolated.weather.local,report.weather.global);
  assert.deepEqual(isolated.weather.fronts,[]);
  assert.equal(isolated.exposure,null);
  assert.equal(isolated.cutouts,null);
  assert.equal(isolated.wind.exposureGain,1);
});

test('CLI inspects scene and recorded simulation time, with the same pack, cues, and render choices', t => {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'ink-env-inspect-'));
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const root=path.join(__dirname,'..'), cli=path.join(root,'cli/ink-studio.js');
  const scene=path.join(root,'examples/world-conditional-weather.json'), pack=path.join(root,'examples/coastal-environment-pack.json');
  const record=path.join(dir,'station.json'), report=path.join(dir,'report.json');
  const cliArgs = (...args)=>[cli,...args];
  const run = (...args)=>execFileSync(process.execPath,cliArgs(...args),{cwd:dir,encoding:'utf8'});
  run('sim','run',scene,'--asset-pack',pack,'--ticks','22','--record',record);
  const options=['--at','2.55,.6,2.38','--t','3.6'];
  const original=JSON.parse(run('environment','inspect',scene,...options,'--asset-pack',pack));
  run('environment','inspect',record,...options,'--out',report);
  assert.deepEqual(JSON.parse(fs.readFileSync(report)),original);
  assert.equal(original.preset.revision,1);
  assert.equal(original.time.scene,3.5);
  assert.equal(original.time.requested,3.6);
  assert.equal(original.tick,14);
  assert.deepEqual(original.conditional,[{id:'warning-bell',at:1.1},{id:'path-entry',at:3}]);
  assert.equal(original.sky.transitions.find(row=>row.origin.id==='path-entry').origin.trigger.enter.entity,'courier');
  const fixed=JSON.parse(run('environment','inspect',scene,...options,'--asset-pack',pack,'--weather-tracks','off',
    '--sky-time','5','--sky-profile','light=dusk','--json'));
  assert.equal(fixed.sky.tracks[0].pinnedProfile,'dusk');
  assert.equal(fixed.time.sky,5);
  assert.equal(fixed.sky.transitions.length,0);
  const invalid=spawnSync(process.execPath,cliArgs('environment','inspect',scene,'--at','1,,2'),{cwd:dir,encoding:'utf8'});
  assert.equal(invalid.status,1);
  assert.match(invalid.stderr,/finite comma-separated/);
});

const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { execFileSync } = require('node:child_process');
const ink = require('..');
const PNG = require('../cli/png.js');
const { ArtPasses, KIT: K } = ink.load();
const size = 41, middle = 20 * size + 20;
const view = { w:size, h:size, px:1, ortho:true };
const rgba = (data,p) => [...data.subarray(p*4,p*4+4)];
const rgb = (data,p) => [...data.subarray(p*3,p*3+3)];

const fixture = ({ KIT:K, makeBuilder }) => ({
  id:'rain', name:'Rain', seed:16,
  build(seed) {
    const B = makeBuilder(seed,[0x182334,0xb64321,0x70a8f2]);
    const flake = { k:2, ph:.5, sp:1, rg:2, nd:true, em:true };
    B.disc(0,1,-1,[0,0,1],.55,.04,B.P[2],.55,flake);
    B.disc(0,0,1,[0,0,1],.23,.04,B.P[1],3);
    return B.finish({
      cam:{target:[0,0,0],dist:5,yaw:0,pitch:0}, radius:4, detail:14, dither:0,
      skyEnvironment:{ defaults:{zenith:'#607fa9',horizon:'#607fa9',ground:'#607fa9',sunStrength:0} },
      atmosphere:[K.atmosphere.box({min:[-2,-2,-3],max:[2,2,3],density:.18,color:'#abb8c9'})],
    });
  }
});

test('environment passes share the art grid and leave RGB unchanged',()=>{
  const world = fixture(ink.load()).build(16);
  for (const settings of [view,{...view,raw:true,splatOrder:'surface'},
    {...view,colored:true,stable:{resolve:'clusters'}}]) {
    const original = ink.render(world,settings);
    const frame = ink.render(world,{...settings,passes:['environment','coverage'],captureFog:true});
    const {passes} = frame;
    assert.deepEqual(frame.rgb,original.rgb);
    assert.deepEqual(Object.keys(passes),['w','h',...ArtPasses.environment,'coverage']);
    assert.deepEqual(rgb(passes.sky,middle),rgb(passes.sky,0));
    assert.deepEqual(rgb(passes.sky,0).map(v=>Math.round(v*255)),[96,127,169]);
    assert(passes.foregroundCoverage[middle]>.99);
    assert.equal(passes.foregroundCoverage[0],0);
    assert(passes.precipitation[middle*4+3]<.008);
    const rain = passes.precipitation.findIndex((v,i)=>i%4===3 && v>.1)>>2;
    assert(rain>=0 && passes.coverage[rain] > passes.foregroundCoverage[rain]);
    assert(rgba(passes.precipitation,rain)[2]>.05);
    const through = passes.fogTransmittance[middle];
    assert(through>.55 && through<.85);
    assert(Math.abs(through+frame.fog[middle]-1)<1e-6);
    assert(passes.fogTransmittance.every(v=>v>=0 && v<=1));
    assert(!passes.reflections.some(Boolean));
  }
  const disabled = ink.render(world,{...view,atmosphere:false,transparent:true,passes:['sky','fogTransmittance']});
  assert.equal(disabled.alpha[0],0);
  assert(rgb(disabled.passes.sky,0).every(v=>v>0));
  assert(disabled.passes.fogTransmittance.every(v=>v===1));
  assert.equal(ink.render(world,{...view,passes:true}).passes.sky,undefined);
});

test('fog transmission excludes water extinction and includes depth-based aerial perspective',()=>{
  const world = fixture(ink.load()).build(16);
  const {waterBodies} = K.procedural;
  const pool = waterBodies.create({id:'pool',bounds:{min:[-2,1.5],max:[2,3.5]},
    sample:()=>({bed:-1,surface:1})});
  world.water = waterBodies.scene([pool]);
  const settings = {...view,raw:true,passes:['fogTransmittance'],captureFog:true};
  const dry = ink.render(world,{...settings,water:false}), wet = ink.render(world,settings);
  assert(wet.passes.fogTransmittance[middle] > dry.passes.fogTransmittance[middle]);
  const waterOnly = ink.render({...world,atmosphere:[]},settings);
  assert(waterOnly.passes.fogTransmittance.every(v=>v===1));
  assert(waterOnly.fog[middle]>0);
  assert(wet.fog[middle] > dry.fog[middle]);
  const aerial = ink.render(world,{...settings,water:false,aerialPerspective:{start:0,density:.5}});
  assert(aerial.passes.fogTransmittance[middle]<dry.passes.fogTransmittance[middle]);
});

test('authored legacy snow is visible in the precipitation pass and leaves stay in the foreground',()=>{
  const make = kind => {
    const B=ink.load().makeBuilder(5,[0x131f3e,0xffffff]);
    K.weather.fall(B,{kind,n:20,box:[-.45,.45,-.4,.4],size:.1,top:.5,cols:[1]});
    return ink.render(B.finish({cam:{target:[0,.25,0],dist:4,pitch:0,yaw:0}}),
      {...view,passes:['precipitation','foregroundCoverage']}).passes;
  };
  const snow = make('snow'), leaves = make('leaf');
  assert(snow.precipitation.some((v,i)=>i%4===3 && v>.05));
  assert(!snow.foregroundCoverage.some(Boolean));
  assert(!leaves.precipitation.some(Boolean));
  assert(leaves.foregroundCoverage.some(Boolean));
});

test('the CLI writes aligned native PNGs and replays RGBA precipitation clips',t=>{
  const dir = fs.mkdtempSync(path.join(os.tmpdir(),'ink-environment-passes-'));
  t.after(()=>fs.rmSync(dir,{recursive:true,force:true}));
  const cli = path.join(__dirname,'../cli/ink-studio.js');
  const file = name => path.join(dir,name);
  const run = (...args) => execFileSync(process.execPath,[cli,...args],{cwd:dir,encoding:'utf8'});
  const fixed = ['--raw','--ortho','--w','41','--h','41','--px','1'];
  fs.writeFileSync(file('rain.js'),'module.exports = '+fixture.toString());
  run('passes','rain.js',...fixed,'--channels','environment','--out','stills');
  const manifest = JSON.parse(fs.readFileSync(file('stills/passes.json'),'utf8'));
  assert.deepEqual(Object.keys(manifest.files),['color',...ArtPasses.environment]);
  assert.match(manifest.encodings.fogTransmittance,/white is full transmission/);
  const image = PNG.raster(file('stills/precipitation.png'));
  assert.deepEqual([image.w,image.h],[41,41]);
  assert(image.data[middle*4+3]<=2);
  assert.deepEqual(rgba(image.data,0),[0,0,0,0]);
  assert(image.data.some((v,i)=>i%4===3 && v>0 && v<255));
  run('clip','rain.js',...fixed,'--passes','environment','--from','0','--to','.75','--fps','4',
    '--recipe','take.json','--out','take.png');
  const animated = fs.readFileSync(file('take-precipitation.png'));
  assert(animated.includes('acTL'));
  assert.equal(animated[25],6);
  assert.deepEqual(PNG.raster(animated).data,image.data);
  run('shot','replay','take.json','--out','replayed.png');
  for (const channel of ArtPasses.environment)
    assert.deepEqual(fs.readFileSync(file('replayed-'+channel+'.png')),fs.readFileSync(file('take-'+channel+'.png')));
  const replay = JSON.parse(fs.readFileSync(file('replayed-passes.json'),'utf8'));
  assert.equal(replay.files.precipitation,'replayed-precipitation.png');
});

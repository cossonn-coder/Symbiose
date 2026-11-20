const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const test = require('node:test');
const ink = require('..');
const { KIT:K, makeBuilder } = ink.load();
const fill = color => ({ zenith:color,horizon:color,ground:color,sunStrength:0 });
const start = { ...fill('#7eabd0'), sunAzimuth:6.2, daylight:.88, rain:.03, fogDensity:.28, windX:.2 };
const dusk = { ...fill('#f49673'), sunAzimuth:6.05, daylight:.33, rain:.12, fogDensity:.49, windX:.5 };
const storm = { ...fill('#2f4568'), sunAzimuth:.2, daylight:.12, rain:.9, fogDensity:2.1 };
const base = {
  defaults:{ windZ:0, humidity:.42 },
  profiles:{ start,dusk,storm, clearing:{rain:0,fogDensity:.3}, gust:{windZ:1.2}, invalid:{z:'#8899aa'}, wrong:{humidity:'#618849'} },
  sequences:{ sunset:{duration:10,loop:false,keys:[{at:0,profile:'start',ease:'linear'},{at:8,profile:'dusk'}]} },
  tracks:[{id:'light',sequence:'sunset'}]
};
const sky = K.skyEnvironment.compile(base);
const squall = { at:4,profile:'storm',duration:3,ease:'linear' };
const clear = { at:5,profile:'clearing',duration:2,ease:'linear' };
const near = (a,b) => assert(Math.abs(a-b)<1e-10, a + ' vs ' + b);

test('the first frame keeps every sampled value, and interrupted channels keep moving on their own', () => {
  const withStorm = sky.interrupt(squall);
  assert.deepEqual(withStorm.frame(4),sky.frame(4));
  assert.deepEqual(withStorm.sample(3.99999),sky.sample(3.99999));
  const previous = withStorm.sample(5), interrupted = withStorm.interrupt(clear);
  assert.deepEqual(interrupted.sample(5),previous);
  near(interrupted.sample(6).rain,previous.rain/2);
  near(interrupted.sample(7).fogDensity,.3);
  assert.deepEqual(interrupted.sample(6).horizon,withStorm.sample(6).horizon);
  near(interrupted.sample(6).windX,sky.sample(6).windX);
  assert(withStorm.sample(5).sunAzimuth > 6.1, 'azimuth follows the short path through zero');
  assert.equal(withStorm.sample(7).sunAzimuth,.2);
  assert.deepEqual(withStorm.sample(7).horizon,sky.profile('storm').horizon);

  const pinned = { light:'start' };
  assert.deepEqual(withStorm.frame(4,pinned),sky.frame(4,pinned));
  assert.notDeepEqual(withStorm.sample(5,pinned),withStorm.sample(5));
});

test('authored transitions round-trip and match runtime events in any seek order', () => {
  const gust = {at:5,profile:'gust',duration:1};
  const before = sky.interrupt(squall).interrupt(clear).interrupt(gust);
  const doc = JSON.parse(JSON.stringify({ ...base, transitions:[gust,clear,squall] }));
  const after = K.skyEnvironment.compile(doc);
  for (const t of [8,5,0,6,4,9,2,5.5,7]) assert.deepEqual(before.frame(t),after.frame(t));
  assert(Object.isFrozen(before.transitions) && before.transitions.every(Object.isFrozen));
  assert.equal(before.transitions.length,3);
  assert.equal(sky.transitions.length,0);
  assert.equal(after.sample(6).windZ,1.2);
  const sameFrame = sky.interrupt(squall).interrupt({ ...clear,at:4 });
  assert.deepEqual(sameFrame.frame(4),sky.frame(4));
  assert.equal(sameFrame.sample(6).rain,0);
  assert.deepEqual(sameFrame.sample(6).horizon,sky.interrupt(squall).sample(6).horizon);
  assert.deepEqual(after.withTransitions(false).frame(6),sky.frame(6));
  assert.throws(()=>sky.interrupt({...clear,duration:0}),/duration/);
  assert.throws(()=>sky.interrupt({...clear,profile:'missing'}),/Unknown/);
  assert.throws(()=>sky.interrupt({...clear,profile:'invalid'}),/initial object value for z/);
  assert.throws(()=>sky.interrupt({...clear,profile:'wrong'}),/initial object value for humidity/);
  assert.throws(()=>sky.interrupt({...clear,ease:'hold'}),/linear or smooth/);
});

test('weather forcing, retained wetness and rendered fog share the interrupted history', () => {
  const surface = {width:4,height:4,cell:1,origin:[-2,-2],step:.125,evaporation:.15,maxRunoff:0};
  const time = 4;
  const original = K.weather.bind(sky,{surface});
  const next = K.weather.bind(sky.interrupt(squall),{surface});
  for (const t of [time,3.75,1]) {
    assert.deepEqual(original.sample(t),next.sample(t));
    assert.deepEqual(original.surfaceAt(t).sample(0,0),next.surfaceAt(t).sample(0,0));
  }
  assert(next.frame(6).rainGain > original.frame(6).rainGain);
  assert(next.frame(6).surface(0,0).wetness > original.frame(6).surface(0,0).wetness);
  assert.deepEqual(next.frame(4).surface(0,0),original.frame(4).surface(0,0));

  const world = makeBuilder(9,[0x212638]).finish({
    cam:{target:[0,.7,0],yaw:0,pitch:.09,dist:6},detail:18,skyEnvironment:sky,
    weatherBinding:{surface},atmosphere:[K.atmosphere.fog({density:.30,color:'#a1c2cd',top:4,bottom:-1,far:9})]
  });
  const view = {w:47,h:31,px:1,raw:true,captureFog:true};
  const reference = ink.render(world,{...view,t:time});
  const trigger = ink.render(world,{...view,t:time,skyTransitions:[squall]});
  assert.deepEqual(trigger.rgb,reference.rgb);
  assert.deepEqual(trigger.fog,reference.fog);
  const transition = ink.render(world,{...view,t:6,skyTransitions:[squall]});
  const expected = ink.render(world,{...view,t:6,skyEnvironment:sky.interrupt(squall)});
  assert.deepEqual(transition.rgb,expected.rgb);
  assert.deepEqual(transition.fog,expected.fog);
  const plan = [squall];
  const first = ink.render(world,{...view,t:6,skyTransitions:plan});
  plan.push(clear);
  const superseded = ink.render(world,{...view,t:6,skyTransitions:plan});
  assert.notDeepEqual(first.fog,superseded.fog);
  assert.deepEqual(superseded.fog,ink.render(world,{...view,t:6,skyEnvironment:sky.withTransitions(plan)}).fog);
});

test('a revision-pinned environment pack accepts transition cues and CLI can override them', t => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(),'ink-sky-transition-'));
  t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  const file = name => path.join(root,name);
  const input = {format:'ink-studio/asset-pack',version:1,id:'shore',title:'Shore',revision:2,
    environments:[{id:'shore/sunset',label:'Sunset',settings:{skyEnvironment:{...base,transitions:[squall]}}}]};
  const diorama = {id:'shore',name:'Shore',environmentPreset:{asset:'shore/sunset',revision:2},
    camera:{target:[0,.7,0],yaw:0,pitch:.09,dist:6},
    solids:[{kind:'ball',at:[0,0,0],r:.4,mat:'stone'}]};
  fs.writeFileSync(file('pack.json'),JSON.stringify(input));
  fs.writeFileSync(file('scene.json'),JSON.stringify(diorama));
  fs.writeFileSync(file('events.json'),JSON.stringify([squall]));
  const cli = path.join(__dirname,'../cli/ink-studio.js');
  function draw(name, settings = []) {
    execFileSync(process.execPath,[cli,'render',file('scene.json'),'--asset-pack',file('pack.json'),'--t','6','--raw','--px','1',
      '--w','42','--h','24','--out',file(name),...settings],{cwd:root});
    return fs.readFileSync(file(name));
  }
  const authored = draw('authored.png');
  assert.deepEqual(authored,draw('overridden.png',['--sky-transitions',file('events.json')]));
  assert.notDeepEqual(authored,draw('off.png',['--sky-transitions','off']));
});

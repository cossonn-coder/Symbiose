const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const test = require('node:test');
const ink = require('..');
const PNG = require('../cli/png.js');
const { makeBuilder } = ink.load();
const native = { width:36, height:24, view:{raw:true} };
const cam = { yaw:0, pitch:.05, dist:6, target:[0,.12,0] };
const flat = color => ({ zenith:color, horizon:color, ground:color, sunStrength:0 });

function sky(a, b, loop = false, ease = 'hold') {
  return {
    profiles:{ a:flat(a), b:flat(b) },
    sequences:{ phase:{ duration:4, loop, keys:[{at:0,profile:'a',ease},{at:2,profile:'b',ease}] } },
    tracks:[{id:'sky',sequence:'phase'}]
  };
}

function world(skyEnvironment, geometry = false) {
  const B = makeBuilder(1,[0x121a25,0xeaad5c,0x466998]);
  if (geometry) {
    B.disc(-1,.35,-.25,[0,0,1],.65,.12,B.P[1],2);
    B.disc(1,-.20,.35,[0,0,1],.28,.20,B.P[2],2);
  }
  return B.finish({cam,detail:22,skyEnvironment});
}

function tile(sheet, rect) {
  const rgb = new Uint8Array(rect.width * rect.height * 3);
  for (let y = 0; y < rect.height; y++) {
    const start = ((rect.y+y)*sheet.w+rect.x)*3;
    rgb.set(sheet.rgb.subarray(start,start+rect.width*3), y*rect.width*3);
  }
  return rgb;
}
const boundary = event => event.steps[event.boundaryStep];
const kinds = evidence => evidence.flags.map(flag => flag.kind);

test('sampling wraps midnight at the requested fps and preserves export pixels', () => {
  const w = world(sky('#1f2738','#33324a',true,'smooth'));
  const plan = {fps:12,events:[{id:'midnight',kind:'midnight',at:1,skyTime:4}]};
  const {image,report} = ink.transitionReview(w,{...native,plan});
  const row = report.events[0], before = row.frames[1], after = row.frames[2];
  assert.equal(before.skyTime,4-1/12);
  assert.equal(after.skyTime,4);
  assert.equal(report.flagCount,0);
  for (let i=0;i<row.frames.length;i++) {
    const frame = row.frames[i];
    const direct = ink.render(w,{w:36,h:24,px:1,raw:true,t:frame.time,skyTime:frame.skyTime});
    assert.deepEqual(tile(image,row.tiles[i]),direct.rgb);
  }
});

test('flags a one-frame brightness pop and a separate chroma change', () => {
  const plan = { fps:10, events:[{id:'front',kind:'storm',at:2}] };
  let report = ink.transitionReview(world(sky('#999999','#333333')),{...native,plan}).report;
  assert.deepEqual(kinds(boundary(report.events[0]).screen),['pop','lighting-jump']);
  assert.equal(boundary(report.events[0]).screen.metrics.lumaShift,-.4);
  const w = world(sky('#d04090','#107a80'));
  report = ink.transitionReview(w,{...native,plan}).report;
  assert.deepEqual(kinds(boundary(report.events[0]).screen),['pop','palette-change']);
  assert.equal(report.events[0].evidence.offset,0);
  assert.equal(report.events[0].steps[0].screen.flags.length,0);
  assert.equal(report.events[0].steps[2].screen.flags.length,0);
});

test('detects a changed output palette even with a neutral ramp', () => {
  const cloudy = sky('#555555','#555555');
  cloudy.profiles.a.deck = 0;
  cloudy.profiles.b.deck = 1;
  const w = world(cloudy);
  w.look = { effectPalettes:{sky:{colors:['#888888'],when:{channel:'deck',min:.5}}} };
  const plan = { events:[{id:'ramp',at:2}], thresholds:{lightingDelta:1,popFraction:1} };
  const { report } = ink.transitionReview(w,{...native,view:{},plan});
  const {metrics,flags} = boundary(report.events[0]).screen;
  assert(metrics.paletteReplacement>.95);
  assert.deepEqual(flags.map(flag=>flag.kind),['palette-change']);
});

test('expected camera cut compares both locked views and keeps actual framing in the sheet', () => {
  const cut = {id:'gate-cut',kind:'cut',at:2,incomingCamera:{target:[1.2,0,0],yaw:1.15,zoom:1.4}};
  const plan = { fps:12, thresholds:{popFraction:.02}, events:[cut] };
  const w = world(sky('#60758e','#60758e'),true);
  let {image,report} = ink.transitionReview(w,{...native,plan});
  let event = report.events[0], step = boundary(event);
  assert.equal(step.expectedCut,true);
  assert(step.screen.metrics.changedFraction > .02);
  assert.equal(report.flagCount,0);
  assert.deepEqual(step.matched.map(kinds),[[],[]]);
  assert.notDeepEqual(tile(image,event.tiles[1]),tile(image,event.tiles[2]));
  for (let i=0;i<4;i+=2) assert.deepEqual(tile(image,event.matchedTiles[i]),tile(image,event.matchedTiles[i+1]));

  report = ink.transitionReview(world(sky('#aaaaaa','#333333'),true),{...native,plan}).report;
  event = report.events[0];
  step = boundary(event);
  assert.equal(step.screen.flags.length,0);
  assert(step.matched.every(pair => kinds(pair).includes('lighting-jump')));
  assert(event.flagCount>=2);
});

test('overlapping reviews pose once per time in chronological order and lock animated camera motion', () => {
  const w = world(sky('#815321','#815321'),true);
  w.anim = { stateful:true };
  const plan = { fps:8, preroll:1, events:[{id:'later',at:1.125},{id:'early',at:1}] };
  assert.throws(() => ink.transitionReview(w,{...native,plan}), /stateful scene needs a pose callback/);
  const passes = [];
  const { report } = ink.transitionReview(w,{...native,plan,pose(world,t) {
    passes.push(t);
    world.anim.kick = [t*2,0,0];
    world.anim.zoom = 1+t;
  }});
  assert.deepEqual(passes,[.625,.75,.875,1,1.125,1.25]);
  assert.deepEqual(report.events.map(event => event.id),['later','early']);
  assert(report.events.every(event => event.steps.every(step => step.screen.metrics.changedFraction === 0)));
  assert.throws(() => ink.transitionReview(w,{...native,pose:()=>{},plan:{events:[{id:'zero',at:0}]}}),/before the event/);
});

test('CLI writes the native review sheet and flags sidecar before optional nonzero status', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(),'ink-transition-'));
  t.after(() => fs.rmSync(dir,{recursive:true,force:true}));
  const fixture = path.join(dir,'scene.js'), plan = path.join(dir,'plan.json'), output = path.join(dir,'review.png');
  fs.writeFileSync(fixture,`module.exports=({makeBuilder})=>({
    id:'review-fixture',name:'Review',build:()=>makeBuilder(1,[0]).finish({cam:${JSON.stringify(cam)},
    detail:20,skyEnvironment:${JSON.stringify(sky('#999999','#333333'))}})
  });`);
  fs.writeFileSync(plan,JSON.stringify({events:[{id:'storm',kind:'storm',at:2}]}));
  const cli = path.resolve(__dirname,'../cli/ink-studio.js');
  const args = [cli,'transition-review',fixture,'--plan',plan,'--w','36','--h','24','--raw','--out',output];
  const normal = spawnSync(process.execPath,args,{cwd:dir,encoding:'utf8'});
  assert.equal(normal.status,0,normal.stderr);
  const strict = spawnSync(process.execPath,[...args,'--fail-on-flags'],{cwd:dir,encoding:'utf8'});
  assert.equal(strict.status,2,strict.stderr);
  const summary = JSON.parse(fs.readFileSync(path.join(dir,'review.json')));
  const image = PNG.read(output);
  assert.equal(summary.width,36);
  assert.equal(summary.height,24);
  assert.equal(image.w,summary.sheet.w);
  assert.deepEqual(kinds(boundary(summary.events[0]).screen),['pop','lighting-jump']);
});

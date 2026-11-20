const test = require('node:test');
const assert = require('node:assert/strict');
const kit = require('..').load();
const { KIT:{world:W,procedural:P}, makeBuilder } = kit;
const demo = require('../examples/world-lightwell-workshop.json');
const copy = data => JSON.parse(JSON.stringify(data));
const system = 'workshop';
const lighting = run => run.query().probe(system+'/lighting').value;
const render = run => run.query().renderVolume(system);
const shades = world => world.parts.map(part => part.data);
const rgb = n => [n&255,n>>8&255,n>>16&255];

test('a skylight relights retained surfaces along its shadow path and agrees with a fresh render', () => {
  const run=W.runtime.create(demo), before=render(run);
  const references=new Map(before.parts.flatMap(part=>part.splatIds.map((id,i)=>[id,part.data[i*16+7]])));
  run.advance(2);
  const open=render(run), w=lighting(run);
  assert(w.relitChunks.length>0 && w.reusedChunks>w.relitChunks.length);
  assert(w.shadowRays>0 && w.diffuseRays>0);
  const geometry=run.query().probe(system+'/work').value.lastEdit.splatChunks;
  assert(w.relitChunks.some(id=>!geometry.includes(id)),'The shadow must update surfaces with unchanged geometry');
  assert(open.parts.some(part=>part.splatIds.some((id,i)=>references.has(id)&&part.data[i*16+7]!==references.get(id))));
  assert(open.parts.some((part,i)=>part.count>0&&part===before.parts[i]));
  const saved=copy(run.checkpoint());
  assert.deepEqual(shades(open),shades(render(W.runtime.create(demo,{checkpoint:saved}))));

  run.advance(4);
  const moved=render(run), light=lighting(run);
  assert.equal(light.gatheredSamples,0);
  assert.equal(light.diffuseRays,0);
  assert(light.shadowRays>0 && light.reusedChunks>0);
  assert(open.parts.some((part,i)=>part.count>0&&part!==moved.parts[i]));
  assert.deepEqual(open.parts.map(part=>part.splatIds),moved.parts.map(part=>part.splatIds));
  assert.deepEqual(shades(moved),shades(render(W.runtime.create(demo,{checkpoint:copy(run.checkpoint())}))));
  assert.deepEqual(run.checkpoint(),W.runtime.replay(copy(run.recording())).checkpoint());
});

test('local bounce changes with donor paint and lamp motion even with no direct light on the receiver', () => {
  const b=makeBuilder(4,[0,0xffffff]), index=b.count();
  b.disc(0,0,0,[0,1,0],.2,.04,b.P[1],1);
  b.describeAlbedo(index,b.count(),'#ffffff');
  const part=b.finish(), box={min:[-.25,-.25,-.25],max:[.25,.25,.25]};
  const region={min:[-6,-1,-4],max:[6,2,4]};
  const context=P.relighting.create({ambient:.08,indirect:{distance:2.5,strength:1.2,rays:1},lamps:{
    lantern:{at:[0,0,-.75],range:3,intensity:3}
  }},{bounds:region,cell:.15});
  const field=albedo=>({distance:(x,y,z)=>Math.abs(y-1.1)-.1,albedo:()=>albedo});
  const chunks=[{id:'floor',bounds:box,part}];
  const red=context.refresh({chunks,field:field(0xff2010)});
  const first=rgb(red.parts[0].data[7]);
  assert(first[0]>first[1]+35);
  const edits=[{bounds:{min:[-1,.99,-1.5],max:[1,1.22,.4]},occlusion:false}];
  const green=context.refresh({chunks,field:field(0x12ff18),previous:red,edits});
  const second=rgb(green.parts[0].data[7]);
  assert(second[1]>second[0]+35);
  const lamps=P.relighting.lamps({lantern:{at:[4,0,-.75],range:3,intensity:3}});
  const dark=context.refresh({chunks,field:field(0x12ff18),previous:green,lamps});
  const third=rgb(dark.parts[0].data[7]);
  assert.equal(third[0],third[1]);
  assert(third[1]<second[1]);
  assert.equal(dark.work.diffuseRays,0);
  assert.deepEqual(shades(dark),shades(context.refresh({chunks,field:field(0x12ff18),lamps})));
});

test('lighting requests preserve old snapshots and compose multiple edits before the next render', () => {
  const run=W.runtime.create(demo), old=run.query();
  const initial=old.renderVolume(system);
  run.advance(4);
  const query=run.query(), fresh=W.runtime.create(demo,{checkpoint:copy(run.checkpoint())});
  const after=query.renderVolume(system);
  assert.deepEqual(shades(after),shades(render(fresh)));
  assert.strictEqual(old.renderVolume(system),initial);
  run.schedule([{tick:5,action:system+'/set-light',args:{id:'lantern',enabled:false}},
    {tick:6,action:system+'/set-light',args:{id:'lantern',enabled:true}}]);
  run.advance(6);
  const resumed=render(run);
  assert.deepEqual(shades(after),shades(resumed));
  assert.equal(lighting(run).relitChunks.length,0);
  assert.equal(lighting(run).shadowRays,0);
  assert.throws(()=>run.schedule([{tick:7,action:system+'/set-light',args:{id:'bad',range:4}}]),/authored point light/);
});

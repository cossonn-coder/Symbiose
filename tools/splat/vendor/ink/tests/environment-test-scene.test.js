const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('../index.js');
const define = require('../examples/environment-test-scene.js');
const { compare } = require('../cli/environment-parity.js');

const kit = ink.load(), scene = define(kit);
const byId = id => scene.checkpoints.find(key=>key.id===id);
const camera = (id,ortho) => scene.camera(byId(id).time,ortho);
const view = {w:192,h:128,px:1,raw:true};
const channelError = (a,b,pixel) => Math.max(...[0,1,2].map(c=>Math.abs(a[pixel*3+c]-b[pixel*3+c])));

test('observatory camera separates orbit, pitch and pan, then crosses both fog boundaries',()=>{
  const establish = camera('establish'), orbit = camera('orbit');
  const pitch = camera('pitch'), pan = camera('pan');
  assert.deepEqual(orbit.target,establish.target);
  assert.equal(orbit.dist,establish.dist);
  assert.equal(orbit.pitch,establish.pitch);
  assert(orbit.yaw-establish.yaw>.3);
  assert.deepEqual(pitch.target,orbit.target);
  assert.equal(pitch.yaw,orbit.yaw);
  assert(pitch.pitch-orbit.pitch>.1);
  assert.deepEqual([pan.yaw,pan.pitch,pan.dist],[pitch.yaw,pitch.pitch,pitch.dist]);
  assert(Math.abs(pan.eye[0]-pitch.eye[0]-.78)<1e-8);

  const world = scene.animate(scene.build(scene.seed));
  const {min,max} = world.atmosphere[0];
  const isInside = eye => eye.every((n,i)=>min[i]<n && n<max[i]);
  const approach = camera('approach'), inside = camera('inside'), exit = camera('exit');
  assert(approach.eye[2]>max[2]);
  assert(isInside(inside.eye));
  assert(exit.eye[2]<min[2]);
  for (const {time} of scene.checkpoints) {
    const perspective = scene.camera(time), orthographic = scene.camera(time,true);
    assert.deepEqual(orthographic,{...perspective,ortho:true});
    world.anim.update(0,time);
    assert.deepEqual(world.cam,{...perspective,sway:0});
  }
});

test('the tower masks the card and the tinted pane transmits fog without changing surface depth',()=>{
  const world = scene.build(scene.seed);
  const settings = {...view,...camera('establish'),passes:['foregroundCoverage','objectId','depth','fogTransmittance']};
  const sample = (source,override) => ink.render(source,{...settings,...override});
  const frame = sample(world), noCard = sample(world,{cloudField:false});
  const tower = frame.passes.objects.indexOf('tower');
  const pane = frame.passes.objects.indexOf('transparent pane');
  assert(tower>0 && pane>0);
  let shielded = 0, visible = 0;
  for (let p=0;p<view.w*view.h;p++) {
    const delta = channelError(frame.rgb,noCard.rgb,p);
    const {foregroundCoverage,objectId} = frame.passes;
    if (objectId[p]===tower && foregroundCoverage[p]>.985 && delta<=3) shielded++;
    if (foregroundCoverage[p]<.15 && delta>18) visible++;
  }
  assert(shielded>400 && visible>400, 'the card is visible outside the opaque tower silhouette');

  const openWorld = {...world,data:world.data.slice()};
  let panes = 0;
  for (let i=0;i<openWorld.count;i++) if (openWorld.renderMetadata.objectIds[i]===pane) {
    assert(openWorld.data[i*16+3]>0 && openWorld.data[i*16+3]<1);
    openWorld.data[i*16+3] = 0;
    panes++;
  }
  assert(panes>0);
  const open = sample(openWorld), noFog = sample(world,{atmosphere:false});
  assert.deepEqual(frame.passes.depth,open.passes.depth);
  assert.deepEqual(frame.passes.fogTransmittance,open.passes.fogTransmittance);
  let tintedFog = 0;
  for (let p=0;p<view.w*view.h;p++) {
    if (frame.passes.fogTransmittance[p]<.85 && channelError(frame.rgb,open.rgb,p)>5 &&
        channelError(frame.rgb,noFog.rgb,p)>6) tintedFog++;
  }
  assert(tintedFog>1500, 'a substantial part of the pane still shows fog behind it');

  const sampleFog = id => sample(world,{...camera(id),t:byId(id).time}).passes.fogTransmittance;
  assert(sampleFog('inside').some(value=>value<.66));
  assert(sampleFog('exit').every(value=>value===1));
});

test('observatory exports matched CLI and WebGL checkpoints in both projections', {
  skip: !process.env.INK_TEST_CHROME
},()=>{
  const {fixture,frames} = compare({fixture:'observatory'});
  assert.equal(fixture,'observatory');
  assert.equal(frames.length,scene.checkpoints.length*2);
  for (const mode of ['perspective','ortho']) {
    const matching = frames.filter(frame=>frame.id.startsWith(mode+'-'));
    assert.deepEqual(matching.map(frame=>frame.id.slice(mode.length+1)),scene.checkpoints.map(key=>key.id));
    assert(matching.every(frame=>frame.camera.ortho===(mode==='ortho')));
    assert(matching.some(frame=>frame.cliEffect>1 && frame.webglEffect>1),mode+' shows the cloud card');
    for (const frame of matching) {
      assert(frame.mean<2.5 && frame.p95<=20,frame.id+' stays within the comparison tolerance');
    }
  }
});

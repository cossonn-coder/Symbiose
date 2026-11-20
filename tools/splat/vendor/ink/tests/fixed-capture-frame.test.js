const test = require('node:test'), assert = require('node:assert/strict');
const { captureFrame: F } = require('..').load().KIT;
const { makeBuilder } = require('..').load();
const { render } = require('..');

test('a fixed PNG keeps the crop composition as the source view scales', () => {
  const options = {aspect:'portrait',edge:1920,scale:4};
  const a = F.fixed(400,300,options), b = F.fixed(800,600,options);
  assert.deepEqual([a.x,a.y,a.width,a.height],[87.5,0,225,300]);
  assert.deepEqual([b.x,b.y,b.width,b.height],[175,0,450,600]);
  for (const f of [a,b]) {
    assert.deepEqual([f.outputWidth,f.outputHeight],[1440,1920]);
    assert.deepEqual([f.renderWidth,f.renderHeight,f.lensScale],[360,480,1]);
  }
  const wide = F.fixed(320,480,{aspect:'wide',edge:1920,scale:2});
  assert.equal(wide.y,150);
  assert.equal(wide.lensScale,480/180);
  for (const args of [[0,12,{}],[17,4,{aspect:'toString'}],[17,4,{aspect:0}],
    [30,20,{edge:7.5}],[30,20,{edge:8192,aspect:'square'}],[30,20,{scale:0}]])
    assert.throws(()=>F.fixed(...args),/Capture/);
});

test('odd output dimensions preserve exact art pixels and convert bottom-up readback',()=>{
  const f = F.fixed(8,5,{edge:5,scale:2}), data=Uint8Array.of(1,2,3,4,5,6);
  assert.deepEqual([f.outputWidth,f.outputHeight,f.renderWidth,f.renderHeight],[5,3,3,2]);
  assert.deepEqual([...F.pixels(data,f,{channels:1,flipY:true})],[
    4,4,5,5,6, 4,4,5,5,6, 1,1,2,2,3
  ]);
  assert.deepEqual([...data],[1,2,3,4,5,6]);
  assert.throws(()=>F.pixels(data,f),/matching byte raster/);
});

test('the offscreen software renderer reprojects the same centred crop at a fixed target',()=>{
  const B=makeBuilder(1,[0x172129,0xff9244]);
  B.dab(.32,1,.4,[0,0,1],[1,0,0],.22,.18,.09,B.P[1],3);
  const world=B.finish({cam:{yaw:0,pitch:0,dist:5,target:[0,1,0]}});
  const full=render(world,{w:128,h:100,px:1,raw:true});
  const f=F.fixed(128,100,{aspect:'wide',edge:128,scale:1});
  const shot=render(world,{w:f.renderWidth,h:f.renderHeight,px:1,raw:true,lensScale:f.lensScale});
  assert.equal(shot.w,128);
  assert.equal(shot.h,72);
  assert.deepEqual([...shot.rgb],[...full.rgb.subarray(14*128*3,(14+72)*128*3)]);
  assert.throws(()=>render(world,{lensScale:0}),/Lens scale/);
});

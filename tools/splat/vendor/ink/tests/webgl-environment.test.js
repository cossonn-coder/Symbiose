const { test } = require('node:test');
const assert = require('node:assert/strict');
const { compare } = require('../cli/environment-parity.js');
const runWebGL = require('../cli/look-webgl.js');

test('fixed cameras match the CLI directional sky, depth-aware cloud card and bounded fog', {
  skip: !process.env.INK_TEST_CHROME
}, () => {
  const {frames} = compare();
  assert.equal(frames.length,7);
  for (const frame of frames) {
    assert(frame.cliEffect > 2 && frame.webglEffect > 2, frame.id+' draws the environment effect');
    assert(Math.abs(frame.cliEffect-frame.webglEffect) < .35, frame.id+' responds to its effect toggle');
    assert(frame.mean < .55 && frame.p95 <= 4, frame.id+' matches at the art grid');
    assert(frame.fractionAbove12 < .005, frame.id+' has no large visible mismatch');
  }
  for (const frame of frames.filter(frame=>!frame.cloud && !frame.fog)) {
    assert(frame.mean < .01, frame.id+' matches the isolated directional sky');
    assert.equal(frame.p95,0);
  }
});

test('bounded fog works with material-pixel and water shader variants', {
  skip: !process.env.INK_TEST_CHROME
}, () => {
  const result = runWebGL({},({makeBuilder,makeSculpt,KIT:K})=>{
    const B = makeBuilder(3,[0x102032,0xa85f47,0xf0cca2,0x536d8c]);
    const S = K.sculpt(makeSculpt(B));
    S.pixel = true;
    S.box([0,0,0],[1.8,.45,1.2],{r:[1,2]},{res:.12});
    S.bake();
    const body = K.procedural.waterBodies.create({id:'pool',bounds:{min:[-3,-3],max:[3,3]},
      sample:()=>({bed:-2,surface:-.35})});
    const water = K.procedural.waterBodies.scene([body]);
    return B.finish({cam:{target:[0,0,0],yaw:.14,pitch:.22,dist:7},radius:6,look:{pixel:true},
      water,atmosphere:[K.atmosphere.sphere({at:[0,0,4],radius:2.4,color:'#869ac6',density:.23})]});
  },(kit,fixture,backend)=>{
    const world = fixture(kit), draw = backend(64,48,{dither:0,damp:false,colored:false});
    try {
      const changed = [false,true].map(water=>{
        draw.draw(world,{water,atmosphere:false});
        const dry = draw.image();
        draw.draw(world,{water});
        return dry !== draw.image();
      });
      return {changed};
    } finally {
      draw.close();
    }
  });
  assert.deepEqual(result.changed,[true,true]);
});

const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('../index.js');
const { KIT: K, makeBuilder, makeSculpt } = ink.load();
const optics = K.atmosphere;

const density = K.procedural.density.bounded({
  bounds: { min:[-10,-4,-1], max:[10,4,1] }, sample: () => 1
});
const fog = optics.prepare([optics.field({ field:density, density:.45, step:.11, color:'#ffffff', anisotropy:0 })]);
const spot = { at:[0,0,0], direction:[1,0,0], innerAngle:8, outerAngle:28, radius:8, intensity:2, color:'#ff0000' };

function trace(x, y, settings, options) {
  const media = optics.lighting({ ambient:0, ...settings }, [], options);
  return optics.trace(fog, [x,y,3], [0,0,-1], 5, undefined, { media });
}

test('aimable fog lights have a soft cone and finite reach, and can share a volume with point lights', () => {
  const settings = { spots:[spot], points:[{ at:[3.6,0,0], radius:3, color:'#0000ff' }] };
  const [r,g,b,t] = trace(4, 0, settings);
  assert(r > .22 && b > .30);
  assert.equal(g, 0);
  const soft = trace(4, 1.15, { spots:[spot] })[0];
  assert(soft > .02 && soft < r * .82);
  for (const [x,y] of [[4,2.5], [-4,0], [9,0]]) {
    assert.equal(trace(x, y, { spots:[spot] })[0], 0);
  }
  assert.deepEqual(trace(4, 0, settings, { localLights:false }), [0,0,0,t]);

  let updates = 0;
  const beacon = { ...spot, direction(t) { updates++; return [Math.cos(t), 0, Math.sin(t)]; } };
  assert(trace(4, 0, { spots:[beacon] }, { time:0 })[0] > .22);
  assert.equal(trace(4, 0, { spots:[beacon] }, { time:Math.PI })[0], 0);
  assert.equal(updates, 2, 'aim is resolved once for each lighting frame');
  assert.throws(() => trace(4, 0, { spots:[{ ...spot, direction:[0,0,0] }] }), /Spot direction/);
  assert.throws(() => trace(4, 0, { spots:[{ ...spot, innerAngle:30 }] }), /Spot inner angle/);
});

test('local shadow rays stop at the light and leave extinction and other illumination intact', () => {
  const slab = x => Math.abs(x - 2) - .15;
  const sun = { direction:[0,1,0], color:'#ffffff', intensity:.23 };
  const setting = { ambient:.22, sun, spots:[spot], shadow:optics.occluder(slab) };
  const blocked = trace(4, 0, setting);
  const open = trace(4, 0, setting, { localShadows:false });
  assert.deepEqual(blocked, trace(4, 0, setting, { localLights:false }));
  assert.deepEqual(open, trace(4, 0, { ...setting, spots:[{ ...spot, castsShadow:false }] }));
  assert.deepEqual(open, trace(4, 0, { ...setting, shadow:optics.occluder(x => Math.abs(x + 1) - .15) }));
  assert(open[0] > blocked[0] + .20);
  assert.deepEqual(open.slice(1), blocked.slice(1));
});

test('the CPU renderer lets sculpted geometry cut a moving cone in perspective and orthographic views', () => {
  const B = makeBuilder(5, [0, 0x727276]);
  const S = K.sculpt(makeSculpt(B));
  S.box([0,0,0],[.19,.67,.79],{ r:[1] },{ res:.14 });
  const shadow = optics.occluder(S.modelSource().field.sdf);
  S.bake();
  const world = B.finish({ cam:{ target:[0,0,0], dist:10, pitch:0, yaw:0, sway:0 }, radius:12, detail:18,
    atmosphere:[optics.field({ field:density, density:.45, step:.14, color:'#ffffff', anisotropy:0 })],
    volumeLighting:{ ambient:.03, shadow, spots:[{ ...spot, at:[-3,0,0], direction:t => t ? [-1,0,0] : [1,0,0] }] }
  });
  for (const ortho of [false,true]) {
    const view = { w:95, h:55, px:1, raw:true, ortho, captureFog:true };
    const blocked = ink.render(world, view);
    const open = ink.render(world, { ...view, volumeLocalShadows:false });
    const off = ink.render(world, { ...view, volumeLocalLights:false });
    const turned = ink.render(world, { ...view, t:1 });
    const center = (27 * open.w + 65) * 3;
    assert(open.rgb[center] > blocked.rgb[center] + 12, 'the sculpt occludes the light beyond the wall');
    assert(open.rgb[center] > off.rgb[center] + 28, 'the optional light brightens the mist');
    assert.equal(turned.rgb[center], off.rgb[center], 'turning the spot away clears the beam');
    assert.deepEqual(open.fog, blocked.fog);
    assert.deepEqual(open.fog, off.fog);
  }
});

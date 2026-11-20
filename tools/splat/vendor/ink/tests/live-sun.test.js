const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('../index.js');
const { KIT, makeBuilder, makeSculpt } = ink.load();

const view = { w: 111, h: 81, px: 1, raw: true, passes: ['position', 'materialId'] };
function gallery() {
  const B = makeBuilder(4, [0x15202a, 0x555555, 0xcccccc, 0xffb650]);
  const S = KIT.sculpt(makeSculpt(B));
  S.captureAlbedo = true;
  S.sun = KIT.V.norm([1, 1, 1]);
  S.box([0, -.12, 0], [3, .12, 2.6], { r: [1, 2], albedo: '#cccccc', materialId: 'floor' }, { res: .11 });
  S.box([0, .80, 0], [.35, .82, .36], { r: [1,2], materialId: 'pillar' }, { res: .085 });
  S.ball([0, 1.78, 0], .19, { r: [3], em: true, materialId: 'lamp' }, { res: .07 });
  S.bake();
  return B.finish({ cam: { target:[0,.35,0], dist:9.8, yaw:0, pitch:.90 }, detail:18, radius:6, dither:0 });
}

function floorShadow(im, open) {
  const { position, materialId, materials } = im.passes;
  const affected = [];
  for (let p = 0; p < materialId.length; p++) {
    const i = p * 3;
    if (materials[materialId[p]] !== 'floor' || Math.abs(position[i + 1]) > .08 ||
        Math.abs(position[i + 2]) > .32 || Math.abs(position[i]) < .57 || Math.abs(position[i]) > 1.7) continue;
    if (open.rgb[i] - im.rgb[i] > 70) affected.push(position[i]);
  }
  return affected;
}

test('live sun rebuilds directional shadows from opaque sculpted splats as time changes', () => {
  const world = gallery();
  const light = { direction: time => time < .5 ? [1, .80, 0] : [-1, .80, 0], ambient:.22, intensity:.93 };
  for (const ortho of [false, true]) {
    const settings = { ...view, ortho, liveSun: light };
    const east = ink.render(world, { ...settings, t:0 });
    const west = ink.render(world, { ...settings, t:1 });
    const open = ink.render(world, { ...settings, t:0, liveSun: { ...light, shadows:false } });
    const a = floorShadow(east, open), b = floorShadow(west, open);
    assert(a.length > 10 && b.length > 10, 'cast shadows cover the floor');
    assert(a.every(x => x < 0) && b.every(x => x > 0), 'the floor shadow crosses the pillar');
    assert.deepEqual(east.rgb, ink.render(world, { ...settings, t:0 }).rgb);
    const ids = east.passes.materialId, lamp = east.passes.materials.indexOf('lamp');
    const fullyCovered = ink.render(world, { ...settings, t:0, passes:['materialId','coverage'] }).passes.coverage;
    let count = 0;
    for (let i=0; i<ids.length; i++) {
      if (ids[i] !== lamp || fullyCovered[i] < .98) continue;
      if (east.rgb[i*3] > 247 && west.rgb[i*3] > 247) count++;
    }
    assert(count > 0, 'emissive lamp stays bright');
  }
});

test('scene settings can be overridden per frame and baked rendering remains the default', () => {
  const world = gallery();
  const baked = ink.render(world, view);
  assert.deepEqual(ink.render(world, { ...view, liveSun:false }).rgb, baked.rgb);
  const configured = { ...world, liveSun: { direction:[1,1,0], ambient:.20, intensity:.9 } };
  assert.deepEqual(ink.render(configured, { ...view, liveSun:false }).rgb, baked.rgb);
  assert.notDeepEqual(ink.render(configured, view).rgb, baked.rgb);
  assert.notDeepEqual(ink.render(configured, { ...view, liveSun:{ direction:[-1, 1, 0] } }).rgb, ink.render(configured, view).rgb);
  assert.throws(() => ink.render(world, { ...view, liveSun:{ direction:[0, 0, 0] } }), /nonzero XYZ/);
  assert.throws(() => ink.render(world, { ...view, liveSun:{ mapSize:0 } }), /shadow map settings/);
});

function bounceFixture() {
  const B = makeBuilder(17, [0x192531, 0x2c2c2c, 0x777777, 0xc4c4c4, 0xffffff]);
  const ramp = [1, 2, 3, 4];
  for (const [id, x, normal] of [
    ['top', -1.25, [0, 1, 0]], ['wall', 0, [0, 0, 1]], ['underside', 1.25, [0, -1, 0]]
  ]) {
    const i = B.count();
    B.pixNext(ramp, .6, null, ...normal);
    B.disc(x, 0, 0, normal, .35, .025, B.P[3], 3);
    B.describeSplats(i, i + 1, { object: id });
    B.describeAlbedo(i, i + 1, '#d5d5d5');
  }
  return B.finish({ cam: { target:[0,0,0], dist:6.2, yaw:0, pitch:.58 }, detail:18, look:{ pixel:true } });
}

function colorAt(frame, name) {
  const { objectId, objects, coverage } = frame.passes;
  const id = objects.indexOf(name), s = [0,0,0];
  let count = 0;
  for (let i = 0; i < objectId.length; i++) {
    if (objectId[i] !== id || coverage[i] < .9) continue;
    for (let c = 0; c < 3; c++) s[c] += frame.rgb[i*3+c];
    count++;
  }
  assert(count > 5, name + ' has visible samples');
  return s.map(value => value / count);
}

test('sky and ground bounce follow world normals and can be changed independently', () => {
  const world = bounceFixture();
  const options = { w:97, h:59, px:1, ortho:true, passes:['objectId','coverage'] };
  const skyBounce = { color:'#3264ff', intensity:.48 }, groundBounce = { color:'#ff9933', intensity:.48 };
  world.liveSun = { ambient:.16, intensity:0, skyBounce, groundBounce };

  for (const style of [{ raw:true }, { coverageAware:true }]) {
    const optionsForStyle = { ...options, ...style };
    const both = ink.render(world, optionsForStyle);
    const top = colorAt(both, 'top'), under = colorAt(both, 'underside'), wall = colorAt(both, 'wall');
    assert(top[2] > top[0] + 30, 'upper fill is blue');
    assert(under[0] > under[2] + 30, 'lower fill is warm');
    assert(wall[0] > top[0] + 20 && wall[2] > under[2] + 20, 'vertical surface mixes both lights');
    const upperOnly = ink.render(world, { ...optionsForStyle, liveSun:{ groundBounce:false } });
    assert(colorAt(upperOnly, 'top').every((v, c) => Math.abs(v - top[c]) < .2));
    assert(colorAt(upperOnly, 'underside')[0] < under[0] - 20);
    const lowerOnly = ink.render(world, { ...optionsForStyle, liveSun:{ skyBounce:'off' } });
    assert(colorAt(lowerOnly, 'underside').every((v, c) => Math.abs(v - under[c]) < .2));
    assert(colorAt(lowerOnly, 'top')[2] < top[2] - 20);
  }

  const raw = { ...options, raw:true };
  const neutral = ink.render(world, { ...raw, liveSun:{ skyBounce:false, groundBounce:false } });
  const zero = ink.render(world, { ...raw, liveSun:{ skyBounce:{ intensity:0 }, groundBounce:{ intensity:0 } } });
  assert.deepEqual(zero.rgb, neutral.rgb);
  const animated = { ...world, liveSun:{ ...world.liveSun, groundBounce: t => t < 1 ? 'sand' : 'water' } };
  assert(colorAt(ink.render(animated, { ...raw, t:0 }), 'underside')[0] >
    colorAt(ink.render(animated, { ...raw, t:1 }), 'underside')[0] + 30);
  assert.throws(() => ink.render(world, { ...raw, liveSun:{ skyBounce:'unknown' } }), /Bounce color/);
  assert.throws(() => ink.render(world, { ...raw, liveSun:{ groundBounce:{ intensity:-1 } } }), /Bounce intensity/);
});

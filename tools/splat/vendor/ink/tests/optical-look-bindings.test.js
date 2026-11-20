const assert = require('node:assert/strict');
const test = require('node:test');
const studio = require('../index.js');
const { KIT: K, makeBuilder, makeSculpt, RenderStages, SceneOptics } = studio.load();
const { traceMedia } = require('../cli/scene-optics.js');
const { waterBodies: water } = K.procedural;

const tint = (name, offset) => ({ name, steps: [{ type: 'channelMix', matrix: [[0, 0, 0], [0, 0, 0], [0, 0, 0]], offset }] });
const optics = { tint: [0, 0, 0], extinction: [.7, .7, .7] };
const origin = [.5, -.5, 3], direction = [0, 0, -1];
const close = (a, b) => assert(Math.abs(a - b) < 1e-6, a + ' differs from ' + b);
function body(style = optics) {
  return water.create({ id: 'basin', bounds: { min: [0, -2], max: [1, 2] }, resolution: [1, 4],
    optics: style, sample: (_x, z) => z < -1 ? null : { bed: -1, surface: 0 } });
}

test('bound tint accumulates on clipped water columns and leaves air pockets dry', () => {
  const field = water.scene([body()], { airPockets: [{ id: 'pocket', bounds: { min: [0, -1, 0], max: [1, 0, .5] } }] });
  const bindings = RenderStages.optics([{ select: { medium: 'basin' }, stack: tint('Red water', [1, 0, 0]) }]);
  const mapped = field.mapColors((medium, mediumKind) => bindings.transform({ medium, mediumKind }));
  assert.deepEqual(mapped.mediumAt(.5, -.5, .25), field.mediumAt(.5, -.5, .25));
  const rays = mapped.raySegments(origin, direction, 10);
  assert.deepEqual(rays.map(([a, b]) => [a, b]), [[1, 2], [2, 2.5], [3, 4]]);
  for (const [stop, wet] of [[.8, 0], [1.6, .6], [2.8, 1.5], [4.8, 2.5]]) {
    const result = traceMedia([], rays, origin, direction, stop, new Float64Array(6), [], {});
    close(result[0], 1 - Math.exp(-.7 * wet));
    close(result[3], Math.exp(-.7 * wet));
    close(result[1], 0);
  }
});

test('headless water integrates behind a near object and to the actual depth of a submerged object', () => {
  const view = { w: 55, h: 55, px: 1, ortho: true }, center = (27 * 55 + 27) * 3;
  function draw(z) {
    const B = makeBuilder(7, [0, 0xffffff]);
    B.disc(.5, -.5, z, [0, 0, 1], .35, .02, B.P[1], 3);
    return studio.render(B.finish({ cam: { target: [.5, -.5, 0], dist: 6, yaw: 0, pitch: 0 },
      water: water.scene([body()]), look: { optics: [{ select: { medium: 'basin' }, stack: tint('Teal', [0, 1, .5]) }] }
    }), view).rgb.slice(center, center + 3);
  }
  const front = draw(2.5), near = draw(1.4), deep = draw(-.8);
  assert(front[0] > 246);
  assert(front[0] > near[0] && near[0] > deep[0]);
  assert(deep[1] > 248 && deep[2] > deep[0] + 100);
});

test('reflections carry the signed object grade and apply a capture look only at the mirror', () => {
  function render(optical, reflections = true) {
    const B = makeBuilder(6, [0x141b27, 0x1d2a38, 0x99a1a6]);
    const S = makeSculpt(B), plane = K.reflection.plane({ id: 'mirror' });
    S.box([0, -.04, 0], [1.6, .04, 1.5], K.reflection.material({ r: [1], a: 1 }, plane.id, { f0: 1 }), { res: .075 });
    S.box([0, .52, -.6], [.26, .32, .09], { r: [2], em: true }, { res: .049, target: { surface: 'sign' } });
    S.bake();
    return studio.render(B.finish({
      cam: { target: [0, .25, 0], dist: 5.6, yaw: 0, pitch: .63 }, reflections: [plane],
      look: { paletteConstraints: { targets: [{ select: { surface: 'sign' }, palette: ['#ff0000'] }] },
        ...(optical && { optics: [{ select: { medium: 'mirror', mediumKind: 'reflection' }, stack: tint('Blue capture', [0, 0, 1]) }] }) }
    }), { w: 101, h: 101, px: 1, ortho: true, reflections }).rgb;
  }
  const base = render(false, false), reflected = render(false), graded = render(true);
  assert.deepEqual(render(true, false), base);
  let redMirror = 0, blueMirror = 0;
  for (let i = 0; i < base.length; i += 3) {
    if (base[i] > 200 && base[i + 1] < 10) assert.equal(graded[i], base[i]);
    if (base[i] < 100 && reflected[i] > 180 && reflected[i + 2] < 40) redMirror++;
    if (reflected[i] > 180 && graded[i + 2] > 180 && graded[i] < 35) blueMirror++;
  }
  assert(redMirror > 20 && blueMirror > 20);
});

test('named glass and fog bindings enter their respective optical paths', () => {
  const B = makeBuilder(5, [0, 0xffffff, 0x444444]);
  B.disc(0, 0, 0, [0, 0, 1], .8, .02, B.P[1], 3);
  B.disc(0, 0, .3, [0, 0, 1], .5, .02, B.P[2], .4, { gl: true, nd: true });
  B.describeSplats(1, 2, { object: 'pane' });
  const pack = { format: 'ink-studio/asset-pack', id: 'optics', title: 'Optics', version: 1, revision: 1,
    looks: [{ id: 'optics/rose', label: 'Rose', stack: tint('Rose', [1, 0, 0]) }] };
  const look = K.authoring.looks.scene({ optics: [
    { select: { medium: 'pane', mediumKind: 'glass' }, asset: 'optics/rose' },
    { select: { medium: 'mist' }, stack: tint('Green mist', [0, 1, 0]) }
  ] }, K.authoring.assetPacks.create({ packs: [pack] }));
  const scene = B.finish({ cam: { target: [0, 0, 0], dist: 4, yaw: 0, pitch: 0 }, refract: 0, look,
    atmosphere: [SceneOptics.sphere({ id: 'mist', at: [0, 0, 1], radius: .28, density: 1, color: '#000000' })] });
  const camera = { w: 55, h: 55, px: 1, ortho: true }, center = (27 * 55 + 27) * 3;
  const pane = studio.render(scene, { ...camera, atmosphere: false }).rgb.slice(center, center + 3);
  assert.deepEqual(Array.from(pane), [253, 151, 151]);
  const fog = studio.render(scene, camera).rgb.slice(center, center + 3);
  assert(fog[0] < pane[0] && fog[1] > pane[1] && fog[2] < pane[2]);
  const probe = K.world.query.fromScene(scene).probe('look/output', { medium: 'pane' }, { stage: 'optics', rgb: [0, 0, 0] });
  assert.deepEqual(probe.value.targets[0].rgb, [1, 0, 0]);
});

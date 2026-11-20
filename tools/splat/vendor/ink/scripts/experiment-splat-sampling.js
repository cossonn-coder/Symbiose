/* Compare two independent sampling changes using the bundled scenes and a known overlap. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { performance } = require('node:perf_hooks');
const studio = require('../index.js');
const { render, grid, upscale } = require('../cli/render.js');
const { flicker } = require('../cli/critic.js');
const PNG = require('../cli/png.js');
const kit = studio.load();

function motion(scene, time, mode) {
  const world = scene.build(scene.seed);
  if (world.anim) world.anim.update(1 / 60, time);
  if (world.pix) {
    const { pixel } = kit.KIT;
    Object.assign(world, { pixTex: pixel.evaluators(world), pixCell: pixel.CELL, pixView: pixel.VIEW,
      pixUnfold: pixel.unfold, pixAnchors: pixel.anchors });
  }
  const view = { w: 384, h: 264, px: 3, t: time };
  function frames(filter) {
    const photos = [];
    const elapsed = [];
    for (let i = 0; i < 12; i++) {
      const start = performance.now();
      photos.push(render(world, {
        ...view, splatFilter: filter,
        ...(mode === 'orbit' ? { yaw: world.cam.yaw + i * .004 } :
          { target: world.cam.target.map((v, j) => v + i * [.02, 0, .01][j]) })
      }));
      elapsed.push(performance.now() - start);
    }
    elapsed.sort((a, b) => a - b);
    return { photos, ms: elapsed[elapsed.length >> 1], flicker: flicker(photos, { bg: world.pal[0] }) };
  }
  frames(); // Warm the painter on the same camera sequence.
  const base = frames(), footprint = frames('footprint');
  return { scene: scene.id, mode, base: { ms: base.ms, flicker: base.flicker },
    footprint: { ms: footprint.ms, flicker: footprint.flicker },
    render: [base.photos[0], footprint.photos[0]] };
}

function crossedPlanes() {
  const b = kit.makeBuilder(8, [0x111722, 0xf07f64, 0x7cbdea]);
  const normal = slope => kit.KIT.V.norm([-slope, 0, 1]);
  // z = x + 0.03 must be in front on the right. z = -x is in front on the left.
  b.disc(0, 0, .03, normal(1), .62, .009, b.P[1], 2.9);
  b.disc(0, 0, 0, normal(-1), .62, .009, b.P[2], 2.9);
  const world = b.finish({ cam: { target: [0, 0, 0], dist: 4, pitch: 0, yaw: 0 } });
  const w = 80, h = 60, fragments = Array.from({ length: w * h }, () => []);
  render(world, { w, h, px: 1, ortho: true, raw: true,
    fragmentProbe(p, id, centerDepth, surfaceDepth, red, green, blue, opacity) {
      fragments[p].push({ id, centerDepth, surfaceDepth, color: [red, green, blue], opacity });
    }
  });
  function blend(depth) {
    let right = 0, wrong = 0;
    const rgb = new Uint8Array(w * h * 3);
    for (let p = 0; p < w * h; p++) {
      const layers = fragments[p].slice().sort((a, b) => b[depth] - a[depth] || a.id - b.id);
      let c = [0x11 / 255, 0x17 / 255, 0x22 / 255];
      for (const { color, opacity } of layers) c = c.map((value, i) => (1 - opacity) * value + opacity * color[i]);
      const y = h - 1 - Math.floor(p / w), x = p % w;
      for (let i = 0; i < 3; i++) rgb[(y * w + x) * 3 + i] = Math.round(c[i] * 255);
      if (layers.length === 2 && layers.every(layer => layer.opacity > .75) && Math.abs(x - w / 2) > 2) {
        const known = x >= w / 2 ? 0 : 1;
        if (layers.at(-1).id === known) right++;
        else wrong++;
      }
    }
    return { w, h, rgb, right, wrong };
  }
  const center = blend('centerDepth'), local = blend('surfaceDepth');
  const rendered = render(world, { w, h, px: 1, ortho: true, raw: true, splatOrder: 'surface' });
  assert(local.wrong === 0 && center.wrong > 0);
  assert(local.rgb.every((value, i) => Math.abs(value - rendered.rgb[i]) <= 1));
  return {
    fixture: 'crossed planar splats', centerCorrect: center.right, centerWrong: center.wrong,
    localCorrect: local.right, localWrong: local.wrong, render: [center, local]
  };
}

const watcher = kit.SCENES.find(scene => scene.id === 'watcher');
const beacon = require('../examples/beacon-pool.js')(kit);
const results = [motion(watcher, 2.6, 'orbit'), motion(watcher, 2.6, 'pan'), motion(beacon, 1.2, 'orbit')];
const crossing = crossedPlanes();
const record = entry => Object.fromEntries(Object.entries(entry).filter(([key]) => key !== 'render'));
const report = { footprint: results.map(record), ordering: record(crossing) };
console.log(JSON.stringify(report, null, 2));
const out = process.argv[2];
if (out) {
  fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(path.join(out, 'splat-experiment.json'), JSON.stringify(report, null, 2) + '\n');
  const sheet = grid(crossing.render.map(frame => upscale(frame, 4)), 2);
  PNG.write(path.join(out, '08-local-splat-order.png'), sheet.w, sheet.h, sheet.rgb);
  const compare = grid(results.flatMap(row => row.render).map(frame => upscale(frame, 2)), 2);
  PNG.write(path.join(out, '09-splat-footprint.png'), compare.w, compare.h, compare.rgb);
}

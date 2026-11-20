const fs = require('node:fs');
const path = require('node:path');
const studio = require('..').load();
const gallery = require('../examples/surface-gallery.js');
const { render, upscale } = require('../cli/render.js');
const PNG = require('../cli/png.js');

const dir = path.resolve(process.argv[2] || 'studio/out/surface-gallery');
fs.mkdirSync(dir, { recursive: true });
function save(filename, world, options) {
  const image = render(world, options);
  const pixels = upscale(image, image.px);
  PNG.write(path.join(dir, filename), pixels.w, pixels.h, pixels.rgb);
}

const demo = gallery(studio);
const stillLife = demo.build(demo.seed);
save('after-the-rain.png', stillLife, { w: 1236, h: 816, t: 0.6 });
save('after-the-rain-turned.png', stillLife, { w: 1236, h: 816, t: 0.6, yaw: 0.31, pitch: 0.33 });
for (const [id, direction, roughness] of [
  ['uniform', 'y', [0.17, 0.17]],
  ['vertical', 'y', [0.065, 0.63]],
  ['horizontal', 'x', [0.065, 0.63]]
]) {
  const sample = gallery.swatch(studio, 'brushed-steel', 'slate', 'orb', {
    direction,
    layers: { brush: { roughness, color: '#ffffff' } }
  });
  save('roughness-' + id + '.png', sample, { w: 272, h: 210, px: 2, pitch: 0.26, yaw: 0.23 });
}
for (const group of gallery.groups) {
  for (const [name, ramp, shape] of group.swatches) {
    const world = gallery.swatch(studio, name, ramp, shape);
    const flat = shape === 'water' || shape === 'cobbles';
    const viewport = { w: 224, h: 176, px: 2, t: 0.6 };
    save(name + '-a.png', world, { ...viewport, yaw: -0.39, pitch: flat ? 0.66 : 0.29 });
    save(name + '-b.png', world, { ...viewport, yaw: 0.67, pitch: flat ? 0.13 : 0.2 });
  }
  console.log('Rendered ' + group.swatches.length + ' materials for ' + group.name);
}
fs.writeFileSync(path.join(dir, 'swatches.json'), JSON.stringify(gallery.groups, null, 2) + '\n');
console.log(dir);

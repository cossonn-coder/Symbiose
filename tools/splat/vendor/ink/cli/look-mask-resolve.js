const PixelLook = require('../src/pixel-look.js');
const { sampleFrames } = require('./art-passes.js');
const { surfacePoint } = require('./scene-optics.js');

function createMaskResolve(world, grid, overlay, policies, grade, visit) {
  const { w, h, time, x, y, z, depth, rayAt, span } = grid;
  const sample = sampleFrames(world, time), frames = new Map();
  const scene = Array.from(world.pal, color => [color >> 16, color >> 8 & 255, color & 255].map(n => n / 255));
  const weights = new Float32Array(w * h), colors = new Uint32Array(w * h);
  function record(pixel, r, g, b, dx, dy) {
    const policy = policies[overlay.slots[pixel] - 1];
    if (!policy) return;
    const i = overlay.owners[pixel];
    if (!frames.has(i)) frames.set(i, sample(i));
    const frame = frames.get(i), px = pixel % w, py = Math.floor(pixel / w);
    const cx = x[i], cy = y[i], cz = z[i];
    const point = frame.normal ? surfacePoint(rayAt(px + .5, py + .5), frame.normal, cx, cy, cz, -depth[i], span) : [cx, cy, cz];
    const offset = frame.localOffset(point[0] - cx, point[1] - cy, point[2] - cz);
    const position = [frame.rest[0] + offset[0], frame.rest[1] + offset[1], frame.rest[2] + offset[2]];
    const amount = policy.mask({ position, worldPosition: point, normal: frame.normal, time });
    if (!amount) return;
    if (visit) visit(pixel, policy, amount);
    const out = (h - 1 - py) * w + px;
    weights[out] = amount;
    colors[out] = policy.packed[PixelLook.paletteIndex(policy, [r, g, b], dx, dy, { grade, scene })];
  }
  return { record, output: { colors, weights } };
}

function applyMasks(rgb, overlay) {
  if (!overlay) return;
  const { weights, colors } = overlay;
  for (let i = 0; i < weights.length; i++) {
    const amount = weights[i];
    if (!amount) continue;
    const pixel = i * 3, packed = colors[i];
    for (let k = 0; k < 3; k++) {
      const color = packed >> ((2 - k) * 8) & 255;
      rgb[pixel + k] = Math.round(rgb[pixel + k] * (1 - amount) + color * amount);
    }
  }
}

module.exports = { createMaskResolve, applyMasks };

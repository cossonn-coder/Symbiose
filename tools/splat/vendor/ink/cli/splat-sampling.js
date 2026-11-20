const clamp = (value, lo, hi) => Math.max(lo, Math.min(hi, value));
const ContributionRules = require('../src/contribution-rules.js');

function footprint(dx, dy, k0, k1, k2, gain, hard, edge) {
  let total = 0;
  for (const v of [-.25, .25]) for (const u of [-.25, .25]) {
    const x = dx + u, y = dy + v;
    total += ContributionRules.alpha(-.5 * (k0 * x * x + k2 * y * y) - k1 * x * y, gain, hard, edge);
  }
  return total * .25;
}

function sampledDepth(ray, normal, center, depth, reach) {
  if (!normal) return depth;
  const { direction, origin, axial } = ray;
  const facing = normal[0] * direction[0] + normal[1] * direction[1] + normal[2] * direction[2];
  if (Math.abs(facing) < .025) return depth;
  const distance = (normal[0] * (center[0] - origin[0]) + normal[1] * (center[1] - origin[1]) +
    normal[2] * (center[2] - origin[2])) / facing;
  return distance > 0 ? depth + clamp(axial * distance - depth, -reach, reach) : depth;
}
module.exports = { footprint, sampledDepth };

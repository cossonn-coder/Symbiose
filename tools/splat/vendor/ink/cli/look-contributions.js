const PixelLook = require('../src/pixel-look.js');

function contributionLook(palettes, policies, targets, targetOffset, fallback, scene, grade) {
  const slot = (i, layer) => targets?.[i] ? targetOffset + targets[i] : layer || fallback;
  function shade(i, layer, rgb, x, y, sample, dither, visit) {
    const id = slot(i, layer);
    if (!id) return rgb;
    const policy = policies?.[id - 1];
    if (!policy) return palettes[id - 1][PixelLook.nearest(rgb, palettes[id - 1], false)];
    const amount = policy.mask ? sample ? policy.mask(sample) : 0 : 1;
    if (amount && visit) visit(policy, policy.mask ? amount : null, amount);
    const options = { scene, grade, useDither: dither };
    const index = plan => PixelLook.paletteIndex(plan, rgb, x, y, options);
    if (amount === 1) return policy.swatches[index(policy)];

    // A soft mask reveals the underlying material or default look in the same fragment.
    const under = [layer, fallback].find(id => id && !policies?.[id - 1]?.mask);
    const underlying = policies?.[under - 1];
    if (!amount && underlying && visit) visit(underlying, null, 1);
    const base = underlying ? underlying.swatches[index(underlying)] : under ?
      palettes[under - 1][PixelLook.nearest(rgb, palettes[under - 1], false)] : rgb;
    if (!amount) return base;
    return policy.swatches[index(policy)].map((value, channel) => base[channel] + (value - base[channel]) * amount);
  }
  return { shade, applies: slot, masked: (i, layer) => Boolean(policies?.[slot(i, layer) - 1]?.mask) };
}

function contributionLayers(col, alpha, w, h, patterned, bend) {
  // Pattern RGB and its surviving alpha. Later fragments attenuate only this contribution.
  const pattern = patterned ? new Float32Array(w * h * 4) : null;
  // Captured backdrop RGB, transmission, backdrop alpha, pattern coverage and pane depth.
  const REAR = 7;
  let backdrop;

  function before(p, r, g, b, a, winner, glass, depth) {
    const ia = 1 - a, q = p * 4, j = p * REAR, k = p * 3;
    if (glass && bend) {
      backdrop ??= new Float32Array(w * h * REAR);
      if (!backdrop[j + 3]) {
        for (let c = 0; c < 3; c++) backdrop[j + c] = col[k + c];
        backdrop[j + 3] = 1;
        backdrop[j + 4] = alpha?.[p] ?? 1;
        backdrop[j + 5] = pattern?.[q + 3] ?? 0;
        backdrop[j + 6] = depth;
      }
    }
    if (backdrop) {
      backdrop[j + 3] *= ia;
      if (winner) backdrop[j + 5] = 0;
    }
    if (!pattern) return;
    if (winner) {
      pattern[q] = r;
      pattern[q + 1] = g;
      pattern[q + 2] = b;
      pattern[q + 3] = a;
    } else pattern[q + 3] *= ia;
  }

  function replacePattern(p, rgb) {
    const q = p * 4, j = p * REAR, k = p * 3;
    for (let c = 0; c < 3; c++) {
      const change = rgb[c] - pattern[q + c];
      col[k + c] += change * pattern[q + 3];
      if (backdrop) backdrop[j + c] += change * backdrop[j + 5];
    }
  }

  function refract(glass, depth) {
    if (!backdrop) return;
    const at = (x, y) => Math.max(0, Math.min(h - 1, y)) * w + Math.max(0, Math.min(w - 1, x));
    for (let p = 0; p < w * h; p++) {
      const j = p * REAR, weight = backdrop[j + 3];
      if (weight < 1e-6 || glass[p] < 1e-6) continue;
      const x = p % w, y = Math.floor(p / w);
      const dx = Math.round((glass[at(x + 1, y)] - glass[at(x - 1, y)]) * bend);
      const dy = Math.round((glass[at(x, y + 1)] - glass[at(x, y - 1)]) * bend);
      const source = at(x + dx, y + dy);
      if (source === p) continue;
      const sourceRear = backdrop[source * REAR + 3] > 0;
      if (!sourceRear && depth[source] < backdrop[j + 6]) continue;
      const from = source * (sourceRear ? REAR : 3), colors = sourceRear ? backdrop : col;
      for (let c = 0; c < 3; c++) col[p * 3 + c] += (colors[from + c] - backdrop[j + c]) * weight;
      if (alpha) {
        const coverage = sourceRear ? backdrop[from + 4] : alpha[source];
        alpha[p] += (coverage - backdrop[j + 4]) * weight;
      }
    }
  }

  return { before, replacePattern, refract, weight: pixel => pattern?.[pixel * 4 + 3] || 0 };
}

module.exports = { contributionLook, contributionLayers };

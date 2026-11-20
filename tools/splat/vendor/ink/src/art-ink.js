/* Art-pixel line classification and palettes. The inputs are top-down render passes. */
const ArtInk = (() => {
  const defaults = Object.freeze({
    silhouette: { steps: 1, litSteps: 0 },
    crease: { steps: 1, litSteps: 0 },
    boundary: { steps: 1, litSteps: 0 }
  });
  const kinds = Object.keys(defaults);
  const luma = (r, g, b) => .30 * r + .55 * g + .15 * b;
  const clamp = (value, lo, hi) => Math.max(lo, Math.min(hi, value));

  function packed(value, palette) {
    if (typeof value === 'string' && /^#[0-9a-f]{6}$/i.test(value)) return Number.parseInt(value.slice(1), 16);
    if (Number.isSafeInteger(value) && value >= 0 && value < palette.length) return palette[value];
    throw new TypeError('Ink colors must be #rrggbb or scene palette indices');
  }

  function colors(values, palette) {
    if (!Array.isArray(values) || !values.length || values.length > 64)
      throw new RangeError('Ink palettes need between one and 64 colors');
    return values.map(value => packed(value, palette));
  }

  function lineRule(rule, inherited, palette) {
    if (rule === false) return null;
    if (rule === undefined) return inherited;
    if (rule !== true && (!rule || typeof rule !== 'object' || Array.isArray(rule)))
      throw new TypeError('Ink line rules must be true, false, or an object');
    const { color, highlight, shadow, steps = inherited?.steps ?? 1, litSteps = inherited?.litSteps ?? 0 } =
      rule === true ? {} : rule;
    if (![steps, litSteps].every(Number.isSafeInteger) || Math.abs(steps) > 64 || Math.abs(litSteps) > 64)
      throw new RangeError('Ink steps must be integers between -64 and 64');
    return {
      steps, litSteps,
      color: color === undefined ? inherited?.color : packed(color, palette),
      highlight: highlight === undefined ? inherited?.highlight : packed(highlight, palette),
      shadow: shadow === undefined ? inherited?.shadow : packed(shadow, palette)
    };
  }

  function prepare(definition, palette) {
    if (!definition) return null;
    const settings = definition === true ? {} : definition;
    if (typeof settings !== 'object' || Array.isArray(settings)) throw new TypeError('Expected an ink settings object');
    const {
      depthGap = .09, creaseCosine = .72, litAt = .38, suppressSameMaterial = true,
      light = [-.5, .8, .45], emissionThreshold = .25, fogThreshold = .25, materials = {}, reserved = {}
    } = settings;
    if (!Number.isFinite(depthGap) || depthGap <= 0 ||
        ![creaseCosine, litAt].every(value => Number.isFinite(value) && Math.abs(value) <= 1) ||
        ![emissionThreshold, fogThreshold].every(v => Number.isFinite(v) && v >= 0 && v <= 1) ||
        !Array.isArray(light) || light.length !== 3 || !light.every(Number.isFinite) || !Math.hypot(...light) ||
        typeof suppressSameMaterial !== 'boolean')
      throw new RangeError('Invalid selective ink thresholds or light direction');
    const length = Math.hypot(...light);
    const ramps = new Map(Object.entries(reserved).map(([key, value]) => [key, colors(value, palette)]));
    const base = Object.fromEntries(kinds.map(kind => [kind, lineRule(settings[kind], defaults[kind], palette)]));
    const styles = new Map(Object.entries(materials).map(([name, style]) => {
      if (!style || typeof style !== 'object' || Array.isArray(style))
        throw new TypeError('Material ink style must be an object');
      if (style.palette !== undefined && !ramps.has(style.palette)) throw new RangeError('Unknown reserved palette ' + style.palette);
      const rules = Object.fromEntries(kinds.map(kind => [kind, lineRule(style[kind], base[kind], palette)]));
      return [name, { ...rules, ramp: style.ramp === undefined ? null : colors(style.ramp, palette), palette: style.palette }];
    }));
    return { base, styles, ramps, depthGap, creaseCosine, litAt, suppressSameMaterial,
      light: light.map(value => value / length), emissionThreshold, fogThreshold };
  }

  function closest(ramp, r, g, b) {
    let best = 0, score = Infinity;
    for (let i = 0; i < ramp.length; i++) {
      const color = ramp[i], dr = r - (color >> 16), dg = g - ((color >> 8) & 255), db = b - (color & 255);
      const candidate = .30 * dr * dr + .55 * dg * dg + .15 * db * db;
      if (candidate < score) {
        best = i;
        score = candidate;
      }
    }
    return best;
  }

  function apply(frame, passes, settings, palette, signals) {
    const { w, h, rgb } = frame;
    const { depth, normal, objectId, materialId, materials, emission, splatId } = passes;
    const mask = new Uint8Array(w * h);
    const { base, styles, ramps, depthGap, creaseCosine, litAt, light, suppressSameMaterial } = settings;
    const byId = materials.map((label, id) => styles.get(String(label ?? id)) || base);
    const source = rgb.slice();
    const outputPalette = Array.from(frame.palette || palette);
    const known = new Map(outputPalette.map((color, index) => [color, index]));
    const counts = new Uint32Array(outputPalette.length);
    const additions = [];

    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const p = y * w + x, q = p * 3;
      const id = objectId[p], material = materialId[p], style = byId[material] || base;
      let hasSilhouette = false, hasBoundary = false, hasCrease = false;
      if (Number.isFinite(depth[p])) {
        for (let i = 0; i < 4; i++) {
          const z = i === 0 ? (x > 0 ? p - 1 : -1) : i === 1 ? (x + 1 < w ? p + 1 : -1) :
            i === 2 ? (y > 0 ? p - w : -1) : (y + 1 < h ? p + w : -1);
          if (z < 0 || !Number.isFinite(depth[z])) {
            hasSilhouette = true;
            continue;
          }
          const dz = depth[z] - depth[p], sameMaterial = material > 0 && materialId[z] === material;
          const split = (id !== objectId[z] && (id || objectId[z])) || (material !== materialId[z] && (material || materialId[z]));
          if (split) {
            if ((!suppressSameMaterial || !sameMaterial) &&
                (dz > depthGap || (dz >= -depthGap && p < z))) hasBoundary = true;
            continue;
          }
          if (splatId[p] === splatId[z]) continue;
          const a = z * 3;
          const dot = normal[q] * normal[a] + normal[q + 1] * normal[a + 1] + normal[q + 2] * normal[a + 2];
          const aLength = Math.abs(normal[a]) + Math.abs(normal[a + 1]) + Math.abs(normal[a + 2]);
          const pLength = Math.abs(normal[q]) + Math.abs(normal[q + 1]) + Math.abs(normal[q + 2]);
          if (dz > depthGap || (Math.abs(dz) <= depthGap && p < z && aLength && pLength && dot < creaseCosine)) hasCrease = true;
        }
      }
      const r = source[q], g = source[q + 1], b = source[q + 2];
      let color = (r << 16) | (g << 8) | b;
      const emit = Math.max(emission[q], emission[q + 1], emission[q + 2]);
      const signal = signals?.[p] > settings.fogThreshold ? 'fog' : null;
      const emitting = emit >= settings.emissionThreshold && emit > 0;
      const reserved = (emitting && ramps.get('emission')) || ramps.get(signal || style.palette);
      if (reserved) {
        color = reserved[closest(reserved, r, g, b)];
        mask[p] = 4;
      } else {
        const type = style.silhouette && hasSilhouette ? 'silhouette' :
          style.boundary && hasBoundary ? 'boundary' : style.crease && hasCrease ? 'crease' : null;
        if (type) {
          const rule = style[type];
          const lit = (normal[q] || normal[q + 1] || normal[q + 2]) ?
            normal[q] * light[0] + normal[q + 1] * light[1] + normal[q + 2] * light[2] >= litAt : luma(r, g, b) > 160;
          const explicit = (lit ? rule.highlight : rule.shadow) ?? rule.color;
          const steps = lit ? rule.litSteps : rule.steps;
          if (explicit !== undefined) color = explicit;
          else if (steps) {
            const ramp = style.ramp;
            if (ramp) color = ramp[clamp(closest(ramp, r, g, b) - steps, 0, ramp.length - 1)];
            else {
              const gain = Math.pow(.73, steps);
              color = palette[closest(palette, r * gain, g * gain, b * gain)];
            }
          }
          if (color !== ((r << 16) | (g << 8) | b)) mask[p] = type === 'silhouette' ? 1 : type === 'crease' ? 2 : 3;
        }
      }
      rgb[q] = color >> 16;
      rgb[q + 1] = (color >> 8) & 255;
      rgb[q + 2] = color & 255;
      let index = known.get(color);
      if (index === undefined) {
        index = outputPalette.length;
        known.set(color, index);
        outputPalette.push(color);
        additions.push(0);
      }
      if (index < counts.length) counts[index]++;
      else additions[index - counts.length]++;
    }
    const use = new Uint32Array(outputPalette.length);
    use.set(counts);
    use.set(additions, counts.length);
    return { ...frame, palette: outputPalette, use, inkMask: mask };
  }

  const channels = Object.freeze(['depth', 'normal', 'objectId', 'materialId', 'emission', 'splatId']);
  return Object.freeze({ prepare, apply, channels });
})();
if (typeof module !== 'undefined') module.exports = ArtInk;

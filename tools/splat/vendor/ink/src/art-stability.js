/* Optional camera and sampling controls in native art pixels. */
const ArtStability = (() => {
  const spaces = ['screen', 'world', 'object'];
  const origin = [0, 0, 0];
  const vector = value => Array.isArray(value) && value.length === 3 && Array.from(value).every(Number.isFinite);

  function pattern({ dither = 'screen', spacing = .08, origin: point = origin }) {
    if (!spaces.includes(dither) || !Number.isFinite(spacing) || spacing <= 0 || !vector(point))
      throw new RangeError('Invalid dither space, spacing or origin');
    return { dither, spacing, origin: point.slice() };
  }

  function prepare(definition, override) {
    if (override === false || (override === undefined && !definition)) return null;
    function read(value) {
      if (value === true) return { snap: true };
      if (value === undefined || value === false || value === null) return {};
      if (typeof value !== 'object' || Array.isArray(value)) throw new TypeError('Expected pixel stability settings');
      return value;
    }
    const settings = { ...read(definition), ...read(override) };
    const { snap = false, anchor = origin, resolve = 'native', threshold = .4, protect = [], targets = [] } = settings;
    if (typeof snap !== 'boolean' || !vector(anchor) ||
        !['native', 'coverage', 'clusters'].includes(resolve) || !Number.isFinite(threshold) || threshold <= 0 || threshold > 1 ||
        !Array.isArray(protect) || !Array.from(protect).every(value => typeof value === 'string' || Number.isSafeInteger(value)) ||
        !Array.isArray(targets) || targets.length > 64)
      throw new RangeError('Invalid pixel stability settings');
    const main = pattern(settings);
    const named = value => typeof value === 'string' && value.trim() || Number.isSafeInteger(value);
    const rules = Array.from(targets, row => {
      if (!row || Object.getPrototypeOf(row) !== Object.prototype ||
          Object.keys(row).some(key => !['object', 'material', 'dither', 'spacing', 'origin'].includes(key)))
        throw new TypeError('Invalid dither target');
      const { object, material } = row;
      if (object === undefined && material === undefined ||
          object !== undefined && !named(object) || material !== undefined && !named(material))
        throw new TypeError('A dither target needs an object or material name');
      return { ...pattern({ ...main, ...row }), object, material };
    });
    const anchorSpaces = new Set([main.dither, ...rules.map(rule => rule.dither)]);
    anchorSpaces.delete('screen');
    return { ...main, snap, anchor: anchor.slice(), resolve, threshold, protect: new Set(protect.map(String)), rules, anchorSpaces };
  }

  function snapView(view, pixelsPerUnit, anchor) {
    const result = view.slice();
    for (let row = 0; row < 2; row++) {
      const position = anchor[0] * view[row] + anchor[1] * view[4 + row] + anchor[2] * view[8 + row] + view[12 + row];
      const snapped = Math.round(position * pixelsPerUnit) / pixelsPerUnit;
      result[row + 12] += snapped - position;
    }
    return result;
  }

  const modulo = (n, size) => ((n % size) + size) % size;
  function matching(settings, object, material) {
    for (let i = settings.rules.length - 1; i >= 0; i--) {
      const rule = settings.rules[i];
      if ((rule.object === undefined || rule.object === object) &&
          (rule.material === undefined || rule.material === material)) return rule;
    }
    return settings;
  }

  function coordinates(rule, point, x, y) {
    if (!point || rule.dither === 'screen') return [x, y];
    const cell = i => Math.floor((point[i] - rule.origin[i]) / rule.spacing + 1e-5);
    const ix = cell(0), iy = cell(1), iz = cell(2);
    if (![ix, iy, iz].every(Number.isFinite)) return [x, y];
    // Mixing the three integer axes lets any axis-aligned surface use both pattern dimensions.
    return [ix + 3 * iy + 2 * iz, 2 * ix + iy + 3 * iz];
  }

  function ditherCoordinates(settings, passes, p, x, y) {
    if (!settings?.anchorSpaces.size || !passes || !(passes.depth ? Number.isFinite(passes.depth[p]) : passes.splatId?.[p]))
      return [x, y];
    const object = passes.objects?.[passes.objectId?.[p]], material = passes.materials?.[passes.materialId?.[p]];
    const rule = matching(settings, object, material);
    if (rule.dither === 'screen') return [x, y];
    const buffer = rule.dither === 'object' ? passes.objectPosition : passes.position;
    const point = (rule.dither === 'object' && passes.ditherRest?.get(p)) || buffer?.subarray(p * 3, p * 3 + 3);
    return coordinates(rule, point, x, y);
  }

  function protectedPixel(settings, passes, p) {
    if (!settings || !passes) return false;
    const object = passes.objectId?.[p], material = passes.materialId?.[p];
    return (object > 0 && settings.protect.has(String(passes.objects[object] ?? object))) ||
      (material > 0 && settings.protect.has(String(passes.materials[material] ?? material)));
  }

  function resolve(native, samples, settings, palette, pixelLook, dither, { local, grade, tone } = {}) {
    const { w, h, color, passes } = native, sw = samples.w;
    const rgb = new Uint8Array(w * h * 3), use = new Uint32Array(local?.output.packed.length ?? palette.length);
    const coverage = new Float32Array(w * h), detail = new Uint8Array(w * h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const p = y * w + x, s = (y * sw + x) * 2;
      coverage[p] = (samples.passes.coverage[s] + samples.passes.coverage[s + 1] +
        samples.passes.coverage[s + sw] + samples.passes.coverage[s + sw + 1]) * .25;
      const n = p * 3, light = passes.emission;
      detail[p] = Boolean(native.detail?.[p] || passes.protected?.[p] || protectedPixel(settings, passes, p) ||
        (light && Math.max(light[n], light[n + 1], light[n + 2]) > .12));
    }
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const p = y * w + x, s = (y * sw + x) * 2, q = p * 3;
      const c = ((h - 1 - y) * w + x) * 3;
      const [dx, dy] = ditherCoordinates(settings, passes, p, x, y);
      const bias = (pixelLook.bayerRank(dx, dy) - .5) * dither;
      const localId = local?.at[(h - 1 - y) * w + x];
      if (localId && (detail[p] || coverage[p] >= settings.threshold)) {
        const nativeShade = [color[c] / 255, color[c + 1] / 255, color[c + 2] / 255];
        const index = pixelLook.localIndex(local, localId, nativeShade, dx, dy, !detail[p]);
        use[index]++;
        const packed = local.output.packed[index];
        rgb[q] = packed >> 16; rgb[q + 1] = (packed >> 8) & 255; rgb[q + 2] = packed & 255;
        continue;
      }
      let threshold = settings.threshold, chosen = 0;
      if (settings.resolve === 'clusters' && coverage[p] > 0 && coverage[p] < 1) {
        const neighbor = (x > 0 && coverage[p - 1] >= threshold) || (x + 1 < w && coverage[p + 1] >= threshold) ||
          (y > 0 && coverage[p - w] >= threshold) || (y + 1 < h && coverage[p + w] >= threshold);
        threshold += neighbor ? -.12 : .10;
      }
      if (detail[p] || coverage[p] >= threshold) {
        const votes = new Map();
        if (coverage[p] < .98 && !detail[p]) {
          for (const j of [s, s + 1, s + sw, s + sw + 1]) {
            const weight = samples.passes.coverage[j];
            if (weight < .06) continue;
            const iy = (sw * (samples.h - 1 - Math.floor(j / sw)) + j % sw) * 3, a = weight || 1;
            // The raw samples are composited against palette zero. Recover the foreground.
            const shade = palette[0].map((bg, k) => {
              const value = samples.color[iy + k] / 255;
              const foreground = samples.alpha ? value : (value - bg * (1 - a)) / a;
              return Math.max(0, Math.min(1, foreground + bias));
            });
            const index = tone ? pixelLook.toneIndex(tone, ...shade, dx, dy) : pixelLook.nearest(shade, palette, true);
            votes.set(index, (votes.get(index) || 0) + weight);
          }
        }
        const shade = [color[c] / 255, color[c + 1] / 255, color[c + 2] / 255];
        chosen = tone ? pixelLook.toneIndex(tone, ...shade, dx, dy) :
          pixelLook.nearest(shade.map(value => value + bias), palette, !detail[p]);
        let best = votes.get(chosen) || 0;
        for (const [index, weight] of votes) if (weight > best) {
          chosen = index;
          best = weight;
        }
      }
      use[chosen]++;
      for (let k = 0; k < 3; k++) rgb[q + k] = Math.round((grade ? grade[chosen * 3 + k] : palette[chosen][k]) * 255);
    }
    return { w, h, rgb, use, detail, ...((local || tone) && { palette: local?.output.packed || tone.palette }) };
  }

  return Object.freeze({ prepare, snapView, modulo, ditherCoordinates, coordinates, matching, protectedPixel, resolve });
})();
if (typeof module !== 'undefined') module.exports = ArtStability;

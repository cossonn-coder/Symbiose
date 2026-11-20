/* Fixed-grid, palette-aware resolve using coverage and cluster voting.
   No per-frame palette fitting, camera movement or black ink. */
const PixelLook = (() => {
  const selectors = typeof TargetSelectors === 'undefined' ? require('./target-selectors.js') : TargetSelectors;
  let curves, luts, stacks, spaces;
  try {
    curves = ColorCurves;
    luts = ColorLUT;
    stacks = ColorStack;
    spaces = ColorSpace;
  } catch {
    curves = require('./color-curves.js');
    luts = require('./color-lut.js');
    stacks = require('./color-stack.js');
    spaces = require('./color-space.js');
  }
  const weights = [0.30, 0.55, 0.15];
  const bayer = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
  const stipple = Object.freeze({
    cutoff: 0.19,
    stops: Object.freeze([
      [0, '#000000'], [0.14, '#176bfa'], [0.37, '#44c73d'],
      [0.57, '#e85dc9'], [0.77, '#ff8d27'], [1, '#fff1cd']
    ].map(Object.freeze)),
    pattern: 'bayer',
    amount: 1,
    seed: 0,
    preserveDots: true
  });
  const presets = Object.freeze({ stipple });
  const fraction = value => Number.isFinite(value) && value >= 0 && value <= 1;
  const bayerRanks = Float32Array.from(bayer, rank => (rank + 0.5) / bayer.length);
  const bayerRank = (x, y) => bayerRanks[(x & 3) + ((y & 3) << 2)];
  const isColor = n => Number.isSafeInteger(n) && n >= 0 && n <= 0xffffff;
  const isSwatch = value => typeof value === 'string' && /^#[0-9a-f]{6}$/i.test(value);
  const unpack = color => [color >> 16, (color >> 8) & 255, color & 255].map(n => n / 255);
  const clamp = n => Math.max(0, Math.min(1, n));
  const record = value => value && Object.getPrototypeOf(value) === Object.prototype;
  const packedRgb = ([r, g, b]) => (Math.round(clamp(r) * 255) << 16) |
    (Math.round(clamp(g) * 255) << 8) | Math.round(clamp(b) * 255);

  function paletteSelector(colors, roles) {
    const index = value => {
      if (!Number.isSafeInteger(value) || value < 0 || value >= colors.length)
        throw new RangeError('Palette index out of range: ' + value);
      return value;
    };
    return from => {
      if (typeof from === 'number') return [index(from)];
      if (typeof from !== 'string' || !from) throw new TypeError('Expected a palette index, #rrggbb swatch or role');
      if (isSwatch(from)) {
        const color = parseInt(from.slice(1), 16), indices = [];
        colors.forEach((entry, i) => { if (entry === color) indices.push(i); });
        if (!indices.length) throw new RangeError('Swatch is missing from the palette: ' + from);
        return indices;
      }
      const at = from.lastIndexOf('.'), whole = Object.hasOwn(roles, from) || at < 0;
      const name = whole ? from : from.slice(0, at), ramp = Object.hasOwn(roles, name) && roles[name];
      if (!Array.isArray(ramp) || !ramp.length) throw new RangeError('Unknown or empty palette role: ' + name);
      if (whole) return Array.from(ramp, index);
      const stop = from.slice(at + 1);
      const step = stop === 'shadow' ? 0 : stop === 'midtone' ? Math.floor((ramp.length - 1) / 2) :
        stop === 'highlight' ? ramp.length - 1 : /^(0|[1-9]\d*)$/.test(stop) ? Number(stop) : -1;
      if (step < 0 || step >= ramp.length) throw new RangeError('Unknown palette ramp stop: ' + from);
      return [index(ramp[step])];
    };
  }

  function prepareRemap(definition, palette, roles = {}, override, { deferTargets = false } = {}) {
    if (definition === undefined || definition === false) return null;
    if (!record(definition) || Object.keys(definition).some(key => !['rules', 'protect', 'color'].includes(key)))
      throw new TypeError('Palette remap needs a settings object with rules and optional protect');
    const colors = Array.isArray(palette) || ArrayBuffer.isView(palette) ? Array.from(palette) : [];
    if (!deferTargets && (!colors.length || !colors.every(isColor)))
      throw new TypeError('Palette remap needs a palette of packed RGB colors');
    const { rules, protect = [] } = definition;
    const contract = spaces.settings(override === undefined ? definition.color : override);
    const encodeTarget = contract && spaces.prepare(undefined, { ...contract.output, outOfRange: 'preserve' });
    const applyTarget = contract && spaces.wrap((rgb, out, target) => {
      for (let i = 0; i < 3; i++) out[i] = target[i];
    }, contract);
    if (!Array.isArray(rules) || rules.length > 1024 || !Array.isArray(protect) || protect.length > 1024)
      throw new TypeError('Palette remap rules and protect must be lists of at most 1024 entries');
    const select = deferTargets ? value => {
      if (!(typeof value === 'string' && value.trim() || Number.isSafeInteger(value) && value >= 0))
        throw new TypeError('Expected a palette index, #rrggbb swatch or role');
      return [];
    } : paletteSelector(colors, roles);
    const overrides = new Map();
    for (const rule of rules) {
      if (!rule || Object.getPrototypeOf(rule) !== Object.prototype ||
          Object.keys(rule).some(key => key !== 'from' && key !== 'to'))
        throw new TypeError('Expected a palette remap rule with from and to');
      const color = isSwatch(rule.to) ? parseInt(rule.to.slice(1), 16) : rule.to;
      let output;
      if (isColor(color)) output = encodeTarget ? encodeTarget(unpack(color)) : unpack(color);
      else if (contract && Array.isArray(color) && color.length === 3 && Array.from(color).every(Number.isFinite)) output = color.slice();
      else throw new TypeError('Palette remap output needs a hex swatch, packed RGB or a declared numeric RGB triple');
      for (const i of select(rule.from)) overrides.set(i, Object.freeze(output));
    }
    const locked = new Set();
    for (const from of protect) for (const i of select(from)) {
      locked.add(i);
      overrides.set(i, Object.freeze(unpack(colors[i])));
    }
    const base = Float32Array.from(colors.flatMap(unpack));
    function target(index, rgb) {
      const value = overrides.get(index);
      return value && applyTarget && !locked.has(index) ? applyTarget(rgb ?? unpack(colors[index]), undefined, value) : value;
    }
    return Object.freeze({
      target,
      protects: index => locked.has(index),
      grade(prior, amount = 1, onClip) {
        if (!fraction(amount)) throw new RangeError('Palette remap strength must be in [0, 1]');
        const output = base.slice();
        if (prior) output.set(prior.subarray ? prior.subarray(0, output.length) : prior.slice(0, output.length));
        for (const i of overrides.keys()) {
          const input = applyTarget && prior?.length >= i * 3 + 3 ? prior.slice(i * 3, i * 3 + 3) : undefined;
          const rgb = target(i, input);
          if (onClip) onClip(i, ...rgb.map((n, k) => base[i * 3 + k] + (n - base[i * 3 + k]) * amount));
          for (let channel = 0; channel < 3; channel++) {
            const key = i * 3 + channel;
            output[key] = clamp(base[key] + (rgb[channel] - base[key]) * amount);
          }
        }
        return output;
      }
    });
  }

  function gradePalette(grade) {
    const byte = n => Math.round(Math.max(0, Math.min(1, n)) * 255);
    return Array.from({ length: grade.length / 3 }, (_, i) =>
      (byte(grade[i * 3]) << 16) | (byte(grade[i * 3 + 1]) << 8) | byte(grade[i * 3 + 2]));
  }

  function prepareColorStack(stack, palette, roles) {
    return stacks.prepare(stack, { palette, roles,
      paletteRemap: (definition, color) => prepareRemap(definition, palette, roles, color) });
  }

  function colorGrade(palette, roles, prior, remap, definition, lut, stack, onClip) {
    const transfer = curves.prepare(definition), plan = prepareRemap(remap, palette, roles);
    const lookup = lut === undefined || lut === false ? null : luts.prepare(lut);
    const ordered = prepareColorStack(stack, palette, roles);
    if (!transfer && !lookup && !ordered) return plan ? plan.grade(prior, 1, onClip) : null;
    const grade = new Float32Array(palette.length * 3), result = [0, 0, 0], protectedSlots = [];
    for (let i = 0; i < palette.length; i++) {
      const offset = i * 3;
      if (ordered?.protects(i)) {
        protectedSlots.push(i);
        grade.set(unpack(palette[i]), offset);
        continue;
      }
      const base = prior?.length >= offset + 3 ? prior.slice(offset, offset + 3) : unpack(palette[i]);
      let shaped = transfer ? transfer(base, result) : base;
      if (lookup) shaped = lookup.apply(shaped, result);
      if (ordered) shaped = ordered.sample(shaped, result, i);
      grade.set(shaped, offset);
    }
    const resolved = plan ? plan.grade(grade, 1, onClip) : grade;
    if (plan) for (const i of protectedSlots) resolved.set(grade.subarray(i * 3, i * 3 + 3), i * 3);
    for (let i = 0; i < resolved.length; i += 3) {
      if (onClip) onClip(i / 3, resolved[i], resolved[i + 1], resolved[i + 2]);
      for (let channel = 0; channel < 3; channel++) resolved[i + channel] = clamp(resolved[i + channel]);
    }
    return resolved;
  }

  function toneSettings(definition) {
    if (definition === undefined || definition === false) return null;
    const overrides = typeof definition === 'string' ? { preset: definition } : definition;
    if (!overrides || Object.getPrototypeOf(overrides) !== Object.prototype)
      throw new TypeError('Expected a tone preset name or settings object');
    const { preset = 'stipple', ...changes } = overrides;
    if (!Object.hasOwn(presets, preset)) throw new RangeError('Unknown tone preset: ' + preset);
    for (const key of Object.keys(changes)) {
      if (!Object.hasOwn(stipple, key)) throw new TypeError('Unknown tone setting: ' + key);
    }
    const settings = { ...presets[preset], ...changes };
    const { cutoff, stops, pattern, amount, seed, preserveDots } = settings;
    if (!fraction(cutoff) || cutoff === 1) throw new RangeError('Tone cutoff must be in [0, 1)');
    if (!fraction(amount)) throw new RangeError('Tone dither amount must be in [0, 1]');
    if (pattern !== 'bayer' && pattern !== 'blue-noise')
      throw new RangeError('Tone pattern must be bayer or blue-noise');
    if (!Number.isSafeInteger(seed)) throw new RangeError('Tone seed must be a safe integer');
    if (typeof preserveDots !== 'boolean') throw new TypeError('Tone preserveDots must be a boolean');
    if (!Array.isArray(stops) || stops.length < 2 || stops.length > 48 ||
        !Array.from(stops).every((stop, i) => Array.isArray(stop) && stop.length === 2 &&
          fraction(stop[0]) && typeof stop[1] === 'string' && /^#[\da-f]{6}$/i.test(stop[1]) &&
          (i === 0 || stop[0] > stops[i - 1][0])) ||
        stops[0][0] !== 0 || stops[0][1] !== '#000000' || stops.at(-1)[0] !== 1)
      throw new RangeError('Use 2 to 48 increasing [position, #rrggbb] tone stops from [0, "#000000"] to position 1');
    return settings;
  }

  function prepareTone(definition, blueNoise) {
    const settings = toneSettings(definition);
    if (!settings) return null;
    let width = 4, height = 4, thresholds = bayerRanks.slice();
    if (settings.pattern === 'blue-noise') {
      if (typeof blueNoise !== 'function') throw new TypeError('Pass materials.blueNoise to prepare this tone pattern');
      const tile = blueNoise({ seed: settings.seed });
      width = tile.width;
      height = tile.height;
      thresholds = Float32Array.from(tile.ranks, rank => (rank + 0.5) / tile.ranks.length);
    }
    return {
      ...settings, width, height, thresholds,
      palette: settings.stops.map(stop => parseInt(stop[1].slice(1), 16))
    };
  }

  // Coordinates are top-left art pixels. Each band mixes its two adjacent palette entries.
  function toneIndex(tone, r, g, b, x, y) {
    const luma = r * weights[0] + g * weights[1] + b * weights[2];
    if (luma <= tone.cutoff) return 0;
    const value = (luma - tone.cutoff) / (1 - tone.cutoff);
    const stops = tone.stops;
    let low = 0;
    while (low < stops.length - 2 && value > stops[low + 1][0]) low++;
    const share = (value - stops[low][0]) / (stops[low + 1][0] - stops[low][0]);
    const rank = tone.thresholds[((y % tone.height + tone.height) % tone.height) * tone.width + (x % tone.width + tone.width) % tone.width];
    return low + Number(share >= 0.5 + (rank - 0.5) * tone.amount);
  }

  function nearest(c, palette, solid) {
    let best = solid && palette.length > 1 ? 1 : 0, distance = Infinity;
    for (let i = best; i < palette.length; i++) {
      const d = c.reduce((sum, v, k) => sum + (v - palette[i][k]) ** 2 * weights[k], 0);
      if (d < distance) { distance = d; best = i; }
    }
    return best;
  }

  function preparePalette(definition, { palette = [], roles = {}, blueNoise } = {}) {
    if (!record(definition) || Object.keys(definition).some(key => !['palette', 'reserved', 'dither', 'source'].includes(key)))
      throw new TypeError('A palette constraint accepts palette, reserved, dither and source settings');
    const { source = 'lit' } = definition;
    if (!['lit', 'graded'].includes(source)) throw new RangeError('Palette source must be lit or graded');
    const select = paletteSelector(palette, roles);
    function colors(values, name) {
      if (!Array.isArray(values) || values.length > 48)
        throw new RangeError(name + ' needs up to 48 swatches');
      return [...new Set(Array.from(values).flatMap(value => {
        if (isSwatch(value)) return parseInt(value.slice(1), 16);
        if (Array.isArray(value) && value.length === 3 && Array.from(value).every(fraction)) return packedRgb(value);
        return select(value).map(index => {
          const color = palette[index];
          if (!isColor(color)) throw new RangeError('Palette constraints require packed RGB scene swatches');
          return color;
        });
      }))];
    }
    const reserved = colors(definition.reserved ?? [], 'Reserved list');
    const candidates = colors(definition.palette ?? Array.from(palette, (_, i) => i), 'Output palette')
      .filter(color => !reserved.includes(color));
    const packed = [...candidates, ...reserved];
    if (!candidates.length || packed.length > 48) throw new RangeError('Use 1 to 48 swatches with at least one unreserved color');
    const swatches = packed.map(unpack), exact = new Map(reserved.map((color, index) => [color, candidates.length + index]));
    const dither = definition.dither ?? {};
    if (!record(dither) || Object.keys(dither).some(key => !['pattern', 'strength', 'seed'].includes(key)))
      throw new TypeError('Palette dither accepts pattern, strength and seed settings');
    const { pattern = 'bayer', strength = 0, seed = 0 } = dither;
    if (!['none', 'checker', 'bayer', 'blue-noise'].includes(pattern) || !fraction(strength) || !Number.isSafeInteger(seed))
      throw new RangeError('Palette dither requires a valid pattern, strength in [0, 1] and integer seed');
    const amount = pattern === 'none' ? 0 : strength;
    let width = 4, height = 4, ranks = bayerRanks;
    if (pattern === 'checker') {
      width = height = 2;
      ranks = Float32Array.of(.25, .75, .75, .25);
    } else if (pattern === 'blue-noise' && amount) {
      if (typeof blueNoise !== 'function') throw new TypeError('Pass materials.blueNoise to prepare this palette pattern');
      const tile = blueNoise({ seed });
      ({ width, height } = tile);
      ranks = Float32Array.from(tile.ranks, rank => (rank + .5) / tile.ranks.length);
    }
    const count = candidates.length;
    const mod = (n, size) => ((Math.floor(n) % size) + size) % size;
    const reservedIndex = rgb => exact.size ? exact.get(packedRgb(rgb)) : undefined;
    function index(rgb, x = 0, y = 0, useDither = true) {
      const locked = reservedIndex(rgb);
      if (locked !== undefined) return locked;
      let best = 0, second = 0, firstDistance = Infinity, secondDistance = Infinity;
      for (let i = 0; i < count; i++) {
        let distance = 0;
        for (let k = 0; k < 3; k++) distance += weights[k] * (rgb[k] - swatches[i][k]) ** 2;
        if (distance < firstDistance) {
          second = best; secondDistance = firstDistance;
          best = i; firstDistance = distance;
        } else if (distance < secondDistance) {
          second = i; secondDistance = distance;
        }
      }
      if (!amount || !useDither || count < 2) return best;
      const rank = ranks[mod(y, height) * width + mod(x, width)];
      if (rank >= .5) return best;
      let projection = 0, length = 0;
      for (let k = 0; k < 3; k++) {
        const delta = swatches[second][k] - swatches[best][k];
        projection += weights[k] * delta * (rgb[k] - swatches[best][k]);
        length += weights[k] * delta * delta;
      }
      return projection >= (.5 + (rank - .5) * amount) * length ? second : best;
    }
    return { packed, swatches, count, width, height, ranks, amount, source, reservedIndex, index };
  }

  function prepareLookPolicy(definition, options = {}) {
    if (!record(definition)) throw new TypeError('Expected a look palette policy');
    const { stack, assetId, mask, ...policy } = definition;
    const active = options.skipMaskedStacks && mask ? undefined : stack;
    if (stack && !active && !Object.keys(policy).length) return null;
    const grade = active && colorGrade(options.palette, options.roles, undefined, false, false, false, active,
      options.onPaletteClip && ((i, r, g, b) => options.onPaletteClip({ assetId, stack: active.name }, i, r, g, b)));
    const mapOnly = Boolean(grade && !Object.keys(policy).length);
    const plan = preparePalette(mapOnly ? { palette: ['#000000'] } : policy, options);
    if (mapOnly) {
      plan.packed = gradePalette(grade);
      plan.swatches = plan.packed.map(unpack);
    }
    const effects = mask !== undefined && mask !== false ?
      (typeof SplatEffects === 'undefined' ? require('./splat-effects.js') : SplatEffects) : null;
    return Object.assign(plan, { grade, mapOnly, assetId, stackName: active?.name, maskSource: mask || undefined,
      sourceSwatches: grade ? Array.from(options.palette, unpack) : undefined,
      mask: effects?.prepareMask(mask, options.context, { validateOnly: options.validateOnly }) });
  }

  function preparePaletteConstraints(definition, options) {
    if (definition === undefined || definition === false) return null;
    if (!record(definition) || Object.keys(definition).some(key => key !== 'default' && key !== 'targets'))
      throw new TypeError('Palette constraints accept default and targets');
    const { default: fallback, targets = [] } = definition;
    if (!Array.isArray(targets) || targets.length > 63)
      throw new RangeError('Palette constraints accept up to 63 targets');
    const rules = [], palettes = [];
    const skipMask = policy => Boolean(policy?.mask && (options?.skipMasks ||
      options?.maskSupported && !options.maskSupported(policy.mask)));
    const defaultPolicy = fallback === undefined || skipMask(fallback) ? null :
      prepareLookPolicy(fallback, options);
    const defaultSlot = defaultPolicy ? palettes.push(defaultPolicy) : 0;
    for (const target of targets) {
      if (!record(target)) throw new TypeError('Expected a palette target');
      const { select, object, material, ...policy } = target;
      if (select !== undefined && (object !== undefined || material !== undefined))
        throw new TypeError('Use select or legacy object and material fields on a target');
      const filter = selectors.prepare(select ?? { ...(object !== undefined && { object }), ...(material !== undefined && { material }) });
      const prepared = skipMask(policy) ? null : prepareLookPolicy(policy, options);
      if (prepared) rules.push({ select: filter, slot: palettes.push(Object.assign(prepared, { select: filter })) });
    }
    if (!palettes.length) return null;

    const match = target => rules.findLast(rule => selectors.matches(rule.select, target))?.slot ?? 0;
    function slots(world) {
      const index = selectors.index(world);
      const matches = new Map(), result = new Uint8Array(world.count);
      if (!rules.length) return result;
      for (let i = 0; i < world.count; i++) {
        const target = index.row(i);
        let slot = matches.get(target);
        if (slot === undefined) {
          slot = match(target);
          matches.set(target, slot);
        }
        result[i] = slot;
      }
      return result;
    }
    return { palettes, defaultSlot, slots, match, rules };
  }

  function outputPalettes(base, locals) {
    const packed = base.slice();
    const indices = new Map(packed.map((color, index) => [color, index]));
    const rows = locals.map(palette => palette.map(([r, g, b]) => {
      const color = (Math.round(r * 255) << 16) | (Math.round(g * 255) << 8) | Math.round(b * 255);
      if (!indices.has(color)) {
        indices.set(color, packed.length);
        packed.push(color);
      }
      return indices.get(color);
    }));
    return { packed, rows };
  }

  function paletteIndex(policy, rgb, x, y, { scene, grade, useDither } = {}) {
    const input = policy.sourceSwatches ?? scene;
    const mapping = policy.grade || (policy.source === 'graded' ? grade : undefined);
    if (input && mapping) {
      const reserved = policy.reservedIndex(rgb);
      if (reserved !== undefined) return reserved;
      const at = nearest(rgb, input, false);
      if (policy.mapOnly) return at;
      rgb = mapping.slice(at * 3, at * 3 + 3);
    }
    return policy.index(rgb, x, y, useDither);
  }

  function localIndex(local, id, rgb, x, y, useDither) {
    const row = id - 1, policy = local.constraints?.[row];
    const slot = policy ? paletteIndex(policy, rgb, x, y, { scene: local.scene, grade: local.grade, useDither }) :
      nearest(rgb, local.palettes[row], false);
    return local.output.rows[row][slot];
  }

  function mediumTransform(plan, medium) {
    const slot = plan?.match(medium);
    if (!slot) return undefined;
    const policy = plan.palettes[slot - 1];
    if (policy.mask) return undefined;
    return rgb => unpack(policy.packed[paletteIndex(policy, rgb, 0, 0, { useDither: false })]);
  }

  function ink(body) {
    const shade = body.map(v => v * 0.64), luma = shade.reduce((n, v, k) => n + v * weights[k], 0);
    return shade.map(v => Math.min(1, v * Math.max(1, 0.12 / Math.max(luma, 0.001))));
  }
  function resolve({ color, depth, w, h, palette, grade, interiorColor, dither = 0, local, contour = true, ditherAt }) {
    const width = w / 2, height = h / 2, rgb = new Uint8Array(width * height * 3), use = new Uint32Array(local?.output.packed.length ?? palette.length);
    const mapped = i => grade ? grade.slice(i * 3, i * 3 + 3) : palette[i];
    const at = (x, y) => Math.max(0, Math.min(h - 1, y)) * w + Math.max(0, Math.min(w - 1, x));
    const z = (x, y) => Math.min(...[at(x * 2, y * 2), at(x * 2 + 1, y * 2), at(x * 2, y * 2 + 1), at(x * 2 + 1, y * 2 + 1)].map(i => depth[i]));
    for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) {
      const ids = [at(x * 2, y * 2), at(x * 2 + 1, y * 2), at(x * 2, y * 2 + 1), at(x * 2 + 1, y * 2 + 1)];
      const samples = ids.map(i => [color[i * 3] / 255, color[i * 3 + 1] / 255, color[i * 3 + 2] / 255]);
      const average = [0, 1, 2].map(k => samples.reduce((s, c) => s + c[k], 0) / 4);
      const base = (y * width + x) * 3;
      const native = interiorColor ? [0, 1, 2].map(k => interiorColor[base + k] / 255) : average;
      const anchor = ditherAt?.(x, y);
      const localId = local?.at[y * width + x];
      if (localId) {
        const [dx, dy] = anchor ?? [x, height - 1 - y];
        const index = localIndex(local, localId, native, dx, dy);
        const tone = local.output.packed[index], q = ((height - 1 - y) * width + x) * 3;
        rgb[q] = tone >> 16;
        rgb[q + 1] = (tone >> 8) & 255;
        rgb[q + 2] = tone & 255;
        use[index]++;
        continue;
      }
      const rank = anchor ? bayerRank(...anchor) : bayerRank(x, y);
      const noise = interiorColor ? (rank - 0.5) * dither : 0;
      let selected = nearest(native.map(v => Math.max(0, Math.min(1, v + noise))), palette, false);
      let c = Array.from(mapped(selected));
      const votes = new Map(); let best = -1, score = 0, coverage = 0;
      ids.forEach((id, j) => {
        if (depth[id] >= 0.995) return;
        coverage++;
        const label = nearest(samples[j], palette, true), n = (votes.get(label) || 0) + 1;
        votes.set(label, n);
      });
      ids.forEach((id, j) => {
        if (depth[id] >= 0.995) return;
        const label = nearest(samples[j], palette, true), n = votes.get(label);
        if (n > score) { best = label; score = n; }
      });
      if (best >= 0) {
        const outer = coverage < 4 || [z(x - 1, y), z(x + 1, y), z(x, y - 1), z(x, y + 1)].some(d => d >= 0.995);
        if (outer && contour) {
          selected = best;
          const body = mapped(best), tone = ink(Array.from(body)), background = mapped(0), a = coverage / 4;
          c = body.map((v, k) => background[k] * (1 - a) + (v * 0.35 + tone[k] * 0.65) * a);
        }
      }
      use[selected]++;
      const q = ((height - 1 - y) * width + x) * 3;
      c.forEach((v, k) => { rgb[q + k] = Math.round(Math.max(0, Math.min(1, v)) * 255); });
    }
    return { w: width, h: height, rgb, use, ...(local && { palette: local.output.packed }) };
  }
  const glsl = `
int pixelNearest(vec3 c, bool solid) {
  int best = solid && u_n > 1 ? 1 : 0; float bd = 1e9;
  for (int i = 0; i < 48; i++) {
    if (i >= u_n) break; if (solid && i == 0 && u_n > 1) continue;
    vec3 df = c - u_pal[i]; float d = dot(df * df, vec3(0.30, 0.55, 0.15));
    if (d < bd) { bd = d; best = i; }
  }
  return best;
}
vec3 pixelMapped(int i) { return u_grade > 0.5 ? u_out[i] : u_pal[i]; }
ivec2 pixelAt(ivec2 p) { return clamp(p, ivec2(0), textureSize(u_depth, 0) - 1); }
float pixelDepth(ivec2 p) {
  ivec2 q = p * 2; float d = 1.0;
  for (int y = 0; y < 2; y++) for (int x = 0; x < 2; x++) d = min(d, texelFetch(u_depth, pixelAt(q + ivec2(x, y)), 0).r);
  return d;
}
#ifndef PIXEL_NATIVE
vec3 pixelNative(ivec2 p) { return texelFetch(u_crispScene, p, 0).rgb; }
#endif
vec3 pixelResolve(ivec2 p) {
  vec3 samples[4]; int labels[4]; bool solid[4]; float coverage = 0.0;
  for (int i = 0; i < 4; i++) {
    ivec2 q = pixelAt(p * 2 + ivec2(i & 1, i >> 1));
    samples[i] = texelFetch(u_scene, q, 0).rgb;
    solid[i] = texelFetch(u_depth, q, 0).r < 0.995;
    labels[i] = pixelNearest(samples[i], solid[i]); if (solid[i]) coverage += 0.25;
  }
  vec3 native = pixelNative(p);   // (a page may define PIXEL_NATIVE and its own pixelNative, to work on the native picture first: glass, contact shade)
  float noise = ((BAYER[(p.x & 3) + ((p.y & 3) << 2)] + 0.5) / 16.0 - 0.5) * u_dither;
  vec3 c = pixelMapped(pixelNearest(clamp(native + noise, 0.0, 1.0), false)); int best = -1, score = 0;
  for (int i = 0; i < 4; i++) {
    if (!solid[i]) continue; int n = 0;
    for (int j = 0; j < 4; j++) if (solid[j] && labels[j] == labels[i]) n++;
    if (n > score) { best = labels[i]; score = n; }
  }
  if (best >= 0) {
    bool outer = coverage < 1.0 || max(max(pixelDepth(p - ivec2(1, 0)), pixelDepth(p + ivec2(1, 0))),
      max(pixelDepth(p - ivec2(0, 1)), pixelDepth(p + ivec2(0, 1)))) >= 0.995;
    if (outer) {
      vec3 body = pixelMapped(best);
      vec3 tone = body * 0.64; tone = min(vec3(1.0), tone * max(1.0, 0.12 / max(dot(tone, vec3(0.30, 0.55, 0.15)), 0.001)));
      c = mix(pixelMapped(0), mix(body, tone, 0.65), coverage);
    }
  }
  return c;
}`;
  const toneGlsl = `
uniform int u_inkToneCount;
uniform float u_inkToneCutoff;
uniform float u_inkToneAmount;
uniform vec4 u_inkToneStops[48]; // RGB color and stop position
uniform highp sampler2D u_inkToneRanks; // normalized threshold tile

vec3 inkToneResolve(vec3 color, ivec2 pixel) {
  float luma = dot(color, vec3(0.30, 0.55, 0.15));
  if (luma <= u_inkToneCutoff) return u_inkToneStops[0].rgb;
  float value = (luma - u_inkToneCutoff) / (1.0 - u_inkToneCutoff);
  int low = 0;
  for (int i = 1; i < 47; i++) {
    if (i >= u_inkToneCount - 1 || value <= u_inkToneStops[i].a) break;
    low = i;
  }
  vec4 a = u_inkToneStops[low], b = u_inkToneStops[low + 1];
  float share = (value - a.a) / (b.a - a.a);
  float rank = texelFetch(u_inkToneRanks, pixel % textureSize(u_inkToneRanks, 0), 0).r;
  return share >= mix(0.5, rank, u_inkToneAmount) ? b.rgb : a.rgb;
}`;
  return { nearest, ink, resolve, glsl, presets, toneSettings, prepareTone, toneIndex, toneGlsl, bayerRank, outputPalettes, localIndex,
    preparePalette, prepareLookPolicy, preparePaletteConstraints, paletteIndex, mediumTransform,
    prepareRemap, gradePalette, prepareColorStack, colorGrade };
})();
if (typeof module !== 'undefined') module.exports = PixelLook;

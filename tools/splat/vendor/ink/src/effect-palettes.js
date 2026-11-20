/* Per-effect output ramps, selected by visible coverage on the native art grid. */
const EffectPalettes = (() => {
  const pixel = typeof PixelLook === 'undefined' ? require('./pixel-look.js') : PixelLook;
  const kinds = Object.freeze(['fog', 'clouds', 'sky', 'emission']);
  const floors = { fog: .58, clouds: .46, sky: .48, emission: .24 };
  const order = ['emission', 'fog', 'clouds', 'sky'];
  const symbols = Object.freeze(Object.fromEntries(kinds.map((name, i) => [name, i + 1])));
  const list = (value, label) => {
    if (!Array.isArray(value) || Array.from(value).some(item => typeof item !== 'string' || !item.trim()))
      throw new TypeError(label + ' needs an array of names');
    return new Set(value);
  };
  const unit = (value, label) => {
    if (!Number.isFinite(value) || value < 0 || value > 1) throw new RangeError(label + ' needs a number from 0 to 1');
    return value;
  };
  function record(value, keys, label) {
    if (!value || ![Object.prototype, null].includes(Object.getPrototypeOf(value)) ||
        Object.keys(value).some(key => !keys.includes(key))) throw new TypeError('Invalid ' + label + ' settings');
    return value;
  }
  function limits(value, label) {
    if (!Array.isArray(value) || value.length !== 2 || !value.every(Number.isFinite) || !(value[0] < value[1]))
      throw new RangeError(label + ' needs two increasing numbers');
    return value.slice();
  }

  function prepare(source, palette) {
    if (source == null || source === false) return null;
    record(source, [...kinds, 'protect'], 'effect palette');
    const protect = record(source.protect ?? {}, ['objects', 'materials'], 'effect palette protection');
    const objects = list(protect.objects ?? [], 'Protected objects'), materials = list(protect.materials ?? [], 'Protected materials');
    const ramps = new Map();
    for (const kind of kinds) {
      const raw = source[kind];
      if (raw === undefined || raw === false) continue;
      const rule = Array.isArray(raw) ? { colors: raw } :
        record(raw, ['colors', 'threshold', 'geometry', 'mode', 'range', 'dither', 'when'], kind + ' palette');
      const { colors, geometry = false, mode = 'luma', dither = 0, when } = rule;
      if (typeof geometry !== 'boolean' || !['luma','nearest'].includes(mode)) throw new TypeError('Invalid ' + kind + ' palette mode or geometry');
      const threshold = unit(rule.threshold ?? floors[kind], kind + ' coverage threshold');
      const amount = unit(dither, kind + ' palette dither');
      const range = limits(rule.range ?? [0,1], kind + ' tone range');
      range.forEach(n => unit(n, kind + ' tone range'));
      if (!Array.isArray(colors) || !colors.length || colors.length > 64)
        throw new RangeError('Effect palettes need 1 to 64 colors');
      const packed = Array.from(colors, color => {
        if (typeof color === 'string' && /^#[\da-f]{6}$/i.test(color)) return parseInt(color.slice(1),16);
        if (Number.isSafeInteger(color) && color >= 0 && color < palette.length) return palette[color];
        throw new TypeError('Effect colors need #rrggbb or a scene palette index');
      });
      let gate;
      if (when !== undefined) {
        const { channel, min = -Infinity, max = Infinity } = record(when,['channel','min','max'],'effect palette profile gate');
        if (typeof channel !== 'string' || !channel.trim() || (min !== -Infinity && !Number.isFinite(min)) ||
            (max !== Infinity && !Number.isFinite(max)) || min > max)
          throw new TypeError('A profile gate needs a numeric channel and an optional min/max range');
        gate = { channel, min, max };
      }
      const rgb = packed.map(c => [(c>>16)/255, ((c>>8)&255)/255, (c&255)/255]);
      ramps.set(kind, { packed, rgb, geometry, mode, amount, range, threshold, gate });
    }
    return ramps.size ? { ramps, objects, materials } : null;
  }

  function activate(settings, parameters) {
    if (!settings) return null;
    const ramps = new Map([...settings.ramps].filter(([, { gate }]) => {
      if (!gate) return true;
      const value = parameters?.[gate.channel];
      return Number.isFinite(value) && value >= gate.min && value <= gate.max;
    }));
    return ramps.size ? { ...settings, ramps } : null;
  }

  function apply(frame, passes, signals, source, palette, capture, ditherAt) {
    const { rules, media, backdropCloud, sky, haze } = signals;
    const { w, h, rgb } = frame, { ramps, objects, materials } = rules;
    const mask = capture ? new Uint8Array(w*h) : null;
    const active = order.filter(kind => ramps.has(kind));
    const protectedObjects = new Set(passes.objects?.flatMap((name,id) => objects.has(name) ? [id] : []));
    const protectedMaterials = new Set(passes.materials?.flatMap((name,id) => materials.has(name) ? [id] : []));
    const sample = [0,0,0];
    let changed = false;
    for (let p=0; p<w*h; p++) {
      if (frame.alpha && !frame.alpha[p] || protectedObjects.has(passes.objectId?.[p]) ||
          protectedMaterials.has(passes.materialId?.[p]) || frame.inkMask?.[p] > 0 && frame.inkMask[p] < 4) continue;
      const x = p%w, y = Math.floor(p/w), bottom = (h-1-y)*w+x, q = p*3;
      const coverage = passes.coverage[p], geometry = Number.isFinite(passes.depth[p]);
      const through = media?.[q+2] ?? 1, cloud = backdropCloud?.[bottom] ?? 0;
      const back = (1-coverage)*through;
      const emission = passes.emission;
      const weights = {
        fog: (media?.[q] ?? 0) + through*(haze?.[bottom] ?? 0),
        clouds: (media?.[q+1] ?? 0) + back*cloud,
        sky: sky ? back*(1-cloud) : 0,
        emission: emission ? Math.max(emission[q],emission[q+1],emission[q+2]) : 0
      };
      for (const kind of active) {
        const ramp = ramps.get(kind), weight = weights[kind];
        if (!(weight > 0 && weight >= ramp.threshold) ||
            (geometry && !ramp.geometry && (kind === 'fog' || kind === 'clouds'))) continue;
        for (let c=0;c<3;c++) sample[c] = kind === 'emission' ? emission[q+c] : source[bottom*3+c]/255;
        let index;
        if (ramp.mode === 'nearest') index = pixel.nearest(sample, ramp.rgb, false);
        else {
          const luma = sample[0]*.30 + sample[1]*.55 + sample[2]*.15;
          const [lo,hi] = ramp.range, span = ramp.packed.length-1;
          const step = Math.min(1, Math.max(0,(luma-lo)/(hi-lo)))*span;
          const [dx,dy] = ramp.amount && ditherAt ? ditherAt(x,y) : [x,y];
          index = Math.min(span, Math.max(0,Math.round(step + (pixel.bayerRank(dx,dy)-.5)*ramp.amount)));
        }
        const color = ramp.packed[index];
        rgb[q] = color>>16;
        rgb[q+1] = (color>>8)&255;
        rgb[q+2] = color&255;
        if (mask) mask[p] = symbols[kind];
        changed = true;
        break;
      }
    }
    if (mask) frame.effectPaletteMask = mask;
    if (!changed) return frame;
    const counts = new Map(Array.from(frame.palette ?? palette, color => [color,0]));
    for (let q=0;q<rgb.length;q+=3) {
      const color = rgb[q]*65536 + rgb[q+1]*256 + rgb[q+2];
      counts.set(color, (counts.get(color) ?? 0)+1);
    }
    return { ...frame, palette:[...counts.keys()], use:Uint32Array.from(counts.values()) };
  }
  return Object.freeze({ prepare, activate, apply, kinds });
})();
if (typeof module !== 'undefined') module.exports = EffectPalettes;

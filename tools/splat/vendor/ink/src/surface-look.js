/* View-dependent surface finishes for splats. The shader works on a surface sample
   in world space and is shared by the software renderer and script bundle. */
const SurfaceLook = (() => {
  const optics = typeof SceneOptics === 'undefined' ? require('./scene-optics.js') : SceneOptics;
  const effects = typeof SplatEffects === 'undefined' ? require('./splat-effects.js') : SplatEffects;
  const pixelLook = typeof PixelLook === 'undefined' ? require('./pixel-look.js') : PixelLook;
  let luts, stacks;
  try {
    luts = ColorLUT;
    stacks = ColorStack;
  } catch {
    luts = require('./color-lut.js');
    stacks = require('./color-stack.js');
  }
  const STRIDE = 8; // binding ID (one-based), normal XYZ, visibility, optional tangent XYZ
  const AXES = { x: [1, 0, 0], y: [0, 1, 0], z: [0, 0, 1] };
  const WHITE = [1, 1, 1];
  const TAU = Math.PI * 2;
  const clamp = n => Math.min(1, Math.max(0, n));
  const mix = (a, b, t) => a + (b - a) * t;
  const unit = (v, fallback = AXES.y) => {
    const length = Math.hypot(...v);
    return length > 1e-8 ? v.map(n => n / length) : fallback;
  };
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const vector = (v, fallback = AXES.x) => {
    if (typeof v === 'string' && Object.hasOwn(AXES, v)) return AXES[v];
    if (Array.isArray(v) && v.length === 3 && v.every(Number.isFinite)) return v;
    return fallback;
  };
  const smooth = (low, high, x) => {
    const t = clamp((x - low) / Math.max(1e-8, high - low));
    return t * t * (3 - 2 * t);
  };
  const fract = x => x - Math.floor(x);
  const positive = (v, fallback) => Math.max(0.001, v ?? fallback);
  const bell = (x, width) => Math.exp(-((x / width) ** 2));

  function prepareLightTrack(keys) {
    if (!Array.isArray(keys) || !keys.length) throw new TypeError('Expected surface light keys [time, x, y, z]');
    const frames = Array.from(keys, (key, i) => {
      if (!Array.isArray(key) || key.length !== 4 || !Array.from(key).every(Number.isFinite) ||
          key[0] < 0 || (i > 0 && key[0] <= keys[i - 1][0]))
        throw new RangeError('Surface light keys need finite values and strictly increasing nonnegative times');
      const direction = key.slice(1);
      const length = Math.hypot(...direction);
      if (length < 1e-8 || !Number.isFinite(length)) throw new RangeError('Surface light directions must be nonzero');
      return { time: key[0], direction: unit(direction) };
    });
    return time => {
      const first = frames[0], last = frames.at(-1);
      if (time <= first.time) return first.direction.slice();
      if (time >= last.time) return last.direction.slice();
      const i = frames.findIndex(frame => frame.time >= time);
      const a = frames[i - 1], b = frames[i];
      const fraction = smooth(0, 1, (time - a.time) / (b.time - a.time));
      const similarity = Math.min(1, Math.max(-1, dot(a.direction, b.direction)));
      const tangent = b.direction.map((value, axis) => value - a.direction[axis] * similarity);
      if (similarity > 0.9999) return unit(a.direction.map((value, axis) => mix(value, b.direction[axis], fraction)));
      // Opposite keys can turn through either half-circle. Pick a stable perpendicular.
      const axis = Math.abs(a.direction[1]) < 0.9 ? AXES.y : AXES.x;
      const perpendicular = unit(tangent, unit(cross(a.direction, axis)));
      const angle = Math.acos(similarity) * fraction;
      return a.direction.map((value, axis) => value * Math.cos(angle) + perpendicular[axis] * Math.sin(angle));
    };
  }

  function hash(x, y, z, key) {
    let n = Math.imul(x, 374761393) ^ Math.imul(y, 668265263) ^ Math.imul(z, 1442695041) ^ Math.imul(key, 1013904223);
    n = Math.imul(n ^ (n >>> 13), 1274126177);
    return ((n ^ (n >>> 16)) >>> 0) / 4294967296;
  }

  function noise(p, scale, seed) {
    const [x, y, z] = p.map(v => v / scale);
    const [i, j, k] = [Math.floor(x), Math.floor(y), Math.floor(z)];
    const [a, b, c] = [x, y, z].map(v => smooth(0, 1, fract(v)));
    const row = (dy, dz) => mix(hash(i, j + dy, k + dz, seed), hash(i + 1, j + dy, k + dz, seed), a);
    return mix(mix(row(0, 0), row(1, 0), b), mix(row(0, 1), row(1, 1), b), c);
  }

  const isRecord = v => v && Object.getPrototypeOf(v) === Object.prototype;
  function merge(base, changes) {
    const a = isRecord(base) ? base : {};
    const b = isRecord(changes) ? changes : {};
    return Object.fromEntries(
      [...new Set([...Object.keys(a), ...Object.keys(b)])].map(key => {
        const value = Object.hasOwn(b, key) ? b[key] : a[key];
        if (key === 'lut' && (b.type ?? a.type) === 'colorLut') return [key, luts.normalize(value)];
        if (key === 'stack' && (b.type ?? a.type) === 'colorStack') return [key, stacks.normalize(value)];
        return [key, isRecord(value) ? merge(a[key], value) : Array.isArray(value) ? value.slice() : value];
      })
    );
  }

  function color(value, palette, fallback = WHITE) {
    if (value === undefined) return fallback;
    if (Array.isArray(value) && value.length === 3 && value.every(Number.isFinite)) return value.map(clamp);
    if (typeof value === 'string' && /^#[\da-f]{6}$/i.test(value)) value = parseInt(value.slice(1), 16);
    else if (Number.isInteger(value)) value = palette[value];
    else throw new TypeError('Expected a palette index, #rrggbb or RGB triple for a surface colour');
    if (!Number.isInteger(value)) throw new RangeError('Surface colour is outside the palette');
    return [((value >> 16) & 255) / 255, ((value >> 8) & 255) / 255, (value & 255) / 255];
  }

  function material(base, settings) {
    const source = Array.isArray(base) ? { r: base } : base;
    return Object.assign({}, source, { surface: merge(source?.surface, settings) });
  }

  function maskAt(mask, p, seed, position, frame) {
    if (!mask) return 1;
    if (typeof mask === 'function') {
      const coverage = mask(position[0], position[1], position[2], frame);
      if (!Number.isFinite(coverage)) throw new TypeError('Surface mask must return a finite number');
      return clamp(coverage);
    }
    const scale = positive(mask.scale, 0.2);
    let weight;
    switch (mask.type) {
      case 'noise':
        weight = smooth(mask.low ?? 0.25, mask.high ?? 0.75, noise(p, scale, seed + (mask.seed || 0)));
        break;
      case 'stripes': {
        const phase = fract(dot(p, vector(mask.axis)) / scale + (mask.phase || 0));
        const edge = Math.abs(phase - 0.5) * 2;
        const width = clamp(mask.width ?? 0.45);
        weight = 1 - smooth(width, width + (mask.feather ?? 0.12), edge);
        break;
      }
      case 'checker': {
        const a = Math.floor(dot(p, vector(mask.axis)) / scale);
        const b = Math.floor(dot(p, vector(mask.cross, AXES.y)) / scale);
        weight = (a + b) & 1;
        break;
      }
      default:
        throw new RangeError('Unknown surface mask: ' + mask.type);
    }
    return mask.invert ? 1 - weight : weight;
  }

  function weatherMask(mask) {
    const { channel = 'wetness', low = 0, high = 1, invert = false } = mask;
    if (!['wetness', 'standingWater', 'snow', 'frost'].includes(channel) || !Number.isFinite(low) || !Number.isFinite(high) ||
        low < 0 || high <= low || typeof invert !== 'boolean')
      throw new RangeError('Weather masks need wetness, standingWater, snow or frost and increasing nonnegative bounds');
    return sample => {
      const [x,,z] = sample.worldPosition ?? sample.position;
      const value = sample.weather?.(x, z)?.[channel];
      if (!Number.isFinite(value)) return 0;
      const coverage = smooth(low, high, value);
      return invert ? 1 - coverage : coverage;
    };
  }

  function rainMask(mask) {
    const { receiver, channel = 'splash' } = mask;
    if (typeof receiver !== 'string' || !receiver.trim() || !['splash','runoff'].includes(channel))
      throw new RangeError('Rain impact masks need a receiver ID and splash or runoff channel');
    return sample => sample.rain?.mask(receiver, channel, sample.worldPosition ?? sample.position) ?? 0;
  }

  function directionAt(direction, p, normal) {
    if (typeof direction === 'function') return vector(direction(p, normal));
    if (direction?.type === 'circular') {
      return cross(vector(direction.axis, AXES.y), p);
    }
    if (direction?.type === 'weave') {
      const scale = positive(direction.scale, 0.2);
      const a = vector(direction.along),
        b = vector(direction.across, AXES.y);
      return (Math.floor(dot(a, p) / scale) + Math.floor(dot(b, p) / scale)) & 1 ? a : b;
    }
    return vector(direction);
  }

  function tangent(direction, n) {
    const projection = dot(direction, n);
    const t = direction.map((v, i) => v - n[i] * projection);
    const fallback = Math.abs(n[0]) < 0.8 ? AXES.x : AXES.y;
    return unit(t, unit(cross(fallback, n)));
  }

  function bump(settings, n, t, b, p, time, footprint, seed) {
    if (settings?.type === 'rings' && typeof settings.sample === 'function') {
      const slope = settings.sample(p, time, footprint);
      return unit(
        n.map((value, i) => value + slope[i]),
        n
      );
    }
    if (!settings?.amplitude) return n;
    const scale = positive(settings.scale, 0.3);
    const amp = settings.amplitude * (1 - smooth(scale * 0.35, scale * 0.85, footprint));
    if (!amp) return n;
    const u = dot(p, vector(settings.axis)) / scale;
    const v = dot(p, vector(settings.cross, AXES.z)) / scale;
    const phase = time * (settings.speed ?? 0);
    const a = settings.type === 'noise' ? 2 * noise(p, scale, seed) - 1 : Math.sin(TAU * (u + v * 0.23) + phase);
    const c =
      settings.type === 'noise' ? 2 * noise(p, scale, seed + 1) - 1 : Math.sin(TAU * (v - u * 0.33) - phase * 0.7);
    return unit(
      n.map((value, i) => value + amp * (t[i] * a + b[i] * c)),
      n
    );
  }

  function fresnel(cosine, f0, power = 5) {
    return f0 + (1 - f0) * (1 - clamp(cosine)) ** power;
  }

  const models = {
    specular(layer, q) {
      const { nt, ht, hb, nl, light } = q;
      if (nl <= 0 || nt <= 0 || light <= 0) return 0;
      return bell(ht / nt, layer.roughness[0]) * bell(hb / nt, layer.roughness[1]) * light;
    },
    fiber(layer, q) {
      const tilt =
        (layer.figure || 0) * Math.sin((dot(q.p, vector(layer.axis, AXES.y)) * TAU) / positive(layer.scale, 0.5));
      const alignment = q.ht + tilt * q.nt - (layer.shift || 0);
      return bell(alignment, layer.roughness[0]) * Math.sqrt(clamp(q.nl * 2)) * q.light;
    },
    reflection(layer, q, col) {
      const source = q.skyReflectionSource ?? layer.source;
      const scene = source === 'scene' && q.sky;
      if (!scene || q.skyOverlay) {
        // A compact three-colour environment reflected in the sample normal.
        const up = q.n[1] * 2 * q.nv - q.v[1];
        const tint = up < 0 ? layer.ground : layer.sky;
        const blend = smooth(0, 0.8, Math.abs(up));
        for (let i = 0; i < 3; i++) col[i] = mix(layer.horizon[i], tint[i], blend);
      }
      if (scene) {
        const normal = q.skyNormal ? unit(q.skyNormal(q.n), q.n) : q.n;
        const view = q.skyView ? unit(q.skyView, normal) : q.v;
        const twice = 2 * dot(normal, view);
        q.sky(normal.map((v, i) => twice * v - view[i]), col);
      }
      return fresnel(q.nv, layer.f0 ?? 0.04, layer.power ?? 5) * (scene ? q.skyAccess : 1);
    },
    planarReflection(layer, q, col) {
      const reflected = q.reflection?.(layer, q.n, q.geometricNormal);
      if (!reflected) return 0;
      for (let i = 0; i < 3; i++) col[i] *= reflected.rgb[i];
      return reflected.coverage * fresnel(q.nv, layer.f0 ?? 0.04, layer.power ?? 5);
    },
    sheen(layer, q) {
      const directional = clamp(layer.directional ?? 0);
      return (1 - q.nv) ** (layer.power ?? 2) * mix(1, Math.abs(q.vt), directional);
    },
    film(layer, q, col) {
      const ior = positive(layer.ior, 1.45);
      const cosine = clamp(mix(q.nv, Math.abs(q.vt), layer.axisBias ?? 0));
      const refracted = Math.sqrt(Math.max(0, 1 - (1 - cosine * cosine) / (ior * ior)));
      const thickness =
        (layer.thickness ?? 400) + (layer.variation || 0) * (noise(q.p, positive(layer.scale, 0.35), q.seed) * 2 - 1);
      const path = 2 * ior * thickness * refracted;
      if (layer.colors.length > 1) {
        const u = fract(path / positive(layer.period, 530)) * layer.colors.length;
        const index = Math.floor(u);
        const a = layer.colors[index],
          b = layer.colors[(index + 1) % layer.colors.length];
        for (let i = 0; i < 3; i++) col[i] = mix(a[i], b[i], fract(u));
      } else {
        const contrast = clamp(layer.contrast ?? 0.85);
        for (let i = 0; i < 3; i++) {
          const wave = i === 0 ? 635 : i === 1 ? 530 : 460;
          col[i] = 1 - contrast * (0.5 + 0.5 * Math.cos((TAU * path) / wave));
        }
      }
      const flash = layer.flash ? bell(1 - q.nt, positive(layer.flash, 0.12)) * q.light : 1;
      return fresnel(cosine, layer.f0 ?? 0.25, layer.power ?? 3) * flash;
    },
    diffraction(layer, q, col) {
      if (q.nl <= 0) return 0;
      // The grooves run along T. Only the component across them splits into colours.
      const wavelength = (Math.abs(q.vb + q.lb) * positive(layer.spacing, 1200)) / positive(layer.order, 1);
      const width = positive(layer.bandwidth, 40);
      col[0] = bell(wavelength - 620, width);
      col[1] = bell(wavelength - 530, width);
      col[2] = bell(wavelength - 450, width);
      const peak = Math.max(...col);
      if (peak < 0.004) return 0;
      for (let i = 0; i < 3; i++) col[i] /= peak;
      return peak * bell(q.vt + q.lt, layer.roughness[0]) * q.light;
    },
    directionalColor(layer, q, col) {
      const angle = Math.abs(q.vt) - Math.abs(q.vb);
      const t = smooth(-positive(layer.width, 0.4), positive(layer.width, 0.4), angle + (layer.bias || 0));
      for (let i = 0; i < 3; i++) col[i] = mix(layer.crossColor[i], layer.color[i], t);
      return 1;
    },
    glints(layer, q, col) {
      if (q.nl <= 0 || q.nt <= 0) return 0;
      const cell = positive(layer.scale, 0.12),
        radius = clamp(layer.radius ?? 0.37);
      const p = q.p.map(value => value / cell);
      const [x, y, z] = p.map(Math.floor);
      const hashAt = salt => hash(x, y, z, q.seed + (layer.seed || 0) + salt);
      if (hashAt(17) >= clamp(layer.density ?? 0.45)) return 0;
      const reach = Math.min(0.44, Math.max(radius, (q.footprint / cell) * 0.45));
      const distance = Math.hypot(...p.map((v, i) => fract(v) - mix(0.45, 0.55, hashAt(i + 3))));
      const shape = 1 - smooth(reach * 0.5, reach, distance);
      if (shape <= 0) return 0;
      const tilt = layer.tilt ?? 0.5;
      const ht = q.ht / q.nt - (hashAt(25) * 2 - 1) * tilt;
      const hb = q.hb / q.nt - (hashAt(41) * 2 - 1) * tilt;
      const band = bell(ht, layer.roughness[0]) * bell(hb, layer.roughness[1]);
      if (layer.colors.length) {
        const choice = layer.colors[Math.floor(hashAt(61) * layer.colors.length)];
        for (let i = 0; i < 3; i++) col[i] = choice[i];
      }
      const filter = Math.min(1, (radius * cell) / Math.max(1e-6, q.footprint * 0.5)) ** 2;
      return (shape * band) ** positive(layer.response, 0.65) * filter * q.light;
    }
  };

  function numeric(object, fields, label) {
    for (const field of fields) {
      if (object[field] !== undefined && !Number.isFinite(object[field]))
        throw new TypeError(label + '.' + field + ' must be a number');
    }
  }

  function prepare(settings, palette = [], lightDirection = [-0.55, 0.72, 0.43], context = {},
    { colorCurves = true, colorLut = true, colorStack = true, paletteConstraints = true, paletteRoles, blueNoise, onPaletteClip,
      validateOnly = false } = {}) {
    if (!isRecord(settings)) throw new TypeError('Surface settings must be an object');
    if (validateOnly && settings.renderStages !== undefined) {
      const stages = typeof RenderStages === 'undefined' ? require('./render-stages.js') : RenderStages;
      stages.prepare(settings.renderStages, { palette, roles: paletteRoles, blueNoise, context, validateOnly });
    }
    numeric(settings, ['scale', 'seed', 'steps'], 'surface');
    if (settings.rainRipple !== undefined && (typeof settings.rainRipple !== 'string' || !settings.rainRipple.trim()))
      throw new TypeError('Surface rainRipple must be a water receiver ID');
    if (settings.layers !== undefined && !isRecord(settings.layers))
      throw new TypeError('Surface layers must be named in an object');
    if (
      settings.origin !== undefined &&
      (!Array.isArray(settings.origin) || settings.origin.length !== 3 || !settings.origin.every(Number.isFinite))
    )
      throw new TypeError('Surface origin must be an XYZ position');
    if (settings.opacity) {
      if (!isRecord(settings.opacity)) throw new TypeError('Surface opacity must be an object');
      numeric(settings.opacity, ['facing', 'grazing', 'power'], 'surface.opacity');
    }
    let normal = settings.normal;
    if (settings.normal) {
      if (!isRecord(settings.normal)) throw new TypeError('Surface normal variation must be an object');
      numeric(settings.normal, ['amplitude', 'scale', 'speed'], 'surface.normal');
      if (settings.normal.type && !['noise', 'waves', 'rings'].includes(settings.normal.type))
        throw new RangeError('Unknown surface normal pattern: ' + settings.normal.type);
      if (settings.normal.type === 'rings' && typeof settings.normal.sample !== 'function') {
        numeric(settings.normal, ['width', 'damping'], 'surface.normal');
        if (!Array.isArray(settings.normal.drops) || settings.normal.drops.length > 64)
          throw new TypeError('Ripple rings need a list of up to 64 drops');
        for (const drop of settings.normal.drops) {
          if (!isRecord(drop) || !Array.isArray(drop.at) || drop.at.length !== 3 || !drop.at.every(Number.isFinite))
            throw new TypeError('Each ripple drop needs a finite XYZ position');
          numeric(drop, ['start', 'repeat', 'strength'], 'ripple drop');
          if (drop.repeat !== undefined && drop.repeat <= 0) throw new RangeError('Ripple repeat must be positive');
        }
        const scale = positive(normal.scale, 0.3);
        normal = {
          type: 'rings',
          sample: optics.ringSampler(() => settings.normal.drops, {
            along: unit(vector(normal.axis)),
            across: unit(vector(normal.cross, AXES.z)),
            amplitude: normal.amplitude || 0,
            scale,
            speed: positive(normal.speed, 1),
            width: positive(normal.width, scale * 2.5),
            damping: Math.max(0, normal.damping ?? 0.3)
          })
        };
      }
    }
    const layers = Object.entries(settings.layers || {})
      .filter(([, layer]) => layer && layer.strength !== 0 &&
        (colorCurves || layer.type !== 'colorCurve') && (colorLut || layer.type !== 'colorLut') &&
        (colorStack || layer.type !== 'colorStack'))
      .map(([id, layer]) => {
        const colorLayer = ['projected', 'colorCurve', 'colorLut', 'colorStack'].includes(layer.type);
        if (!colorLayer && !Object.hasOwn(models, layer.type))
          throw new RangeError('Unknown surface layer: ' + layer.type);
        numeric(
          layer,
          [
            'strength',
            'steps',
            'rotation',
            'scale',
            'power',
            'f0',
            'directional',
            'seed',
            'shift',
            'figure',
            'ior',
            'thickness',
            'variation',
            'period',
            'contrast',
            'flash',
            'axisBias',
            'spacing',
            'order',
            'bandwidth',
            'width',
            'bias',
            'density',
            'radius',
            'tilt',
            'response',
            'distortion',
            'blur'
          ],
          id
        );
        if (layer.type === 'reflection' && layer.source !== undefined && !['scene', 'material'].includes(layer.source))
          throw new RangeError(id + '.source must be scene or material');
        if (layer.type === 'planarReflection') {
          if (typeof layer.plane !== 'string' || !layer.plane.trim())
            throw new TypeError(id + '.plane must be a reflection plane ID');
          if ((layer.blur ?? 0) < 0 || (layer.distortion ?? 0) < 0)
            throw new RangeError(id + ' needs nonnegative blur and distortion');
        }
        const fieldMask = layer.mask?.type === 'field' ? effects.fieldMask(layer.mask, context) : null;
        const spatialMask = layer.mask?.type === 'weather' ? weatherMask(layer.mask) :
          layer.mask?.type === 'rainImpact' ? rainMask(layer.mask) :
          ['axis', 'texture', 'query'].includes(layer.mask?.type)
          ? effects.prepareMask(layer.mask, context, { validateOnly }) : fieldMask;
        if (layer.mask && typeof layer.mask !== 'function' && !spatialMask) {
          if (!isRecord(layer.mask)) throw new TypeError(id + '.mask must be an object');
          if (!['noise', 'stripes', 'checker'].includes(layer.mask.type))
            throw new RangeError('Unknown surface mask: ' + layer.mask.type);
          numeric(layer.mask, ['scale', 'low', 'high', 'seed', 'phase', 'width', 'feather'], id + '.mask');
        }
        if (colorLayer) {
          const blend = layer.blend ?? 'mix';
          if (!['mix', 'add', 'multiply'].includes(blend)) throw new RangeError('Unknown surface color blend: ' + blend);
          const resolveColor = value => color(value, palette);
          let effect;
          if (layer.type === 'colorLut' || layer.type === 'colorStack') effect = effects[layer.type](layer, resolveColor);
          else effect = (layer.type === 'projected' ? effects.layer : effects.colorCurve)(layer, context, resolveColor);
          return { ...layer, id, blend, strength: clamp(layer.strength ?? 1), effect, spatialMask };
        }
        if (layer.colors !== undefined && !Array.isArray(layer.colors))
          throw new TypeError(id + '.colors must be a list');
        if (
          layer.roughness !== undefined &&
          !Number.isFinite(layer.roughness) &&
          !(Array.isArray(layer.roughness) && layer.roughness.length === 2 && layer.roughness.every(Number.isFinite))
        ) {
          throw new TypeError(id + '.roughness must be a number or an along/across pair');
        }
        const roughness = Array.isArray(layer.roughness) ? layer.roughness : [layer.roughness, layer.roughness];
        return {
          ...layer,
          id,
          spatialMask,
          model: models[layer.type],
          strength: clamp(layer.strength ?? 1),
          roughness: [roughness[0], roughness[1] ?? roughness[0]].map(v =>
            positive(v, layer.type === 'glints' ? 0.085 : 0.22)
          ),
          color: color(layer.color, palette),
          crossColor: color(layer.crossColor, palette),
          colors: (layer.colors || []).map(c => color(c, palette)),
          sky: color(layer.sky, palette, [0.6, 0.78, 0.97]),
          horizon: color(layer.horizon, palette, [0.86, 0.91, 0.97]),
          ground: color(layer.ground, palette, [0.21, 0.23, 0.28]),
          cosine: Math.cos(layer.rotation || 0),
          sine: Math.sin(layer.rotation || 0)
        };
      });
    return {
      settings, normal, layers, sun: unit(vector(lightDirection, AXES.y)),
      paletteConstraint: paletteConstraints && settings.paletteConstraint !== undefined
        ? pixelLook.prepareLookPolicy(settings.paletteConstraint, { palette, roles: paletteRoles, blueNoise, context, validateOnly, onPaletteClip,
          skipMaskedStacks: !colorStack }) : null,
      projected: Boolean(settings.rainRipple) || layers.some(layer => layer.effect || layer.spatialMask),
      depth: layers.some(layer => layer.effect?.depth),
      reveals: layers.some(layer => layer.effect?.reveals)
    };
  }

  /* Inputs are RGB in 0..1 and a world-space sample. Output packs RGB, the opacity
     multiplier, a glint mask and, for projected paint, an optional local palette.
     Supply a normal Array when you want to retain the palette reference. */
  function shade(prepared, sample, base, output = [0, 0, 0, 1, 0], trace, visit, onClip, reflected) {
    const { settings, layers } = prepared;
    const sun = sample.lightDirection ?? prepared.sun;
    const { position, normal, view } = sample;
    const origin = settings.origin || [0, 0, 0],
      scale = positive(settings.scale, 1);
    const p = position.map((v, i) => (v - origin[i]) / scale);
    const footprint = (sample.footprint || 0) / scale;
    const seed = settings.seed || 0;
    let n = unit(normal),
      t = tangent(sample.tangent ?? directionAt(settings.direction, p, n), n);
    const geometricNormal = n, geometricTangent = t;
    n = bump(prepared.normal, n, t, cross(n, t), p, sample.time || 0, footprint, seed);
    if (settings.rainRipple && sample.rainSlope) n = unit(n.map((value, i) => value + sample.rainSlope[i]), n);
    t = tangent(t, n);
    const b = cross(n, t),
      v = unit(view, n),
      half = unit(
        v.map((value, i) => value + sun[i]),
        n
      );
    const visibility = clamp(sample.visibility ?? 1);
    const nv = clamp(dot(n, v));
    const shading = {
      p,
      n,
      v,
      nv,
      footprint,
      seed,
      geometricNormal,
      reflection: sample.reflection,
      sky: sample.sky, skyOverlay: sample.skyOverlay, skyReflectionSource: sample.skyReflectionSource,
      skyNormal: sample.skyNormal, skyView: sample.skyView, skyAccess: sample.skyAccess ?? 1,
      nt: dot(n, half),
      nl: dot(n, sun),
      light: visibility
    };
    const tx = dot(t, half),
      bx = dot(b, half),
      tv = dot(t, v),
      bv = dot(b, v);
    const tl = dot(t, sun),
      bl = dot(b, sun);
    const rgb = [0, 0, 0];
    reflected?.fill(0);
    for (let i = 0; i < 3; i++) output[i] = base[i];
    output[3] = settings.opacity
      ? clamp(
          mix(settings.opacity.facing ?? 1, settings.opacity.grazing ?? 1, (1 - nv) ** (settings.opacity.power ?? 3))
        )
      : 1;
    output[4] = 0;
    if (prepared.projected || output.length > 5) output[5] = undefined;
    let maskFrame;
    for (const layer of layers) {
      if (typeof layer.mask === 'function' && !maskFrame) maskFrame = {
        normal: geometricNormal, tangent: geometricTangent, bitangent: cross(geometricNormal, geometricTangent),
        footprint: sample.footprint || 0, time: sample.time || 0
      };
      const maskWeight = layer.spatialMask ? layer.spatialMask(sample) : maskAt(layer.mask, p, seed, position, maskFrame);
      const strength = layer.strength * maskWeight;
      const step = trace && layer.effect && { layer: layer.id, type: layer.type,
        ...(layer.stack?.name && { stack: layer.stack.name }), maskWeight, input: output.slice(0, 3) };
      if (step) trace.push(step);
      if (!strength) {
        if (step) Object.assign(step, { applied: false, effectiveWeight: 0, output: step.input });
        continue;
      }
      if (layer.effect) {
        const result = layer.effect.sample(sample, output);
        const amount = clamp(result[3] * strength);
        if (!amount && layer.type === 'colorCurve') {
          if (step) Object.assign(step, { applied: false, effectiveWeight: 0, output: step.input });
          continue;
        }
        output[3] *= mix(1, clamp(result[4]), strength);
        output[4] = Math.max(output[4], clamp(result[5] * strength));
        if (amount >= 0.5) output[5] = layer.effect.palette;
        let clipped;
        for (let i = 0; i < 3; i++) {
          const next = layer.blend === 'add' ? output[i] + result[i] :
            layer.blend === 'multiply' ? output[i] * result[i] : result[i];
          const value = mix(output[i], next, amount);
          if (onClip && (value < 0 || value > 1)) (clipped ??= [0, 0, 0])[i] = value;
          output[i] = clamp(value);
          if (reflected && layer.blend !== 'add') reflected[i] *= mix(1, layer.blend === 'multiply' ? result[i] : 0, amount);
        }
        if (clipped) onClip(...clipped);
        if (step) Object.assign(step, { applied: amount > 0, effectiveWeight: amount, output: output.slice(0, 3) });
        if (amount && visit) visit(layer, layer.mask ? maskWeight : null, amount, settings);
        continue;
      }
      const { cosine: c, sine: s } = layer;
      shading.ht = tx * c + bx * s;
      shading.hb = bx * c - tx * s;
      shading.vt = tv * c + bv * s;
      shading.vb = bv * c - tv * s;
      shading.lt = tl * c + bl * s;
      shading.lb = bl * c - tl * s;
      shading.light = layer.shadow === false ? 1 : visibility;
      for (let i = 0; i < 3; i++) rgb[i] = layer.color[i];
      const weight = clamp(layer.model(layer, shading, rgb) * strength);
      if (layer.type === 'glints') output[4] = Math.max(output[4], weight);
      const steps = layer.steps ?? settings.steps ?? 0;
      const amount = steps > 1 ? Math.round(weight * steps) / steps : weight;
      for (let i = 0; i < 3; i++) output[i] = mix(output[i], rgb[i], amount);
      if (reflected && amount) {
        const reflection = layer.type === 'reflection' || layer.type === 'planarReflection';
        for (let i = 0; i < 3; i++) reflected[i] = mix(reflected[i], reflection ? rgb[i] : 0, amount);
      }
    }
    if (prepared.paletteConstraint) output[5] = prepared.paletteConstraint.swatches;
    return output;
  }

  return { STRIDE, material, merge, prepare, shade, prepareLightTrack };
})();
if (typeof module !== 'undefined') module.exports = SurfaceLook;

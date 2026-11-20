/* Front-to-back integration for a bounded density with optional single scattering. */
const VolumeLight = (() => {
  const clouds = typeof CloudField === 'undefined' ? require('./cloud-field.js') : CloudField;
  const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const vector = (value, name) => {
    if (!Array.isArray(value) || value.length !== 3 || !Array.from(value).every(Number.isFinite))
      throw new RangeError(name + ' expects a finite XYZ vector');
    return value.slice();
  };
  const number = (value, min, max, name) => {
    if (!Number.isFinite(value) || value < min || value > max) throw new RangeError(name + ' is out of range');
    return value;
  };

  function unit(value, name) {
    const direction = vector(value, name), length = Math.hypot(...direction);
    if (!length || !Number.isFinite(length)) throw new RangeError(name + ' must be nonzero with finite length');
    return direction.map(v => v / length);
  }

  function lighting(settings, color, palette, { time = 0, localLights = true, localShadows = true, celestialSun } = {}) {
    const { ambient = .35, sun, point, points = [], spots = [], shadow } = settings || {};
    if (shadow !== undefined && typeof shadow !== 'function') throw new TypeError('Atmosphere shadow must be a ray query');
    if (!Array.isArray(points) || !Array.isArray(spots)) throw new TypeError('Volume points and spots must be arrays');
    let directional = null, animatedLocals = false;
    if (sun) {
      directional = { direction: unit(celestialSun?.direction ?? sun.direction, 'Sun direction'), rgb: color(sun.color ?? '#fff3dc', palette),
        intensity: number(sun.intensity ?? .7, 0, 64, 'Sun intensity') * (celestialSun?.gain ?? 1),
        distance: number(sun.distance ?? 20, .001, 1000, 'Sun shadow distance') };
    }

    const atTime = value => {
      if (typeof value !== 'function') return value;
      animatedLocals = true;
      return value(time);
    };
    function local(light, name) {
      if (!light || typeof light !== 'object' || Array.isArray(light)) throw new TypeError(name + ' needs an object');
      const { castsShadow = true } = light;
      if (typeof castsShadow !== 'boolean') throw new TypeError(name + ' castsShadow must be boolean');
      return {
        at: vector(atTime(light.at), name + ' position'),
        rgb: color(light.color ?? '#ffd095', palette),
        intensity: number(atTime(light.intensity ?? 1), 0, 64, name + ' intensity'),
        radius: number(light.radius ?? 3, .001, 1000, name + ' radius'),
        castsShadow
      };
    }
    function spot(light) {
      const source = local(light, 'Spot light');
      const outer = number(light.outerAngle ?? 24, .01, 90, 'Spot outer angle');
      const inner = number(light.innerAngle ?? outer * .65, 0, outer, 'Spot inner angle');
      const radians = Math.PI / 180;
      return { ...source, direction: unit(atTime(light.direction), 'Spot direction'),
        innerCos: Math.cos(inner * radians), outerCos: Math.cos(outer * radians) };
    }
    const single = localLights && point ? local(point, 'Point light') : null;
    const locals = localLights ? [...Array.from(points, light => local(light, 'Point light')), ...Array.from(spots, spot)] : [];
    return { ambient: number(ambient, 0, 64, 'Ambient light'), sun: directional, point: single,
      locals, shadow, localShadows, animatedLocals };
  }

  function occluder(field, { bias = .025, step = .035, steps = 24, safety = .75 } = {}) {
    if (typeof field !== 'function' || !Number.isFinite(bias) || bias <= 0 || !Number.isFinite(step) || step <= 0 ||
        !Number.isSafeInteger(steps) || steps < 1 || steps > 256 || !Number.isFinite(safety) || safety <= 0 || safety > 1)
      throw new RangeError('Invalid density occluder settings');
    function hitDistance(x, y, z, direction, stop) {
      let distance = bias;
      for (let i = 0; i < steps && distance < stop; i++) {
        const d = field(x + direction[0] * distance, y + direction[1] * distance, z + direction[2] * distance);
        if (d < 0) return distance;
        distance += Math.max(step, d * safety);
      }
      return Infinity;
    }
    const hit = (x,y,z,direction,stop) => hitDistance(x,y,z,direction,stop) !== Infinity;
    hit.hitDistance = hitDistance;
    return hit;
  }

  function mediumColor(volume, density) {
    const { ramp, rgb } = volume;
    if (!ramp) return rgb;
    return ramp[Math.min(ramp.length - 1, Math.floor(density * ramp.length))];
  }

  const phase = (g, cosine) => (1 - g * g) / Math.pow(1 + g * g - 2 * g * cosine, 1.5);
  function illuminateLocal(light, output, x, y, z, direction, anisotropy, shadow) {
    if (!light.intensity) return;
    const dx = light.at[0] - x, dy = light.at[1] - y, dz = light.at[2] - z;
    const range = Math.hypot(dx, dy, dz);
    if (range >= light.radius || range <= 1e-6) return;
    const toLight = [dx / range, dy / range, dz / range];
    let weight = 1;
    if (light.direction) {
      const cosine = -dot(toLight, light.direction);
      if (cosine < light.outerCos) return;
      if (cosine < light.innerCos) {
        const u = (cosine - light.outerCos) / (light.innerCos - light.outerCos);
        weight = u * u * (3 - 2 * u);
      }
    }
    if (!weight) return;
    if (shadow && light.castsShadow !== false && shadow(x, y, z, toLight, range)) return;
    const scatter = anisotropy ? phase(anisotropy, dot(direction, toLight)) : 1;
    const amount = light.intensity * weight * (1 - range / light.radius) ** 2 * scatter;
    for (let i = 0; i < 3; i++) output[i] += light.rgb[i] * amount;
  }

  function addLocal(media, x, y, z, output, direction, anisotropy = 0) {
    const { point, locals, localShadows, shadow } = media;
    const localShadow = localShadows === false ? null : shadow;
    if (point) illuminateLocal(point, output, x, y, z, direction, anisotropy, localShadow);
    if (locals) for (const light of locals)
      illuminateLocal(light, output, x, y, z, direction, anisotropy, localShadow);
  }

  function illuminate(volume, output, x, y, z, direction, media, visibility) {
    const { ambient, sun, shadow } = media;
    output.fill(ambient);
    if (sun && sun.intensity && visibility && (!shadow || !shadow(x, y, z, sun.direction, sun.distance))) {
      const amount = sun.intensity * visibility * phase(volume.anisotropy, dot(direction, sun.direction));
      for (let i = 0; i < 3; i++) output[i] += sun.rgb[i] * amount;
    }
    addLocal(media, x, y, z, output, direction, volume.anisotropy);
  }

  function integrate(segments, origin, direction, stop, result, options = {}) {
    const { time = 0, media, maxSteps = 64, stepScale = 1, jitter = .5, skip = true, cloudShadow, flash, exposure, cutouts, counters } = options;
    const active = new Set(), rgb = [0, 0, 0], light = [1, 1, 1];
    result[0] = result[1] = result[2] = 0;
    result[3] = 1;
    let last = 0;
    const cloudVisibility = t => cloudShadow(origin[0] + t * direction[0], origin[1] + t * direction[1],
      origin[2] + t * direction[2]);
    function blend(density, length, gain = 1) {
      if (density <= 0) return;
      const alpha = -Math.expm1(-density * length * (options?.fogScale ?? 1));
      const contribution = result[3] * alpha / density;
      for (let k = 0; k < 3; k++) result[k] += contribution * rgb[k] * gain;
      result[3] *= 1 - alpha;
    }
    const entry = segments[0]?.[0] ?? 0;
    const exit=Math.min(stop,segments.at(-1)?.[0]??stop);
    const cutRay=exit>entry ? cutouts?.fog?.ray(origin,direction,entry,exit) : null;
    const exposureLength=exposure?.fogDistance && ((a,b)=>exposure.fogDistance(origin,direction,a,b));
    const effectiveLength = cutRay ? (a,b) => cutRay.distance(a,b,exposureLength) : exposureLength;
    const rateFloor = (exit - entry) / maxSteps;
    const hasField = segments.some(([, volume]) => volume.type === 'field' || volume.densityField);
    for (const [end, volume, sign] of segments) {
      if (hasField && result[3] < .001) break;
      if (active.size && end > last) {
        let minStep = flash ? flash.step * stepScale : Infinity;
        for (const v of active) {
          if (v.type === 'field') minStep = Math.min(minStep, v.step * stepScale);
          if (v.densityField) minStep = Math.min(minStep, v.densityField.step * stepScale);
        }
        if (minStep === Infinity) {
          let density = 0;
          rgb.fill(0);
          for (const v of active) {
            density += v.density;
            for (let k = 0; k < 3; k++) rgb[k] += v.density * v.rgb[k];
          }
          if (counters) counters.analyticSegments++;
          if (cloudShadow) {
            // Sample the changing light along the segment while keeping analytic extinction.
            const step = (end - last) / 4;
            for (let i = 0; i < 4; i++) {
              const length = effectiveLength?.(last+i*step,last+(i+1)*step) ?? step;
              blend(density, length, clouds.dim(cloudVisibility(last + (i + .5) * step)));
            }
          } else blend(density, effectiveLength?.(last,end) ?? end-last);
        } else {
          const step = Math.max(minStep, rateFloor);
          const volumes = [...active];
          const gaps = skip && volumes.some(v=>v.type === 'field' && v.field.skip) ? new Float64Array(volumes.length) : null;
          for (let t = last; t < end && (!hasField || result[3] >= .001);) {
            const distance = Math.min(end - t, step);
            if (t + distance === t) break;
            if (counters) counters.marchSteps++;
            if (gaps) {
              // Check occupancy before evaluating lighting, exposure, or cutout samplers.
              const x = origin[0]+t*direction[0], y = origin[1]+t*direction[1], z = origin[2]+t*direction[2];
              let empty = Infinity;
              for (let i=0;i<volumes.length;i++) {
                const v = volumes[i];
                let gap = 0;
                if (v.type === 'field' && v.field.skip) {
                  if (counters) counters.skipTests++;
                  gap = v.field.skip(x,y,z,direction,time);
                }
                gaps[i] = gap >= distance ? gap : 0;
                empty = Math.min(empty,gaps[i]);
              }
              if (empty >= distance) {
                const jump = empty > distance ? Math.min(end-t,Math.max(1,Math.floor(empty/step))*step) : distance;
                if (counters) counters.skippedSteps += Math.ceil(jump/step-1e-9);
                t += jump;
                continue;
              }
            }
            const depth = t + distance * jitter;
            const x = origin[0] + depth * direction[0], y = origin[1] + depth * direction[1], z = origin[2] + depth * direction[2];
            const visibility = cloudShadow?.(x, y, z) ?? 1;
            const gain = clouds.dim(visibility);
            const strike = flash?.light(x, y, z);
            const mist = (exposure?.fog?.(x,y,z) ?? 1) *
              (cutRay ? cutRay.distance(t,t+distance)/distance : 1);
            let density = 0;
            rgb.fill(0);
            for (let i=0;i<volumes.length;i++) {
              if (gaps?.[i] >= distance) continue;
              const v = volumes[i];
              if (counters && v.densityField) counters.densitySamples++;
              const localDensity = v.density * (v.densityField?.sample(x,z) ?? 1) * mist;
              if (v.type !== 'field') {
                density += localDensity;
                for (let k = 0; k < 3; k++) rgb[k] += localDensity * (v.rgb[k] * gain + .45 * (strike?.[k] ?? 0));
                continue;
              }
              if (counters) counters.densitySamples++;
              const value = v.field.sample(x, y, z, time, options);
              const extinction = value * localDensity;
              if (!extinction) continue;
              density += extinction;
              const base = mediumColor(v, value);
              if (v.lit && media) illuminate(v, light, x, y, z, direction, media, visibility * (exposure?.light?.(x,y,z) ?? 1));
              else light.fill(v.lit ? gain : 1);
              for (let k = 0; k < 3; k++)
                rgb[k] += extinction * (base[k] * light[k] + v.emissiveRgb[k] * v.emissiveGain + (v.lit ? .45 * (strike?.[k] ?? 0) : 0));
            }
            blend(density, distance);
            t += distance;
          }
        }
      }
      if (sign > 0) active.add(volume);
      else active.delete(volume);
      last = end;
    }
    return result;
  }

  function history({ weight = .55, depthTolerance = .08, maxGap = .14 } = {}) {
    number(weight, 0, .95, 'Volume history weight');
    number(depthTolerance, 0, 10, 'Volume history depth tolerance');
    number(maxGap, .001, 10, 'Volume history time gap');
    let last;
    return {
      filter(color, depth, time, key) {
        if (last && last.key === key && time > last.time && time - last.time <= maxGap && last.depth.length === depth.length) {
          for (let p = 0; p < depth.length; p++) {
            const dz = depth[p] === last.depth[p] ? 0 : Math.abs(depth[p] - last.depth[p]);
            // A sharp change in transmittance signals disocclusion or a fast density change.
            if (dz > depthTolerance || Math.abs(color[p * 4 + 3] - last.color[p * 4 + 3]) > .18) continue;
            for (let c = 0; c < 4; c++) {
              const i = p * 4 + c;
              color[i] += (last.color[i] - color[i]) * weight;
            }
          }
        }
        last = { time, key, depth: depth.slice(), color: color.slice() };
        return color;
      },
      clear() { last = undefined; }
    };
  }

  return Object.freeze({ lighting, addLocal, occluder, integrate, history });
})();
if (typeof module !== 'undefined') module.exports = VolumeLight;

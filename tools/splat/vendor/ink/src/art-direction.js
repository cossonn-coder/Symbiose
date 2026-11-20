/* Optional optical and timing controls shared by the native render paths. */
const ArtDirection = (() => {
  const presets = {
    'painted-pixel': { cloudEdge: .79, atmosphereBands: 6, foreground: { contrast: 1.19, pivot: .48 }, cadence: { scene: 12, environment: 12 } },
    'storm-silhouette': { cloudEdge: .96, atmosphereBands: 4, foreground: { contrast: 2.05, pivot: .61 }, cadence: { scene: 8, environment: 6 } },
    'soft-dawn': { cloudEdge: .17, atmosphereBands: 0, foreground: { contrast: .76, pivot: .49 }, cadence: { scene: 0, environment: 0 } }
  };
  const names = Object.freeze(Object.keys(presets));
  const clamp = (x, min = 0, max = 1) => Math.max(min, Math.min(max, x));
  const number = (x, min, max, name) => {
    if (!Number.isFinite(x) || x < min || x > max) throw new RangeError(name + ' is out of range');
    return x;
  };
  const record = (value, keys, name) => {
    if (!value || ![Object.prototype, null].includes(Object.getPrototypeOf(value)) ||
        Object.keys(value).some(key => !keys.includes(key))) throw new TypeError('Invalid ' + name + ' settings');
    return value;
  };

  function prepare(authored, override) {
    const source = override === true ? authored : override ?? authored;
    if (source == null || source === false) return null;
    const raw = typeof source === 'string' ? { preset: source } :
      record(source, ['preset','cloudEdge','atmosphereBands','foreground','cadence'],'art direction');
    const { preset } = raw;
    if (preset !== undefined && !Object.hasOwn(presets, preset)) throw new TypeError('Unknown art-direction preset ' + preset);
    const base = preset === undefined ? {} : presets[preset];
    const hardness = number(raw.cloudEdge ?? base.cloudEdge ?? .5, 0, 1, 'Cloud edge hardness');
    const count = raw.atmosphereBands ?? base.atmosphereBands ?? 0;
    if (!Number.isInteger(count) || (count !== 0 && (count < 2 || count > 64)))
      throw new RangeError('Atmosphere bands need zero or an integer from 2 to 64');
    const fg = raw.foreground === false ? {} : { ...base.foreground,
      ...record(raw.foreground ?? {}, ['contrast','pivot','near','far'], 'foreground') };
    const contrast = number(fg.contrast ?? 1, 0, 4, 'Foreground contrast');
    const pivot = number(fg.pivot ?? .5, 0, 1, 'Foreground contrast pivot');
    const near = number(fg.near ?? 10, 0, 1e6, 'Foreground near distance');
    const far = number(fg.far ?? 31, near, 1e6, 'Foreground far distance');
    if (far <= near) throw new RangeError('Foreground far must exceed near');
    const cadence = { ...base.cadence, ...record(raw.cadence ?? {}, ['scene','environment'], 'motion cadence') };
    const scene = number(cadence.scene ?? 0, 0, 240, 'Scene cadence');
    const environment = number(cadence.environment ?? 0, 0, 240, 'Environment cadence');
    const cloudEdge = hardness === .5 ? null : opacity => {
      if (opacity <= 0 || opacity >= 1) return opacity;
      if (hardness > .5) return clamp(.5 + (opacity-.5)*(1+(hardness-.5)*13));
      const soft = Math.acos(1-2*opacity)/Math.PI;
      return opacity + (soft-opacity)*(1-2*hardness);
    };
    const steps = count-1;
    const bands = count ? value => Math.round(clamp(value)*steps)/steps : null;
    function foreground(depth, r, g, b, out) {
      const w = clamp((far-depth)/(far-near)), amount = (contrast-1)*w*w*(3-2*w);
      return gradeContrast(r,g,b,amount,pivot,out);
    }
    return Object.freeze({ cloudEdge, bands, atmosphereBands:count, cloudHardness:hardness, foreground: contrast === 1 ? null : foreground,
      cadence: Object.freeze({ scene, environment }) });
  }

  function gradeContrast(r,g,b,amount,pivot,out) {
    const offset = (.30*r+.55*g+.15*b-pivot)*amount;
    out[0] = amount ? clamp(r+offset) : r;
    out[1] = amount ? clamp(g+offset) : g;
    out[2] = amount ? clamp(b+offset) : b;
    return out;
  }

  function time(settings, seconds, channel = 'scene') {
    const rate = settings?.cadence[channel];
    return rate ? Math.floor(seconds*rate+1e-8)/rate : seconds;
  }

  function remapOpacity(sample, curve) {
    const opacity = 1-sample[3];
    if (!(opacity > 0)) return sample;
    const mapped = curve(opacity), gain = mapped/opacity;
    for (let k = 0; k < 3; k++) sample[k] *= gain;
    sample[3] = 1-mapped;
    return sample;
  }

  return Object.freeze({ presets:names, prepare, time, remapOpacity, gradeContrast });
})();
if (typeof module !== 'undefined') module.exports = ArtDirection;

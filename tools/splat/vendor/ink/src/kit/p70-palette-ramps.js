/* Perceptual ramps in OKLab with chroma-preserving gamut adjustment in OKLCh. */
(function (K) {
  const P = K.procedural, TAU = 2 * Math.PI,
    clamp = n => Math.max(0, Math.min(1, n)),
    lerp = (a,b,t) => a + (b - a) * t,
    linear = n => n <= 0.04045 ? n / 12.92 : ((n + 0.055) / 1.055) ** 2.4,
    encoded = n => n <= 0.0031308 ? 12.92 * n : 1.055 * n ** (1 / 2.4) - 0.055;

  function parse(input) {
    if (Array.isArray(input) && input.length === 3 && input.every(v => Number.isFinite(v) && v >= 0 && v <= 1))
      return input.slice();
    const number = typeof input === 'string' && /^#[0-9a-f]{6}$/i.test(input) ? parseInt(input.slice(1), 16) : input;
    if (!Number.isSafeInteger(number) || number < 0 || number > 0xffffff)
      throw new Error('Palette ramp anchors need normalized RGB or six-digit hex colors');
    return [number >> 16,(number >> 8) & 255,number & 255].map(v => v / 255);
  }
  function lab(input) {
    const [r,g,b] = input.map(linear),
      l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b),
      m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b),
      s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
    return [
      0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
      1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
      0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s
    ];
  }
  function rgb([L,A,B], chroma = 1) {
    const a = A * chroma, b = B * chroma,
      l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3,
      m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3,
      s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
    return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
      -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
      -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s];
  }
  const inside = input => input.every(v => v >= -1e-8 && v <= 1 + 1e-8);
  function gamut(p) {
    let result = rgb(p);
    if (!inside(result)) {
      let low = 0, high = 1;
      result = rgb(p, low);
      for (let i = 0; i < 19; i++) {
        const middle = (low + high) * 0.5, candidate = rgb(p,middle);
        if (inside(candidate)) {
          low = middle;
          result = candidate;
        } else high = middle;
      }
    }
    return result.map(v => clamp(encoded(v)));
  }
  const toHex = ([r,g,b]) => (Math.round(r * 255) << 16) | (Math.round(g * 255) << 8) | Math.round(b * 255);
  function angle(a, b, mode) {
    const forward = ((b - a) % TAU + TAU) % TAU,
      backward = forward - TAU;
    if (forward < 1e-8) return 0;
    if (mode === 'increasing') return forward;
    if (mode === 'decreasing') return backward;
    if (mode === 'long') return forward >= Math.PI ? forward : backward;
    return forward <= Math.PI ? forward : backward;
  }

  function ramp(input, { steps = 7, space = 'lab', hue = 'short', interpolation = 'linear' } = {}) {
    if (!Array.isArray(input) || input.length < 2 || input.length > 64 ||
      !Number.isSafeInteger(steps) || steps < 2 || steps > 4096 ||
        !['lab','lch'].includes(space) || !['short','long','increasing','decreasing'].includes(hue) ||
        !ColorCurves.modes.includes(interpolation))
      throw new Error('Palette ramps need ordered anchors, steps and a perceptual interpolation mode');
    let previous = -1;
    const stops = input.map((entry, i) => {
      const object = entry && typeof entry === 'object' && !Array.isArray(entry), at = object ? entry.at : i / (input.length - 1),
        color = parse(object ? entry.color : entry);
      if (!Number.isFinite(at) || at < 0 || at > 1 || at <= previous) throw new Error('Palette stops must increase over zero to one');
      previous = at;
      const [L,a,b] = lab(color);
      return { at, color, lab: [L,a,b], lch: [L,Math.hypot(a,b),Math.atan2(b,a)] };
    });
    if (stops[0].at !== 0 || stops.at(-1).at !== 1) throw new Error('Palette ramp stops must include both endpoints');
    function sample(t) {
      if (!Number.isFinite(t)) throw new Error('Palette ramp coordinates must be finite');
      t = clamp(t);
      const high = ColorCurves.segmentIndex(stops, t), b = stops[high];
      if (b.at === t || high === 0) return b.color.slice();
      const a = stops[high - 1];
      if (interpolation === 'step') return a.color.slice();
      const w = ColorCurves.weight(interpolation, (t - a.at) / (b.at - a.at));
      if (space === 'lab') return gamut(a.lab.map((v,i) => lerp(v,b.lab[i],w)));
      const [L1,C1,H1] = a.lch, [L2,C2,H2] = b.lch,
        h1 = C1 < 1e-6 ? H2 : H1, h2 = C2 < 1e-6 ? H1 : H2,
        h = h1 + angle(h1,h2,hue) * w, c = lerp(C1,C2,w);
      return gamut([lerp(L1,L2,w), c * Math.cos(h), c * Math.sin(h)]);
    }
    const colors = Array.from({ length: steps }, (_, i) => sample(i / (steps - 1)));
    return P.data.freeze({ rgb: colors, hex: colors.map(toHex), sample });
  }

  P.materials.ramp = ramp;
  P.materials.colorCurves = ColorCurves;
})(KIT);

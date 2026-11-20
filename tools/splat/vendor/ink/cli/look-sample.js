const path = require('node:path');
const fs = require('node:fs');
const PNG = require('./png.js');
const Palette = require('./look-palette.js');

const normalized = packed => Palette.unpack(packed).map(byte => byte / 255);
const mix = (from, to, amount) => from.map((n, i) => n * (1 - amount) + to[i] * amount);

function chart() {
  const gray = Array.from({ length: 8 }, (_, i) => Array(3).fill(i / 7));
  const primaries = [[1, 0, 0], [1, .5, 0], [1, 1, 0], [0, 1, 0], [0, 1, 1], [0, 0, 1], [.5, 0, 1], [1, 0, 1]];
  return [
    ...gray, ...primaries.map(rgb => rgb.map(n => n * .35)), ...primaries,
    ...primaries.map(rgb => rgb.map(n => .65 + n * .35))
  ];
}

function vector(value, size, label) {
  if (value === undefined) return undefined;
  const result = value.split(',').map(part => part.trim() ? Number(part) : NaN);
  if (result.length !== size || !result.every(Number.isFinite)) throw new TypeError(label + ' needs ' + size + ' finite coordinates');
  return result;
}

function writeChart(file, samples, columns) {
  const cell = 48, row = 28, gap = 2;
  const w = columns * cell + gap, h = Math.ceil(samples.length / columns) * row + gap;
  const pixels = new Uint8Array(w * h * 3).fill(30);
  for (const [i, sample] of samples.entries()) {
    const left = i % columns * cell + gap, top = Math.floor(i / columns) * row + gap;
    const before = Palette.unpack(Palette.round(sample.input).color), after = Palette.unpack(Palette.round(sample.rgb).color);
    for (let y = top; y < top + row - gap; y++) {
      for (let x = 0; x < cell - gap; x++) {
        if (x !== (cell - gap) / 2) pixels.set(x < (cell - gap) / 2 ? before : after, (y * w + left + x) * 3);
      }
    }
  }
  fs.mkdirSync(path.dirname(path.resolve(file)), { recursive: true });
  PNG.write(file, w, h, pixels);
}

module.exports = function sample({ file, options, source, look, reference, kit, report, compile }) {
  const accepted = ['look', 'params', 'swatches', 'colors', 'chart', 'at', 'rest', 'pixel', 'out'];
  for (const [name, value] of Object.entries(options)) {
    if (!accepted.includes(name) || (name === 'chart' ? value !== true : typeof value !== 'string'))
      throw new TypeError('Invalid option --' + name + ' for look sample');
  }
  if (options.colors !== undefined && options.chart) throw new TypeError('Use --colors or --chart');
  const generated = options.colors === undefined;
  const colors = generated ? chart() : JSON.parse(options.colors);
  if (!Array.isArray(colors) || !colors.length || colors.length > 4096)
    throw new TypeError('--colors needs an array of 1 to 4096 hex swatches or RGB triples');
  const worldPosition = vector(options.at, 3, '--at'), position = vector(options.rest, 3, '--rest');
  const pixel = vector(options.pixel, 2, '--pixel') ?? [0, 0];
  if (!pixel.every(Number.isSafeInteger)) throw new TypeError('--pixel needs two integer art coordinates');

  const { PixelLook, SplatEffects, KIT } = kit;
  const refs = reference?.rows.map(row => row.color) ?? [];
  const stack = look.stage === 'palette' ? undefined : look.stack;
  const transfer = stack && compile(stack, reference, 'Indexed remaps need --swatches to supply the reference palette');
  const indexed = transfer?.requiresIndex ? refs.map(normalized) : null;
  const external = look.paletteFile?.rows.map(row => row.color);
  const policy = !external && look.palette && PixelLook.preparePalette(look.palette, {
    palette: refs, blueNoise: KIT.procedural.materials.blueNoise
  });
  const palette = policy?.packed ?? external;
  const candidates = external?.map(normalized);
  const mask = SplatEffects.prepareMask(look.mask, undefined, { validateOnly: true });
  const sceneMask = ['query', 'field'].includes(look.mask?.type);
  const havePoint = (look.mask?.space ?? (look.mask?.type === 'query' ? 'world' : 'rest')) === 'world' ? worldPosition : position;
  const maskWeight = mask ? !sceneMask && havePoint ? mask({ worldPosition, position, time: 0 }) : null : 1;
  const weight = look.weight ?? 1;
  const staged = look.stage !== undefined || look.order !== undefined || look.weight !== undefined;
  const rows = colors.map((value, i) => {
    const input = typeof value === 'string' && /^#[\da-f]{6}$/i.test(value) ? normalized(parseInt(value.slice(1), 16)) :
      Array.isArray(value) && value.length === 3 && value.every(Number.isFinite) ? value : null;
    if (!input) throw new TypeError('Color ' + (i + 1) + ' needs a six-digit hex swatch or a finite RGB triple');
    // Arbitrary RGB colors use the closest reference swatch when a look requires a palette index.
    const index = indexed ? PixelLook.nearest(input, indexed, false) : undefined;
    const transformed = transfer ? transfer.sample(input, undefined, index) : input;
    const amount = weight * (maskWeight ?? 1);
    const graded = staged ? mix(input, transformed, amount) : transformed;
    const slot = palette && (!staged || amount >= .5) ?
      policy ? policy.index(graded, ...pixel) : PixelLook.nearest(graded, candidates, false) : null;
    const resolved = slot == null ? graded : normalized(palette[slot]);
    const rgb = staged || !mask ? resolved : mix(input, resolved, amount);
    const swatch = slot != null && (staged || !mask || amount === 1) ? Palette.hex(palette[slot]) : null;
    return { input, transformed, rgb, swatch, ...(index !== undefined && { paletteIndex: index }) };
  });
  const columns = Math.min(8, rows.length);
  const output = { source, look: look.id ?? null, label: look.label, ...(look.stage && { stage: look.stage }),
    maskWeight, ...(sceneMask && { maskNeedsScene: true }),
    ...(palette && { palette: palette.map(Palette.hex) }), ...(generated && { chart: { columns, rows: 4 } }), samples: rows };
  if (options.out && /\.png$/i.test(options.out)) {
    if (path.resolve(options.out) === path.resolve(file)) throw new TypeError('--out needs a separate path');
    writeChart(options.out, rows, columns);
    return;
  }
  return report(output, options, file);
};

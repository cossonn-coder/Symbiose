const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const core = require('..');
const { ColorStack, PixelLook, SurfaceLook, KIT } = core.load();

const definition = (...steps) => ({ name: 'Test grade', steps });
const sample = (step, rgb) => ColorStack.prepare(definition(step)).sample(rgb);
function close(actual, expected) {
  assert(actual.every((value, i) => Math.abs(value - expected[i]) < 1e-12), `${actual} differs from ${expected}`);
}

test('exposure, contrast, saturation, hue and the RGB mixer have independent controls', () => {
  close(sample({ type: 'exposure', stops: 1 }, [.25, .5, 1]), [.5, 1, 2]);
  close(sample({ type: 'contrast', factor: 2, pivot: .25 }, [.125, .25, .5]), [0, .25, .75]);
  close(sample({ type: 'saturation', factor: 0 }, [1, 0, 1]), [.45, .45, .45]);
  close(sample({ type: 'hue', degrees: 120 }, [1, 0, 0]), [0, 1, 0]);
  close(sample({ type: 'hue', degrees: -120 }, [1, 0, 0]), [0, 0, 1]);
  close(sample({ type: 'hue', degrees: 60 }, [.3, .3, .3]), [.3, .3, .3]);
  close(sample({ type: 'channelMix', matrix: [[0, 0, 1], [0, 1, 0], [1, 0, 0]], offset: [.1, 0, -.1] },
    [.2, .4, .6]), [.7, .4, .1]);
});

test('ordered steps support edits, partial strength, and reversible overrange values', () => {
  const exposure = { id: 'expose', type: 'exposure', stops: 1 };
  const contrast = { id: 'contrast', type: 'contrast', factor: 2, pivot: .25 };
  const color = new Float64Array([.3, .3, .3]);
  const forward = ColorStack.prepare(definition(exposure, contrast));
  assert.equal(forward.sample(color, color), color);
  close(color, [.95, .95, .95]);
  close(ColorStack.prepare(definition(contrast, exposure)).sample([.3, .3, .3]), [.7, .7, .7]);
  close(ColorStack.prepare(definition(exposure, { ...exposure, id: 'undo', stops: -1 })).sample([.8, 1, .6]), [.8, 1, .6]);
  close(ColorStack.prepare(definition({ ...exposure, amount: .5 }, { ...contrast, enabled: false })).sample([.25, .5, 1]),
    [.375, .75, 1.5]);
  exposure.stops = -1;
  close(ColorStack.prepare(definition(exposure)).sample([1, .5, 0]), [.5, .25, 0]);
});

test('curves, LUTs, and slot remaps compose in order and keep protected entries locked', () => {
  const palette = [0, 0x400000, 0x406080, 0xffcc20];
  const roles = { stone: [1, 2], emblem: [3] };
  const lut = { size: 2, data: Array.from({ length: 8 }, (_, i) => [i >> 2 & 1, i >> 1 & 1, i & 1]).flat() };
  const exposure = { type: 'exposure', stops: -1 };
  const remap = { type: 'paletteRemap', amount: .5, remap: {
    rules: [{ from: 'stone.shadow', to: '#4080a0' }], protect: ['emblem']
  } };
  const curves = { type: 'curves', curves: { channels: { blue: { stops: [[0, 0], [1, .5]] } } } };
  const legacy = { rules: [{ from: 'emblem', to: '#ff00ff' }] };
  const grade = (...steps) => PixelLook.gradePalette(
    PixelLook.colorGrade(palette, roles, undefined, legacy, undefined, undefined, definition(...steps)));
  assert.equal(grade(exposure, remap, curves, { type: 'lut', lut })[1], 0x284030);
  assert.equal(grade(remap, exposure, curves, { type: 'lut', lut })[1], 0x142020);
  assert.equal(grade(remap, exposure)[3], 0xffcc20);
  assert.equal(grade({ ...remap, enabled: false }, exposure)[3], 0xff00ff);
  assert.throws(() => ColorStack.prepare(definition(remap)), /scene palette/);
});

test('stack definitions validate the name, ordered IDs, operation parameters, and surface scope', () => {
  const bad = [
    { type: 'unknown' }, { type: ['exposure'], stops: 1 }, { type: 'contrast', factor: -1 },
    { type: 'exposure', stops: 2048 }, { type: 'hue', degrees: 1, amount: -1 },
    { type: 'channelMix', matrix: [[1], [1], [1]] }, { type: 'curves', curves: false }, { type: 'lut' }
  ];
  for (const step of bad) assert.throws(() => ColorStack.prepare(definition(step)));
  const dupe = { id: 'same', type: 'exposure', stops: 1 };
  assert.throws(() => ColorStack.prepare(definition(dupe, dupe)), /distinct/);
  assert.throws(() => ColorStack.prepare({ name: '', steps: [] }), /name/);
  const invalid = { id: 'bad-stack', solids: [], finish: { look: { colorStack: definition(bad[0]) } } };
  assert(KIT.diorama.check(invalid).some(row => row.path === 'finish.look.colorStack'));
});

test('a material stack transforms its lit sample and can be bypassed', () => {
  const layer = { type: 'colorStack', strength: .5, outputPalette: ['#ff5599'],
    stack: definition({ type: 'hue', degrees: 120 }, { type: 'exposure', stops: -1 }) };
  const settings = SurfaceLook.material([0], { layers: { overlay: layer } }).surface;
  const point = { position: [0, 0, 0], normal: [0, 1, 0], view: [0, 1, 0] }, base = [1, 0, 0];
  const on = SurfaceLook.shade(SurfaceLook.prepare(settings), point, base);
  close(on.slice(0, 3), [.5, .25, 0]);
  assert.equal(PixelLook.gradePalette(on[5][0])[0], 0xff5599);
  const off = SurfaceLook.prepare(settings, [], undefined, {}, { colorStack: false });
  assert.deepEqual(SurfaceLook.shade(off, point, base).slice(0, 3), base);
});

test('an authored color stack and a CLI JSON override produce the same image', () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-color-stack-')), root = path.resolve(__dirname, '..');
  const cli = (...args) => execFileSync(process.execPath, [path.join(root, 'cli/ink-studio.js'), ...args],
    { cwd: temp, encoding: 'utf8' });
  try {
    const exported = execFileSync(process.execPath, ['-e',
      'const { ColorStack } = require(' + JSON.stringify(root) + ').load(); process.stdout.write(typeof ColorStack.prepare);'],
    { encoding: 'utf8' });
    assert.equal(exported, 'function');
    const stack = require('../examples/lantern-dusk.json'), spec = {
      id: 'stack-test', finish: { look: { colorStack: stack } },
      camera: { target: [0, .5, 0], dist: 4, pitch: .3 },
      solids: [{ kind: 'box', at: [0, .5, 0], half: [.5, .5, .5], mat: 'pale' }]
    };
    const scene = path.join(temp, 'scene.json');
    fs.writeFileSync(scene, JSON.stringify(spec));
    for (const [name, args] of [['authored', []], ['off', ['--color-stack', 'off']],
      ['override', ['--color-stack', path.join(root, 'examples/lantern-dusk.json')]]])
      cli('render', scene, '--w', '128', '--h', '96', '--out', path.join(temp, name + '.png'), ...args);
    const [authored, off, override] = ['authored', 'off', 'override'].map(name => fs.readFileSync(path.join(temp, name + '.png')));
    assert.deepEqual(override, authored);
    assert.notDeepEqual(off, authored);
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
});

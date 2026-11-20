const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const studio = require('../index.js');
const kit = studio.load(), { KIT, ColorStack } = kit;
const { assetPacks, looks } = KIT.authoring;
const pack = require('../examples/relay-look-pack.json');
const sampleWorld = require('../examples/look-prefabs.json');
const clay = { strength: .86, params: { shadow: '#4d2435', mid: '#ae5653', highlight: '#f4bc86' },
  palette: ['#4d2435', '#783747', '#ae5653', '#d48562', '#f4bc86'] };
const view = { w: 260, h: 180, ortho: true };

test('look assets bundle and revise through the versioned catalog', () => {
  const payload = JSON.stringify(assetPacks.bundle([pack], ['relay']));
  const installed = assetPacks.merge([], payload).packs;
  const catalog = assetPacks.create({ packs: installed });
  assert.equal(catalog.looks.length, 2);
  assert.equal(catalog.getLook('relay/blue-hour').revision, 1);
  const next = assetPacks.reviseLook(installed[0], 'relay/blue-hour', { label: 'Evening' });
  assert.equal(next.revision, 2);
  assert.equal(assetPacks.reviseLook(next, 'relay/blue-hour', { label: 'Evening' }).revision, 2);
  const updated = assetPacks.create({ packs: assetPacks.merge(installed, next).packs });
  assert.equal(updated.getLook('relay/blue-hour').look.label, 'Evening');
  assert.throws(() => looks.bind({ asset: 'relay/blue-hour', revision: 1 }, updated), /requires pack revision 1/);
  assert.throws(() => assetPacks.merge(installed, { ...next, revision: 1 }), /Conflicting content/);
  assert.throws(() => assetPacks.manifest({ ...pack, looks: [pack.looks[0], pack.looks[0]] }), /Duplicate look/);
  assert.throws(() => assetPacks.manifest({ ...pack, looks: [{ ...pack.looks[0], id: 'other/enamel' }] }), /namespaced/);
});

test('strength blends the completed stack and bindings keep authored defaults independent', () => {
  const catalog = assetPacks.create({ packs: [pack] });
  const first = looks.bind('relay/glazed-enamel', catalog);
  const second = looks.bind({ asset: 'relay/glazed-enamel', ...clay }, catalog);
  assert.equal(first.palette.palette[0], '#152d3f');
  assert.equal(second.palette.palette[0], '#4d2435');
  assert.equal(second.stack.steps[0].curves.ramp.stops[1][1], '#ae5653');
  assert.equal(second.stack.amount, .86);
  assert.equal(first.stack.amount, 1);
  assert.throws(() => looks.bind({ asset: first.id, params: { wrong: 1 } }, catalog), /Unknown look parameter/);
  assert.throws(() => looks.bind({ asset: first.id, params: { mid: 2 } }, catalog), /must be string/);
  assert.equal(looks.bind({ asset: first.id, palette: false }, catalog).palette, undefined);
  const steps = [{ type: 'exposure', stops: 1 }, { type: 'exposure', stops: 1 }];
  const rgb = [.2, .2, .2];
  ColorStack.prepare({ name: 'Combined', amount: .5, steps }).sample(rgb, rgb);
  assert.deepEqual(rgb, [.5, .5, .5]);
});

test('simulation entities inherit a prefab look, keep overrides isolated, and capture them', () => {
  const { world: W } = KIT;
  const source = W.manifest({ ...sampleWorld, assetPacks: [pack] });
  const stamped = W.stamp(W.stamp(source, 'relay', 'left', { position: [-1, 0, 0] }).world,
    'relay', 'right', { position: [1, 0, 0], lookAsset: clay }).world;
  assert.equal(stamped.entities.left.lookAsset.strength, undefined);
  assert.equal(stamped.entities.right.lookAsset.strength, .86);
  assert.equal(stamped.entities.right.lookAsset.asset, 'relay/glazed-enamel');
  const captured = W.capture(stamped, 'right', 'clay-copy').world;
  assert.deepEqual(captured.prefabs['clay-copy'].lookAsset, stamped.entities.right.lookAsset);
  const run = W.runtime.create(stamped);
  const world = W.visual(kit, run.view(), run.query());
  assert.equal(world.look.colorStack.name, 'Blue hour');
  const image = studio.render(world, view);
  for (const hex of ['#65ab97', '#d48562']) {
    const color = parseInt(hex.slice(1), 16);
    assert(image.use[image.palette.indexOf(color)] > 0);
  }
  const invalid = { ...stamped, entities: { ...stamped.entities,
    right: { ...stamped.entities.right, lookAsset: { asset: 'relay/absent' } } } };
  assert.throws(() => W.runtime.validate(invalid), /Unknown look asset/);
});

test('a scene asset grades the source swatches before quantizing to its palette', () => {
  const look = { id: 'relay/dim', label: 'Dim', stack: { name: 'Dim', steps: [{ type: 'exposure', stops: -4 }] },
    palette: { palette: ['#100620', '#e0fff0'] } };
  const catalog = assetPacks.create({ packs: [{ ...pack, looks: [look] }] });
  const b = kit.makeBuilder(1, [0, 0xeeeeee]);
  b.disc(0, 0, 0, [0, 0, 1], .6, .03, b.P[1], 3);
  const world = b.finish({ cam: { target: [0, 0, 0], dist: 4, yaw: 0, pitch: 0 },
    look: looks.scene({ asset: look.id }, catalog) });
  for (const options of [{}, { colored: true }, { stable: { resolve: 'coverage' } }]) {
    const render = parameters => studio.render(world, { w: 40, h: 40, px: 1, ortho: true, ...options, ...parameters });
    const pixel = ({ rgb }) => Array.from(rgb.slice((20 * 40 + 20) * 3, (20 * 40 + 20) * 3 + 3));
    assert.deepEqual(pixel(render({})), [0x10, 0x06, 0x20]);
    assert.deepEqual(pixel(render({ colorStack: false })), [0xe0, 0xff, 0xf0]);
  }
});

test('CLI loads a standalone pack and renders a scene plus two material instances', () => {
  const root = path.resolve(__dirname, '..'), temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-look-'));
  const scene = path.join(root, 'examples/look-assets.json');
  const asset = path.join(root, 'examples/relay-look-pack.json');
  const cli = (...args) => execFileSync(process.execPath, [path.join(root, 'cli/ink-studio.js'), ...args],
    { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
  try {
    assert.match(cli('validate', scene, '--asset-pack', asset), /sound/);
    assert.throws(() => cli('validate', scene), /Unknown look asset/);
    const output = path.join(temp, 'relay.png');
    cli('render', scene, '--asset-pack', asset, '--ortho', '--w', '360', '--h', '250', '--out', output);
    const { rgb } = require('../cli/png.js').read(output);
    const colors = new Set();
    for (let i = 0; i < rgb.length; i += 3) colors.add(rgb[i] * 65536 + rgb[i + 1] * 256 + rgb[i + 2]);
    assert(colors.has(0x65ab97));
    assert(colors.has(0xd48562));
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
});

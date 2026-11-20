const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawnSync } = require('node:child_process');
const relay = require('../examples/relay-look-pack.json');
const { world: W } = require('../index.js').load().KIT;

const root = path.resolve(__dirname, '..');
const cliPath = path.join(root, 'cli/ink-studio.js');
const packPath = path.join(root, 'examples/relay-look-pack.json');
const run = (...args) => spawnSync(process.execPath, [cliPath, ...args], { cwd: root, encoding: 'utf8' });
function cli(...args) {
  const result = run(...args);
  assert.equal(result.status, 0, result.stderr);
  return result.stdout ? JSON.parse(result.stdout) : undefined;
}
const read = file => fs.readFileSync(file, 'utf8');
function fixture(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-scene-look-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return (name, contents) => {
    const file = path.join(dir, name);
    if (contents !== undefined) fs.writeFileSync(file, typeof contents === 'string' ? contents : JSON.stringify(contents));
    return file;
  };
}
function scene() {
  const block = (id, x, materialId) => ({ id, kind: 'box', at: [x, .4, 0], half: [.4, .4, .4], res: .12,
    surfaceId: id + '-face', mat: { role: 'stone', materialId } });
  return { id: 'binding-check', style: { extends: 'slate', finish: { look: { pixelSize: 3 } } },
    solids: [block('west', -1, 'steel'), block('east', 1, 'copper')] };
}
const bind = (select, binding) => ({ op: 'bind-look', select, binding });

test('scene apply attaches, replaces and removes a scoped binding in a JSON diorama', t => {
  const file = fixture(t), input = file('scene.json', scene()), before = read(input);
  const select = { material: 'steel', surface: 'west-face' };
  const attach = file('attach.json', [bind(select, 'relay/glazed-enamel')]);
  const preview = cli('scene', 'apply', input, attach, '--asset-pack', packPath, '--dry-run');
  assert.deepEqual(preview.changed, [['finish']]);
  assert.deepEqual(preview.lookBindings.materials, ['steel']);
  assert.deepEqual(preview.lookBindings.surfaces, ['west-face']);
  assert.deepEqual(preview.lookBindings.entities, ['west']);
  assert.deepEqual(preview.lookBindings.instances, []);
  assert.equal(read(input), before);
  const edited = file('edited.json');
  cli('scene', 'apply', input, attach, '--asset-pack', packPath, '--out', edited);
  const applied = JSON.parse(read(edited));
  assert.equal(applied.finish.look.pixelSize, 3);
  assert.equal(applied.assetPacks[0].id, 'relay');
  assert.equal(cli('look', 'inspect', edited).rules[0].matchedTargets[0].surface, 'west-face');

  const replacement = { asset: 'relay/glazed-enamel', stage: 'lit', params: { mid: '#9a3434' }, weight: .65 };
  const replace = file('replace.json', [bind({ surface: 'west-face', material: 'steel' }, replacement)]);
  const replaced = file('replaced.json');
  cli('scene', 'apply', edited, replace, '--out', replaced);
  assert.equal(JSON.parse(read(replaced)).finish.look.targets.length, 1);
  assert.deepEqual(JSON.parse(read(replaced)).finish.look.targets[0].asset, replacement);
  assert.deepEqual(cli('scene', 'apply', edited, replace, '--dry-run').lookBindings.entities, ['west']);

  const remove = file('remove.json', [bind(select, null)]);
  assert.deepEqual(cli('scene', 'apply', replaced, remove, '--dry-run').lookBindings.surfaces, ['west-face']);
  assert.deepEqual(cli('scene', 'apply', replaced, remove).finish.look.targets, []);
  assert.deepEqual(cli('scene', 'apply', input, remove, '--dry-run'), { changed: [] });
});

test('previews attribute inherited look changes to the placed instance', t => {
  const file = fixture(t), original = require('../examples/look-prefabs.json');
  const world = W.stamp(W.stamp(W.manifest({ ...original, assetPacks: [relay] }), 'relay', 'west', { position: [-1, 0, 0] }).world,
    'relay', 'east', { position: [1, 0, 0] }).world;
  const input = file('world.json', world);
  const direct = file('overrides.json', [
    { op: 'set', path: '/entities/west/lookAsset/params', value: { mid: '#a05a35' } }
  ]);
  const override = cli('scene', 'apply', input, direct, '--dry-run');
  assert.deepEqual(override.lookBindings.instances, ['west']);
  assert.deepEqual(override.lookBindings.entities, ['west.box']);
  assert.deepEqual(override.lookBindings.materials, ['entity']);
  const scoped = file('scoped.json', [bind({ prefab: 'east' }, 'relay/blue-hour')]);
  assert.deepEqual(cli('scene', 'apply', input, scoped, '--dry-run').lookBindings.instances, ['east']);
  assert.equal(cli('validate', scoped, '--world', input, '--kind', 'edits').valid, true);
});

test('scene apply validates the complete look batch and preserves output on failure', t => {
  const file = fixture(t), input = file('world.json', {
    format: W.format, id: 'look-batch', assetPacks: [relay],
    visual: { bounds: { min: [-1, -.3, -1], max: [1, 1, 1] }, resolution: .2 }
  });
  const original = read(input), target = { surface: 'new-wall' };
  const bad = file('bad.json', [bind(target, 'relay/glazed-enamel')]);
  const output = file('output.json', 'existing output');
  const result = run('scene', 'apply', input, bad, '--out', output);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /No render target matches.*new-wall/);
  assert.equal(read(output), 'existing output');
  assert.equal(read(input), original);
  assert.equal(run('validate', bad, '--world', input, '--kind', 'edits').status, 1);

  const good = file('valid.json', [
    bind(target, 'relay/glazed-enamel'),
    { op: 'set', path: ['entities', 'panel'], value: {
      position: [0, .45, 0], visual: { half: [.4, .4, .4], surfaceId: 'new-wall' }
    } }
  ]);
  assert.deepEqual(cli('scene', 'apply', input, good, '--dry-run').lookBindings.surfaces, ['new-wall']);
  assert.equal(run('scene', 'apply', input, good, '--dry-run', '--out', input).status, 1);
  assert.equal(read(input), original);
});

test('dry runs detect changes to LUT values with an unchanged table shape', t => {
  const file = fixture(t), spec = scene();
  spec.finish = { look: { renderStages: [{ stage: 'lit', select: { surface: 'east-face' },
    stack: { name: 'Table', steps: [{ type: 'lut', lut: { size: 2, data: Array(24).fill(.5) } }] } }] } };
  const input = file('look.json', spec);
  const edits = file('table.json', [
    { op: 'set', path: '/finish/look/renderStages/0/stack/steps/0/lut/data/0', value: .25 }
  ]);
  assert.deepEqual(cli('scene', 'apply', input, edits, '--dry-run').lookBindings.surfaces, ['east-face']);
});

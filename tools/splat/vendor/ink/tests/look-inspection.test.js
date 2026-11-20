const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const source = file => path.join(root, 'examples', file);
const run = (...args) => spawnSync(process.execPath, ['cli/ink-studio.js', ...args],
  { cwd: root, encoding: 'utf8' });
function cli(...args) {
  const result = run(...args);
  assert.equal(result.status, 0, result.stderr);
  return result.stdout;
}
function fixture(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-look-inspect-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return (name, contents) => {
    const file = path.join(dir, name);
    if (contents !== undefined) fs.writeFileSync(file, typeof contents === 'string' ? contents : JSON.stringify(contents));
    return file;
  };
}

test('look inspect lists scene, target and surface rules with resolved provenance', () => {
  const selected = JSON.parse(cli('look', 'inspect', source('shared-look-selectors.js'), '--renderer', 'webgl'));
  assert.equal(selected.valid, true);
  const tag = { tag: 'paint-sample', material: 'bone' };
  const rule = selected.rules.find(rule => rule.select?.tag === tag.tag);
  assert.equal(rule.asset, 'relay/glazed-enamel');
  assert.equal(rule.stage, 'palette');
  assert.deepEqual(rule.matchedTargets, JSON.parse(cli('inspect', source('shared-look-selectors.js'), '--select', JSON.stringify(tag))).targets);
  assert(selected.rules.some(rule => rule.asset === 'relay/blue-hour' && rule.path === 'look.colorStack'));

  const surface = JSON.parse(cli('look', 'inspect', source('look-assets.json'), '--asset-pack', source('relay-look-pack.json')));
  const materials = surface.rules.filter(rule => rule.mode === 'surface' && rule.asset === 'relay/glazed-enamel');
  assert(materials.some(rule => rule.matchedTargets.some(target => target.entity === 'sea-glaze')));
  assert(materials.some(rule => rule.matchedTargets.some(target => target.entity === 'clay-glaze')));
  assert(materials.every(rule => new Set(rule.matchedTargets.map(target => target.entity)).size === 1));
});

test('look inspect uses saved simulation inputs and reports mask dependencies', t => {
  const file = fixture(t), checkpoint = file('forge.json');
  cli('sim', 'run', source('driven-look-forge.json'), '--actions', source('driven-look-forge-actions.json'),
    '--ticks', '64', '--checkpoint', checkpoint);
  const report = JSON.parse(cli('look', 'inspect', checkpoint));
  assert.equal(report.tick, 64);
  assert.equal(report.time, 3.2);
  const coil = report.rules.find(rule => rule.select?.surface === 'heater-coil');
  assert.equal(coil.inputs.strength.port, 'heater/value');
  assert.equal(coil.sampledInputs.strength, 1);
  assert.deepEqual(coil.dependencies, [{ type: 'asset', id: 'forge/hot-steel' },
    { type: 'signal', id: 'heater/value' }, { type: 'query', id: 'forge/temperature' }]);
  const wet = JSON.parse(cli('look', 'inspect', source('wet-spillway.js')));
  const masked = wet.rules.find(rule => rule.mask?.field === 'runoff/wetness');
  assert.equal(masked.mask.space, 'world');
  assert(masked.dependencies.some(dependency => dependency.type === 'query' && dependency.id === 'runoff/wetness'));
});

test('validate detects unresolved selectors and missing swatches in their scene context', t => {
  const file = fixture(t);
  const scene = { format: 'ink-studio/world', version: 1, id: 'look-check',
    visual: { bounds: { min: [-1, -.3, -1], max: [1, 1, 1] }, resolution: .2,
      look: { renderStages: [{ stage: 'lit', select: { surface: 'missing' },
        stack: { name: 'Dim', steps: [{ type: 'exposure', stops: -1 }] } }] } } };
  const absent = file('absent.json', scene);
  const report = JSON.parse(cli('look', 'inspect', absent));
  assert.equal(report.valid, false);
  assert.deepEqual(report.rules[0].matchedTargets, []);
  assert.equal(report.issues[0].code, 'unresolved-selector');
  const result = run('validate', absent);
  assert.equal(result.status, 1);
  assert.match(result.stderr, /No render target matches.*missing/);

  scene.visual.look = { paletteRemap: { rules: [{ from: '#012345', to: '#fffafa' }] } };
  const missing = run('validate', file('missing-swatch.json', scene));
  assert.equal(missing.status, 1);
  assert.match(missing.stderr, /Swatch is missing from the palette: #012345/);

  scene.visual.look = { colorLut: { size: 2, data: [0, 0, 0] } };
  assert.match(run('validate', file('bad-world-lut.json', scene)).stderr, /needs exactly 8 RGB rows/);
});

test('standalone validation checks LUT rows and WebGL binding compatibility', t => {
  const file = fixture(t);
  const short = file('short.cube', 'LUT_3D_SIZE 2\n0 0 0\n');
  const bad = run('validate', short);
  assert.equal(bad.status, 1);
  assert.match(bad.stderr, /needs exactly 8 RGB rows/);
  const lut = JSON.parse(cli('look', 'inspect', source('blue-shadow.cube')));
  assert(lut.rules[0].stack.steps[0].lut.rows > 0);
  assert(!Object.hasOwn(lut.rules[0].stack.steps[0].lut, 'data'));
  const native = JSON.parse(cli('look', 'inspect', source('relay-look-pack.json'), '--look', 'relay/glazed-enamel'));
  assert.equal(native.rules[0].parameters.mid, '#36787a');
  assert.equal(native.rules[0].revision, 1);

  const stages = run('validate', source('render-stages.js'), '--renderer', 'webgl');
  assert.equal(stages.status, 1);
  assert.match(stages.stderr, /webgl does not evaluate explicit material stages/);
  const optics = JSON.parse(cli('look', 'inspect', source('optical-look-bindings.js'), '--renderer', 'webgl'));
  const water = optics.rules.find(rule => rule.select?.medium === 'cistern-water');
  const fog = optics.rules.find(rule => rule.select?.medium === 'drift');
  assert(water.matchedTargets.length > 0);
  assert(!optics.issues.some(issue => issue.path === water.path));
  assert(optics.issues.some(issue => issue.path === fog.path && issue.code === 'unsupported-renderer'));
});

const assert = require('node:assert/strict');
const test = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const PNG = require('../cli/png.js');

const root = path.resolve(__dirname, '..');
const run = (...args) => spawnSync(process.execPath, ['cli/ink-studio.js', ...args], { cwd: root, encoding: 'utf8' });
function cli(...args) {
  const child = run(...args);
  assert.equal(child.status, 0, child.stderr);
  return child.stdout ? JSON.parse(child.stdout) : undefined;
}
function fixture(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-look-comparison-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return (name, contents) => {
    const file = path.join(dir, name);
    if (contents !== undefined) fs.writeFileSync(file, typeof contents === 'string' ? contents : JSON.stringify(contents));
    return file;
  };
}
const local = { surface: 'test-face' };
const exposure = (name, stops) => ({ name, steps: [{ type: 'exposure', stops }] });
const cfg = ['--w', '80', '--h', '48', '--ortho'];

test('compare groups color changes, measures clipping and counts unused output swatches', t => {
  const temp = fixture(t);
  const scene = temp('panels.js', `module.exports = ({ makeBuilder }) => ({ id:'panels', seed:4, build() {
    const B = makeBuilder(4, [0, 0x606060, 0xffffff]);
    B.disc(-1, 0, 0, [0,0,1], .35, .02, B.P[1], 3);
    B.describeSplats(0, 1, { object:'left', material:'iron', target:{surface:'test-face'} });
    B.disc(1, 0, 0, [0,0,1], .35, .02, B.P[1], 3);
    B.describeSplats(1, 2, { object:'right', material:'stone', target:{surface:'other-face'} });
    return B.finish({ cam:{target:[0,0,0],dist:4,yaw:0,pitch:0},
      look:{renderStages:[{stage:'frame',stack:{name:'Base',steps:[]}}]} });
  } });`);
  const cases = temp('cases.json', [
    { id: 'base' },
    { id: 'frame', look: { renderStages: [{ stage: 'frame', select: local, stack: exposure('Bright', 3) }] } },
    { id: 'palette', look: { palette: ['#ff3300', '#ffff00'], select: local } },
    { id: 'grade-file', look: 'grade.json' }
  ]);
  temp('grade.json', { renderStages: false, colorStack: exposure('Legacy lift', 3) });
  const preview = temp('comparison.png'), reportFile = temp('report.json');
  cli('compare', scene, '--looks', cases, ...cfg, '--t', '0', '--out', preview, '--report', reportFile);
  const report = JSON.parse(fs.readFileSync(reportFile, 'utf8'));
  const [base, frame, palette, grade] = report.results;
  assert.equal(report.baseline, 'base');
  assert.equal(report.time, 0);
  assert.deepEqual(report.camera.target, [0, 0, 0]);
  assert.equal(base.clipping.pixels, 0);
  assert(frame.clipping.pixels > 0);
  assert.equal(frame.clipping.stages.frame.above, frame.clipping.pixels * 3);
  assert.deepEqual(frame.difference.targets.filter(row => row.changedPixels).map(row => row.target.surface), ['test-face']);
  assert(frame.difference.bindings.some(row => row.binding.select?.surface === local.surface && row.changedPixels > 0));
  assert(palette.swatches.used.some(row => row.swatch === '#ff3300'));
  assert(palette.swatches.unused.includes('#ffff00'));
  assert(grade.clipping.palette.some(row => row.input === '#606060' && row.rgb.every(n => n > 1)));
  assert(PNG.read(preview).w >= 4 * report.width);
});

test('look sweeps hold a saved simulation tick and reuse the same named look for strength and palette cases', t => {
  const temp = fixture(t);
  const pack = { format: 'ink-studio/asset-pack', version: 1, revision: 1, id: 'test', title: 'Test artist',
    looks: [{ id: 'test/lift', label: 'Raise', stage: 'frame', stack: exposure('Lift', 2) }] };
  const scene = temp('world.json', { format: 'ink-studio/world', id: 'look-world', dt: .1, seed: 17, assetPacks: [pack],
    scenario: { until: 15 }, entities: { wall: { position: [0, .4, 0], visual: { half: [.5,.4,.35], surfaceId: 'wall-face' } } },
    visual: { resolution: .15, bounds: { min: [-1.25,-.25,-1], max: [1.25,1,1] },
      look: { renderStages: [{ stage: 'frame', stack: exposure('Base', 0) }] } } });
  const checkpoint = temp('saved.json'), recording = temp('run.json');
  cli('sim', 'run', scene, '--ticks', '6', '--checkpoint', checkpoint, '--record', recording);
  const cases = temp('cases.json', [
    { id: 'base' },
    { id: 'weak', look: { asset: 'test/lift', strength: .25, select: { surface: 'wall-face' } } },
    { id: 'strong', look: { asset: 'test/lift', strength: 1, palette: ['#333333','#eeeeee'], select: { surface: 'wall-face' } } }
  ]);
  const result = cli('sim', 'sweep', checkpoint, cases, ...cfg);
  assert.equal(result.tick, 6);
  assert.equal(result.time, 6 * .1);
  assert.equal(result.seed, 17);
  assert(result.runs[1].difference.changedPixels > 0);
  assert(result.runs[2].swatches.used.length > 0);
  assert(result.runs[2].difference.targets.filter(row => row.changedPixels).every(row => row.target?.surface === 'wall-face'));
  assert.deepEqual(cli('compare', checkpoint, '--looks', cases, ...cfg).results, result.runs);
  assert.equal(cli('sim', 'sweep', recording, cases, '--ticks', '4', ...cfg).tick, 4);

  const mixed = temp('mixed.json', [{ id: 'base' }, { id: 'bad', ticks: 9, look: 'off' }]);
  assert.match(run('sim', 'sweep', checkpoint, mixed, ...cfg).stderr, /Set camera and simulation inputs on the command/);
});

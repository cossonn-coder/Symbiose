const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const test = require('node:test');

const cli = path.resolve(__dirname, '../cli/ink-studio.js');
const look = (...args) => spawnSync(process.execPath, [cli, 'look', ...args], { encoding: 'utf8', timeout: 130000 });

test('look profile measures a baseline, global grade and scoped palette on the same workload', () => {
  const run = look('profile', '--frames', '3', '--warmup', '1', '--splats', '25', '--w', '60', '--h', '48');
  assert.equal(run.status, 0, run.stderr);
  const profile = JSON.parse(run.stdout);
  assert.equal(profile.format, 'ink-studio/look-profile');
  assert.deepEqual([profile.frames, profile.warmup, profile.splats, profile.width, profile.height], [3, 1, 25, 60, 48]);
  const { cases, batch, samples } = profile.results.headless;
  assert.deepEqual([batch, samples], [1, 3]);
  assert.deepEqual(cases.map(entry => entry.id), ['baseline', 'global-lut', 'scoped-palette', 'scoped-mask', 'layered-coverage']);
  for (const { splats, setupMs, frameMs } of cases) {
    assert.equal(splats, 25);
    assert.deepEqual(Object.keys(setupMs), ['fixture', 'renderer', 'firstFrame', 'lookPlan']);
    assert(Object.values(setupMs).every(ms => Number.isFinite(ms) && ms >= 0));
    assert(frameMs.min <= frameMs.p50 && frameMs.p50 <= frameMs.p95 && frameMs.p95 <= frameMs.max);
    assert(frameMs.min <= frameMs.mean && frameMs.mean <= frameMs.max);
  }
  assert.deepEqual(cases[0].deltaMs, { lookPlan: 0, p50Frame: 0, meanFrame: 0 });
  const invalid = look('profile', '--frames', '0');
  assert.equal(invalid.status, 1);
  assert.match(invalid.stderr, /--frames expects an integer/);
});

test('look parity compares actual WebGL output with the headless fixtures', { skip: !process.env.INK_TEST_CHROME }, () => {
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-look-parity-test-'));
  try {
    const output = path.join(temp, 'parity.json');
    const run = look('parity', '--strict', '--out', output);
    assert.equal(run.error, undefined);
    assert.equal(run.stderr, '');
    const parity = JSON.parse(fs.readFileSync(output, 'utf8'));
    assert.equal(parity.format, 'ink-studio/look-parity');
    assert.match(parity.driver, /SwiftShader/i);
    assert.deepEqual(parity.summary, { passed: 13, knownGaps: 0, failed: 0 });
    assert.equal(parity.ok, true);
    assert.equal(run.status, 0);
    const cases = Object.fromEntries(parity.cases.map(entry => [entry.id, entry]));
    assert.deepEqual(cases.tetrahedral.samples.left.webgl, [96, 64, 128]);
    assert.deepEqual(cases.trilinear.samples.left.webgl, [48, 64, 128]);
    for (const id of ['linear-legal-range', 'scoped-palette', 'glass-control'])
      assert.equal(cases[id].status, 'passed');
    for (const id of ['spatial-mask','projected-texture-mask','coverage-compositing','masked-pane','pane-stack','layered-panes','refracted-pane'])
      assert.equal(cases[id].status,'passed');
    assert.equal(cases['layered-panes'].pick.matched,true);
    assert.deepEqual(cases['layered-panes'].pick.webgl.contributions.map(hit=>hit.target.entity),['pane-front','pane','left']);
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
});

function bendFixture({makeBuilder}, bend) {
  const B=makeBuilder(44,[0,0x00fa00,0xf50000,0x0000ff]);
  B.disc(-.38,0,0,[0,0,1],.55,.024,B.P[1],3);
  B.disc(.4,0,.02,[0,0,1],.55,.024,B.P[2],3);
  B.disc(0,0,.45,[0,0,1],.29,.025,B.P[1],.5,{gl:true,nd:true});
  B.describeSplats(2,3,{object:'glass'});
  return B.finish({cam:{target:[0,0,0],dist:2.7,yaw:0,pitch:0},refract:bend,
    look:{coverageAware:true,paletteConstraints:{targets:[{object:'glass',palette:['#0000ff']}]}}});
}
function bendCheck(kit, build, open) {
  const backend=open(100,80,{ortho:true,dither:0,colored:false,outline:false});
  try {
    const points=Object.fromEntries(Array.from({length:58},(_,i)=>[String(i),[22+i,40]]));
    backend.draw(build(kit,0));
    const before=backend.sample(points);
    backend.draw(build(kit,96));
    const after=backend.sample(points);
    const pairs=Object.keys(points).map(key=>[before[key],after[key]]);
    return {backdropDelta:Math.max(...pairs.map(([a,b])=>Math.max(Math.abs(a[0]-b[0]),Math.abs(a[1]-b[1])))),
      glassDelta:Math.max(...pairs.map(([a,b])=>Math.abs(a[2]-b[2])))};
  } finally { backend.close(); }
}
test('refraction displaces the graded backdrop while the pane contribution stays at the original pixel', {
  skip:!process.env.INK_TEST_CHROME
},()=>{
  const result=require('../cli/look-webgl.js')({},bendFixture,bendCheck,{});
  assert(result.backdropDelta>15,JSON.stringify(result));
  assert(result.glassDelta<=1,JSON.stringify(result));
});

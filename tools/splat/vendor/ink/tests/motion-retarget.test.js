const assert = require('node:assert/strict');
const { test } = require('node:test');
const { mkdtempSync, readFileSync, rmSync, writeFileSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { join, resolve } = require('node:path');
const { execFileSync } = require('node:child_process');
const studio = require('..');
const kit = studio.load(), { KIT: K } = kit;
const api = K.anim.retarget;
const near = (a, b, tolerance = 1e-7) => {
  assert.equal(a.length, b.length);
  for (let i = 0; i < a.length; i++) assert(Math.abs(a[i] - b[i]) < tolerance, a + ' does not match ' + b);
};

function skeleton(profile, size, rotation = K.M.id()) {
  const template = api.profiles[profile];
  const parts = { [template.root]: { pivot: [0, 0, 0] } };
  let y = 0;
  for (const [id, entry] of Object.entries(template.roles)) {
    if (id !== template.root && !entry.marker)
      parts[id] = { pivot: K.M.app(rotation, [0, --y * size, (y % 3) * size]) };
  }
  return { puppet: { parts }, forward: K.M.app(rotation, [0, 0, 1]), up: K.M.app(rotation, [0, 1, 0]) };
}

test('built-in role maps retarget biped, quadruped, avian, and serpentine root and body motion', () => {
  const rotation = K.M.rot([0, 1, 0], Math.PI / 2);
  for (const profile of Object.keys(api.profiles)) {
    const root = api.profiles[profile].root, source = skeleton(profile, 1), target = skeleton(profile, 2, rotation);
    const role = { biped: 'leftThigh', quadruped: 'rightHindLower', avian: 'leftWing', serpentine: 'tail' }[profile];
    const clip = K.anim.clip({ dur: 1, tracks: {
      [root + '.pos']: [[0, [0, 0, 0]], [1, [0, 0.3, 2]]], [role + '.rot']: [[0, [0, 0, 0]], [1, [30, 0, 0]]]
    } });
    const plan = api.create({ profile, clip, source, target });
    assert.equal(plan.status, 'ready');
    assert.equal(plan.report().travelScale, 2);
    near(plan.sample(1)[root].pos, [4, 0.6, 0]);
    near(K.deform.euler(plan.sample(1)[role].rot), K.M.rot([0, 0, -1], Math.PI / 6));
    near(api.create({ profile, clip, source, target, travel: 'in-place' }).sample(1)[root].pos, [0, 0.6, 0]);
    near(api.create({ profile, clip, source, target, travel: 'unscaled' }).sample(1)[root].pos, [2, 0.3, 0]);
    assert(plan.bake().clip.tracks.some(track => track.part === role));
  }
});

test('creator role maps remap differently named and oriented segments, including endpoint points', () => {
  const profile = { id: 'climber', root: 'body', roles: {
    body: {}, claw: { required: true, aim: 'tip' }, tip: { marker: true, required: true }, crest: {}
  }, scaleChains: [['claw', 'tip']] };
  const rig = (root, part, point) => ({
    puppet: { parts: { [root]: { pivot: [0, 0, 0] }, [part]: { pivot: [0, 0, 0] } } },
    roles: { body: root, claw: part, tip: { part, point } }
  });
  const source = rig('center', 'legA', [0, -1, 0]), target = rig('carriage', 'talon', [2, 0, 0]);
  const clip = K.anim.clip({ dur: 1, tracks: {
    'center.pos': [[0, [0, 0, 0]], [1, [0, 0, 1]]],
    'legA.rot': [[0, [0, 0, 0]], [1, [0, 0, 90]]],
    'legA.pos': [[0, [0, 0, 0]], [1, [0, -0.2, 0]]]
  } });
  const plan = api.create({ clip, profile, source, target });
  assert.equal(plan.status, 'ready');
  assert.equal(plan.report().roles.find(item => item.role === 'tip').driven, false);
  near(plan.sample(0).talon.rot, [0, 0, 0]);
  const pose = plan.sample(1);
  near(pose.carriage.pos, [0, 0, 2]);
  near(pose.talon.pos, [0.4, 0, 0]);
  near(K.M.app(K.deform.euler(pose.talon.rot), [2, 0, 0]), [0, 2, 0]);

  const partialTarget = { ...target, roles: { ...target.roles, claw: 'missing' } };
  const partial = api.create({ clip, profile, source, target: partialTarget });
  assert.equal(partial.status, 'partial');
  assert(partial.report().target.missing.some(item => item.role === 'claw' && item.reason === 'unknown-part'));
  assert(partial.report().skippedTracks.some(track => track.part === 'legA'));
  assert.deepEqual(partial.bake().definition.tracks.map(track => track.part), ['carriage']);
  const unsupported = api.create({ clip, profile, source, target: { ...partialTarget, roles: {} } });
  assert.equal(unsupported.status, 'unsupported');
  assert.throws(() => unsupported.bake(), /mapped root/);
});

test('a baked quadruped trot carries all four pads and a tail through native puppet playback', () => {
  function animal(prefix, size) {
    const B = kit.makeBuilder(7), S = K.sculpt(kit.makeSculpt(B)), tags = K.deform.tags(S);
    const parts = {}, roles = {};
    const part = (role, at, parent) => {
      const id = prefix + role, point = K.V.mul(at, size);
      roles[role] = id;
      parts[id] = { ids: [], pivot: point, parent: roles[parent] };
      S.ball(point, 0.10 * size, { r: [1, 2, 3] }, { tag: id, res: 0.07 });
    };
    part('hips', [0, 1.3, 0]);
    part('tail', [0, 1.4, -0.70], 'hips');
    roles.tailTip = { part: roles.tail, point: K.V.mul([0, 1.35, -1.1], size) };
    for (const [side, x] of [['left', -0.3], ['right', 0.3]]) for (const [limb, z] of [['Fore', 0.62], ['Hind', -0.56]]) {
      const role = side + limb;
      part(role + 'Upper', [x, 1.2, z], 'hips');
      part(role + 'Lower', [x, 0.62, z], role + 'Upper');
      part(role + 'Paw', [x, 0.12, z], role + 'Lower');
      roles[role + 'Pad'] = { part: roles[role + 'Paw'], point: K.V.mul([x, 0, z], size) };
    }
    S.bake();
    for (const [id, def] of Object.entries(parts)) def.ids = tags[id];
    const world = B.finish({ cam: { target: [0, 1, 0], dist: 6, yaw: 0.7, pitch: 0.1 } });
    return { world, puppet: K.puppet(world, { parts }), roles };
  }
  const source = animal('c-', 1), target = animal('m-', 1.6), tracks = [
    { part: source.roles.hips, ch: 'pos', keys: [[0, [0, 0, 0]], [1, [0, 0, 1]]] },
    { part: source.roles.tail, ch: 'rot', keys: [[0, [0, -20, 0]], [0.5, [0, 20, 0]], [1, [0, -20, 0]]] }
  ];
  for (const [i, name] of ['leftFore', 'rightFore', 'leftHind', 'rightHind'].entries()) {
    const swing = i === 0 || i === 3 ? 25 : -25;
    tracks.push({ part: source.roles[name + 'Upper'], ch: 'rot',
      keys: [[0, [swing, 0, 0]], [0.5, [-swing, 0, 0]], [1, [swing, 0, 0]]] });
  }
  const plan = api.create({ profile: 'quadruped', clip: K.anim.clip({ dur: 1, tracks }), source, target });
  assert.equal(plan.status, 'ready');
  const { clip } = plan.bake();
  const time = 8 / clip.fps, sourcePoints = plan.landmarks(time).source;
  const timeline = K.anim.timeline.create({ clip, world: target.world, puppet: target.puppet });
  timeline.frame(time, { stage: 'spline' });
  for (const role of ['leftForePad', 'rightForePad', 'leftHindPad', 'rightHindPad', 'tailTip']) {
    const { part, point } = target.roles[role];
    near(target.puppet.point(part, point), K.V.mul(sourcePoints[role], 1.6));
  }
});

test('bakes editable keys through held transitions, spin wraps, and an off-grid terminal pose', () => {
  const profile = { root: 'body', roles: { body: {} } };
  const rig = { puppet: { parts: { body: { pivot: [0, 0, 0] } } } };
  const clip = K.anim.clip({ id: 'take', dur: 1.14, loop: true, fps: 1, cues: [[0.52, 'beat']], tracks: {
    'body.rot': [[0, [0, 0, 0], 'linear'], [1, [0, 360, 0]], [1.14, [10, 370, 3]]],
    'body.pos': [[0, [0, 0, 0], 'step'], [0.52, [2, 0, 0]], [1.14, [3, 0, 1]]]
  } });
  const plan = api.create({ clip, profile, source: rig, target: rig });
  const baked = plan.bake(), roundTrip = K.anim.clip(JSON.parse(JSON.stringify(baked.definition)));
  assert.equal(roundTrip.id, 'take');
  assert.equal(roundTrip.loop, true);
  assert.deepEqual(roundTrip.cues, clip.cues);
  near(roundTrip.sample(0.5, {}, { sourceTime: true }).body.pos, [0, 0, 0]);
  near(roundTrip.sample(0.52, {}, { sourceTime: true }).body.pos, [2, 0, 0]);
  near(roundTrip.sample(1.14, {}, { sourceTime: true }).body.pos, [3, 0, 1]);
  near(K.deform.euler(roundTrip.sample(0.25).body.rot), K.deform.euler([0, 90, 0]));
  assert(Math.abs(roundTrip.tracks[0].keys.at(-1).t - 1.14) < 1e-8);
});

test('walk bake preserves the planted phase on a longer rig and can drive Ink’s shared timeline', () => {
  const a = require('../examples/retarget-courier')(kit), b = require('../examples/retarget-guard')(kit);
  const source = a.build(a.seed).retargetRig, world = b.build(b.seed), target = world.retargetRig;
  const plan = api.create({ clip: source.clips.walk, source, target });
  assert.equal(plan.status, 'ready');
  const p = plan.landmarks(0.125), q = plan.landmarks(0.375);
  assert(Math.abs(p.source.leftSole[2] - q.source.leftSole[2]) < 0.002);
  assert(Math.abs(p.target.leftSole[2] - q.target.leftSole[2]) < 0.002);
  assert(Math.abs(p.target.leftSole[1]) < 0.002);
  const { clip } = plan.bake();
  const seq = K.anim.sequence.create({ clips: { walk: clip }, root: 'belt-pivot', steps: [{ id: 'stride', clip: 'walk' }] });
  const timeline = K.anim.timeline.create({ world, puppet: target.puppet, sequence: seq });
  timeline.set({ stage: 'spline' });
  const at = 0.375;
  timeline.frame(at);
  near(target.puppet.point('sabatons-l', target.roles.leftSole.point), q.target.leftSole);
});

test('CLI discovers profiles, bakes native clip JSON and renders two synchronized sprite previews', () => {
  const dir = mkdtempSync(join(tmpdir(), 'ink-retarget-'));
  const cli = resolve(__dirname, '../cli/ink-studio.js'), source = resolve(__dirname, '../examples/retarget-courier.js');
  const target = resolve(__dirname, '../examples/retarget-guard.js');
  const run = (...args) => JSON.parse(execFileSync(process.execPath, [cli, 'retarget', ...args], { encoding: 'utf8' }));
  try {
    assert(run('--profiles').quadruped.scaleChains.length === 4);
    const file = join(dir, 'guard.json'), preview = join(dir, 'preview');
    const report = run(source, target, '--bake', file, '--preview', preview, '--frames', '4', '--direction', '1', '--w', '48', '--h', '48');
    assert.equal(report.status, 'ready');
    const read = f => JSON.parse(readFileSync(f, 'utf8'));
    const baked = read(file);
    assert(baked.tracks.some(track => track.part === 'belt-pivot'));
    const a = read(join(preview, 'source', 'atlas.json')), b = read(join(preview, 'target', 'atlas.json'));
    assert.equal(b.tileWidth, 48);
    assert(b.frames.every(frame => frame.silhouette.pixels > 0));
    assert.deepEqual(a.frames.map(frame => frame.sourceTime), b.frames.map(frame => frame.sourceTime));
    assert.equal(b.timeline.direction, 1);
    const map = join(dir, 'guard-map.json');
    writeFileSync(map, JSON.stringify({ roles: { hips: 'belt-pivot' } }));
    const partial = run(target, target, '--motion', file, '--target-map', map, '--at', '0.5');
    assert.equal(partial.clip, 'walk');
    assert.equal(partial.status, 'partial');
    assert.deepEqual(Object.keys(partial.landmarks.target), ['hips']);
    const custom = join(dir, 'profile.json'), customMap = join(dir, 'custom-map.json');
    writeFileSync(custom, JSON.stringify({ id: 'root-only', root: 'center', roles: { center: {} } }));
    writeFileSync(customMap, JSON.stringify({ roles: { center: 'belt-pivot' } }));
    const explicit = run(target, target, '--motion', file, '--profile', custom,
      '--source-map', customMap, '--target-map', customMap, '--at', '0.5');
    assert.equal(explicit.profile, 'root-only');
    assert.deepEqual(Object.keys(explicit.landmarks.target), ['center']);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

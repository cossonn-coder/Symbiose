const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const ink = require('..').load();
const { anim } = ink.KIT;
const demo = require('../examples/clip-sequence')(ink);
const near = (a, b) => Math.abs(a - b) < 1e-8;

test('trims and retimes reusable instances and moves later keys and cues together', () => {
  const source = anim.clip({ dur: 1, tracks: { 'hip.pos': [[0,[0,0,0],'linear'], [0.5,[0.5,0,0],'linear'], [1,[1,0,0]]] },
    cues: [[0.1, 'omit'], [0.5, 'mark'], { id: 'flash', type: 'flash', time: 0.5, duration: 0.5 }] });
  const original = JSON.stringify([source.tracks, source.cues]);
  const before = anim.sequence.create({ clips: { source }, steps: [{ id: 'a', clip: 'source' }, { id: 'b', clip: 'source' }] });
  const after = before.edit('a', { in: 0.25, out: 0.75, duration: 1.5, ease: 'in-sine' });
  assert.equal(after.steps[1].start, 1.5);
  const mark = after.cues.find(cue => cue.step === 'a' && cue.id === 'mark');
  const key = after.keys.find(key => key.step === 'a' && key.sourceTime === 0.5);
  assert.equal(mark.time, key.time);
  assert.ok(near(mark.time, 1));
  assert.ok(near(after.sample(mark.time).hip.pos[0], 0.5));
  assert.ok(near(after.cues.find(cue => cue.step === 'a' && cue.id === 'flash').duration, 0.5));
  assert.ok(!after.cues.some(cue => cue.step === 'a' && cue.id === 'omit'));
  assert.equal(after.cues.find(cue => cue.step === 'b' && cue.id === 'mark').time, 2);
  assert.equal(after.keys.find(key => key.step === 'b' && key.sourceTime === 0.5).time, 2);
  assert.equal(after.change.delta, 0.5);
  assert.ok(after.change.end < after.duration);
  assert.ok(near(after.change.timeAt(after.change.duration + 0.17), 0.17));
  assert.equal(before.steps[1].start, 1);
  assert.equal(after.edit('a', { out: 0.5 }).steps[0].duration, 0.75);
  assert.equal(after.edit('a', { ease: 'in-sine' }), after);
  assert.equal(after.arrange([after.steps[1], after.steps[0]]).steps[0].id, 'b');
  assert.equal(after.arrange([after.steps[1]]).change.focus, 'b');
  assert.equal(JSON.stringify([source.tracks, source.cues]), original);
});

test('handoffs measure output velocity and the nearby-cut proposal edits only its two instances', () => {
  const base = demo.build(demo.seed).clipSequence;
  const report = base.handoffs[0];
  assert.ok(report.poseGap > 0 && report.velocityGap > 0);
  assert.notEqual(report.velocityGap, base.edit('walk', { duration: 2 }).handoffs[0].velocityGap);
  const suggestion = base.suggestCut(0);
  assert.ok(suggestion.improvement >= 6);
  assert.ok(Math.abs(suggestion.sourceFrames) <= 8 && Math.abs(suggestion.targetFrames) <= 8);
  const result = base.applyCut(0);
  assert.equal(result.handoffs[0].score, suggestion.score);
  assert.equal(result.steps[0].out, suggestion.out);
  assert.equal(result.steps[1].in, suggestion.in);
  assert.equal(result.steps[2].in, base.steps[2].in);
  assert.equal(base.steps[1].in, 0);
  assert.ok(result.change.end >= result.handoffs[0].time);
  assert.equal(base.suggestCut(1), null);
});

test('root and matched planted sole alignment preserve distinct positions and unedited pose channels', () => {
  const authored = demo.build(demo.seed).clipSequence;
  const root = authored.align('root'), planted = authored.align('foot');
  const cut = root.handoffs[0].time, before = cut - 1e-7;
  const toe = pose => pose.body.pos[0] + pose.rightLeg.pos[0];
  assert.ok(authored.handoffs[0].rootGap > 1);
  assert.ok(root.handoffs[0].rootGap < 1e-8);
  assert.equal(planted.handoffs[0].foot, 'right-sole');
  assert.ok(Math.abs(toe(root.sample(cut)) - toe(root.sample(before))) > 0.15);
  assert.ok(near(toe(planted.sample(cut)), toe(planted.sample(before))));
  assert.deepEqual(planted.sample(cut).head.rot, authored.sample(cut).head.rot);
  assert.equal(planted.sample(cut).body.pos[1], authored.sample(cut).body.pos[1]);
  const fallback = anim.sequence.create({ root: 'body', alignment: 'foot',
    clips: { rest: anim.clip({ dur: 1 }) }, steps: [{ id: 'a', clip: 'rest' }, { id: 'b', clip: 'rest' }] });
  assert.equal(fallback.handoffs[0].alignment, 'root');
  assert.equal(fallback.handoffs[0].foot, null);
});

test('Once clamps, Loop stays in place and Travel loop accumulates X/Z over exact cycle boundaries', () => {
  const clip = anim.clip({ dur: 0.1, loop: true, tracks: { 'root.pos': [
    [0,[2,0,1],'linear'], [0.05,[3,0.3,0],'linear'], [0.1,[4,0,-1]]
  ] }, cues: [[0, 'enter'], [0.05, 'mid'], [0.1, 'exit']] });
  const sequence = anim.sequence.create({ clips: { clip }, root: 'root', steps: [{ id: 'a', clip: 'clip' }] });
  assert.deepEqual(sequence.sample(0.1).root.pos, [4,0,-1]);
  assert.deepEqual(sequence.sample(10).root.pos, [4,0,-1]);
  assert.ok(sequence.at(10).finished);
  assert.deepEqual(sequence.sample(0.05, {}, { mode: 'loop' }).root.pos, [2,0.3,1]);
  assert.equal(sequence.at(0.3, { mode: 'travel-loop' }).cycle, 3);
  assert.deepEqual(sequence.sample(0.3, {}, { mode: 'travel-loop' }).root.pos, [8,0,-5]);
  assert.ok(near(sequence.sample(0.15, {}, { mode: 'travel-loop' }).root.pos[0], 5));
  assert.deepEqual(sequence.eventsBetween(-0.00001, 0.1, { mode: 'loop' }).map(event => [event.id, event.cycle]),
    [['enter',0], ['mid',0], ['exit',0], ['enter',1]]);
  assert.deepEqual(sequence.eventsBetween(0.1, 0.2, { mode: 'travel-loop' }).map(event => event.id),
    ['mid', 'exit', 'enter']);
});

test('CLI publishes ripple evidence and cut data from the native sequence', () => {
  const data = execFileSync(process.execPath, ['cli/ink-studio.js', 'clip-sequence', 'examples/clip-sequence.js',
    '--handoff', '0', '--params', '{"edit":{"step":"walk","duration":1.5}}'],
  { cwd: path.join(__dirname, '..'), encoding: 'utf8' });
  const report = JSON.parse(data);
  assert.ok(near(report.change.delta, 0.3));
  assert.ok(near(report.cues.find(cue => cue.id === 'Signal up').time, 2.82));
  assert.ok(report.cut.improvement >= 6);
});

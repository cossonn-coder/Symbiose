const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const ink = require('..').load();
const { anim, V } = ink.KIT;
const demo = require('../examples/motion-review')(ink);

const near = (a, b) => Math.abs(a-b) < 1e-9;
const position = sample => sample.point;
const longestStep = path => Math.max(...path.slice(1).map((p, i) => V.dist(p.point, path[i].point)));
const endToEnd = path => V.dist(path[0].point, path.at(-1).point);
function corner(path, issue) {
  const i = issue.frame-issue.first;
  const a = V.norm(V.sub(path[i].point, path[i-1].point));
  const b = V.norm(V.sub(path[i+1].point, path[i].point));
  return Math.acos(Math.max(-1, Math.min(1, V.dot(a, b))));
}
function reviewDemo() {
  return demo.build(demo.seed).motionReview;
}

test('reports the four reviewed beats and supplies one focused guide for each', () => {
  const review = reviewDemo();
  assert.deepEqual(review.findings.map(({ kind }) => kind), ['spacing-spike', 'arc-kink', 'foot-drift', 'loop-pop']);
  for (const issue of review.findings.slice(0, -1)) {
    const focus = review.focus(issue.id);
    assert.ok(focus.start <= issue.start && focus.end >= issue.end);
    assert.equal(focus.evidence.type, 'path');
    assert.ok(near(focus.timeAt(focus.duration + 0.01), focus.start + 0.01));
    const points = focus.evidence.points;
    assert.ok(points.slice(1).every((p, i) => near(p.time-points[i].time, 1/24)));
  }
  const seam = review.focus('loop-pop');
  assert.equal(seam.wraps, true);
  assert.deepEqual(seam.evidence, { type: 'ghosts', times: [4, 0] });
  assert.ok(near(seam.timeAt(4-seam.start+0.02), 0.02));
  assert.ok(review.findings.at(-1).distance > .5);
});

test('corrective layers improve the sampled path, preserve range boundaries and can be muted independently', () => {
  const review = reviewDemo();
  for (const issue of review.findings.slice(0, -1)) {
    const original = review.focus(issue.id).evidence.points;
    const layer = review.accept(issue.id);
    assert.equal(layer.phase, 'corrective');
    assert.equal(layer.source.tracks[0].part, issue.part);
    assert.equal(review.accept(issue.id).source, layer.source);
    const corrected = review.focus(issue.id, { before: false }).evidence.points;
    assert.ok(V.dist(position(original[0]), position(corrected[0])) < 1e-9);
    if (issue.kind === 'spacing-spike') {
      assert.ok(longestStep(corrected) < longestStep(original) / 2);
      assert.ok(V.dist(position(original.at(-1)), position(corrected.at(-1))) < 1e-9);
    } else if (issue.kind === 'arc-kink') {
      assert.ok(corner(corrected, issue) < corner(original, issue) / 2);
      assert.ok(V.dist(position(original.at(-1)), position(corrected.at(-1))) < 1e-9);
    } else {
      assert.ok(endToEnd(original) > .25);
      assert.ok(endToEnd(corrected) < 1e-9);
      assert.ok(corrected.every((point, i) => near(point.point[1], original[i].point[1])));
    }
    const options = { sourceTime: true };
    const at = issue.time;
    const baseline = review.sample(at, {}, { ...options, before: true });
    assert.notDeepEqual(review.sample(at, {}, options), baseline);
    assert.equal(review.setEnabled(issue.id, false), true);
    assert.deepEqual(review.sample(at, {}, options), baseline);
    review.setEnabled(issue.id, true);
    assert.notDeepEqual(review.sample(at, {}, options), baseline);
    assert.equal(review.remove(issue.id), true);
    assert.deepEqual(review.sample(at, {}, options), baseline);
  }
});

test('true endpoint sampling closes the seam without altering loop playback or source keys', () => {
  const review = reviewDemo(), source = { sourceTime: true };
  const start = review.sample(0, {}, source), last = review.sample(4, {}, source);
  assert.notDeepEqual(last.head, start.head);
  assert.deepEqual(review.sample(4, {}), start);
  review.accept('loop-pop');
  assert.deepEqual(review.sample(4, {}, source), start);
  assert.deepEqual(review.sample(4, {}, { ...source, before: true }), last);
  review.remove('loop-pop');
  assert.deepEqual(review.sample(4, {}, source), last);
});

test('native driven and explicit corrective layers both evaluate after base layers', () => {
  const clip = anim.clip({ dur: 2, loop: true, tracks: { 'head.rot': [[0,[0,0,0]], [2,[0,20,0]]] },
    tools: { layers: [
      { part: 'head', phase: 'corrective', values: { head: { rot: [0,30,0] } } },
      { values: { head: { rot: [0,10,0] } } },
      { driver: { part: 'head', ch: 'rot.1', from: 0, to: 60, ease: 'linear' },
        values: { head: { rot: [0,60,0] } } }
    ] } });
  assert.deepEqual(clip.sample(2).head.rot, [0,50,0]);
  assert.deepEqual(clip.sample(2, {}, { sourceTime: true }).head.rot, [0,90,0]);
  assert.deepEqual(clip.sample(2, {}, { plain: true, sourceTime: true }).head.rot, [0,20,0]);
});

test('headless CLI can print a single selected finding for downstream tooling', () => {
  const result = execFileSync(process.execPath, ['cli/ink-studio.js', 'motion-review', 'examples/motion-review.js',
    '--finding', 'loop-pop'], { cwd: path.join(__dirname, '..'), encoding: 'utf8' });
  const report = JSON.parse(result);
  assert.equal(report.findings.length, 1);
  assert.equal(report.findings[0].kind, 'loop-pop');
  assert.deepEqual(report.findings[0].focus.evidence.times, [4, 0]);
});

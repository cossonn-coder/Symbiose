const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: K, makeBuilder } = require('..').load();

const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-6, `${a} differs from ${b}`);

test('a captured model uses a fixed local pivot and transforms its full covariance', () => {
  const B = makeBuilder(1);
  B.iso(3, 1, 2, 0.5, B.P[3], 3, { k: 6, em: true });
  B.iso(0, -99, 0, 0.5, B.P[1], 0);
  const source = B.finish();
  const model = K.frameSplats.capture(source, [2, 0, 0]);
  assert.equal(model.count, 1);
  source.data.fill(0);

  const dest = makeBuilder(2);
  const frame = K.frameSplats(dest, 2, draw => {
    const matrix = [2, 1, 0, 0, 3, 0, 0, 0, 0.5];
    assert.equal(draw.model(model, [10, 20, 30], { matrix, opacity: 0.5 }), true);
    assert.equal(draw.model(model, [0, 0, 0]), true);
  });
  const W = dest.finish();
  const st = K.stage(W);
  st.add(frame);
  st.update(0, 0);
  assert.deepEqual(Array.from(W.data.slice(0, 4)), [13, 23, 31, 1.5]);
  assert.deepEqual([4, 5, 6, 8, 9, 10].map(i => W.data[i]), [1.25, 0.75, 0, 2.25, 0, 0.0625]);
  assert.equal(W.data[7], 0x52b582);
  assert.deepEqual(Array.from(W.data.slice(11, 16)), [32, 0, 0, 0, 0]);
  assert.deepEqual(Array.from(W.data.slice(16, 20)), [1, 1, 2, 3]);
  assert.equal(st.rows[0], 1);
});

test('frames reuse their reserved rows and hide leftovers without touching scenery or particles', () => {
  const B = makeBuilder(1);
  B.iso(0, 1, 0, 0.1, B.P[2], 3);
  const model = K.frameSplats.capture(B.finish());
  let retained;
  const frame = K.frameSplats(B, 2, (draw, dt, t) => {
    retained = draw;
    if (t === 0) {
      assert.equal(draw.model(model, [2, 0, 0]), true);
      assert.equal(draw.model(model, [3, 0, 0]), true);
      assert.equal(draw.model(model, [4, 0, 0]), false);
    } else if (t === 1) {
      assert.equal(draw.streak([0, 1, 0], [2, 1, 0], { width: 0.25, emissive: false }), true);
      assert.equal(draw.vortex([0, 0, 0], { arms: 1, segments: 2 }), false);
    }
  });
  const pool = K.pool(B, 1);
  const W = B.finish();
  const st = K.stage(W);
  st.add(K.particles(st, pool)).emit({ p: [7, 1, 0], life: 3, fixed: true });
  st.add(frame);

  st.update(0, 0);
  assert.deepEqual([W.data[3], W.data[19], W.data[35], W.data[51]], [3, 3, 3, 3]);
  assert.throws(() => retained.streak([0, 0, 0], [1, 0, 0]), /draw callback/);
  st.rows.fill(0);
  st.update(0.02, 1);
  assert.deepEqual(Array.from(W.data.slice(16, 21)), [1, 1, 0, 2, 1]);
  assert.equal(W.data[24], 0.0625);
  assert.equal(W.data[27], 16);
  assert.deepEqual([W.data[3], W.data[35], W.data[51]], [3, 0, 3]);
  st.update(0.02, 2);
  assert.deepEqual([W.data[3], W.data[19], W.data[35], W.data[51]], [3, 0, 0, 3]);
  assert.equal(st.rows[0], 1);
});

test('vortex phase rotates the streaks around an arbitrary axis while preserving their height', () => {
  const B = makeBuilder(1);
  const frame = K.frameSplats(B, 4, (draw, dt, t) => {
    draw.vortex([1, 2, 3], {
      axis: [2, 0, 0],
      radius: [1, 2],
      height: 4,
      turns: 0,
      phase: t * Math.PI / 2,
      arms: 2,
      segments: 2
    });
  });
  const W = B.finish();
  const st = K.stage(W);
  st.add(frame);
  st.update(0, 0);
  assert.deepEqual([0, 16, 32, 48].map(i => W.data[i]), [2, 4, 2, 4]);
  near(W.data[2], 1.75);
  near(W.data[34], 4.25);
  st.update(0.02, 1);
  near(W.data[1], 3.25);
  near(W.data[2], 3);
  near(W.data[33], 0.75);
  near(W.data[34], 3);
  assert.deepEqual([0, 16, 32, 48].map(i => W.data[i]), [2, 4, 2, 4]);
});

test('wobble is a signed offset that decays to zero between poses', () => {
  assert.deepEqual([-1, 0, 1, 2].map(t => K.wobble(t)), [0, 0, 0, 0]);
  assert.ok(K.wobble(0.125) > 0);
  assert.ok(K.wobble(0.375) < 0);
  assert.ok(K.wobble(0.625) < K.wobble(0.125));
  assert.ok(K.wobble(0.375, 1) > 0);
});

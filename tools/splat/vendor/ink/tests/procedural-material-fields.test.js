const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: K, SurfaceLook } = require('..').load();
const { geometry, materials } = K.procedural;
const near = (a, b, eps = 1e-7) => assert(Math.abs(a - b) <= eps, a + ' differs from ' + b);

test('separable distance transforms match brute force in anisotropic 2D and 3D grids', () => {
  for (const size of [[6,9],[7,1,5],[6,4,5]]) {
    const spacing = [0.2,0.8,0.37].slice(0,size.length), n = size.reduce((a,b) => a * b, 1),
      indexPoints = Array.from({ length: n }, (_, i) => size.map(w => { const n = i % w; i = Math.floor(i / w); return n; })),
      mask = Uint8Array.from(indexPoints, (_,i) => Number(i % 27 === 0 || i % 11 === 2)),
      result = geometry.distanceTransform(mask, { size, spacing, signed: true });
    for (const [i,p] of indexPoints.entries()) {
      const sq = q => p.reduce((sum,v,j) => sum + ((v - q[j]) * spacing[j]) ** 2, 0),
        best = Math.min(...indexPoints.map((q,j) => mask[i] === mask[j] ? Infinity : sq(q))),
        sample = result.at(...p);
      near(sample.squared, best);
      near(sample.distance, Math.sqrt(best) * (mask[i] ? -1 : 1));
      near(sq(indexPoints[sample.nearest]), best);
      assert.notEqual(mask[i], mask[sample.nearest]);
    }
  }
  const empty = geometry.distanceTransform([0,0,0,0], { size: [2,2] });
  assert.deepEqual(empty.at(0,0), { distance: Infinity, squared: Infinity, nearest: -1 });
  assert.equal(empty.at(-1,0), null);
  assert.throws(() => geometry.distanceTransform([0,1,1,2], { size: [2,2] }), /binary values/);
});

test('triplanar weights blend smoothly by normal and supply projection footprints', () => {
  const field = materials.triplanar([() => [1,0,0], () => [0,1,0], () => [0,0,1]], { sharpness: 4 });
  assert.deepEqual(field(0,0,0,{normal:[-1,0,0]}), [1,0,0]);
  const blend = field(0,0,0,{normal:[1,2,0]});
  near(blend[0],1/17);
  near(blend[1],16/17);
  let info;
  const sample = materials.triplanar((u,v,config) => { info = config; return 2 * u + v; }, { scale: [2,4,8] });
  near(sample(3,8,16,{normal:[0,1,0],footprint:2}), 5);
  assert.deepEqual(info, { axis: 1, sign: 1, footprint: [1,0.25] });
});

test('tangent masks follow the supplied grain and filtered coverage stays anchored as the camera rotates', () => {
  const tangent = materials.tangent((u,v) => 10 * u + v, { scale: [2,0.5] });
  near(tangent(2,1,0,{ normal: [0,0,1], tangent: [1,0,0] }), 12);
  near(tangent(2,1,0,{ normal: [0,0,1], tangent: [0,1,0] }), 1);
  const filter = materials.threshold(x => x, { level: 0, samples: 7, seed: 8 }),
    close = { normal: [0,0,1], tangent: [1,0,0], footprint: 0 },
    far = { ...close, footprint: 1 };
  assert.equal(filter(0.01,0,0,close),1);
  assert.equal(filter(-0.01,0,0,close),0);
  assert(filter(0.01,0,0,far) > 0.35 && filter(0.01,0,0,far) < 0.65);
  let seen;
  const prepared = SurfaceLook.prepare({ direction: 'x', layers: {
    paint: { type:'directionalColor', color:'#ffffff', crossColor:'#ffffff',
      mask: (x,y,z,frame) => { seen = frame; return filter(x,y,z,frame); } }
  } }, [], [0,0,1]), sample = { ...far, position: [0.01,0,0], view: [0,0,1] }, base = [0,0,0];
  const a = SurfaceLook.shade(prepared, sample, base)[0];
  assert.deepEqual(seen.tangent,[1,0,0]);
  assert.equal(seen.footprint,1);
  near(a,SurfaceLook.shade(prepared, { ...sample, view:[1,0,0.2] }, base)[0]);
});

test('palette ramps preserve anchors, interpolate perceptual lightness and retain valid sRGB', () => {
  const gray = materials.ramp(['#000000', '#ffffff'], { steps: 3 }),
    high = materials.ramp([0x2d6db6,{ at: 0.5, color: '#ef7042' },'#fffeaa'], { steps: 9, space: 'lch', hue: 'long' });
  near(gray.rgb[1][0],0.3885728590463344,1e-6);
  assert.deepEqual(gray.hex, [0x000000,0x636363,0xffffff]);
  assert.equal(high.hex[4],0xef7042);
  assert(high.rgb.every(c => c.every(v => v >= 0 && v <= 1)));
  assert(high.hex.length === 9 && new Set(high.hex).size > 7);
});

test('distance masks distinguish outer and inner ink and accept physical pixel spacing', () => {
  const size = [7,7], mask = Uint8Array.from({ length:49 }, (_,i) => Number(i%7 >= 2 && i%7 <= 4 && i >= 14 && i < 35)),
    ink = materials.outline(mask, { size, spacing:[1,0.5], outer:0.8, inner:0.6 });
  assert.equal(ink.outside[1*7+3],1);
  assert.equal(ink.outside[3*7+1],0);
  assert.equal(ink.inside[2*7+3],1);
  assert.equal(ink.inside[3*7+3],0);
});

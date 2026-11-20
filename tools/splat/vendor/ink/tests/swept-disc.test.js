const test = require('node:test');
const assert = require('node:assert/strict');
const { compile } = require('../src/swept-disc');

test('indexed strokes retain the exhaustive distances and radii on tapered self-intersecting paths', () => {
  const points = Array.from({ length: 191 }, (_, i) =>
    i % 19 === 0 ? [0, 0] : [3 * Math.sin(i * 0.247), 3 * Math.cos(i * 0.677)]);
  const radii = points.map((_, i) => 0.1 + (i % 17) * 0.09);
  const indexed = compile(points, radii);
  const segments = points.slice(1).map((_, i) => compile(points.slice(i, i + 2), radii.slice(i, i + 2)));
  for (let i = 0; i < 370; i++) {
    const x = 6 * Math.sin(i * 8.713), y = 6 * Math.cos(i * 4.134);
    let best = Infinity, radius = radii[0];
    for (const distanceAt of segments) {
      const distance = distanceAt(x, y);
      if (distance < best) {
        best = distance;
        radius = distanceAt(x, y, true);
      }
    }
    assert.equal(indexed(x, y), best);
    assert.equal(indexed(x, y, true), radius);
  }
});

test('equal distances retain the earliest segment radius regardless of search order', () => {
  const points = Array.from({ length: 38 }, (_, i) => [i + 2, 0]);
  points.push([39, 10], [3, 10]);
  for (let i = 0; i < 20; i++) points.push([3, 10 - i * 6 / 19]);
  const radii = points.map((_, i) => i < 38 ? 1 : 4);
  const distance = compile(points, radii);
  assert.equal(distance(0, 0), 1);
  assert.equal(distance(0, 0, true), 1);
});

test('distant finite queries retain the slow-path overflow behavior', () => {
  const points = Array.from({ length: 75 }, (_, i) => [i * 4, i % 2]);
  const radii = points.map(() => 0.25), distance = compile(points, radii);
  assert.equal(distance(1e160, -1e160), Math.hypot(1e160, 1e160));
  assert.equal(distance(1e160, -1e160, true), 0.25);
});

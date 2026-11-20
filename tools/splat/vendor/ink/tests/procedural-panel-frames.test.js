const { test } = require('node:test');
const assert = require('node:assert/strict');
const { procedural: P } = require('..').load().KIT;

const spec = { width: 6, height: 4, unit: [2, 2], beam: .2, braceWidth: .16 };

test('panel frames fit continuous tracks with individually keyed, clipped braces', () => {
  const result = P.panelFrames({ ...spec, braces: 'alternating' });
  assert.equal(result.postCount, 4);
  assert.equal(result.railCount, 3);
  assert.equal(result.parts.filter(part => part.role === 'brace').length, 6);
  assert(result.distance(2, 1) < 0);
  assert(result.distance(3, 2) < 0);
  assert(result.distance(1, 1) < 0);
  assert(result.distance(.65, .35) > 0);
  assert.equal(result.distance(-.01, 1), Infinity);
  assert.equal(new Set(result.parts.map(part => part.key)).size, result.parts.length);
  for (const part of result.parts) for (const [u, v] of part.polygon)
    assert(u >= 0 && u <= spec.width && v >= 0 && v <= spec.height);
});

test('a periodic frame keeps one logical post at the seam and supports per-bay policies', () => {
  const result = P.panelFrames({
    ...spec, periodic: true, braces: cell => cell.row === 0 && cell.column === 1 ? 'cross' : 'none'
  });
  assert.equal(result.postCount, 3);
  assert.equal(result.parts.filter(part => part.key === 'post/0').length, 2);
  assert.equal(result.parts.filter(part => part.role === 'brace').length, 2);
  assert.equal(result.distance(-.02, 1), result.distance(5.98, 1));
  assert(result.distance(3, 1) < 0);
  assert(result.distance(1, 1) > 0);
});

test('frame keys stay usable through openings and reject overbuilt configurations', () => {
  const result = P.panelFrames({ ...spec, braces: 'cross' });
  const mask = [[[.4, .1], [1.6, .1], [1.6, 1.6], [.4, 1.6]]];
  const clipped = P.surfaceCells.clip(result.parts, { holes: mask });
  assert(clipped.cells.some(cell => cell.key === 'brace/0/0/ascending'));
  assert(clipped.cells.some(cell => cell.key === 'post/0'));
  assert.throws(() => P.panelFrames({ ...spec, beam: 2 }), /leave room/);
  assert.throws(() => P.panelFrames({ ...spec, braces: () => 'wrong' }), /brace policy/);
  assert.throws(() => P.panelFrames({ ...spec, braces: 'cross', budget: 6 }), /member budget/);
});

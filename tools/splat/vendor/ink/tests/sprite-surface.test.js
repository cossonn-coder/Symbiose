const test = require('node:test');
const assert = require('node:assert/strict');
const { make } = require('../src/sprite-surface.js');

test('surface texels stay aligned to the authored world-space face', () => {
  const atlas = make(4, 6);
  atlas.face([2,3,4], [2,0,0], [0,1,0], 3, 2, (x,y) => x === 0 && y === 0 ? 0x12abef : x === 2 ? null : 0x091524);
  atlas.face([6,7,8], [0,0,2], [0,1,0], 2, 1, () => 0xff4939);
  const sprite = atlas.finish();
  assert.equal(sprite.width, 4);
  assert.equal(sprite.height, 3);
  assert.deepEqual(Array.from(sprite.pixels.slice(0, 4)), [0x12,0xab,0xef,255]);
  assert.equal(sprite.pixels[2 * 4 + 3], 0);
  assert.deepEqual(Array.from(sprite.pixels.slice(32, 36)), [255,73,57,255]);
  assert.deepEqual(Array.from(sprite.vertices.slice(0, 15)),
    [2,4,4,.5,.5, 4,4,4,2.5,.5, 2,3,4,.5,1.5]);
  assert.equal(sprite.vertices.length, 60);
});

test('atlas capacity errors leave a valid batch', () => {
  const atlas = make(4, 3), draw = () => 0;
  atlas.face([0,0,0],[4,0,0],[0,3,0],4,3,draw);
  assert.throws(() => atlas.face([0,0,0],[1,0,0],[0,1,0],1,1,draw), /full/);
});

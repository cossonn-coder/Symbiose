const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');

// the text module stands alone over a KIT object
function loadAscii() {
  const KIT = {};
  new Function('KIT', fs.readFileSync(path.join(__dirname, '../src/kit/kza-ascii.js'), 'utf8'))(KIT);
  return KIT.ascii;
}

test('the font has every set, and characters to write out', () => {
  const A = loadAscii().atlas();
  assert.equal(A.sets.ascii[1], 95);
  assert.equal(A.sets.braille[1], 256);
  assert(A.sets.symbols[1] > 200 && A.sets.blocks[1] === 49);
  assert.equal(A.chars.length, A.glyphs);
  assert(A.chars.includes('@') && A.chars.includes('░') && A.chars.includes('⣿'));
  assert.equal(A.font.data.length, A.font.w * A.font.h);
});

test('a shape is matched by shape: a bright left half reads as a character inked down its left', () => {
  const K = loadAscii(), w = 6, h = 8, rgb = new Uint8Array(w * h * 3);
  for (let y = 0; y < h; y++) for (let x = 0; x < 3; x++) rgb.fill(255, (y * w + x) * 3, (y * w + x) * 3 + 3);
  const T = K.draw({ w, h, rgb }, { g: 1, px: 1, pal: [0x000000, 0xffffff] });
  assert.equal(T.cols, 1); assert.equal(T.rows, 1);
  const A = K.atlas(), g = T.glyph[0];
  let left = 0, right = 0;
  for (let y = 0; y < 8; y++) for (let x = 0; x < 6; x++) { const on = A.font.data[((g / A.per | 0) * 8 + y) * A.font.w + (g % A.per) * 6 + x] > 127; if (on) x < 3 ? left++ : right++; }
  assert(left > right * 2, 'inked on the left: ' + T.text);
});

test('a flat field is shading in its own colour, dark is blank, and the colours are the palette\'s', () => {
  const K = loadAscii(), w = 24, h = 16, rgb = new Uint8Array(w * h * 3);
  for (let i = 0; i < w * h; i++) rgb.set(i % w < 12 ? [0, 0, 0] : [80, 120, 200], i * 3);
  const pal = [0x000000, 0x2a3c64, 0x5078c8, 0xa0c0f0], T = K.draw({ w, h, rgb }, { g: 1, px: 1, pal });
  assert.equal(T.text.split('\n')[0][0], ' ');
  for (let i = 0; i < T.cols * T.rows; i++) assert(T.fg[i] < pal.length && T.bg[i] < pal.length);
  const right = T.cols - 1; assert(T.bg[right] === 2 || T.bg[right] === 1);
});

test('a zone grows, holds, and draws back', () => {
  const z = loadAscii().zone({ at: [1, 2, 3], r: 10, t0: 1, grow: 2, hold: 1, back: 1, soft: 2 });
  assert.equal(z.at(0.5), null);
  assert.equal(z.at(3)[3], 10);
  assert(z.at(4.5)[3] < 10);
  assert.equal(z.at(5.5), null);
});

test('a dab asks for text, and for its own set, in bits that leave the wind and coverage alone', () => {
  const K = loadAscii();
  assert.equal(K.setOf(0), -1);
  assert.equal(K.setOf(2048), 0);
  assert.equal(K.setOf(2048 + 4096), 1);
  assert.equal(K.setOf(2048 + 16384), 2);
  assert.equal(K.setOf(2048 + 4096 + 16384 + 8192 + 32768), 3);
});

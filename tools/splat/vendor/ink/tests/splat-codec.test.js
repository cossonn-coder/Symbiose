const test = require('node:test');
const assert = require('node:assert/strict');
const { gzipSync } = require('node:zlib');
const studio = require('..');
const { KIT, SCENES } = studio.load();
const codec = KIT.procedural.splatCodec;
const covariance = [4, 5, 6, 8, 9, 10];

test('native rows preserve order, exact bits and the requested geometric limits', () => {
  const count = 4100;
  const data = new Float32Array((count + 2) * 16).subarray(16);
  const bits = new Uint32Array(data.buffer, data.byteOffset, data.length);
  for (let i = 0; i < count; i++) {
    const a = i * 0.017, x = Math.cos(a), y = Math.sin(a);
    data.set([i * 0.004, -Math.sin(a), i < 2048 ? 5 : 500000 + (i % 3) * 1000,
      3, 1 - 0.9*x*x, -0.9*x*y, 0, i, 1 - 0.9*y*y, 0, 1, i % 9, 0, 0, 0, 0], i * 16);
  }
  bits[12] = 0x7f800001;
  bits[16 + 13] = 0x80000000;
  // A triaxial pose and an axial covariance outside the compact range escape exactly.
  data[2 * 16 + 8] = 3;
  data[3 * 16 + 4] = 1e-26;
  data[3 * 16 + 8] = 2e-26;
  data[3 * 16 + 10] = 2e-26;

  const lossless = codec.decode(codec.encode(data, count, { maxPositionError: 0, maxCovarianceError: 0 }));
  assert.equal(lossless.count, count);
  assert.deepEqual(new Uint32Array(lossless.data.buffer), bits.subarray(0, count * 16));
  const encoded = codec.encode(data, count);
  const slice = new Uint8Array(encoded.length + 6).subarray(3, 3 + encoded.length);
  slice.set(encoded);
  const roundtrip = codec.decode(slice);
  const decoded = new Uint32Array(roundtrip.data.buffer);
  let changed = 0;
  for (let row = 0; row < count; row++) {
    const at = 16 * row;
    for (let field = 0; field < 16; field++) {
      if (field < 3) assert(Math.abs(roundtrip.data[at + field] - data[at + field]) <= 0.0001);
      else if (!covariance.includes(field) || row === 2 || row === 3) assert.equal(decoded[at + field], bits[at + field]);
    }
    let error = 0, scale = 0;
    for (const field of covariance) {
      const weight = [4, 8, 10].includes(field) ? 1 : 2;
      const before = data[at + field], after = roundtrip.data[at + field];
      error += weight * (after - before) ** 2;
      scale += weight * before ** 2;
    }
    assert(error <= 0.004 ** 2 * scale);
    if (error > 0) changed++;
  }
  assert(changed > 2000);
  assert(encoded.length < lossless.data.byteLength / 2);
});

test('codec validates headers, complete sections and row limits before decoding', () => {
  const empty = codec.encode(new Float32Array(0));
  assert.deepEqual(codec.decode(empty), { count: 0, data: new Float32Array(0) });
  const bytes = codec.encode(new Float32Array(16 * 2200));
  assert.throws(() => codec.decode(bytes, { maxRows: 2199 }), /row limit/i);
  for (let i = 0; i < bytes.length; i++) assert.throws(() => codec.decode(bytes.subarray(0, i)));
  const bad = bytes.slice();
  bad[8] = 255;
  assert.throws(() => codec.decode(bad), /column/);
  const trailing = new Uint8Array(bytes.length + 1);
  trailing.set(bytes);
  assert.throws(() => codec.decode(trailing), /trailing/);
  assert.throws(() => codec.encode(Float32Array.of(NaN, ...Array(15).fill(0))), /finite/);
});

test('compressed Old Idol retains its pixel appearance from multiple cameras', () => {
  const scene = SCENES.find(s => s.id === 'idol');
  const world = scene.build(scene.seed);
  const bytes = codec.encode(world.data, world.count);
  const raw = Buffer.from(world.data.buffer, world.data.byteOffset, 64 * world.count);
  assert(gzipSync(bytes).length < gzipSync(raw).length / 3);
  const decoded = { ...world, ...codec.decode(bytes) };
  for (const offset of [0, 0.7, 1.9]) {
    const options = { w: 256, h: 192, yaw: world.cam.yaw + offset, zoom: offset ? 1.35 : 1 };
    const before = studio.render(world, options), after = studio.render(decoded, options);
    let changed = 0;
    for (let i = 0; i < before.rgb.length; i += 3) {
      if (Math.max(...[0, 1, 2].map(c => Math.abs(before.rgb[i + c] - after.rgb[i + c]))) > 8) changed++;
    }
    assert(changed / (before.w * before.h) < 0.004, 'visible differences at camera offset ' + offset);
  }
});

test('version one retains its header, column order and little-endian exact floats', () => {
  const row = new Float32Array(16);
  row[0] = 1;
  row[7] = 0x654321;
  row[12] = -0;
  const fixture = Buffer.from('4952433101000000' +
    '000000803f' + '0000000000'.repeat(6) + '004286ca4a' +
    '0000000000'.repeat(4) + '0000000080' + '0000000000'.repeat(3), 'hex');
  assert.deepEqual(codec.encode(row), new Uint8Array(fixture));
  assert.deepEqual(codec.decode(fixture).data, row);
});

// Run from a Node checkout. Compression totals include the codec header, but not auxiliary world data.
const { gzipSync, brotliCompressSync, constants } = require('node:zlib');
const { SCENES, KIT } = require('..').load();
const codec = KIT.procedural.splatCodec;
const selected = process.argv.slice(2);
const brotli = bytes => brotliCompressSync(bytes, { params: { [constants.BROTLI_PARAM_QUALITY]: 5 } }).length;
const median = times => times.sort((a, b) => a - b)[times.length >>> 1].toFixed(2);
const measurements = [];
for (const scene of SCENES) {
  if (selected.length && !selected.includes(scene.id)) continue;
  const world = scene.build(scene.seed);
  const raw = Buffer.from(world.data.buffer, world.data.byteOffset, world.count * 64);
  let bytes = codec.encode(world.data, world.count);
  codec.decode(bytes);
  const encode = [],
    decode = [];
  for (let i = 0; i < 7; i++) {
    const start = performance.now();
    bytes = codec.encode(world.data, world.count);
    const encoded = performance.now();
    codec.decode(bytes);
    encode.push(encoded - start);
    decode.push(performance.now() - encoded);
  }
  measurements.push({
    scene: scene.id,
    splats: world.count,
    bakedBytes: raw.length,
    encodedBytes: bytes.length,
    rawGzip: gzipSync(raw).length,
    encodedGzip: gzipSync(bytes).length,
    rawBrotli: brotli(raw),
    encodedBrotli: brotli(bytes),
    encodeMs: median(encode),
    decodeMs: median(decode)
  });
}
console.table(measurements);

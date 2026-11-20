const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const zlib = require('node:zlib');
const { execFileSync } = require('node:child_process');
const { KIT, makeBuilder, makeSculpt } = require('..').load();
const PNG = require('../cli/png.js');

const close = (actual, expected, distance = 1e-6) => assert(Math.abs(actual - expected) < distance, actual + ' vs ' + expected);
const vertex = (mesh, i) => Array.from(mesh.pos.slice(i * 3, i * 3 + 3));

test('calibrated depth reconstructs camera rays and keeps projected RGB on dabs', () => {
  const model = KIT.depth.fromMap({
    width: 2, height: 2, depth: [2, 4, 2, 4], maxDepthJump: 2,
    camera: { type: 'perspective', fx: 4, fy: 2, cx: 0, cy: 0 },
    image: { width: 2, height: 2, data: new Uint8Array([255, 0, 0, 0, 255, 0, 0, 0, 255, 248, 138, 32]) }
  });
  assert.deepEqual(vertex(model.front, 1), [1, 0, -4]);
  assert.deepEqual(vertex(model.front, 2), [0, -1, -2]);
  assert.equal(KIT.mesh.info(model.mesh).open, 0);
  const world = model.world();
  assert.equal(world.count, 4);
  assert.equal(world.data[7], 255);
  assert.equal(world.data[23], 255 * 256);
  assert.equal(world.data[39], 255 * 65536);
  assert(model.front.tri.length === 6 && model.mesh.tri.length === 36);
});

test('the backed mesh gives a signed distance field that can be exported, loaded and composed', () => {
  const model = KIT.depth.fromMap({ width: 4, height: 4, depth: new Float32Array(16).fill(2), thickness: 0.4 });
  const grid = model.field({ cells: 44 });
  assert(grid.sd(0, 0, -2.2) < -0.13);
  assert(grid.sd(0, 0, -1.8) > 0.15);
  assert(grid.sd(0, 0, -2.6) > 0.15);
  assert(grid.sd(1, 0, -2.2) > 0.10);
  close(grid.sd(0, 0, -2), 0, 0.04);
  const restored = KIT.depth.readField({
    format: 'ink-studio-sdf-grid-v1', origin: grid.lo, spacing: grid.h, dimensions: grid.n, values: Array.from(grid.D)
  });
  close(restored.sd(0.13, 0.29, -2.13), grid.sd(0.13, 0.29, -2.13));
  const S = KIT.sculpt(makeSculpt(makeBuilder(1)));
  const solid = model.addSolid(S, { r: [1, 2, 3] }, { cells: 44 });
  assert.equal(solid.field, grid);
  S.ready();
  assert(S.sdf(0, 0, -2.2) < 0);
});

test('depth steps and masked holes do not get bridged, and isolated pixels remain usable', () => {
  const width = 7, height = 4;
  const depth = Array.from({ length: width * height }, (_, i) => i % width < 4 ? 1 : 2);
  const mask = depth.map((_, i) => i % width === 3 ? 0 : 1);
  const model = KIT.depth.fromMap({ width, height, depth, mask, maxDepthJump: 0.15 });
  assert.equal(model.count, 24);
  for (let i = 0; i < model.front.tri.length; i += 3) {
    const z = [...model.front.tri.slice(i, i + 3)].map(j => vertex(model.front, j)[2]);
    assert.equal(Math.max(...z), Math.min(...z));
  }
  assert.equal(KIT.mesh.info(model.mesh).open, 0);
  const single = KIT.depth.fromMap({
    width: 2, height: 1, depth: [1, 1], alphaMask: true,
    image: { width: 2, height: 1, channels: 4, data: new Uint8Array([255, 0, 0, 255, 255, 255, 0, 0]) }
  });
  assert.equal(single.count, 1);
  assert.equal(single.front.tri.length, 6);
  assert.equal(KIT.mesh.info(single.mesh).open, 0);
  assert.throws(() => KIT.depth.fromMap({ width: 2, height: 1, depth: [0, NaN] }), /no valid samples/);
});

test('islands meeting at one sample stay closed after backing is added', () => {
  const model = KIT.depth.fromMap({
    width: 3, height: 3, depth: [1.9, 1.9, 0, 1.9, 2, 2.1, 0, 2.1, 2.1], maxDepthJump: 0.15
  });
  assert.equal(model.count, 7);
  assert.equal(KIT.mesh.info(model.mesh).open, 0);
  const example = KIT.depth.fromMap(require('../examples/depth-map.js').input());
  assert.equal(KIT.mesh.info(example.mesh).open, 0);
});

// A small grayscale PNG with values chosen to differ only in the low byte.
function png16(file) {
  const sig = Buffer.from('89504e470d0a1a0a', 'hex');
  const chunk = (type, body) => {
    const buf = Buffer.alloc(body.length + 12);
    buf.writeUInt32BE(body.length);
    buf.write(type, 4);
    body.copy(buf, 8);
    let crc = 0xffffffff;
    for (const byte of buf.subarray(4, -4)) {
      crc ^= byte;
      for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ ((crc & 1) ? 0xedb88320 : 0);
    }
    buf.writeUInt32BE((crc ^ 0xffffffff) >>> 0, buf.length - 4);
    return buf;
  };
  const header = Buffer.alloc(13);
  header.writeUInt32BE(2, 0);
  header.writeUInt32BE(2, 4);
  header[8] = 16;
  const raw = Buffer.from([0, 0x04, 0x11, 0x04, 0x21, 1, 0x04, 0x11, 0x00, 0x10]);
  fs.writeFileSync(file, Buffer.concat([sig, chunk('IHDR', header), chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]));
}

test('the CLI accepts 16-bit PNG depth and aligned colour, and writes four usable outputs', () => {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-depth-'));
  try {
    const depth = path.join(tmp, 'range.png'), image = path.join(tmp, 'rgb.png'), out = path.join(tmp, 'out');
    png16(depth);
    const rgb = new Uint8Array([255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 0]);
    PNG.write(image, 2, 2, rgb);
    assert.deepEqual(PNG.read(image).rgb, rgb);
    assert.deepEqual([...PNG.raster(depth).data.filter((_, i) => i % 4 === 0)], [1041, 1057, 1041, 1057]);
    execFileSync(process.execPath, [
      path.join(__dirname, '../cli/ink-studio.js'), 'depth', depth, '--image', image,
      '--depth-scale', '0.001', '--cells', '20', '--w', '80', '--h', '64', '--out-dir', out
    ]);
    assert.deepEqual(fs.readdirSync(out).sort(), ['mesh.obj', 'preview.png', 'sdf.json', 'splats.json']);
    const splats = JSON.parse(fs.readFileSync(path.join(out, 'splats.json'), 'utf8'));
    assert.equal(splats.count, 4);
    close(splats.data[2], -1.041);
    close(splats.data[18], -1.057);
    assert.equal(splats.data[7], 255);
    const mesh = KIT.mesh.obj(fs.readFileSync(path.join(out, 'mesh.obj'), 'utf8'));
    assert.equal(KIT.mesh.info(mesh).open, 0);
    const sdf = KIT.depth.readField(JSON.parse(fs.readFileSync(path.join(out, 'sdf.json'), 'utf8')));
    assert(sdf.sd(0, 0, -1.085) < 0);
    assert(PNG.read(path.join(out, 'preview.png')).w >= 80);
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
});

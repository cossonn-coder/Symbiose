const test = require('node:test');
const assert = require('node:assert/strict');
const { geometry } = require('..').load().KIT.procedural;

test('height clipping keeps the face attributes and does not cap an open cut', () => {
  const builder = geometry.builder();
  builder.quad([-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0], {
    owner: 'rim', surface: 'reveal', material: 'stone'
  }, [[0, 0], [1, 0], [1, 1], [0, 1]]);
  const mesh = builder.finish();
  const cut = geometry.clipHeightMesh(mesh, (x, z) => 0, { slopeBound: 0 });
  assert.deepEqual(cut.bounds, { min: [-1, 0, 0], max: [1, 1, 0] });
  assert.equal(cut.positions.length, 27);
  assert.equal(cut.groups[0].surface, 'reveal');
  assert.equal(cut.groups[0].owner, 'rim');
  for (let i = 0; i < cut.positions.length / 3; i++) {
    const [x, y] = cut.positions.subarray(i * 3, i * 3 + 2);
    assert.equal(cut.uv[i * 2], (x + 1) / 2);
    assert.equal(cut.uv[i * 2 + 1], (y + 1) / 2);
    assert.equal(cut.normals[i * 3 + 2], 1);
  }
  assert.throws(() => geometry.clipHeightMesh(mesh, () => NaN, { slopeBound: 0 }), /finite/);
  assert.throws(() => geometry.clipHeightMesh(mesh, () => 0, { slopeBound: 2, budget: 2 }), /budget/);
});

test('adaptive height clipping catches terrain crossing between same-side vertices', () => {
  const builder = geometry.builder();
  builder.quad([-1, 0, -1], [1, 0, -1], [1, 0, 1], [-1, 0, 1]);
  const height = x => .32 - Math.abs(x);
  const mesh = geometry.clipHeightMesh(builder.finish(), height, { slopeBound: 1, resolution: .08 });
  assert(mesh.positions.length > 18);
  for (let i = 0; i < mesh.positions.length; i += 3) {
    const [x, y, z] = mesh.positions.subarray(i, i + 3);
    assert(y >= height(x, z) - 1e-7);
  }
  for (let i = 0; i < mesh.positions.length; i += 9) {
    const xs = [mesh.positions[i], mesh.positions[i + 3], mesh.positions[i + 6]];
    assert(xs.every(x => x < 0) || xs.every(x => x > 0));
  }
});

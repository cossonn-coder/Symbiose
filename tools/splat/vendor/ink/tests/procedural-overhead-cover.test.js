const test = require('node:test');
const assert = require('node:assert/strict');
const P = require('..').load().KIT.procedural;

function slab(left, right, front, back, height) {
  const corner = (x, z) => [x, height(x, z), z];
  const a = corner(left, front), b = corner(left, back);
  const c = corner(right, front), d = corner(right, back);
  return { positions: Float32Array.from([...a, ...b, ...c, ...b, ...c, ...d]) };
}

test('overhead cover preserves open gaps and lets the topmost surface receive coating', () => {
  const { rasterize, exposure } = P.overheadCover;
  const low = slab(-2, -1, -1, 1, () => 0), high = slab(-2, -1, -1, 1, () => 2);
  const separated = slab(1, 2, -1, 1, () => 1);
  const field = rasterize({ meshes: [high, separated, low] }, { spacing: .25 });
  assert.deepEqual(field.origin, [-2, -1]);
  assert.deepEqual([field.width, field.height], [16, 8]);
  assert.equal(exposure(field, [-1.5, 0, 0]), 0);
  assert.equal(exposure(field, [-1.5, 2, 0]), 1);
  assert.equal(exposure(field, [1.5, .5, 0]), 0);
  assert.equal(exposure(field, [1.5, 1, 0]), 1);
  assert.equal(exposure(field, [0, -1, 0]), 1);
  assert.equal(exposure(field, [-10, 0, 0]), 1);
  assert.equal(exposure(field, [2, -1, 0]), .5);
  const amount = (point) => P.environmentFields.coating.amount({
    normal: [0, 1, 0], exposure: exposure(field, point), load: .8
  });
  assert.equal(amount([-1.5, 0, 0]), 0);
  assert(amount([-1.5, 2, 0]) > 0);
});

test('sloping surfaces stay exposed and the caller controls clearance and resolution', () => {
  const { rasterize, exposure } = P.overheadCover;
  const profile = x => 2 * x + 3;
  const field = rasterize({ meshes: [slab(0, 25, 0, 2, profile)] },
    { spacing: .05, maxSize: 25, clearance: .05, softness: .1 });
  assert.deepEqual([field.step, field.width, field.height], [1, 25, 2]);
  const normal = [-2, 1, 0], x = 3.83, z = 1, roof = profile(x);
  assert.equal(exposure(field, [x, roof, z], normal), 1);
  assert(exposure(field, [x, roof, z]) < 1);
  assert.equal(exposure(field, [x, roof - .2, z], normal), 0);
  assert(Math.abs(exposure(field, [x, roof - .1, z], normal) - .5) < 1e-9);
  assert.equal(exposure(rasterize(), [x, 0, z]), 1);
  assert.throws(() => rasterize({ meshes: [{ positions: [0, 0, 0] }] }), /XYZ triangles/);
  assert.throws(() => rasterize({ meshes: [slab(0, 1, 0, 1, () => Infinity)] }), /finite/);
});

test('analytic roofs and triangle meshes contribute to the same field', () => {
  const { rasterize, exposure } = P.overheadCover;
  const field = rasterize({
    meshes: [slab(-1, 0, -1, 1, () => 1)],
    surfaces: [{ min: [-1, -1], max: [1, 1], heightAt(x) { return x < 0 ? 2 : null; } }]
  }, { spacing: .25 });
  assert.equal(exposure(field, [-.5, 1.5, 0]), 0);
  assert.equal(exposure(field, [-.5, 2, 0]), 1);
  assert.equal(exposure(field, [.5, 0, 0]), 1);
  assert.equal(exposure(field, [0, 0, 0]), .5);
});

test('indexed assets project the same cover as their expanded triangles', () => {
  const { rasterize, exposure } = P.overheadCover;
  const positions = new Float32Array([0,1,0, 0,1,1, 1,1,0, 1,1,1]);
  const indexed = { positions, triangles:new Uint16Array([0,1,2,1,2,3]) };
  const field = rasterize({ meshes:[indexed] }, { spacing:.125 });
  assert.deepEqual(field,rasterize({ meshes:[slab(0,1,0,1,()=>1)] },{ spacing:.125 }));
  assert.equal(exposure(field,[.5,0,.5]),0);
  assert.throws(()=>rasterize({meshes:[{...indexed,triangles:[0,1,8]}]}),/invalid triangle indices/);
});

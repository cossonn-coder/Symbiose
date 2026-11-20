const test = require('node:test'),
  assert = require('node:assert/strict'),
  K = require('..').load().KIT,
  A = K.procedural,
  V = K.V;
const box = { min: [-1, -1, -1], max: [1, 1, 1] },
  meta = { owner: 'field', surface: 'shell', material: 'stone' };
function area(mesh) {
  let n = 0;
  for (let i = 0; i < mesh.positions.length; i += 9) {
    const p = [0, 1, 2].map(j => Array.from(mesh.positions.slice(i + j * 3, i + j * 3 + 3)));
    n += V.len(V.cross(V.sub(p[1], p[0]), V.sub(p[2], p[0]))) / 2;
  }
  return n;
}
test('an implicit plane has exact area and faces away from the negative field', () => {
  const m = A.geometry.implicitSurface(p => p[0] - 0.13, box, { resolution: 0.23, meta });
  assert(Math.abs(area(m) - 4) < 1e-5);
  for (let i = 0; i < m.positions.length; i += 3) {
    assert(Math.abs(m.positions[i] - 0.13) < 1e-6);
    assert(m.normals[i] > 0.999);
  }
  assert(m.groups.every(g => g.owner === 'field' && g.material === 'stone'));
});
test('implicit curved shells are finite, outward and converge near their analytic area', () => {
  const m = A.geometry.implicitSurface(p => Math.hypot(...p) - 0.7, box, { resolution: 0.13, meta });
  assert(Math.abs(area(m) - 4 * Math.PI * 0.7 ** 2) < 0.12);
  for (let i = 0; i < m.positions.length; i += 3) {
    const p = Array.from(m.positions.slice(i, i + 3)),
      n = Array.from(m.normals.slice(i, i + 3));
    assert(V.dot(p, n) > 0.5);
  }
  assert(m.positions.every(Number.isFinite));
});
test('edge refinement resolves a nonlinear crossing inside a coarse cell', () => {
  const field = ([x]) => x ** 3 - 0.033;
  const options = { resolution: 0.5, meta };
  const linear = A.geometry.implicitSurface(field, box, options);
  const refined = A.geometry.implicitSurface(field, box, { ...options, edgeRefinements: 10 });
  const error = mesh => Math.max(...mesh.positions.filter((_, i) => i % 3 === 0)
    .map(x => Math.abs(x - Math.cbrt(0.033))));
  assert(error(linear) > 0.1);
  assert(error(refined) < 0.001);
  assert.deepEqual(refined.sampling, linear.sampling);
  assert.throws(() => A.geometry.implicitSurface(field, box, { edgeRefinements: 13 }), /budget/);
});
test('the streamed implicit triangles match the mesh facets and sampling budget', () => {
  const options = {resolution:.21, maxCells:900, edgeRefinements:2,
    prepareColumn:(x,z)=>y=>x*x+y*y+z*z-.49};
  const field = ([x,y,z])=>x*x+y*y+z*z-.49;
  const mesh = A.geometry.implicitSurface(field,box,options), positions=[], normals=[];
  const sampling = A.geometry.implicitTriangles(field,box,options,(a,b,c,n)=>{
    positions.push(...a,...b,...c);
    normals.push(...n,...n,...n);
  });
  assert.deepEqual(Float32Array.from(positions),mesh.positions);
  assert.deepEqual(Float32Array.from(normals),mesh.normals);
  assert.deepEqual(sampling,mesh.sampling);
  assert.throws(()=>A.geometry.implicitTriangles(field,box,options),/output callback/);
});
test('sampling is bounded, empty fields stay empty and invalid inputs fail promptly', () => {
  let calls = 0;
  const m = A.geometry.implicitSurface(
    p => {
      calls++;
      return p[1];
    },
    box,
    { resolution: 0.000001, maxCells: 1000 }
  );
  assert(m.sampling.cells <= 1000);
  assert(calls <= 8000);
  assert.equal(A.geometry.implicitSurface(() => 1, box).bounds, null);
  assert.throws(() => A.geometry.implicitSurface(() => NaN, box), /finite/);
  assert.throws(() => A.geometry.implicitSurface(() => 0, { min: [-1e308, -1, -1], max: [1e308, 1, 1] }), /extent/);
  assert.throws(() => A.geometry.implicitSurface(() => 0, box, { maxCells: 3000000 }), /budget/);
});
test('surface clipping interpolates UVs and preserves metadata without making a cap', () => {
  const b = A.geometry.builder();
  b.quad([-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0], meta, [
    [0, 0],
    [1, 0],
    [1, 1],
    [0, 1]
  ]);
  const m = b.finish(),
    before = structuredClone(m),
    c = A.geometry.clipSurface(m, [{ normal: [2, 0, 0], offset: 0 }]);
  assert(Math.abs(area(c) - 2) < 1e-6);
  assert(c.groups.every(g => g.owner === 'field' && g.surface === 'shell'));
  for (let i = 0; i < c.positions.length; i += 3) {
    assert(c.positions[i] <= 1e-7);
    assert.equal(c.positions[i + 2], 0);
    assert(Math.abs(c.uv[(i / 3) * 2] - (c.positions[i] + 1) / 2) < 1e-6);
    assert(c.normals[i + 2] > 0.99);
  }
  assert.deepEqual(m, before);
  const sphere = A.geometry.implicitSurface(p => Math.hypot(...p) - 0.7, box);
  const half = A.geometry.clipSurface(sphere, [{ normal: [1, 0, 0], offset: 0 }]);
  let caps = 0;
  for (let i = 0; i < half.positions.length; i += 9)
    if ([0, 3, 6].every(j => Math.abs(half.positions[i + j]) < 1e-7)) caps++;
  assert.equal(caps, 0);
});
test('clipping validates triangle spans and all attribute buffers, including discarded vertices', () => {
  const b = A.geometry.builder();
  b.triangle([0, 0, 0], [1, 0, 0], [0, 1, 0], meta);
  const m = b.finish();
  for (const bad of [
    { ...m, normals: new Float32Array(0) },
    { ...m, uv: Float32Array.of(NaN, 0, 0, 0, 0, 0) },
    { ...m, groups: [{ ...m.groups[0], count: 6 }] }
  ])
    assert.throws(() => A.geometry.clipSurface(bad, []), /clipping/);
  assert.throws(() => A.geometry.clipSurface(m, [{ normal: [0, 0, 0], offset: 0 }]), /plane normals/);
});


test('prepared implicit columns produce the same mesh and keep ordinary edge refinement', () => {
  let columns = 0, samples = 0;
  const prepare = (x, z) => y => x * x + z * z + y * y - 0.49;
  const field = ([x, y, z]) => prepare(x, z)(y);
  const options = { resolution: 0.27, edgeRefinements: 3, meta };
  const baseline = A.geometry.implicitSurface(field, box, options);
  const mesh = A.geometry.implicitSurface(p => {
    samples++;
    return field(p);
  }, box, {
    ...options,
    prepareColumn(x, z) {
      columns++;
      return prepare(x, z);
    }
  });
  assert.deepEqual(mesh, baseline);
  const [nx, , nz] = mesh.sampling.counts;
  assert.equal(columns, (nx + 1) * (nz + 1));
  assert(samples > 0, 'edge refinement still queries the regular field');
  const columnOnly = A.geometry.implicitSurface(() => { throw new Error('lattice used the regular field'); },
    box, { prepareColumn: prepare });
  assert(columnOnly.positions.length > 0);
  assert.throws(() => A.geometry.implicitSurface(field, box, { prepareColumn: () => 0 }), /column/);
  assert.throws(() => A.geometry.implicitSurface(field, box, { prepareColumn: () => () => Infinity }), /finite/);
});

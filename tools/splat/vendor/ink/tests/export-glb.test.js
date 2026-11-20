const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const studio = require('..');
const lib = studio.load(), K = lib.KIT;
const puppet = require('../examples/puppet.js')(lib);
const bounds = { min: [-1.3, -1.3, -1.3], max: [1.3, 1.3, 1.3] };
const sphere = (x, y, z) => Math.hypot(x, y, z) - 1;

function parseGlb(file) {
  const bytes = fs.readFileSync(file), jsonEnd = 20 + bytes.readUInt32LE(12);
  const gltf = JSON.parse(bytes.subarray(20, jsonEnd));
  const bin = bytes.subarray(jsonEnd + 8);
  const data = index => {
    const accessor = gltf.accessors[index], view = gltf.bufferViews[accessor.bufferView];
    const [read, step] = {
      5121: ['readUInt8', 1], 5123: ['readUInt16LE', 2], 5125: ['readUInt32LE', 4], 5126: ['readFloatLE', 4]
    }[accessor.componentType];
    const components = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 }[accessor.type];
    return Array.from({ length: accessor.count }, (_, i) => Array.from({ length: components }, (_, c) =>
      bin[read]((view.byteOffset || 0) + (accessor.byteOffset || 0) +
        i * (view.byteStride || components * step) + c * step)
    ));
  };
  return { bytes, gltf, data };
}

function meshMetrics(points, faces) {
  const edges = new Map();
  const keys = points.map(p => p.map(v => Math.round(v * 1e6)).join('/'));
  let volume = 0, area = Infinity;
  for (const face of faces) {
    const [a, b, c] = face.map(i => points[i]);
    const normal = K.V.cross(K.V.sub(b, a), K.V.sub(c, a));
    area = Math.min(area, K.V.len(normal) / 2);
    volume += K.V.dot(a, normal) / 6;
    for (let j = 0; j < 3; j++) {
      const k = [keys[face[j]], keys[face[(j + 1) % 3]]].sort().join('|');
      edges.set(k, (edges.get(k) || 0) + 1);
    }
  }
  return { unique: new Set(keys).size, volume, area, badEdges: [...edges.values()].filter(n => n !== 2).length };
}

test('SDF export keeps indexed, outward closed surfaces with inner walls facing into cavities', () => {
  for (const method of ['surfaceNets', 'dualContour', 'tetrahedra']) {
    const mesh = K.model.fromSdf((x, y, z) => Math.max(sphere(x, y, z), 0.55 - Math.hypot(x, y, z)),
      { bounds, resolution: 0.145, method });
    const faces = mesh.faces.flatMap(f => f.length === 3 ? [f] : [[f[0], f[1], f[2]], [f[0], f[2], f[3]]]);
    const inner = faces.filter(f => Math.hypot(...mesh.points[f[0]]) < 0.7);
    assert.ok(meshMetrics(mesh.points, inner).volume < 0);
    const metrics = meshMetrics(mesh.points, faces);
    assert.ok(metrics.volume > 3);
    assert.equal(metrics.badEdges, 0);
    assert.ok(mesh.points.length < faces.length);
  }
  assert.throws(() => K.model.fromSdf(sphere, { bounds: { min: [-1, -1, -1], max: [1, 1, 1] }, resolution: 0.1 }), /positive at the sampling bounds/);
});

test('JSON dioramas export independently skinned parts and sample their runtime pose', () => {
  const spec = {
    id: 'jointed',
    solids: [
      { kind: 'ground', rad: 2 },
      { kind: 'ball', at: [-0.9, 1, 0], r: 0.2 },
      { kind: 'ball', at: [0, 1, 0], r: 0.6, part: 'body' },
      { kind: 'ball', at: [0, 2, 0], r: 0.35, part: 'head' }
    ],
    parts: { body: { joint: [0, 0.7, 0] }, head: { joint: [0, 1.7, 0], parent: 'body' } },
    motion: [{ part: 'body', do: 'spin', speed: 1 }, { part: 'head', do: 'turn', axis: [0, 0, 1], period: 1 }]
  };
  const scene = K.diorama.scene(spec), model = scene.model(1, { duration: 0.5, fps: 4 });
  assert.deepEqual(model.joints.map(({ name, parent }) => [name, parent]), [['body', null], ['head', 0]]);
  assert.equal(model.meshes[0].static, true);
  assert.deepEqual(model.meshes[2].weights[0], [[1, 1]]);
  const world = scene.build(1);
  world.anim.update(0, 0);
  world.anim.update(0.25, 0.25);
  for (let i = 0; i < model.joints.length; i++) {
    const offset = world.lab.rig.names.indexOf(model.joints[i].name) * 12;
    assert.deepEqual(model.animations[0].frames[1].matrices[i], [...world.lab.rig.M.slice(offset, offset + 12)]);
  }
});

const transform = (matrix, point) => [0, 1, 2].map(i =>
  matrix[i] * point[0] + matrix[4 + i] * point[1] + matrix[8 + i] * point[2] + matrix[12 + i]);
const matrixMul = (a, b) => b.map((_, i) => [0, 1, 2, 3].reduce((s, j) =>
  s + a[j * 4 + i % 4] * b[i - i % 4 + j], 0));
function trs(node) {
  if (node.matrix) return node.matrix;
  const [x, y, z, w] = node.rotation || [0, 0, 0, 1], [sx, sy, sz] = node.scale || [1, 1, 1];
  return [
    (1 - 2 * (y*y + z*z)) * sx, 2 * (x*y + w*z) * sx, 2 * (x*z - w*y) * sx, 0,
    2 * (x*y - w*z) * sy, (1 - 2 * (x*x + z*z)) * sy, 2 * (y*z + w*x) * sy, 0,
    2 * (x*z + w*y) * sz, 2 * (y*z - w*x) * sz, (1 - 2 * (x*x + y*y)) * sz, 0,
    ...(node.translation || [0, 0, 0]), 1
  ];
}

test('GLB export writes a clean UV atlas and reproduces the puppet deformation', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-glb-test-'));
  t.after(() => fs.rmSync(dir, { force: true, recursive: true }));
  const file = path.join(dir, 'puppet.glb'), model = puppet.model(puppet.seed);
  const report = studio.exportGlb(model, { out: file, textureSize: 512 });
  const { gltf, data, bytes } = parseGlb(file), p = gltf.meshes[0].primitives[0], attr = p.attributes;
  const verts = data(attr.POSITION), indices = data(p.indices).flat();
  const faces = Array.from({ length: indices.length / 3 }, (_, i) => indices.slice(i * 3, i * 3 + 3));
  const metrics = meshMetrics(verts, faces);
  assert.deepEqual([metrics.unique, faces.length, metrics.badEdges], [report.meshes[0].vertices, report.meshes[0].triangles, 0]);
  assert.ok(metrics.volume > 0 && metrics.area > 0);
  assert.equal(data(attr.NORMAL).length, verts.length);
  const uv = data(attr.TEXCOORD_0);
  assert.ok(uv.every(uv => uv.every(x => Number.isFinite(x) && x >= 0 && x <= 1)));
  assert.ok(faces.every(f => {
    const [[ax, ay], [bx, by], [cx, cy]] = f.map(i => uv[i]);
    return Math.abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax)) > 1e-9;
  }));
  assert.equal(gltf.images[0].mimeType, 'image/png');
  assert.equal(gltf.materials[0].pbrMetallicRoughness.baseColorTexture.index, 0);

  const skin = gltf.skins[0], clip = gltf.animations[0];
  const animated = structuredClone(gltf.nodes), at = 0.5;
  assert.equal(clip.name, 'Victory');
  assert.equal(skin.joints.length, model.joints.length);
  for (const channel of clip.channels) {
    const sampler = clip.samplers[channel.sampler], times = data(sampler.input).flat();
    const i = times.findIndex(t => Math.abs(t - at) < 1e-5);
    const values = data(sampler.output);
    assert.ok(i >= 0 || values.every(v => v.every((x, k) => Math.abs(x - values[0][k]) < 1e-6)));
    animated[channel.target.node][channel.target.path] = values[Math.max(0, i)];
  }
  const parents = new Map(animated.flatMap(({ children = [] }, i) => children.map(c => [c, i])));
  const jointWorld = (list, i) => parents.has(i) ? matrixMul(jointWorld(list, parents.get(i)), trs(list[i])) : trs(list[i]);
  const frame = model.animations[0].frames.find(f => f.time === at), inverseBind = data(skin.inverseBindMatrices);
  const deltas = skin.joints.map((index, i) => matrixMul(jointWorld(animated, index), inverseBind[i]));
  const sourceDelta = skin.joints.map(index => frame.matrices[model.joints.findIndex(j => j.name === animated[index].name)]);
  const weights = data(attr.WEIGHTS_0), joints = data(attr.JOINTS_0);
  let drift = 0, displacement = 0;
  for (let i = 0; i < verts.length; i++) {
    assert.ok(Math.abs(weights[i].reduce((sum, w) => sum + w, 0) - 1) < 1e-6);
    const blend = (matrices, apply) => weights[i].reduce((p, w, j) => w ? K.V.mad(
      p, apply(matrices[joints[i][j]], verts[i]), w
    ) : p, [0, 0, 0]);
    const got = blend(deltas, transform);
    const expected = blend(sourceDelta, (m, p) => K.V.add(K.M.app(m, p), m.slice(9)));
    drift = Math.max(drift, K.V.len(K.V.sub(got, expected)));
    displacement = Math.max(displacement, K.V.len(K.V.sub(got, verts[i])));
  }
  assert.ok(drift < 1e-4, 'maximum vertex drift ' + drift);
  assert.ok(displacement > 0.05);

  const copy = path.join(dir, 'copy.glb');
  assert.equal(studio.exportGlb(file, { out: copy }).preserved, true);
  assert.deepEqual(fs.readFileSync(copy), bytes);
  assert.throws(() => studio.exportGlb({ points: [], faces: [] }, { out: file }), /GLB export requires/);
  assert.deepEqual(fs.readFileSync(file), bytes);
});

test('authored quad topology keeps its UV seams through the per-texel bake', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-authored-topology-'));
  t.after(() => fs.rmSync(dir, { force: true, recursive: true }));
  const S = K.sculpt(lib.makeSculpt(lib.makeBuilder(1)));
  S.box([0, 0, 0], [1, 1, 1], { r: [2, 3, 4] });
  const mesh = K.model.fromSculpt(S, {
    topology: {
      points: [[-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]],
      faces: [[0, 1, 2, 3]],
      uvs: [[[0.1, 0.1], [0.9, 0.1], [0.9, 0.9], [0.1, 0.9]]]
    }
  });
  assert.equal(mesh.uvs.length, 2);
  const file = path.join(dir, 'piece.glb');
  const report = studio.exportGlb(mesh, { out: file, textureSize: 256 });
  assert.equal(report.meshes[0].generatedUVs, false);
  const { gltf } = parseGlb(file);
  assert.ok(gltf.materials[0].pbrMetallicRoughness.baseColorTexture);
});

test('JSON supports independent analytic props and authored PBR channels', () => {
  const spec = {
    id: 'metal-ring',
    solids: [{ kind: 'torus', id: 'band', at: [0, 0, 0], R: 1, r: 0.02, separate: true,
      mat: { role: 'metal', model: { metallic: 0.9, roughness: 0.3 } } }]
  };
  const model = K.diorama.scene(spec).model(1, { resolution: 0.8 });
  assert.equal(model.meshes[0].name, 'band');
  assert.equal(model.meshes[0].materials[0].metallic, 0.9);
  assert.ok(model.meshes[0].faces.length > 20);
  assert.equal(model.meshes[0].static, true);
});

test('native conversion preserves guided sections, thin details, groom roots and material channels', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-model-fur-'));
  t.after(() => fs.rmSync(dir, { force: true, recursive: true }));
  const B = lib.makeBuilder(2), S = K.sculpt(lib.makeSculpt(B)), creature = K.creature(B, S);
  const coat = K.look.fur([2, 3, 4], { len: 0.24, comb: [0, -1, 0], rim: [5, 6], droop: 0.8 });
  coat.model = (p, n) => ({ emission: p[1] > 1.35 ? [2, 0.25, 0.02] : [0, 0, 0],
    roughness: p[0] > 0 ? 0.64 : 0.97, normal: VaryNormal(n) });
  const VaryNormal = n => K.V.norm(K.V.mad(n, [0, 1, 0], 0.05));
  S.ball([0, 1, 0], [0.58, 0.63, 0.5], coat, { tag: 'body' });
  S.torus([0, 1.25, 0.72], 0.19, 0.02, { r: [5], model: { metallic: 0.82 } },
    { tag: 'body', res: 0.03, model: { separate: true, name: 'Thin ring' } });
  S.ball([0.2, 1.32, 0.44], 0.06, { r: [6], em: true },
    { tag: 'body', ghost: true, model: { separate: true, name: 'Eye glow' } });
  const mesh = K.model.fromSculpt(S, {
    resolution: 0.09, targetTriangles: 680, guides: [{ center: [0, 1, 0], radius: 0.72, axis: [0, 1, 0] }],
    fur: { maxLocks: 30 }
  });
  assert.ok(mesh.faces.length < mesh.sourceTriangles);
  assert.ok(mesh.faces.flat().filter(v => Math.abs(mesh.points[v][1] - 1) < 1e-8).length > 10);
  assert.equal(meshMetrics(mesh.points, mesh.faces).badEdges, 0);
  assert.ok(mesh.attachments.some(p => p.name === 'Fur locks'));
  const cards = mesh.attachments.find(p => p.name === 'Fur cards');
  assert.ok(cards.faces.length > 0);
  assert.deepEqual(cards.skinPoints[0], cards.skinPoints[7]);
  assert.ok(K.V.dist(cards.skinPoints[7], cards.points[7]) > 0.1);
  assert.ok(mesh.attachments.find(p => p.name === 'Thin ring').closed);
  S.bake();
  const W = B.finish({ cam: { target: [0, 1, 0], dist: 7, pitch: 0, yaw: 0 } });
  creature.bind(W, time => creature.set('body', [1, 0.2 * time, 0, 0, 1, 0, 0, 0, 1], [0, 1, 0], [time, 1, 0]));
  const model = K.model.fromCreature(mesh, creature, { clips: [{ name: 'Sheared bow', duration: 1, fps: 2 }] });
  assert.ok(model.meshes.every(part => part.weights.every(row => row.length === 1 && row[0][1] === 1)));
  const pathOut = path.join(dir, 'fur.glb');
  const report = studio.exportGlb(model, { out: pathOut, textureSize: 256 });
  const { gltf, data } = parseGlb(pathOut);
  assert.equal(report.joints, 1);
  const skin = gltf.skins[0], pick = gltf.meshes.find(m => m.name === 'Fur cards').primitives[0];
  assert.equal(gltf.materials[pick.material].alphaMode, 'MASK');
  const core = gltf.materials[gltf.meshes[0].primitives[0].material];
  assert.ok(core.emissiveTexture && core.normalTexture && core.pbrMetallicRoughness.metallicRoughnessTexture);
  assert.equal(core.extensions.KHR_materials_emissive_strength.emissiveStrength, 2);

  const node = skin.joints[0], driver = gltf.nodes.findIndex(obj => obj.children?.includes(node));
  assert.notEqual(driver, -1);
  const poses = structuredClone(gltf.nodes);
  for (const c of gltf.animations[0].channels) poses[c.target.node][c.target.path] = data(gltf.animations[0].samplers[c.sampler].output).at(-1);
  const delta = matrixMul(matrixMul(trs(poses[driver]), trs(poses[node])), data(skin.inverseBindMatrices)[0]);
  const p = [0.3, 1.4, 0.1], actual = transform(delta, p);
  assert.ok(K.V.dist(actual, [1.38, 1.4, 0.1]) < 1e-6, 'native shear bake drift ' + actual);
});

test('native GLB repacks external glTF buffers and keeps OBJ UVs, hard normals and textures', t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-portable-model-'));
  t.after(() => fs.rmSync(dir, { force: true, recursive: true }));
  const PNG = require('../cli/png');
  const red = Uint8Array.of(255, 0, 0);
  PNG.write(path.join(dir, 'red.png'), 1, 1, red);
  fs.writeFileSync(path.join(dir, 'tri.mtl'), 'newmtl Red\nKd 1 1 1\nmap_Kd red.png\n');
  const source = path.join(dir, 'tri.obj'), out = path.join(dir, 'tri.glb');
  fs.writeFileSync(source, [
    'mtllib tri.mtl', 'v 0 0 0', 'v 1 0 0', 'v 0 1 0', 'vt 0 1', 'vt 1 1', 'vt 0 0',
    'vn 0 0 1', 'usemtl Red', 'f 1/1/1 2/2/1 3/3/1'
  ].join('\n'));
  const report = studio.exportGlb(source, { out });
  const { gltf, data, bytes } = parseGlb(out);
  assert.equal(report.meshes[0].generatedUVs, false);
  assert.deepEqual(data(gltf.meshes[0].primitives[0].attributes.TEXCOORD_0), [[0, 0], [1, 0], [0, 1]]);
  assert.deepEqual(data(gltf.meshes[0].primitives[0].attributes.NORMAL), Array.from({ length: 3 }, () => [0, 0, 1]));
  assert.equal(gltf.images[0].mimeType, 'image/png');
  gltf.buffers[0].uri = 'tri.bin';
  const start = 28 + bytes.readUInt32LE(12);
  fs.writeFileSync(path.join(dir, 'tri.bin'), bytes.subarray(start, start + gltf.buffers[0].byteLength));
  fs.writeFileSync(path.join(dir, 'tri.gltf'), JSON.stringify(gltf));
  const embedded = path.join(dir, 'packed.glb');
  studio.exportGlb(path.join(dir, 'tri.gltf'), { out: embedded });
  const result = parseGlb(embedded);
  delete gltf.buffers[0].uri;
  assert.deepEqual(result.gltf, gltf);
  assert.deepEqual(result.data(gltf.meshes[0].primitives[0].attributes.POSITION), data(gltf.meshes[0].primitives[0].attributes.POSITION));
});

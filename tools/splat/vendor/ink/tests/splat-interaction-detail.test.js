const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: K } = require('..').load();

test('interaction density shares representatives within a surface and preserves exceptional samples', () => {
  const count = 11, data = new Float32Array(count * 16), normals = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const at = i * 16;
    data[at] = .02 + .02 * i;
    data[at + 3] = 1;
    data[at + 4] = data[at + 8] = data[at + 10] = .0002;
    normals[i * 3 + 1] = 1;
  }
  const owners = new Uint32Array(count), materialIds = new Uint32Array(count), fine = new Float32Array(count * 12);
  normals[10] = -1;
  owners[4] = 1;
  materialIds[5] = 2;
  data[6 * 16 + 3] = .75;
  data[7 * 16 + 11] = 11;
  fine[8 * 12 + 11] = 1;
  const world = { count, data, owners, ownerIds:['wall','ground'], materialIds, surfaceNormals:normals, fine,
    back:Int32Array.of(9), sortRanges:[{start:10,end:11,bias:.15}] };
  const before = structuredClone(world), level = K.splatInteractionDetail.compile(world, .25);
  assert.deepEqual([...level.indices], [1,3,4,5,6,7,8,9,10]);
  assert.deepEqual([...level.representative], [1,1,1,3,4,5,6,7,8,9,10]);
  assert(level.scale[1] > 0);
  assert.deepEqual(world, before);
  const { representatives, extras } = K.splatInteractionDetail.restore(level, Uint32Array.of(2),
    Uint32Array.of(0), i => i === 0);
  assert.deepEqual([...representatives], [1]);
  assert.deepEqual([...extras], [2]);
  assert.equal(K.splatInteractionDetail.compile(world,.25,{preserveOwners:['wall']}).indices.length, count);
  assert.throws(() => K.splatInteractionDetail.compile(world, 0), /cell/);
});

test('a conservative height ceiling clips empty ray space and retains raised hits', () => {
  const { heightSurface } = K.procedural || K.authoring;
  const raised = { min:[-.3,0,-6], max:[.3,6,6] };
  let queries = 0, normalQueries = 0;
  const surface = {
    bounds:{ min:[-12,-1,-12], max:[12,10,12] },
    height(x,z) { queries++; return Math.abs(z)>6?0:Math.max(0, 1 - Math.abs(x)/.3) * 6; },
    normal() { normalQueries++; return [0,1,0]; }
  };
  const hint = heightSurface.ceiling(0, [raised]);
  const hit = (x, ceiling) => heightSurface.raycast(surface,[x,12,8],[0,-1,-.6],
    {ceiling,withNormal:!ceiling});
  const natural = hit(4), initial = queries;
  queries = 0;
  const clipped = hit(4, hint);
  assert.deepEqual(clipped.n, undefined);
  assert.equal(normalQueries, 1);
  assert(Math.abs(clipped.distance-natural.distance) < 1e-7);
  assert(queries * 8 < initial, 'distant relief should not drive an empty ray scan');
  assert(Math.abs(hit(.12,hint).distance - hit(.12).distance) < 1e-7);
  assert(Math.abs(hit(.12,hint).p[1]-3.6)<1e-7);
  const upward = heightSurface.raycast(surface,[4,-.7,0],[0,1,.1],{ceiling:hint});
  assert.equal(upward.p[1], 0);
});

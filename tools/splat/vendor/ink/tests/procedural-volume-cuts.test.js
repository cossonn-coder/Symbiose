const test = require('node:test');
const assert = require('node:assert/strict');
const P = require('..').load().KIT.procedural;

const square = (x0, z0, x1, z1) => [[x0, z0], [x1, z0], [x1, z1], [x0, z1]];

test('volume cuts subtract only the supplied host and keep their own stable profiles', () => {
  const spec = { key: 'cut', profile: square(-1, -1, 1, 1), span: [.5, 3] };
  const volume = P.volumeCuts.compile([spec]);
  const host = ([x, y, z]) => Math.max(Math.abs(x) - 2, -y, y - 2, Math.abs(z) - 2);
  const carved = volume.subtract(host);
  spec.profile[0][0] = 10;
  assert.equal(carved([0, 1, 0]), .5);
  assert.equal(carved([0, .4, 0]), -.09999999999999998);
  assert.equal(carved([1.5, 1, 0]), -.5);
  assert(volume.distance([1.5, 1, 0], 0) === 0);
  assert.deepEqual(volume.bounds, { min: [-1, .5, -1], max: [1, 3, 1] });
  assert.throws(() => P.volumeCuts.compile([spec, spec]), /unique keys/);
});

test('overlapping volumes omit buried samples and pick exposed floors through filtered faces', () => {
  const volume = P.volumeCuts.compile([
    { key: 'deep', profile: square(-2, -1, 1, 1), span: [.5, 4] },
    { key: 'shallow', profile: square(0, -1, 2, 1), span: [1, 4] }
  ]);
  const samples = [];
  volume.sample(.2, (p, n, key) => samples.push({ p, n, key }));
  assert(samples.some(s => s.key === 'shallow' && s.n[1] === -1 && s.p[0] > 1));
  assert(!samples.some(s => s.key === 'shallow' && s.n[1] === -1 && s.p[0] < 1));
  const hit = volume.raycast([.5, 5, 0], [0, -1, 0], 6, p => p[1] <= 3);
  assert.deepEqual(hit, { p: [.5, .5, 0], n: [0, -1, 0], distance: 4.5, key: 'deep' });
  assert.throws(() => volume.sample(.001, () => {}, { maxSamples: 5 }), /sample budget/);
});

test('touching cut volumes do not expose the shared interior face', () => {
  const volume = P.volumeCuts.compile([
    { key: 'left', profile: square(-2, -1, 0, 1), span: [0, 2] },
    { key: 'right', profile: square(0, -1, 2, 1), span: [0, 2] }
  ]);
  volume.sample(.5, p => assert.notEqual(p[0], 0));
  assert.equal(volume.raycast([-1, 1, 0], [1, 0, 0], 5).distance, 3);
});

test('plane sections trace a swept concave profile through its frame',()=>{
  const outline=[[-2,-1],[2,-1],[2,1],[.5,1],[.5,0],[-.5,0],[-.5,1],[-2,1]];
  const frame=P.transforms.local({position:[1,2,3],rotation:Math.PI/4,scale:[1.3,1,.7]});
  const section=(point,normal)=>P.geometry.profilePlaneSection({outline,span:[-1,0],frame,plane:{point,normal}});
  const front=section(frame.t,[1,0,1]);
  assert.equal(front.length,outline.length);
  const middle=section(P.transforms.point(frame,[0,0,-.5]),[1.04,0,1]);
  assert(middle.length>4);
  assert(middle.every(p=>Math.abs(1.04*(p[0]-middle[0][0])+p[2]-middle[0][2])<1e-8));
  assert(middle.some(p=>Math.abs(p[1]-2)<1e-8));
  assert.deepEqual(section([1,2,50],[0,0,1]),[]);
  assert.throws(()=>section(frame.t,[0,0,0]),/normal/);
});

const test = require('node:test'),
  assert = require('node:assert/strict'),
  lib = require('..'),
  { KIT: K } = lib.load(),
  A = K.procedural,
  V = K.V;
const near = (a, b, e = 1e-5) => assert(Math.abs(a - b) < e, `${a} != ${b}`),
  loop = [
    [-1, 0, -1],
    [1, 0, -1],
    [1, 0, 1],
    [-1, 0, 1]
  ],
  ground = {
    height: (x, z) => -0.7 - 0.3 * x + 0.2 * z,
    slopeBound: Math.hypot(0.3, 0.2),
    bounds: { min: [-3, -3, -3], max: [3, 2, 3] }
  };
test('a support skirt is a filled gravity volume with sloping ground, caps and bounded picking', () => {
  const raw = JSON.stringify(loop),
    r = A.supportSkirt({ outline: loop, ground });
  assert(r.distance([0, -0.3, 0]) < 0);
  assert(r.distance([0, 0.2, 0]) > 0);
  assert(r.distance([2, -0.3, 0]) > 0);
  near(r.bottom(0.5, 0.2), ground.height(0.5, 0.2) - 0.06);
  const hit = r.raycast([0, -0.3, 4], [0, 0, -1], 10);
  near(hit.p[2], 1);
  near(hit.distance, 3);
  assert.equal(r.raycast([0, 1, 4], [0, 0, -1], 10), null);
  assert.equal(JSON.stringify(loop), raw);
  const mesh = r.mesh();
  assert(mesh.positions.length > 100);
  assert(mesh.positions.every(Number.isFinite));
  for (let i = 0; i < mesh.positions.length; i += 3)
    assert(A.spatial.contains(r.bounds, [...mesh.positions.subarray(i, i + 3)]));
});
test('support distance bounds stay conservative on sloping and tilted carriers', () => {
  const tilted = loop.map(p => [p[0], p[0] * 0.23 + p[2] * 0.1, p[2]]),
    r = A.supportSkirt({ outline: tilted, ground });
  for (let i = 0; i < 500; i++) {
    const q = [-1.3 + ((i * 0.618) % 1) * 2.6, -1 + ((i * 0.73) % 1) * 1.5, -1.3 + ((i * 0.419) % 1) * 2.6],
      g = [0, 1, 2].map(k => {
        const a = q.slice(),
          b = q.slice();
        a[k] += 1e-5;
        b[k] -= 1e-5;
        return (r.distance(a) - r.distance(b)) / 2e-5;
      });
    assert(Math.hypot(...g) <= 1.0001);
  }
  assert.throws(() => r.distance([NaN, 0, 0]));
});
test('fitted support courses recess their joints and keep the same bearing and course datum', () => {
  const skirt=A.supportSkirt({outline:loop,ground}), spec={unit:[.45,.22],joint:.04,depth:.045};
  const finish=A.supportCourses(skirt,spec), y=finish.top-finish.layout.unit[1];
  near(skirt.distance([.2,y,1]),0);
  assert(finish.distance([.2,y,1])>.002);
  assert(finish.distance([.2,y,.93])<0);
  near(finish.distance([.2,finish.top,1]),0);
  const changed=A.supportSkirt({outline:loop,ground:{
    ...ground,height:(x,z)=>ground.height(x,z)-.35,bounds:{min:[-3,-4,-3],max:[3,2,3]}
  }});
  const next=A.supportCourses(changed,spec), p=[.2,y-.05,1];
  assert.equal(next.lookup(p).cell.id,finish.lookup(p).cell.id);
  near(next.lookup(p).v,finish.lookup(p).v);
  const seamY=finish.top-1.5*finish.layout.unit[1];
  assert.equal(finish.lookup([-.99999,seamY,-1]).cell.id,finish.lookup([-1,seamY,-.99999]).cell.id);
  const samples=[];
  assert.equal(finish.sample(.14,q=>samples.push(q)),samples.length);
  assert(samples.some(p=>Math.abs(p[1]-y)<1e-6&&skirt.horizontal(p[0],p[2])<-.02));
  assert(samples.every(p=>Math.abs(finish.distance(p))<.001));
});
test('omitted support blocks recess both sides of the periodic seam and keep their ground-clipped backing', () => {
  const skirt=A.supportSkirt({outline:loop,ground}), spec={unit:[.45,.22],joint:.04,depth:.045};
  const fitted=A.supportCourses(skirt,spec), y=fitted.top-1.5*fitted.layout.unit[1];
  const points=[[-.92,y,-1],[-1,y,-.92]],key=fitted.lookup(points[0]).cell.id;
  assert.equal(fitted.lookup(points[1]).cell.id,key);
  const open=A.supportCourses(skirt,{...spec,omit:[key]});
  for(const p of points){
    near(fitted.distance(p),0);
    assert(open.lookup(p).omitted);
    assert(open.distance(p)>.01);
  }
  const adjacent=[-.62,y,-1],bearing=[-.92,y,-.91];
  assert(!open.lookup(adjacent).omitted);
  near(open.distance(adjacent),fitted.distance(adjacent));
  assert(open.distance(bearing)<-.01);
  assert.equal(open.frontage(key).length,2,'one logical block can front both sides of a corner');
  assert(open.frontage(key).every(({points})=>points.every(([x,y,z])=>
    y>=skirt.bottom(x,z)-1e-9&&y<=skirt.top(x,z)+skirt.overlap+1e-9)));
  const samples=[];
  open.sample(.11,p=>samples.push(p));
  assert(samples.some(p=>open.lookup(p).omitted&&open.lookup(p).side<-.02));
  assert(samples.every(p=>Math.abs(open.distance(p))<.001));
  assert.throws(()=>A.supportCourses(skirt,{...spec,omit:['invalid']}),/bounded course dimensions/);
});
test('skirt validation and budgets reject invalid or unbounded geometry before expensive allocation', () => {
  for (const raw of [
    {
      outline: [
        [0, 0, 0],
        [1, 1, 0],
        [1, 0, 1],
        [0, 0, 1]
      ]
    },
    {
      outline: [
        [0, 0, 0],
        [1, 0, 1],
        [1, 0, 0],
        [0, 0, 1]
      ]
    },
    { ground: { ...ground, slopeBound: -1 } },
    { maxDrop: Infinity },
    { overlap: -1 },
    { embed: 1 }
  ])
    assert.throws(() => A.supportSkirt({ outline: loop, ground, ...raw }));
  const r = A.supportSkirt({ outline: loop, ground });
  assert.throws(() => r.mesh({ budget: 1 }), /budget/);
  assert.throws(() => r.sample(0.0001, () => {}), /budget/);
  assert.throws(() => r.sample(0.1, () => {}, { budget: 0 }), /budget/);
  assert.throws(() => r.raycast([0, 0, 0], [0, 0, 0]));
  const invalid = A.supportSkirt({ outline: loop, ground: { ...ground, height: () => NaN } });
  assert.throws(() => invalid.distance([0, 0, 0]), /finite/);
});
test('support sampling covers a steep curtain and returns no exposed mesh when ground covers its carrier', () => {
  const g = { height: x => -1.2 - 0.8 * x, slopeBound: 0.8, bounds: { min: [-3, -4, -3], max: [3, 3, 3] } },
    r = A.supportSkirt({ outline: loop, ground: g }),
    points = [];
  r.sample(0.16, q => points.push(q));
  for (let x = -0.9; x <= 0.9; x += 0.12)
    for (let y = r.bottom(x, -1) + 0.1; y < 0.02; y += 0.13) {
      const q = [x, y, -1],
        distance = Math.min(...points.map(p => V.dist(p, q)));
      assert(distance < 0.16, `curtain gap ${distance}`);
    }
  const hidden = A.supportSkirt({
    outline: loop,
    ground: { height: () => 1, slopeBound: 0, bounds: { min: [-3, 1, -3], max: [3, 1, 3] } }
  });
  assert.equal(hidden.mesh().positions.length, 0);
  assert.equal(hidden.raycast([0, 0.5, 4], [0, 0, -1], 10), null);
});

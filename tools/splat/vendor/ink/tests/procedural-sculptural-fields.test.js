const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: K, makeBuilder, makeSculpt } = require('..').load();
const { forms, grammar } = K.procedural;
const close = (a, b, error = 1e-7) => assert(Math.abs(a - b) < error, a + ' differs from ' + b);

test('rest geometry measurement combines tight primitive bounds without sampling a sculpt', () => {
  const {measureSculptBounds}=K.procedural, q=Math.SQRT1_2, frame=[[q,0,q],[0,1,0],[-q,0,q]];
  const bounds=measureSculptBounds(S=>{
    S.box([1,.4,0],[1,.4,.5],{}, {ax:frame});
    S.ball([-2,.3,.1],[.3,.2,.15],{});
    S.tube([[0,0,0],[0,2,0]],.2,.4,{});
    S.lathe([.3,0,-1],.5,t=>t>.62&&t<.64?.6:.15,{}, {maxRadius:.6});
    S.box([90,0,0],[2,2,2],{}, {neg:true});
    S.box([30,0,0],[1,1,1],{}, {hold:true});
  });
  [-2.3,-.2,-1.6].forEach((n,i)=>close(bounds.min[i],n));
  [1+1.5*q,2.4,1.5*q].forEach((n,i)=>close(bounds.max[i],n));
  assert.deepEqual(measureSculptBounds(S=>{
    S.solid([1,2,3],.25,()=>0,()=>{throw Error('unexpected surface sampling');},{});
  }),{min:[.75,1.75,2.75],max:[1.25,2.25,3.25]});
  assert.equal(measureSculptBounds(()=>{}),null);
});

test('superquadrics interpolate pointed and rounded-box shapes in a world pose', () => {
  const shape = forms.superquadric({ radii: [1, 2, 0.5] }),
    angular = forms.superquadric({ radii: [1, 2, 0.5], exponents: [1, 1] }),
    boxy = forms.superquadric({ radii: [1, 2, 0.5], exponents: [7, 7] });
  close(shape.sd(0, 0, 0), -0.5);
  close(shape.sd(0, 2, 0), 0);
  assert(angular.sd(0.65, 0, 0.32) > 0);
  assert(boxy.sd(0.65, 0, 0.32) < 0);
  const moved = forms.superquadric({
    radii: [1, 2, 0.5], pose: { position: [4, 5, 6], rotation: [0, 0, Math.PI / 2], scale: 2 }
  });
  close(moved.sd(8, 5, 6), 0);
  assert(moved.bounds.max[0] > 7.99);
  assert.throws(() => forms.superquadric({ exponents: [0, 2] }), /exponents/);
});

test('lofts match authored sections with different vertex counts and close both ends', () => {
  const shape = forms.loft([
    { y: -1, profile: [[0,-1],[1,1],[-1,1]] },
    { y: 0, profile: [[-1,-1],[1,-1],[1,1],[-1,1]], center: [0.4,0] },
    { y: 1, profile: [[-1,-1],[1,-1],[1,1],[-1,1]], center: [0.8,0], scale: 0.5, roll: Math.PI / 2 }
  ]);
  close(shape.sd(1.4, 0, 0), 0);
  assert(shape.sd(1.41, 0, 0) > 0);
  assert(shape.sd(0.6, 0.5, 0) < 0);
  assert(shape.sd(0.9, 1.01, 0) > 0 && shape.sd(0, -1.01, 0) > 0);
  close(shape.sd(0.8, 1, 0), 0);
  const moved = forms.loft([
    { y: 0, profile: [[-1,-1],[1,-1],[1,1],[-1,1]] },
    { y: 1, profile: [[-1,-1],[1,-1],[1,1],[-1,1]] }
  ], { pose: { position: [-3, 0, 0] } });
  assert(moved.sd(-3, 0.5, 0) < 0 && moved.sd(0, 0.5, 0) > 0);
  assert(moved.bounds.max[0] < -1);
});

test('medial spheres sweep a tapered centerline and blend through junctions', () => {
  const medial = [
    { point: [0,0,0], radius: 0.5 },
    { point: [0,2,0], radius: 0.3, parent: 0 },
    { point: [1,3,0], radius: 0.22, parent: 1 },
    { point: [-1,3,0], radius: 0.2, parent: 1 }
  ], hard = forms.skeleton(medial), blend = forms.skeleton(medial, { blend: 0.25 });
  close(hard.sd(0.5, 1, 0), 0.5 * Math.sqrt(0.99) - 0.4);
  assert(hard.sd(0, 3.2, 0) > 0);
  assert(hard.sd(0, 2.16, 0.3) > blend.sd(0, 2.16, 0.3));
  assert(hard.sd(...medial[2].point) < 0);
  const contained = forms.skeleton([{ point: [0,0,0], radius: 0.1 }, { point: [0,0.1,0], radius: 0.8, parent: 0 }]);
  close(contained.sd(0, 0.1, 0), -0.8);
});

test('periodic lattices repeat, clip to a host and become native sculpted splats', () => {
  const bound = { min: [-2,-2,-2], max: [2,2,2] },
    periodic = forms.periodic({ bounds: bound, period: [0.7, 1.1, 1.3] }),
    source = forms.superquadric({ radii: [0.82,0.82,0.82] }),
    contained = forms.periodic({ bounds: source.bounds, period: 0.7, host: source.sd, thickness: 0.11 });
  close(periodic.sd(0.19, 0.14, 0.12), periodic.sd(0.89, 1.24, 1.42));
  assert(contained.sd(0.62, 0.62, 0.62) > 0);
  assert(contained.sd(0, 0, 0) < 0);
  const B = makeBuilder(7), S = K.sculpt(makeSculpt(B)),
    solid = S.implicitForm(contained, { r: [1,2,3] }, { res: 0.1 });
  assert(S.psd(solid, 0, 0, 0) < 0);
  S.bake();
  assert(B.finish({}).count > 300);
  const tooSmall = S.implicitForm(source, {}, { hold: true, cell: 0.002 });
  assert.throws(() => tooSmall.sample(() => {}), /sample budget/);
});

test('local shell thickness varies on either side of the same host', () => {
  const ball = forms.superquadric(), layer = forms.shell(ball, {
    inner: (x, y) => y > 0 ? 0.3 : 0.11, outer: x => x > 0 ? 0.11 : 0, maxOuter: 0.11
  });
  assert(layer.sd(0, 0.8, 0) < 0);
  assert(layer.sd(0, -0.8, 0) > 0);
  assert(layer.sd(1.05, 0, 0) < 0);
  assert(layer.sd(-1.05, 0, 0) > 0);
  assert.equal(layer.bounds.max[0], 1.11);
  assert.throws(() => forms.shell(ball, { outer: () => 0.2 }), /bounded/);
});

test('mirrored and radial grammar parts retain keys during scoped variants', () => {
  const scope = { id: 'rig', symbol: 'pod', bounds: { min: [0.3, 0, -0.2], max: [1.3, 0.4, 0.2] } },
    group = role => ({ op: 'group', children: [
      { key: 'body', use: { op: 'emit', role } }, { key: 'connector', use: { op: 'socket', name: 'tip', axis: 'x' } }
    ] }),
    rules = { pod: group('pod'), heavy: group('tank') },
    a = grammar.symmetry(scope, rules), b = grammar.symmetry(scope, rules, { copies: [{ index: 1, symbol: 'heavy', scale: 1.2 }] });
  assert.deepEqual(a.parts.map(p => p.key), b.parts.map(p => p.key));
  assert.deepEqual(a.parts.map(p => p.handedness), [1, -1]);
  assert.deepEqual(a.sockets.map(p => p.normal), [[1,0,0],[-1,0,0]]);
  assert.equal(b.parts[1].role, 'tank');
  close(b.parts[1].center[0], -0.96);
  const c = grammar.symmetry(scope, rules, { mode: 'radial', count: 4 });
  close(Math.abs(c.parts[1].center[2]), 0.8);
  close(c.parts[2].center[0], -0.8);
});

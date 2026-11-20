const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const P = KIT.procedural;

test('ordered swept masks taper, retain ownership, and support erasing and repainting', () => {
  const base = {
    id: 'base',
    points: [
      [-2, 0],
      [2, 0]
    ],
    radii: [0.3, 1.1],
    softness: 0
  };
  const erase = { id: 'erase', points: [[0, 0]], width: 0.9, operation: 'erase', order: 1 };
  const restore = { id: 'restore', points: [[0, 0]], width: 0.35, order: 2 };
  const field = P.masks.compose([erase, base]);
  assert(field.distance([0, 0]) > 0);
  assert.equal(field.owner([0, 0]), null);
  assert(field.distance([1.7, 0.6]) < 0);
  assert(field.distance([-1.7, 0.6]) > 0);
  assert.equal(field.sample([1.7, 0.6]).owner, 'base');
  assert.equal(P.masks.compose([erase, restore, base]).owner([0, 0]), 'restore');
  assert.throws(() => P.masks.compose([base, base]), /unique/);
  base.points[0][0] = 2;
  assert(field.distance([-1.8, 0]) < 0);
});

test('bounded brush queries keep exact distances under the ceiling through erase and repaint', () => {
  const specs = [
    { id: 'ground', points: [[-2, 0], [3, 2], [4, 0]], radii: [.7, 1.3, .8] },
    { id: 'erase', points: [[0, 1], [2, 1]], width: 1.6, operation: 'erase', order: 1 },
    { id: 'restore', points: [[1, 1]], width: .4, order: 2 }
  ];
  const reference = P.masks.compose(specs), bounded = P.masks.compose(specs);
  for (let i = -12; i <= 24; i++) for (let j = -6; j <= 14; j++) {
    const p = [i / 4, j / 4], exact = reference.sample(p).distance;
    for (const ceiling of [-1, 0, .1, 5, Infinity, .2]) {
      assert.equal(bounded.distanceAt(...p, ceiling), Math.min(exact, ceiling));
    }
    assert.equal(bounded.distance(p), exact);
  }
});

test('a compiled planar profile keeps concave gaps, winding and its own edge storage', () => {
  const points = [[0, 0], [2, 0], [2, 0], [2, 1], [1, 1], [1, 2], [0, 2]];
  const forward = P.geometry.profileDistance(points);
  const reverse = P.geometry.profileDistance(points.slice().reverse());
  points[0][0] = 8;
  for (const evaluate of [forward, reverse]) {
    assert.equal(evaluate(.5, 1.5), -.5);
    assert.equal(evaluate(1.5, 1.5), .5);
    assert.equal(Math.abs(evaluate(1, 1.5)), 0);
    assert.equal(evaluate(3, 3), Math.sqrt(5));
    assert.equal(evaluate(1e200, 1e200), Math.hypot(1e200, 1e200));
  }
});

test('concave extrusions cut along an affine profile and line only the retained host', () => {
  const profile = [
    [-1, -1],
    [1, -1],
    [1, 0],
    [0, 0],
    [0, 1],
    [-1, 1]
  ];
  const frame = P.transforms.local({ position: [3, 1, -2], rotation: 0.4, scale: [1.2, 1, 0.8] });
  const cut = P.profileCut({ profile, span: [-2, 2], frame });
  const host = world => Math.abs(cut.project(world)[2]) - 0.6;
  const liner = cut.lining(0.2, host);
  assert(cut.subtract(host)(cut.sample([-0.5, 0.5, 0])) > 0);
  assert(cut.subtract(host)(cut.sample([0.5, 0.5, 0])) < 0);
  assert(liner(cut.sample([0.07, 0.5, 0])) < 0);
  assert(liner(cut.sample([0.07, 0.5, 0.8])) > 0);
  assert(cut.distance(cut.sample([-0.5, 0.5, 2.01])) > 0);
});

test('clearance finds only participating fields and rejects excessive total work', () => {
  const block = P.pieces.beam([0, 0, 0], [2, 0, 0], 0.6, 0.6);
  const fields = P.clearance.field([
    { ...block, id: 'beam' },
    {
      id: 'remote',
      bounds: { min: [8, 8, 8], max: [9, 9, 9] },
      distance: () => assert.fail('A distant solid must not be probed')
    }
  ]);
  const box = { min: [0.8, -0.1, -0.1], max: [1.2, 0.1, 0.1] };
  assert.equal(fields.probe(box).contacts[0].id, 'beam');
  assert(fields.probe(box, { exclude: ['beam'] }).clear);
  assert.throws(() => fields.probe(box, { budget: 1 }), /budget/);
  assert.equal(fields.probe({ min: [1, 0, 0], max: [1, 0, 0] }).tested, 1);
});

test('compiled emitters cycle in a caller supplied direction and stay finite at large times', () => {
  const spec = {
    id: 'flow',
    p: [1, 2, 3],
    color: [1, 0.6, 0.2],
    count: 5,
    height: 2,
    seed: 18,
    speed: 1,
    direction: [0, -1, 0],
    drift: [0, 0, 0],
    spread: 0
  };
  const emitter = P.emitters.compile(spec);
  const samples = emitter.samples(0.31);
  assert.deepEqual(samples, P.emitters.compile(spec).samples(0.31));
  for (let i = 0; i < samples.length; i++) {
    const { p, opacity } = samples[i];
    assert.equal(p[0], 1);
    assert.equal(p[2], 3);
    assert(p[1] >= 0 && p[1] <= 2 && opacity >= 0);
    assert(Math.abs(emitter.sample(i, 0.31 + emitter.period).p[1] - p[1]) < 1e-10);
    assert(emitter.sample(i, Number.MAX_VALUE).p.every(Number.isFinite));
  }
});

test('bounded airflow carries a looping emitter by age and exposes a saturated flex response', () => {
  const wind = [1, -.5];
  const frame = P.airflow.frame(wind);
  assert.deepEqual(frame.velocity, wind);
  assert(Math.hypot(...frame.flex) < 1);
  assert.deepEqual(P.airflow.frame([0, 0]).flex, [0, 0]);
  assert.throws(() => P.airflow.frame([21, 0]), /Wind/);
  assert.equal(P.airflow.bend(1, 0, 1.8, 0), 0);
  assert.notEqual(P.airflow.bend(0, 0, 1.8, 1), P.airflow.bend(.9, 0, 1.8, 1));
  const opts = {id:'volute',p:[0,0,0],color:[.6,.6,.6],height:2,speed:1,spread:0,drift:[0,0,0]};
  const plume = P.emitters.compile({...opts,windborne:true}), steady = P.emitters.compile(opts);
  const still = plume.sample(0,.38), blown = plume.sample(0,.38,{wind});
  assert.equal(blown.p[0],still.p[1]);
  assert.equal(blown.p[1],still.p[1]);
  assert.equal(blown.p[2],-.5*still.p[1]);
  assert.equal(blown.opacity,still.opacity);
  assert.deepEqual(plume.samples(.38,{wind})[0],blown);
  assert.deepEqual(steady.sample(0,.38,{wind}),still);
});

test('sculpt materials can encode spatially varying motion on selected samples', () => {
  const { KIT, makeBuilder, makeSculpt } = require('..').load();
  const builder = makeBuilder(1,[0,0x558866,0x77aa88]);
  const sculpt = KIT.sculpt(makeSculpt(builder));
  sculpt.box([0,.3,0],[.4,.4,.07],{
    r:[1,2],motionAt:(x,y)=>x>0?{k:11,wind:true,rg:y+.15}:undefined
  },{res:.08});
  sculpt.bake();
  const {data,count}=builder.finish(),flag=KIT.procedural.airflow.packedFlag;
  let moving=0,still=0;
  for(let i=0;i<count;i++){
    const q=i*16;
    if(data[q+11]&flag){assert(data[q]>0);assert.equal(data[q+11]&15,11);moving++;}
    else if(data[q]<0)still++;
  }
  assert(moving>10&&still>10);
});

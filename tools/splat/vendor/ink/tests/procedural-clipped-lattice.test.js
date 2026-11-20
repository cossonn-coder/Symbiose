const { test } = require('node:test');
const assert = require('node:assert/strict');
const { clippedLattice, pieces } = require('..').load().KIT.procedural;

const panels = [
  { key: 'left', polygon: [[0, 0], [1, 0], [1, 2], [0, 1]] },
  { key: 'right', polygon: [[1, 0], [2, 0], [2, 1], [1, 2]] }
];
const runs = [
  { axis: [1, 0], pitch: .4, width: .1 },
  { axis: [0, 1], pitch: .98, width: .08 }
];
const build = lattice => lattice.pieces({
  direction: [0, 0, 1], depth: [-.07, .15],
  map: (panel, [u, v]) => [u, v, 0],
  key: 'gate', owner: 'panel', material: 'metal', frameMaterial: 'wood'
});

test('convex containment and picking work before the mesh is requested', () => {
  const vertices = [[0,0,0],[1,0,0],[0,1,0],[0,0,1]];
  const part = pieces.convex(vertices, [[0,1,2],[0,1,3],[1,2,3],[2,0,3]], {key:'tetrahedron'});
  const solid = pieces.union([part]);
  vertices[0][0] = 20;
  for (const point of [[.1,.1,.1],[.5,.5,.1],[0,.2,.2],[.01,.01,.01]]) {
    for (const tolerance of [0,.01,.05]) {
      assert.equal(part.contains(point,tolerance),part.distance(point)<-tolerance);
      assert.equal(solid.contains(point,tolerance),part.contains(point,tolerance));
    }
  }
  assert.equal(solid.raycast([.2,.2,-1],[0,0,1]).distance,1);
  assert.deepEqual(part.mesh.bounds,part.bounds);
  assert.equal(part.mesh,part.mesh);
});

test('projected solid intervals preserve narrow gaps and reach recessed material', () => {
  const frame=[1,0,0,0,1,0,0,0,1];
  const piece=(id,x,half,z=0)=>pieces.box([x,0,z],[half,.2,.05],frame,{key:id});
  const left=piece('left',.2,.2),right=piece('right',.74,.26);
  const distant=Array.from({length:24},(_,i)=>piece('remote/'+i,8+i,.25));
  const a=[0,0,.05],b=[1,0,.05],n=[0,0,3],reach={outward:.015,inward:.15};
  const exposed=pieces.union([left,right,...distant]);
  const spans=exposed.projectedIntervals(a,b,n,reach);
  assert.equal(spans.length,2);
  assert(Math.abs(spans[0][1]-.4)<1e-6);
  assert(Math.abs(spans[1][0]-.48)<1e-6);
  assert.equal(exposed.raycast([.44,0,.12],[0,0,-1],.3),null);
  const backed=pieces.union([left,right,piece('backing',.5,.5,-.11),...distant]);
  assert.deepEqual(backed.projectedIntervals(a,b,n,reach),[[0,1]]);
  assert.equal(backed.projectedIntervals(a,b,n,{...reach,inward:.03}).length,2);
  assert.equal(backed.raycast([.44,0,.12],[0,0,-1],.3).part,'backing');
  assert.throws(()=>backed.projectedIntervals(a,b,n,{outward:1,inward:-1}),/nonnegative reaches/);
});

test('a profiled lattice clips members to several convex patches and retains open cells', () => {
  const lattice = clippedLattice({ panels, runs, edges: [[[0, 0], [2, 0]]], edgeWidth: .16 });
  const rail = lattice.members.find(m => m.key === 'run/1/0');
  assert.deepEqual(rail.fragments.map(f => f.panel), ['left', 'right']);
  const realized = build(lattice), union = pieces.union(realized);
  assert(realized.every(p => p.owner === 'panel' && p.mesh.positions.every(Number.isFinite)));
  assert(realized.some(p => p.material === 'wood' && p.role === 'frame'));
  assert.deepEqual(realized.map(p => p.key), build(lattice).map(p => p.key));
  const cast = (x, y) => union.raycast([x, y, 1], [0, 0, -1]);
  assert.equal(cast(.27, .7), null);
  assert.equal(cast(.2, 1.7), null);
  assert(Math.abs(cast(.2, .7).distance - .85) < 1e-6);
  assert.equal(cast(.27, .02).material, 'wood');
});

test('lattices accept oblique runs and reject invalid geometry, width and budgets', () => {
  const l = clippedLattice({ panels, runs: [{axis: [1, -1], pitch: .48, width: .1, phase: .25}] });
  assert(build(l).length > 3);
  assert.throws(() => clippedLattice({ panels, runs, budget: 2 }), /budget/);
  assert.throws(() => clippedLattice({ panels, runs: [{axis: [0, 1], pitch: .1, width: .13}] }), /pitch/);
  assert.throws(() => clippedLattice({ panels: [...panels, panels[0]], runs }), /unique/);
  assert.throws(() => l.pieces({ direction: [0, 0, 0], depth: [0, .2], map: (_, [u, v]) => [u, v, 0] }), /direction/);
});

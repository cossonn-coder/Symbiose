const { test } = require('node:test');
const assert = require('node:assert/strict');
const { procedural: P } = require('..').load().KIT;

const rectangle = (x, y, width, height) => [[x, y], [x + width, y], [x + width, y + height], [x, y + height]];
const area = polygon => polygon.reduce((sum, p, index) => {
  const q = polygon[(index + 1) % polygon.length];
  return sum + (p[0] * q[1] - p[1] * q[0]) / 2;
}, 0);
const total = result => result.cells.flatMap(cell => cell.fragments).reduce((sum, polygon) => sum + area(polygon), 0);
const near = (a, b) => assert(Math.abs(a - b) < 1e-7, a + ' != ' + b);

test('sampled masks share boundaries with cell clipping and preserve islands inside a cut',()=>{
  const {fieldMask,clip}=P.surfaceCells, bounds={min:[-2,-1.5],max:[2,1.5]};
  const mask=fieldMask((x,y)=>Math.max(Math.hypot(x,y)-1,.37-Math.hypot(x,y)),{bounds,cell:.045});
  assert(mask);
  assert(mask.distance(0,0)>.33);
  assert(mask.distance(.65,0)<-.2);
  assert(mask.distance(1.3,0)>.27);
  const result=clip([{key:'single-course',polygon:rectangle(-1.5,-1.3,3,2.6)}],{holes:mask.holes});
  assert.equal(result.cells[0].key,'single-course');
  for(const fragment of result.cells[0].fragments){
    const point=fragment.reduce((sum,p)=>p.map((v,i)=>sum[i]+v/fragment.length),[0,0]);
    assert(mask.distance(...point)>-1e-5);
  }
  const expected=7.8-Math.PI*(1-.37**2);
  assert(Math.abs(total(result)-expected)<.025);
  assert.equal(fieldMask(()=>Infinity,{bounds}),null);
  const clipped=fieldMask(()=>-1,{bounds:{min:[0,0],max:[1,1]},cell:.1});
  assert(clipped.distance(.5,.5)<-.45);
  assert(clipped.distance(-.2,.5)>.15);
});

test('clipping handles an enclosed hole and an angled outer boundary while preserving the logical cell', () => {
  const cells = [{ key: 'panel', polygon: rectangle(0, 0, 4, 4) }];
  const boundary = [[0, 4], [4, 0], [0, 0]];
  const holes = [rectangle(1, 1, 1, 1)];
  const result = P.surfaceCells.clip(cells, { boundary, holes });
  assert.equal(result.cells[0].key, 'panel');
  assert(result.fragmentCount > 1);
  near(total(result), 7);
  for (const fragment of result.cells[0].fragments) {
    assert(fragment.every(([x, y]) => x + y <= 4 + 1e-7));
    const [x, y] = fragment.reduce((sum, p) => sum.map((v, i) => v + p[i] / fragment.length), [0, 0]);
    assert(!(x > 1 && x < 2 && y > 1 && y < 2));
  }
  assert(Object.isFrozen(result.cells[0].fragments[0][0]));
  assert(!Object.isFrozen(cells[0].polygon[0]));
});

test('overlapping cutouts subtract their combined area, and a remote cutout leaves a cell intact', () => {
  const cells = [{ key: 'x', polygon: rectangle(0, 0, 5, 5) }];
  const holes = [rectangle(1, 1, 2, 2), rectangle(2, 2, 2, 2)];
  near(total(P.surfaceCells.clip(cells, { holes })), 18);
  assert.deepEqual(P.surfaceCells.clip(cells, { holes: [rectangle(5, 0, 1, 1)] }).cells[0].fragments, [cells[0].polygon]);
  assert.deepEqual(P.surfaceCells.clip(cells, { holes: [rectangle(-1, -1, 7, 7)] }).cells, []);
  assert.throws(() => P.surfaceCells.clip(cells, { holes, budget: 1 }), /fragment budget/);
  assert.throws(() => P.surfaceCells.clip(cells, { holes, work: 1 }), /work budget/);
  assert.throws(() => P.surfaceCells.clip(cells, { holes: [[[0, 0], [2, 0], [1, 1], [2, 2], [0, 2]]] }), /convex/);
});

test('indexed cells pick all surviving fragments and can omit one logical unit', () => {
  const plan = P.surfaceCells.clip([
    {key:'cut',polygon:rectangle(0,0,3,1)},
    {key:'intact',polygon:rectangle(0,1,3,1)}
  ],{holes:[rectangle(1,-.5,1,2)]});
  const stock = P.surfaceCells.index(plan);
  assert.equal(stock.get('cut').fragments.length,2);
  assert(stock.contains('cut',[.5,.5]));
  assert(stock.contains('cut',[2.5,.5]));
  assert(!stock.contains('cut',[1.5,.5]));
  assert(!stock.contains('missing',[1.5,.5]));
  const reduced=stock.excluding(['cut','dormant']);
  assert.deepEqual(reduced.cells,[stock.get('intact')]);
  assert.equal(reduced.fragmentCount,stock.get('intact').fragments.length);
  assert.equal(plan.cells.length,2);
});

test('fitted-course fragments on a periodic chart seam retain one logical key', () => {
  const layout = P.fittedCourses({ width: 6, height: 2, unit: [1, 1], periodic: true, stagger: .5 });
  const result = P.surfaceCells.clip(layout.cells);
  assert.equal(result.cells.length, 12);
  const seam = result.cells.find(cell => cell.key === '1/5');
  assert.equal(seam.fragments.length, 2);
  assert(seam.fragments.some(polygon => polygon.some(([x]) => x === 0)));
  assert(seam.fragments.some(polygon => polygon.some(([x]) => x === 6)));
  near(total(result), 12);
});

test('lofted cells follow a curved carrier with closed sides and a distinct material role', () => {
  const layout = P.surfaceCells.clip([{ key: 'panel', polygon: rectangle(0, 0, 2, 1) }]);
  const sample = ([u, v], level) => [u, u * u / 2 + level, v];
  const mesh = P.surfaceCells.loft(layout, {
    sample, levels: [-.05, .12], step: .3, metadata: key => ({ surface: key, material: 'ceramic' })
  }).finish();
  assert(mesh.positions.length > 36);
  for (const group of mesh.groups) {
    assert.equal(group.surface, 'panel');
    assert.equal(group.material, 'ceramic');
  }
  const edges = new Map();
  for (let i = 0; i < mesh.positions.length; i += 9) {
    const points = [0, 3, 6].map(j => Array.from(mesh.positions.subarray(i + j, i + j + 3)));
    for (const [j, [x, y, z]] of points.entries()) {
      assert(x >= 0 && x <= 2 && z >= 0 && z <= 1);
      assert([-.05, .12].some(level => Math.abs(y - x * x / 2 - level) < 1e-6));
      const a = points[j].map(v => Math.round(v * 1e6)).join(',');
      const b = points[(j + 1) % 3].map(v => Math.round(v * 1e6)).join(',');
      const key = a < b ? a + '/' + b : b + '/' + a;
      edges.set(key, (edges.get(key) || 0) + (a < b ? 1 : -1));
    }
  }
  assert([...edges.values()].every(sum => sum === 0));
  assert.throws(() => P.surfaceCells.loft(layout, { sample, step: .01, budget: 15 }), /triangle budget/);
  assert.throws(() => P.surfaceCells.loft(layout, { sample: ([u, v]) => [u, 0, v] }), /volume/);
});

test('height prisms preserve a clipped hole and distinguish tessellation seams from outer edges', () => {
  const layout = P.surfaceCells.clip([{key:'cover',polygon:rectangle(0,0,2,2)}],{
    holes:[rectangle(.8,.8,.4,.4)]
  });
  const sample = ([x,z],level) => [x,level+.2*x+.1*z,z];
  const inside = (point,pieces) => pieces.some(({planes}) => planes.every(({normal,offset}) =>
    normal.reduce((sum,component,i)=>sum+component*point[i],0)<=offset+1e-7));
  for(const options of [{step:.27},{planar:true}]){
    const pieces=P.surfaceCells.prisms(layout,{sample,...options});
    assert(pieces.every(piece=>piece.key==='cover'));
    assert(inside([.5,.65,.5],pieces));
    assert(!inside([1,.70,1],pieces));
    assert(!inside([.5,1.4,.5],pieces));
    assert(pieces.every(piece=>piece.planes.some(plane=>plane.kind==='upper'&&plane.exterior)));
    if(!options.planar)assert(pieces.some(piece=>piece.planes.some(plane=>plane.kind==='side'&&!plane.exterior)));
  }
  assert.throws(()=>P.surfaceCells.prisms(layout,{sample,step:.15,budget:1}),/piece budget/);
});

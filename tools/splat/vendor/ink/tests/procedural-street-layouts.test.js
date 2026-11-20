const test = require('node:test');
const assert = require('node:assert/strict');
const { routes } = require('..').load().KIT.procedural;

test('grid and radial tensor components produce orthogonal families and traced curvature', () => {
  const grid = routes.tensor([{type:'grid',angle:Math.PI/4}]),
    g = grid.sample(3,-2);
  assert(Math.abs(g.major[0] - Math.SQRT1_2) < 1e-10);
  assert.equal(g.major[0] * g.minor[0] + g.major[1] * g.minor[1], 0);
  const ring = routes.tensor([{ type: 'ring', origin: [0,0] }]),
    paths = routes.followTensor(ring, [{id:'loop',point:[1,0],family:'major'}], {
      bounds:{min:[-1.3,-1.3],max:[1.3,1.3]}, step:0.09,length:2.5
    });
  assert.equal(paths.streets.length,1);
  const route = paths.streets[0].route;
  assert(route.points.length > 35);
  assert(route.points.every(([x,,z]) => Math.abs(Math.hypot(x,z) - 1) < 0.02));
  assert(route.points.some(([x,,z]) => z > 0.85));
});

test('seeded road agents join crossing streets at shared nodes and honor their segment limit', () => {
  const opts = {
      bounds: {min:[-2,-2],max:[2,2]},
      step:0.38, branchChance:0, snap:0, seed:4, maxAge:12, cost:(x,z)=>Math.min(Math.abs(x),Math.abs(z))*100
    },
    seeds = [{point:[-1.3,0],angle:0},{point:[0,-1.18],angle:Math.PI/2}],
    grown = routes.growStreets(seeds, opts),
    center = grown.points.findIndex(([x,,z])=>Math.hypot(x,z)<1e-8);
  assert(center >= 0);
  assert(grown.edges.filter(e=>e.a===center || e.b===center).length >= 3);
  assert.deepEqual(grown.edges.map(e=>[e.a,e.b]),routes.growStreets(seeds,opts).edges.map(e=>[e.a,e.b]));
  const limited = routes.growStreets(seeds,{...opts,maxSegments:1});
  assert.equal(limited.status,'limit');
  assert.equal(limited.edges.length,1);
});

test('frontage subdivision clips to a concave block and gives every retained lot real frontage', () => {
  const polygon = [[0,0],[8,0],[8,5],[5,5],[5,3],[0,3]],
    {lots} = routes.parcels(polygon,{edge:0,pitch:2,depth:4});
  assert.deepEqual(lots.map(x=>x.area),[6,6,7,8]);
  assert.deepEqual(lots.map(x=>x.frontage),[
    [[0,0],[2,0]],[[2,0],[4,0]],[[4,0],[6,0]],[[6,0],[8,0]]
  ]);
  for (const lot of lots) {
    assert(lot.fragments.flat().every(([x,z])=>x>=lot.frontage[0][0] - 1e-8 &&
      x<=lot.frontage[1][0]+1e-8 && z>=-1e-8 && z<=4+1e-8));
  }
});

test('medial paths stay inside a holed boundary and report clearance', () => {
  const polygon = [[0,0],[8,0],[8,5],[0,5]],
    hole = [[2.9,1.7],[5.1,1.7],[5.1,3.4],[2.9,3.4]],
    medial = routes.medial([polygon,hole],{spacing:0.4,minRadius:0.2});
  assert(medial.edges.length > 20);
  assert(medial.nodes.some(n=>n.radius>0.65));
  assert(medial.nodes.every(n=>n.radius>=0.2));
  for (const edge of medial.edges) for(let i=0;i<=15;i++){
    const [x,,z] = edge.route.sample(i/15).point;
    assert(x>0 && x<8 && z>0 && z<5);
    assert(x<=2.9 || x>=5.1 || z<=1.7 || z>=3.4);
  }
});

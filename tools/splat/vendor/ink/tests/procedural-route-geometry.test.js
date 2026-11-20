const test = require('node:test');
const assert = require('node:assert/strict');
const { routes } = require('..').load().KIT.procedural;
const box = [[-1,-1],[1,-1],[1,1],[-1,1]];

test('strip footprints share the same shape when their stations are reversed',()=>{
  const next=routes.stripFootprint([1,2],[4,2],.5,.25);
  assert.deepEqual(next,[[.75,1.5],[4.25,1.5],[4.25,2.5],[.75,2.5]]);
  const previous=routes.stripFootprint([4,2],[1,2],.5,.25);
  assert.deepEqual(previous,next.slice(2).concat(next.slice(0,2)));
  assert.deepEqual(routes.stripFootprint([1,2],[1,2],.5),[]);
  assert.throws(()=>routes.stripFootprint([1,2],[4,2],.5,-.1),/extension/);
});

test('pinned returns route around a finite approach and can use either side',()=>{
  const approach=[[0,0],[1.05,0]],end=[3.05,0],base={occupiedHalfWidth:1.5,halfWidth:1.5,
    toeExtension:1.5,clearance:.04,maxLength:30};
  const fit=options=>routes.fitReturn(approach,end,{...base,...options});
  const open=fit();
  assert.equal(open.status,'ok');
  assert.deepEqual(open.points[0],approach[0]);
  assert.deepEqual(open.points.at(-1),end);
  assert(open.points[1][0]<0,'the entry moves away from the occupied approach');
  const side=point=>Math.sign(point[1]);
  const used=side(open.points.reduce((a,b)=>Math.abs(a[1])>=Math.abs(b[1])?a:b));
  assert(used);
  const wall=[[-.9,used*1.9],[3.8,used*1.9],[3.8,used*4],[-.9,used*4]];
  const alternate=fit({obstacles:[wall]});
  assert.equal(alternate.status,'ok');
  assert(alternate.points.every(point=>side(point)!==used));
  assert.deepEqual(alternate.points.at(-1),end);
  assert.equal(routes.fitReturn(approach,[.6,.2],base).status,'blocked-pin');
  assert.equal(fit({maxLength:2}).status,'unreachable');
});

test('one return clears two opposing approaches with a straight lead at each pin',()=>{
  const first=[[0,0],[1.05,0]],second=[[7,0],[5.95,0]],end=second[0],
    options={occupiedHalfWidth:1.5,halfWidth:1.5,toeExtension:1.5,clearance:.04,
      maxLength:32,endApproach:second};
  assert.equal(routes.fitReturn(first,end,options).status,'ok');
  const shape=routes.fitReturn(first,end,options),points=shape.points;
  assert.deepEqual(points[0],first[0]);
  assert.deepEqual(points.at(-1),end);
  assert(points[1][0]<=-1.54);
  assert(points.at(-2)[0]>=8.54);
  const side=Math.sign(points.find(p=>Math.abs(p[1])>3)[1]),
    barrier=[[1,2*side],[6,2*side],[6,4*side],[1,4*side]];
  const alternate=routes.fitReturn(first,end,{...options,obstacles:[barrier]});
  assert.equal(alternate.status,'ok');
  assert(alternate.points.some(p=>p[1]*side<-3));
  assert.equal(routes.fitReturn(first,end,{...options,maxLength:5}).status,'unreachable');
  assert.equal(routes.fitReturn(first,[.5,0],{...options,endApproach:[[.5,0],[2,0]]}).status,'blocked-pin');
  assert.throws(()=>routes.fitReturn(first,end,{...options,endApproach:[[6.9,0],[5.95,0]]}),/destination/);
});

test('strip joins close only the outside of a turn and partition the overlapping strips',()=>{
  const close=(a,b)=>assert(Math.abs(a-b)<1e-8,`${a} vs ${b}`);
  const center=[2,3],previous=[0,3],next=[2,5];
  const join=routes.stripJoin(previous,center,next,1),reverse=routes.stripJoin(next,center,previous,1);
  assert.equal(join.exterior.length,6);
  assert.deepEqual(join.exterior[0],center);
  close(join.exterior[1][0],2);
  close(join.exterior[1][1],2);
  close(join.exterior.at(-1)[0],3);
  close(join.exterior.at(-1)[1],3);
  for(const [x,y] of join.exterior.slice(1)){
    assert(x>=2-1e-8&&y<=3+1e-8);
    close(Math.hypot(x-2,y-3),1);
  }
  const before=[[0,2],[2,2],[2,4],[0,4]],after=[[1,3],[3,3],[3,5],[1,5]];
  const incoming=join.clip(before,'incoming'),outgoing=join.clip(after,'outgoing');
  assert(incoming.every(([x,y])=>x+y<=5+1e-8));
  assert(outgoing.every(([x,y])=>x+y>=5-1e-8));
  assert.deepEqual(reverse.clip(before,'outgoing'),incoming);
  assert.deepEqual(reverse.clip(after,'incoming'),outgoing);
  assert.deepEqual(join.clip(after.map(([x,y])=>[x+4,y]),'incoming'),[]);
  const bevel=routes.stripJoin(previous,center,next,1,{maxArcAngle:Math.PI});
  assert.equal(bevel.exterior.length,3);
  center[0]=20;
  assert.deepEqual(join.clip(before,'incoming'),incoming);
  assert.equal(routes.stripJoin([0,0],[1,0],[2,0],1),null);
  assert.equal(routes.stripJoin([0,0],[1,0],[0,0],1),null);
  assert.equal(routes.stripJoin([1,0],[1,0],[1,2],1),null);
  assert.throws(()=>routes.stripJoin(previous,center,next,0),/positive width/);
});

test('landing footprints leave room for one or more measured approaches',()=>{
  const center=[0,2,0],at={center,tangent:[1,.4,0],width:4,depth:2},
    stair={point:[0,2,0],direction:[-1,-.8,0]},
    side={point:[0,2,0],direction:[0,-.2,1]};
  const sideBounds=ring=>[Math.min(...ring.map(p=>p[0])),Math.max(...ring.map(p=>p[0])),
    Math.min(...ring.map(p=>p[1])),Math.max(...ring.map(p=>p[1]))];
  assert.deepEqual(sideBounds(routes.landingFootprint(at)),[-1,1,-2,2]);
  assert.deepEqual(sideBounds(routes.landingFootprint({...at,approaches:[stair]})),[0,1,-2,2]);
  assert.deepEqual(sideBounds(routes.landingFootprint({...at,approaches:[stair,side]})),[0,1,-2,0]);
  assert.deepEqual(sideBounds(routes.landingFootprint({...at,approaches:[
    {...stair,point:[-.5,2,0]}]})),[-.5,1,-2,2]);
  assert.deepEqual(routes.landingFootprint({...at,approaches:[
    stair,{...stair,direction:[1,-.3,0]}]}),[]);
  assert.throws(()=>routes.landingFootprint({...at,tangent:[0,1,0]}),/horizontal/);
});

test('upright route motion preserves level surfaces and rejects stretching or shearing',()=>{
  const guide=[[0,0,0],[0,1,0],[2,1,0],[2,2,2]],
    moved=guide.map(([x,y,z])=>[z+3,y-.4,1-x]);
  const rigid=routes.uprightMotion(guide,moved);
  assert.deepEqual(rigid.t,[3,-.4,1]);
  for(const [k,expected] of [0,0,1,0,1,0,-1,0,0].entries())assert(Math.abs(rigid.R[k]-expected)<1e-9);
  assert.equal(routes.uprightMotion(guide,moved.map(([x,y,z])=>[x,y+x*.2,z])),null);
  assert.equal(routes.uprightMotion(guide,moved.map(([x,y,z])=>[x*1.1,y,z])),null);
  assert.deepEqual(routes.uprightMotion([[1,2,3],[1,4,3]],[[2,3,4],[2,5,4]]).t,[1,1,1]);
  assert.equal(routes.uprightMotion([[0,0,0],[0,1,0]],[[1,0,1],[1,2,1]]),null);
  assert.throws(()=>routes.uprightMotion([],[]),/paired/);
});

test('visibility graphs choose the shortest plan path around polygons and keep exact pins', () => {
  const a = [-4, 0.1, 0], b = [4, 0.4, 0],
    path = routes.visibility(a, b, [box]);
  assert.equal(path.status, 'ok');
  const points = path.route.points;
  assert.equal(points.length, 4);
  assert.deepEqual(points[0], a);
  assert.deepEqual(points.at(-1), b);
  assert(points.slice(1, -1).every(p => Math.abs(p[0]) === 1 && Math.abs(p[2]) === 1));
  const run = points.slice(1).reduce((sum, p, i) => sum + Math.hypot(p[0] - points[i][0], p[2] - points[i][2]), 0);
  assert.equal(run, 2 * Math.sqrt(10) + 2);
  assert.equal(routes.visibility([0, 0, 0], b, [box]).status, 'blocked-pin');
  assert.equal(routes.visibility(a, b, [box], { maxTests: 1 }).status, 'budget');
  assert.equal(routes.visibility([0, 0, -1], [3, 0, -1], [box]).route.points.length, 2);
});

test('the visibility test respects concave outlines and corridors between close obstacles', () => {
  const concave = [[0,0],[3,0],[3,2],[2,2],[2,1],[1,1],[1,2],[0,2]],
    p = routes.visibility([1.5, 0, 3], [1.5, 0, 1.2], [concave]),
    q = routes.visibility([-3, 0, 3], [5, 0, 3], [concave, [[-2,3.1],[5,3.1],[5,4],[-2,4]]]);
  assert.equal(p.route.points.length, 2);
  assert.equal(q.route.points.length, 2);
});

test('spline fitting rounds safe corners while retaining a corner that would enter a keep-out', () => {
  const raw = routes.polyline([[-2, 0, 0], [-1, 0, 0], [-1, 0, 1], [2, 0, 1]]),
    options = { radius: 0.7, spacing: 0.035, keepOut: (x, z) => x < -1 && z > 0 },
    rounded = routes.spline(raw, options);
  assert.equal(rounded.status, 'ok');
  assert.equal(rounded.work.retained, 1);
  assert.equal(rounded.work.rounded, 1);
  assert.equal(rounded.quadratics.length, 1);
  assert.deepEqual(rounded.route.points[0], raw.points[0]);
  assert.deepEqual(rounded.route.points.at(-1), raw.points.at(-1));
  for (let i = 0; i <= 300; i++) {
    const [x, , z] = rounded.route.sample(i / 300).point;
    assert(!options.keepOut(x, z));
  }
  assert.equal(routes.spline(raw, { clearance: () => -1 }).status, 'blocked');
});

test('fast marching solves a uniform Eikonal field and traces a route through continuous coordinates', () => {
  const bounds = { min: [-3, -3], max: [3, 3] },
    field = routes.travelTime([[0, 0]], { bounds, cell: 0.06 });
  assert.equal(field.time(0, 0), 0);
  assert(Math.abs(field.time(2.4, 0) - 2.4) < 1e-9);
  assert(Math.abs(field.time(2, 2) - Math.sqrt(8)) < 0.14);
  const start = [-2.15, -1.74],
    plan = field.trace(start, { height: (x, z) => 0.19 * z }),
    output = plan.route.points;
  assert.equal(plan.status, 'ok');
  assert.deepEqual(output[0], [start[0], 0.19 * start[1], start[1]]);
  assert.deepEqual(output.at(-1), [0, 0, 0]);
  for (let i = 1; i < output.length; i++) {
    assert(field.time(output[i][0], output[i][2]) <= field.time(output[i - 1][0], output[i - 1][2]) + 1e-8);
  }
});

test('fast marching traces around a blocked disk, chooses seeded outlets, and reports unreachable cells', () => {
  const bounds = { min: [-5, -4], max: [5, 4] },
    speed = (x, z) => Math.hypot(x, z) > 1.21 ? (z < -2 ? 0.6 : 1) : 0,
    field = routes.travelTime([[4, 0.13], [4, 3.1]], { bounds, cell: 0.18, speed });
  const plan = field.trace([-4, 0]);
  assert.equal(plan.status, 'ok');
  assert(Math.abs(plan.route.length - 8) > 0.1);
  for (let i = 0; i <= 500; i++) {
    const [x, , z] = plan.route.sample(i / 500).point;
    assert(speed(x, z) > 0);
  }
  assert.equal(field.trace([0, 0]).status, 'blocked');
  const wall = routes.travelTime([[3, 0]], { bounds, cell: 0.22, speed: x => Math.abs(x) < 0.14 ? 0 : 1 });
  assert.equal(wall.time(-2, 0), Infinity);
  assert.equal(wall.trace([-2, 0]).status, 'unreachable');
});

test('shared convex footprints reserve a disk margin around unordered and acute samples', () => {
  const samples = [[3, 0], [-1, 1], [-1, -1], [0, 0], [-1, -1]];
  const margin = 0.7, outline = routes.convexFootprint(samples, { margin });
  assert.deepEqual(routes.convexFootprint(samples), [[-1, -1], [3, 0], [-1, 1]]);
  for (const [x, z] of samples) for (let i = 0; i < 64; i++) {
    const angle = 2 * Math.PI * i / 64, q = [x + margin * Math.cos(angle), z + margin * Math.sin(angle)];
    assert(outline.every(([ax, az], j) => {
      const [bx, bz] = outline[(j + 1) % outline.length];
      return (bx - ax) * (q[1] - az) - (bz - az) * (q[0] - ax) >= -1e-8;
    }));
  }
  const a = [-4, 0.2, 0], b = [5, 1.4, 0],
    path = routes.visibility(a, b, [outline, routes.convexFootprint([[1, 1], [2, 1], [2, 3], [1, 3]], { margin })]);
  assert.equal(path.status, 'ok');
  assert.deepEqual(path.route.points[0], a);
  assert.deepEqual(path.route.points.at(-1), b);
  assert(path.route.points.length > 2);
});

test('convex clearance checks permit exact boundary travel and reject interior chords in either winding', () => {
  const loop = Array.from({length: 96}, (_, i) => {
    const angle = i * Math.PI * 2 / 96;
    return [5e5 + 3 * Math.cos(angle), -5e5 + 3 * Math.sin(angle)];
  });
  const pin = ([x, z], y = 0) => [x, y, z];
  for (const polygon of [loop, loop.slice().reverse()]) {
    const a = pin(loop[0]), edge = pin(loop[1]), b = pin(loop[24], 1);
    assert.equal(routes.visibility(a, edge, [polygon]).route.points.length, 2);
    const route = routes.visibility(a, b, [polygon], { maxTests: 250000 });
    assert.equal(route.status, 'ok');
    assert.equal(route.route.points.length, 25);
    assert.deepEqual(route.route.points[0], a);
    assert.deepEqual(route.route.points.at(-1), b);
    assert.equal(routes.visibility(pin([5e5, -5e5]), b, [polygon]).status, 'blocked-pin');
  }
});

test('visibility links bypass only their own obstacle and report the chosen point indices', () => {
  const wall = [[-2,-4],[2,-4],[2,4],[-2,4]], origin = [-3,0,1], end = [3,0.4,1];
  const links = [{start: [-3,1], end: [3,1], through: 0}];
  const pass = routes.visibility(origin, end, [wall], { links });
  assert.deepEqual(pass.route.points, [origin,end]);
  assert.deepEqual(pass.links, [{link: 0, from: 0, to: 1}]);
  const reverse = routes.visibility(end, origin, [wall], { links });
  assert.equal(reverse.links[0].link,0);
  assert.deepEqual(reverse.route.points, [end,origin]);
  const other = [[-.1, .8],[.1,.8],[.1,1.2],[-.1,1.2]];
  const blocked = routes.visibility(origin, end, [wall,other], { links });
  assert(!blocked.links);
  assert(blocked.route.length > pass.route.length);
});

test('a link can cross a composite obstacle while every other polygon remains solid', () => {
  const rectangle = (x0, x1, z0, z1) => [[x0,z0],[x1,z0],[x1,z1],[x0,z1]];
  const walls = [rectangle(-2,.1,-2,2),rectangle(-.1,2,-2,2)];
  const origin = [-3,0,0], end = [3,.2,0], start = [-3,0], finish = [3,0];
  const link = {start, end:finish, through:[0,1]};
  const pass = routes.visibility(origin,end,walls,{links:[link]});
  assert.deepEqual(pass.route.points,[origin,end]);
  assert.deepEqual(pass.links,[{link:0,from:0,to:1}]);
  const partly = routes.visibility(origin,end,walls,{links:[{...link,through:[0]}]});
  assert.equal(partly.links,undefined);
  const blocked = routes.visibility(origin,end,walls.concat([rectangle(-.2,.2,-.3,.3)]),{links:[link]});
  assert.equal(blocked.links,undefined);
  for(const through of [[],[1,1],[0,2],new Array(1)])
    assert.throws(()=>routes.visibility(origin,end,walls,{links:[{...link,through}]}),/obstacle indices/);
});

test('swept clearance probes both sides and headroom along a sloping span', () => {
  const start = [0,.8,0], end = [3,1.4,0];
  const section = {halfWidth: .5, below: .2, above: .35, spacing: .1, minClearance: .02};
  const tunnel = ([x,y,z]) => x < 1 || x > 2 ? Infinity : Math.min(.6 - Math.abs(z), 1.8 - y, y - .5);
  assert.equal(routes.sweep(start, end, {...section,clearance:tunnel}).status,'ok');
  const tight = routes.sweep(start, end, {...section,halfWidth:.65,clearance:tunnel});
  assert.equal(tight.status,'blocked');
  assert(Math.abs(tight.point[2]) >= .5);
  assert.equal(routes.sweep(start, end, {...section,above:.9,clearance:tunnel}).status,'blocked');
  assert.equal(routes.sweep(start, end, {...section,maxSamples:2,clearance:tunnel}).status,'budget');
});

test('bent visibility links keep private waypoints and use their length for the grade', () => {
  const wall=[[-2,-4],[2,-4],[2,4],[-2,4]],start=[-3,.5,0],end=[3,1.1,0];
  const link={start:[-3,0],end:[3,0],via:[[-1,.6],[1,.6]],through:0};
  const result=routes.visibility(start,end,[wall],{links:[link]});
  const points=result.route.points;
  assert.deepEqual(result.links,[{link:0,from:0,to:3}]);
  assert.deepEqual(points.map(([x,,z])=>[x,z]),[link.start,...link.via,link.end]);
  assert.deepEqual(points[0],start);
  assert.deepEqual(points.at(-1),end);
  const first=Math.hypot(2,.6),run=first*2+2;
  assert(Math.abs(points[1][1]-(.5+.6*first/run))<1e-9);
  const reversed=routes.visibility(end,start,[wall],{links:[link]});
  assert.deepEqual(reversed.route.points.map(([x,,z])=>[x,z]),[link.end,...link.via.slice().reverse(),link.start]);
  const obstacle=[[-.2,.45],[.2,.45],[.2,.75],[-.2,.75]];
  assert.equal(routes.visibility(start,end,[wall,obstacle],{links:[link]}).links,undefined);
  const long={...link,via:[[-1,3.9],[1,-3.9]]};
  assert.equal(routes.visibility(start,end,[wall],{links:[long]}).links,undefined);
  assert.throws(()=>routes.visibility(start,end,[wall],{links:[link],maxVertices:9}),/vertex budget/);
  assert.throws(()=>routes.visibility(start,end,[wall],{links:[{...link,via:[link.start]}]}),/nonzero spans/);
});

test('path section clearance probes the exposed corner join under a shared sample limit', () => {
  const points=[[-1,.3,0],[0,.3,0],[0,.3,1]],clearance=([x,,z])=>Math.hypot(x-.25,z+.25)-.08;
  const options={halfWidth:.4,below:.12,above:.45,spacing:.06,clearance};
  assert.equal(routes.sweep(points[0],points[1],options).status,'ok');
  assert.equal(routes.sweep(points[1],points[2],options).status,'ok');
  const blocked=routes.sweepPath(points,options);
  assert.equal(blocked.status,'blocked');
  assert(blocked.point[0]>0&&blocked.point[2]<0);
  const open=routes.sweepPath(points,{...options,clearance:()=>Infinity});
  assert.equal(open.status,'ok');
  const budget=routes.sweepPath(points,{...options,clearance:()=>Infinity,maxSamples:open.samples-1});
  assert.equal(budget.status,'budget');
  assert(budget.samples<open.samples);
});

test('section bands reserve a deck and a single rail on the oriented side of a sloped run',()=>{
  const start=[-1,.3,0],end=[1,.4,0],field=([,y,z])=>Math.max(.64-y,z+.17),
    right={lateral:[.33,.48],vertical:[0,.67]},deck={lateral:[-.53,.53],vertical:[-.14,.01]},
    options={spacing:.055,clearance:field,sectionBands:[deck,right]};
  const open=routes.sweep(start,end,options);
  assert.equal(open.status,'ok');
  const reversed=routes.sweep(end,start,options);
  assert.equal(reversed.status,'blocked');
  assert(reversed.point[2]<-.25);
  assert.equal(routes.sweep(start,end,{...options,maxSamples:open.samples-1}).status,'budget');
  assert.throws(()=>routes.sweep(start,end,{...options,sectionBands:[{...deck,lateral:[1,-1]}]}),/intervals/);
  const outline=[[-.8,0],[.8,0],[.8,1.4],[-.8,.63]],
    chart={project:([,y,z])=>[z,y],minHeight:.28,maxHeight:.43,maxGrade:.15,clearance:.008};
  assert(routes.profileSection(outline,[-1,0],[1,0],{...chart,sectionBands:[deck,right]}));
  assert.equal(routes.profileSection(outline,[1,0],[-1,0],{...chart,sectionBands:[deck,right]}),null);
});

test('banded joins reserve rail height on the outside corner only when that side has a rail',()=>{
  const points=[[-1,.3,0],[0,.3,0],[0,.3,1]],deck={lateral:[-.45,.45],vertical:[-.12,.035]},
    inside={lateral:[.33,.45],vertical:[0,.64]},outside={lateral:[-.45,-.33],vertical:[0,.64]},
    options={spacing:.045,maxSamples:24000,clearance:([x,y,z])=>Math.max(.58-y,Math.hypot(x-.26,z+.26)-.07)};
  assert.equal(routes.sweepPath(points,{...options,sectionBands:[deck,inside]}).status,'ok');
  assert.equal(routes.sweep(points[0],points[1],{...options,sectionBands:[deck,outside]}).status,'ok');
  assert.equal(routes.sweep(points[1],points[2],{...options,sectionBands:[deck,outside]}).status,'ok');
  const hit=routes.sweepPath(points,{...options,sectionBands:[deck,outside]});
  assert.equal(hit.status,'blocked');
  assert(hit.point[0]>.1&&hit.point[2]<-.1&&hit.point[1]>.58);
});

test('section height bands climb a curved guide under a ceiling that only clears one rail side',()=>{
  const path=[[-1,0],[0,0],[0,1]],deck={lateral:[-.4,.4],vertical:[-.12,.04]},
    inside={lateral:[.3,.4],vertical:[0,.64]},outside={lateral:[-.4,-.3],vertical:[0,.64]},
    ground=(x,z)=>.2+Math.max(0,.24-Math.hypot(x,z)*.42),
    ceiling=(x,z)=>Math.hypot(x-.24,z+.24)<.15?.76:1.28,
    options={minHeight:.2,maxHeight:.65,spacing:.045,
      clearHeights:(x,z,low,high)=>[ground(x,z)-low,ceiling(x,z)-high]};
  const fit=routes.sectionHeightBands(path,{...options,sectionBands:[deck,inside]});
  assert.equal(fit.status,'ok');
  assert.deepEqual(fit.stations.filter(s=>s.keep).map(s=>s.point),path);
  assert(fit.stations.find(s=>s.at===1).min>.54);
  const profile=routes.fitHeightBands(fit.stations,{maxGrade:.65,maxPoints:12});
  assert(profile);
  const points=profile.indices.map((index,i)=>{
    const [x,z]=fit.stations[index].point;
    return [x,profile.elevations[i],z];
  });
  assert.equal(routes.sweepPath(points,{spacing:.045,maxSamples:24000,sectionBands:[deck,inside],
    clearance:([x,y,z])=>Math.min(y-ground(x,z)+.015,ceiling(x,z)-y)}).status,'ok');
  assert.equal(routes.sectionHeightBands(path,{...options,sectionBands:[deck,inside,outside]}).status,'blocked');
  assert.equal(routes.sectionHeightBands(path.slice().reverse(),{...options,sectionBands:[deck,outside]}).status,'ok');
  assert.equal(routes.sectionHeightBands(path.slice().reverse(),{...options,sectionBands:[deck,inside]}).status,'blocked');
  assert.deepEqual(routes.sectionHeightBands(path,{...options,sectionBands:[deck,inside],maxSamples:10}),
    {status:'budget',samples:10});
  assert.deepEqual(routes.sectionHeightBands(path,{...options,sectionBands:[deck,inside],maxStations:10}),
    {status:'budget',samples:0});
});

test('certified crossings can restrict graph traversal direction in plan and elevation',()=>{
  const ring=[[-.8,-4],[.8,-4],[.8,4],[-.8,4]],a=[-2,.45,0],b=[2,.45,0],
    link={start:[-1,0],end:[1,0],through:0,direction:'forward'};
  assert.equal(routes.visibility(a,b,[ring],{links:[link]}).links?.[0].link,0);
  assert.equal(routes.visibility(b,a,[ring],{links:[link]}).links,undefined);
  const walls=[{ring,min:-2,max:3}],
    opening={points:[[-1,.45,0],[1,.45,0]],through:[0],direction:'forward'},
    options={minHeight:.1,maxHeight:1.4,maxGrade:.8,maxLength:5,links:[opening]};
  assert.equal(routes.prismVisibility(a,b,walls,options).links?.[0].link,0);
  assert.equal(routes.prismVisibility(b,a,walls,options).status,'unreachable');
  assert.equal(routes.prismVisibility(b,a,walls,{...options,links:[{...opening,direction:'reverse'}]}).links?.[0].link,0);
});

test('visibility waypoints connect through a composed clearance domain and respect erasure',()=>{
  const start=[-2,.3,0],end=[0,.7,2],waypoints=[[0,0],[-1.6,1.6]];
  const clearance=(x,z)=>.52-Math.min(
    Math.hypot(x-Math.max(-2,Math.min(x,0)),z),
    Math.hypot(x,z-Math.max(0,Math.min(z,2)))
  );
  const domain={clearance,minClearance:.2,spacing:.055},options={domain,waypoints};
  const route=routes.visibility(start,end,[],options);
  assert.equal(route.status,'ok');
  assert.deepEqual(route.route.points,[start,[0,.5,0],end]);
  const erase=(x,z)=>Math.min(clearance(x,z),Math.hypot(x,z)-.24);
  assert.equal(routes.visibility(start,end,[],{...options,domain:{...domain,clearance:erase}}).status,'unreachable');
  const wall=[[-.75,-.75],[.75,-.75],[.75,.75],[-.75,.75]];
  const links=[{start:[-2,0],end:[0,2],via:[[0,0]],through:0}];
  assert.deepEqual(routes.visibility(start,end,[wall],{links,domain}).links,[{link:0,from:0,to:2}]);
  assert.equal(routes.visibility(start,end,[wall],{links,domain:{...domain,clearance:erase}}).status,'unreachable');
  assert.equal(routes.visibility(start,end,[],{...options,maxTests:2}).status,'budget');
  assert.equal(routes.visibility([-3,0,0],end,[],options).status,'blocked-pin');
  assert.throws(()=>routes.visibility(start,end,[],{...options,maxVertices:3}),/vertex budget/);
  assert.throws(()=>routes.visibility(start,end,[],{domain:{clearance:()=>NaN}}),/signed distance/);
});

test('elevation profiles climb over or dip under a barrier within the forward grade limit',()=>{
  const bands=[{from:4,to:6,min:.2,max:1.5}];
  const over=routes.elevationProfile(10,.6,.6,bands,{minHeight:.35,maxGrade:.25});
  assert.equal(over.status,'ok');
  assert.deepEqual(over.points,[[0,.6],[4,1.5],[6,1.5],[10,.6]]);
  const under=routes.elevationProfile(10,.6,.6,bands,{minHeight:.1,maxGrade:.25});
  assert.deepEqual(under.points,[[0,.6],[4,.2],[6,.2],[10,.6]]);
  assert.equal(routes.elevationProfile(10,.6,.6,bands,{minHeight:.35,maxGrade:.1}).status,'unreachable');
  assert.equal(routes.elevationProfile(10,.6,.6,bands,{maxVertices:5}).status,'budget');
});

test('an elevation profile fits between overlapping high and low clearance bands',()=>{
  const bands=[{from:3,to:7,min:-1,max:1.15},{from:4,to:8,min:1.5,max:3}];
  const fitted=routes.elevationProfile(12,.55,.9,bands,{minHeight:.4,maxHeight:2,maxGrade:.35});
  assert.equal(fitted.status,'ok');
  assert.deepEqual(fitted.points[0],[0,.55]);
  assert.deepEqual(fitted.points.at(-1),[12,.9]);
  for(let i=1;i<fitted.points.length;i++){
    const [a,y]=fitted.points[i-1],[b,z]=fitted.points[i];
    assert(b>a&&Math.abs(z-y)<=.35*(b-a)+1e-9);
    for(const band of bands)for(let s=Math.max(a,band.from)+.01;s<Math.min(b,band.to);s+=.02){
      const height=y+(s-a)/(b-a)*(z-y);
      assert(height<=band.min+1e-9||height>=band.max-1e-9);
    }
  }
});

test('prism visibility climbs over one solid and turns around another within the same length and grade limits',()=>{
  const rect=(x0,x1,z0,z1)=>[[x0,z0],[x1,z0],[x1,z1],[x0,z1]];
  const pins=[[0,.5,0],[13,.5,0]];
  const obstacles=[{ring:rect(3,4,-9,9),min:-1,max:1.5},{ring:rect(6,8,-1.5,1.5),min:-1,max:7}];
  const limits={minHeight:.45,maxHeight:3,maxGrade:.7,maxLength:15,floor:()=>.45};
  const route=routes.prismVisibility(...pins,obstacles,limits);
  assert.equal(route.status,'ok');
  assert.deepEqual([route.points[0],route.points.at(-1)],pins);
  assert(route.points.some(([,y])=>y>=1.5));
  assert(route.points.some(([,,z])=>Math.abs(z)>=1.5));
  for(let i=1;i<route.points.length;i++){
    const [a,b]=route.points.slice(i-1,i+1);
    assert(Math.abs(b[1]-a[1])<=.7*Math.hypot(b[0]-a[0],b[2]-a[2])+1e-9);
  }
  assert.equal(routes.prismVisibility(...pins,obstacles,{...limits,maxGrade:.1}).status,'unreachable');
  assert.equal(routes.prismVisibility(...pins,obstacles,{...limits,maxVertices:4}).status,'budget');
  assert.equal(routes.prismVisibility(...pins,obstacles,{...limits,maxTests:5}).status,'budget');
  assert.equal(routes.prismVisibility(...pins,obstacles,{...limits,floor:()=>.7}).status,'blocked-pin');
  assert.equal(routes.prismVisibility([3.5,.5,0],pins[1],obstacles,limits).status,'blocked-pin');
});

test('prism visibility can dip below an elevated band while bypassing a second solid',()=>{
  const reverse=(a,b,c,d)=>[[a,c],[a,d],[b,d],[b,c]];
  const obstacles=[{ring:reverse(3,4,-9,9),min:.65,max:8},{ring:reverse(6,8,-1.5,1.5),min:-1,max:8}];
  const bounds={minHeight:.3,maxHeight:2,maxGrade:.7,maxLength:13,floor:()=>.3};
  const route=routes.prismVisibility([0,1.5,0],[12,1.5,0],obstacles,bounds);
  assert.equal(route.status,'ok');
  assert(route.points.some(([,y])=>y<=.65));
  assert(route.points.some(([,,z])=>Math.abs(z)>=1.5));
  assert.equal(routes.prismVisibility([0,1.5,0],[12,1.5,0],obstacles,{...bounds,floor:()=>.8}).status,'unreachable');
});

test('bounded footprint simplification keeps the entire rounded clearance hull inside',()=>{
  const ring=Array.from({length:128},(_,i)=>{
    const t=i*Math.PI/64;
    return [4+2.3*Math.cos(t),-5+.8*Math.sin(t)];
  });
  const dense=routes.convexFootprint(ring,{margin:.18});
  const coarse=routes.convexFootprint(ring,{margin:.18,maxSides:16});
  assert.equal(coarse.length,16);
  assert(dense.length>coarse.length);
  for(const [x,z] of dense)for(const [i,[a,b]] of coarse.entries()){
    const [c,d]=coarse[(i+1)%coarse.length];
    assert((c-a)*(z-b)-(d-b)*(x-a)>=-1e-9);
  }
});

test('prism links preserve bent passage geometry while other obstacles still require elevation clearance', () => {
  const box=(lo,hi,z)=>[[lo,-z],[hi,-z],[hi,z],[lo,z]];
  const solids=[
    {ring:box(3,4,5),min:-1,max:1.4},
    {ring:box(7,8,5),min:-1,max:5}
  ];
  const points=[[6.8,1.4,.6],[7.4,1.4,.68],[8.2,1.4,.6]];
  const pins=[[0,.45,0],[12,.45,0]],link={points,through:[1]};
  const limits={minHeight:.2,maxHeight:2,maxGrade:.7,maxLength:14};
  assert.equal(routes.prismVisibility(...pins,solids,limits).status,'unreachable');
  const result=routes.prismVisibility(...pins,solids,{...limits,links:[link]});
  assert.equal(result.status,'ok');
  assert(result.points.some(([x,y])=>x>=3&&x<=4&&y>=1.4));
  assert.deepEqual(result.points.slice(result.links[0].from,result.links[0].to+1),points);
  assert(Object.isFrozen(result.links)&&Object.isFrozen(result.links[0]));
  const reverse=routes.prismVisibility(pins[1],pins[0],solids,{...limits,links:[link]});
  assert.deepEqual(reverse.points.slice(reverse.links[0].from,reverse.links[0].to+1),points.slice().reverse());
  assert.equal(routes.prismVisibility(...pins,solids,{...limits,links:[{...link,through:[]}]}).status,'unreachable');
  const other={ring:[[7.2,.4],[7.7,.4],[7.7,.9],[7.2,.9]],min:1,max:2};
  assert.equal(routes.prismVisibility(...pins,[...solids,other],{...limits,links:[link]}).status,'unreachable');
  const interior={...link,points:points.slice(1)};
  assert.equal(routes.prismVisibility(...pins,solids,{...limits,links:[interior]}).status,'unreachable');
  assert.equal(routes.prismVisibility(...pins,solids,{...limits,links:[link],
    floor:(x,z)=>x>=7.2&&x<=7.8&&z>.35&&z<.9?1.6:0,spacing:.12}).status,'unreachable');
  assert.throws(()=>routes.prismVisibility(...pins,solids,{...limits,links:[{...link,through:[2]}]}),/prism indices/);
});

test('guide profiles preserve planar corners within continuous flights and report projected crossings',()=>{
  const guide=[[0,0],[2,0],[2,2],[4,2],[4,4]];
  const prism={ring:[[1.6,1.25],[2.4,1.25],[2.4,1.75],[1.6,1.75]],min:-1,max:1.3};
  const options={minHeight:.2,maxHeight:2,maxGrade:.7,maxLength:9};
  const result=routes.guideElevation(guide,.4,.4,[prism],options);
  assert.equal(result.status,'ok');
  assert.deepEqual(result.points.map(([x,,z])=>[x,z]).filter(point=>
    guide.some(p=>point.every((v,i)=>p[i]===v))),guide);
  assert.deepEqual(result.points[0],[0,.4,0]);
  assert.deepEqual(result.points.at(-1),[4,.4,4]);
  assert.equal(result.flights.length,3);
  assert(result.flights[0].last>1,'the first flight continues across a planar corner');
  assert.equal(result.points[result.flights[0].last][1],1.3);
  assert.equal(result.points[result.flights[1].last][1],1.3);
  assert.equal(result.crossings.length,1);
  assert.equal(result.crossings[0].prism,0);
  assert(Math.abs(result.crossings[0].from-3.25)<1e-7);
  assert(Math.abs(result.crossings[0].to-3.75)<1e-7);
  assert(result.points.slice(1).every((q,i)=>
    Math.abs(q[1]-result.points[i][1])<=.7*(result.stations[i+1]-result.stations[i])+1e-8));
  assert.equal(routes.guideElevation(guide,.4,.4,[prism],{...options,maxLength:8}).status,'unreachable');
  assert.equal(routes.guideElevation(guide,.4,.4,[prism],{...options,maxTests:7}).status,'budget');
  assert.equal(routes.guideElevation(guide.slice().reverse(),.4,.4,[prism],options).status,'ok');
  assert.throws(()=>routes.guideElevation([[0,0],[0,0]],.4,.4,[]),/nonzero spans/);
});

test('a guide preserves separate entries into one obstacle and reports an obstructed pin',()=>{
  const guide=[[0,0],[4,0],[4,2],[0,2]];
  const prism={ring:[[1,-1],[2,-1],[2,3],[1,3]],min:1.2,max:3};
  const options={minHeight:.3,maxHeight:2,maxGrade:.9};
  const result=routes.guideElevation(guide,1.6,1.6,[prism],options);
  assert.equal(result.status,'ok');
  assert.equal(result.crossings.length,2);
  assert(result.crossings[1].from>result.crossings[0].to);
  assert(result.points.some(([,y])=>y===1.2));
  assert.equal(routes.guideElevation([[1.5,0],[4,0]],1.6,1.6,[prism],options).status,'blocked-pin');
});

test('guide detours replace only blocked station intervals and keep their clearance corridor',()=>{
  const guide=[[-4,-1],[-3,0],[-2,0],[0,0],[2,0],[3,0],[4,1]];
  const left=[[-2.1,-.3],[-1.6,-.3],[-1.6,.62],[-2.1,.62]];
  const right=[[1.6,-.3],[2.1,-.3],[2.1,.62],[1.6,.62]];
  const reserved=[[4,-3],[4,-.04],[-4,-.04],[-4,-3]];
  const options={reserved:[reserved],lead:.3,maxDeviation:.75};
  // The first leg approaches the guide outside the reserved footprint.
  guide[0][1]=.8;
  const result=routes.guideVisibility(guide,[left,right],options);
  assert.equal(result.status,'ok');
  assert.deepEqual(result.points[0],guide[0]);
  assert.deepEqual(result.points.at(-1),guide.at(-1));
  assert.equal(result.splices.length,2);
  const [a,b]=result.splices;
  assert(a.from<a.to&&a.to<b.from&&b.from<b.to);
  assert.deepEqual(result.points.slice(a.last+1,b.first),[[0,0]]);
  assert.deepEqual(result.points.slice(0,a.first),guide.slice(0,2));
  assert.deepEqual(result.points.slice(b.last+1),guide.slice(-2));
  for(const {first,last} of result.splices) {
    assert.equal(result.points[first][1],0);
    assert.equal(result.points[last][1],0);
    assert(result.points.slice(first+1,last).some(([,z])=>z===.62));
    for(let i=first;i<last;i++)for(let k=0;k<=40;k++){
      const t=k/40,[x,z]=result.points[i].map((v,j)=>v+(result.points[i+1][j]-v)*t);
      assert(z>=-.04-1e-8&&z<=.75+1e-8);
      assert(z>=.62-1e-8||x<=-2.1||x>=2.1||(x>=-1.6&&x<=1.6));
    }
  }
  const unchanged=routes.guideVisibility(guide,[],options);
  assert.deepEqual(unchanged.points,guide);
  assert.deepEqual(unchanged.splices,[]);
  assert.equal(routes.guideVisibility(guide,[left,right],{...options,maxDeviation:.4}).status,'unreachable');
  assert.equal(routes.guideVisibility(guide,[left,right],{...options,maxLength:result.length-.1}).status,'unreachable');
  assert.equal(routes.guideVisibility(guide,[left,right],{...options,maxVertices:5}).status,'budget');
  assert.equal(routes.guideVisibility(guide,[left,right],{...options,maxTests:71}).status,'budget');
  assert.equal(routes.guideVisibility([[-1.9,0],[4,1]],[left],options).status,'blocked-pin');
});

test('guide detours cannot jump across the gap between two legs of a bent corridor',()=>{
  const guide=[[-2,0],[0,0],[0,3],[2,3]],obstacle=[[-.22,1],[.3,1],[.3,2],[-.22,2]];
  const result=routes.guideVisibility(guide,[obstacle],{lead:3,maxDeviation:.35});
  assert.equal(result.status,'ok');
  for(const [i,a] of result.points.slice(0,-1).entries())for(let j=0;j<=100;j++){
    const [x,z]=a.map((n,k)=>n+(result.points[i+1][k]-n)*j/100);
    const d=Math.min(Math.hypot(x-Math.min(0,Math.max(x,-2)),z),
      Math.hypot(x,z-Math.min(3,Math.max(z,0))),Math.hypot(x-Math.min(2,Math.max(x,0)),z-3));
    assert(d<=.35+1e-8);
  }
  assert(result.points.length>4);
});

test('a profile section fits endpoint heights to an oblique affine chart and grade bound',()=>{
  const outline=[[-.6,-.5],[.6,-.5],[.6,.5],[-.6,.5]],start=[1,0],end=[5,0],
    options={project:([x,y,z])=>[z+.1*y,y-.5*x],minHeight:0,maxHeight:4,maxGrade:.5,
      halfWidth:.32,below:.11,above:.27,clearance:.03};
  const fit=routes.profileSection(outline,start,end,options);
  assert(fit&&fit.heights.length>=3);
  assert.equal(routes.profileSection(outline,start,end,{...options,maxGrade:0}),null);
  assert.equal(routes.profileSection(outline,start,end,{...options,maxGrade:.25}),null);
  assert.equal(routes.profileSection(outline,start,end,{...options,halfWidth:.7}),null);
  const near=fit.closest([0,0]);
  assert(near[1]>near[0]+1.4);
  for(const heights of [near,...fit.heights]) {
    assert(Math.abs(heights[1]-heights[0])<=2+1e-8);
    for(let i=0;i<=20;i++)for(const z of [-.32,0,.32])for(const dy of [-.11,.27]){
      const t=i/20,y=heights[0]+t*(heights[1]-heights[0]);
      const [u,v]=options.project([1+4*t,y+dy,z]);
      assert(Math.abs(u)<=.57+1e-8&&Math.abs(v)<=.47+1e-8);
    }
  }
  const reversed=routes.profileSection(outline.slice().reverse(),end,start,options);
  const other=reversed.closest([0,0]);
  assert(Math.abs(other[0]-near[1])<1e-8&&Math.abs(other[1]-near[0])<1e-8);
});

test('level profile sections expose a height line and reject oversized guards',()=>{
  const outline=[[-1,-1],[1,-1],[1,1],[-1,1]],options={
    project:([,y,z])=>[z,y],minHeight:-2,maxHeight:2,maxGrade:0,halfWidth:.4,below:.2,above:.8,clearance:.05
  };
  const result=routes.profileSection(outline,[0,0],[4,0],options);
  assert.equal(result.heights.length,2);
  assert(result.heights.every(([a,b])=>Math.abs(a-b)<1e-9));
  const [lo,hi]=result.closest([1,2]);
  assert(Math.abs(lo-.15)<1e-8&&Math.abs(hi-.15)<1e-8);
  assert.deepEqual(result.closest([0,0]),[0,0]);
  assert.equal(routes.profileSection(outline,[0,0],[4,0],{...options,above:2}),null);
});
test('an elevation frame retains moving guide sections and reserves the prism at every height',()=>{
  const {routes}=require('..').load().KIT.procedural;
  const frame=routes.elevationFrame({drift:[-.3,.4],datum:1.5}),
    ring=[[2,-1],[3,-1],[3,1],[2,1]],swept=frame.prismFootprint(ring,2,4);
  const inside=([x,z])=>swept.every(([ax,az],i)=>{
    const [bx,bz]=swept[(i+1)%swept.length];
    return (bx-ax)*(z-az)-(bz-az)*(x-ax)>=-1e-8;
  });
  for(const y of [2,2.5,3,3.75,4])for(const [x,z] of ring){
    const local=frame.project([x,y,z]);
    assert(inside([local[0],local[2]]));
    assert(frame.lift(local).every((value,i)=>Math.abs(value-[x,y,z][i])<1e-9));
  }
  const limit=1.2,grade=frame.grade(limit),a=frame.lift([0,0,0]),b=frame.lift([.6,grade,-.8]);
  assert(Math.abs((b[1]-a[1])/Math.hypot(b[0]-a[0],b[2]-a[2])-limit)<1e-8);
  assert.throws(()=>routes.elevationFrame({drift:[0,Infinity]}),/finite drift/);
});

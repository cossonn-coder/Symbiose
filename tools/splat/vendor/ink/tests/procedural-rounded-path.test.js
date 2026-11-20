const test = require('node:test'),assert = require('node:assert/strict');
const {KIT:K}=require('..').load(),{V}=K,{roundedPath}=K.procedural;
const near=(a,b)=>assert(V.dist(a,b)<1e-7,JSON.stringify({a,b}));

test('a 3D bend meets both legs tangentially and respects the chord error',()=>{
  const chordError=.004,path=[[2,0,0],[2,3,0],[2,3,4]];
  const {points,bends}=roundedPath(path,{radius:.65,chordError});
  const [bend]=bends;
  near(points[0],path[0]);near(points.at(-1),path.at(-1));
  near(points[bend.start],[2,2.35,0]);near(points[bend.end],[2,3,.65]);
  near(bend.center,[2,2.35,.65]);
  for(let i=bend.start;i<=bend.end;i++){
    assert(Math.abs(V.dist(points[i],bend.center)-.65)<1e-7);
    if(i>bend.start){
      const mid=V.mul(V.add(points[i-1],points[i]),.5);
      assert(.65-V.dist(mid,bend.center)<=chordError+1e-8);
    }
  }
});

test('adjacent corners share leg length without overlapping even at a large requested radius',()=>{
  const {points,bends}=roundedPath([[0,0,0],[3,0,0],[3,0,.3],[5,1,.3]],{radius:4});
  assert.equal(bends.length,2);
  assert(bends.every(b=>b.cut<=.3*.45+1e-8&&b.radius<4));
  const a=points[bends[0].end],b=points[bends[1].start];
  assert(a[2]<b[2]);
  assert(V.dist(a,b)>.028);
});

test('a corner deviation limit preserves clearance across the bend',()=>{
  const point=[2,0,0],limit=.04;
  const {points,bends:[bend]}=roundedPath([[0,0,0],point,[2,0,2]],
    {radius:.8,chordError:.001,maxDeviation:limit});
  assert(bend.radius<.1);
  const towardCorner=V.norm(V.sub(point,bend.center));
  const nearest=V.mad(bend.center,towardCorner,bend.radius);
  assert(Math.abs(V.dist(nearest,point)-limit)<1e-8);
  assert(points.some(p=>V.dist(p,nearest)<.03));
});

test('zero radius and reversals retain corners, and sample limits reject oversized subdivision',()=>{
  const reversal=[[0,0,0],[2,0,0],[1,0,0]];
  assert.deepEqual(roundedPath(reversal,{radius:1}),{points:reversal,bends:[]});
  const bent=[[0,0,0],[2,0,0],[2,0,2]];
  assert.deepEqual(roundedPath(bent,{radius:0,budget:3}),{points:bent,bends:[]});
  assert.throws(()=>roundedPath(bent,{radius:1,chordError:1e-6,budget:4}),/sample budget/);
  assert.throws(()=>roundedPath([[0,0,0],[0,0,0]],{radius:1}),/distinct/);
});

const test=require('node:test'),assert=require('node:assert/strict');
const K=require('..').load().KIT,P=K.procedural;
const near=(a,b)=>assert(K.V.dist(a,b)<1e-9);

test('a route follower seeks by distance and looks through a turn without shifting position',()=>{
  const rail=P.routes.polyline([[0,0,0],[4,0,0],[4,0,2]]);
  const follow=P.routes.follower(rail,{lookAhead:1});
  assert.equal(follow.length,6);
  near(follow.sample(2.5).point,[2.5,0,0]);
  assert(follow.sample(3.9).forward[2]>.2);
  const end=follow.sample(12);
  near(end.point,[4,0,2]);near(end.forward,[0,0,1]);
  assert(end.ended);
  near(follow.sample(0,-1).forward,[-1,0,0]);
  assert(follow.sample(0,-1).ended);
  assert.throws(()=>P.routes.follower(rail,{loop:true}),/endpoints/);
});

test('closed routes retain a continuous pose across their junction and expose laps',()=>{
  const route=P.routes.polyline([[0,0,0],[2,0,0],[2,1,2],[0,0,0]]);
  const follow=P.routes.follower(route,{loop:true});
  const a=follow.sample(0),b=follow.sample(route.length);
  near(a.point,b.point);near(a.forward,b.forward);
  assert.equal(b.lap,1);assert(!b.ended);
  assert.equal(follow.sample(-.1).lap,-1);
  assert(K.V.dist(follow.sample(-1e-5).forward,follow.sample(1e-5).forward)<.001);
});

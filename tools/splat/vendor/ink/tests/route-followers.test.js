const {test}=require('node:test');
const assert=require('node:assert/strict');
const {KIT:K}=require('..').load();
const {V}=K;
const line=(length=10)=>K.anim.path([[0,0,0],[0,0,length]],{curve:0});
const circle=()=>K.anim.path(Array.from({length:80},(_,i)=>{const a=i*Math.PI/40;return [4*Math.sin(a),4-4*Math.cos(a),0];}),{closed:true});
const near=(a,b,tolerance=1e-5)=>assert(Math.abs(a-b)<=tolerance,`${a} != ${b}`);
function axes(f){
  for(const a of [f.right,f.up,f.tan]){assert(a.every(Number.isFinite));near(V.len(a),1);}
  near(V.dot(f.right,f.up),0);near(V.dot(f.right,f.tan),0);near(V.dot(f.up,f.tan),0);
  assert(V.dot(V.cross(f.right,f.up),f.tan)>.99999);
}

test('parallel transport stays inverted through a vertical loop and joins the closed seam',()=>{
  const r=K.anim.route(circle(),{speed:3,bank:{gain:2,limit:.2}});
  for(let d=-r.length;d<r.length*2;d+=.047)axes(r.frame(d));
  assert(r.frame(r.length*.5).up[1]<-.98);
  assert(V.dot(r.frame(-1e-5).up,r.frame(1e-5).up)>.99999);
  const knot=K.anim.path(Array.from({length:120},(_,i)=>{const t=i*Math.PI/60;return [5*Math.cos(t),2*Math.sin(t*3),4*Math.sin(t)];}),{closed:true});
  const twisted=K.anim.route(knot,{up:[0,0,1]});
  assert(V.dot(twisted.frame(-1e-5).up,twisted.frame(1e-5).up)>.99999);
});

test('timing inverts travelled distance and respects stops, caps and acceleration on both sides of a seam',()=>{
  const p=K.anim.path([[0,0,0],[0,0,12],[10,0,12],[10,0,0]],{closed:true,curve:0});
  const r=K.anim.route(p,{speed:6,step:.17,acceleration:2,sections:[{from:3,to:8,speed:1.5}],stops:[{at:0,duration:1.3},{at:20,duration:.7}]});
  near(r.distanceAt(.9),0);near(r.speedAt(.9),0);
  const hit=r.timeAtDistance(20);near(r.distanceAt(hit+.4),20);near(r.speedAt(hit+.4),0);
  for(let d=.1;d<r.length;d+=.14){
    const t=r.timeAtDistance(d);near(r.distanceAt(t),d,1e-6);
    if(d>3&&d<8)assert(r.speedAt(t)<=1.50001);
  }
  let previous=r.state(0);
  for(let t=.007;t<r.period*2;t+=.007){
    const state=r.state(t);assert(Math.abs(state.speed-previous.speed)/.007<=2.00001);
    assert(state.travel+1e-6>=previous.travel);previous=state;
  }
  assert(r.state(-.1).travel<0);
});

test('stationary starts, short spans, finite endpoints and reverse shuttles are sampled without a warmup',()=>{
  const r=K.anim.route(line(5),{speed:2,acceleration:2,stops:[{at:0,duration:1},{at:5,duration:.7}],mode:'pingpong'});
  near(r.state(.8).distance,0);near(r.state(r.duration-.2).distance,5);
  near(r.period,2*r.duration-1-.7);
  assert(r.state(r.duration+.2).distance<5);
  const reverse=r.vehicle(r.duration+1.4);assert(reverse.direction===-1&&reverse.tan[2]<-.99);axes(reverse);
  const open=K.anim.route(line(),{speed:2});
  assert(open.state(100).finished);near(open.state(100).speed,0);near(open.distanceAt(100),10);
  assert.equal(open.vehicle(0,{offset:2}).active,false);
  const short=K.anim.route(line(.02),{step:1,speed:2,acceleration:3,stops:[{at:0,duration:.2},{at:.02,duration:.3}]});
  assert(Number.isFinite(short.duration));near(short.distanceAt(100),.02);
  const slow=K.anim.route(line(),{acceleration:1e-9,stops:[{at:0,duration:0},{at:10,duration:0}]});
  const midpoint=slow.timeAtDistance(5);
  assert(Number.isFinite(midpoint));near(slow.distanceAt(midpoint),5);

});

test('vehicles keep arc-length spacing through loops and wheelbase frames remain orthonormal',()=>{
  const r=K.anim.route(circle(),{speed:5});
  const cars=r.vehicles(2,{count:5,spacing:.94,wheelbase:.47});
  for(let i=0;i<cars.length;i++){
    axes(cars[i]);assert(cars[i].active);near(V.len(cars[i].velocity),5);
    if(i)near((cars[i-1].distance-cars[i].distance+r.length)%r.length,.94);
  }
  const corner=K.anim.route(K.anim.path([[0,0,0],[0,0,5],[5,0,5]],{curve:0}),{speed:2});
  const straddling=corner.vehicle(2.4,{wheelbase:2});
  assert(straddling.tan[0]>.4);
  near(straddling.velocity[0],0);near(straddling.velocity[2],2);
  const plain=r.frame(2);const rolled=K.anim.route(circle(),{bank:Math.PI/2}).frame(2);
  assert(Math.abs(V.dot(plain.up,rolled.up))<.00001);
});

test('events choose reachable sites ahead without changing the follower, including trailing cars and skipped laps',()=>{
  const r=K.anim.route(circle(),{speed:3,stops:[{at:0,duration:.5}]}),events=[{id:'gate',at:3},{id:'fault',at:12}];
  const before=r.vehicle(1),next=r.nextEvent(1,events,{lead:.3});
  assert(next.time>1.3);assert.deepEqual(r.vehicle(1),before);
  near(r.distanceAt(next.time),next.at);
  const trailing=r.nextEvent(next.time-.01,[{id:'tail',at:next.at}],{offset:1.1});
  near(r.vehicle(trailing.time,{offset:1.1}).distance,next.at);
  const all=r.eventsBetween(-.01,r.period*3+.01,events);
  assert.equal(all.length,6);
  const batches=[...r.eventsBetween(-.01,2,events),...r.eventsBetween(2,r.period*3+.01,events)];
  assert.deepEqual(batches.map(e=>e.time),all.map(e=>e.time));
  assert.deepEqual(r.eventsBetween(next.time,next.time,events),[]);
  assert.deepEqual(r.eventsBetween(10,1,events),[]);
  assert.equal(K.anim.route(line(),{speed:2}).nextEvent(6,[{at:9}]),null);
});

test('shuttle events include arrivals at each terminus and reverse crossings of intermediate stops',()=>{
  const r=K.anim.route(line(),{speed:2,mode:'pingpong',stops:[{at:0,duration:1},{at:10,duration:2},{at:5,duration:.4}]});
  const events=[{id:'a',at:0},{id:'b',at:10},{id:'c',at:5}],out=r.eventsBetween(0,r.period,events);
  assert.equal(out.filter(e=>e.id==='a').length,1);assert.equal(out.filter(e=>e.id==='b').length,1);
  assert.deepEqual(out.filter(e=>e.id==='c').map(e=>e.direction),[1,-1]);
  for(const e of out)near(r.distanceAt(e.time),e.at,1e-6);
});

test('invalid routes, speed samplers and unbounded event requests fail before changing a caller',()=>{
  assert.throws(()=>K.anim.route(line(),{speed:0}),/speed/);
  assert.throws(()=>K.anim.route(line(),{speed:()=>NaN}),/positive/);
  assert.throws(()=>K.anim.route(line(),{step:.000001}),/budget/);
  assert.throws(()=>K.anim.route(line(),{sections:[{from:5,to:4,speed:2}]}),/sections/);
  assert.throws(()=>K.anim.route(line(),{stops:[{at:3,duration:1},{at:3,duration:2}]}),/distinct/);
  const r=K.anim.route(circle());
  assert.throws(()=>r.eventsBetween(0,r.period*100,[{at:1}],{maxEvents:2}),/budget/);
  assert.throws(()=>r.eventsBetween(0,10,[{id:'x',at:1},{id:'x',at:2}]),/distinct/);
  assert.throws(()=>r.nextEvent(0,[],{lead:-1}),/lead/);
  assert.throws(()=>r.frame(NaN),/finite/);
  assert.throws(()=>r.vehicles(1,{count:1e6}),/count/);
});

const test=require('node:test'), assert=require('node:assert/strict');
const {KIT}=require('..').load(),{routeStations}=KIT.procedural||KIT.authoring;
const part=(key,length)=>({key,length});
const near=(a,b)=>assert(Math.abs(a-b)<1e-9,`${a} != ${b}`);

test('a station keeps its local section position after a split and downstream length changes',()=>{
  const before=[part('first',4),part('changed',8),part('last',4)];
  const after=[part('first',4),part('left',3),part('right',9),part('last',8)];
  const m=routeStations.remap(before,after,[
    {from:'changed',to:'left',fromRange:[0,.25]},
    {from:'changed',to:'right',fromRange:[.25,1]}
  ]);
  near(m(2/16),2/24);
  near(m(5/16),5.5/24);
  near(m(6/16),7/24);
  near(m(9/16),11.5/24);
  near(m(14/16),20/24);
  assert.equal(m(1),1);
});

test('two source sections can map to one join and removed sections give callers a fallback',()=>{
  const original=[part('left',3),part('right',9),part('removed',8)];
  const joined=[part('join',6)];
  const m=routeStations.remap(original,joined,[
    {from:'left',to:'join',toRange:[0,.25]},
    {from:'right',to:'join',toRange:[.25,1]}
  ]);
  near(m(1.5/20),.125);
  near(m(3/20),.25);
  near(m(7.5/20),.625);
  assert.equal(m(.8),null);
  assert.equal(routeStations.remap([],joined)(.4),null);
  assert.throws(()=>m(2),/station/i);
  assert.throws(()=>routeStations.remap([part('bad',0)],joined),/positive/);
  assert.throws(()=>routeStations.remap(original,joined,[
    {from:'left',to:'join',fromRange:[0,.5]},
    {from:'left',to:'join',fromRange:[.4,1]}
  ]),/overlap/);
});

test('destination intervals can run in reverse without changing source order',()=>{
  const before=[part('south',3),part('north',2)];
  const after=[part('northward',4),part('southward',9)];
  const map=routeStations.remap(before,after,[
    {from:'south',to:'southward',toRange:[1,0]},
    {from:'north',to:'northward',toRange:[1,0]}
  ]);
  near(map(0),1);
  near(map(.3),8.5/13);
  near(map(.6),4/13);
  near(map(.8),2/13);
  near(map(1),0);
  assert.throws(()=>routeStations.remap(before,after,[{from:'south',to:'southward',toRange:[.5,.5]}]),/mapping/);
});

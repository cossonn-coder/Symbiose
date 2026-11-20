const test = require('node:test');
const assert = require('node:assert/strict');
const { procedural:P } = require('..').load().KIT;

const square=[[-.2,-.1],[.2,-.1],[.2,.1],[-.2,.1]];

test('fitted profiles leave physical joints and expose closed pieces with stable keys',()=>{
  const path=[[0,0,0],[0,0,.3],[0,0,2]], profiles=[square.map(p=>p.slice())];
  const run=P.fittedProfileRun({path,profiles,pitch:1,gap:.2});
  path[2][2]=4; profiles[0][0][0]=-4;
  const pieces=run.pieces({owner:'cover',key:'cap'});
  assert.equal(run.count,2);
  assert.deepEqual(pieces.map(p=>p.key),['cap/0/0/0','cap/1/0/0']);
  assert(pieces[0].distance([0,0,.5])<0);
  assert(pieces[1].distance([0,0,1.5])<0);
  assert(pieces.every(p=>p.distance([0,0,1])>.09));
  assert(pieces.every(p=>p.mesh.positions.every(Number.isFinite)));
});

test('a sloping turn can carry independent profiles within a shared length budget',()=>{
  const path=[[0,0,0],[0,.5,2],[-2,1,2]], profiles=[square,square.map(([x,y])=>[x+.4,y])];
  const run=P.fittedProfileRun({path,profiles,pitch:1,gap:.1});
  assert(run.pieces().length>=run.count*2);
  assert.throws(()=>P.fittedProfileRun({path,profiles,pitch:.001,budget:4}),/budget/);
  assert.throws(()=>P.fittedProfileRun({path:[[0,0,0],[0,1,0]],profiles,pitch:1}),/parallel/);
});

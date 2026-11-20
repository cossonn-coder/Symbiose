const test = require('node:test');
const assert = require('node:assert/strict');
const { supportGraph } = require('..').load().KIT.procedural.construct;

test('only a connection to a live bearing supports a group, including a cycle', () => {
  const parts = [
    { id:'bridge', links:['gallery','removed'] },
    { id:'tower', grounded:true },
    { id:'landing', links:['tower','walk'] },
    { id:'gallery', links:['bridge'] },
    { id:'walk', links:['landing'] }
  ];
  const result = supportGraph(parts);
  assert.deepEqual(result.map(p=>p.state),['floating','supported','supported','floating','supported']);
  assert.deepEqual(result[0].links,['gallery','removed']);
  assert(Object.isFrozen(result[0].links));
  assert.equal(parts[2].grounded,undefined);
  assert(supportGraph(parts.filter(p=>p.id!=='tower')).every(p=>p.state==='floating'));
  assert.throws(()=>supportGraph([parts[0],parts[0]]),/unique/);
});

test('a long reversed contact chain resolves without recursion or an order assumption', () => {
  const parts = Array.from({length:10000},(_,i)=>({id:String(i),links:[String(i+1)],grounded:i===9999}));
  const direct = supportGraph(parts), reversed = supportGraph(parts.slice().reverse()).slice().reverse();
  assert(direct.every(p=>p.grounded));
  assert.deepEqual(direct,reversed);
});

const test = require('node:test');
const assert = require('node:assert/strict');
const {sampleVisibility, splatOrder} = require('..').load().KIT.procedural;

test('visibility words address distinct samples through word and texture row boundaries', () => {
  const bank = sampleVisibility.create(1200);
  const hidden = [0, 31, 32, 510, 511, 512, 1024, 1199];
  bank.set(Uint32Array.from(hidden));
  assert.equal(bank.words.byteLength, 192);
  assert.deepEqual([bank.changedRows.start, bank.changedRows.end], [0, 3]);
  for (let i = 0; i < 1200; i++) assert.equal(bank.hidden(i), hidden.includes(i));
  assert.throws(() => bank.set(Uint32Array.of(32, 31)), /ordered/);
  assert(bank.hidden(512));
  bank.set(Uint32Array.from(hidden.slice(0, -1)));
  assert.deepEqual([bank.changedRows.start, bank.changedRows.end], [2, 3]);
  bank.set(Uint32Array.from(hidden.slice(0, -1)));
  assert.equal(bank.changedRows, null);
  bank.set(new Uint32Array());
  assert(bank.words.every(n => n === 0));
});

test('retained depth buckets preserve full-sort ties, behind samples and moving inserts', () => {
  const values = [-8, -5, -3, -5, -.22, .1, -8, -3.00001, -7];
  const retained = [0, 2, 4, 6, 8], tail = [1, 3, 5, 7], behind = i => i === 5 || i === 8;
  const depths = i => values[i];
  const bank = splatOrder.compile(retained, depths, behind);
  assert.throws(() => splatOrder.compile([2, 1], depths, behind), /increasing/);
  const combined = new Int32Array(values.length),keys=new Uint16Array(values.length);
  assert.equal(splatOrder.merge(bank, Int32Array.from(tail), depths, behind, combined, keys), false,
    'a moving sample can extend the full depth range');
  values[5] = -.5;
  assert(splatOrder.merge(bank, Int32Array.from(tail), depths, behind, combined, keys));
  assert.deepEqual(combined, splatOrder.compile(values.map((_, i) => i), depths, behind).order);
});

test('large retained merges preserve ties across both depth bytes and changing tail sizes', () => {
  const ids=Array.from({length:5600},(_,i)=>i),depths=i=>i===0?-32:i===1?32:((i*1079)%64000)/1024-31,
    behind=i=>i%13===0,order=splatOrder.compile(ids,depths,behind).order,
    combined=new Int32Array(ids.length),keys=new Uint16Array(ids.length);
  const retained=ids.filter(i=>i<2||i%3===0),active=ids.filter(i=>i>=2&&i%3!==0);
  const bank=splatOrder.compile(retained,depths,behind);
  assert(splatOrder.merge(bank,Int32Array.from(active),depths,behind,combined,keys));
  assert.deepEqual(combined,order);
  assert(splatOrder.merge(bank,Int32Array.from(active.reverse()),depths,behind,combined,keys));
  assert.deepEqual(combined,order);
  const shorter=active.reverse().slice(0,950);
  assert(splatOrder.merge(bank,Int32Array.from(shorter),depths,behind,combined,keys));
  const reduced=splatOrder.compile(retained.concat(shorter).sort((a,b)=>a-b),depths,behind);
  assert.deepEqual(combined.subarray(0,reduced.order.length),reduced.order);
});

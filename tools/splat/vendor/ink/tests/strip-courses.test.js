const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const fit = KIT.stripCourses;
const section = (s, lower, upper) => ({ s, lower, upper });
const close = (a, b) => assert(Math.abs(a - b) < 1e-7);

test('full-height stock joins each station without introducing a horizontal joint',()=>{
  const sections=[section(0,-.4,1.4),section(.62,.36,1.9),section(2,.08,2.2)];
  const {pieces,unit}=fit({sections,unit:[.82,null],joint:.08,datum:7});
  assert.deepEqual(unit,[.82,null]);
  assert.equal(pieces.length,4);
  assert(pieces.every(p=>p.row===0&&p.polygon.length===4));
  const joined=pieces.filter(p=>p.id==='0/0');
  assert.equal(joined.length,2);
  for(const piece of joined)assert.deepEqual(piece.polygon.filter(([s])=>s===.62).map(([,y])=>y),[.36,1.9]);
  close(Math.min(...pieces[0].polygon.map(([s])=>s)),.04);
  close(Math.max(...joined[1].polygon.map(([s])=>s)),.78);
});

test('full-height stock preserves closed seam identity and handles pinched bands',()=>{
  const sections=[section(0,0,1),section(1.2,.3,.3),section(2.85,0,1)];
  const {pieces,unit,columnPeriod}=fit({sections,unit:[1,null],closed:true,offset:.21});
  close(unit[0],.95);
  assert.equal(columnPeriod,3);
  const wraps=pieces.filter(p=>p.id==='0/0');
  assert(wraps.some(p=>p.polygon.some(([s])=>s===0)));
  assert(wraps.some(p=>p.polygon.some(([s])=>s===2.85)));
  assert.deepEqual(fit({sections:[section(0,1,1),section(1,1,1)],unit:[.3,null]}).pieces,[]);
  assert.throws(()=>fit({sections,unit:[.2,null],joint:.2}),/joint/);
});

test('stock clips to both edges of a sloped strip and continues across sections', () => {
  const sections = [section(0, .33, 1.6), section(.62, .64, 1.38), section(2, .33, 1.6)];
  const { pieces } = fit({ sections, unit: [1, .4], joint: .04 });
  assert(pieces.length > 8);
  for (const { segment, polygon } of pieces) {
    const a = sections[segment], b = sections[segment + 1];
    for (const [s, y] of polygon) {
      const t = (s - a.s) / (b.s - a.s);
      assert(t >= -1e-8 && t <= 1 + 1e-8);
      assert(y >= a.lower + t * (b.lower - a.lower) - 1e-8);
      assert(y <= a.upper + t * (b.upper - a.upper) + 1e-8);
    }
  }
  const parts = pieces.filter(p => p.id === '2/0');
  assert.equal(parts.length, 2);
  for (const piece of parts) assert(piece.polygon.some(([s]) => Math.abs(s - .62) < 1e-7));
  for (const piece of pieces.filter(p => p.row === 2))
    for (const [, y] of piece.polygon) assert(y >= .82 - 1e-8 && y <= 1.18 + 1e-8);
});

test('a closed strip fits whole pitches, with one staggered cell across its seam', () => {
  const { unit, pieces } = fit({ sections: [section(0, 0, 2), section(2.8, 0, 2)],
    unit: [1, 1], closed: true, joint: .1 });
  close(unit[0], 2.8 / 3);
  const joined = pieces.filter(p => p.id === '1/2');
  assert.equal(joined.length, 2);
  assert(joined[0].polygon.some(([s]) => s === 0));
  assert(joined[1].polygon.some(([s]) => s === 2.8));
  assert.equal(new Set(pieces.filter(p => p.row === 1).map(p => p.id)).size, 3);
});

test('datum stays fixed across edits to a strip floor, including negative rows', () => {
  const make = lower => fit({ sections: [section(0, lower, 3), section(2, lower, 3)],
    unit: [1, .5], datum: .18 });
  const low = make(-.35), high = make(.35);
  assert(low.pieces.some(p => p.row === -1 && p.column === 0));
  assert.deepEqual(low.pieces.filter(p => p.row >= 1), high.pieces.filter(p => p.row >= 1));
  assert.throws(() => fit({ sections: [section(0, -1e9, 3), section(2, 0, 3)],
    unit: [1, .5], budget: 20 }), RangeError);
  assert.throws(() => fit({ sections: [section(0, 0, 2), section(1, 0, 2), section(1, 0, 1)],
    unit: [1, 1] }), /ordered sections/);
});

test('stock offset retains grid joints and logical identities on a cut fragment', () => {
  const options = { unit: [1, .5], joint: .06, columnPeriod: 3 };
  const original = fit({ ...options, sections: [section(0, 0, 2), section(7, 0, 2)] });
  const shifted = fit({ ...options, offset: 3.36, sections: [section(0, 0, 2), section(3.64, 0, 2)] });
  const compare = entry => [entry.id, entry.stockColumn, ...entry.polygon.map(([x]) => x.toFixed(7))];
  const comparable = shifted.pieces.filter(p => p.polygon.every(([x]) => x > 0))
    .map(p => compare({ ...p, polygon: p.polygon.map(([x, y]) => [x + 3.36, y]) }));
  assert.deepEqual(comparable, original.pieces.filter(p => p.polygon.every(([x]) => x > 3.36))
    .map(compare));
  assert.equal(fit({ sections: [section(0, 1, 1), section(2, 1, 1)], unit: [1, .5] }).pieces.length, 0);
});

test('nominal stock addressing follows sloped bands, stagger, and the wrapped datum',()=>{
  const sections=[section(0,-.4,1.4),section(.62,.36,1.9),section(2.3,.08,2.2)];
  for(const config of [{unit:[.4,null]},{unit:[.48,.3],closed:true,offset:.17,datum:.11}]){
    const layout=fit({sections,joint:.04,...config});
    for(const {polygon,id} of layout.pieces){
      const [s,y]=polygon.reduce(([u,v],[x,z])=>[u+x/polygon.length,v+z/polygon.length],[0,0]);
      assert.equal(layout.keyAt(s,y),id);
    }
    const band=layout.bandAt(.31);
    close(band.lower,-.02);close(band.upper,1.65);
    assert.equal(layout.keyAt(.31,band.upper),null);
    assert.equal(layout.keyAt(-.1,.7),null);
  }
  const layout=fit({sections:[section(0,0,1),section(2,0,1)],unit:[.5,null],joint:.06});
  assert.equal(layout.keyAt(.5,.6),'0/1');
  assert.equal(layout.keyAt(2,.6),'0/3');
});

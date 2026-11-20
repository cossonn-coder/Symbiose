const test = require('node:test');
const assert = require('node:assert/strict');
const P = require('..').load().KIT.procedural;

test('surface masks retain brush stations while measuring width in a resized chart', () => {
  const strokes = [{ points: [[.35, .4], [.65, .4]], width: 1, softness: .1 }];
  const wide = P.surfaceMasks.compile(strokes, { size: [8, 4] });
  const tall = P.surfaceMasks.compile(strokes, { size: [8, 10] });
  for (const mask of [wide, tall]) assert.equal(mask.weight(.51, .4), 1);
  assert.equal(wide.weight(.51, .525), .5);
  assert.equal(tall.weight(.51, .525), 0);
  assert.equal(wide.weight(-.02, .4, .3), .3);
  assert.equal(wide.weight(.55, 1.1, .3), .3);
  const remove = { operation: 'erase', width: .4, points: [[.51, .4]] };
  const erased = P.surfaceMasks.compile([...strokes, remove], { size: [8, 4] });
  assert.equal(erased.weight(.51, .4, .3), 0);
  assert.equal(erased.weight(.62, .4, .3), 1);
  assert.equal(P.surfaceMasks.compile([remove, ...strokes], { size: [8, 4] }).weight(.51, .4), 1);
});

test('periodic surface strokes cross the shortest seam and can make multiple turns', () => {
  const brush = { points: [[.95, .5], [.05, .5]], width: .42, softness: .04 };
  const chart = { size: [10, 4], periodic: true };
  const round = P.surfaceMasks.compile([brush], chart);
  assert.equal(round.weight(0, .5), 1);
  assert.equal(round.weight(1, .5), 1);
  assert.equal(round.weight(-1.001, .5), 1);
  assert.equal(round.weight(.5, .5), 0);
  assert.equal(P.surfaceMasks.compile([brush], { ...chart, periodic: false }).weight(.5, .5), 1);
  const winding = P.surfaceMasks.compile([{ ...brush, points: [
    [.8, .1], [.03, .2], [.29, .31], [.55, .43], [.8, .57], [.02, .69], [.24, .8]
  ] }], chart);
  assert.equal(winding.weight(0, .19), 1);
  assert.equal(winding.weight(0, .68), 1);
  assert.equal(winding.weight(0, .43), 0);
  assert.equal(winding.weight(.8, .57), 1);
  const erase = { ...brush, operation: 'erase', points: [[0, .5]] };
  assert.equal(P.surfaceMasks.compile([brush, erase], chart).weight(.99, .5, .7), 0);
  assert.equal(P.surfaceMasks.compile([brush, erase], chart).weight(.04, .5, .7), 1);
});

test('surface masks reject invalid or unbounded charts, strokes and queries', () => {
  const options = { size: [1, 1] }, stroke = { points: [[.5, .5]], width: .1 };
  for (const change of [{ size: [0, 1] }, { size: [1, Infinity] }, { periodic: 2 }])
    assert.throws(() => P.surfaceMasks.compile([stroke], { ...options, ...change }));
  for (const change of [{ points: [[1.1, .5]] }, { width: 0 }, { softness: -1 }, { operation: 'blur' }])
    assert.throws(() => P.surfaceMasks.compile([{ ...stroke, ...change }], options));
  assert.throws(() => P.surfaceMasks.compile([{ ...stroke, points: Array(8193).fill([.5, .5]) }], options), /budget/);
  assert.throws(() => P.surfaceMasks.compile([stroke], options).weight(Infinity, 0));
});

test('dirty bounds enclose all changed samples on both sides of a periodic seam',()=>{
  const options={size:[10,4],periodic:true};
  const start={points:[[.48,.15]],width:1}, seam={points:[[.96,.5],[.04,.55]],width:.55,softness:.12};
  const restore={points:[[.01,.54]],operation:'erase',width:.3};
  for(const [a,b] of [[[start],[start,seam]],[[start,seam],[start,seam,restore]],[[start,seam,restore],[start]]]){
    const bounds=P.surfaceMasks.dirtyBounds(a,b,options);
    assert(bounds.length>0);
    assert(bounds.every(box=>box.min[0]>=0&&box.max[0]<=1&&box.min[1]>=0&&box.max[1]<=1));
    const from=P.surfaceMasks.compile(a,options),to=P.surfaceMasks.compile(b,options);
    for(let y=0;y<=40;y++)for(let x=0;x<=100;x++){
      const u=x/100,v=y/40;
      if(from.weight(u,v)===to.weight(u,v))continue;
      assert(bounds.some(box=>u>=box.min[0]&&u<=box.max[0]&&v>=box.min[1]&&v<=box.max[1]));
    }
    assert(bounds.every(box=>box.max[0]<.25||box.min[0]>.75),'unrelated central samples stay clean');
  }
  assert.deepEqual(P.surfaceMasks.dirtyBounds([start],[{...start}],options),[]);
});

test('loop brushes cross unequal chart edges, retain point anchors and compose local layers in order',()=>{
  const charts=[{key:'a',length:4},{key:'b',length:1},{key:'c',length:3}],options={charts,height:2};
  const point=(chart,u,v)=>({chart,uv:[u,v]});
  const dab={points:[point('a',.98,.45)],width:.5,softness:.1};
  const stroke={...dab,points:[point('a',.80,.35),point('b',.50,.55)]};
  const restored={chart:'b',points:[[.08,.45]],width:.34,operation:'erase'};
  const legacy={chart:'a',points:[[0,.79]],width:.8};
  const tint=P.surfaceMasks.compileLoop([dab],options);
  assert.equal(tint.weight('b',.05,.45),1);
  assert(tint.weight('b',.13,.45)>0&&tint.weight('b',.13,.45)<1);
  assert.equal(tint.weight('b',.31,.45),0);
  const before=[legacy,stroke,restored];
  const mask=P.surfaceMasks.compileLoop(before,options);
  assert.equal(mask.weight('b',.08,.45),0);
  assert.equal(mask.weight('a',.99,.45),1);
  assert.equal(mask.weight('c',.999,.79),0,'older single-chart paint remains clipped');
  assert.equal(P.surfaceMasks.compileLoop([restored,stroke],options).weight('b',.08,.45),1);
  const after=[legacy,stroke,{...dab,points:[point('c',.97,.61),point('a',.04,.67)]},restored],
    dirty=P.surfaceMasks.loopDirtyBounds(before,after,options),
    next=P.surfaceMasks.compileLoop(after,options);
  assert.equal(next.weight('a',0,.64),1);
  assert.equal(next.weight('c',1,.64),1);
  for(const {key:chart} of charts)for(let y=0;y<=40;y++)for(let x=0;x<=60;x++){
    const u=x/60,v=y/40;
    if(mask.weight(chart,u,v)===next.weight(chart,u,v))continue;
    assert(dirty.some(box=>box.chart===chart&&u>=box.min[0]&&u<=box.max[0]&&v>=box.min[1]&&v<=box.max[1]));
  }
  assert.deepEqual(P.surfaceMasks.loopDirtyBounds(after,structuredClone(after),options),[]);
  const resized=P.surfaceMasks.compileLoop([stroke],{height:6,charts:charts.map(span=>({...span,
    length:span.key==='a'?11:span.length}))});
  assert.equal(resized.weight('a',.80,.35),1);
  assert.equal(resized.weight('b',.50,.55),1);
  assert.equal(resized.weight('b',.50,.79),0);
  assert.throws(()=>P.surfaceMasks.compileLoop([{...dab,points:[point('missing',.5,.45)]}],options),/chart/);
});

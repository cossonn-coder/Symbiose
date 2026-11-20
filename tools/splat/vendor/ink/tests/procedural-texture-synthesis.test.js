const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: K } = require('..').load();
const M = K.procedural.materials;
const grid = (width,height,fn) => ({ width,height,channels:1,
  data: Float64Array.from({length:width*height},(_,i) => fn(i%width,Math.floor(i/width))) });

test('quilting preserves swatch values, fills its domain and returns reproducible patch seams', () => {
  const swatch = grid(18,17,(x,y) => (x + 2*y) % 5),
    options = { width:31,height:26,patch:7,overlap:3,seed:8,candidates:90 },
    a = M.quilt(swatch,options), b = M.quilt(swatch,options);
  assert.equal(a.status,'ok');
  assert.deepEqual(a.data,b.data);
  assert.deepEqual(a.patches,b.patches);
  assert(a.coverage.every(v=>v===1));
  assert(a.data.every(v=>Number.isInteger(v)&&v>=0&&v<5));
  const cross = a.data.reduce((count,v,i) => count + Number(i%a.width > 0 && (v+5-a.data[i-1])%5 === 1),0);
  assert(cross > a.data.length*0.77);
  assert.equal(M.quilt(swatch,{...options,maxWork:1}).status,'budget');
});

test('bidirectional propagation recovers a displaced patch match and never raises an accepted score', () => {
  const samples = grid(16,14,(x,y) => K.hash(x,y,18)),
    target = grid(9,8,(x,y) => samples.data[(y+3)*16+x+4]),
    seed = 71, before = M.patchMatch(samples,target,{radius:2,iterations:0,seed}),
    after = M.patchMatch(samples,target,{radius:2,iterations:7,seed});
  assert(after.costs.every((c,i)=>c<=before.costs[i]));
  assert(after.costs.filter(v=>v<1e-12).length > 62);
  assert.equal(after.nearest[4*9+3],7*16+7);
  assert.equal(M.patchMatch(samples,target,{radius:2,maxWork:2}).status,'budget');
});

test('mask-preserving synthesis continues a repeated painted swatch through a gap', () => {
  const pattern = (x,y) => Number((x+y)%3===0),
    source = grid(16,16,pattern), pristine = grid(15,17,pattern),
    mask = grid(15,17,(x,y) => Number(x>3&&x<12&&y>3&&y<14)).data,
    target = { ...pristine, data: pristine.data.map((p,i) => mask[i] ? 0.125 : p) },
    options = { mask,seed:22,cycles:3,guide:0.12,radius:2,iterations:3 },
    filled = M.synthesize(source,target,options);
  assert.equal(filled.status,'ok');
  assert.deepEqual(filled.data,pristine.data);
  assert.deepEqual(filled.data,M.synthesize(source,target,options).data);
  assert(target.data.some((v,i)=>mask[i]&&v===0.125));
  assert.equal(M.synthesize(source,target,{...options,maxWork:1}).work.cycles,0);
});

test('void-and-cluster ranks are complete, periodic and dispersed at low thresholds', () => {
  const primary = M.blueNoise({width:28,height:19,seed:25,sigma:1.4}),
    repeat = M.blueNoise({width:28,height:19,seed:25,sigma:1.4});
  assert.deepEqual(primary.ranks,repeat.ranks);
  const n = 28*19;
  assert.equal(new Set(primary.ranks).size,n);
  assert(primary.ranks.every(v=>v>=0&&v<n));
  assert(primary.converged);
  assert.equal(primary.sample(-1,2),primary.sample(27,2));
  assert.equal(primary.sample(4,3),primary.sample(32,-16));
  const lights = primary.ranks.reduce((sum,rank,i) => {
    if (rank >= Math.floor(n*0.12)) return sum;
    return sum + Number(primary.sample(i%28+1,Math.floor(i/28)) < 0.12) +
      Number(primary.sample(i%28,Math.floor(i/28)+1) < 0.12);
  },0);
  assert(lights < 5);
  assert.throws(()=>M.blueNoise({width:20,maxWork:200}),/budget/);
});

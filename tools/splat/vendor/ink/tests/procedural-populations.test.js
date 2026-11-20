const test = require('node:test'),
  assert = require('node:assert/strict'),
  P = require('..').load().KIT.procedural.populations;
const box = r => ({ min: [-r, 0, -r], max: [r, 1, r] });
test('seeded mixtures respect weights and keep winners when unrelated choices are removed', () => {
  const entries=[{key:'fern',weight:1},{key:'stone',weight:2},{key:'grass',weight:5}];
  const mix=P.mix(entries,{seed:29}),shuffled=P.mix([...entries].reverse(),{seed:29}),
    reduced=P.mix(entries.slice(1),{seed:29}),counts={fern:0,stone:0,grass:0};
  for(let seed=0;seed<4096;seed++){
    const point=[2,-1],kind=mix(point,seed);
    counts[kind]++;
    assert.equal(kind,shuffled(point,seed));
    if(kind!=='fern')assert.equal(kind,reduced(point,seed));
  }
  assert(Math.abs(counts.fern/4096-.125)<.025);
  assert(Math.abs(counts.stone/4096-.25)<.035);
  assert(Math.abs(counts.grass/4096-.625)<.04);
  const local=P.mix(entries,{seed:29,patchSize:2,coherence:1}),
    a=local([.2,.3],1);
  assert.equal(local([.2,.3],3),a);
  assert.equal(local([.201,.299],178),a);
  assert(new Set(Array.from({length:32},(_,i)=>local([2*i,0],1))).size>1);
  assert.throws(()=>P.mix([{key:'empty',weight:0}]),/positive weight/);
  assert.throws(()=>P.mix(entries,{coherence:.5}),/patch size/);
});
test('ranked world candidates retain identity, pose and seed through density and domain extension', () => {
  const a = P.layout([box(1)], () => ({ density: 0.25 })),
    b = P.layout([box(2)], () => ({ density: 0.7 })),
    byKey = new Map(b.instances.map(p => [p.key, p]));
  assert(a.instances.length > 5);
  for (const p of a.instances) {
    const q = byKey.get(p.key);
    assert(q);
    assert.deepEqual([q.point, q.seed, q.yaw, q.scale], [p.point, p.seed, p.yaw, p.scale]);
  }
  assert.deepEqual(
    P.layout([box(1)], () => ({ density: 0.25 })),
    a
  );
});
test('work regions deduplicate, samples carry arbitrary consumer data, and caller data remains mutable', () => {
  const data = { density: 1, habitat: { name: 'rock' } };
  const a = P.layout([box(1)], () => data),
    b = P.layout([box(1), box(1)], () => data);
  assert.deepEqual(a, b);
  assert(!Object.isFrozen(data.habitat));
  data.habitat.name = 'changed';
  assert.equal(a.instances[0].sample.habitat.name, 'rock');
  assert(Object.isFrozen(a.instances[0].point));
});
test('masks remove candidates without rerolling survivors and reject bad inputs or unbounded work', () => {
  const a = P.layout([box(1)], () => ({ density: 1 })),
    b = P.layout([box(1)], (x, z) => (x < 0 ? null : { density: 1 }));
  assert.deepEqual(
    b.instances,
    a.instances.filter(p => p.point[0] >= 0)
  );
  for (const raw of [{ spacing: 0 }, { slots: 9 }, { jitter: 2 }, { maxCandidates: 0 }, { seed: NaN }])
    assert.throws(() => P.layout([box(1)], () => null, raw));
  assert.throws(() => P.layout([box(1)], () => ({ density: 2 })));
  assert.throws(() => P.layout([box(1)], () => ({ density: 1 }), { maxInstances: 1 }), /budget/);
  assert.throws(() => P.layout([box(30)], () => null, { maxCandidates: 10 }), /budget/);
});

test('minimum-distance placement is identical in full, reversed, and independently built work regions', () => {
  const setup = { spacing: 0.25, slots: 5, seed: 27, exclusion: { distance: 0.33, maxDistance: 0.65, species: { oak: { moss: 0.53 } } } },
    sample = (x, z, candidate) => ({
      density: 0.48 + 0.3 * Math.cos(x * 0.8 + z),
      species: candidate.seed % 2 ? 'oak' : 'moss',
      minDistance: z > 0.65 ? 0.65 : 0.33
    }),
    a = { min: [-3, 0, -2.2], max: [0.04, 1, 2.2] },
    b = { min: [0.04, 0, -2.2], max: [3, 1, 2.2] },
    full = { min: a.min, max: b.max },
    both = P.layout([full], sample, setup),
    reverse = P.layout([b, a], sample, setup),
    union = new Map([...P.layout([a], sample, setup).instances, ...P.layout([b], sample, setup).instances].map(p => [p.key, p]));
  assert(both.instances.length > 20);
  assert.deepEqual(both, reverse);
  assert.equal(union.size, both.instances.length);
  for (const [i, p] of both.instances.entries()) {
    assert.deepEqual(p, union.get(p.key));
    for (const q of both.instances.slice(i + 1)) {
      const gap = Math.max(p.sample.minDistance, q.sample.minDistance, p.sample.species === q.sample.species ? 0 : 0.53);
      assert(Math.hypot(p.point[0] - q.point[0], p.point[1] - q.point[1]) + 1e-10 >= gap);
    }
  }
});

test('eligible priorities preserve survivors when uniformly increasing density and account for a halo budget', () => {
  const setup = { spacing: 0.25, seed: 14, exclusion: { distance: 0.39 } },
    a = P.layout([box(2)], () => ({ density: 0.3 }), setup),
    b = P.layout([box(2)], () => ({ density: 0.85 }), setup),
    keys = new Set(b.instances.map(p => p.key));
  assert(a.instances.length > 10);
  assert(a.instances.every(p => keys.has(p.key)));
  assert(b.sampling.evaluated > b.sampling.candidates);
  assert.throws(() => P.layout([box(2)], () => ({ density: 1 }), { ...setup, exclusion: { distance: 0.4, maxComparisons: 1 } }), /comparison budget/);
  assert.throws(() => P.layout([box(2)], () => ({ density: 1, minDistance: 1 }), setup), /distance/);
});

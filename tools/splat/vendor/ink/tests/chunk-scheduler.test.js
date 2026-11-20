const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT, makeSculpt } = require('..').load();
const { chunks } = KIT.procedural;
const flush = () => new Promise(resolve => setImmediate(resolve));
const deferred = () => {
  let resolve;
  const promise = new Promise(yes => { resolve = yes; });
  return { promise, resolve };
};

test('grid windows use half-open boundaries and resolve signed 2D and 3D addresses on demand', () => {
  const planar = chunks.grid({ size: 0.1, dimensions: 2, origin: [-0.7, 0.22] });
  assert.deepEqual(planar.cover(planar.bounds([7, -3])), [[7, -3]]);
  assert.deepEqual(planar.index(planar.bounds([7, -3]).max), [8, -2]);
  const grid = chunks.grid({ size: 8 });
  assert.deepEqual(grid.cover({ min: [-8, -1, 0], max: [8, 0, 8] }), [[-1, -1, 0], [0, -1, 0]]);
  assert.throws(() => grid.cover({ min: [-24, 0, 0], max: [24, 16, 8] }, { limit: 8 }), /limit/);
  const at = [-500000009, 11, 940000000];
  assert.deepEqual(grid.address(grid.key('ridges:/islands', at)), { place: 'ridges:/islands', index: at });
  assert.notEqual(grid.key('earth', at), grid.key('moon', at));
  assert.deepEqual(grid.index(grid.bounds(at).min), at);
});

test('independent interests share one resident and arbitrate the byte budget deterministically', async () => {
  const built = [], released = [];
  const scheduler = chunks.createScheduler({
    budgetBytes: 15, concurrency: 2, describe: () => ({ revision: 1, bytes: 5 }),
    load({ key }) { built.push(key); return { key }; },
    release({ key }) { released.push(key); }
  });
  const player = scheduler.interest('player', { priority: 100 });
  const camera = scheduler.interest('camera', { priority: 20 });
  const doorway = scheduler.interest('doorway', { priority: 30 });
  player.update(['seam']);
  camera.update(['seam', 'scenery', { key: 'vista', priority: 2 }]);
  doorway.update(['seam', 'landing']);
  const [ground, view, preview] = await Promise.all([
    player.ready(), camera.ready({ keys: ['seam', 'vista'] }), doorway.ready()
  ]);
  assert.equal(ground[0], view[0]);
  assert.equal(ground[0], preview[0]);
  assert.deepEqual(built, ['seam', 'landing', 'vista']);
  assert.equal(scheduler.status('scenery').state, 'budget');
  assert.equal(scheduler.snapshot(), scheduler.snapshot());
  await assert.rejects(camera.ready(), /active byte budget/);
  doorway.update(['landing', 'beyond'], { priority: 100 });
  player.close();
  const [landing, beyond] = await doorway.ready();
  assert.equal(landing, preview[1]);
  assert.equal(beyond.value.key, 'beyond');
  assert.equal(built.filter(key => key === 'landing').length, 1);
  assert(scheduler.stats().bytes + scheduler.stats().reservedBytes <= scheduler.stats().budgetBytes);
  assert(released.includes('seam'));
  assert.equal(scheduler.get('vista'), view[1]);
  assert.equal(scheduler.get('landing'), landing);
  scheduler.dispose();
  assert.deepEqual(scheduler.snapshot().entries, []);
  assert.equal(scheduler.stats().bytes, 0);
  assert.deepEqual(released.sort(), built.sort());
});

test('superseded jobs keep their reservation and cannot publish late or replace a newer revision', async () => {
  const slow = deferred(), loads = [], releases = [];
  let revision = 1, staleSignal;
  const scheduler = chunks.createScheduler({
    budgetBytes: 12, concurrency: 2, describe: () => ({ revision, bytes: 6 }),
    load({ key, revision }, { signal }) {
      loads.push([key, revision]);
      if (key === 'a' && revision === 1) { staleSignal = signal; return slow.promise; }
      return { key, revision };
    },
    release(value) { releases.push(value); }
  });
  const interest = scheduler.interest('focus');
  interest.update(['a']);
  const old = interest.ready();
  await flush();
  assert.equal(scheduler.status('a').state, 'loading');
  interest.update([]);
  assert.equal(await old, null);
  assert.equal(staleSignal.aborted, true);
  revision = 2;
  scheduler.refresh();
  interest.update([{ key: 'a', priority: 10 }, 'b']);
  const current = interest.ready();
  await flush();
  assert.deepEqual(loads, [['a', 1], ['b', 2]]);
  assert.equal(scheduler.stats().reservedBytes, 6);
  assert.equal(scheduler.get('a'), null);
  slow.resolve({ key: 'a', revision: 1 });
  const entries = await current;
  assert.deepEqual(entries.map(entry => entry.value.revision), [2, 2]);
  assert.deepEqual(releases, [{ key: 'a', revision: 1 }]);
  const stable = scheduler.get('b');
  scheduler.refresh();
  await interest.ready();
  assert.equal(scheduler.get('b'), stable);
  scheduler.dispose();
});

test('measured residency frees capacity and a failed or oversize chunk can be retried', async () => {
  let oversized = true;
  const release = [];
  const scheduler = chunks.createScheduler({
    budgetBytes: 10,
    describe: key => key === 'void' ? null : { revision: 1, bytes: 6 },
    load: ({ key }) => ({ key, used: key === 'crest' && oversized ? 7 : 3 }),
    sizeOf: value => value.used, release: value => release.push(value.key)
  });
  const interest = scheduler.interest('camera');
  interest.update([{ key: 'crest', priority: 2 }, 'slope']);
  await assert.rejects(interest.ready({ keys: ['crest'] }), /reservation/);
  assert.equal((await interest.ready({ keys: ['slope'] }))[0].bytes, 3);
  assert.deepEqual(release, ['crest']);
  oversized = false;
  scheduler.refresh();
  assert.deepEqual((await interest.ready()).map(entry => entry.bytes), [3, 3]);
  assert.equal(scheduler.stats().bytes, 6);
  interest.update(['void']);
  await assert.rejects(interest.ready(), /unavailable/);
  scheduler.dispose();
});

test('waiting cancels independently and late completions after disposal are reclaimed', async () => {
  const held = deferred(), released = [];
  let signal;
  const scheduler = chunks.createScheduler({
    budgetBytes: 4, describe: () => ({ revision: 1, bytes: 4 }),
    load(entry, context) { signal = context.signal; return held.promise; },
    release(value) { released.push(value); }
  });
  const a = scheduler.interest('a'), b = scheduler.interest('b');
  a.update(['chunk']); b.update(['chunk']);
  const controller = new AbortController(), cancelled = a.ready({ signal: controller.signal }), pending = b.ready();
  await flush();
  controller.abort();
  assert.equal(await cancelled, null);
  a.close();
  await flush();
  assert.equal(signal.aborted, false);
  scheduler.dispose();
  assert.equal(await pending, null);
  assert.equal(signal.aborted, true);
  held.resolve('late');
  await flush();
  assert.deepEqual(released, ['late']);
  assert.equal(scheduler.stats().reservedBytes, 0);
  assert.equal(scheduler.snapshot().entries.length, 0);
});

test('a live portal hands off the same visible chunks and procedural movement swaps distant windows', async () => {
  const { grid, scheduler, session, dispose } = require('../examples/streamed-places')(KIT, makeSculpt);
  try {
    await session.enter('heath');
    const asset = await session.prepare('to-mesa'), landing = grid.key('mesa', [0, -1]);
    const entries = scheduler.snapshot().entries.filter(entry => entry.value.place === 'mesa');
    const start = scheduler.get(landing);
    assert.equal(entries.length, 9);
    assert(asset.world.count > 0);
    const result = await session.cross('to-mesa', { previous: [0.2, 1.42, 0.5], actor: { position: [0.2, 1.42, -0.5] } });
    assert.equal(result.place.asset, asset);
    await asset.ready();
    assert.equal(scheduler.get(landing), start);
    assert(entries.every(entry => scheduler.get(entry.key) === entry));
    assert.equal(scheduler.snapshot().entries.length, 25);
    const distant = [-24003, 1.5, 50228];
    asset.track(distant);
    await asset.ready();
    const far = scheduler.get(grid.key('mesa', grid.index([distant[0], distant[2]])));
    assert(far?.value.chunk.splats.count > 0);
    assert.equal(scheduler.get(landing), null);
    assert.equal(scheduler.snapshot().entries.length, 25);
    assert(scheduler.snapshot().entries.every(entry => entry.value.place === 'mesa'));
    asset.track(result.actor.position);
    await asset.ready();
    assert.deepEqual(scheduler.get(landing).value.chunk.splats.data, start.value.chunk.splats.data);
  } finally {
    dispose();
  }
});

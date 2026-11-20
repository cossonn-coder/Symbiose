const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const { procedural: P, authoring: A } = KIT;
const bounds = x => ({ min: [x, 0, 0], max: [x + 1, 1, 1] });
const entry = (key, revision, x, dependencies = []) => ({ key, revision, bounds: bounds(x), dependencies });
const deferred = () => {
  let resolve, reject;
  const promise = new Promise((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
};

test('chunk patches refine only changed data and retain unrelated payload identity', async () => {
  const build = ({ key }, { quality }) => ({ key, quality, data: Float32Array.of(1, 2, 3) });
  const chunks = P.chunks.create({ preview: build, refine: build });
  const a = entry('a', 1, 0),
    b = entry('b', 1, 8);
  const initial = await chunks.update([b, a]);
  assert.deepEqual(
    initial.replaced.map(c => c.key),
    ['a', 'b']
  );
  const far = chunks.get('b');
  const next = entry('a', 2, 2);
  const preview = await chunks.update([next, b], { quality: 'preview' });
  assert.deepEqual(
    preview.replaced.map(c => c.key),
    ['a']
  );
  assert.deepEqual(preview.regions, [bounds(0), bounds(2)]);
  assert.equal(chunks.get('b'), far);
  assert.equal(chunks.get('a').value.quality, 'preview');
  const final = await chunks.update([next, b]);
  assert.deepEqual(
    final.replaced.map(c => c.key),
    ['a']
  );
  assert.equal(chunks.get('a').value.quality, 'final');
  assert.equal(chunks.get('b'), far);
  const unchanged = await chunks.update([next, b], { quality: 'preview' });
  assert.deepEqual(unchanged.replaced, []);
  const removal = await chunks.update([b]);
  assert.deepEqual(removal.removed, ['a']);
  assert.deepEqual(removal.regions, [bounds(2)]);
});

test('dependency and region invalidation survive superseded requests and stale completions', async () => {
  const hold = deferred();
  let delayed = false,
    oldSignal,
    builds = 0;
  const chunks = P.chunks.create({
    preview: (entry, { signal }) => {
      if (delayed && entry.key === 'a') {
        oldSignal = signal;
        return hold.promise;
      }
      return { key: entry.key, build: ++builds };
    }
  });
  const items = [entry('a', 1, 0, ['field']), entry('b', 1, 8), entry('c', 1, 20)];
  await chunks.update(items);
  const saved = chunks.get('c');
  delayed = true;
  const stale = chunks.update(items, { changedIds: ['field'] });
  delayed = false;
  const latest = await chunks.update(items, { regions: [bounds(8)] });
  assert(oldSignal.aborted);
  assert.deepEqual(
    latest.replaced.map(c => c.key),
    ['a', 'b']
  );
  hold.resolve({ bad: true });
  assert.equal(await stale, null);
  assert(!chunks.get('a').value.bad);
  assert.equal(chunks.get('c'), saved);
});

test('failed or explicitly cancelled builders leave the current chunk set atomic', async () => {
  const hold = deferred();
  const chunks = P.chunks.create({
    preview: ({ key, revision }) => {
      if (revision === 3 && key === 'a') return hold.promise;
      if (revision === 2 && key === 'b') throw Error('Builder failed');
      return { revision };
    }
  });
  await chunks.update([entry('a', 1, 0), entry('b', 1, 2)]);
  const previous = chunks.entries();
  await assert.rejects(chunks.update([entry('a', 2, 0), entry('b', 2, 2)]), /Builder failed/);
  assert.deepEqual(chunks.entries(), previous);
  const cancelled = chunks.update([entry('a', 3, 0)]);
  assert(chunks.cancel());
  hold.reject(Error('Worker aborted'));
  assert.equal(await cancelled, null);
  assert.deepEqual(chunks.entries(), previous);
});

test('retained bindings reuse normalized profiles and follow carrier edits through attached frames', () => {
  const d = A.document(),
    c = A.context(d);
  c.register('plate', {
    describe(e) {
      const origin = e.parameters.position,
        surface = P.surface.plane({ id: 'face', origin, u: [4, 0, 0], v: [0, 2, 0] });
      return { bounds: surface.bounds, surfaces: [surface] };
    }
  });
  d.transact('Create', () => {
    d.setStyle('site', { materials: { shell: '#223344', edge: 'shell' } });
    d.setStyle('assembly', { extends: 'site', materials: { shell: '#445566' } });
    d.setEnvironment({ styleRef: 'site' });
    d.create('plate', { id: 'surface', styleRef: 'assembly', parameters: { position: [0, 0, 0] } });
    d.create('clip', { id: 'clip', anchor: { host: 'surface', surface: 'face', uv: [0.5, 0.5], offset: 0.2 } });
    d.create('tip', { id: 'tip', parent: 'clip', parameters: { transform: { position: [0, 0, 0.3] } } });
  });
  const style = c.style('tip');
  assert.deepEqual(P.styles.material(style, 'edge').color, [68 / 255, 85 / 255, 102 / 255]);
  assert.deepEqual(A.worldFrame(c, 'tip').t, [2, 1, 0.5]);
  const a = d.snapshot();
  d.update('surface', { parameters: { position: [3, 1, 0] } });
  assert.equal(d.snapshot().styles, a.styles);
  assert.equal(d.snapshot().entities.tip, a.entities.tip);
  assert.equal(c.style('tip'), style);
  assert.deepEqual(A.worldFrame(c, 'tip').t, [5, 2, 0.5]);
  d.setStyle('assembly', { extends: 'site', materials: { shell: '#aabbcc' } });
  assert.notEqual(c.style('tip'), style);
  assert.equal(c.read('constructor'), null);
  c.dispose();
});

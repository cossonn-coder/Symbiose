const test = require('node:test');
const assert = require('node:assert/strict');
const core = require('..');
const { KIT } = core.load();
const coastline = require('../examples/biome-world');

const map = chunks => new Map(chunks.map(chunk => [chunk.key, chunk]));
const itineraryMedia = trace => trace.media.map(({ kind, id }) => [kind, id]);
const passage = [['air', null], ['water', 'coast-water'], ['air', 'chamber-air']];

function checkWalkAndDive(coast, frame) {
  const walker = frame.traversal({ radius: 0.14, height: 1.2, stepUp: 0.25, stepDown: 0.35 });
  const from = walker.stand([-14, frame.heightAt(-14, 0.54), 0.54]);
  assert.equal(from.support, 'terrain');
  const motion = walker.move(from.foot, [4, 0], { trace: true });
  assert.equal(motion.blocked, false);
  assert(Math.abs(motion.foot[0] + 10) < 1e-10);
  const trace = frame.traceRoute(coast.itinerary(frame));
  assert.equal(trace.ok, true);
  assert.deepEqual(itineraryMedia(trace), passage);
  assert.equal(frame.traceRoute([[3, -2.6, 0.54], [3, -2.6, 2]]).ok, false);
}

test('chunks build deterministic splats, placements and sampled solids against the same traversable field', () => {
  const coast = coastline(KIT), { compiler, indices } = coast;
  const frame = compiler.prepare(coast.author.view(), { water: coast.water() });
  const ordered = indices.map(index => compiler.build(frame, index));
  const reversed = indices.slice().reverse().map(index => compiler.build(frame, index));
  const forwardWorld = compiler.makeWorld(frame, ordered), reverseWorld = compiler.makeWorld(frame, reversed);
  assert.deepEqual(forwardWorld.data, reverseWorld.data);
  assert.deepEqual(forwardWorld.splatIds, reverseWorld.splatIds);
  assert.deepEqual(forwardWorld.renderMetadata, reverseWorld.renderMetadata);
  const labels = KIT.world.query.fromScene(forwardWorld).probe('look/provenance', { surface: 'terrain' });
  assert.equal(labels.status, 'ok');
  assert(labels.value.targets.every(row => row.surfaceId === 'terrain' && typeof row.materialId === 'string'));
  assert.equal(new Set(forwardWorld.splatIds).size, forwardWorld.count);
  for (const { splats } of ordered) assert.equal(splats.data.buffer.byteLength, splats.count * 16 * 4);
  const cpu = core.render(forwardWorld, { w: 72, h: 48, px: 1, raw: true });
  assert.equal(cpu.w, 72);
  assert.equal(cpu.h, 48);
  for (const chunk of reversed) assert.deepEqual(chunk.placements, map(ordered).get(chunk.key).placements);
  assert.deepEqual([...new Set(ordered.flatMap(chunk => chunk.placements.map(p => p.species).filter(Boolean)))].sort(),
    ['glow-moss', 'kelp', 'lichen', 'reed']);
  const chunks = map(ordered), left = chunks.get('0/0'), right = chunks.get('1/0');
  for (const y of [-4.4, -4, -2.2, -0.6, 0.4, 1.2]) {
    const x = left.bounds.max[0], z = 0.65, value = left.field.sample(x, y, z);
    assert.equal(value, right.field.sample(x, y, z));
    assert.equal(Math.sign(value), Math.sign(frame.distance(x, y, z)));
  }
  assert(left.field.sample(2, -2.4, 0.54) > 0);
  assert(left.field.sample(2, -4.8, 0.54) < 0);
  assert.equal(left.field.sample(-1, 0, 0), null);
  assert(left.work.heightColumns < left.work.samples);
  const support = frame.supports(2, 0.54, -5, 3);
  assert.equal(support[0].id, 'cave');
  assert.equal(support[0].y, -4.25);
  assert.equal(support[1].id, 'terrain');
  const marker = chunks.get('-4/0').placements.find(p => p.kind === 'landmark');
  assert.equal(marker.point[1], frame.heightAt(marker.point[0], marker.point[2]));
  const cut = a => a.routes.some(route => route.route === 'dive' && route.points.some(p => p[0] === 4));
  assert(cut(left) && cut(right));
  checkWalkAndDive(coast, frame);
});

test('paint, moving a pinned route and tide revisions rebuild local chunks and match a reloaded cold build', async () => {
  const coast = coastline(KIT), { compiler, author, indices } = coast;
  const prepare = level => compiler.prepare(author.view(), { water: coast.water(level) });
  const originalPath = prepare(0).view.layout.routes.find(route => route.id === 'dive').points;
  author.pinRoute('passage', 'dive', originalPath);
  const initial = prepare(0);
  await compiler.update(initial, indices);
  const start = map(compiler.chunks());
  checkWalkAndDive(coast, initial);
  author.paint({ id: 'kelp-gap', channel: 'population', target: 'kelp', points: [[3.7, 0.55]],
    width: 2.4, softness: 0, height: [-4, -3] });
  const painted = prepare(0);
  const a = await compiler.update(painted, indices.slice().reverse());
  assert.deepEqual(a.replaced.map(c => c.key), ['0/-1', '0/0', '1/-1', '1/0']);
  const afterPaint = map(compiler.chunks());
  assert.equal(afterPaint.get('-4/0'), start.get('-4/0'));
  assert.equal(afterPaint.get('2/0'), start.get('2/0'));
  const removedKelp = start.get('0/0').placements.filter(item => item.species === 'kelp' &&
    !afterPaint.get('0/0').placements.some(after => after.id === item.id));
  assert(removedKelp.length > 0);
  assert.deepEqual(afterPaint.get('0/0').splats.ids.filter(id => id.startsWith('surface/')),
    start.get('0/0').splats.ids.filter(id => id.startsWith('surface/')));

  const movedRoute = originalPath.map((point, i) => i === originalPath.length - 1 ?
    [point[0], point[1], point[2] + 0.18] : point);
  author.pinRoute('passage', 'dive', movedRoute);
  const moved = prepare(0);
  const b = await compiler.update(moved, indices);
  assert.deepEqual(b.replaced.map(c => c.key), ['1/-1', '1/0', '2/-1', '2/0']);
  assert.equal(map(compiler.chunks()).get('0/0'), afterPaint.get('0/0'));
  checkWalkAndDive(coast, moved);

  const raised = prepare(0.38);
  const c = await compiler.update(raised, indices);
  assert.equal(c.replaced.length, 10);
  assert(c.replaced.some(chunk => chunk.key === '-2/0'));
  const end = map(compiler.chunks());
  assert.equal(end.get('-4/0'), start.get('-4/0'));
  assert.equal(end.get('-3/0'), start.get('-3/0'));
  assert.deepEqual(end.get('-4/0').splats.ids, start.get('-4/0').splats.ids);
  assert.deepEqual(end.get('-4/0').placements, start.get('-4/0').placements);
  assert.equal(initial.view.mediumAt(0, -0.3, 0.54).surface, 0);
  assert.equal(raised.view.mediumAt(0, -0.3, 0.54).surface, Math.fround(0.38));
  const reloaded = coastline(KIT, author.document.serialize());
  const cold = reloaded.compiler.prepare(reloaded.author.view(), { water: reloaded.water(0.38) });
  checkWalkAndDive(reloaded, cold);
  const coldChunks = reloaded.indices.slice().reverse().map(index => reloaded.compiler.build(cold, index));
  assert.deepEqual(compiler.makeWorld(raised, [...end.values()]).data, reloaded.compiler.makeWorld(cold, coldChunks).data);
  for (const chunk of coldChunks) {
    assert.deepEqual(chunk.placements, end.get(chunk.key).placements);
    assert.deepEqual(chunk.routes, end.get(chunk.key).routes);
    assert.deepEqual(chunk.splats.ids, end.get(chunk.key).splats.ids);
  }
  assert.deepEqual((await compiler.update(prepare(0.38), indices)).replaced, []);
});

test('failed builds preserve the published revision and serialized updates can recover', async () => {
  const author = KIT.procedural.biomeRecipes.create({ fallback: 'plain',
    recipes: [{ id: 'plain', materials: { dirt: [0x334411] },
      landmarks: [{ id: 'rock', at: [0.5, 0.5, 0.5] }] }],
    regions: [{ id: 'main', biome: 'plain', bounds: { min: [0, -1, 0], max: [2, 1, 2] } }] });
  const compiler = KIT.procedural.biomeWorld.create({ height: () => 0, chunkCells: 8,
    emit(B, item, frame) {
      if (frame.time === 1) throw new Error('asset unavailable');
      B.iso(...item.point, 0.08, B.P[1], 1);
    } });
  const frame = time => compiler.prepare(author.view(), { time });
  await compiler.update(frame(0), [[0, 0]]);
  const old = compiler.chunks()[0];
  await assert.rejects(compiler.update(frame(1), [[0, 0]]), /asset unavailable/);
  assert.equal(compiler.frame().time, 0);
  assert.equal(compiler.chunks()[0], old);
  const a = compiler.update(frame(2), [[0, 0]]);
  const b = compiler.update(frame(3), [[0, 0]]);
  assert.equal((await a).frame.time, 2);
  assert.equal((await b).frame.time, 3);
  assert.equal(compiler.frame().time, 3);
});

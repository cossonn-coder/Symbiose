const test = require('node:test'),
  assert = require('node:assert/strict');
const { authoring: A, procedural: P } = require('..').load().KIT;
const near = (a, b, e = 1e-6) => assert(Math.abs(a - b) < e, `${a} differs from ${b}`);
const box = (x, size = 1) => ({ min: [x - size, 0, -size], max: [x + size, 2, size] });
function setup() {
  const d = A.document(),
    c = A.context(d);
  c.register('mass', {
    describe(e) {
      return { bounds: box(e.parameters.x || 0), tags: ['solid'] };
    }
  });
  c.register('route', {
    describe(e) {
      return { bounds: box(e.parameters.x || 0, 0.2) };
    }
  });
  c.rule({
    id: 'route-openings',
    types: ['mass'],
    generate(e, ctx) {
      return ctx
        .query(box(e.parameters.x || 0), { types: ['route'] })
        .map(r => ({ key: r.id, type: 'opening', parameters: { variant: 'arch', crossing: r.id } }));
    }
  });
  return { d, c };
}

test('surface coordinates round-trip, skewed planes project correctly, and rays respect extents', () => {
  const p = P.surface.plane({ id: 'facade', origin: [2, 1, 3], u: [4, 0, 0], v: [1, 3, 0] });
  const at = [0.3, 0.7],
    sample = p.sample(at),
    project = p.project(sample.p);
  near(project[0], at[0]);
  near(project[1], at[1]);
  const hit = p.raycast([sample.p[0], sample.p[1], 10], [0, 0, -1], 100);
  near(hit.distance, 7);
  near(hit.uv[0], 0.3);
  assert.equal(p.raycast([-100, 0, 10], [0, 0, -1], 100), null);
  assert(Object.isFrozen(p.bounds.min));
  const q = P.surface.plane({ id: 'skew', origin: [0, 0, 0], u: [1, 0, 0], v: [1, 1, 0] });
  const closest = q.closest([-1, 0.5, 0]);
  near(closest.p[0], 0);
  near(closest.p[1], 0);
});

test('ray filters receive immutable per-query options and can reveal farther hits', () => {
  const d=A.document(),c=A.context(d);
  c.register('sheet',{
    describe(e){
      const surface=P.surface.plane({id:'face',origin:[-1,0,e.parameters.z],u:[2,0,0],v:[0,2,0]});
      return {bounds:surface.bounds,surfaces:[surface]};
    }
  });
  d.create('sheet',{id:'front',parameters:{z:3}});
  d.create('sheet',{id:'rear',parameters:{z:1}});
  const dispose=c.rayFilter('pick-context',(hit,entity,context,query)=>{
    assert.equal(context,c);
    assert(Object.isFrozen(query));
    assert.equal(hit.id,entity.id);
    return entity.id!=='front'||!query.skipFront;
  });
  const pick=options=>c.raycast([0,1,5],[0,0,-1],options)?.id;
  assert.equal(pick(),'front');
  assert.equal(pick({skipFront:true}),'rear');
  assert.equal(pick({skipFront:true,maxDistance:3}),undefined);
  assert.equal(pick({skipFront:true,rayFilters:false}),'front');
  assert.equal(pick(),'front');
  dispose();
  assert.equal(pick({skipFront:true}),'front');
  c.dispose();
});

test('cylindrical and elliptical hosts wrap normalized anchors and return actual ray intersections', () => {
  const s = P.surface.cylinder({ id: 'wall', origin: [0, 1, 0], radius: 2, height: 4 });
  const q = s.sample([1.25, 0.5]);
  near(q.p[0], 0);
  near(q.p[1], 3);
  near(q.p[2], 2);
  const uv = s.project(q.p);
  near(uv[0], 0.25);
  near(uv[1], 0.5);
  const hit = s.raycast([0, 3, 5], [0, 0, -1], 20);
  near(hit.distance, 3);
  near(hit.n[2], 1);
  assert.equal(s.raycast([0, 9, 5], [0, 0, -1], 20), null);
  const ellipse = P.surface.cylinder({ id: 'ellipse', origin: [0, 0, 0], radii: [3, 1], height: 2 });
  const closest = ellipse.closest([2, 1, 2]);
  near(closest.p[0] ** 2 / 9 + closest.p[2] ** 2, 1);
  const offset = [2 - closest.p[0], 0, 2 - closest.p[2]];
  near(offset[0] * closest.tangent[0] + offset[2] * closest.tangent[2], 0, 1e-5);
});

test('registered transformed charts can sample just the point and normal', () => {
  const d = A.document(), c = A.context(d);
  const local = P.surface.cylinder({ id: 'wall', origin: [2, 1, -1], radii: [3, 1], height: 2 });
  const pose = P.transforms.local({ position: [-3, 2, 1], rotation: [.2, .7, -.4], scale: [-1, 2, 3] });
  const surface = P.surface.transform(local, pose);
  c.register('carrier', {describe() { return {bounds:surface.bounds, surfaces:[surface]}; }});
  d.create('carrier', {id:'carrier'});
  const chart = c.surfaces('carrier')[0];
  for (const uv of [[0,0],[.33,.5],[.999,1]]) {
    const {p,n} = chart.sample(uv);
    assert.deepEqual(chart.samplePointNormal(uv), {p,n});
  }
  c.dispose();
});

test('both creation orders produce the same retained generated opening; removal and undo include consequences', () => {
  const a = setup(),
    b = setup();
  a.d.create('mass', { id: 'wall', parameters: { x: 0 } });
  a.d.create('route', { id: 'path' });
  b.d.create('route', { id: 'path' });
  b.d.create('mass', { id: 'wall', parameters: { x: 0 } });
  assert.deepEqual(a.d.entities('opening'), b.d.entities('opening'));
  const opening = a.d.entities('opening')[0],
    before = a.d.serialize();
  a.d.remove('path');
  assert.equal(a.d.entities('opening').length, 0);
  a.d.undo();
  assert.equal(a.d.serialize(), before);
  a.d.redo();
  assert.equal(a.d.entities('opening').length, 0);
  a.d.undo();
  a.d.update('wall', { parameters: { x: 0.1 } });
  assert.equal(a.d.entities('opening')[0].id, opening.id);
});

test('context regeneration respects explicit variants, promoted slots and canceled drag state', () => {
  const { d, c } = setup();
  d.transact('Build', () => {
    d.create('mass', { id: 'wall' });
    d.create('route', { id: 'path' });
  });
  const id = d.entities('opening')[0].id;
  d.update(id, { parameters: { variant: 'pointed' } });
  const before = d.serialize();
  d.begin('Move crossing');
  d.update('path', { parameters: { x: 50 } });
  d.preview();
  assert.equal(d.get(id), null);
  d.cancel();
  assert.equal(d.serialize(), before);
  c.sync();
  d.update('path', { parameters: { x: 0.1 } });
  assert.equal(d.get(id).parameters.variant, 'pointed');
  d.promote(id);
  d.update('path', { parameters: { x: 0.2 } });
  assert.equal(d.entities('opening').length, 1);
  assert.equal(d.get(id).derived, undefined);
});

test('moving a local route invalidates its old and new neighborhoods and leaves a distant assembly untouched', () => {
  const { d, c } = setup();
  d.transact('Level', () => {
    d.create('mass', { id: 'left' });
    d.create('mass', { id: 'right', parameters: { x: 10 } });
    d.create('mass', { id: 'far', parameters: { x: 500 } });
    d.create('route', { id: 'moving' });
    d.create('route', { id: 'far-path', parameters: { x: 500 } });
  });
  const far = d.entities('opening').find(e => e.derived.owner === 'far'),
    before = c.dependencies();
  assert(before.some(j => j.owner === 'far' && j.regions.length));
  c.resetStats();
  d.update('moving', { parameters: { x: 10 } });
  assert(!d.entities('opening').some(e => e.derived.owner === 'left'));
  assert(d.entities('opening').some(e => e.derived.owner === 'right'));
  assert.deepEqual(d.get(far.id), far);
  assert.equal(c.stats().jobsRun, 2);
  assert.equal(c.stats().adapterUpdates, 1);
});

test('an initially empty spatial read and an initially missing explicit read both invalidate on creation', () => {
  const { d, c } = setup();
  d.create('mass', { id: 'wall' });
  c.rule({
    id: 'explicit',
    types: ['mass'],
    generate(e, ctx) {
      return ctx.read('future') ? [{ key: 'found', type: 'marker' }] : [];
    }
  });
  c.reconcile();
  assert.equal(d.entities('marker').length, 0);
  d.create('route', { id: 'future' });
  assert.equal(d.entities('marker').length, 1);
  assert.equal(d.entities('opening').length, 1);
});

test('anchored bounds and hits move with their host while UV and generated identity remain stable', () => {
  const d = A.document(),
    c = A.context(d);
  c.register('host', {
    describe(e) {
      const x = e.parameters.x || 0;
      return {
        bounds: { min: [x, 0, 0], max: [x + 4, 3, 0] },
        surfaces: [P.surface.plane({ id: 'front', origin: [x, 0, 0], u: [4, 0, 0], v: [0, 3, 0] })]
      };
    }
  });
  c.register('prop', {
    describe(e, ctx) {
      const p = ctx.anchor(e.anchor).p;
      return { bounds: { min: p.map(v => v - 0.1), max: p.map(v => v + 0.1) } };
    }
  });
  d.transact('Host and child', () => {
    d.create('prop', { id: 'child', anchor: { host: 'host', surface: 'front', uv: [0.5, 0.5], offset: 0.2 } });
    d.create('host', { id: 'host' });
  });
  near(c.anchor('child').p[0], 2);
  near(c.anchor('child').p[2], 0.2);
  d.update('host', { parameters: { x: 10 } });
  near(c.query(box(12, 1), { types: ['prop'] })[0].bounds.min[0], 11.9);
  assert.deepEqual(d.get('child').anchor.uv, [0.5, 0.5]);
  const hit = c.raycast([12, 1.5, 5], [0, 0, -1], { types: ['host'] });
  near(hit.distance, 5);
  assert.equal(hit.surface, 'front');
  const closest = c.nearest([12, 1.5, 0.3], { types: ['host'], radius: 1 });
  near(closest.distance, 0.3);
});

test('rules converge across dependencies and cyclic generation aborts the whole triggering edit', () => {
  const { d, c } = setup();
  c.rule({
    id: 'opening-detail',
    types: ['opening'],
    generate(e) {
      return [{ key: 'sill', type: 'prop', parameters: { chosen: 'urn' } }];
    }
  });
  d.transact('Build', () => {
    d.create('mass', { id: 'wall' });
    d.create('route', { id: 'path' });
  });
  assert.equal(d.entities('prop').length, 1);
  const before = d.serialize();
  const stop = c.rule({
    id: 'infinite',
    types: ['source'],
    generate() {
      return [{ key: 'again', type: 'source' }];
    }
  });
  assert.throws(() => d.create('source'), /did not converge/);
  assert.equal(d.serialize(), before);
  stop();
  d.update('wall', { parameters: { x: 0.2 } });
  assert.equal(d.entities('prop').length, 1);
});

test('invalid descriptors roll back, large bounds use a safe fallback, and disposal detaches rules', () => {
  const d = A.document(),
    c = A.context(d, { maxCells: 8 });
  c.register('large', {
    describe(e) {
      return { bounds: e.parameters.bounds };
    }
  });
  d.create('large', { id: 'huge', parameters: { bounds: { min: [-1e12, -1e12, -1e12], max: [1e12, 1e12, 1e12] } } });
  assert.equal(c.query(box(0)).length, 1);
  assert.equal(c.query({ min: [1e100, 0, 0], max: [1e100, 1, 1] }).length, 0);
  const before = d.serialize();
  assert.throws(() => d.update('huge', { parameters: { bounds: { min: [3, 0, 0], max: [1, 1, 1] } } }), /bounds/);
  assert.equal(d.serialize(), before);
  c.dispose();
  assert.throws(() => c.query(box(0)), /disposed/);
  d.update('huge', { parameters: { note: 'still editable without context' } });
});

test('later rules skip generated owners pruned earlier in the same reconciliation pass', () => {
  const d = A.document(),
    c = A.context(d);
  c.rule({
    id: 'a-details',
    types: ['mass'],
    generate(e) {
      return e.parameters.detail ? [{ key: 'detail', type: 'mass', parameters: { leaf: true } }] : [];
    }
  });
  c.rule({
    id: 'z-covers',
    types: ['mass'],
    generate(e) {
      return e.parameters.leaf ? [] : [{ key: 'cover', type: 'cover' }];
    }
  });
  d.create('mass', { id: 'house', parameters: { detail: true } });
  assert.equal(d.entities('mass').length, 2);
  const before = d.serialize();
  d.update('house', { parameters: { detail: false } });
  assert.equal(d.entities('mass').length, 1);
  assert.equal(d.entities('cover').length, 1);
  d.undo();
  assert.equal(d.serialize(), before);
});

test('composable ray filters reject realized surface hits and can be bypassed or removed for substrate tools', () => {
  const d = A.document(),
    c = A.context(d);
  c.register('envelope', {
    describe(e) {
      const z = e.parameters.transform.position[2];
      const surface = P.surface.plane({ id: 'front', origin: [-1, 0, z], u: [2, 0, 0], v: [0, 2, 0] });
      return { bounds: surface.bounds, surfaces: [surface] };
    }
  });
  d.create('envelope', {
    id: 'front',
    parameters: { width: 2, depth: 1, height: 2, transform: { position: [0, 0, 2] } }
  });
  d.create('envelope', {
    id: 'back',
    parameters: { width: 2, depth: 1, height: 2, transform: { position: [0, 0, -2] } }
  });
  const origin = [0, 1, 6],
    dir = [0, 0, -1],
    before = d.serialize();
  assert.equal(c.raycast(origin, dir).id, 'front');
  const remove = c.rayFilter('hide-front', (hit, entity) => {
    assert.equal(typeof hit.surface, 'string');
    return entity.id !== 'front';
  });
  assert.equal(c.raycast(origin, dir).id, 'back');
  assert.equal(c.raycast(origin, dir, { rayFilters: false }).id, 'front');
  assert.throws(() => c.rayFilter('hide-front', () => true), /unique/);
  const unhide = c.rayFilter('hide-back', hit => hit.id !== 'back');
  assert.equal(c.raycast(origin, dir), null);
  unhide();
  assert.equal(c.raycast(origin, dir).id, 'back');
  remove();
  assert.equal(c.raycast(origin, dir).id, 'front');
  assert.equal(d.serialize(), before);
  c.dispose();
  assert.throws(() => c.rayFilter('later', () => true), /disposed/);
});

test('related-entity collections track additions/removals during descriptors without spatial queries or far-host invalidation', () => {
  const d = A.document(),
    c = A.context(d),
    updates = [];
  c.register('host', {
    describe(e) {
      return { bounds: box(e.parameters.x || 0) };
    }
  });
  c.register('leaf', {
    describe(e, s) {
      const siblings = s.collection({ type: 'leaf', anchorHost: e.anchor.host });
      updates.push([e.id, siblings.map(e => e.id)]);
      return { bounds: box(e.parameters.x || 0) };
    }
  });
  c.register('anchored-host', {
    describe() {
      return {
        bounds: box(0),
        surfaces: [P.surface.plane({ id: 's', origin: [0, 0, 0], u: [1, 0, 0], v: [0, 1, 0] })]
      };
    }
  });
  d.create('anchored-host', { id: 'a' });
  d.create('anchored-host', { id: 'b' });
  d.create('leaf', { id: 'one', anchor: { host: 'a', surface: 's', uv: [0.5, 0.5] } });
  d.create('leaf', { id: 'far', anchor: { host: 'b', surface: 's', uv: [0.5, 0.5] } });
  updates.length = 0;
  d.create('leaf', { id: 'two', anchor: { host: 'a', surface: 's', uv: [0.5, 0.5] } });
  assert(updates.some(([id, ids]) => id === 'one' && ids.includes('two')));
  assert(!updates.some(([id]) => id === 'far'));
  updates.length = 0;
  d.remove('two');
  assert(updates.some(([id, ids]) => id === 'one' && !ids.includes('two')));
  assert.equal(c.stats().queries, 0);
});
test('empty related collections invalidate generation rules when a matching entity is later added', () => {
  const d = A.document(),
    c = A.context(d);
  c.register('host', {
    describe() {
      return { bounds: box(0) };
    }
  });
  c.rule({
    id: 'related-count',
    types: ['host'],
    generate(e, s) {
      return [
        { key: 'count', type: 'count', parameters: { value: s.collection({ type: 'leaf', parent: e.id }).length } }
      ];
    }
  });
  d.create('host', { id: 'host' });
  assert.equal(d.entities('count')[0].parameters.value, 0);
  d.create('leaf', { parent: 'host' });
  assert.equal(d.entities('count')[0].parameters.value, 1);
  d.undo();
  assert.equal(d.entities('count')[0].parameters.value, 0);
});

test('stable views keep reads current across adapter registration, pending edits, cancellation and new rules', () => {
  const d = A.document(),
    c = A.context(d),
    id = d.create('mass', { parameters: { x: 0 } });
  const adapter = shift => ({
    describe(e) {
      return { bounds: box((e.parameters.x || 0) + shift) };
    }
  });
  c.register('mass', adapter(0));
  const original = d.snapshot();
  for (let i = 0; i < 20; i++) assert.strictEqual(c.read(id), original.entities[id]);
  assert.equal(c.stats().adapterUpdates, 1);
  c.register('mass', adapter(10));
  assert.equal(c.query(box(10)).length, 1, 'new adapter invalidates unchanged intent');
  assert.equal(c.query(box(0)).length, 0);
  assert.equal(c.stats().adapterUpdates, 2);
  d.begin('Move draft');
  d.update(id, { parameters: { x: 5 } });
  assert.equal(c.query(box(15)).length, 1);
  d.cancel();
  assert.equal(c.query(box(10)).length, 1);
  assert.equal(c.query(box(15)).length, 0);
  c.rule({
    id: 'later',
    types: ['mass'],
    generate() {
      return [{ key: 'one', type: 'detail' }];
    }
  });
  c.reconcile();
  assert.equal(d.entities('detail').length, 1, 'a new rule still runs on unchanged intent');
  d.update(id, { parameters: { x: 20 } });
  assert.equal(c.query(box(30), { types: ['mass'] }).length, 1);
  d.undo();
  assert.equal(c.query(box(10), { types: ['mass'] }).length, 1);
  c.dispose();
});

test('an explicit environment key excludes presentation without masking physical scene changes', () => {
  const d = A.document(),
    c = A.context(d, {
      environmentKey: environment => {
        const key = { ...environment };
        delete key.presentation;
        return key;
      }
    });
  let runs = 0;
  c.register('mass', {
    describe() {
      return { bounds: { min: [0, 0, 0], max: [1, 1, 1] } };
    }
  });
  c.rule({
    id: 'count',
    types: ['mass'],
    generate() {
      runs++;
      return [];
    }
  });
  d.create('mass');
  const initial = c.stats(),
    count = runs;
  d.setEnvironment({ presentation: { grade: { saturation: 0 } } });
  assert.equal(c.stats().adapterUpdates, initial.adapterUpdates);
  assert.equal(runs, count);
  assert.equal(c.snapshot().environment.presentation.grade.saturation, 0);
  d.setEnvironment({ physical: { level: 2 } });
  assert(c.stats().adapterUpdates > initial.adapterUpdates);
  assert(runs > count);
  c.dispose();
  assert.throws(() => A.context(d, { environmentKey: 42 }), /settings/);
});

test('a watched intent value invalidates descriptors and rules when its result changes', () => {
  const d = A.document(), c = A.context(d);
  const size = scene => scene.entities.measure?.parameters.size ?? 1;
  let describes = 0, generates = 0;
  c.register('receiver', { describe(e, ctx) {
    describes++;
    return { bounds: box(ctx.watch(size) * 5, .2) };
  } });
  c.rule({ id: 'transfer', types: ['receiver'], generate(e, ctx) {
    generates++;
    return [{ key:'measurement', type:'reading', parameters:{ size:ctx.watch(size) } }];
  } });
  d.create('receiver', {id:'target'});
  const prepared = describes, generated = generates;
  d.create('setting', {id:'other',parameters:{size:99}});
  assert.equal(describes, prepared);
  assert.equal(generates, generated);
  d.create('setting', {id:'measure',parameters:{size:2}});
  assert.equal(c.query(box(10,.2))[0].id,'target');
  assert.equal(d.entities('reading')[0].parameters.size,2);
  d.update('measure',{parameters:{size:3}});
  assert.equal(c.query(box(10,.2)).length,0);
  assert.equal(c.query(box(15,.2))[0].id,'target');
  d.undo();
  assert.equal(c.query(box(10,.2))[0].id,'target');
  assert.equal(d.entities('reading')[0].parameters.size,2);
  c.dispose();
});

test('spatial rules track matching records as they enter and leave filtered queries', () => {
  const d = A.document(), c = A.context(d);
  c.register('sensor',{describe:()=>({bounds:box(0)})});
  for (const type of ['block','ornament']) c.register(type,{describe:e=>({
    bounds:box(e.parameters.x || 0,.3),tags:[e.parameters.tag || 'solid']
  })});
  let runs = 0;
  c.rule({id:'sense',types:['sensor'],generate(e,ctx){
    runs++;
    const hits = ctx.query(box(0),{types:['block'],tags:['solid'],exclude:['skip']});
    return [{key:'reading',type:'reading',parameters:{ids:hits.map(hit=>hit.id)}}];
  }});
  d.create('sensor',{id:'sensor'});
  const initial = runs;
  d.create('ornament',{id:'bush'});
  d.create('block',{id:'skip'});
  d.create('block',{id:'moving',parameters:{tag:'decoration'}});
  assert.equal(runs,initial);
  d.update('moving',{parameters:{tag:'solid'}});
  assert.deepEqual(d.entities('reading')[0].parameters.ids,['moving']);
  d.update('moving',{parameters:{x:10}});
  assert.deepEqual(d.entities('reading')[0].parameters.ids,[]);
  d.update('moving',{parameters:{x:0}});
  assert.deepEqual(d.entities('reading')[0].parameters.ids,['moving']);
  d.update('moving',{parameters:{tag:'decoration'}});
  assert.deepEqual(d.entities('reading')[0].parameters.ids,[]);
  c.dispose();
});

test('parameter-scoped collections update only when an entity enters, leaves or changes within the filter',()=>{
  const d=A.document(),c=A.context(d),queries=[];
  c.register('probe',{describe(e,ctx){
    queries.push(ctx.collection({type:'stroke',parameters:{layer:'water'}}).map(item=>item.id));
    return {bounds:box(0)};
  }});
  d.create('probe',{id:'probe'});
  assert.deepEqual(queries,[[]]);
  d.create('stroke',{id:'track',parameters:{layer:'path'}});
  d.update('track',{parameters:{width:2}});
  assert.deepEqual(queries,[[]]);
  d.update('track',{parameters:{layer:'water'}});
  assert.deepEqual(queries.at(-1),['track']);
  d.update('track',{parameters:{width:3}});
  assert.deepEqual(queries.at(-1),['track']);
  d.update('track',{parameters:{layer:'plants'}});
  assert.deepEqual(queries,[[],['track'],['track'],[]]);
  assert.throws(()=>c.collection({parameters:{layer:['path']}}),/named scalar/);
  c.dispose();
});

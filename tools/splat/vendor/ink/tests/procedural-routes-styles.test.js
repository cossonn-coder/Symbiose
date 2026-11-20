const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const P = KIT.procedural;
const near = (a, b) => assert(Math.abs(a - b) < 1e-8, `${a} != ${b}`);

test('polyline routes measure 3D length and return usable frames and closest points', () => {
  const points = [
    [0, 0, 0],
    [3, 0, 0],
    [3, 4, 0]
  ];
  const route = P.routes.polyline(points);
  near(route.length, 7);
  near(route.breaks[0], 3 / 7);
  assert.deepEqual(route.sample(0).point, points[0]);
  assert.deepEqual(route.sample(1).point, points[2]);
  for (const t of [0.2, 0.9]) {
    const at = route.sample(t);
    near(KIT.V.dot(at.tangent, at.side), 0);
    near(KIT.V.dot(at.normal, at.side), 0);
    near(KIT.V.len(at.normal), 1);
    near(route.closest(at.point).t, t);
  }
  assert.deepEqual(route.closest([3, 2, 1]).point, [3, 2, 0]);
  points[2][1] = 50;
  assert.deepEqual(route.sample(1).point, [3, 4, 0]);
  assert.throws(
    () =>
      P.routes.polyline([
        [0, 0, 0],
        [0, 0, 0]
      ]),
    /distinct/
  );
});

test('convex perimeter policies preserve offset, corners, and endpoint elevations', () => {
  const square = [
    [-1, -1],
    [1, -1],
    [1, 1],
    [-1, 1]
  ];
  for (const outline of [square, square.slice().reverse()]) {
    const route = P.routes.aroundConvex(outline, [0, 0, -1], [1, 1, 0], { offset: 0.2 });
    assert.deepEqual(route.points, [
      [0, 0, -1.2],
      [1.2, 0.5, -1.2],
      [1.2, 1, 0]
    ]);
    near(route.length, 2.6);
    const long = P.routes.aroundConvex(outline, [0, 0, -1], [1, 1, 0], { offset: 0.2, direction: 'longest' });
    assert(long.length > route.length * 2);
    assert.deepEqual(long.sample(0).point, route.sample(0).point);
    assert.deepEqual(long.sample(1).point, route.sample(1).point);
  }
  assert.throws(
    () =>
      P.routes.aroundConvex(
        [
          [0, 0],
          [3, 0],
          [1, 1],
          [3, 3],
          [0, 3]
        ],
        [0, 0, 0],
        [0, 0, 1]
      ),
    /convex/
  );
});

test('route layout preserves bends, creates gaps and accepts existing catenaries', () => {
  const route = P.routes.polyline([
    [0, 0, 0],
    [1.2, 0, 0],
    [1.2, 0, 2.2]
  ]);
  const parts = P.routes.layout(route, { pitch: 0.78, gap: 0.08, key: 'rail' });
  near(
    parts.reduce((sum, p) => sum + p.size, 0),
    route.length
  );
  for (const p of parts) {
    const gap = p.segment === 0 ? p.last[0] - p.first[0] : p.last[2] - p.first[2];
    near(gap, p.length);
    if (p.segment === 0) assert(p.first[2] === 0 && p.last[2] === 0);
    else assert(p.first[0] === 1.2 && p.last[0] === 1.2);
  }
  assert.equal(new Set(parts.map(p => p.key)).size, parts.length);
  const span = P.spans.catenary([0, 3, 0], [4, 4, 0], { sag: 0.65 });
  const curved = P.routes.layout(span, { pitch: 0.5, gap: 0.03, from: 0.25, to: 0.75 });
  near(
    curved.reduce((sum, p) => sum + p.size, 0),
    span.length / 2
  );
  assert.throws(() => P.routes.layout(route, { pitch: 0.000001, budget: 12 }), /budget/);
});

test('style inheritance composes arbitrary channels and resolves reusable material roles', () => {
  const base = {
    materials: { body: { color: '#225544', shade: '#18211a' }, accents: 'body' },
    sizing: { width: 2, depth: 1 }
  };
  const catalog = P.styles.catalog({
    base,
    warm: { extends: 'base', materials: { body: '#cc8833' } },
    alpha: { sizing: { depth: 2 } },
    combined: { extends: ['warm', 'alpha'], sizing: { height: 5 } }
  });
  const profile = catalog.resolve('combined', { sizing: { width: 3 }, custom: { enabled: true } });
  assert.deepEqual(profile.sizing, { width: 3, depth: 2, height: 5 });
  assert.deepEqual(P.styles.material(profile, 'accents'), {
    color: [204 / 255, 136 / 255, 51 / 255],
    shade: [24 / 255, 33 / 255, 26 / 255]
  });
  assert.equal(catalog.resolve('combined', { sizing: { width: 3 }, custom: { enabled: true } }), profile);
  base.materials.body.color = '#000000';
  assert.deepEqual(P.styles.material(catalog.resolve('base'), 'body').color, [34 / 255, 85 / 255, 68 / 255]);
  assert.deepEqual(P.styles.sample(profile, ['custom']), { custom: { enabled: true } });
  assert.throws(() => P.styles.catalog({ loop: { extends: 'loop' } }), /Cyclic/);
  assert.throws(() => P.styles.catalog({ loop: { extends: 'missing' } }), /Unknown/);
  assert.throws(() => P.styles.material(P.styles.compose({ materials: { a: 'b', b: 'a' } }), 'a'), /Cyclic/);
});

test('material references retain inherited channels through a local recolor',()=>{
  const base=P.styles.compose({materials:{
    timber:{color:'#765745',shade:'#473527',roughness:.65},
    panel:{alias:'timber',sun:'#d3ae8e'},
    frame:'panel'
  }});
  const color=P.styles.recolor(base,'frame','#50a6a6');
  assert.deepEqual(color,{alias:'panel',color:P.styles.rgb('#50a6a6')});
  const recolored=P.styles.compose(base,{materials:{frame:color,timber:{roughness:.34}}});
  assert.deepEqual(P.styles.material(recolored,'frame'),{
    color:P.styles.rgb('#50a6a6'),shade:P.styles.rgb('#473527'),
    sun:P.styles.rgb('#d3ae8e'),roughness:.34
  });
  assert.deepEqual(P.styles.material(recolored,'panel').color,P.styles.rgb('#765745'));
  assert.throws(()=>P.styles.compose({materials:{bad:{alias:'__proto__'}}}),/Invalid material alias/);
  const loop=P.styles.compose({materials:{first:{alias:'second'},second:{alias:'first',color:'#123456'}}});
  assert.throws(()=>P.styles.material(loop,'first'),/Cyclic material role/);
});

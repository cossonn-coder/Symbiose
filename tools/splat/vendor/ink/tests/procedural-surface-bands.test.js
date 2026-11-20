const test = require('node:test');
const assert = require('node:assert/strict');
const { fitSurfaceBands } = require('..').load().KIT.procedural;

test('edge fitting keeps its mount, trims toward it and drops a fully blocked side', () => {
  const domain = { min: [-2, -2], max: [2, 2] };
  const opening = { min: [-.5, -.5], max: [.5, .5] };
  const side = { reach: .8, minReach: .2, gap: .125 };
  const edges = { left: side, right: side, bottom: { span: .75, reach: .25, gap: .125 } };
  const [left, right, sill] = fitSurfaceBands({ domain, opening, edges });
  assert.deepEqual(left.hinge, [-.625, 0]);
  assert.deepEqual(right.hinge, [.625, 0]);
  assert.deepEqual(sill.bounds, { min: [-.375, -.875], max: [.375, -.625] });
  const obstructions = [
    { min: [-1.8, -.3], max: [-1, .2] },
    { min: [.57, -.4], max: [1, .1] },
    { min: [-.4, .8], max: [.4, 1.2] }
  ];
  const fitted = fitSurfaceBands({ domain, opening, edges, obstructions, clearance: .125 });
  assert.deepEqual(fitted.map(part => part.edge), ['left', 'bottom']);
  assert.deepEqual(fitted[0].hinge, left.hinge);
  assert.equal(fitted[0].reach, .25);
  assert.equal(fitted[0].bounds.min[0], -.875);
  assert.deepEqual(fitted[1], sill);
  assert(Object.isFrozen(fitted[0].bounds.min));
});

test('a short carrier limits the span and outward reach without moving the edge', () => {
  const opening = { min: [-.5, -.6], max: [.5, .5] };
  const domain = { min: [-.8, -.55], max: [1.5, .38] };
  const [band] = fitSurfaceBands({ domain, opening, edges: { left: { reach: 1, minReach: .2 } } });
  assert.equal(band.reach, .30000000000000004);
  assert.deepEqual(band.bounds, { min: [-.8, -.55], max: [-.5, .38] });
  assert.throws(() => fitSurfaceBands({ domain, opening, edges: { left: { reach: NaN } } }), /positive/);
});

test('panel bands split span at a seam and stay on their own mounting panel', () => {
  const panels = [{ id: 'a', min: [-2, -2], max: [-.05, 2] },
    { id: 'b', min: [.05, -2], max: [2, 2] }];
  const opening = { min: [-.7, -.6], max: [.7, .6] };
  const side = { reach: .8, minReach: .15 };
  const edges = { left: side, right: side, bottom: { reach: .4, span: 1.5, minSpan: .2 } };
  const bands = fitSurfaceBands({ panels, opening, edges,
    obstructions: [{ min: [1.05, -.4], max: [1.6, .4] }] });
  assert.deepEqual(bands.map(r => [r.panel, r.edge]), [
    ['a', 'left'], ['a', 'bottom'], ['b', 'right'], ['b', 'bottom']
  ]);
  assert.equal(bands[1].bounds.max[0], -.05);
  assert.equal(bands[3].bounds.min[0], .05);
  assert.equal(bands[1].hinge[1], bands[3].hinge[1]);
  assert(Math.abs(bands[2].reach - .35) < 1e-8);
  assert.throws(() => fitSurfaceBands({ panels: [panels[0], panels[0]], opening, edges }), /uniquely/);
});

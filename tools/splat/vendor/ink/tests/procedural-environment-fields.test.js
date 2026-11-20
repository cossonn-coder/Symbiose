const test = require('node:test');
const assert = require('node:assert/strict');
const P = require('..').load().KIT.procedural.environmentFields;
const near = (actual, expected, epsilon = 1e-8) => assert(Math.abs(actual - expected) < epsilon, [actual, expected].join(' vs '));

test('coating thickness extends the exposed side of a splat and preserves its substrate', () => {
  const {coating} = P, profile = {depth:.24};
  assert.equal(coating.thickness(1,profile),.24);
  assert.equal(coating.thickness(.1,profile),0);
  assert.equal(coating.thickness(1),0);
  const point=[3,2,1], covariance=[.04,0,0,0,.0004,0,0,0,.01];
  const expanded=coating.shape({point,normal:[0,2,0],covariance,amount:1},profile);
  near(expanded.point[1]-3*Math.sqrt(expanded.covariance[4]), point[1]-3*Math.sqrt(covariance[4]));
  near(expanded.point[1]+3*Math.sqrt(expanded.covariance[4]), point[1]+3*Math.sqrt(covariance[4])+.24);
  assert.equal(expanded.covariance[0],covariance[0]);
  assert.equal(expanded.covariance[8],covariance[8]);
  assert.deepEqual(coating.shape({point,normal:[1,1,0],covariance,amount:0},profile),{depth:0,point,covariance});
  assert.throws(()=>coating.profile({depth:-1}),/bounded depth/);
});

test('the solar clock is deterministic, wraps both ways, and supplies a unit sun direction', () => {
  const noon = P.evaluate({ hour: 12, latitude: 0, declination: 0 }), dawn = P.evaluate({ hour: 6, latitude: 0, declination: 0 }),
    midnight = P.evaluate({ hour: 0, latitude: 0, declination: 0 });
  near(noon.sun[1], 1);
  near(dawn.sun[0], 1);
  near(Math.hypot(...dawn.sun), 1);
  assert(noon.daylight > dawn.daylight && dawn.daylight > midnight.daylight);
  assert.equal(P.evaluate({ hour: 23, rate: .5 }, 6).hour, 2);
  assert.equal(P.evaluate({ hour: 1, rate: -.5 }, 6).hour, 22);
  assert.equal(P.evaluate({ hour: 12, rate: 1e-309 }, 1).hour, 12);
  assert(P.evaluate({ north: Number.MAX_VALUE }).sun.every(Number.isFinite));
  assert.throws(() => P.evaluate({ fog: { height: 0 } }), /height-fog/);
});

test('fog integrates below, above, and across the ground plane', () => {
  const f = { floor: 0, height: 2, cling: 1, density: .1 };
  near(P.opticalDepth([0, -2, 0], [0, 2, 0], f), .2 * (2 - Math.exp(-1)));
  near(P.opticalDepth([0, 2, 0], [0, -2, 0], f), .2 * (2 - Math.exp(-1)));
  near(P.opticalDepth([0, 2, 0], [3, 2, 0], f), .3 * Math.exp(-1));
  near(P.opticalDepth([0, 12, 0], [3, 12, 0], { ...f, cling: 0 }), .3);
  assert.equal(P.opticalDepth([0, 0, 0], [0, 0, 0], f), 0);
});

test('local lights scatter into fog only before the ray endpoint', () => {
  const light = { p: [6, 0, 0], radius: 2, intensity: 1 }, f = { density: .12, height: 2 };
  assert.equal(P.scatter([0, 0, 0], [3, 0, 0], light, f), 0);
  assert.equal(P.scatter([0, 3, 0], [9, 3, 0], light, f), 0);
  assert.equal(P.scatter([0, 0, 0], [9, 0, 0], light, { ...f, density: 0 }), 0);
  assert(P.scatter([0, 0, 0], [9, 0, 0], light, f) > P.scatter([0, 0, 0], [5, 0, 0], light, f));
});

test('deposition varies with load, slope, shelter and exposure', () => {
  assert.equal(P.deposition({ normal: [0, -1, 0], load: 1 }), 0);
  assert.equal(P.deposition({ normal: [1, 0, 0], load: 1 }), 0);
  assert.equal(P.deposition({ normal: [0, 1, 0], load: 1, exposure: 0 }), 0);
  assert(P.deposition({ normal: [0, 2, 0], load: .3, shelter: 1 }) > P.deposition({ normal: [0, 2, 0], load: .3 }));
  assert(P.deposition({ normal: [0, 1, 0], load: 1 }) > P.deposition({ normal: [0, 1, 1], load: 1 }));
});

test('surface coating profiles preserve material and slope differences with a configurable palette', () => {
  const {coating}=P;
  const floor={normal:[0,1,0],load:.9};
  const incline={normal:[1,1,0],load:.9};
  const floorStone=coating.amount({...floor,material:'stone'});
  assert(coating.amount({...floor,material:'wood'})<floorStone);
  assert(coating.amount(incline)<floorStone);
  assert(coating.amount(incline,{bias:.3})>coating.amount(incline,{bias:-.3}));
  assert.equal(coating.amount(floor,{bias:-.4}),coating.amount(floor,{bias:.4}));
  assert.equal(coating.amount({normal:[1,0,0],load:.9},{bias:.4}),0);
  assert.equal(coating.amount({...floor,exposure:0}),0);
  const color=[.14,.21,.32], palette=[.7,.55,.4];
  const spec={shadow:palette,highlight:palette,retention:{ceramic:0}};
  const baked=P.evaluate({coating:spec}).coating;
  palette[0]=.1;
  assert.equal(baked.shadow[0],.7);
  assert.equal(coating.amount({...floor,material:'ceramic'},baked),0);
  assert.deepEqual(coating.color(color,0,baked),color);
  assert.deepEqual(coating.color(color,1,baked),[.7,.55,.4]);
  assert.throws(()=>coating.profile({slope:[.8,.3]}),/Coating/);
  assert.throws(()=>coating.profile({retention:{roof:2}}),/Coating/);
});

const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('..');
const { KIT: K, makeBuilder } = ink.load();
const { airflow, density } = K.procedural;
const wall = (x,y,z) => Math.max(Math.abs(x)-.18, Math.abs(y-.9)-1.1, Math.abs(z)-2);
const blocker = K.atmosphere.occluder(wall,{ bias:.008,step:.016,steps:38 });
const shelter = { occluder:blocker, reach:5, strength:.87, spacing:.08, spread:.08 };

test('a shared gust leaves a recoverable wake behind an upwind wall', () => {
  const flow = airflow.field({ velocity:[4,0], gust:{ amplitude:.5, period:4 }, shelter });
  assert.deepEqual(flow.open(1),[6,0]);
  assert.deepEqual(flow.xyz(-1,.5,0,1),[6,0,0]);
  assert(flow.sample(1,.5,0,1)[0] < 1.5);
  assert(flow.sample(3,.5,0,1)[0] > flow.sample(1,.5,0,1)[0]+2);
  assert.deepEqual(flow.sample(6,.5,0,1),[6,0]);
  assert.deepEqual(flow.sample(1,2.6,0,1),[6,0]);
  assert.deepEqual(flow.sample(1,.5,3,1),[6,0]);
  assert(Math.abs(flow.cloudTravel(0,1)[0]-(4+4/Math.PI)) < .002);
  assert(flow.travel(1,.5,0,0,1)[0] < 1.5);

  const reversing = airflow.field({ shelter },{ ambient:t => [t < 1 ? 4 : -4,0] });
  assert(reversing.sample(1,.5,0,0)[0] < 1);
  assert(reversing.sample(-1,.5,0,2)[0] > -1);
  assert.deepEqual(reversing.sample(1,.5,0,2),[-4,0]);
  assert.throws(() => airflow.field({ shelter:{ reach:4 } }), /occluder/);
});

test('the renderer shares profile gusts with flexible foliage and cloth and advects spray in the lee', () => {
  const B = makeBuilder(3,[0x1c2945,0xccd5bc,0x82b9d4]);
  const bend = airflow.pinned({ reach:1, phase:.1, phaseTravel:0, frequency:2 })(1);
  for (const x of [-1.3,1.3]) {
    B.disc(x,.65,0,[0,0,1],.24,.021,B.P[1],3,bend);
    B.disc(x,.24,.21,[0,0,1],.093,.07,B.P[2],.9,{ k:3, wind:true, ph:.37, sp:1, rg:1 });
  }
  const world = B.finish({ cam:{ target:[0,.65,0], dist:7.5, yaw:0, pitch:.16, sway:0 },
    skyEnvironment:{ sky:false, defaults:{ windX:1.9, windZ:0, windGust:1.6 } },
    weatherBinding:true, windField:{ shelter } });
  const view = { t:.55, w:136, h:80, px:1, raw:true, captureMotion:true };
  const a = ink.render(world,view).motionReference.centers;
  const b = ink.render(world,{ ...view, windField:{ shelter:false } }).motionReference.centers;
  const off = ink.render(world,{ ...view, windField:false }).motionReference.centers;
  assert.equal(a[0],b[0]);
  assert.equal(a[2],b[2]);
  assert(b[0] > off[0]);
  assert(b[4] > a[4]+1.5);
  assert(b[6] > a[6]+12);
  assert.deepEqual(ink.render(world,view).motionReference.centers,a);
});

test('cloud coverage and shadows travel together while smoke uses the sheltered wind offset', () => {
  const B = makeBuilder(4,[0x192436,0xcadfee]);
  B.disc(0,0,0,[0,1,0],3,.04,B.P[1],3);
  const cfg = { bounds:{ min:[-5,-5],max:[5,5] }, resolution:[24,24], height:3,
    coverage:(x,z) => Math.max(0,1-Math.hypot(x,z)/2) };
  const world = B.finish({ cam:{ target:[0,0,0],dist:7,pitch:.14,yaw:0,sway:0 },
    skyEnvironment:{ defaults:{ zenith:'#334767', horizon:'#839eb4' } },
    cloudField:K.clouds.compile(cfg), cloudShadows:{ direction:[0,1,0] },
    windField:{ velocity:[1.3,.21], shelter }
  });
  const view = { t:1.85, w:85, h:73, px:1, raw:true };
  const shared = ink.render(world,view);
  const authored = ink.render({ ...world, windField:false, cloudField:K.clouds.compile({ ...cfg, velocity:[1.3,.21] }) },view);
  assert.deepEqual(shared.rgb,authored.rgb);
  assert.notDeepEqual(shared.rgb,ink.render(world,{ ...view, windField:false }).rgb);

  const shape = density.fromSdf({ bounds:{ min:[-4,-1,-3],max:[4,3,3] }, field:() => -1,
    breakup:1, windInfluence:1, noise:x => .5+x*.08 });
  const flow = airflow.field({ velocity:[2,0], shelter });
  const lee = flow.frame(1);
  const open = airflow.field({ velocity:[2,0] }).frame(1);
  assert(shape.sample(1,.5,0,1,lee) > shape.sample(1,.5,0,1,open)+.1);
  assert.equal(shape.sample(-1,.5,0,1,lee),shape.sample(-1,.5,0,1,open));
});

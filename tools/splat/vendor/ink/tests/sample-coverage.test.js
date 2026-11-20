const assert = require('node:assert/strict');
const test = require('node:test');
const { KIT, makeBuilder, makeSculpt } = require('..').load();
const { render } = require('../cli/render');
const coverage = KIT.procedural.sampleCoverage;

test('coverage cohorts stay stable in local cells and preserve the low motion bits', () => {
  assert.equal(coverage.cohort(-.9, .1, .2, 1, 34), coverage.cohort(-.1, .8, .6, 1, 34));
  assert(new Set(Array.from({length:32}, (_,i) => coverage.cohort(i, 0, 0, .5, 34))).size > 16);
  const code = Float32Array.of(coverage.pack(127) + 8192 + 11)[0];
  assert.equal(code & 15, 11);
  assert.equal(code & 8192, 8192);
  assert.equal(coverage.visible(code, .99), true);
  assert.equal(coverage.visible(code, 1), false);
  assert.equal(coverage.visible(11, 1), true);
  assert.throws(() => coverage.pack(128), /rank/);
  assert.throws(() => coverage.amount(-1), /between/);
});

test('withdrawal changes visible samples through the standard offline render path', () => {
  const builder = makeBuilder(62, [0, 0x718240, 0xec954d, 0x414388]);
  for (const [x, shade, rank] of [[-1.25,1,28],[0,2,94],[1.25,3,undefined]])
    builder.dab(x, 1, 0, [0,0,1], [1,0,0], .34, .4, .025, builder.P[shade], 3, {coverage:rank});
  const world = builder.finish({cam:{target:[0,1,0],yaw:0,pitch:.2,dist:9},detail:12});
  const count = sampleWithdrawal => render(world,{w:160,h:90,px:1,raw:true,samples:true,sampleWithdrawal}).drawn;
  assert.deepEqual([0,.5,1].map(count),[3,2,1]);
});

test('entering cohorts exchange visibility with departing cohorts at the same rank', () => {
  const rank = 93, threshold = (rank + .5) / coverage.bins;
  const entering = Float32Array.of(coverage.pack(rank, true) + 16384 + 8192 + 11)[0];
  const departing = coverage.pack(rank);
  assert.equal(entering & 32767, 16384 + 8192 + 11);
  assert.equal(coverage.visible(entering, 0), false);
  assert.equal(coverage.visible(entering, threshold - 1e-6), false);
  assert.equal(coverage.visible(entering, threshold), true);
  assert.equal(coverage.visible(departing, threshold), false);
  assert.equal(coverage.visible(coverage.pack(127, true), 1), true);
  const builder = makeBuilder(62, [0, 0xec954d]);
  builder.dab(0, 1, 0, [0,0,1], [1,0,0], .34, .4, .025, builder.P[1], 3,
    {coverage: rank, coverageEnter: true});
  const world = builder.finish({cam:{target:[0,1,0],yaw:0,pitch:.2,dist:9},detail:12});
  const count = sampleWithdrawal => render(world,{w:160,h:90,px:1,raw:true,samples:true,sampleWithdrawal}).drawn;
  assert.deepEqual([0,.5,1].map(count),[0,0,1]);
});

test('whole template parts retain their buried samples while other solids still clip the instance', () => {
  const builder = makeBuilder(12,[0,0xc09778,0x48615b]), sculpt = makeSculpt(builder);
  const tpl = sculpt.template(local => {
    local.ball([0,0,0], 1, {r:[2]}, {res:.16});
    local.tube([[0,-.9,0],[0,.9,0]], .14, .08, {r:[1]}, {res:.09,whole:true});
  });
  assert.equal(builder.count(),0);
  assert(tpl.samples.some(q => q[9] && Math.abs(q[1]) < .2));
  sculpt.ball([0,.44,0], .23, {r:[2]}, {res:.10});
  sculpt.place(tpl,[0,0,0]);
  sculpt.bake();
  const world=builder.finish();
  const [r,g,b]=builder.P[1], color=r+g*256+b*65536;
  const bark=[];
  for(let i=0;i<world.count;i++) if(world.data[i*16+7]===color) bark.push(world.data[i*16+1]);
  assert(bark.some(y=>Math.abs(y)<.12));
  assert(!bark.some(y=>Math.abs(y-.44)<.09));
});

test('optional template layers retain their local field and samples but keep the instance proxy clear',()=>{
  const builder=makeBuilder(12,[0,0xc09778,0x48615b]), sculpt=makeSculpt(builder);
  const tpl=sculpt.template(local=>{
    local.ball([0,0,0],.23,{r:[1]},{res:.08});
    local.ball([0,1.2,0],.49,{r:[2],omitFromProxy:true},{res:.1});
  });
  assert(tpl.sdf(0,1.2,0)<0);
  assert(tpl.proxySdf(0,1.2,0)>0);
  assert(tpl.samples.some(q=>q[1]>1));
  sculpt.place(tpl,[1,0,0]);
  sculpt.bake();
  assert(sculpt.sdf(1,0,0)<0);
  assert(sculpt.sdf(1,1.2,0)>0);
});

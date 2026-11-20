const test=require('node:test');
const assert=require('node:assert/strict');
const { inputActions }=require('..').load().KIT.procedural;

test('the same physical control has independent semantic actions across contexts',()=>{
  const edit={select:['key:Enter','pad:South'], undo:['key:KeyZ']};
  const map=inputActions.compile({edit, menu:{confirm:['key:Enter','pad:South'],back:['pad:East']}});
  edit.select.fill('key:KeyK');
  assert.deepEqual(map.resolve('edit','pad:South'),{action:'select',value:1});
  assert.deepEqual(map.resolve('menu','pad:South'),{action:'confirm',value:1});
  assert.equal(map.resolve('menu','key:KeyZ'),null);
  assert.equal(map.bindings('edit','select')[0].input,'key:Enter');
  assert.throws(()=>map.resolve('unknown','pad:South'),/Unknown/);
  assert.throws(()=>inputActions.compile({edit:{select:['key:Enter'],undo:['key:Enter']}}),/already/);
});

test('independent devices combine without dead-zone drift or doubling the same action',()=>{
  const map=inputActions.compile({edit:{
    rotate:[{input:'pad:RightX',deadZone:.25,scale:-1},'key:ArrowLeft'],
    pan:['pad:LeftX']
  }});
  const centered={'pad:RightX':.18,'pad:LeftX':0};
  assert.deepEqual(map.sample('edit',[centered]),{rotate:0,pan:0});
  assert.deepEqual(map.sample('edit',[{'pad:RightX':-.625,'pad:LeftX':-.3}]),{rotate:.5,pan:-.3});
  assert.deepEqual(map.sample('edit',[{'pad:RightX':-.625},{'key:ArrowLeft':1},{'key:ArrowLeft':1}]),{rotate:1,pan:0});
  assert.deepEqual(map.sample('edit',[]),{rotate:0,pan:0});
  assert.throws(()=>map.resolve('edit','pad:RightX',2),/Input values/);
});

test('modifier combinations are exact, order independent and scoped to their context',()=>{
  const modifiers=['Shift','Alt'];
  const binding={input:'key:KeyX',modifiers,scale:.5};
  const map=inputActions.compile({
    edit:{focus:[binding,'mouse:Right'],inspect:['key:KeyX']},
    menu:{confirm:[binding]}
  });
  modifiers.pop();
  assert.deepEqual(map.resolve('edit','key:KeyX',1,['Alt','Shift']),{action:'focus',value:.5});
  assert.equal(map.resolve('menu','key:KeyX',1,['Shift','Alt']).action,'confirm');
  assert.equal(map.resolve('edit','key:KeyX',1,['Shift']),null);
  assert.equal(map.resolve('edit','key:KeyX',1,['Alt','Control','Shift']),null);
  assert.equal(map.resolve('edit','key:KeyX').action,'inspect');
  assert.equal(map.resolve('edit','mouse:Right').action,'focus');
  assert.deepEqual(map.sample('edit',[{'key:KeyX':1}]),{focus:0,inspect:1});
  assert(Object.isFrozen(map.bindings('edit','focus')[0].modifiers));
  assert.throws(()=>inputActions.compile({edit:{
    first:[{...binding,modifiers:['Alt','Shift']}], second:[{...binding,modifiers:['Shift','Alt']}]
  }}),/already/);
  assert.throws(()=>map.resolve('edit','key:KeyX',1,['Shift','Shift']),/Invalid input modifiers/);
});

test('radial pairs keep headings, reject drift, and cap travel on diagonals',()=>{
  const {radial}=inputActions;
  assert.deepEqual(radial(.09,-.14,.2),[0,0]);
  const near=(value,target)=>assert(Math.abs(value-target)<1e-9);
  near(radial(0,-.6,.2)[1],-.5);
  const [x,y]=radial(.3,.4,.2);
  near(x/y,.75);
  near(Math.hypot(x,y),.375);
  near(Math.hypot(...radial(-1,1,.2)),1);
  assert.throws(()=>radial(NaN,0),/Radial input/);
  assert.throws(()=>radial(0,1,1),/Radial input/);
});

test('control permutations swap owners and persist only changed assignments',()=>{
  const slots=['pad:South','pad:East','pad:LeftTrigger'];
  const defaults=inputActions.permutation(slots);
  const first=defaults.swap('pad:LeftTrigger','pad:South');
  const second=first.swap('pad:East','pad:South');
  assert.deepEqual(defaults.overrides,{});
  assert.deepEqual(first.overrides,{'pad:LeftTrigger':'pad:South','pad:South':'pad:LeftTrigger'});
  assert.deepEqual(second.overrides,{'pad:LeftTrigger':'pad:East','pad:South':'pad:LeftTrigger','pad:East':'pad:South'});
  assert.deepEqual(first.swap('pad:LeftTrigger','pad:LeftTrigger').overrides,{});
  const restored=inputActions.permutation(slots,JSON.parse(JSON.stringify(second.overrides)));
  assert.equal(restored.remap('key:Enter'),'key:Enter');
  assert.equal(restored.remap('pad:RightX'),'pad:RightX');
  const map=inputActions.compile({
    edit:{pick:[restored.remap('pad:South')],grab:[restored.remap('pad:LeftTrigger')]},
    menu:{confirm:[restored.remap('pad:South'),'key:Enter'],back:[restored.remap('pad:East')]}
  });
  assert.equal(map.resolve('edit','pad:East').action,'grab');
  assert.equal(map.resolve('menu','pad:LeftTrigger').action,'confirm');
  assert.equal(map.resolve('menu','key:Enter').action,'confirm');
  assert.throws(()=>inputActions.permutation(slots,{'pad:South':'pad:East'}),/unique assignment/);
  assert.throws(()=>inputActions.permutation(slots,{'pad:South':'wheel:Up'}),/Unknown control/);
  assert.throws(()=>inputActions.permutation(['pad:South','pad:South']),/distinct controls/);
  assert.throws(()=>inputActions.permutation(Array(1)),/distinct controls/);
  assert.throws(()=>restored.swap('pad:North','pad:South'),/Unknown control/);
});

test('axis mapping projects each device simultaneously and preserves logical inversion across swaps',()=>{
  const slots=['pad:LeftX','pad:LeftY','pad:RightX','pad:RightY'];
  const original=inputActions.axisMapping(slots);
  const remapped=original.invert('pad:RightY').swap('pad:RightY','pad:LeftX');
  const raw={'pad:LeftX':.4,'pad:RightY':-.8,'pad:South':1};
  assert.deepEqual(remapped.project(raw),{
    'pad:LeftX':-.8,'pad:LeftY':0,'pad:RightX':0,'pad:RightY':-.4,'pad:South':1
  });
  assert.deepEqual(raw,{'pad:LeftX':.4,'pad:RightY':-.8,'pad:South':1});
  assert.equal(original.project(raw)['pad:RightY'],-.8);
  const {overrides,inverted}=remapped;
  const restored=inputActions.axisMapping(slots,JSON.parse(JSON.stringify({overrides,inverted})));
  slots.reverse();
  assert.deepEqual(restored.project(raw),remapped.project(raw));
  assert.equal(restored.invert('pad:RightY',false).project(raw)['pad:RightY'],.4);
  assert.deepEqual(restored.project({}),{'pad:LeftX':0,'pad:LeftY':0,'pad:RightX':0,'pad:RightY':0});
  assert.throws(()=>restored.project({'pad:LeftX':1.1}),/Axis values/);
  assert.throws(()=>restored.invert('pad:South'),/Unknown axis/);
  assert.throws(()=>inputActions.axisMapping(slots,{inverted:['pad:RightY','pad:RightY']}),/distinct inverted axes/);
});

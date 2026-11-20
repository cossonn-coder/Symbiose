const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('..');
const { KIT: K, makeBuilder } = ink.load();

const names = ['cirrus','coastal-stratus','cumulus','storm-front'];
const bounds = { min:[-24,-24], max:[24,24] };
const descriptor = { seed:19, bounds, resolution:[64,64], shape:{ scale:6 } };
const sites = Array.from({ length:19*19 }, (_,i)=>[(i%19-9)*2, (Math.floor(i/19)-9)*2]);
const grid = field => {
  const frame=field.frame(0);
  return sites.map(([x,z])=>frame.coverage(x,z));
};
const tune = (recipe, extra={}) => K.clouds.recipe(recipe,{ ...descriptor, ...extra });
const close = (value, expected) =>
  assert(Math.abs(value-expected)<1e-10, value+' vs '+expected);

test('cloud recipes are seeded, distinct and configurable through a serializable descriptor', () => {
  assert.deepEqual(K.clouds.recipes,names);
  const fingerprints = new Set();
  for (const recipe of names) {
    const current = grid(tune(recipe));
    const baked = K.clouds.compile(JSON.parse(JSON.stringify({ ...descriptor, recipe })));
    assert.deepEqual(current,grid(baked));
    assert(current.some(n=>n>.15) && current.some(n=>n<.05));
    fingerprints.add(current.join());
    assert.notDeepEqual(current,grid(tune(recipe,{seed:12})));
    assert.notDeepEqual(grid(tune(recipe,{edgeBreakup:0})),grid(tune(recipe,{edgeBreakup:1})));
    assert.notDeepEqual(current,grid(tune(recipe,{shape:{ scale:7, stretch:2.8, heading:1.2, center:[1,3] }})));
    assert(grid(tune(recipe,{coverage:0})).every(n=>n===0));
    const named = K.clouds.compile(recipe);
    assert(named.frame(0).visible);
    assert.equal(K.clouds.compile(recipe),named);
  }
  assert.equal(fingerprints.size,names.length);
  assert.throws(()=>K.clouds.compile('unknown'), /Unknown cloud recipe/);
  for (const change of [{ edgeBreakup:2 },{ coverage:[1,0] },{ shape:{stretch:0} },
    { lighting:{rim:2} },{ thickness:-1 },{ shape:{center:[2,Infinity]}},{ steps:1 }])
    assert.throws(()=>tune('cumulus',change), /Cloud/);
});

test('recipe drift and shared wind advect the same coverage used by the projected shadows', () => {
  const field = tune('coastal-stratus',{velocity:[2,-1],height:6});
  const casts = K.clouds.shadowSettings({ direction:[0,1,0],strength:1,softness:0 });
  const fixed = field.frame(0,casts), moved = field.frame(2,casts,undefined,[3,4]);
  for (const [x,z] of sites) {
    const cover=fixed.coverage(x,z);
    close(moved.coverage(x+7,z+2),cover);
    close(moved.shadow(x+7,0,z+2),1-cover);
    assert.equal(moved.shadow(x+7,7,z+2),1);
  }
});

test('a thick recipe paints through its vertical extent, with controllable light and lightning', () => {
  const options={...descriptor,height:8,thickness:5,coverage:1,color:'#48556d',opacity:1,
    shape:{scale:6,stretch:1}};
  const flat = K.clouds.recipe('coastal-stratus',{ ...options, thickness:0,lighting:false }).frame(0);
  const cloud = K.clouds.recipe('coastal-stratus',{...options,lighting:false}).frame(0);
  const lit = K.clouds.recipe('coastal-stratus',{ ...options,
    lighting:{color:'#fff3cc',ambient:1,strength:0,rim:0} }).frame(0);
  const [x,z] = sites.find(([x,z])=>cloud.coverage(x,z)>.85);
  const origin = [x,7,z], direction = [1,0,0], clear = [0,0,0];
  assert.deepEqual(flat.paint(origin,direction,clear.slice()), clear);
  assert(cloud.paint(origin,direction,clear.slice())[0]>.10);
  assert.deepEqual(cloud.paint([x,11,z],direction,clear.slice()),clear);
  assert(lit.paint(origin,direction,clear.slice())[0]>cloud.paint(origin,direction,clear.slice())[0]+.18);
  let struck=0;
  const flash=cloud.paint([x,0,z],[0,1,0],clear.slice(),(_x,y)=>{
    assert(y>=5.5 && y<=10.5);
    struck++;
    return [.6,.3,.5];
  });
  assert(struck>1);
  assert(flash[0]>cloud.paint([x,0,z],[0,1,0],clear.slice())[0]+.2);
});

test('a recipe can replace or disable a cloud field on the standard render path', () => {
  const B=makeBuilder(4,[0x355878]);
  const cloudField=tune('coastal-stratus',{height:3,thickness:1.5,coverage:1});
  const world=B.finish({
    cloudField, cam:{ target:[0,0,0],dist:6,pitch:-.21,yaw:0,sway:0 },
    skyEnvironment:{ defaults:{ zenith:'#347fb8',horizon:'#bbd7ed', ground:'#4f697f',sunStrength:0 } }
  });
  for (const ortho of [false,true]) {
    const view={ortho,w:82,h:60,px:1,t:0,raw:true};
    const withClouds=ink.render(world,view), clear=ink.render(world,{...view,cloudField:false});
    const story=ink.render(world,{...view,cloudField:{...descriptor,height:3,recipe:'storm-front'}});
    assert(withClouds.rgb.some((value,index)=>Math.abs(value-clear.rgb[index])>30));
    assert(story.rgb.some((value,index)=>Math.abs(value-withClouds.rgb[index])>30));
  }
});

const test = require('node:test');
const assert = require('node:assert/strict');
const ink = require('..');
const {KIT:K,makeBuilder,ContributionRules:R} = ink.load();

function layered(extinction=[.5,.5,.5]) {
  const B=makeBuilder(13,[0x181d24,0xcc8048,0x527f31,0x4ec8d2]);
  function disc(z,alpha,slot,object,material,flags) {
    const i=B.count();
    B.disc(0,0,z,[0,0,1],.45,.025,B.P[slot],alpha,flags);
    B.describeSplats(i,i+1,{object,material});
  }
  disc(-.65,3,1,'statue','stone');
  disc(.1,.3,2,'ivy','foliage',{nd:true});
  disc(.65,.4,3,'pane','glass',{nd:true,gl:true});
  const {waterBodies}=K.procedural;
  const water=waterBodies.scene([waterBodies.create({id:'tank',bounds:{min:[-1,-.5],max:[1,.5]},
    resolution:[2,4],sample:()=>({bed:-1,surface:.5}),
    optics:{extinction}})]);
  return B.finish({water,splatIds:['statue/0','ivy/0','pane/0']});
}

test('picking preserves glass, water, foliage and a solid receiver on one ray', () => {
  const world=layered(), ray={origin:[0,0,2],direction:[0,0,-20],maxDistance:4};
  const picker=ink.createSplatPicker(world), result=picker.ray(ray);
  assert.deepEqual(result.contributions.map(h=>[h.kind,h.id]),
    [['glass','pane/0'],['water','tank'],['splat','ivy/0'],['water','tank'],['splat','statue/0']]);
  assert.equal(result.solid.target.entity,'statue');
  assert(result.transmission>0 && result.transmission<.01);
  assert(Math.abs(result.contributions[0].alpha-.4)<1e-6);
  assert(Math.abs(result.contributions[1].transmissionBefore-.6)<1e-6);
  assert(Math.abs(result.contributions.reduce((n,h)=>n+h.weight,0)+result.transmission-1)<1e-9);
  assert.deepEqual(K.world.query.fromScene(world).trace('world/contributions',ray.origin,ray).value,result);
  assert.equal(picker.ray({...ray,limit:2}).truncated,true);
  assert.equal(picker.ray({...ray,water:false}).contributions.filter(h=>h.kind==='water').length,0);
  assert.equal(picker.ray({...ray,origin:[2,0,2]}).dominant,null);
});

test('picking reports clear media intervals and keeps their transmission',()=>{
  const ray={origin:[0,0,2],direction:[0,0,-1],maxDistance:4};
  const result=ink.createSplatPicker(layered([0,0,0])).ray(ray);
  assert(result.media.some(interval=>interval.id==='tank'&&interval.exit>interval.distance));
  assert.equal(result.contributions.some(layer=>layer.kind==='water'),false);
});

test('ray reduction preserves colored extinction over multiple intervals',()=>{
  const a=R.reduce([{alpha:.45,transmissionRGB:[0,1,0]},{alpha:.7,transmissionRGB:[1,0,0]}],0);
  assert.equal(a.transmission,0);
  assert.deepEqual(a.transmissionRGB,[0,0,0]);
  assert(Math.abs(a.contributions[0].weight-.45)<1e-9);
});

test('native ray queries prune samples outside the ray and respect animation time',()=>{
  const B=makeBuilder(2,[0,0xffffff]);
  for(let i=0;i<4096;i++)B.iso((i%64)*.5,0,Math.floor(i/64)*-.5,.07,B.P[1],1);
  B.iso(0,1,1,.09,B.P[1],1,{k:6,ph:0,sp:1,rg:1});
  const world=B.finish(),ray={origin:[0,2,3],direction:[0,0,-1],maxDistance:5};
  const still=ink.createSplatPicker(world).ray(ray);
  const moved=ink.createSplatPicker(world,{time:Math.PI/2}).ray(ray);
  assert.equal(still.dominant,null);
  assert.equal(moved.dominant.index,4096);
  assert(moved.visited<32);
});

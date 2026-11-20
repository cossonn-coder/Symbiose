const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('../index.js');

const kit = ink.load(), { KIT: K, makeBuilder } = kit;
const camera = {target:[0,0,0],dist:8,yaw:0,pitch:0};
const view = {w:48,h:40,px:1,raw:true};

test('opt-in frame budgets count blended fragments and internal raster passes without changing pixels',()=>{
  const B = makeBuilder(2,[0x152235,0xb4a875,0x869cb2]);
  B.disc(0,0,0,[0,0,1],.64,.034,B.P[1],3);
  B.disc(0,0,.5,[0,0,1],.40,.022,B.P[2],.32,{nd:true});
  const world = B.finish({cam:camera});
  const options = {...view,raw:false,colored:true,splatOrder:'surface'};
  const plain = ink.render(world,options);
  const profiled = ink.render(world,{...options,renderStats:true});
  assert.deepEqual(profiled.rgb,plain.rgb);
  assert.equal(plain.renderStats,undefined);
  const stats = profiled.renderStats;
  assert(Number.isFinite(stats.frameMs) && stats.frameMs>=0);
  assert(stats.rasterPasses>1);
  assert(stats.fragments>stats.translucentFragments && stats.translucentFragments>0);
  assert(stats.peakDeferredFragments>0 && stats.deferredFlushes>0);
  assert.equal(stats.volume.densitySamples,0);
});

test('cached fog bounds and full paths preserve jitter, focus protection, clouds and water',()=>{
  const B = makeBuilder(9,[0x192538,0xcb905f,0x9cb4b9]);
  for (const z of [-3,-2,-1.0,1.3]) {
    const first=B.count();
    B.disc(0,0,z,[0,0,1],.8,.025,B.P[z===-2 ? 1 : 2],z===-2 ? 3 : .38,{nd:z!==-2});
    if (z===-2) B.describeSplats(first,B.count(),{object:'protected'});
  }
  const field = K.procedural.density.bounded({bounds:{min:[-2,-2,-.25],max:[2,2,1]},
    sample:(x,y,z)=>.4+.3*Math.sin(12*z-x+y)});
  const cloud = K.clouds.asset({bounds:{min:[-2,-4],max:[2,-2]},height:1,thickness:1.2,coverage:()=>.6},
    {resolution:16});
  const waterBodies = K.procedural.waterBodies;
  const water = waterBodies.scene([waterBodies.create({id:'half',bounds:{min:[0,.21],max:[2,.7]},
    sample:()=>({bed:-.8,surface:.8})})]);
  const world = B.finish({cam:camera,cloudField:cloud,cloudRepresentation:'card',water,
    atmosphere:[K.atmosphere.field({field,color:'#85a5bf',density:.65,step:.14,lit:false})]});
  const options = {...view,passes:['environment'],renderStats:true, volumeQuality:{samples:3,jitter:'blue-noise'},
    silhouetteProtection:{targets:[{select:{object:'protected'},fogScale:.45}]}};
  const cached = ink.render(world,options);
  const uncached = ink.render(world,{...options,volumeQuality:{...options.volumeQuality,cacheBounds:false}});
  assert.deepEqual(cached.rgb,uncached.rgb);
  assert.deepEqual(cached.passes,uncached.passes);
  const before=uncached.renderStats.volume, after=cached.renderStats.volume;
  assert(after.boundsTests<before.boundsTests*.5);
  assert(after.densitySamples<before.densitySamples);
  assert(after.boundsCacheHits>0 && after.fullFogCacheHits>0 && after.emptyFogIntervals>0);
});

test('the sparse march skips proven empty grid steps and produces the same fog',()=>{
  const B = makeBuilder(4,[0x182740]);
  const density = K.procedural.density;
  const field = density.sparse(density.fromSdf({
    bounds:{min:[-4,-4,-4],max:[4,4,4]},field:(x,y,z)=>Math.hypot(x,y,z)-.9
  }),{resolution:[32,32,32],brick:4});
  const world = B.finish({cam:camera,atmosphere:[K.atmosphere.field({field,step:.12,density:.55,lit:false})]});
  const options = {...view,renderStats:true};
  const skipped = ink.render(world,options);
  const dense = ink.render(world,{...options,volumeQuality:{skip:false}});
  assert.deepEqual(skipped.rgb,dense.rgb);
  assert(skipped.renderStats.volume.skippedSteps>0 && dense.renderStats.volume.skippedSteps===0);
  assert(skipped.renderStats.volume.densitySamples<dense.renderStats.volume.densitySamples*.5);
  assert(skipped.renderStats.volume.marchSteps<dense.renderStats.volume.marchSteps*.65);
});

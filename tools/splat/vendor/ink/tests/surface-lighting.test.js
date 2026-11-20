const test=require('node:test');
const assert=require('node:assert/strict');
const {surfaceLighting}=require('..').load().KIT.procedural;

test('surface overrides use attributed light and keep the caller palette separate',()=>{
  const raw={albedo:[.9,.8,.5],fallback:.4,background:[.7,.7,.7]};
  const style=surfaceLighting.override(raw);
  raw.albedo[0]=0;
  assert(Object.isFrozen(style.albedo));
  assert.deepEqual(surfaceLighting.shade(0,style),[0,0,0]);
  assert.deepEqual(surfaceLighting.shade(1,style),[.9,.8,.5]);
  assert.deepEqual(surfaceLighting.shade(2,style),[1,1,.75]);
  surfaceLighting.shade(undefined,style).forEach((value,i)=>assert.equal(value,style.albedo[i]*.4));
  assert.deepEqual(style.background,[.7,.7,.7]);
});

test('surface overrides reject invalid material envelopes and irradiance',()=>{
  for(const value of [null,[],{texture:'brick'},{albedo:[2,0,0]},
    {fallback:-.1},{fallback:3},{background:[0,0,NaN]}])
    assert.throws(()=>surfaceLighting.override(value),/surface lighting/i);
  assert.throws(()=>surfaceLighting.shade(Infinity),/irradiance/);
});

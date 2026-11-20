const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT:K}=require('..').load();
const {motion}=K.procedural;
const sum=a=>a.reduce((x,y)=>x+y,0);

test('a cover field blocks local rain and accumulated snow without changing thermal shelter',()=>{
  const {overheadCover}=K.procedural;
  const field=overheadCover.rasterize({surfaces:[{min:[0,0],max:[2,2],heightAt:()=>1}]});
  const weather=motion.surfaceWeather({width:8,height:4,cell:.5,initial:()=>({temperature:-4}),
    maxRunoff:0,freezeRate:0,wetDiffusion:0,heatDiffusion:0,evaporation:0});
  const forcing=(x,z)=>({air:-4,rain:.2,snowfall:.3,shelter:.5,
    precipitationExposure:overheadCover.exposure(field,[x,0,z])});
  const next=weather.step(1,{forcing}), dry=next.sample(1,1), open=next.sample(3,1);
  assert.equal(dry.wetness,0);
  assert.equal(dry.snow,0);
  assert(open.wetness>.19&&open.snow>.2);
  assert.equal(dry.temperature,open.temperature);
  assert.throws(()=>weather.step(1,{forcing:()=>({precipitationExposure:2})}),/forcing values/);
  assert.deepEqual(weather.snapshot().snow,next.snow);
});

test('surface temperature separates sheltered frost from warm wetness, then thaws and dries',()=>{
  const w=motion.surfaceWeather({width:19,height:10,cell:0.13,origin:[-1.235,-0.65],
    initial:()=>({wetness:0.27,temperature:-4}),maxRunoff:0,heatDiffusion:0.003});
  const first=w.step(2.1,{forcing:x=>({air:x<0?-7:17,light:x<0?0.03:0.81,snowfall:0.27,shelter:x<0?0.4:0})}),
    cold=first.sample(-0.9,0), warm=first.sample(0.9,0);
  assert(cold.temperature<-4&&warm.temperature>10);
  assert(cold.snow>0.3&&cold.frost>0.2);
  assert(warm.snow===0&&warm.frost===0&&warm.wetness>0.4);
  assert(warm.exposure>cold.exposure+1);
  const second=w.step(3.3,{forcing:()=>({air:18,light:0.9,humidity:0.3})});
  assert.equal(second.sample(-0.9,0).snow,0);
  assert.equal(second.sample(-0.9,0).frost,0);
  assert(second.sample(-0.9,0).wetness>cold.wetness);
  assert(second.sample(0.9,0).wetness<warm.wetness);
  assert(second.sample(0.9,0).exposure>warm.exposure);
});

test('weather transports wetness downslope without leaking through closed cells or failed advances',()=>{
  const weather=motion.surfaceWeather({width:24,height:9,cell:0.1,mask:x=>Math.abs(x-1.35)>0.02,
    initial:x=>({wetness:x>0.35&&x<0.65?0.49:0}),maxRunoff:0.4,
    heatDiffusion:0,wetDiffusion:0.003,evaporation:0});
  const before=weather.snapshot(), after=weather.step(0.85,{forcing:()=>({runoff:[0.32,0]})});
  assert(Math.abs(sum(after.wetness)-sum(before.wetness))<1e-8);
  assert(after.sample(0.83,0.43).wetness>0.06);
  assert(after.sample(1.65,0.43).wetness===0);
  assert.equal(after.sample(1.35,0.43),null);
  assert.throws(()=>weather.step(0.5,{forcing:()=>({snowfall:NaN})}),/forcing values/);
  assert.deepEqual(weather.snapshot().wetness,after.wetness);
});

test('material events advance individual retained states in order and can resume from a snapshot',()=>{
  const spec={initial:'dry',states:{
    dry:{shade:'sand'},wet:{shade:'blue'},muddy:{shade:'umber'},cracked:{shade:'pale'}
  },transitions:[
    {id:'wetting',from:'dry',event:'rain',to:'wet',when:e=>e.payload.depth>0.12},
    {id:'tracked',from:'wet',event:'footfall',to:'muddy',patch:{compacted:true}},
    {id:'baked',from:'muddy',event:'sun',to:'cracked',minAge:0.8}
  ]}, controller=motion.materialStateGraph(spec,[{id:'court'},{id:'sheltered'}]),
    first=controller.advance(2,[
      {at:1.2,type:'footfall',target:'court'},
      {at:0.1,type:'rain',target:'court',payload:{depth:0.21}},
      {at:1.45,type:'sun',target:'court'}
    ]);
  assert.deepEqual(first.changes.map(c=>c.to),['wet','muddy']);
  assert.equal(controller.get('court').state,'muddy');
  assert.equal(controller.get('sheltered').state,'dry');
  const copy=motion.materialStateGraph(spec,first.entities,{time:2}), after=copy.dispatch('sun',{target:'court',at:2.2});
  assert.deepEqual(after.changes.map(c=>c.to),['cracked']);
  assert.equal(copy.get('court').material.shade,'pale');
  assert.equal(copy.get('court').data.compacted,true);
  assert.equal(copy.get('court').revision,3);
});

test('a material graph budget cannot partially publish a broadcast',()=>{
  const machine={initial:'dry',states:{dry:{},wet:{}},transitions:[
    {id:'rain',from:'dry',event:'wet',to:'wet'}
  ]}, engine=motion.materialStateGraph(machine,[{id:'a'},{id:'b'}],{maxChecks:3}), saved=engine.snapshot();
  assert.throws(()=>engine.dispatch('wet',{at:1}),/budget/);
  assert.deepEqual(engine.snapshot(),saved);
});

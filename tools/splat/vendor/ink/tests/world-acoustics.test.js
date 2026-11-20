const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT:{world:W}}=require('..').load();
const example=require('../examples/world-acoustic-hatch.json');
const shelter=require('../examples/world-ventilated-shelter.json');
const listener={entity:'listen-post'}, beacon={entity:'beacon',socket:'speaker'};
const compare=(a,b)=>assert(Math.abs(a-b)<1e-8,`${a} != ${b}`);
const read=(query,to=listener,options={})=>query.probe('acoustics/audible',to,{from:beacon,...options}).value;
const trace=(query,to=listener,options={})=>query.trace('acoustics/path',to,{from:beacon,...options}).value;

test('a live hatch controls acoustic gain, muffling and an agent decision using the same field',()=>{
  const run=W.runtime.create(example), before=run.query();
  const opened=read(before), detail=trace(before);
  assert.equal(opened.audible,true);
  assert.equal(detail.path.openings[0].fraction,1);
  assert.deepEqual(detail.path.rooms,['machine-room','hall']);
  assert.deepEqual(detail.path.openings.map(row=>[row.from,row.to]),[['machine-room','hall']]);
  assert.deepEqual(opened.direction,[1,0,0]);
  compare(opened.distanceMeters,4.7);
  compare(opened.delaySeconds,4.7/343);
  compare(opened.levelDb,60-20*Math.log10(4.7)-.35-4.7*.008);
  const reverse=read(before,beacon,{from:listener});
  assert.deepEqual(reverse.direction,[-1,0,0]);
  compare(reverse.gain,opened.gain);
  run.advance(8);
  const shut=trace(run.query());
  assert.equal(shut.path.openings[0].fraction,0);
  assert.equal(shut.audible,false);
  assert(shut.bands.high.gain<shut.bands.low.gain*.03);
  assert(shut.muffleDb>30);
  assert.deepEqual(read(before),opened);
  run.advance(16);
  assert.deepEqual(read(run.query()),opened);
  const choices=run.history.filter(row=>row.kind==='activity-selected').map(row=>row.choice.activity);
  assert.deepEqual(choices,['inspect','standby','inspect']);
  assert.deepEqual(W.runtime.replay(JSON.parse(JSON.stringify(run.recording()))).checkpoint(),run.checkpoint());
});

test('portal search picks an audible alternate route and reports a sealed frontier',()=>{
  const air=example.systems.air;
  const world={...example,systems:{air:{...air,config:{...air.config,openings:{
    ...air.config.openings, bypass:{from:'hall',to:'machine-room',at:[0,1,1.5],opening:.6}
  }}},acoustics:{kind:'acoustics',config:{layout:'air/acoustic-layout',
    openings:{hatch:{sealed:true},bypass:{sealed:true,openLossDb:[2,3,5]}}}}},commands:[
    example.commands[0],
    {tick:10,action:'world/input',args:{port:'air/opening.bypass',value:0}}
  ]};
  const run=W.runtime.create(world);
  const direct=trace(run.query());
  assert.equal(direct.path.openings[0].id,'hatch');
  run.advance(6);
  const around=trace(run.query());
  assert.equal(around.path.openings[0].id,'bypass');
  assert(around.distanceMeters>direct.distanceMeters);
  assert(around.direction[2]>.5);
  assert.equal(around.apparentSource[2],1.5);
  assert.equal(around.path.segments[1].from[2],1.5);
  run.advance(10);
  const blocked=trace(run.query());
  assert.equal(blocked.status,'blocked');
  assert.equal(blocked.audible,false);
  assert.equal(blocked.gain,0);
  assert.deepEqual(blocked.blockedOpenings.map(row=>[row.id,row.reason]),[['bypass','sealed'],['hatch','sealed']]);
});

test('a physical slider gate changes acoustic transmission through the ventilation adapter',()=>{
  const acoustic={kind:'acoustics',config:{layout:'air/acoustic-layout'}};
  const run=W.runtime.create({...shelter,systems:{...shelter.systems,acoustics:acoustic}});
  const options={from:[1,1,.14]};
  assert.equal(trace(run.query(),[-1,1,.14],options).path.openings[0].fraction,0);
  run.advance(39);
  const open=trace(run.query(),[-1,1,.14],options);
  assert.equal(open.path.openings[0].id,'door');
  assert.equal(open.path.openings[0].fraction,1);
});

test('cached multihop mix totals agree with the ordered path and pan from the last doorway',()=>{
  const room=x=>({bounds:{min:[x,0,-3],max:[x+4,3,3]}});
  const run=W.runtime.create({systems:{air:{kind:'ventilation',config:{
    rooms:{a:room(0),b:room(4),c:room(8)},openings:{
      first:{from:'a',to:'b',at:[4,1,-2]},last:{from:'b',to:'c',at:[8,1,2]}
    }
  }},acoustics:{kind:'acoustics',config:{layout:'air/acoustic-layout'}}}});
  const to=[10,1,0], query=run.query();
  for(const from of [[2,1,0],[3,2,-2]]){
    const summary=read(query,to,{from}), detail=trace(query,to,{from});
    const {path,...mix}=detail;
    assert.deepEqual(mix,summary);
    assert.deepEqual(path.rooms,['a','b','c']);
    assert.deepEqual(path.openings.map(row=>row.id),['first','last']);
    assert.equal(mix.apparentSource[2],2);
    compare(mix.distanceMeters,path.segments.reduce((length,row)=>length+row.distanceMeters,0));
    compare(mix.bands.high.lossDb,mix.distanceLossDb+path.segments.reduce((loss,row)=>loss+row.lossDb[2],0));
  }
});

const water={kind:'enclosed-water',config:{
  chambers:{pool:{bounds:{min:[1,0,-1],max:[3,4,1]},initial:8}}
}};
test('an enclosed water surface splits exact medium distance and adds interface loss',()=>{
  const run=W.runtime.create({systems:{wet:water,acoustics:{kind:'acoustics',config:{layout:'wet/acoustic-layout'}}}});
  const result=trace(run.query(),[2,3,0],{from:[2,1,0]});
  compare(result.distanceMeters,2);
  compare(result.delaySeconds,1/1480+1/343);
  compare(result.bands.mid.lossDb,20*Math.log10(2)+30+.02+.008);
  assert.deepEqual(result.path.segments[0].media,[{medium:'water',meters:1},{medium:'air',meters:1}]);
  assert.equal(result.path.openings.length,0);
  const alone=run.query().probe('acoustics/audible',[0,1,0],{from:[2,1,0]});
  assert.equal(alone.status,'outside');
});

test('water media from a second system clips the exact flooded span of a ventilation path',()=>{
  const run=W.runtime.create({systems:{wet:water,air:{kind:'ventilation',config:{
    rooms:{hall:{bounds:{min:[-1,0,-2],max:[5,4,2]}}}
  }},acoustics:{kind:'acoustics',config:{layout:'air/acoustic-layout',media:['wet/acoustic-layout']}}}});
  const result=trace(run.query(),[4,1,0],{from:[0,1,0]});
  const pieces=result.path.segments[0].media;
  assert.deepEqual(pieces.map(row=>row.medium),['air','water','air']);
  [1,2,1].forEach((n,i)=>compare(pieces[i].meters,n));
  compare(result.delaySeconds,2/1480+2/343);
});

test('surface-water columns muffle points below their surface and leave overhead paths in air',()=>{
  const run=W.runtime.create({systems:{fluid:{kind:'water',config:{width:4,height:4,cell:1,origin:[0,0],
    initial:[{bounds:{min:[0,0],max:[4,4]},value:2}]}},air:{kind:'ventilation',config:{
    rooms:{hall:{bounds:{min:[0,0,0],max:[4,4,4]}}}
  }},acoustics:{kind:'acoustics',config:{layout:'air/acoustic-layout',media:['fluid/water']}}}});
  const q=run.query();
  const low=trace(q,[3,1,1],{from:[1,1,1]}), high=trace(q,[3,3,1],{from:[1,3,1]});
  assert.deepEqual(low.path.segments[0].media,[{medium:'water',meters:2}]);
  assert.deepEqual(high.path.segments[0].media,[{medium:'air',meters:2}]);
  assert(low.delaySeconds<high.delaySeconds);
});

test('typed medium fields can block sound in vacuum without stale results after an edit',()=>{
  const world={systems:{air:{kind:'ventilation',config:{
    rooms:{hall:{bounds:{min:[0,0,0],max:[10,3,3]}}}
  }},media:{kind:'fields',config:{fields:{phase:{type:'category',categories:['air','vacuum'],default:'air'}}}},
  acoustics:{kind:'acoustics',config:{layout:'air/acoustic-layout',media:['media/phase']}}},
  commands:[{tick:2,action:'media/set',args:{field:'phase',
    region:{bounds:{min:[3,0,0],max:[7,3,3]},value:'vacuum'}}}]};
  const run=W.runtime.create(world), first=run.query(), args={from:[1,1,1]};
  assert.equal(read(first,[9,1,1],args).status,'audible');
  run.advance(2);
  assert.equal(read(run.query(),[9,1,1],args).status,'blocked');
  assert.equal(read(first,[9,1,1],args).status,'audible');
});

test('acoustic configuration and endpoints fail through query validation',()=>{
  const world=config=>({...example,systems:{...example.systems,acoustics:{kind:'acoustics',config}}});
  assert.throws(()=>W.runtime.validate(world({layout:'air/rooms'})),/room and opening layout/);
  assert.throws(()=>W.runtime.validate(world({layout:'air/acoustic-layout',openings:{missing:{sealed:true}}})),/Unknown acoustic opening/);
  assert.throws(()=>W.runtime.validate(world({layout:'air/acoustic-layout',media:['acoustics/audible']})),/Invalid acoustic medium/);
  const run=W.runtime.create(example);
  assert.equal(run.query().probe('acoustics/audible',listener,{from:{entity:'beacon',socket:'missing'}}).status,'missing');
  assert.throws(()=>read(run.query(),listener,{band:'ultrasound'}),/Invalid hearing query settings/);
});

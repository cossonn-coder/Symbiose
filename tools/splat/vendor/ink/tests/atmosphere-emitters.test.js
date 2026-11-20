const assert = require('node:assert/strict');
const test = require('node:test');
const ink = require('..');
const { KIT: K, makeBuilder, SceneOptics } = ink.load();
const emitters = K.atmosphere.emitters;
const cam = { target:[0,.3,0], dist:5, pitch:0, yaw:0 };
const point = {p:[0,0,0],dir:[0,1,0]};
const live = {rate:2,lifetime:[1,1],fadeIn:0,fadeOut:0};
const motion = {speed:0,wind:0,spread:0,gravity:[0,0,0]};
const descriptors = (sockets, list) => ({sockets,emitters:list});
const smoke = (socket, edits) => ({id:'puffs',preset:'smoke',socket,life:live,motion,style:{size:.28,growth:1,lit:false},...edits});
const spray = (socket, edits) => ({id:'drops',preset:'spray',socket,life:live,motion,style:{size:.07,growth:1},...edits});
function positions(frame) {
  const packed=frame.write(new Float32Array(frame.count*16)), rows=[];
  for (let i=0;i<frame.count;i++) if (packed[i*16+3]) rows.push([...packed.subarray(i*16,i*16+3)]);
  return rows;
}

test('socket-born particles sample keyed birth positions and age in world space when seeking', () => {
  const program=emitters.compile(descriptors({moving:{keys:[
    {at:0,...point},{at:2,p:[4,0,0],dir:point.dir}
  ]}},[spray('moving'),smoke('moving')]));
  const frame=program.frame(1.25);
  assert.deepEqual(positions(frame),[[1,0,0],[2,0,0]]);
  assert(frame.volumes[0].field.sample(1,0,0)>.7);
  assert(frame.volumes[0].field.sample(2,0,0)>.7);
  assert.equal(frame.volumes[0].field.sample(2.5,0,0),0);
  program.frame(16);
  assert.deepEqual(positions(program.frame(1.25)),positions(frame));
  assert.equal(program.frame(-1).volumes.length,0);
  const bounded=emitters.compile(descriptors({s:point},[spray('s',{life:{...live,end:1}})]));
  assert.equal(positions(bounded.frame(1.4)).length,2);
  assert.equal(positions(bounded.frame(2)).length,0);
});

test('all named presets share one source and wind transport moves released particles by age', () => {
  const program=emitters.compile(descriptors({s:point},emitters.presets.map(preset=>({
    id:preset,preset,socket:'s',life:live,motion:{...motion,wind:.5}
  }))));
  const steady=program.frame(1.25);
  const gust=program.frame(1.25,{travel:(_p,from,to)=>[2*(to-from),0]});
  assert.equal(steady.volumes.length,3);
  assert(steady.volumes.every(v=>v.field.sample(0,0,0)>0));
  assert.deepEqual(positions(steady),[[0,0,0],[0,0,0]]);
  assert.deepEqual(positions(gust),[[.75,0,0],[.25,0,0]]);
  assert.throws(()=>emitters.compile({emitters:[smoke('r',{life:{rate:1024}})]}),/particle budget/);
  assert.throws(()=>emitters.compile(descriptors({s:{p:[0,0,0],dir:[0,0,0]}},[])),/nonzero/);
  assert.throws(()=>emitters.compile({emitters:[smoke('r'),smoke('r')]}),/unique/);
});

test('stage emitters retain earlier positions and rotate their directions with the carrying part', () => {
  const B=makeBuilder(1,[0x121b22]), rig=K.rig(B,{});
  rig.part('boiler');
  const world=B.finish({cam,atmosphereEmitters:{emitters:[spray('stack',{motion:{...motion,speed:1}})]}});
  const stage=K.stage(world);
  rig.bind(stage);
  stage.socket('stack',[0,0,0],'boiler',[0,1,0]);
  stage.add({update(_dt,t) {
    rig.set('boiler',t>=1 ? [0,-1,0,1,0,0,0,0,1] : K.M.id(),[0,0,0],[3*t,0,0]);
  }});
  for (let i=0;i<=6;i++) stage.update(.25,i/4);
  const frame=world.atmosphereEmitters.frame(1.25,{socket:stage.atmosphereSocket});
  assert.deepEqual(positions(frame),[[1.5,.75,0],[2.75,0,0]]);
  const opts={w:83,h:61,px:1,raw:true,t:1.25};
  assert.notDeepEqual(ink.render(world,opts).rgb,ink.render(world,{...opts,atmosphereEmitters:false}).rgb);
});

test('simulation socket histories respect rotated axes and missing entities without moving old births', () => {
  const program=emitters.compile({emitters:[spray({entity:'mill',socket:'outlet',dir:[0,0,1]})]});
  const history=emitters.history(program.targets,program.lifetime);
  const query=point=>({frame:target=>target.entity==='mill' && point &&
    {point,rotation:[1,0,0,0,0,-1,0,1,0]}});
  history.capture(0,target=>emitters.entityPose(query([1,2,3]),target));
  history.capture(1,target=>emitters.entityPose(query([3,2,3]),target));
  history.capture(1.5,target=>emitters.entityPose(query(null),target));
  assert.deepEqual(history.at(program.targets[0],.5),{p:[2,2,3],dir:[0,-1,0]});
  assert.equal(history.at(program.targets[0],1.5),null);
  assert.deepEqual(positions(program.frame(1.6,{socket:history.at})),[[3,2,3]]);
});

test('emitted volumes use optical depth, and the switch independently hides both droplets and volumes', () => {
  const B=makeBuilder(1,[0x142235,0x3d686b]);
  B.disc(0,.3,0,[0,0,1],.32,.06,B.P[1],3);
  const source=descriptors({behind:{p:[0,.3,-1]}, drops:{p:[.7,.3,.5]}},[
    smoke('behind',{style:{size:.78,growth:1,density:4,lit:false}}),spray('drops')
  ]);
  const world=B.finish({cam,atmosphereEmitters:source});
  const opts={w:83,h:61,raw:true,t:.25,px:1};
  const off=ink.render(world,{...opts,atmosphereEmitters:false});
  const on=ink.render(world,opts);
  const droplets=ink.render(world,{...opts,atmosphere:false});
  assert(on.rgb.some((n,i)=>n!==droplets.rgb[i]),'a puff is visible around the foreground');
  assert(droplets.rgb.some((n,i)=>n!==off.rgb[i]),'droplets render when volumes are off');
  const center=(30*83+41)*3;
  assert(Math.abs(on.rgb[center]-off.rgb[center])<=6,'opaque foreground masks most of the puff');
  const volumes=SceneOptics.prepareVolumes(world.atmosphereEmitters.frame(.25).volumes,world.pal);
  assert.equal(SceneOptics.trace(volumes,[0,.3,5],[0,0,-1],5)[3],1);
  assert(SceneOptics.trace(volumes,[0,.3,5],[0,0,-1],6)[3]<.9);
});

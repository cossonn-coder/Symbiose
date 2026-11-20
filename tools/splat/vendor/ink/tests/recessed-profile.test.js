const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT } = require('..').load();
const P = KIT.procedural;

const outline = [[-1.2, -1.3], [1.3, -1.3], [1.8, 0], [1.1, 1.35], [-.9, 1.35], [-1.6, 0]];
const recess = [[-.2, -.8], [.2, -.8], [.2, -.25], [.65, -.25], [.65, .2], [.2, .2],
  [.2, .8], [-.2, .8], [-.2, .2], [-.65, .2], [-.65, -.25], [-.2, -.25]];
const spec = { outline, recess: recess.slice().reverse(), span: [-.9, .1], inset: .36 };

test('fitted exterior profiles keep separate spans while adding the required material',()=>{
  const outline=[[-.5,0],[.5,0],[.5,.65],[.25,.65],[.25,.92],
    [.44,.92],[.44,.76],[.5,.76],[.5,1],[-.5,1]];
  const required=[[-.16,.57],[.37,.57],[.37,.81],[-.16,.81]];
  const fitted=P.geometry.fitExteriorOutline({outline:outline.slice().reverse(),required});
  const field=P.geometry.profileDistance(fitted);
  assert(field(.31,.79)<0);
  assert(field(.41,.79)>0);
  assert(field(.47,.79)<0);
  assert(field(.31,.85)>0);
  const shell=P.geometry.recessedProfile({outline:fitted,
    recess:[[-.12,.63],[.28,.63],[.28,.75],[-.12,.75]],
    center:null,span:[-.6,0],inset:.2});
  assert(shell.distance([.31,.85,-.3])>0);
  assert.equal(KIT.mesh.info(P.geometry.toKitMesh(shell.mesh(),()=>[.5,.5,.5])).open,0);
});

test('fitted exteriors close enclosed holes, join along shared edges and reject disconnected regions',()=>{
  const outline=[[-2,-2],[2,-2],[2,-1],[-1,-1],[-1,1],[2,1],[2,2],[-2,2]];
  const required=[[1.5,-1.5],[2.5,-1.5],[2.5,1.5],[1.5,1.5]];
  const enclosed=P.geometry.profileDistance(P.geometry.fitExteriorOutline({outline,required}));
  assert(enclosed(0,0)<0);
  const square=[[0,0],[1,0],[1,1],[0,1]],side=[[1,.25],[2,.25],[2,.75],[1,.75]];
  const connected=P.geometry.profileDistance(P.geometry.fitExteriorOutline({outline:square,required:side}));
  assert(connected(1,.5)<0);
  assert(connected(1.5,.1)>0);
  assert.throws(()=>P.geometry.fitExteriorOutline({outline:square,required:side.map(([x,y])=>[x+1,y])}),
    {code:'DISCONNECTED_PROFILE'});
});

test('a profiled blind recess has a closed mesh and one field across the shell and backing', () => {
  const shape = P.geometry.recessedProfile(spec);
  assert(shape.distance([0, 0, 0]) > 0);
  assert(shape.distance([0, 0, -.5]) < 0);
  assert(shape.distance([.7, .35, 0]) < 0);
  assert(shape.distance([-1.75, 1, 0]) > 0);
  const mesh = shape.mesh({owner:'sample',surface:'recess',material:'stone'});
  assert.equal(KIT.mesh.info(P.geometry.toKitMesh(mesh, () => [.3,.5,.7])).open, 0);
  for (let i = 0; i < mesh.positions.length; i += 3)
    assert(Math.abs(shape.distance(Array.from(mesh.positions.slice(i,i+3)))) < 1e-6);
  let count = 0;
  shape.sample(.38, p => {
    assert(Math.abs(shape.distance(p)) < 1e-8);
    count++;
  });
  assert(count > 100);
});

test('recess profiles reject crossed boundaries, an invalid center and insufficient backing', () => {
  for (const patch of [{ inset: 1.2 }, { center: [2, 2] }, { outline: [[-1,-1],[1,1],[1,-1],[-1,1]] },
    { recess: [[-.3,-.3],[2,-.3],[2,.3],[-.3,.3]] }])
    assert.throws(() => P.geometry.recessedProfile({...spec,...patch}), /profile|Recess/i);
});

test('a blind recess exposes five independently finishable surfaces without splitting its solid', () => {
  const outline=[[-2,-2],[2,-2],[2,2],[-2,2]],recess=[[-1,-1],[1,-1],[1,1],[-1,1]];
  for(const center of [[0,0],null]){
    const shape=P.geometry.recessedProfile({outline,recess,span:[-1,0],inset:.6,center});
    const meta={owner:'solid',material:'stone',surface:'shell'};
    const finish=Object.fromEntries(['front','back','recess-back','outer-wall','reveal']
      .map(surface=>[surface,{surface,material:surface}]));
    const mesh=shape.mesh(meta,finish),plain=shape.mesh(meta);
    assert.deepEqual(mesh.positions,plain.positions);
    assert.deepEqual(mesh.normals,plain.normals);
    assert.equal(KIT.mesh.info(P.geometry.toKitMesh(mesh,()=>[.3,.5,.7])).open,0);
    assert.deepEqual(new Set(mesh.groups.map(g=>g.surface)),new Set(Object.keys(finish)));
    for(const group of mesh.groups){
      assert.equal(group.owner,'solid');
      assert.equal(group.material,group.surface);
      for(let i=group.start;i<group.start+group.count;i+=3){
        const point=[0,1,2].map(axis=>
          (mesh.positions[i*3+axis]+mesh.positions[(i+1)*3+axis]+mesh.positions[(i+2)*3+axis])/3);
        assert.equal(shape.surfaceAt(point),group.surface);
        assert(Math.abs(shape.distance(point))<1e-7);
      }
    }
    assert.equal(shape.surfaceAt([1,.3,0]),'front');
    assert.equal(shape.surfaceAt([1,.3,-.6]),'recess-back');
  }
});

test('a general recess produces a closed cap inside an outline with no radial center', () => {
  const outline=[[-2,-2],[2,-2],[2,-1],[-.4,-1],[-.4,1],[2,1],[2,2],[-2,2]],
    recess=[[-1.5,-.5],[-.9,-.5],[-.9,.5],[-1.5,.5]],span=[-.95,0],inset=.4;
  const volume=P.geometry.recessedProfile({outline,recess,span,inset,center:null});
  assert(volume.distance([1,0,-.5])>0);
  assert(volume.distance([-1.2,0,-.2])>0);
  assert(volume.distance([-1.2,0,-.6])<0);
  const shell=volume.mesh({owner:'concave',material:'stone'});
  assert.equal(KIT.mesh.info(P.geometry.toKitMesh(shell,()=>[1,1,1])).open,0);
  volume.sample(.34,p=>assert(Math.abs(volume.distance(p))<1e-8));
  assert.throws(()=>P.geometry.recessedProfile({outline,recess:[[-1,-1.5],[1,-1.5],[1,1.5],[-1,1.5]],
    span,inset,center:null}),/cannot touch/);
});

test('long thin recesses sample caps and walls within a surface-area budget', () => {
  const outline = [[-80,-.3],[80,-.3],[80,.3],[-80,.3]];
  const recess = [[-77,-.08],[77,-.08],[77,.08],[-77,.08]];
  const shape = P.geometry.recessedProfile({outline,recess,center:null,span:[-.6,0],inset:.25});
  let count = 0;
  const faces = new Set();
  shape.sample(.15, p => {
    assert(Math.abs(shape.distance(p)) < 1e-8);
    const [x,y,z] = p;
    if (z === 0 && Math.abs(y) < .3 && (Math.abs(y) > .08 || Math.abs(x) > 77)) faces.add('front');
    if (z === -.6 && Math.abs(y) < .3) faces.add('rear');
    if (z === -.25 && Math.abs(y) < .08 && Math.abs(x) < 77) faces.add('floor');
    if (z < 0 && Math.abs(y) === .3) faces.add('outer wall');
    if (z < 0 && Math.abs(y) === .08) faces.add('recess wall');
    count++;
  });
  assert(count > 16000 && count < 28000, String(count));
  assert.deepEqual(faces,new Set(['front','rear','floor','outer wall','recess wall']));
});

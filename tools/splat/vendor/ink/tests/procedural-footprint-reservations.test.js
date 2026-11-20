const test = require('node:test');
const assert = require('node:assert/strict');
const {KIT: K} = require('..').load();
const {createFootprintReservations,placeFootprintRequests,footprintFromBounds,footprintCorridor,transforms} = K.procedural;

const at = (point, size=[1,1,1], tangent=[1,0,0]) => ({point,size,tangent});

test('walking corridor volumes follow grade and leave room underneath elevated sections',()=>{
  const points=[[0,0,0],[2,1,0],[2,1,2]],options={width:.7,headroom:1.5,below:.08,step:.5};
  const corridor=footprintCorridor(points,options),ledger=createFootprintReservations();
  assert.equal(corridor.length,9,'two runs and a continuous turn');
  for(const volume of corridor)ledger.occupy(volume);
  assert(!ledger.fits(at([.15,0,0],[.2,.3,.2])));
  assert(ledger.fits(at([1.85,0,0],[.2,.3,.2])));
  assert(!ledger.fits(at([1.85,.98,0],[.2,.3,.2])));
  assert(!ledger.fits(at([2.2,1,-.2],[.2,.3,.2])));
  assert(ledger.fits(at([1.45,1,1.3],[.2,.3,.2])));
  assert(ledger.fits(at([2,2.51,1],[.2,.3,.2])));
  assert.throws(()=>footprintCorridor(points,{...options,maxVolumes:8}),/volume budget/);
});

test('an off-center affine box projects to a tight upright reservation',()=>{
  const bounds={min:[-.1,.3,-.7],max:[1,1.2,.5]},
    pose=transforms.local({position:[-1,.5,2],rotation:[.32,.52,-.13],scale:[1.5,.8,1.2]}),
    claim=footprintFromBounds(bounds,pose),{V}=K,side=[-claim.tangent[2],0,claim.tangent[0]],
    axes=[claim.tangent,[0,1,0],side],coordinates=[];
  for(const x of [bounds.min[0],bounds.max[0]])for(const y of [bounds.min[1],bounds.max[1]])
    for(const z of [bounds.min[2],bounds.max[2]]){
      const local=V.sub(transforms.point(pose,[x,y,z]),claim.point);
      coordinates.push(axes.map(axis=>V.dot(axis,local)));
    }
  for(let i=0;i<3;i++){
    const values=coordinates.map(p=>p[i]),bottom=i===1?0:-claim.size[i]/2;
    assert(Math.abs(Math.min(...values)-bottom)<1e-9);
    assert(Math.abs(Math.max(...values)-(bottom+claim.size[i]))<1e-9);
  }
  assert.throws(()=>footprintFromBounds({min:[2,0,0],max:[1,1,1]},pose),/ordered local bounds/);
});

test('ranked fitters share occupied space, including fallback intervals and fixed obstacles', () => {
  const spot=at([0,0,0]), obstacle=at([2.1,0,0]), high=at([0,1,0]);
  const edited={priority:2,fit:()=>({footprint:spot,value:'edited'})};
  const first={fit:({fits,freeIntervals})=>{
    assert(!fits(spot));
    const intervals=freeIntervals(spot,[1,0,0],[0,4]);
    assert.deepEqual(intervals.map(range=>range.map(v=>Math.round(v*100)/100)),[[1.05,1.05],[3.15,4]]);
    return {footprint:at([-1.1,0,0]),value:'shifted'};
  }};
  const second={fit:({fits})=>{
    assert(!fits(at([-1.1,0,0])));
    return {footprint:high,value:'above'};
  }};
  const blocked={priority:1,fit:()=>({footprint:obstacle,value:'blocked'})};
  const result=placeFootprintRequests([first,second,edited,blocked],{obstacles:[obstacle],clearance:.05});
  assert.deepEqual(result.map(e=>e.value),['edited','shifted','above']);
  assert.equal(result[0].request,edited);
  assert.throws(()=>placeFootprintRequests([{priority:Infinity,fit(){}}]),/finite priority/);
});

test('reservation uses oriented volume overlap and preserves space on other levels', () => {
  const field=createFootprintReservations({cellSize:.2});
  const axis=[1,0,1], halfAngle=Math.SQRT1_2;
  const beam=at([0,0,0],[2,.5,.2],axis);
  assert(field.reserve(beam));
  assert(!field.reserve(at([0,.25,0],[.2,.2,.2])));
  assert(field.reserve({...beam,point:[0,.5,0]}));
  assert(field.reserve({...beam,point:[-.3*halfAngle,0,.3*halfAngle]}));
  assert(!field.fits(at([.5,0,.5],[.1,.2,.1])));
});

test('reserve is atomic and authored volumes can overlap in the same field', () => {
  const field=createFootprintReservations({clearance:.12,cellSize:.4});
  field.occupy(at([0,0,0]));
  field.occupy(at([.25,0,0]));
  assert(!field.reserve(at([1.36,0,0])));
  assert(field.reserve(at([1.38,0,0])));
  assert(field.fits(at([-3,0,0])));
  field.occupy(at([300,0,0],[300,.2,2]));
  assert(!field.reserve(at([250,0,0])));
  assert.throws(()=>field.occupy(at([0,0,0],[1,1,1],[0,1,0])),/horizontal/);
});

test('clearance intervals keep exact touching positions and ignore separate levels',()=>{
  const field=createFootprintReservations({cellSize:.25});
  field.occupy(at([0,0,0]));
  field.occupy(at([2,0,0]));
  field.occupy(at([4,1,0]));
  assert.deepEqual(field.freeIntervals(at([0,0,0]),[2,0,0],[-3,5]),[[-3,-1],[1,1],[3,5]]);
  assert.deepEqual(field.freeIntervals(at([0,0,0]),[1,0,0],[0,0]),[]);
  assert.deepEqual(field.freeIntervals(at([0,0,0]),[1,0,0],[1,1]),[[1,1]]);
  assert.throws(()=>field.freeIntervals(at([0,0,0]),[0,1,0],[-2,2]),/horizontal/);
});

test('clearance intervals match rotated physical overlap over continuous signed offsets',()=>{
  const field=createFootprintReservations({cellSize:.24,clearance:.16});
  field.occupy(at([0,0,0],[1.8,.5,.25],[1,0,1]));
  field.occupy(at([2.1,.1,0],[.9,.25,.65],[1,0,-1]));
  const sample=at([0,.1,.18],[.45,.4,.42],[0,0,1]),dir=[.8,0,.6];
  const free=field.freeIntervals(sample,dir,[-3,3]);
  assert(free.some(([a,b])=>b-a>.5));
  for(let i=0;i<=600;i++){
    const step=(i-300)/100,point=sample.point.map((x,j)=>x+dir[j]*step);
    assert.equal(field.fits({...sample,point}),free.some(([lo,hi])=>lo<=step&&step<=hi));
  }
});

test('nearest footprint translation finds the corner of two blockers between fixed search directions',()=>{
  const field=createFootprintReservations(),spot=at([0,0,0]);
  field.occupy(at([-.68,0,0]));
  field.occupy(at([0,0,-.44]));
  field.occupy(at([.32,1,.56]));
  const reach=.66;
  for(let i=0;i<8;i++){
    const angle=i*Math.PI/4;
    assert.deepEqual(field.freeIntervals(spot,[Math.cos(angle),0,Math.sin(angle)],[0,reach]),[]);
  }
  const fit=field.nearestTranslation(spot,{reach,margin:.001,test:offset=>offset[2]>0?'supported':null});
  assert.equal(fit.status,'ok');
  assert.equal(fit.value,'supported');
  assert(Math.abs(fit.offset[0]-.321)<1e-8&&Math.abs(fit.offset[2]-.561)<1e-8);
  assert(field.fits({...spot,point:fit.offset}));
  assert(!field.fits(spot),'query does not change reservations');
  assert.equal(field.nearestTranslation(spot,{reach:.64}).status,'unreachable');
  assert.equal(field.nearestTranslation(spot,{reach,maxObstacles:1}).status,'budget');
  assert.equal(field.nearestTranslation(spot,{reach,maxTests:1}).status,'budget');
});

test('nearest translation checks a rotated face and uses the same ledger in priority requests',()=>{
  const theta=.31,c=Math.cos(theta),s=Math.sin(theta),spot=at([0,0,0],[.2,.2,.2]),
    obstacle=at([0,0,0],[1,1,.34],[c,0,s]);
  const fit={fit({nearestTranslation}){
    const found=nearestTranslation(spot,{reach:.4,margin:.001,test:(offset,distance)=>
      offset[2]>0&&{distance}});
    assert.equal(found.status,'ok');
    assert(Math.abs(found.offset[0]/found.distance+s)<1e-8);
    assert(Math.abs(found.offset[2]/found.distance-c)<1e-8);
    return {footprint:{...spot,point:found.offset},value:found.value};
  }};
  const result=placeFootprintRequests([fit],{obstacles:[obstacle]});
  assert.equal(result.length,1);
  assert(Math.abs(result[0].value.distance-(.171+.1*(c+s)))<1e-8);
});

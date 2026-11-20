const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT:K,makeBuilder}=require('..').load();
const {motion}=K.procedural;
const near=(a,b,e=1e-7)=>assert(Math.abs(a-b)<=e,a+' differs from '+b);

test('balanced transport matches separated features independent of input order',()=>{
  const a=[{id:'west',position:[-1,0,0],feature:'teal'},{id:'east',position:[1,0,0],feature:'brass'}],
    b=[{id:'right',position:[1.1,0,0],feature:'brass'},{id:'left',position:[-1.1,0,0],feature:'teal'}],
    result=motion.transportSplats(a,b,{epsilon:0.025});
  assert.equal(result.status,'ok');
  assert(result.mass[1]>0.4999&&result.mass[2]>0.4999);
  assert(result.mass[0]<0.0001&&result.mass[3]<0.0001);
  near(result.forward[0][0],-1.1);
  near(result.reverse[0][0],1);
  assert(result.objective<0.012);
});

test('unequal weighted sets have feasible marginal masses even with a short solve',()=>{
  const a=[{id:'island',position:[-1,0,0],weight:1},{id:'bank',position:[1,0,0],weight:3}],
    b=[{id:'a',position:[1.4,0,0],weight:0.15},{id:'b',position:[2.8,0,0],weight:0.25},
      {id:'c',position:[3.3,0,0],weight:0.60}],
    r=motion.transportSplats(a,b,{iterations:1,epsilon:0.017});
  for(let i=0;i<r.rows;i++)
    near(r.mass.slice(i*r.columns,(i+1)*r.columns).reduce((x,y)=>x+y,0),r.rowMass[i],2e-12);
  for(let j=0;j<r.columns;j++)
    near(r.mass[j]+r.mass[r.columns+j],r.columnMass[j],2e-12);
  assert(r.forward.every(p=>p[0]>=1.4-1e-9&&p[0]<=3.3+1e-9));
  const center=r.forward.reduce((a,p,i)=>a+p[0]*r.rowMass[i],0);
  near(center,b.reduce((a,p)=>a+p.position[0]*p.weight,0),1e-10);
  assert.throws(()=>motion.transportSplats(a,b,{maxWork:5}),/work budget/);
});

test('the live morph stage uses noncontiguous dab IDs with nearest and transport options',()=>{
  for(const mode of ['nearest','transport']){
    const B=makeBuilder(8), xs=[-4,-1.05,-0.83,0.2,1.05,1.47];
    for(const x of xs)B.disc(x,0,0,[0,0,1],0.1,0.018,[111,172,161],3);
    const W=B.finish({}), stage=K.stage(W),
      active=K.morph(B,stage,[1,4],Int32Array.of(2,5),{dur:1,loop:[0,1],correspondence:mode});
    stage.add(active);
    stage.update(0,0);
    near(W.data[16],xs[1]);
    assert.equal(W.data[2*16+3],0);
    stage.update(0.02,0.5);
    near(W.data[16],(xs[1]+xs[2])*0.5);
    near(W.data[4*16],(xs[4]+xs[5])*0.5);
    near(W.data[3*16],xs[3]);
    assert.equal(stage.rows[0],1);
    if(mode==='transport')assert.equal(active.transport.status,'ok');
    stage.update(0.02,1.4);
    near(W.data[2*16],xs[2],2e-7);
    near(W.data[2*16+3],3);
    near(W.data[16+3],0);
  }
});

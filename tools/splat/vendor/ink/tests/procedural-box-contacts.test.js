const test = require('node:test');
const assert = require('node:assert/strict');
const K = require('..').load().KIT;
const { orientedBox, boxContact, verticalPrism, volumeContact, volumeSet, volumeSetsContact } = K.procedural.contacts;

test('indexed volume sets match exhaustive contact for sparse mixed shapes',()=>{
  const make=(offset)=>Array.from({length:31},(_,i)=>{
    const x=i*.7,z=x+offset,y=i%4*.2;
    return i%2===0
      ?verticalPrism([[x,z],[x+.4,z],[x,z+.4]],y,y+.2)
      :orientedBox([x,y,z],[.25,.11,.16],K.M.rot([0,1,0],i*.41));
  });
  const a=make(0),index=volumeSet(a);
  for(const offset of [0,.1,.3,.56,1.1,-.21,-.77]){
    const b=make(offset).reverse(),other=volumeSet(b);
    for(const pad of [0,.02,.2]){
      const exact=a.some(first=>b.some(second=>volumeContact(first,second,pad)));
      assert.equal(volumeSetsContact(index,other,pad),exact,'offset '+offset+' pad '+pad);
      assert.equal(volumeSetsContact(other,index,pad),exact);
    }
  }
  const touching=volumeSet(a);
  a.length=0;
  assert.equal(index.size,31);
  assert(Object.isFrozen(index.bounds.min));
  assert(volumeSetsContact(index,touching));
  assert(!volumeSetsContact(index,volumeSet([])));
  assert.throws(()=>volumeSet([{}]),/boxes or prisms/);
  assert.throws(()=>volumeSetsContact(index,touching,-1),/tolerance/);
});

test('vertical prism contact follows the fitted footprint and height',()=>{
  const ring=[[0,0],[2,0],[0,2]],a=verticalPrism(ring,0,1);
  const outside=orientedBox([1.25,.5,1],[.1,.25,.1]);
  assert(!volumeContact(a,outside));
  assert(volumeContact(a,outside,.04));
  assert(volumeContact(outside,a,.04));
  const b=verticalPrism([[1,1],[1,1.5],[1.5,1]],.9,1.2);
  assert(volumeContact(a,b));
  assert(!volumeContact(a,verticalPrism(b.footprint,1.05,2)));
  assert(volumeContact(a,verticalPrism(b.footprint,1.05,2),.05));
  ring[0][0]=30;
  assert(a.containsPlan(.5,.5));
  assert(!a.containsPlan(1.4,1.4));
  assert(Object.isFrozen(a.footprint));
  assert.throws(()=>verticalPrism(ring,2,1),/ordered/);
  assert.throws(()=>verticalPrism([[0,0],[2,0],[1,.5],[2,2],[0,2]],0,1),/convex/);
});

test('prism contact agrees with an equivalent box against tilted volumes',()=>{
  const a=orientedBox([0,.5,0],[.8,.5,.35]);
  const prism=verticalPrism([[-.8,-.35],[.8,-.35],[.8,.35],[-.8,.35]],0,1);
  for(let i=0;i<96;i++){
    const frame=K.M.mul(K.M.rot([1,0,0],.51),K.M.rot([0,1,0],i*.11));
    const box=orientedBox([i%6*.35-.8,i%9*.24-.4,i%11*.17-.85],[.7,.12,.23],frame);
    assert.equal(volumeContact(prism,box),boxContact(a,box),'pose '+i);
    assert.equal(volumeContact(box,prism,.02),boxContact(box,a,.02),'tolerant pose '+i);
  }
});

test('upright prism walls can enclose a sloped band without claiming the entire bounding height',()=>{
  const ring=[[10,20],[12,20],[12,22],[10,22]],
    ramp=verticalPrism(ring,.8,1,{origin:[10,20],gradient:[.5,0]});
  assert.deepEqual(ramp.bounds,{min:[10,.8,20],max:[12,2,22]});
  const overlap=orientedBox([10.25,1.85,20.5],[.1,.15,.1]);
  assert(K.procedural.spatial.overlap(ramp.bounds,overlap.bounds));
  assert(!volumeContact(ramp,overlap));
  assert(!volumeContact(overlap,ramp));
  const facing=verticalPrism([[11.5,20.5],[11.8,20.5],[11.8,21],[11.5,21]],1.7,1.8);
  assert(volumeSetsContact(volumeSet([ramp]),volumeSet([facing])));
  const high=verticalPrism(facing.footprint,1.92,1.95);
  assert(!volumeContact(high,ramp));
  assert(volumeContact(high,ramp,.022));
  const counter=verticalPrism(ring,1.6,1.7,{origin:[10,20],gradient:[-.2,0]});
  assert(volumeContact(ramp,counter));
  assert.throws(()=>verticalPrism(ring,0,1,{gradient:[Infinity,0]}),/finite/);
});

test('box contacts include a face join and reject separated diagonal volumes with overlapping bounds', () => {
  const yaw = Math.PI/4, c = Math.cos(yaw), s = Math.sin(yaw);
  const frame = [c,0,-s,0,1,0,s,0,c];
  const center = [0,1,0], half = [3,.10,.14];
  const a = orientedBox(center,half,frame);
  const at = gap => orientedBox([-s*gap,1,c*gap],half,frame);
  assert(boxContact(a,at(.28)));
  assert(!boxContact(a,at(.31)));
  assert(boxContact(a,at(.31),.035));
  assert(K.procedural.spatial.overlap(a.bounds,at(.8).bounds));
  assert(!boxContact(a,at(.8)));
  assert(!boxContact(at(.8),a));
  assert(boxContact(a,orientedBox(center,[.14,.1,3],frame)));
  assert(!boxContact(a,orientedBox([0,1.4,0],[3,.1,3])));
  center[0] = 42;
  assert.equal(a.center[0],0);
  assert(Object.isFrozen(a.bounds.min));
  assert.throws(() => orientedBox(center,half,[2,0,0,0,1,0,0,0,1]),/orthonormal/);
  assert.throws(() => boxContact(a,a,-1),/tolerance/);
});

test('a skew pair can separate on an edge cross axis while all its face axes overlap', () => {
  const a = orientedBox([0,0,0],[2,.25,.25]);
  const b = orientedBox([-1,.25,1.48],[1.6,.22,.22],K.M.mul(
    K.M.rot([0,1,0],.7),K.M.rot([1,0,0],1.1)
  ));
  const delta = K.V.sub(b.center,a.center);
  const extent = (box,axis) => box.axes.reduce((sum,v,i)=>sum+Math.abs(K.V.dot(v,axis))*box.half[i],0);
  assert([...a.axes,...b.axes].every(axis=>Math.abs(K.V.dot(delta,axis))<extent(a,axis)+extent(b,axis)));
  assert(!boxContact(a,b));
  assert(!boxContact(b,a));
});

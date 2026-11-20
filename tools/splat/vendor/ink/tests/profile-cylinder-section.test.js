const test=require('node:test'),assert=require('node:assert/strict');
const K=require('..').load().KIT,P=K.procedural;
const rectangle=(x,y,X,Y)=>[[x,y],[X,y],[X,Y],[x,Y]];
const near=(a,b)=>assert(Math.abs(a-b)<1e-8,`${a} != ${b}`);

test('cylinder section joins the seam while retaining physically separate contacts',()=>{
  const cylinder={origin:[0,0,0],cosine:[2,0,0],sine:[0,0,1],axis:[0,3,0]};
  const outline=rectangle(-3,.45,3,1.8),frame=P.transforms.local(),span=[-.18,.18];
  const section=P.geometry.profileCylinderSection({outline,span,frame,cylinder});
  const half=Math.asin(.18)/(Math.PI*2);
  assert.equal(section.bands.length,2);
  const [middle,seam]=section.bands;
  near(middle.min[0],.5-half);near(middle.max[0],.5+half);
  near(seam.min[0],1-half);near(seam.max[0],1+half);
  for(const b of section.bands){
    near(b.min[1],.15);near(b.max[1],.6);
  }
  assert.deepEqual(section.at(.3),[]);
  assert.deepEqual(section.at(1.01),section.at(.01));
  assert.equal(section.at(.5).length,1);
  assert.equal(P.geometry.profileCylinderSection({...{outline,frame,cylinder},span:[4,5]}).bands.length,0);
});

test('cylinder section agrees with the volume of a concave sweep in an oblique frame',()=>{
  const outline=[[-2,-1],[2,-1],[2,1],[.6,1],[.6,0],[-.6,0],[-.6,1],[-2,1]];
  const cylinder={origin:[0,-1,0],cosine:[2,0,0],sine:[.25,0,1.2],axis:[.55,3.5,-.16]};
  const frame=P.transforms.local({position:[.45,.7,-.09],rotation:[.18,.42,-.13],scale:[1,1.22,.8]}),
    span=[-.84,.72],cut=P.profileCut({profile:outline,span,frame});
  const section=P.geometry.profileCylinderSection({outline,span,frame,cylinder});
  let checked=0,inside=0;
  for(let row=0;row<127;row++){
    const u=(row+.27)/127,angle=u*Math.PI*2,runs=section.at(u);
    for(let col=0;col<93;col++){
      const v=(col+.44)/93,at=K.V.add(cylinder.origin,K.V.add(K.V.mul(cylinder.cosine,Math.cos(angle)),
        K.V.add(K.V.mul(cylinder.sine,Math.sin(angle)),K.V.mul(cylinder.axis,v))));
      const distance=cut.distance(at);
      if(Math.abs(distance)<1e-8)continue;
      checked++;
      const found=runs.some(([a,b])=>v>=a&&v<=b);
      assert.equal(found,distance<0,`at ${u},${v}`);
      if(found){
        inside++;
        assert(section.bands.some(b=>[u,u+1].some(shifted=>shifted>=b.min[0]&&shifted<=b.max[0])&&
          v>=b.min[1]&&v<=b.max[1]));
      }
    }
  }
  assert(checked>10000&&inside>900);
  assert.throws(()=>P.geometry.profileCylinderSection({outline,span,frame,
    cylinder:{...cylinder,axis:cylinder.cosine}}),/span three/);
});

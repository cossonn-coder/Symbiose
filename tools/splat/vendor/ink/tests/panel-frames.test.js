const test=require('node:test'),assert=require('node:assert/strict');
const P=require('..').load().KIT.procedural;
const standard={width:5,height:3,unit:[1,1],beam:.16,braces:'cross'};

test('opening edges keep exposed spans across a periodic seam and merge overlapping material',()=>{
  const frame=P.panelFrames({...standard,braces:'none',periodic:true,openings:[
    {key:'seam',min:[4.55,.63],max:[5.6,2.17],rim:false},
    {key:'overlap',min:[.4,.82],max:[1.45,1.18],rim:false}
  ]});
  const edges=frame.openingEdges(),close=(a,b)=>Math.abs(a-b)<1e-7;
  assert(edges.length>0);
  assert.equal(frame.openingEdges(),edges);
  assert(!edges.some(edge=>edge.normal[0]&&[0,5].some(seam=>close(edge.start[0],seam))));
  const first=edges.filter(edge=>edge.normal[0]===1&&close(edge.start[0],4.55));
  assert.equal(first.length,2);
  assert(first.some(({start,end})=>close(start[1],.92)&&close(end[1],1.08)));
  const exposed=edges.filter(edge=>edge.normal[0]===-1&&close(edge.start[0],.6));
  assert.equal(exposed.length,1);
  assert(close(exposed[0].start[1],1.92)&&close(exposed[0].end[1],2.08));
  assert(edges.some(edge=>edge.normal[0]===-1&&close(edge.start[0],1.45)&&
    close(edge.start[1],.92)&&close(edge.end[1],1.08)));
  assert.deepEqual(P.panelFrames(standard).openingEdges(),[]);
});

test('a retained opening clips crossing members and fits keyed headers, sills and jambs',()=>{
  const original=P.panelFrames(standard);
  const frame=P.panelFrames({...standard,openings:[{key:'bay',min:[1.65,.58],max:[2.65,1.59]}]});
  assert(original.distance(2,1)<0);
  assert(frame.distance(2,1)>0);
  assert(frame.distance(1.59,1.38)<0);
  assert(frame.distance(2.42,1.64)<0);
  assert(frame.parts.some(p=>p.key==='opening/bay/header'));
  assert(frame.parts.some(p=>p.key==='rail/3'));
  for(const part of frame.parts){
    const center=part.polygon.reduce(([x,y],[u,v])=>[x+u/part.polygon.length,y+v/part.polygon.length],[0,0]);
    assert(frame.distance(...center)<=1e-8);
  }
});

test('seam openings clip the two chart ends with one set of logical keys',()=>{
  const opening={key:'seam',min:[4.7,.62],max:[5.42,1.72]};
  const frame=P.panelFrames({...standard,periodic:true,openings:[opening]});
  for(const u of [-.1,0,.18,4.8,5.19])assert(frame.distance(u,1)>0);
  assert.equal(frame.parts.filter(p=>p.key==='opening/seam/header').length,2);
  const unframed=P.panelFrames({...standard,periodic:true,openings:[{...opening,rim:false}]});
  assert(unframed.parts.every(p=>!p.key.startsWith('opening/')));
});

test('two charts meeting at a cut keep continuous rails with no artificial middle jamb',()=>{
  const common={...standard,braces:'none'};
  const a=P.panelFrames({...common,openings:[
    {key:'join',min:[3.8,.64],max:[5,1.72],rimEdges:['header','sill','start']}
  ]});
  const b=P.panelFrames({...common,openings:[
    {key:'join',min:[0,.64],max:[1.2,1.72],rimEdges:['header','sill','end']}
  ]});
  for(const [frame,u] of [[a,4.96],[b,.04]]){
    assert(frame.distance(u,1)>.02);
    assert(frame.distance(u,1.79)<0);
    assert(frame.distance(u,.56)<0);
  }
  assert(a.parts.some(p=>p.key==='opening/join/start'));
  assert(b.parts.some(p=>p.key==='opening/join/end'));
  assert(a.parts.every(p=>p.key!=='opening/join/end'));
  assert(b.parts.every(p=>p.key!=='opening/join/start'));
  assert.throws(()=>P.panelFrames({...common,openings:[
    {key:'bad',min:[1,1],max:[2,2],rimEdges:['middle']}
  ]}),/rim edges/);
});

test('a full-period opening clears the entire ring and has no artificial end jamb',()=>{
  const frame=P.panelFrames({...standard,periodic:true,openings:[{
    key:'ring',min:[1.25,.62],max:[6.25,1.72]
  }]});
  for(const u of [0,.001,2.7,4.99,5,5.01]){
    assert(frame.distance(u,1)>.1);
    assert(frame.distance(u,1.79)<0);
  }
  const members=frame.parts.filter(part=>part.key.startsWith('opening/ring/'));
  assert.deepEqual(members.map(part=>part.key),['opening/ring/sill','opening/ring/header']);
});

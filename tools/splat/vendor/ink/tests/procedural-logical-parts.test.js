const test = require('node:test');
const assert = require('node:assert/strict');
const P = require('..').load().KIT.procedural;
const { compile, edits, captureAnchors } = P.logicalParts;

test('a wrapped stock key selects every physical fragment and retains order', () => {
  const layout = require('..').load().KIT.stripCourses({
    sections: [{ s: 0, lower: 0, upper: 1 }, { s: 1, lower: .1, upper: 1 },
      { s: 2, lower: 0, upper: 1 }],
    unit: [.5, .3], joint: .04, stagger: .5, closed: true
  });
  const stock = compile(layout.pieces, piece => piece.id);
  const wrapped = stock.groups.find(group => group.fragments.some(piece => piece.stockColumn < 0));
  assert(wrapped);
  assert(wrapped.fragments.some(piece => piece.stockColumn > 0));
  assert.deepEqual(stock.get(wrapped.key), wrapped.fragments);
  assert(Object.isFrozen(wrapped.fragments));
  const change = stock.partition(new Set([wrapped.key, 'unknown']));
  assert.deepEqual(change.omitted, layout.pieces.filter(piece => piece.id === wrapped.key));
  assert.deepEqual(change.visible, layout.pieces.filter(piece => piece.id !== wrapped.key));
  assert.deepEqual(stock.partition().visible, layout.pieces);
});

test('unkeyed backing remains visible and invalid keys fail early', () => {
  const backing = { id: null }, tile = { id: 'tile-0' }, input = [backing, tile];
  const assembly = compile(input, part => part.id);
  input.reverse();
  assert.deepEqual(assembly.partition(), { visible: [backing, tile], omitted: [] });
  assert.deepEqual(assembly.partition(['tile-0']), { visible: [backing], omitted: [tile] });
  assert.deepEqual(assembly.get('unknown'), []);
  assert.throws(() => compile([tile], () => ''), /keys/);
  assert.throws(() => assembly.partition([null]), /keys/);
});

test('anchored exclusions follow a new layout and recover both sites after coarsening', () => {
  const split=([u])=>u<.5?'left':'right';
  const anchors=[{key:'0',site:[.26,.7]},{key:'1',site:[.72,.7]}];
  const old=['0','1','legacy'];
  const coarse=edits(old,anchors,()=> 'wide');
  assert.deepEqual(coarse.keys,['legacy','wide']);
  const edited=coarse.setVisible('third',false,[.83,.85]);
  const refined=edits(edited.keys,edited.anchors,split);
  assert.deepEqual(refined.keys,['left','legacy','right']);
  const restored=refined.setVisible('right',true);
  assert.deepEqual(restored,{keys:['0','legacy'],anchors:[anchors[0]]});
  assert.deepEqual(edits(old,anchors,()=>null).keys,['legacy']);
  assert.deepEqual(edits([],anchors,split).keys,[]);
  assert.equal(coarse.setVisible('wide',false,[.5,.7]),null);
  assert.throws(()=>edits(old,[{key:'0',site:[.1,NaN]}],split),/finite chart point/);
});

test('capture upgrades only known sites and is idempotent for mixed saves',()=>{
  const anchors=Object.freeze([{key:'kept',site:[.2,1]}]),keys=['kept','old','dormant','old'];
  const tried=[],point=[.8,2];
  const captured=captureAnchors(keys,anchors,key=>{
    tried.push(key);
    return key==='old'?point:null;
  });
  assert.deepEqual(tried,['old','dormant']);
  assert.deepEqual(captured,[...anchors,{key:'old',site:[.8,2]}]);
  point[0]=.9;
  assert.equal(captured[1].site[0],.8);
  assert.equal(captureAnchors(keys,captured,()=>null),captured);
  assert.deepEqual(edits(keys,captured,()=>null).keys,['dormant']);
});

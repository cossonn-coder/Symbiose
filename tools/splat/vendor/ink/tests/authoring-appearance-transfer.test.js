const test=require('node:test');
const assert=require('node:assert/strict');
const {KIT}=require('..').load(), A=KIT.authoring, P=KIT.procedural;

function fixture(){
  const doc=A.document();
  doc.setStyle('common',{materials:{wood:'#907151',paint:'#e4ddab',amber:'#da9860'}});
  doc.setEnvironment({styleRef:'common'});
  doc.create('panel',{id:'source',parameters:{role:'wood',finish:'vertical'},appearance:{materials:{wood:'amber'}}});
  doc.create('panel',{id:'receiver',parameters:{role:'paint',finish:'horizontal',span:17},appearance:{detail:{wear:.3}}});
  doc.create('panel',{id:'another',parameters:{role:'wood',finish:'horizontal'}});
  doc.create('glass',{id:'window',parameters:{role:'paint'}});
  const api=A.appearanceTransfer.create({
    describe(e,s){
      const role=e.parameters.role;
      return {family:e.type,label:'Sample '+e.type,slots:{
        face:{path:['appearance','materials',role,'color'],value:P.styles.material(A.styles.resolve(s,e.id),role).color},
        finish:{path:['parameters','finish'],value:e.parameters.finish}
      }};
    }
  });
  return {doc,api};
}

test('appearance capture resolves aliases and transfers matching slots with one undo',()=>{
  const {doc,api}=fixture(), before=doc.serialize(), sample=api.capture(doc,'source');
  assert.deepEqual(sample.values.face,P.styles.rgb('#da9860'));
  const payload=JSON.parse(JSON.stringify(sample));
  const result=api.apply(doc,['receiver','receiver','another','window','missing'],payload);
  assert.deepEqual(result.edits.map(e=>e.id),['receiver','another']);
  assert.deepEqual(result.skipped,[{id:'window',reason:'incompatible'},{id:'missing',reason:'missing'}]);
  assert.deepEqual(doc.get('receiver').appearance,{detail:{wear:.3},materials:{paint:{color:sample.values.face}}});
  assert.equal(doc.get('receiver').parameters.span,17);
  assert.equal(doc.get('receiver').parameters.finish,'vertical');
  assert.equal(doc.get('receiver').styleRef,null);
  assert.equal(api.apply(doc,['receiver'],sample).edits.length,0);
  assert.equal(doc.history().undo.at(-1),'Transfer appearance');
  doc.undo();
  assert.equal(doc.serialize(),before);
  doc.redo();
  assert.deepEqual(api.capture(doc,'receiver').values,sample.values);
});

test('a portable sample can map to a different receiver and incompatible paths fail before writes',()=>{
  const {doc,api}=fixture(), sample=api.capture(doc,'source'), before=doc.serialize();
  const mapped=A.appearanceTransfer.create({
    compatible:()=>true,
    describe:()=>({family:'machine',slots:{face:{path:['parameters','paint','tint']}}})
  });
  assert.deepEqual(mapped.plan(doc,['window'],sample).edits[0].patch,{parameters:{paint:{tint:sample.values.face}}});
  const broken=A.appearanceTransfer.create({
    compatible:()=>true,
    describe:()=>({family:'machine',slots:{
      face:{path:['parameters','paint']},finish:{path:['parameters','paint','tint']}
    }})
  });
  assert.throws(()=>broken.apply(doc,['receiver','another'],sample),/Overlapping/);
  assert.equal(doc.serialize(),before);
  assert.throws(()=>api.plan(doc,['receiver'],{...sample,values:JSON.parse('{"__proto__":{}}')}),/Invalid portable/);
});

test('slot encoders write receiver-specific values without changing the sampled color',()=>{
  const {doc,api}=fixture(), sample=api.capture(doc,'source'), before=doc.serialize();
  const bound=A.appearanceTransfer.create({
    describe(e){
      const role=e.parameters.role;
      return {family:'panel',slots:{face:{
        path:['appearance','materials',role],value:[0,0,0],
        encode:color=>({alias:'amber',color})
      }}};
    }
  });
  const result=bound.apply(doc,['receiver'],sample);
  assert.deepEqual(result.edits[0].patch.appearance.materials.paint,{alias:'amber',color:sample.values.face});
  assert.deepEqual(doc.get('receiver').appearance.materials.paint,{alias:'amber',color:sample.values.face});
  assert.deepEqual(bound.capture(doc,'receiver').values.face,[0,0,0]);
  doc.undo();assert.equal(doc.serialize(),before);

  const broken=A.appearanceTransfer.create({
    describe(e){return {family:'panel',slots:{face:{path:['appearance','color'],
      encode:e.id==='another'?()=>{throw Error('Invalid receiver');}:color=>color}}};}
  });
  assert.throws(()=>broken.apply(doc,['receiver','another'],sample),/Invalid receiver/);
  assert.equal(doc.serialize(),before);
});

test('encoded no-ops and caller validation use the complete plan before any target is written',()=>{
  const {doc}=fixture(),before=doc.serialize();
  let inspected=0;
  const api=A.appearanceTransfer.create({
    describe(e){
      return {family:'panel',slots:{role:{value:e.parameters.role,stored:e.parameters.role,
        path:['parameters','role'],encode:role=>role==='wood'?'paint':role}}};
    },
    validate(source,edits){
      inspected++;
      assert.equal(source.entities.another.parameters.role,'wood');
      assert.deepEqual(edits.map(e=>e.id),['another']);
      throw Error('The receiver cannot realize the complete style');
    }
  });
  const sample=api.capture(doc,'source');
  assert.equal(api.apply(doc,['receiver'],sample).edits.length,0);
  doc.begin('Existing edit');
  assert.throws(()=>api.apply(doc,['receiver','another'],sample),/cannot realize/);
  assert.equal(inspected,1);
  assert.equal(doc.serialize(),before);
  assert(doc.pending());
  doc.cancel();
});

test('an appearance descriptor can bind an assembly slot to a related record atomically',()=>{
  const d=A.document();
  for(const [id,face,trim] of [['source','#8f5342','#547376'],['target','#cdbea9','#756452']]){
    d.create('panel',{id,appearance:{materials:{stone:face}}});
    d.create('trim',{id:id+'-trim',parent:id,appearance:{materials:{wood:trim}}});
  }
  const api=A.appearanceTransfer.create({describe(e,source){
    const trim=source.entities[e.id+'-trim'];
    const slot=(entity,role)=>({target:entity.id,path:['appearance','materials',role,'color'],
      value:P.styles.material(A.styles.resolve(source,entity.id),role).color});
    return {family:'panel',slots:{face:slot(e,'stone'),edge:slot(trim,'wood')}};
  }});
  const sample=api.capture(d,'source'),before=d.serialize();
  const plan=api.apply(d,['target'],sample);
  assert.deepEqual(plan.edits.map(edit=>edit.id),['target','target-trim']);
  assert.deepEqual(api.capture(d,'target'),sample);
  assert.equal(api.plan(d,['target'],sample).skipped[0].reason,'unchanged');
  d.undo();assert.equal(d.serialize(),before);
  const invalid=A.appearanceTransfer.create({describe:()=>({family:'panel',
    slots:{edge:{target:'missing',path:['appearance','materials','wood']}}})});
  assert.throws(()=>invalid.apply(d,['target'],sample),/existing entities/);
  const conflict=A.appearanceTransfer.create({describe:e=>({family:'panel',slots:{edge:{
    target:'target-trim',path:['appearance','materials','wood'],encode:()=>e.id==='target'?'#111111':'#222222'
  }}})});
  assert.throws(()=>conflict.apply(d,['source','target'],sample),/conflict on target-trim/);
  assert.equal(d.serialize(),before);
});

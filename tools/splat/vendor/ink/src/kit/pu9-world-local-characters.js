/* Declarative character controls for headless gravity worlds. */
(function(K){
  const W=K.world, Q=W.query, {V,M}=K, {record,check,vector,id,own}=W.data;
  const zero=[0,0,0];
  function characters(config){
    const {gravity,clearance,support,medium,supportPadding}=config, authored=config.characters;
    check(typeof gravity==='string'&&typeof clearance==='string'&&
      [support,medium].every(name=>name===undefined||typeof name==='string')&&
      (supportPadding===undefined||Number.isFinite(supportPadding)&&supportPadding>=0&&supportPadding<=2)&&
      record(authored)&&Object.keys(authored).length>0&&Object.keys(authored).length<=128,'Invalid local character configuration');
    const initial={}, specs={}, inputs={};
    for(const key of Object.keys(authored).sort()){
      const row=authored[key];
      check(id(key)&&key.length<=80&&record(row)&&id(row.entity??key)&&vector(row.position)&&
        (row.worldMove===undefined||typeof row.worldMove==='boolean')&&
        (row.look===undefined||Array.isArray(row.look)&&row.look.length>0&&row.look.length<=32&&
          row.look.every(n=>Number.isSafeInteger(n)&&n>=0&&n<=255)),'Invalid local character '+key);
      const {position,forward,up,worldMove=false,look,velocity}=row, entity=row.entity??key;
      const controller=W.characters.create({tuning:row.tuning});
      initial[key]=controller.state({position,...(forward!==undefined&&{forward}),...(up!==undefined&&{up}),
        ...(velocity!==undefined&&{velocity})});
      specs[key]={entity,controller,worldMove,look};
      inputs['move.'+key]='vec3';inputs['vertical.'+key]='number';
      inputs['jump.'+key]='bool';inputs['climb.'+key]={type:'bool',default:true};
    }
    check(new Set(Object.values(specs).map(row=>row.entity)).size===Object.keys(specs).length,'Duplicate local character entity');
    const view=(actor,key)=>({...actor,id:key,entity:specs[key].entity,
      direction:actor.forward,bodyCenter:true,radius:specs[key].controller.tuning.radius,
      height:specs[key].controller.tuning.height,...(specs[key].look&&{look:specs[key].look})});
    function environment(query,row){
      return W.characters.fromQuery(query,{gravity,clearance,support,medium,supportPadding,exclude:row.entity});
    }
    return {initial:()=>initial,inputs,
      settleInitial(state,{query}){
        return Object.fromEntries(Object.entries(state).map(([key,actor])=>{
          const axis=environment(query,specs[key]).gravityAt(actor.position).up;
          const heading=V.norm(W.gravity.tangent(actor.forward,axis),V.perp(axis));
          return [key,{...actor,up:axis,forward:heading,gravityForward:heading}];
        }));
      },checkFields(query){
        W.gravity.checkField(query,gravity);
        const collision=query.field(clearance);
        check(collision?.type==='number'&&collision.units==='world','Local character clearance needs a world distance');
        if(medium){
          const field=query.field(medium);
          check(field?.type==='record'||field?.type==='number'&&field.units==='world','Local character medium needs a water record or world depth');
        }
        if(support)check(query.inspect().traces.some(trace=>trace.name===support||trace.name.endsWith('/'+support)),
          'Unknown local character support trace '+support);
      },
      dependencies:{reads:[gravity,clearance,medium].filter(Boolean)},
      step(state,ctx){
        return Object.fromEntries(Object.entries(state).map(([key,actor])=>{
          const spec=specs[key], move=ctx.input['move.'+key]??zero;
          const result=spec.controller.step(actor,{...(spec.worldMove?{moveWorld:move}:{move:[move[0],move[2]]}),
            vertical:ctx.input['vertical.'+key],jump:ctx.input['jump.'+key],climb:ctx.input['climb.'+key]},
          ctx.dt,environment(ctx.query,spec));
          for(const {type,...detail} of result.events)ctx.emit('character-'+type,{entity:spec.entity,...detail});
          return [key,result.actor];
        }));
      },validateState(state){
        check(record(state)&&Object.keys(state).length===Object.keys(specs).length&&Object.entries(state).every(([key,actor])=>
          own(specs,key)&&record(actor)&&vector(actor.gravityForward)&&vector(actor.up)&&V.len(actor.up)>1e-8),
        'Invalid saved local characters');
        for(const [key,actor] of Object.entries(state))specs[key].controller.state(actor);
      },*poseEntities(){for(const row of Object.values(specs))yield row.entity;},
      pose(state,entity){
        const key=Object.keys(specs).find(key=>specs[key].entity===entity), actor=key===undefined?null:state?.[key];
        return actor?{position:actor.position,rotation:W.gravity.basis(actor.up,actor.forward)}:null;
      },
      fields:{actors:{type:'record',role:'character-actors',read:({state})=>Q.ok(
        Object.fromEntries(Object.entries(state).map(([key,actor])=>[key,view(actor,key)])))}}};
  }
  W.runtime.register('characters',characters);
})(KIT);

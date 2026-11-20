/* Habitat policies and motion over the same fields exposed to queries. */
(function (K) {
  const W=K.world, P=K.procedural, Q=W.query, V=K.V;
  const {check,record,id,own,vector}=W.data, {bounds,zone}=W.fields;
  const up=[0,1,0], east=[1,0,0];
  function read(ctx,name,point,args) {
    return name?ctx.query.probe(name,point,args):null;
  }
  function heightAt(ctx,config,x,z) {
    const hit=read(ctx,config.bed,[x,0,z]);
    return hit?.status==='ok'&&Number.isFinite(hit.value)?hit.value:config.ground??0;
  }
  function clearance(ctx,config,point,exclude) {
    const hit=read(ctx,config.clearance,point,{exclude});
    return typeof hit?.value==='number'?hit.value:Infinity;
  }
  function wet(ctx,config,point) {
    const hit=read(ctx,config.water,point);
    return hit?.status==='ok'&&hit.value.depth>0?hit.value:null;
  }
  function supports(ctx,config,x,z,low,high,includeMaterial=false) {
    const output=read(ctx,config.support,[x,(low+high)*.5,z],{low,high,...(includeMaterial&&{includeMaterial})});
    if(output?.status==='ok'&&Array.isArray(output.value))return output.value;
    const y=heightAt(ctx,config,x,z);
    if(y<low||y>high)return [];
    const surface=W.materials.probe(ctx.query,config.surface,[x,y,z]);
    return [{y,normal:up,id:'ground',material:surface?.id??'ground',...(includeMaterial&&surface&&{surface})}];
  }
  function groundPlan(ctx,config,from,to,{radius=.13,maxWade=.16,maxSlope=.9,exclude}={}) {
    const region=config.bounds;
    const height=(x,z)=>config.support?
      (supports(ctx,config,x,z,region.min[1],region.max[1])[0]?.y??heightAt(ctx,config,x,z)):heightAt(ctx,config,x,z);
    if(!zone(from,region)||!zone(to,region))return {status:'outside',points:[]};
    const travel=(x,y,z)=>{
      const water=wet(ctx,config,[x,y,z]);
      if(water&&water.surface-y>maxWade)return Infinity;
      const path=read(ctx,config.wear,[x,y,z]);
      return path?.status==='ok'?(config.wearWeight??.8)*(1-W.fields.clamp(path.value,0,1)):0;
    };
    const start=[from[0],height(from[0],from[2]),from[2]], end=[to[0],height(to[0],to[2]),to[2]];
    if(Math.hypot(start[0]-end[0],start[2]-end[2])<1e-8)return {status:'ok',points:[start],length:0,cost:0};
    const options={bounds:region,height,clearance:(x,y,z)=>clearance(ctx,config,[x,y+Math.max(.15,radius),z],exclude),
      minClearance:radius,cost:travel,cell:config.cell??.25,maxSlope};
    const result=P.routes.terrain(start,end,options);
    const {route,...info}=result;
    if(route)return {...info,points:route.points};
    let blocked=null;
    for(let i=0;i<=48;i++){
      const p=V.lerp(start,end,i/48);
      p[1]=height(p[0],p[2]);
      const solid=read(ctx,config.clearance,V.add(p,[0,radius,0]),{exclude});
      if(solid?.status==='ok'&&solid.value<radius){
        blocked={kind:'clearance',point:p,body:solid.body??null};
        break;
      }
      if(travel(...p)===Infinity){blocked={kind:'water',point:p};break;}
    }
    return {...info,points:[],blocked};
  }
  function spatialPlan(ctx,config,from,to,body) {
    const radius=body.radius, {bounds:region}=config;
    function place(p) {
      if(!zone(p,region))return null;
      let point=p;
      if(body.mode==='swim'){
        const medium=wet(ctx,config,p);
        if(!medium||medium.depth<radius*.6)return null;
        point=[p[0],medium.surface-radius*.35,p[2]];
      }
      return clearance(ctx,config,point,body.entity)>=radius?point:null;
    }
    function link(a,b) {
      const steps=Math.max(1,Math.ceil(V.dist(a,b)/Math.max(.08,radius*.7)));
      if(steps>4096)return false;
      for(let i=1;i<=steps;i++)if(!place(V.lerp(a,b,i/steps)))return false;
      return true;
    }
    const first=place(from), last=place(to);
    if(!first||!last)return {status:'blocked-pin',points:[]};
    if(link(first,last))return {status:'ok',points:[first,last]};
    const {min,max}=region;
    const mid=V.lerp(from,to,.5), offset=Math.max(radius*5,.35), extras=[];
    for(const scale of [1,2,4])for(const direction of [[1,0,0],[-1,0,0],[0,0,1],[0,0,-1],[0,1,0],[0,-1,0]]){
      const p=V.mad(mid,direction,offset*scale).map((n,i)=>W.fields.clamp(n,min[i],max[i]));
      extras.push(p);
    }
    const points=[first,last,...[...(config.waypoints??[]),...extras].map(place).filter(Boolean)];
    const cost=points.map(()=>Infinity), previous=points.map(()=>-1), remaining=new Set(points.keys());
    cost[0]=0;
    while(remaining.size){
      let node=-1, best=Infinity;
      for(const k of remaining)if(cost[k]<best){best=cost[k];node=k;}
      if(node<0||node===1)break;
      remaining.delete(node);
      for(const k of remaining){
        const next=best+V.dist(points[node],points[k]);
        if(next>=cost[k]||!link(points[node],points[k]))continue;
        cost[k]=next;previous[k]=node;
      }
    }
    if(previous[1]<0)return {status:'unreachable',points:[]};
    const route=[];
    for(let i=1;i>=0;i=previous[i])route.unshift(points[i]);
    return {status:'ok',points:route,length:cost[1]};
  }
  function routeDependencies(config) {
    const {min,max} = config.bounds;
    const area = {axes:'xz',min:[min[0],min[2]],max:[max[0],max[2]]};
    return {reads:['bed','support','clearance','water','wear','surface'].flatMap(key=>
      typeof config[key] === 'string' ? [{field:config[key],bounds:area}] : [])};
  }
  function navigation(config) {
    bounds(config.bounds);
    check(Number.isFinite(config.cell??.25)&&(config.cell??.25)>0&&Number.isFinite(config.wearWeight??.8)&&
      (config.wearWeight??.8)>=0&&Array.isArray(config.waypoints??[])&&(config.waypoints??[]).length<=48&&
      (config.waypoints??[]).every(p=>vector(p))&&Number.isFinite(config.ground??0),'Invalid navigation domain');
    function route({query,target,args}) {
      check(target.point&&vector(args.to),'Route needs start and end XYZ points');
      const mode=args.mode??'walk', radius=args.radius??.13;
      check(['walk','swim','fly'].includes(mode)&&Number.isFinite(radius)&&radius>0,'Invalid travel mode or body radius');
      return Q.ok(mode==='walk'?groundPlan({query},config,target.point,args.to,args):
        spatialPlan({query},config,target.point,args.to,{mode,radius,entity:args.exclude}));
    }
    return {initial:()=>null,dependencies:routeDependencies(config),
      ...(config.surface!==undefined&&{checkFields:query=>W.materials.checkSurface(query,config.surface)}),fields:{
      height:{type:'number',units:'world',read:({query,target})=>target.point?
        Q.ok(heightAt({query},config,target.point[0],target.point[2])):Q.missing('point required')}
    },traces:{route:{run:route}}};
  }
  function habitat(config) {
    const species=config.species??{};
    check(record(species)&&Object.keys(species).length<=256,'Invalid species catalog');
    for(const [name,spec] of Object.entries(species)){
      check(id(name)&&record(spec)&&Array.isArray(spec.rules??[])&&(spec.rules??[]).length<=64&&
        Number.isFinite(spec.minimum??1)&&(spec.minimum??1)>=0&&(spec.minimum??1)<=1,'Invalid habitat profile '+name);
      const names=new Set();
      for(const rule of spec.rules??[]){
        check(record(rule)&&id(rule.id)&&!names.has(rule.id)&&(typeof rule.field==='string')!==!!rule.resource&&
          Number.isFinite(rule.weight??1)&&(rule.weight??1)>0,'Invalid habitat rule');
        names.add(rule.id);
        if(rule.resource){
          check(record(rule.resource)&&Number.isFinite(rule.resource.radius)&&rule.resource.radius>=0&&
            (rule.resource.route===undefined||typeof rule.resource.route==='string'),'Invalid habitat resource');
          Q.condition(rule.resource.where,{});
        }
        Q.condition(rule.when,{});
      }
    }
    function suitability({query,target,args}) {
      if(!target.point)return Q.missing('point required');
      const spec=species[args.species];
      if(!own(species,args.species))return Q.missing('unknown species','missing');
      let total=0, passed=0, required=true;
      const reasons=(spec.rules??[]).map(rule=>{
        let read;
        if(rule.resource){
          const {radius,where,route}=rule.resource;
          const candidates=query.spatial({point:target.point,radius,where}).sort((a,b)=>
            V.dist(a.position,target.point)-V.dist(b.position,target.point)).slice(0,32);
          const item=route?candidates.find(candidate=>{
            const result=query.trace(route,target,{to:candidate.position,...rule.resource.args});
            return result.status==='ok'&&result.value.status==='ok';
          }):candidates[0];
          read=item?Q.ok(item):Q.missing('no reachable matching resource','missing');
        }else read=query.probe(rule.field,target,rule.args);
        const weight=rule.weight??1;
        const matches=(read.status==='ok'||read.status===rule.status)&&Q.condition(rule.when,read.value);
        total+=weight;
        if(matches)passed+=weight;
        if(rule.required!==false&&!matches)required=false;
        return {id:rule.id,pass:matches,value:read.value??null,status:read.status};
      });
      const score=total?passed/total:1;
      return Q.ok({species:args.species,score,suitable:required&&score>=(spec.minimum??1),reasons});
    }
    return {initial:()=>null,fields:{suitability:{type:'record',read:suitability}}};
  }
  function agents(config,{catalog}) {
    const materialContacts=config.contactEvents==='material';
    check(config.contactEvents===undefined||typeof config.contactEvents==='boolean'||materialContacts,
      'contactEvents must be boolean or material');
    bounds(config.bounds);
    const initial={}, profiles=config.species??{}, source=config.agents??{}, poseCache=new WeakMap();
    check(record(profiles)&&record(source)&&Object.keys(source).length<=512,'Invalid creature catalog');
    for(const [key,spec] of Object.entries(profiles)){
      check(id(key)&&record(spec)&&['walk','swim','fly'].includes(spec.mode)&&
        Number.isFinite(spec.speed??1)&&(spec.speed??1)>=0&&Number.isFinite(spec.radius??.15)&&(spec.radius??.15)>=.03&&(spec.radius??.15)<=4&&
        (spec.height===undefined||Number.isFinite(spec.height)&&spec.height>=(spec.radius??.15)*2+.05&&spec.height<=12)&&
        (spec.stepUp===undefined||Number.isFinite(spec.stepUp)&&spec.stepUp>=0&&spec.stepUp<=10)&&
        (spec.drop===undefined||Number.isFinite(spec.drop)&&spec.drop>=0&&spec.drop<=16)&&
        Number.isFinite(spec.seekRange??3)&&(spec.seekRange??3)>0&&
        Number.isFinite(spec.maxWade??.14)&&(spec.maxWade??.14)>=0&&
        Number.isFinite(spec.stride??.38)&&(spec.stride??.38)>0&&
        (spec.contactLoad===undefined||Number.isFinite(spec.contactLoad)&&spec.contactLoad>=0&&spec.contactLoad<=1e12)&&
        Array.isArray(spec.limbs??[])&&(spec.limbs??[]).length<=16&&(spec.limbs??[]).every(p=>vector(p)),
        'Invalid movement profile '+key);
    }
    for(const [key,spec] of Object.entries(source)){
      check(id(key)&&record(spec)&&own(profiles,spec.species)&&vector(spec.position)&&
        (spec.goal===undefined||vector(spec.goal))&&(spec.entity===undefined||id(spec.entity)),'Invalid creature '+key);
      initial[key]={id:key,entity:spec.entity??key,species:spec.species,position:spec.position,
        goal:spec.goal??spec.position,home:spec.position,direction:east,radius:profiles[spec.species].radius??.15,
        route:[],cursor:0,mode:'idle',retry:0,travel:0,footprints:0,limbs:[],look:profiles[spec.species].look??[4,5,6,24]};
    }
    const policy = config.decisions === undefined ? null : W.agentDecisions.create(config.decisions, initial);
    const replan=config.replanTicks??24;
    check(Number.isSafeInteger(replan)&&replan>=1&&replan<=10000,'Invalid movement replanning interval');
    function fit(ctx,profile,p){
      if(!zone(p,config.bounds))return null;
      const water=wet(ctx,config,p);
      if(profile.mode==='swim'){
        if(!water||water.depth<profile.radius*.65)return null;
        p=[p[0],water.surface-profile.radius*.24,p[2]];
      }
      if(profile.mode==='walk'){
        const nearest=supports(ctx,config,p[0],p[2],p[1]-(profile.drop??.5),p[1]+(profile.stepUp??.3))[0];
        if(!nearest||water&&water.surface-nearest.y>profile.maxWade)return null;
        p=[p[0],nearest.y,p[2]];
      }
      return clearance(ctx,config,V.add(p,[0,profile.mode==='walk'?profile.radius*1.1:0,0]),profile.entity)>=profile.radius?p:null;
    }
    function suitable(ctx,agent,point){
      if(!config.habitat)return true;
      const result=ctx.query.probe(config.habitat,point,{species:agent.species});
      return result.status==='ok'&&result.value.suitable;
    }
    function choose(ctx,agent,profile){
      const point=fit(ctx,profile,agent.goal);
      if(point&&suitable(ctx,agent,point))return point;
      const max=profile.seekRange??3;
      for(const distance of [max*.2,max*.4,max*.7,max]){
        const angle=ctx.random(agent.id+'/search')*Math.PI*2;
        for(let i=0;i<8;i++){
          const a=angle+i*Math.PI/4;
          const found=fit(ctx,profile,V.add(agent.goal,[Math.cos(a)*distance,0,Math.sin(a)*distance]));
          if(found&&suitable(ctx,agent,found))return found;
        }
      }
      return null;
    }
    const profileFor = agent => ({radius:.15,maxWade:.14,entity:agent.entity,...profiles[agent.species]});
    const plan = (ctx, profile, from, goal) => profile.mode==='walk' ? groundPlan(ctx,config,from,goal,profile) :
      spatialPlan(ctx,config,from,goal,profile);
    function one(agent,ctx,contacts,dirty,directed=false){
      const profile=profileFor(agent);
      let position=fit(ctx,profile,agent.position), previous=agent;
      if(!position){
        if(directed)return {...agent,mode:'blocked',route:[],cursor:0,limbs:[]};
        position=choose(ctx,{...agent,goal:agent.position},profile);
        if(!position){
          if(agent.mode!=='dormant')ctx.emit('habitat-lost',{entity:agent.entity,at:agent.position});
          return {...agent,mode:'dormant',route:[],cursor:0,limbs:[]};
        }
        previous={...agent,route:[],cursor:0,retry:0};
        ctx.emit('habitat-relocate',{entity:agent.entity,at:position});
      }
      let {route,cursor,retry,travel,footprints}=previous;
      const goal=directed ? fit(ctx,profile,agent.goal) : choose(ctx,agent,profile);
      if(!goal || directed&&!suitable(ctx,agent,goal))return {...previous,position,mode:'waiting',route:[],cursor:0};
      if(V.dist(position,goal)<profile.radius*.65)return {...previous,position,mode:'rest',route:[],cursor:0};
      let corridor;
      if (dirty && route.length) {
        const envelope = P.spatial.boxOf([position,...route.slice(cursor)]);
        envelope.min[1] = Math.min(0,envelope.min[1]-(profile.drop??.5));
        envelope.max[1] = Math.max(0,envelope.max[1]+(profile.height??profile.radius*2));
        const area = P.spatial.expand(envelope,profile.radius);
        if (ctx.spatial.changes(area).length) corridor=area;
      }
      if(ctx.tick>=retry||!route.length||corridor){
        const result=plan(ctx,profile,position,goal);
        route=result.points??[];
        cursor=route.length>1?1:0;
        retry=ctx.tick+(route.length?replan:Math.min(6,replan));
        if (corridor) ctx.spatial.rebuilt('agent-route',{entity:agent.entity,status:result.status},corridor);
      }
      if(!route[cursor])return {...previous,position,mode:'blocked',route,cursor,retry};
      const aim=V.sub(route[cursor],position), distance=V.len(aim), step=Math.min(distance,(profile.speed??1)*ctx.dt);
      const desired=distance>1e-8?V.mad(position,aim,step/distance):position;
      let moved, lastSupports=[];
      if(profile.mode==='walk'){
        const requested=profile.stepUp??Math.min(.3,profile.radius*.8);
        const bodyHeight=profile.height??Math.min(12,profile.radius*2+requested+.08);
        const stepUp=Math.min(requested,bodyHeight-profile.radius*2-.025);
        const body=P.traversal.create({radius:profile.radius,height:bodyHeight,
          stepUp,stepDown:profile.drop??.5,
          supports:(x,z,low,high)=>supports(ctx,config,x,z,low,high,materialContacts).filter(s=>{
            const liquid=wet(ctx,config,[x,s.y,z]);
            return !liquid||liquid.surface-s.y<=profile.maxWade;
          }),
          clearance:point=>clearance(ctx,config,point,profile.entity)});
        const result=body.move(position,[desired[0]-position[0],desired[2]-position[2]],{trace:true});
        moved=result.foot;
        lastSupports=result.contacts;
      }else moved=fit(ctx,profile,desired)??position;
      const delta=V.sub(moved,position), movedBy=V.len(delta);
      if(movedBy<1e-8&&step>1e-8)return {...previous,position,mode:'blocked',route:[],cursor:0,retry:ctx.tick+1};
      if(distance<=step+profile.radius*.35)cursor++;
      const direction=movedBy>1e-8?V.norm(delta):previous.direction;
      const stride=profile.stride??.38;
      if(profile.mode==='walk'){
        let foot=position;
        for(const sample of lastSupports){
          const stepDistance=Math.hypot(sample.foot[0]-foot[0],sample.foot[2]-foot[2]);
          if(stepDistance>1e-9){
            const accumulated=travel+stepDistance,count=Math.floor(accumulated/stride);
            for(let n=0;n<count;n++){
              const at=V.lerp(foot,sample.foot,W.fields.clamp((stride-travel+n*stride)/stepDistance,0,1));
              const entry=catalog?.getMaterial(sample.material), cue=entry?.material.sounds?.step;
              const row={entity:agent.entity,point:at,support:sample.support,material:sample.material??null,weight:profile.weight??1,
                ...(cue&&{cue})};
              if(materialContacts){
                const surface=sample.surface??(entry&&W.materials.profile(entry));
                contacts.push(W.contactEffects.capture(ctx,row,contacts.length,'step',{speed:movedBy/ctx.dt,
                  load:profile.contactLoad??10,travel:stride,normal:sample.normal,heading:direction,profile:surface}));
              }else contacts.push(row);
              footprints++;
            }
            travel=accumulated-count*stride;
          }
          foot=sample.foot;
        }
      }
      const side=V.norm(V.cross(up,direction),[0,0,1]);
      const limbs=(profile.limbs??[]).map((offset,i)=>{
        const desired=V.add(V.mad(V.mad(moved,direction,offset[0]),side,offset[2]),[0,offset[1],0]);
        const ground=supports(ctx,config,desired[0],desired[2],desired[1]-.65,desired[1]+.26)[0];
        const phase=(travel/stride+i/(profile.limbs.length||1))%1;
        return {point:ground?[desired[0],ground.y+(phase>.57?Math.sin((phase-.57)*Math.PI/.43)*.09:0),desired[2]]:desired,
          planted:!!ground&&phase<=.57,support:ground?.id??null};
      });
      return {...previous,position:moved,direction,route,cursor,retry,mode:profile.mode,travel,footprints,limbs};
    }
    return {initial:()=>({agents:initial,contacts:[],...(policy&&{decisions:policy.initial})}),dependencies:routeDependencies(config),
    ...(config.contactEvents&&{outputs:{contacts:'event'},output:state=>({contacts:state.contacts})}),
    ...((config.surface!==undefined||policy)&&{checkFields(query){
      if(config.surface!==undefined)W.materials.checkSurface(query,config.surface);
      policy?.checkFields(query);
    }}),validateState(state){
      check(record(state?.agents)&&Array.isArray(state.contacts)&&Object.keys(state.agents).length===Object.keys(initial).length&&
        Object.entries(state.agents).every(([key,agent])=>own(initial,key)&&own(profiles,agent.species)&&vector(agent.position)&&
          vector(agent.goal)&&vector(agent.direction)&&Array.isArray(agent.route)&&agent.route.every(p=>vector(p))),
        'Invalid agent checkpoint');
      policy?.validate(state.decisions);
    },checkAction(type,args){
      check(own(initial,args.agent)&&vector(args.to),'Invalid creature destination');
      check(!policy?.managed(args.agent),'The activity policy owns this creature destination');
    },actions:{
      seek(state,{agent,to},ctx){
        ctx.emit('destination',{entity:state.agents[agent].entity,at:to});
        return {...state,agents:{...state.agents,[agent]:{...state.agents[agent],goal:to,route:[],cursor:0,retry:0}}};
      }
    },step(state,ctx){
      const contacts=[], agents={}, decisions=policy?{}:null, dirty=ctx.spatial?.changes().length>0;
      for(const key of Object.keys(state.agents).sort()){
        const agent=state.agents[key];
        if(!policy?.managed(key)){
          agents[key]=one(agent,ctx,contacts,dirty);
          continue;
        }
        const profile=profileFor(agent);
        let origin;
        const movement={
          fit(point){
            const fitted=fit(ctx,profile,point);
            return fitted&&suitable(ctx,agent,fitted)?fitted:null;
          },
          plan(goal){
            if(origin===undefined)origin=fit(ctx,profile,agent.position);
            return origin?plan(ctx,profile,origin,goal):{status:'origin-unfit',points:[]};
          }
        };
        const {next,route}=policy.select(state.decisions[key],agent,ctx,movement);
        if(!next.choice){
          agents[key]={...agent,goal:agent.position,route:[],cursor:0,mode:'rest'};
          decisions[key]=next;
          continue;
        }
        if(next.phase==='blocked'){
          agents[key]=agent;
          decisions[key]=next;
          continue;
        }
        const directed=route?{...agent,goal:next.choice.point,route,cursor:route.length>1?1:0,retry:ctx.tick+replan}:agent;
        agents[key]=one(directed,ctx,contacts,dirty,true);
        decisions[key]=policy.observe(next,agents[key],ctx,movement);
      }
      return {agents,contacts,...(policy&&{decisions})};
    },*poseEntities(state){
      for(const agent of Object.values(state?.agents??{}))yield agent.entity;
    },pose(state,entity){
      if(!state)return null;
      let poses=poseCache.get(state.agents);
      if(!poses){
        poses=new Map();
        for(const agent of Object.values(state.agents))
          if(agent.mode!=='dormant'&&!poses.has(agent.entity))poses.set(agent.entity,agent);
        poseCache.set(state.agents,poses);
      }
      return poses.get(entity);
    },fields:{
      agents:{type:'record',read:({state})=>Q.ok(state.agents)},
      contacts:{type:'records',units:'world',read:({state})=>Q.ok(state.contacts)},
      ...(policy&&{decisions:{type:'record',read:({state})=>Q.ok(state.decisions)}})
    },...(policy&&{traces:{why:{run({state,args,target}){
      const name=args.agent??target.entity;
      const key=own(state.decisions,name) ? name : Object.keys(state.decisions).find(key=>state.agents[key].entity===name);
      const decision=own(state.decisions,key) ? state.decisions[key] : null;
      return decision ? Q.ok(decision) : Q.missing('unknown managed agent','missing');
    }}}})};
  }
  W.runtime.register('navigation',navigation);
  W.runtime.register('habitat',habitat);
  W.runtime.register('agents',agents);
  W.movement=Object.freeze({groundPlan,spatialPlan});
})(KIT);

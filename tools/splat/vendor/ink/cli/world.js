const fs = require('node:fs');
const path = require('node:path');
const { randomUUID } = require('node:crypto');

const read = file => JSON.parse(fs.readFileSync(path.resolve(file),'utf8'));
const parse = input => JSON.parse(String(input));
const numbers = value => String(value).split(',').map(Number);
function ensure(condition,message) {
  if (!condition) throw Error(message);
}
function write(file,value) {
  ensure(typeof file === 'string' && file.length > 0,'Expected an output file');
  const destination = path.resolve(file);
  fs.mkdirSync(path.dirname(destination),{recursive:true});
  const temporary = destination+'.'+randomUUID()+'.tmp';
  try {
    fs.writeFileSync(temporary,JSON.stringify(value,null,2)+'\n',{flag:'wx'});
    fs.renameSync(temporary,destination);
  } finally {
    if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
  }
}
function target(opt) {
  if (opt.select !== undefined) {
    ensure(opt.at === undefined && opt.entity === undefined && opt.socket === undefined, 'Use --select by itself');
    return parse(opt.select);
  }
  if (opt.at !== undefined) return {point:numbers(opt.at)};
  if (opt.entity !== undefined) return {entity:opt.entity,...(opt.socket?{socket:opt.socket}:{})};
  return {};
}

module.exports = function createCLI({kit,build,pose,dataScene,opt,renderOptions,atmosphereEmittersOption,effectPalettesOption,stabilityOption,artDirectionOption,silhouetteOption,horizonOption,skyTransitionsOption,weatherTracksOption,skyOptions,shot,shotReplay,shotRender}) {
  const W = kit.KIT.world, R = W.runtime;
  const args = () => opt.args ? parse(opt.args) : {};
  function sampleArgs() {
    if (opt.explain === undefined) return args();
    ensure(opt.explain === true,'Use --explain without a value');
    return {...args(),explain:true};
  }
  function fieldMetadata(query,name) {
    const descriptor = query.field?.(name);
    return descriptor?.spatial ? {type:descriptor.type,units:descriptor.units,spatial:descriptor.spatial} : {};
  }
  const respond = value => {
    if (opt.out) write(opt.out,value);
    else process.stdout.write(JSON.stringify(value,null,opt.json?0:2)+'\n');
  };
  function document(world) {
    if (opt['asset-pack'] === undefined) return {world};
    const packs = require('./asset-pack.js').install(kit.KIT.authoring.assetPacks, world.assetPacks, opt['asset-pack']);
    return {world:{...world,assetPacks:packs}};
  }
  function load(file, { lookPreview = false } = {}) {
    ensure(typeof file === 'string','Expected a scene or run file');
    if (/\.(js|cjs)$/i.test(file)) {
      const factory = require(path.resolve(file)), value = typeof factory === 'function' ? factory(kit) : factory;
      return value.format===W.format ? document(value) : value.simulation ? document(value.simulation) : {legacy:file};
    }
    if (/\.json$/i.test(file)) {
      const value = read(file);
      if (value.format === W.format) return document(value);
      if (!lookPreview && [R.checkpointFormat,R.runFormat].includes(value.format))
        ensure(opt['asset-pack']===undefined,'Recorded runs and checkpoints keep their original asset packs');
      if (value.format === R.checkpointFormat) return {world:value.world,checkpoint:value};
      if (value.format === R.runFormat) return {world:value.end.world,checkpoint:value.end,log:value};
      return {legacy:file,document:value};
    }
    return {legacy:file};
  }
  function runtime(input, profile = false) {
    ensure(input.world,'The scene must expose an Ink Studio world manifest');
    const source = !input.checkpoint && (opt.seed !== undefined || opt.dt !== undefined)
      ? {...input.world,...(opt.seed===undefined?{}:{seed:Number(opt.seed)}),...(opt.dt===undefined?{}:{dt:Number(opt.dt)})}
      : input.world;
    if (input.checkpoint) ensure(opt.seed===undefined && opt.dt===undefined,'A resumed run uses its checkpoint seed and timestep');
    return R.create(source,{checkpoint:input.checkpoint,profile});
  }
  function to(run) {
    const {tick,world} = run.view(), modes = [opt.ticks,opt.steps,opt.t].filter(v => v !== undefined);
    ensure(modes.length<=1 && modes.every(v => v!==true && Number.isFinite(Number(v))),'Specify one finite time using --ticks, --steps or --t');
    return opt.ticks !== undefined ? Number(opt.ticks) :
      opt.steps !== undefined ? tick + Number(opt.steps) :
      opt.t !== undefined ? Math.floor(Number(opt.t)/world.dt+1e-10) :
      world.scenario?.until !== undefined ? Math.max(tick,world.scenario.until) : tick;
  }
  function schedule(run) {
    if (opt.actions) run.schedule(read(opt.actions));
  }
  function advanceVisual(run, tick) {
    const emitters = kit.KIT.atmosphere.emitters;
    const { world, tick: start } = run.view();
    const program = emitters.settings(W.visualEnvironment(world).atmosphereEmitters, atmosphereEmittersOption?.());
    const targets = program?.targets.filter(target => target.entity !== undefined);
    if (!targets?.length || tick < start) {
      run.advance(tick);
      return;
    }
    const history = emitters.history(targets, program.lifetime);
    function observe(view, query) {
      history.capture(view.time, target => emitters.entityPose(query, target));
    }
    run.advance(Math.max(start, tick-Math.ceil(program.lifetime/world.dt)-1));
    observe(run.view(), run.query());
    run.advance(tick, {onTick:observe});
    return history.at;
  }
  function visualSnapshot(input) {
    let run = runtime(input);
    const tick = opt.steps === undefined && opt.ticks === undefined && opt.t === undefined ? run.view().tick : to(run);
    if (input.log && tick < run.view().tick) {
      const origin = input.log.origin;
      run = runtime({ world: origin.world, checkpoint: origin });
      run.schedule(input.log.commands);
    }
    schedule(run);
    const atmospherePose = advanceVisual(run,tick);
    const view = run.view(), Preview = require('./look-preview.js');
    const world = Preview.withAlbedo(() => W.visual(kit, view, run.query()));
    return { ...world, ...(atmospherePose && {atmospherePose}), id: view.world.id, assetPacks: view.world.assetPacks,
      ...(!input.checkpoint && { lookPreviewPacks: view.world.assetPacks }) };
  }
  function environmentSnapshot(file) {
    const input=load(file);
    return input.world ? visualSnapshot(input) : null;
  }
  function lookSnapshot(file) {
    const input = load(file, { lookPreview: true });
    return input.world ? visualSnapshot(input) : null;
  }
  function view(file) {
    const input = load(file);
    if (input.world) {
      const run = runtime(input);
      if (opt.actions || opt.ticks !== undefined || opt.steps !== undefined || opt.t !== undefined) {
        schedule(run);
        run.advance(to(run));
      }
      return run.query();
    }
    const world = build(input.legacy);
    const t = Number(opt.t ?? 0);
    ensure(Number.isFinite(t) && t>=0,'Invalid probe time');
    pose(world,t);
    return W.query.fromScene(world,t);
  }
  function inspectLook(file) {
    return view(file).inspectLook({renderer:opt.renderer});
  }
  function assert(run,rules) {
    ensure(Array.isArray(rules) && rules.length<=10000,'Expected an assertion list');
    const out=[], temporal=[];
    const log=run.recording(), tick=run.view().tick;
    function evaluate(rule,query,at) {
      const sample=query.probe(rule.field,rule.at,rule.args);
      return {id:rule.id,tick:at,pass:sample.status===(rule.status??'ok')&&W.query.condition(rule.when,sample.value),result:sample};
    }
    for(const [i,raw] of rules.entries()){
      ensure(raw&&typeof raw==='object','Expected assertion '+(i+1));
      const rule={id:i+1,...raw};
      if(rule.profile!==undefined){
        const metric=rule.metric??'ms', data=run.profile()[rule.profile]?.[metric];
        ensure(['ms','maxMs','calls'].includes(metric)&&Number.isFinite(rule.max)&&rule.max>=0,'Invalid profile assertion');
        out[i]={id:rule.id,pass:Number.isFinite(data)&&data<=rule.max,result:{metric,value:data??null,max:rule.max}};
        continue;
      }
      ensure(typeof rule.field==='string','Assertion '+rule.id+' needs a field');
      if(rule.tick===undefined&&rule.byTick===undefined){out[i]=evaluate(rule,run.query(),tick);continue;}
      const at=rule.tick??rule.byTick;
      ensure((rule.tick===undefined||rule.byTick===undefined)&&Number.isSafeInteger(at)&&at>=log.origin.tick&&at<=tick,
        'Assertion tick lies outside the run');
      temporal.push({i,rule,at});
    }
    if(temporal.length){
      const replay=R.create(log.origin.world,{checkpoint:log.origin});
      replay.schedule(log.commands);
      const exact=new Map(), deadlines=[];
      for(const item of temporal){
        if(item.rule.tick===undefined)deadlines.push(item);
        else {
          const group=exact.get(item.at)??[];
          group.push(item);
          exact.set(item.at,group);
        }
      }
      function sample(frame,query){
        for(const {i,rule} of exact.get(frame.tick)??[])out[i]=evaluate(rule,query,frame.tick);
        for(const {i,rule,at} of deadlines){
          if(out[i])continue;
          const result=evaluate(rule,query,frame.tick);
          if(result.pass||frame.tick===at)out[i]=result;
        }
      }
      sample(replay.view(),replay.query());
      replay.advance(Math.max(...temporal.map(item=>item.at)),{onTick:sample});
    }
    return out;
  }
  function summary(run, checks) {
    const checkpoint = run.checkpoint(), {world,tick} = checkpoint;
    const rates = run.rates?.();
    return {id:world.id,seed:world.seed,dt:world.dt,tick,time:tick*world.dt,...(rates && {rates}),
      systems:Object.keys(checkpoint.states),commands:run.commandCounts(),events:checkpoint.history.length,historyDropped:checkpoint.dropped,
      scenario:run.scenario,...(checks?{checks}:{}),...(opt.profile?{profile:run.profile()}:{})};
  }
  function finish(run) {
    const checks = opt.assert ? assert(run,read(opt.assert)) : null;
    if (opt.checkpoint) write(opt.checkpoint,run.checkpoint());
    if (opt.record) write(opt.record,run.recording());
    respond(summary(run,checks));
    if (checks?.some(row => !row.pass) || opt.scenario && ['fail','timeout'].includes(run.scenario.status))
      process.exitCode = 2;
  }
  function getCheckpoint(file) {
    const input = load(file);
    ensure(input.checkpoint,'Expected a checkpoint or recording');
    if (opt.ticks === undefined || Number(opt.ticks)===input.checkpoint.tick) return input.checkpoint;
    ensure(input.log,'Earlier ticks require a recording');
    const at=Number(opt.ticks);
    ensure(Number.isSafeInteger(at)&&at>=input.log.origin.tick&&at<=input.log.end.tick,'Tick lies outside the recording');
    const run = R.create(input.log.origin.world,{checkpoint:input.log.origin});
    run.schedule(input.log.commands);
    run.advance(at);
    return run.checkpoint();
  }
  function dependencyReport(file) {
    ensure(typeof file==='string','Supply a world, recording or retained dependency driver');
    if (/\.(js|cjs)$/i.test(file)) {
      const source = require(path.resolve(file));
      if (typeof source.dependencies === 'function') {
        ensure(['ticks','steps','t','actions'].every(key=>opt[key]===undefined),
          'Retained dependency drivers supply their own edits');
        return Promise.resolve(source.dependencies(kit)).then(respond);
      }
    }
    const input = load(file);
    let run = runtime(input);
    if (input.log) {
      const origin = input.log.origin;
      run = R.create(origin.world,{checkpoint:origin});
      run.schedule(input.log.commands);
    }
    schedule(run);
    const start = run.view().tick;
    const end = input.log && opt.ticks===undefined && opt.steps===undefined && opt.t===undefined ? input.log.end.tick : to(run);
    const ticks = [];
    run.advance(end,{onTick(view) {
      const {changes,affected,work,pending} = run.dependencies();
      if (changes.length || work.length || pending.length) {
        ensure(ticks.length<10000,'Spatial dependency report exceeds its tick budget');
        ticks.push({tick:view.tick,changes,affected,work,...(pending.length && {pending})});
      }
    }});
    return respond({format:'ink-studio/spatial-dependencies',version:1,id:run.view().world.id,
      fromTick:start,toTick:end,declarations:run.dependencies().declarations,ticks});
  }
  function sim([mode,file,other]) {
    switch (mode) {
      case 'run':
      case 'resume':
      case 'fork': {
        const input = load(file);
        ensure(mode==='run' || input.checkpoint,'Expected a checkpoint or recording to resume or fork');
        const run = runtime(input,!!(opt.profile||opt.assert));
        schedule(run);
        run.advance(to(run),{stopOnOutcome:!!opt.scenario});
        finish(run);
        break;
      }
      case 'dependencies': return dependencyReport(file);
      case 'reset': {
        const input=load(file);
        finish(input.log?R.create(input.log.origin.world,{checkpoint:input.log.origin}):runtime(input));
        break;
      }
      case 'replay': {
        const input=load(file);
        ensure(input.log,'Expected a run recording');
        finish(R.replay(input.log,{profile:!!(opt.profile||opt.assert)}));
        break;
      }
      case 'diff': {
        const a=getCheckpoint(file), b=getCheckpoint(other);
        if(!opt.field){respond(R.diff(a,b));break;}
        ensure(a.tick===b.tick,'Simulation diff needs matched ticks');
        const queries=[a,b].map(checkpoint=>R.create(checkpoint.world,{checkpoint}).query());
        const spec=opt.spec?read(opt.spec):null;
        const readings=queries.map(query=>spec?query.export(opt.field,spec,args()):query.probe(opt.field,target(opt),args()));
        respond({tick:a.tick,field:opt.field,edits:W.query.keyedChanges(...readings),...(spec?{grid:readings[0].grid}:{})});
        break;
      }
      case 'sweep': {
        const spec=read(other);
        ensure(Array.isArray(spec) && spec.length>0 && spec.length<=2000,'Expected a bounded sweep list');
        const lookPreview = spec.some(row => row && Object.hasOwn(row, 'look'));
        const input=load(file,{lookPreview});
        ensure(input.world,'Sweep needs a simulation world');
        if (lookPreview) {
          const { report } = require('./look-compare.js').compare(visualSnapshot(input), spec, kit,
            renderOptions({ w: Number(opt.w ?? 720), h: Number(opt.h ?? 475) }), { opt, file: other });
          const { results, ...summary } = report;
          respond({ ...summary, runs: results });
          break;
        }
        const runs=spec.map((row,i)=>{
          let source=input.world;
          if (row.edits || row.seed!==undefined) {
            ensure(!input.checkpoint,'Use scheduled actions to vary a checkpoint branch');
            if (row.edits) source=W.apply(W.manifest(source),row.edits).world;
            if (row.seed!==undefined) source={...source,seed:row.seed};
          }
          const run=runtime({...input,world:source},!!(opt.profile||row.assert));
          run.schedule(row.actions??[]);
          run.advance(row.ticks??to(run),{stopOnOutcome:!!opt.scenario});
          const measurements=(row.probes??[]).map(spec=>({field:spec.field,...run.query().probe(spec.field,spec.at,spec.args)}));
          return {id:row.id??i, ...summary(run,row.assert?assert(run,row.assert):null),measurements};
        });
        respond({runs});
        if (runs.some(row => row.checks?.some(check => !check.pass))) process.exitCode=2;
        break;
      }
      case 'render': {
        const recording=shotReplay?.runtime;
        const run=recording ? R.create(recording.origin.world,{checkpoint:recording.origin}) : runtime(load(file));
        if (recording) run.schedule(recording.commands);
        else schedule(run);
        ensure(typeof opt.out==='string','Simulation render needs --out image.png');
        const output=path.resolve(opt.out), diagnostics=require('./look-preview.js').preview(opt);
        const suffixes=diagnostics?.suffixes ?? [];
        shot?.destination(output,suffixes);
        const atmospherePose=advanceVisual(run,recording?.end.tick ?? to(run));
        if (recording) ensure(W.data.equal(run.checkpoint(),recording.end),
          'Shot simulation checkpoint diverged at tick '+recording.end.tick);
        if (shot) {
          shot.seed(run.view().world.seed);
          shot.runtime(run.recording());
        }
        const world=W.visual(kit,run.view(),run.query());
        if (atmospherePose) world.atmospherePose=atmospherePose;
        const studio=require('../index.js');
        const image=studio.render(world,{w:Number(opt.w??720),h:Number(opt.h??475),colored:!!opt.colored,
          colorCurves:opt['color-curves']==='off'?false:undefined,
          colorLut:require('./lut.js').override(opt.lut),
          paletteConstraints:require('./palette-constraints.js').override(opt['palette-constraints']),
          water:opt.water==='off'?false:undefined, effectPalettes:effectPalettesOption?.(), stable:stabilityOption?.(), artDirection:artDirectionOption?.(), silhouetteProtection:silhouetteOption?.(),
          horizonBands:horizonOption?.(), skyTransitions:skyTransitionsOption?.(), weatherTracks:weatherTracksOption?.(),
          ...skyOptions?.(),
          atmosphere:opt.atmosphere==='off'?false:undefined, atmosphereEmitters:atmosphereEmittersOption?.(),
          coverageAware:opt['coverage-aware']===undefined?undefined:opt['coverage-aware']!=='off',
          lookMasks:opt['look-masks']==='off'?false:undefined,
          colorStack:require('./color-stack.js').override(opt['color-stack']),t:run.view().time,
          ...diagnostics?.settings,...shotRender});
        fs.mkdirSync(path.dirname(output),{recursive:true});
        require('./png.js').write(output,image.w,image.h,image.rgb);
        diagnostics?.capture(image,1);
        diagnostics?.write(output,{times:[run.view().time]});
        shot?.finish(output,{suffixes});
        break;
      }
      default: throw Error('Use sim run|resume|fork|reset|replay|diff|sweep|render|dependencies');
    }
  }
  function applyEdits(input, edits, { dryRun = false } = {}) {
    const isWorld = Boolean(input.world), retained = input.document?.format === 'ink-studio/authoring';
    const spec = isWorld || retained ? input.world ?? input.document : document(input.document).world;
    const validate = isWorld ? R.validate : retained ? kit.KIT.authoring.data.documentView :
      value => dataScene(input.legacy,value,{installedPacks:true});
    const before = validate(spec);
    const source = isWorld ? before : kit.KIT.procedural.data.freeze(W.data.copy(spec));
    let after;
    const result = W.apply(source,edits,{validate:value=>{after=validate(value);}});
    const looks = require('./look-edits.js');
    if (retained || !looks.touches(source,result.world,result.paths,W.data)) return result;
    function inspect(value) {
      const query = isWorld ? R.create(value,{validated:true}).query() : W.query.fromScene(value.build(value.seed));
      return query.inspectLook({renderer:opt.renderer,definitions:dryRun});
    }
    const report = require('./look.js').assertValid(inspect(after));
    return dryRun ? {...result,lookBindings:looks.impact(inspect(before),report,W.data.equal)} : result;
  }
  function scene([mode,file,reference]) {
    const input=load(file);
    if (mode==='apply'){
      ensure(input.document || input.world && !input.checkpoint,'Expected a world manifest or JSON scene');
      const dryRun = Boolean(opt['dry-run']);
      if (dryRun && typeof opt.out === 'string')
        ensure(![file,reference].some(input=>typeof input==='string'&&path.resolve(input)===path.resolve(opt.out)),
          'The dry-run report needs a separate output path');
      const { world, paths, lookBindings } = applyEdits(input,read(reference),{dryRun});
      respond(dryRun?{changed:paths,...(lookBindings&&{lookBindings})}:world);
      return;
    }
    if(mode==='promote'){
      ensure(input.checkpoint&&typeof reference==='string','Promote needs a run or checkpoint and a trace name');
      const options=args(), trace=runtime(input).query().trace(reference,target(opt),options);
      ensure(trace.status==='ok',trace.reason??'Trace failed');
      const result=W.history.trail(input.world,opt.as,trace.value,options);
      R.validate(result.world);
      respond(opt['dry-run']?{changed:result.paths}:result.world);
      return;
    }
    ensure(input.world && !input.checkpoint,'Expected a world manifest');
    const world=R.validate(input.world);
    let result;
    if (mode==='capture') result=W.capture(world,reference,opt.as);
    else if (mode==='stamp') result=W.stamp(world,reference,opt.as,opt.args?args():{});
    else if (mode==='remix') result=W.remix(world,reference,opt.as,opt.edits?read(opt.edits):[]);
    else if (mode==='history') result=W.history.generate(world,read(reference));
    else throw Error('Use scene apply|stamp|remix|capture|history|promote');
    R.validate(result.world);
    respond(opt['dry-run']?{changed:result.paths,...(result.events?{events:result.events}:{})}:result.world);
  }
  function execute(command,pos) {
    const [file,name] = pos;
    switch (command) {
      case 'inspect': {
        const query=view(file), where=opt.where?parse(opt.where):undefined;
        if (opt.select !== undefined || opt.targets) {
          ensure(opt.near===undefined && opt.where===undefined,'Use --select by itself');
          respond({targets:query.select(opt.select===undefined?undefined:target(opt))});
          break;
        }
        respond(opt.near?query.spatial({point:numbers(opt.near),radius:Number(opt.radius),where}):query.inspect({where}));
        break;
      }
      case 'probe': {
        ensure(typeof opt.field==='string'||opt.select!==undefined||opt.at!==undefined||opt.entity!==undefined,
          'Use --field to select a query');
        const field=opt.field??(opt.at!==undefined||opt.entity!==undefined?'look/sample':'look/output');
        if (field === 'look/sample') {
          ensure(opt.socket===undefined && !(opt.select!==undefined && opt.entity!==undefined),
            'Use one render selector with --select or --entity');
          ensure(opt.at===undefined||typeof opt.at==='string'&&opt.at.split(',').every(value=>value.trim()),
            '--at needs three finite comma-separated coordinates');
          const selector=opt.select!==undefined?parse(opt.select):opt.entity!==undefined?{entity:opt.entity}:undefined;
          const options={...args(),...(opt.at!==undefined&&{at:numbers(opt.at)}),
            ...(opt.radius!==undefined&&{radius:opt.radius===true?NaN:Number(opt.radius)})};
          respond(view(file).probe(field,selector,options));
          break;
        }
        const site=['look/output','look/provenance'].includes(field)&&opt.select===undefined&&opt.at===undefined&&opt.entity===undefined?undefined:target(opt);
        respond(view(file).probe(field,site,sampleArgs()));
        break;
      }
      case 'trace':
        ensure(typeof name==='string','Supply a named trace');
        respond(view(file).trace(name,target(opt),args()));
        break;
      case 'field': {
        ensure(typeof name==='string'&&typeof opt.spec==='string','Provide a field and --spec file.json');
        const spec=read(opt.spec), sample=sampleArgs();
        if (spec.ticks) {
          const run=runtime(load(file));
          schedule(run);
          ensure(Array.isArray(spec.ticks)&&spec.ticks.length<=10000,'Invalid sample ticks');
          const ticks=spec.ticks.slice().sort((a,b)=>a-b), metadata=fieldMetadata(run.query(),name);
          if (spec.spatial) {
            const samples=[], limit=100000;
            let count=0;
            for(const tick of ticks){
              run.advance(tick);
              const frame=run.query().export(name,spec.spatial,sample);
              count+=frame.samples.length;
              ensure(count<=limit,'Time-series spatial sample budget exceeded');
              samples.push(frame);
            }
            respond({field:name,...metadata,series:samples});
          } else respond({field:name,...metadata,series:ticks.map(tick=>{
            run.advance(tick);
            return {tick,time:run.view().time,...run.query().probe(name,spec.at??target(opt),sample)};
          })});
        } else respond(view(file).export(name,spec,sample));
        break;
      }
      case 'scene': scene(pos); break;
      case 'sim': return sim(pos);
      default: throw Error('Unknown world command');
    }
  }
  function validate(file) {
    if (opt.select !== undefined) {
      const query=view(file), selector=target(opt), targets=query.select(selector);
      ensure(targets.length>0,'No render target matches '+JSON.stringify(selector));
      require('./look.js').assertValid(query.inspectLook({renderer:opt.renderer}));
      respond({valid:true,selector,targets});
      return true;
    }
    if(opt.world){
      const input=load(opt.world);
      ensure(input.world||input.document,'Provide a scene, world or checkpoint with --world');
      const edits=read(file);
      if(opt.kind==='edits') applyEdits(input,edits);
      else if(opt.kind==='actions') runtime(input).schedule(edits);
      else throw Error('Validation with --world needs --kind edits or actions');
      respond({valid:true,kind:opt.kind});
      return true;
    }
    if (!/\.json$/i.test(file??'')) return false;
    const raw=read(file);
    if (raw.format==='ink-studio/authoring') {
      kit.KIT.authoring.data.documentView(raw);
      respond({valid:true,format:raw.format});
      return true;
    }
    if (raw.format!==W.format && raw.format!==R.checkpointFormat && raw.format!==R.runFormat) return false;
    const run = raw.format===R.runFormat ? R.replay(raw) :
      raw.format===R.checkpointFormat ? R.create(raw.world,{checkpoint:raw}) : undefined;
    const world = run?.view().world ?? R.validate(document(raw).world);
    const visual = world.visual;
    if (opt.renderer || visual?.look || visual?.terrainSurface || visual?.terrainLookAsset ||
        Object.values(world.entities).some(entity=>entity.lookAsset || entity.visual?.lookAsset || entity.visual?.surface)) {
      const query = opt.actions || opt.ticks !== undefined || opt.steps !== undefined || opt.t !== undefined ?
        view(file) : (run ?? R.create(world,{validated:true})).query();
      const report = require('./look.js').assertValid(query.inspectLook({renderer:opt.renderer}));
      if (opt.json) { respond({format:raw.format,...report}); return true; }
    }
    respond({valid:true,format:raw.format});
    return true;
  }
  return {execute,validate,inspectLook,lookSnapshot,environmentSnapshot};
};

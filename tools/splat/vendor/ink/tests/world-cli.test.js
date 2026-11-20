const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawnSync } = require('node:child_process');

const root=path.join(__dirname,'..'), cli=path.join(root,'cli','ink-studio.js');
test('headless commands apply edits, resume, fork, replay, sample, diff and assert', () => {
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'ink-studio-world-'));
  function write(name,value){
    fs.writeFileSync(path.join(dir,name),JSON.stringify(value));
    return name;
  }
  function call(argv,code=0){
    const child=spawnSync(process.execPath,[cli,...argv,'--json'],{cwd:dir,encoding:'utf8'});
    assert.equal(child.status,code,child.stderr||child.stdout);
    return child.stdout?JSON.parse(child.stdout):null;
  }
  try {
    const scene=write('scene.json',{format:'ink-studio/world',id:'basin',dt:.1,
      entities:{sensor:{position:[1.5,0,.5]}},
      systems:{river:{kind:'water',config:{width:4,height:1,initial:[
        {bounds:{min:[0,0],max:[1,1]},value:.8}
      ]}}}
    });
    const author=require('..').load().KIT.authoring.document();
    author.create('prop',{id:'lamp',parameters:{strength:1}});
    const retained=write('retained.json',author.snapshot());
    const retainedEdit=write('retained-edit.json',[{op:'set',path:'/entities/lamp/parameters/strength',value:4}]);
    assert.equal(call(['scene','apply',retained,retainedEdit]).entities.lamp.parameters.strength,4);
    assert(call(['validate',retainedEdit,'--world',retained,'--kind','edits']).valid);
    const diorama=path.join(root,'lab','data-shrine.json');
    const dioramaEdit=write('diorama-edit.json',[{op:'set',path:'/seed',value:17}]);
    assert.equal(call(['scene','apply',diorama,dioramaEdit]).seed,17);
    const edits=write('edit.json',[{op:'set',path:'/metadata/author',value:'test'}]);
    const scheduled=[{tick:5,action:'river/bed',args:{bounds:{min:[2,0],max:[3,1]},height:.3}}];
    const actions=write('actions.json',scheduled);
    assert.equal(call(['validate',scene]).valid,true);
    assert.equal(call(['validate',edits,'--world',scene,'--kind','edits']).valid,true);
    assert.equal(call(['validate',actions,'--world',scene,'--kind','actions']).valid,true);
    assert.deepEqual(call(['scene','apply',scene,edits,'--dry-run']).changed,[['metadata','author']]);
    call(['scene','apply',scene,edits,'--out','edited.json']);
    assert.equal(JSON.parse(fs.readFileSync(path.join(dir,'edited.json'))).metadata.author,'test');

    const base=call(['sim','run',scene,'--ticks','4','--checkpoint','base.json']);
    assert.equal(base.tick,4);
    const checks=write('assertions.json',[
      {id:'mass',field:'mass',when:{path:['error'],op:'lte',value:1e-9}},
      {id:'by-tick',field:'depth',at:{entity:'sensor'},byTick:10,when:{op:'gt',value:.01}},
      {profile:'river',metric:'calls',max:6}
    ]);
    const fork=call(['sim','fork','base.json','--ticks','10','--actions',actions,
      '--profile','--assert',checks,'--record','edit.run.json']);
    assert.equal(fork.tick,10);
    assert.equal(fork.commands.applied,1);
    assert(fork.checks.every(row=>row.pass));
    call(['sim','resume','base.json','--ticks','10','--record','base.run.json']);
    const replay=call(['sim','replay','edit.run.json']);
    assert.equal(replay.tick,10);
    assert.equal(call(['sim','reset','edit.run.json']).tick,4);
    assert.equal(call(['probe','edit.run.json','--field','world/history']).value.events[0].kind,'bed-edit');
    const maps=write('grid.json',{grid:{min:[.5,0,.5],max:[3.5,0,.5],counts:[4,1,1]}});
    const compare=call(['sim','diff','base.run.json','edit.run.json','--field','depth','--spec',maps]);
    assert(compare.edits.length>0);
    const exportSpec=write('series.json',{ticks:[1,2,3],at:{entity:'sensor'}});
    const series=call(['field',scene,'depth','--spec',exportSpec]).series;
    assert.deepEqual(series.map(row=>row.tick),[1,2,3]);
    assert(series[2].value>series[0].value);
    const sweep=write('sweep.json',[
      {id:'a',ticks:3,seed:1,probes:[{field:'mass'}]},
      {id:'b',ticks:5,actions:scheduled,probes:[{field:'depth',at:{entity:'sensor'}}]}
    ]);
    assert.equal(call(['sim','sweep',scene,sweep]).runs.length,2);
    const failing=write('fail.json',[{field:'mass',when:{path:['volume'],op:'lt',value:0}}]);
    assert.equal(call(['sim','run',scene,'--assert',failing],2).checks[0].pass,false);
  } finally {
    fs.rmSync(dir,{recursive:true,force:true});
  }
});

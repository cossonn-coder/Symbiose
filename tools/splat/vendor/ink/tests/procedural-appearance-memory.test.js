const test=require('node:test'),assert=require('node:assert/strict'),
  {appearanceMemory}=require('..').load().KIT.procedural;

test('appearance memory keeps separate named settings and normalizes both writes and reloads',()=>{
  const stored=new Map(),storage={getItem:key=>stored.get(key),setItem:(key,value)=>stored.set(key,value)};
  const build=appearanceMemory({storage,key:'build',normalize:value=>({...value,normalized:true})});
  const source={color:[.25,.3,.8]};
  build.set('stone',source);
  build.set('wood',{color:[.7,.4,.1]});
  source.color[0]=1;
  assert.deepEqual(build.get('stone'),{color:[.25,.3,.8],normalized:true});
  assert(Object.isFrozen(build.get('stone').color));
  assert.equal(build.get('constructor'),null);
  assert.deepEqual(appearanceMemory({storage,key:'build'}).snapshot(),build.snapshot());
  assert.equal(appearanceMemory({storage,key:'detail'}).get('stone'),null);
  build.clear('stone');
  assert.equal(appearanceMemory({storage,key:'build'}).get('stone'),null);
  assert.deepEqual(build.get('wood').color,[.7,.4,.1]);
  build.clear();
  assert.deepEqual(appearanceMemory({storage,key:'build'}).snapshot(),{});
});

test('invalid settings and failed adapter writes preserve the previous snapshot',()=>{
  let fail=false,value;
  const storage={getItem:()=>value,setItem:(key,next)=>{
    if(fail)throw Error('Storage full');
    value=next;
  }};
  const memory=appearanceMemory({storage});
  memory.set('guard',{pattern:'bars'});
  const before=memory.snapshot();
  assert.throws(()=>memory.set('__proto__',{pattern:'solid'}),/scope/);
  assert.throws(()=>memory.set('guard',[]),/object/);
  fail=true;
  assert.throws(()=>memory.set('guard',{pattern:'solid'}),/Storage full/);
  assert.strictEqual(memory.snapshot(),before);
  assert.deepEqual(appearanceMemory({storage}).snapshot(),before);
});

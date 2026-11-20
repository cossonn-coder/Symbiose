/* Declarative accounts and fixed-rate or fixed-quantity transfer links. */
(function (K) {
  const W = K.world, T = W.transfers;
  const {check,id,record,own} = W.data;

  function store(config) {
    const specs = config.accounts;
    check(record(specs) && Object.keys(specs).length <= 512,'A store needs a bounded account table');
    const accounts = {}, initial = {};
    for (const [key,spec] of Object.entries(specs)) {
      check(id(key) && record(spec),'Invalid store account '+key);
      const {resource,units,type='number',min,max} = spec;
      check(['number','integer','vec2','vec3'].includes(type),'Invalid store account type '+type);
      const normalized = T.balanceOf({type,name:key},{balance:spec.initial,min,max}).report;
      initial[key] = normalized.balance;
      accounts[key] = {resource,units,type,read:state=>({balance:state[key],min:normalized.min,max:normalized.max}),
        write:(state,balance)=>({...state,[key]:balance})};
    }
    return {accounts,initial:()=>initial};
  }

  function exchange(config, {world}) {
    const specs = config.links;
    check(record(specs) && Object.keys(specs).length <= 512,'An exchange needs a bounded link table');
    const inputs = {}, links = [];
    for (const [key,spec] of Object.entries(specs)) {
      check(id(key) && record(spec) && own(spec,'amount') !== own(spec,'rate') &&
        (spec.enabled === undefined || typeof spec.enabled === 'boolean'),'Invalid transfer link '+key);
      inputs[key] = {type:'bool',default:spec.enabled ?? true};
      const amount = own(spec,'amount') ? spec.amount : Array.isArray(spec.rate) ?
        spec.rate.map(n=>Number.isFinite(n)?n*world.dt:null) : Number.isFinite(spec.rate)?spec.rate*world.dt:null;
      links.push({id:key,from:spec.from,to:spec.to,amount,mode:spec.mode ?? 'partial'});
    }
    return {inputs,initial:()=>({}),checkTransfers(validate) {
      for (const link of links) validate(link,true);
    },requestTransfers(state,{input}) {
      return links.filter(link=>input[link.id] && (Array.isArray(link.amount) ? link.amount.some(Boolean) : link.amount !== 0));
    }};
  }

  W.runtime.register('store',store);
  W.runtime.register('exchange',exchange);
})(KIT);

/* Reuse retained depth buckets with smaller transient streams. */
const SplatOrder = (() => {
  const bins = 65536, never = () => false;
  function key(depth,minimum,scale){
    const bucket=(depth-minimum)*scale|0;
    return bucket<0?0:bucket>=bins?bins-1:bucket;
  }
  const sortWorkspace = new WeakMap(), bucketTables = new WeakMap();

  function compile(indices, depthAt, behind = never) {
    if (!indices.length) return null;
    const depths = new Float32Array(indices.length);
    let minimum = Infinity, maximum = -Infinity;
    for (let i = 0; i < indices.length; i++) {
      const index = indices[i], depth = depthAt(index);
      if (!Number.isInteger(index) || index < 0 || index > 0x7fffffff ||
          (i > 0 && index <= indices[i - 1]) || !Number.isFinite(depth))
        throw new Error('Depth sorting needs increasing nonnegative integer indices and finite depths');
      depths[i] = depth;
      minimum = Math.min(minimum, depth);
      maximum = Math.max(maximum, depth);
    }
    const scale = (bins - 1) / (maximum - minimum || 1);
    const backKey = key(Math.fround(minimum), minimum, scale);
    const counts = new Uint32Array(bins), keys = new Uint16Array(indices.length);
    for (let i = 0; i < indices.length; i++) {
      const bucket = behind(indices[i]) ? backKey : key(depths[i], minimum, scale);
      keys[i] = bucket;
      counts[bucket]++;
    }
    let prefix = 0;
    for (let i = 0; i < bins; i++) {
      const count = counts[i];
      counts[i] = prefix;
      prefix += count;
    }
    const order = new Int32Array(indices.length), sortedKeys = new Uint16Array(indices.length);
    for (let i = 0; i < indices.length; i++) {
      const bucket = keys[i], position = counts[bucket]++;
      order[position] = indices[i];
      sortedKeys[position] = bucket;
    }
    const retained=Object.freeze({ minimum, maximum, scale, backKey, order, keys: sortedKeys });
    bucketTables.set(retained,counts);
    return retained;
  }

  function sortTail(retained, indices, keys, ordered) {
    if(!ordered||indices.length<512){
      indices.sort((a,b)=>keys[a]-keys[b]||a-b);
      return;
    }
    let workspace=sortWorkspace.get(retained);
    if(!workspace||workspace.scratch.length<indices.length){
      workspace={scratch:new Int32Array(Math.max(indices.length,Math.ceil((workspace?.scratch.length||0)*1.5))),
        low:new Uint32Array(256),high:new Uint32Array(256)};
      sortWorkspace.set(retained,workspace);
    }
    const {scratch,low,high}=workspace;
    low.fill(0);high.fill(0);
    for(let i=0;i<indices.length;i++){
      const value=keys[indices[i]];
      low[value&255]++;
      high[value>>8]++;
    }
    let a=0,b=0;
    for(let i=0;i<256;i++){
      const countLow=low[i],countHigh=high[i];
      low[i]=a;high[i]=b;
      a+=countLow;b+=countHigh;
    }
    // Stable bucket passes preserve the input's sample-index tie order.
    for(let i=0;i<indices.length;i++){
      const index=indices[i];
      scratch[low[keys[index]&255]++]=index;
    }
    for(let i=0;i<indices.length;i++){
      const index=scratch[i];
      indices[high[keys[index]>>8]++]=index;
    }
  }

  function merge(retained, indices, depthAt, behind, result, keysByIndex) {
    if (result.length < retained.order.length + indices.length) throw new Error('Depth order target is too small');
    let previous=-1,ordered=true;
    for (const index of indices) {
      const depth = depthAt(index);
      if (!Number.isSafeInteger(index) || index < 0 || index >= keysByIndex.length || !Number.isFinite(depth))
        throw new Error('Depth sorting needs in-range indices and finite depths');
      // A changing range requires rebuilding the original buckets, including
      // ties. Let the caller perform its full sort with all current depths.
      if (depth < retained.minimum || depth > retained.maximum) return false;
      keysByIndex[index] = behind(index) ? retained.backKey : key(Math.fround(depth), retained.minimum, retained.scale);
      if(index<previous)ordered=false;
      previous=index;
    }
    sortTail(retained,indices,keysByIndex,ordered);
    const { order, keys } = retained, bucketEnds=bucketTables.get(retained);
    let i = 0, at = 0;
    for (const index of indices) {
      const depth = keysByIndex[index];
      if(bucketEnds){
        let stop=Math.max(i,depth?bucketEnds[depth-1]:0);
        const end=bucketEnds[depth];
        while(stop<end&&order[stop]<index)stop++;
        if(stop-i>=64){
          result.set(order.subarray(i,stop),at);
          at+=stop-i;
          i=stop;
        }else while(i<stop)result[at++]=order[i++];
      }else{
        while(i<order.length&&(keys[i]<depth||keys[i]===depth&&order[i]<index))
          result[at++]=order[i++];
      }
      result[at++] = index;
    }
    result.set(order.subarray(i), at);
    return true;
  }

  return Object.freeze({ compile, merge });
})();
if (typeof module !== 'undefined') module.exports = SplatOrder;

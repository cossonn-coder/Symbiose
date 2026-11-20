/* Artist-authored directional sprite atlases. Coordinates in the atlas are top-down. */
const AtlasSprites = (() => {
  const assetBrand=Symbol.for('ink-studio.sprite-atlas'), placedBrand=Symbol.for('ink-studio.atlas-placement');
  const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
  const integer=(n,min,max)=>Number.isSafeInteger(n)&&n>=min&&n<=max;
  const finite=(n,label)=>{
    if (!Number.isFinite(n)) throw new RangeError(label+' must be finite');
    return n;
  };
  const positive=(n,label)=>{
    if (!Number.isFinite(n)||n<=0) throw new RangeError(label+' must be positive');
    return n;
  };
  const vector=(v,label)=>{
    if (!Array.isArray(v)||v.length!==3||!Array.from(v).every(Number.isFinite))
      throw new TypeError(label+' needs a finite XYZ position');
    return v.slice();
  };

  function basis(yaw,pitch) {
    const x=Math.sin(yaw),z=Math.cos(yaw),s=Math.sin(pitch),c=Math.cos(pitch);
    return {right:[z,0,-x],up:[-x*s,c,-z*s],normal:[x*c,s,z*c]};
  }

  function compile(source) {
    if (source?.[assetBrand]) return source;
    const { metadata:m,images }=source??{};
    const { width,height,frames,encodings={},normalSpace=typeof encodings.normal==='string'?'asset':'view',
      emissionMode=typeof encodings.emission==='string'?'baked':'add', depthFormat='rgb24' }=m??{};
    if (!integer(width,1,8192)||!integer(height,1,8192)||!Array.isArray(frames)||!frames.length||frames.length>32768)
      throw new RangeError('Sprite atlas needs valid dimensions and view frames');
    if (!['view','asset'].includes(normalSpace)||!['baked','add'].includes(emissionMode)||!['rgb24','gray'].includes(depthFormat))
      throw new RangeError('Invalid sprite atlas map encoding');
    const names=['color','depth','normal','emission'];
    if (width*height*names.filter(name=>images?.[name]).length>32e6)
      throw new RangeError('Sprite atlas exceeds its pixel budget');
    const maps={};
    for (const name of names) {
      const data=images?.[name];
      if (!data&&name!=='color') continue;
      if (!(Array.isArray(data)||(ArrayBuffer.isView(data)&&data.BYTES_PER_ELEMENT===1))||data.length!==width*height*4||
          (Array.isArray(data)&&!Array.from(data).every(n=>integer(n,0,255))))
        throw new TypeError('Sprite atlas '+name+' needs a matching RGBA image');
      maps[name]=Uint8Array.from(data);
    }
    const range=encodings.depth?.range??m.depthRange;
    if (maps.depth && range===undefined && !maps.depth.some((n,i)=>i%4===3&&n)) delete maps.depth;
    if (maps.depth&&(!Array.isArray(range)||range.length!==2||!Array.from(range).every(Number.isFinite)||range[1]<range[0]))
      throw new RangeError('Sprite atlas depth needs a finite increasing range');
    const depthLo=range?.[0]??0, depthSpan=(range?.[1]??0)-depthLo;
    const legacyOrigin = typeof encodings.depth?.encoding==='string' && range ?
      .5*range[0]+.5*range[1] : 0;
    const groups=new Map();
    for (const entry of frames) {
      const {frame=0,yaw=0,pitch=m.pitch??0,rect,unitsPerPixel=m.unitsPerPixel??1,
        depthOrigin=m.depthOrigin??legacyOrigin}=entry??{};
      const {x,y,width:w,height:h}=rect??{};
      if (!integer(frame,0,32767)||!integer(x,0,width-1)||!integer(y,0,height-1)||
          !integer(w,1,width-x)||!integer(h,1,height-y))
        throw new RangeError('Sprite atlas view rectangle or frame is out of range');
      const pivot=entry.pivot??{x:w*.5,y:h*.5};
      const view={
        rect:{x,y,width:w,height:h}, pivot:{x:finite(pivot.x,'Sprite pivot X'),y:finite(pivot.y,'Sprite pivot Y')},
        unitsPerPixel:positive(unitsPerPixel,'Sprite units per pixel'), depthOrigin:finite(depthOrigin,'Sprite depth origin'),
        yaw:finite(yaw,'Sprite yaw'), pitch:finite(pitch,'Sprite pitch')
      };
      view.basis=basis(view.yaw,view.pitch);
      if (!groups.has(frame)) groups.set(frame,[]);
      groups.get(frame).push(view);
    }
    function select(frame,mode,direction) {
      const views=groups.get(frame??groups.keys().next().value);
      if (!views) throw new RangeError('Unknown sprite atlas frame: '+frame);
      if (mode==='card') return views[0];
      return views.reduce((best,view)=>dot(view.basis.normal,direction)>dot(best.basis.normal,direction)?view:best);
    }
    function sample(view,x,y,channels,out) {
      const index=((view.rect.y+y)*width+view.rect.x+x)*4;
      const a=maps.color[index+3]/255;
      if (!a) return false;
      out.alpha=a;
      for (let c=0;c<3;c++) out.color[c]=maps.color[index+c]/255;
      out.depth=maps.depth?.[index+3]&&channels.depth
        ? depthLo+depthSpan*(depthFormat==='gray'?maps.depth[index]/255:
          (maps.depth[index]*65536+maps.depth[index+1]*256+maps.depth[index+2])/0xffffff)-view.depthOrigin : 0;
      out.hasNormal=!!maps.normal?.[index+3];
      out.hasEmission=!!(channels.emission&&maps.emission?.[index+3]);
      if (out.hasNormal) for (let c=0;c<3;c++) out.normal[c]=maps.normal[index+c]/127.5-1;
      if (out.hasEmission) {
        const gain=emissionMode==='baked'?1/a:maps.emission[index+3]/255;
        for(let c=0;c<3;c++) out.emission[c]=Math.min(1,maps.emission[index+c]/255*gain);
      } else out.emission.fill(0);
      return true;
    }
    return Object.freeze({[assetBrand]:true, select, sample, normalSpace, emissionMode, hasDepth:Boolean(maps.depth)});
  }

  function place(value) {
    if (value?.[placedBrand]) return value;
    const { atlas,at,mode='impostor',yaw=0,scale=1,opacity=1,frame,depth=true,lighting=true,emission=true,objectId,materialId }=value??{};
    if (!['card','impostor'].includes(mode)||!Number.isFinite(opacity)||opacity<0||opacity>1||
        [depth,lighting,emission].some(value=>typeof value!=='boolean')||
        (frame!==undefined&&typeof frame!=='function'&&!integer(frame,0,32767)))
      throw new RangeError('Invalid sprite atlas placement');
    if (objectId!==undefined || materialId!==undefined) {
      const selectors = typeof TargetSelectors === 'undefined' ? require('./target-selectors.js') : TargetSelectors;
      if (objectId!==undefined) selectors.prepare({object:objectId});
      if (materialId!==undefined) selectors.prepare({material:materialId});
    }
    const anchor=typeof at==='function'?at:Object.freeze(vector(at,'Sprite atlas anchor'));
    return Object.freeze({[placedBrand]:true, atlas:compile(atlas), at:anchor, mode,
      yaw:finite(yaw,'Sprite placement yaw'), scale:positive(scale,'Sprite placement scale'),
      opacity,frame,depth,lighting,emission,...(objectId!==undefined&&{objectId}),...(materialId!==undefined&&{materialId}) });
  }
  function placements(authored,override) {
    const source=override===true?authored:override??authored;
    if (source===false||source===undefined) return [];
    if (!Array.isArray(source)||source.length>128) throw new TypeError('Sprite atlases need a list of up to 128 placements');
    return source.map(place);
  }

  return Object.freeze({compile,place,placements,basis,dot,vector});
})();
if (typeof module !== 'undefined') module.exports = AtlasSprites;

// Pack nearest-sampled pixel art for depth-tested, world-space surfaces.
const SpriteSurface = (() => {
  function make(width = 1024, limit = 4096) {
    if (!Number.isInteger(width) || width < 1 || !Number.isInteger(limit) || limit < 1)
      throw new RangeError('Expected positive atlas dimensions');
    let x = 0, y = 0, shelf = 0;
    const entries = [], vertices = [];
    function mesh(surface,w,h,paint) {
      const geometry=typeof TexturedSurface!=='undefined'?TexturedSurface:require('./textured-surface.js');
      geometry.validate(surface);
      if(!Number.isInteger(w)||!Number.isInteger(h)||w<1||w>width||h<1||typeof paint!=='function')
        throw new RangeError('Expected bounded sprite dimensions and a paint function');
      let nextX=x,nextY=y,nextShelf=shelf;
      if(nextX+w>width){nextX=0;nextY+=nextShelf;nextShelf=0;}
      if(nextY+h>limit)throw new RangeError('Sprite surface atlas is full');
      const pixels=new Uint8Array(w*h*4),packed=[];
      for(let j=0;j<h;j++)for(let i=0;i<w;i++){
        const ink=paint(i,j),offset=(j*w+i)*4;
        if(ink==null)continue;
        if(!Number.isSafeInteger(ink)||ink<0||ink>0xffffff)throw new RangeError('Surface paint must return RGB hex or a transparent pixel');
        pixels.set([(ink>>>16)&255,(ink>>>8)&255,ink&255,255],offset);
      }
      for(const index of surface.triangles){
        packed.push(surface.points[index*3],surface.points[index*3+1],surface.points[index*3+2],
          nextX+.5+(w-1)*surface.uvs[index*2],nextY+.5+(h-1)*surface.uvs[index*2+1]);
      }
      entries.push({x:nextX,y:nextY,w,h,pixels});
      for(const value of packed)vertices.push(value);
      x=nextX+w;y=nextY;shelf=Math.max(nextShelf,h);
      return surface;
    }
    function face(origin,right,up,w,h,paint) {
      if(![origin,right,up].every(v=>v&&v.length===3&&Array.from(v).every(Number.isFinite)))
        throw new RangeError('Expected a finite surface frame and bounded sprite dimensions');
      const points=[];
      for(const [u,v] of [[0,0],[1,0],[0,1],[1,1]])
        points.push(...origin.map((n,k)=>n+right[k]*u+up[k]*(1-v)));
      mesh({points,uvs:[0,0,1,0,0,1,1,1],triangles:[0,1,2,2,1,3]},w,h,paint);
    }
    function finish() {
      const height = Math.max(1, y + shelf), pixels = new Uint8Array(width * height * 4);
      for (const e of entries) for (let row = 0; row < e.h; row++) {
        pixels.set(e.pixels.subarray(row * e.w * 4, (row + 1) * e.w * 4), ((row + e.y) * width + e.x) * 4);
      }
      return { width, height, pixels, vertices: Float32Array.from(vertices) };
    }
    return { face, mesh, finish };
  }
  return Object.freeze({ make });
})();
if (typeof module !== 'undefined') module.exports = SpriteSurface;

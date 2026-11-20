/* Closed staggered-grid flow with implicit diffusion and semi-Lagrangian advection. */
(function (K) {
  const P=K.procedural,M=P.motion,
    integer=(n,a,b)=>Number.isSafeInteger(n)&&n>=a&&n<=b,
    number=(n,a,b)=>Number.isFinite(n)&&n>=a&&n<=b,
    vector=p=>Array.isArray(p)&&p.length===2&&p.every(v=>number(v,-1e7,1e7)),
    clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
  function bilinear(data,width,height,x,z,mask){
    const u=clamp(x,0,width-1),v=clamp(z,0,height-1),
      ix=Math.floor(u),iz=Math.floor(v),jx=Math.min(ix+1,width-1),jz=Math.min(iz+1,height-1),
      fx=u-ix,fz=v-iz,i=iz*width+ix,j=iz*width+jx,k=jz*width+ix,l=jz*width+jx;
    let a=(1-fx)*(1-fz),b=fx*(1-fz),c=(1-fx)*fz,d=fx*fz;
    if(mask){a*=mask[i];b*=mask[j];c*=mask[k];d*=mask[l];}
    const total=a+b+c+d;
    return total?(a*data[i]+b*data[j]+c*data[k]+d*data[l])/total:0;
  }
  function gridDomain({width,height,cell=0.1,origin=[0,0],mask}={}){
    const spacing=typeof cell==='number'?[cell,cell]:cell;
    if(!integer(width,1,768)||!integer(height,1,768)||width*height>220000||
      !vector(spacing)||!spacing.every(v=>number(v,1e-5,10000))||!vector(origin)||
      (mask!==undefined&&typeof mask!=='function')) throw new Error('Motion grids need finite XZ dimensions and spacing');
    const [dx,dz]=spacing,[ox,oz]=origin,size=width*height,bounds={min:[ox,oz],max:[ox+dx*width,oz+dz*height]},
      open=new Uint8Array(size),xAt=i=>ox+(i%width+0.5)*dx,zAt=i=>oz+(Math.floor(i/width)+0.5)*dz,
      center=i=>[xAt(i),zAt(i)];
    for(let i=0;i<size;i++)open[i]=Number(!mask||Boolean(mask(xAt(i),zAt(i),i)));
    function inside(x,z){
      if(x<ox||x>bounds.max[0]||z<oz||z>bounds.max[1]||!Number.isFinite(x)||!Number.isFinite(z))return false;
      const i=Math.min(width-1,Math.floor((x-ox)/dx)),j=Math.min(height-1,Math.floor((z-oz)/dz));
      return Boolean(open[j*width+i]);
    }
    return {width,height,size,dx,dz,ox,oz,bounds:P.data.freeze(bounds),open,center,inside,
      sample:(data,x,z)=>Number.isFinite(x)&&Number.isFinite(z)&&inside(x,z)?
        bilinear(data,width,height,(x-ox)/dx-0.5,(z-oz)/dz-0.5,open):0};
  }
  function stableFluid(options={}){
    const domain=gridDomain(options),{width:w,height:h,size,dx,dz,ox,oz,open,center,inside}=domain,
      {initial,maxDt=0.045,maxSpeed=12,maxDensity=50,pressureIterations=28,diffusionIterations=10,
        maxTracing=40,maxWork=92000000}=options;
    if((initial!==undefined&&typeof initial!=='function')||!number(maxDt,1e-5,1)||
      !number(maxSpeed,1e-4,1e5)||!number(maxDensity,1e-4,1e6)||!integer(pressureIterations,2,240)||
      !integer(diffusionIterations,1,80)||!integer(maxTracing,4,128)||!integer(maxWork,1,260000000))
      throw new Error('Stable fluids need bounded pressure, diffusion and travel controls');
    const uw=w+1,vh=h+1,uf=new Uint8Array(uw*h),vf=new Uint8Array(w*vh),
      X=1/(dx*dx),Z=1/(dz*dz),zeroU=new Float64Array(uw*h),zeroV=new Float64Array(w*vh);
    for(let z=0;z<h;z++)for(let x=1;x<w;x++)uf[z*uw+x]=open[z*w+x-1]&open[z*w+x];
    for(let z=1;z<h;z++)for(let x=0;x<w;x++)vf[z*w+x]=open[(z-1)*w+x]&open[z*w+x];
    const fields={u:zeroU,v:zeroV,density:new Float64Array(size)};
    let time=0;
    function velocityAt(u,v,x,z){
      return [bilinear(u,uw,h,(x-ox)/dx,(z-oz)/dz-0.5),bilinear(v,w,vh,(x-ox)/dx-0.5,(z-oz)/dz)];
    }
    function cellVelocity(u,v,i){
      const x=i%w,z=Math.floor(i/w),a=z*uw+x,b=z*w+x;
      return [(u[a]+u[a+1])*0.5,(v[b]+v[b+w])*0.5];
    }
    function divergence(u,v,i){
      const x=i%w,z=Math.floor(i/w),a=z*uw+x,b=z*w+x;
      return (u[a+1]-u[a])/dx+(v[b+w]-v[b])/dz;
    }
    function project(u,v){
      const pressure=new Float64Array(size), div=new Float64Array(size), local=new Float64Array(size);
      for(let z=0,i=0;z<h;z++)for(let x=0;x<w;x++,i++){
        if(!open[i])continue;
        div[i]=divergence(u,v,i);
        local[i]=X*((x&&open[i-1]?1:0)+(x+1<w&&open[i+1]?1:0))+
          Z*((z&&open[i-w]?1:0)+(z+1<h&&open[i+w]?1:0));
      }
      for(let k=0;k<pressureIterations;k++)for(let z=0,i=0;z<h;z++)for(let x=0;x<w;x++,i++){
        if(!local[i])continue;
        const p=X*((x&&open[i-1]?pressure[i-1]:0)+(x+1<w&&open[i+1]?pressure[i+1]:0))+
          Z*((z&&open[i-w]?pressure[i-w]:0)+(z+1<h&&open[i+w]?pressure[i+w]:0));
        pressure[i]=(p-div[i])/local[i];
      }
      for(let z=0;z<h;z++)for(let x=1;x<w;x++)if(uf[z*uw+x]){
        const i=z*w+x;
        u[z*uw+x]-=(pressure[i]-pressure[i-1])/dx;
      }
      for(let z=1;z<h;z++)for(let x=0;x<w;x++)if(vf[z*w+x]){
        const i=z*w+x;
        v[i]-=(pressure[i]-pressure[i-w])/dz;
      }
    }
    const initX=new Float64Array(size),initZ=new Float64Array(size);
    for(let i=0;i<size;i++){
      if(!open[i]||!initial)continue;
      const {density=0,velocity=[0,0]}=initial(...center(i),i)??{};
      if(!number(density,0,maxDensity)||!vector(velocity))
        throw new Error('Initial fluid values must be finite');
      fields.density[i]=density;
      initX[i]=clamp(velocity[0],-maxSpeed,maxSpeed);
      initZ[i]=clamp(velocity[1],-maxSpeed,maxSpeed);
    }
    for(let z=0;z<h;z++)for(let x=1;x<w;x++)if(uf[z*uw+x])zeroU[z*uw+x]=(initX[z*w+x-1]+initX[z*w+x])*0.5;
    for(let z=1;z<h;z++)for(let x=0;x<w;x++)if(vf[z*w+x])zeroV[z*w+x]=(initZ[(z-1)*w+x]+initZ[z*w+x])*0.5;
    if(initial)project(zeroU,zeroV);

    function diffuse(values,width,height,mask,nu,dt,wall){
      if(!nu)return values;
      const out=values.slice(),a=nu*dt*X,b=nu*dt*Z;
      for(let k=0;k<diffusionIterations;k++)for(let z=0,i=0;z<height;z++)for(let x=0;x<width;x++,i++){
        if(!mask[i])continue;
        let sum=values[i], count=1;
        for(const [j,weight,available] of [
          [i-1,a,x>0],[i+1,a,x+1<width],[i-width,b,z>0],[i+width,b,z+1<height]
        ]){
          if(available&&mask[j]){sum+=weight*out[j];count+=weight;}
          else if(wall)count+=weight;
        }
        out[i]=sum/count;
      }
      return out;
    }
    function advect(values,width,height,mask,u,v,dt,offsetX,offsetZ,scalar){
      const out=new Float64Array(values.length);
      for(let z=0,i=0;z<height;z++)for(let x=0;x<width;x++,i++){
        if(!mask[i])continue;
        const px=ox+(x+offsetX)*dx,pz=oz+(z+offsetZ)*dz,
          [sx,sz]=velocityAt(u,v,px,pz),
          [vx,vz]=velocityAt(u,v,px-sx*dt*0.5,pz-sz*dt*0.5),
          limit=0.47*Math.min(dx,dz),ratio=Math.max(1,Math.hypot(vx,vz)*dt/(maxTracing*limit)),
          ax=-vx*dt/ratio,az=-vz*dt/ratio,
          steps=Math.max(1,Math.ceil(Math.hypot(ax,az)/limit));
        let tx=px,tz=pz;
        for(let j=1;j<=steps;j++){
          const qx=px+ax*j/steps,qz=pz+az*j/steps;
          if(!inside(qx,qz))break;
          tx=qx;tz=qz;
        }
        out[i]=bilinear(values,width,height,(tx-ox)/dx-offsetX,(tz-oz)/dz-offsetZ,scalar?mask:undefined);
      }
      return out;
    }
    function snapshot(substeps=0){
      const density=fields.density.slice(),u=fields.u.slice(),v=fields.v.slice(),
        vx=new Float64Array(size),vz=new Float64Array(size),div=new Float64Array(size);
      for(let i=0;i<size;i++)if(open[i]){
        [vx[i],vz[i]]=cellVelocity(u,v,i);
        div[i]=divergence(u,v,i);
      }
      return Object.freeze({time,width:w,height:h,bounds:domain.bounds,density,vx,vz,divergence:div,substeps,
        sample(x,z){return inside(x,z)?{density:domain.sample(density,x,z),velocity:velocityAt(u,v,x,z)}:null;}});
    }
    function step(duration,{
      force,source,viscosity=0.0002,diffusion=0.001,dissipation=0.025
    }={}){
      if(!number(duration,0,120)||![viscosity,diffusion,dissipation].every(v=>number(v,0,1e8))||
        [force,source].some(fn=>fn!==undefined&&typeof fn!=='function'))
        throw new Error('Fluid steps need finite intervals and source controls');
      if(!duration)return snapshot();
      const n=Math.ceil(duration/maxDt),dt=duration/n,
        work=n*size*(26+2*pressureIterations+3*diffusionIterations+3*maxTracing);
      if(n>5000||work>maxWork)throw new Error('Fluid step exceeds its work budget');
      let u=fields.u.slice(),v=fields.v.slice(),density=fields.density.slice();
      const forceX=new Float64Array(size),forceZ=new Float64Array(size);
      for(let k=0;k<n;k++){
        const t=time+k*dt;
        for(let i=0;i<size;i++){
          if(!open[i])continue;
          const pos=center(i),values={density:density[i],velocity:cellVelocity(u,v,i)};
          if(force){
            const f=force(...pos,t,values);
            if(!vector(f))throw new Error('Fluid forces must be finite XZ vectors');
            forceX[i]=f[0];
            forceZ[i]=f[1];
          }
          if(source){
            const rate=source(...pos,t,values);
            if(!number(rate,-1e7,1e7))throw new Error('Fluid density sources must be finite');
            density[i]=clamp(density[i]+rate*dt,0,maxDensity);
          }
        }
        if(force){
          for(let z=0;z<h;z++)for(let x=1;x<w;x++)if(uf[z*uw+x]){
            const i=z*uw+x,p=z*w+x;
            u[i]=clamp(u[i]+dt*(forceX[p-1]+forceX[p])*0.5,-maxSpeed,maxSpeed);
          }
          for(let z=1;z<h;z++)for(let x=0;x<w;x++)if(vf[z*w+x]){
            const i=z*w+x;
            v[i]=clamp(v[i]+dt*(forceZ[i-w]+forceZ[i])*0.5,-maxSpeed,maxSpeed);
          }
        }
        u=diffuse(u,uw,h,uf,viscosity,dt,true);
        v=diffuse(v,w,vh,vf,viscosity,dt,true);
        project(u,v);
        const nextU=advect(u,uw,h,uf,u,v,dt,0,0.5,false), nextV=advect(v,w,vh,vf,u,v,dt,0.5,0,false);
        [u,v]=[nextU,nextV];
        project(u,v);
        density=diffuse(density,w,h,open,diffusion,dt,false);
        density=advect(density,w,h,open,u,v,dt,0.5,0.5,true);
        const decay=Math.exp(-dissipation*dt);
        for(let i=0;i<size;i++)density[i]*=decay;
      }
      fields.u=u;fields.v=v;fields.density=density;time+=duration;
      return snapshot(n);
    }
    return Object.freeze({step,snapshot});
  }
  Object.assign(M,{stableFluid,gridDomain});
})(KIT);

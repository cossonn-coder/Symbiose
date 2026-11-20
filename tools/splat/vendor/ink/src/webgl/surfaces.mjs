import { createResources } from './resources.mjs';

// Opaque pixel cutouts share an atlas and depth buffer with the splat pass.
export function createSurfacePipeline(gl) {
  const resources=createResources(gl);
  try {
    const shader=resources.program(`#version 300 es
precision highp float;
layout(location=0) in vec3 a_point;
layout(location=1) in vec2 a_texel;
uniform mat4 u_view,u_proj;
out vec2 v_texel;
out vec3 v_world;
out float v_depth;
out vec3 v_camera;
void main(){
  vec4 p=u_view*vec4(a_point,1.0);
  v_texel=a_texel;v_world=a_point;v_depth=-p.z;v_camera=p.xyz;
  gl_Position=u_proj*p;
}`,`#version 300 es
precision highp float;
uniform sampler2D u_atlas;
uniform vec4 u_range,u_arrivalPlane,u_splatPlane;
uniform vec3 u_fog;
uniform bool u_index;
in vec2 v_texel;
in vec3 v_world;
in float v_depth;
in vec3 v_camera;
layout(location=0) out vec4 color;
layout(location=1) out vec4 depth;
layout(location=2) out vec4 water;
void main(){
  vec4 ink=texelFetch(u_atlas,ivec2(v_texel),0);
  if(ink.a<.5||dot(u_arrivalPlane,vec4(v_world,1.0))<0.0||dot(u_splatPlane,vec4(v_camera,1.0))<0.0)discard;
  float d=clamp((v_depth-u_range.x)/(u_range.y-u_range.x),0.0,1.0);
  float fog=u_range.z<1.0?smoothstep(u_range.z,1.0,d)*u_range.w:0.0;
  color=u_index?vec4(0.0):vec4(mix(ink.rgb,u_fog,fog),1.0);
  depth=vec4(d,0.0,0.0,1.0);water=vec4(0.0);
}`);
    const vao=resources.allocate('VertexArray'),buffer=resources.allocate('Buffer'),texture=resources.texture();
    gl.bindVertexArray(vao);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
    gl.enableVertexAttribArray(0);gl.vertexAttribPointer(0,3,gl.FLOAT,false,20,0);
    gl.enableVertexAttribArray(1);gl.vertexAttribPointer(1,2,gl.FLOAT,false,20,12);
    gl.bindVertexArray(null);
    let active,disposed=false;
    function upload(atlas){
      if(disposed)throw new Error('Surface pipeline has been disposed');
      if(active===atlas)return;
      if(!atlas||!(atlas.vertices instanceof Float32Array)||atlas.vertices.length%15||
        !Number.isSafeInteger(atlas.width)||atlas.width<1||!Number.isSafeInteger(atlas.height)||atlas.height<1||
        !(atlas.pixels instanceof Uint8Array)||atlas.pixels.length!==atlas.width*atlas.height*4||
        !atlas.vertices.every(Number.isFinite))throw new RangeError('Invalid sprite surface atlas');
      if(Math.max(atlas.width,atlas.height)>gl.getParameter(gl.MAX_TEXTURE_SIZE))throw new RangeError('Surface atlas exceeds GPU size limit');
      gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,atlas.vertices,gl.STATIC_DRAW);
      gl.activeTexture(gl.TEXTURE0+6);gl.bindTexture(gl.TEXTURE_2D,texture);
      gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA8,atlas.width,atlas.height,0,gl.RGBA,gl.UNSIGNED_BYTE,atlas.pixels);
      active=atlas;
    }
    function draw(atlas,{view,projection,range,fog,index=false,arrivalPlane=[0,0,0,0],clip=[0,0,0,0]}){
      upload(atlas);
      gl.activeTexture(gl.TEXTURE0+6);gl.bindTexture(gl.TEXTURE_2D,texture);
      gl.useProgram(shader.p);shader.set({u_view:view,u_proj:projection,u_range:range,u_fog:fog,u_atlas:6,
        u_index:+index,u_arrivalPlane:arrivalPlane,u_splatPlane:clip});
      gl.bindVertexArray(vao);gl.drawArrays(gl.TRIANGLES,0,active.vertices.length/5);
      gl.activeTexture(gl.TEXTURE0);
    }
    return {draw,dispose(){if(disposed)return;disposed=true;resources.dispose();}};
  }catch(error){resources.dispose();throw error;}
}

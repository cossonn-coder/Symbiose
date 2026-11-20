const { test } = require('node:test');
const assert = require('node:assert/strict');
const core = require('..');

function testContext() {
  const calls = [];
  const gl = {
    ACTIVE_UNIFORMS: 1, LINK_STATUS: 2, COMPILE_STATUS: 3,
    VERTEX_SHADER: 4, FRAGMENT_SHADER: 5, ARRAY_BUFFER: 6,
    STATIC_DRAW: 7, DYNAMIC_DRAW: 8, FLOAT: 9, INT: 10, TRIANGLE_STRIP: 11,
    createProgram: () => ({ shaders: [] }),
    createShader: type => ({ type }),
    shaderSource: (shader, source) => { shader.source = source; },
    compileShader() {},
    getShaderParameter: () => true,
    attachShader: (program, shader) => { program.shaders.push(shader); },
    linkProgram() {},
    getProgramParameter: (_, name) => name === gl.LINK_STATUS ? true : 0,
    deleteProgram: () => calls.push('delete program'),
    deleteShader: () => calls.push('delete shader'),
    createVertexArray: () => ({}), bindVertexArray() {},
    deleteVertexArray: () => calls.push('delete vao'),
    createBuffer: () => ({}), bindBuffer() {},
    deleteBuffer: () => calls.push('delete buffer'),
    bufferData() {}, bufferSubData() {},
    enableVertexAttribArray() {}, vertexAttribPointer() {},
    vertexAttribIPointer() {}, vertexAttribDivisor() {},
    drawArraysInstanced: (...args) => calls.push(args)
  };
  return { gl, calls };
}

test('the optional entry imports in Node without touching the software renderer', async () => {
  const entry = await import('../webgl.mjs');
  const { createRenderer, splatShaderSources } = entry;
  assert.equal(typeof core.render, 'function');
  assert.equal(entry.default, createRenderer);
  assert.equal(require('../package.json').browser, './webgl.mjs');
  assert(splatShaderSources().vertex.startsWith('#version 300 es'));
  const phased = splatShaderSources(undefined,core.load().KIT.procedural.sampleCoverage).vertex;
  assert.match(phased,/int kraw = int\(t2.w\)/);
  assert.match(phased,/if \(!sampleCoverageVisible\(kraw, u_sampleWithdrawal\)\)/);
  assert.throws(() => createRenderer({}, { toolkit: core.load() }), /canvas/);
  assert.throws(() => createRenderer({ getContext: () => null }, { toolkit: core.load() }), /requires WebGL 2/);
});

test('the GPU pipeline chooses the full shader as soon as a visual feature turns on', async () => {
  const { createSplatPipeline } = await import('../webgl.mjs');
  const { gl, calls } = testContext();
  const pipeline = createSplatPipeline(gl);
  const full = pipeline.programFor();
  const empty = { lamps: false, fine: false, textZones: false };
  const plain = pipeline.programFor(empty);
  assert.notEqual(full.p, plain.p);
  assert.equal(pipeline.programFor(empty), plain);
  assert.equal(pipeline.programFor({}), full);
  for (const feature of Object.keys(empty))
    assert.equal(pipeline.programFor({ ...empty, [feature]: true }), full);
  const vertex = plain.p.shaders.find(shader => shader.type === gl.VERTEX_SHADER).source;
  assert.match(vertex, /if \(false && \(flags & 22\)/);
  assert.match(vertex, /if \(false && plain/);

  pipeline.setOrder(Int32Array.of(2, 1));
  pipeline.draw();
  assert.deepEqual(calls.at(-1), [gl.TRIANGLE_STRIP, 0, 4, 2]);
  assert.throws(() => pipeline.draw(3), /draw count/);
  pipeline.dispose();
  pipeline.dispose();
  assert.equal(calls.filter(call => call === 'delete program').length, 2);
  assert.equal(calls.filter(call => call === 'delete buffer').length, 2);
  assert.throws(() => pipeline.draw(), /disposed/);
});

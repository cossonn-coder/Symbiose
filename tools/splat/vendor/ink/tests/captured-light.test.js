const test = require('node:test');
const assert = require('node:assert/strict');
const { KIT: K } = require('..').load();

function fixture() {
  const palette = [0, 0x304054, 0xa1bcde, 0xfffaf0, 0xfb4010, 0xffa100];
  const ramp = [0, 1, 2, 3], data = new Float32Array(64);
  const capture = { ramp: [1, 1, 1], t: [0.18, 0.55, 0.62], n: [[0, 1, 0], [1, 0, 0], [0, 0, 1]], ramps: [ramp] };
  const packedColor = i => ((palette[i] & 255) << 16) | (palette[i] & 65280) | (palette[i] >>> 16);
  for (let i = 0; i < 4; i++) {
    data[i * 16] = (i - 1) * 0.5;
    data[i * 16 + 3] = 3;
    data[i * 16 + 7] = packedColor(i);
  }
  const stage = K.stage({ count: 4, data, pal: palette });
  stage.rig = {
    bid: Uint16Array.of(1, 1, 0, 0), part: name => name === 'moving' ? 1 : -1,
    M: Float32Array.of(1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
  };
  return { stage, capture, data, packedColor };
}
const lamp = (extra = {}) => ({ p: [0.15, 1, 0], r: 2, s: 0.75, ...extra });

test('capture chains its predecessor with every argument and the original receiver', () => {
  let seen;
  const sculpt = { tap(...args) { seen = { receiver: this, args }; } };
  const cap = K.light.capture({ count: () => 8 }, sculpt);
  const ramp = [2, 3];
  sculpt.tap(ramp, 0.5, 0, 1, 0, false, 3);
  assert.deepEqual(seen, { receiver: sculpt, args: [ramp, 0.5, 0, 1, 0, false, 3] });
  assert.equal(cap.ramp[8], 1);
  sculpt.tap(ramp, 0.5, 0, 1, 0, true, 3);
  assert.equal(seen.args[5], true);
});

test('packed light reference agrees with painted rows through rotating, masked, coloured and flashed lights', () => {
  for (const keep of [undefined, 0, Infinity]) {
    const { stage, capture, data, packedColor } = fixture();
    const sun = { dir: [0, 1, 0], amb: 0.2, sky: 0.28, k: 0.31, parts: ['moving'], keep,
      lights: [lamp({ p: [-1, 0.8, 0], s: 0.35 })], shade: (x, y, z) => 0.9 + 0.1 * Math.cos(x + z) };
    const lights = [];
    const options = { sun }, packed = K.light.pack(stage, capture, options);
    const system = stage.add(K.light.system(stage, capture, lights, options));
    assert.equal(packed.count, 4);
    assert.deepEqual(Array.from(packed.rigRamp.slice(0, 3)), [0, 1, 1]);
    assert.equal(packed.rigRamp[12], -1);
    if (keep === Infinity) {
      for (let i = 0; i < 2; i++) {
        assert.equal(K.light.step(packed, i, data.subarray(i * 16, i * 16 + 3), capture.n[i]), i);
      }
      system.update(0);
      assert.equal(data[7], packedColor(0));
      assert.equal(data[23], packedColor(1));
    }
    assert.equal(K.light.step(packed, 3, [0, 0, 0], [0, 1, 0]), -1);
    lights.push(lamp(), lamp({ p: [0, 0.4, 0], ramp: [4, 5], vis: Uint8Array.of(255, 33, 220, 0) }));
    for (const [angle, flash] of [[0, 0], [0.7, 0.16], [-1.1, 0]]) {
      const c = Math.cos(angle), s = Math.sin(angle);
      stage.rig.M.set([c, -s, 0, s, c, 0, 0, 0, 1], 12);
      data[16] = 0.18 * angle;
      lights[0].p[0] = angle;
      lights[1].off = angle < 0;
      system.flash(flash, 0.2);
      stage.update(0, 0);
      for (let i = 0; i < 3; i++) {
        const [x, y, z] = capture.n[i], normal = i < 2 ? [c*x - s*y, s*x + c*y, z] : [x, y, z];
        const index = K.light.step(packed, i, data.subarray(i * 16, i * 16 + 3), normal, lights, flash);
        assert.equal(data[i * 16 + 7], packedColor(index), 'row ' + i + ' at angle ' + angle + ' with keep ' + keep);
      }
    }
  }
});

test('captured GLSL matches the CPU palette result in WebGL2', { skip: !process.env.INK_TEST_CHROME }, () => {
  const fs = require('node:fs');
  const os = require('node:os');
  const path = require('node:path');
  const { pathToFileURL } = require('node:url');
  const { execFileSync } = require('node:child_process');
  const { stage, capture } = fixture();
  const sun = { dir: [0, 1, 0], amb: 0.2, sky: 0.28, k: 0.31, parts: ['moving'], keep: Infinity,
    lights: [lamp({ p: [-1, 0.8, 0], s: 0.35 })] };
  const packed = K.light.pack(stage, capture, { sun });
  const expected = [], buffer = [];
  const colors = [4, 5];
  for (let i = 0; i < 4096; i++) {
    const row = i % 3;
    const a = i * 1.3453;
    const p = i < 3 ? Array.from(stage.D.subarray(16 * row, 16 * row + 3)) :
      [Math.sin(1.7 * a), Math.sin(a) * 0.3, Math.cos(4.3 * a) * 0.5].map(Math.fround);
    const n = i < 3 ? capture.n[row] : [Math.cos(a), Math.sin(a), 0].map(Math.fround);
    const visibility = i < 3 ? 0 : i % 256;
    const flash = i > 3 && i % 5 === 0 ? Math.fround(0.14) : 0;
    const lamp1 = lamp({ s: i < 3 ? 0 : 0.75, vis: new Uint8Array(3).fill(visibility), ramp: colors });
    const level = packed.normalLevel[row * 4 + 3], reference = packed.rigRamp[row * 4 + 3];
    buffer.push(...p, ...n, level, packed.rigRamp[row * 4 + 2], reference, packed.baked[row],
      lamp1.s, visibility / 255, flash);
    expected.push(K.light.step(packed, row, p, n, [lamp1], flash));
  }
  const shader = `#version 300 es
precision highp float;
layout(location=0) in vec3 p;
layout(location=1) in vec3 n;
layout(location=2) in vec4 entry;
layout(location=3) in vec3 inputs;
out float palette;
${K.light.glsl}
void main() {
  float baked = entry.x;
  float level = capturedSun(n, vec3(0,1,0), vec3(0.2,0.28,0.31));
  level += capturedLampShare(p, n, vec4(-1.0,0.8,0.0,2.0), 0.35, 1.0);
  float base = entry.y > 0.5 ? capturedBase(baked, level, 1.0, entry.z, true) : baked;
  float share = capturedLampShare(p, n, vec4(0.15,1.0,0.0,2.0), inputs.x, inputs.y);
  float additional = inputs.z + share, lit = base + additional;
  if (share > 0.0 && capturedOverride(share, base)) palette = 4.0 + float(capturedStep(lit, 2));
  else if (entry.w >= 0.0 && capturedAtRest(baked, base, additional)) palette = entry.w;
  else palette = float(capturedStep(lit, 4));
  gl_Position = vec4(0,0,0,1);
}`;
  const filename = 'light.html';
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-light-browser-'));
  try {
    fs.writeFileSync(path.join(temp, filename), `<!doctype html><canvas></canvas><pre id="result"></pre><script>
try {
  const gl = document.querySelector('canvas').getContext('webgl2');
  if (!gl) throw new Error('WebGL 2 is unavailable');
  function compile(type, source) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader));
    return shader;
  }
  const program = gl.createProgram();
  gl.attachShader(program, compile(gl.VERTEX_SHADER, ${JSON.stringify(shader)}));
  gl.attachShader(program, compile(gl.FRAGMENT_SHADER,
    '#version 300 es\\nprecision highp float; out vec4 color; void main(){color=vec4(0);}'));
  gl.transformFeedbackVaryings(program, ['palette'], gl.INTERLEAVED_ATTRIBS);
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
  gl.useProgram(program);
  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(${JSON.stringify(buffer)}), gl.STATIC_DRAW);
  for (const [i, size, offset] of [[0,3,0],[1,3,3],[2,4,6],[3,3,10]]) {
    gl.enableVertexAttribArray(i);
    gl.vertexAttribPointer(i, size, gl.FLOAT, false, 52, offset * 4);
  }
  const expected = ${JSON.stringify(expected)};
  const output = new Float32Array(expected.length);
  const out = gl.createBuffer();
  gl.bindBuffer(gl.TRANSFORM_FEEDBACK_BUFFER, out);
  gl.bufferData(gl.TRANSFORM_FEEDBACK_BUFFER, output.byteLength, gl.STREAM_READ);
  gl.bindBufferBase(gl.TRANSFORM_FEEDBACK_BUFFER, 0, out);
  gl.enable(gl.RASTERIZER_DISCARD);
  gl.beginTransformFeedback(gl.POINTS);
  gl.drawArrays(gl.POINTS, 0, expected.length);
  gl.endTransformFeedback();
  gl.getBufferSubData(gl.TRANSFORM_FEEDBACK_BUFFER, 0, output);
  const mismatch = expected.findIndex((n,i) => output[i] !== n);
  result.textContent = mismatch < 0 ? 'PASS ' + output.length :
    'Mismatch ' + mismatch + ': expected ' + expected[mismatch] + ' got ' + output[mismatch];
} catch (error) { result.textContent = error.stack; }
</script>`);
    const args = ['--headless', '--no-first-run', '--disable-background-networking', '--enable-unsafe-swiftshader',
      '--use-angle=swiftshader', '--user-data-dir=' + path.join(temp, 'profile'), '--dump-dom',
      pathToFileURL(path.join(temp, filename)).href];
    const html = execFileSync(process.env.INK_TEST_CHROME, args, { timeout: 30000, encoding: 'utf8', maxBuffer: 4e6,
      stdio: ['ignore', 'pipe', 'ignore'] });
    assert.equal(html.match(/<pre id="result">([^<]*)<\/pre>/)?.[1], 'PASS 4096');
  } finally {
    fs.rmSync(temp, { recursive: true, force: true });
  }
});

// node scripts/check.js : the comment guard over the library's own sources
const fs = require('node:fs'),
  path = require('node:path'),
  lib = require('..'),
  webgl = path.join(__dirname, '../src/webgl'),
  gpuFiles = fs.readdirSync(webgl).filter(file => file.endsWith('.mjs')).map(file => path.join(webgl, file)),
  bad = lib.lint(lib.files().concat(lib.demoFiles(), path.join(__dirname, '../webgl.mjs'), gpuFiles));
if (bad.length) {
  console.error('code after a // comment on the same line (it would never run):\n  ' + bad.join('\n  '));
  process.exit(1);
}
console.log('clean');

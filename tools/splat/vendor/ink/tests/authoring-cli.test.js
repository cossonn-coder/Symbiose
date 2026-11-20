const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { spawnSync } = require('node:child_process');

const root = path.join(__dirname, '..');
const cli = path.join(root, 'cli', 'ink-studio.js');
const passage = path.join(root, 'examples', 'editable-passage.js');
const doorway = '@/wall/parts/doorway', landing = '@/wall/parts/landing', cabinet = '@/wall/parts/cabinet';

function session(t) {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), 'ink-authoring-'));
  t.after(() => fs.rmSync(cwd, { force: true, recursive: true }));
  const file = name => path.join(cwd, name);
  const run = (args, status = 0) => {
    const result = spawnSync(process.execPath, [cli, ...args], { cwd, encoding: 'utf8' });
    assert.equal(result.status, status, result.stderr || result.stdout);
    return result;
  };
  return {
    file,
    edit(name, operations, revision) {
      fs.writeFileSync(file(name), JSON.stringify({ revision, operations }));
      return name;
    },
    call(mode, args = [], status = 0) {
      const result = run(['authoring', mode, passage, ...args], status);
      return status === 1 ? result.stderr : JSON.parse(result.stdout);
    },
    run
  };
}

test('the retained CLI previews, saves and reloads a generated doorway and its dependent landing', t => {
  const { call, edit, file, run } = session(t);
  const base = call('inspect');
  assert(base.valid);
  assert.deepEqual(base.parts.map(part => part.id), [cabinet, doorway, landing, 'wall']);
  const opening = base.parts.find(part => part.id === doorway);
  assert.equal(opening.derived.key, 'doorway');
  assert.deepEqual(opening.anchorFrame.p, [0, 0, -.2]);
  assert.deepEqual(opening.bounds, { min: [-.675, 0, -.2], max: [.675, 1.94, .2] });
  assert.equal(base.parts.find(part => part.id === landing).surfaces[0].id, 'top');

  const moves = edit('resize.json', [{ op: 'update', id: doorway,
    patch: { parameters: { width: .94 }, anchor: { uv: [.58, 0] } } }], base.revision);
  const preview = call('preview', [moves, '--image', 'preview.png', '--w', '320', '--h', '240']);
  assert(preview.valid);
  assert.equal(preview.baseRevision, base.revision);
  assert.deepEqual(preview.changes, { added: [], removed: [], updated: [doorway, landing] });
  assert(preview.checks.find(check => check.id === 'walk-to-landing').reached[0] > .3);
  assert.notEqual(preview.splatCount, base.splatCount);
  assert.equal(fs.readFileSync(file('preview.png')).subarray(1, 4).toString(), 'PNG');
  assert.equal(call('inspect').revision, base.revision);

  const applied = call('apply', [moves, '--out', 'first.json']);
  assert.equal(applied.revision, preview.revision);
  const saved = fs.readFileSync(file('first.json'), 'utf8');
  const restored = call('inspect', ['--authoring', 'first.json']);
  assert.equal(restored.revision, preview.revision);
  assert.deepEqual(restored.parts.find(part => part.id === cabinet), base.parts[0]);
  assert.equal(restored.parts.find(part => part.id === doorway).parameters.width, .94);
  run(['render', passage, '--authoring', 'first.json', '--out', 'render.png', '--w', '320', '--h', '240']);
  assert.deepEqual(fs.readFileSync(file('render.png')), fs.readFileSync(file('preview.png')));
  assert.match(call('apply', [moves, '--out', 'first.json'], 1), /Output already exists/);
  assert.equal(fs.readFileSync(file('first.json'), 'utf8'), saved);
  assert.match(call('apply', [moves, '--authoring', 'first.json', '--out', 'stale.json'], 1), /Stale authoring revision/);
  assert(!fs.existsSync(file('stale.json')));

  const wall = edit('wall.json', [{ op: 'update', id: 'wall', patch: { parameters: { width: 5.4 } } }], restored.revision);
  call('apply', [wall, '--authoring', 'first.json', '--out', 'second.json']);
  const rebuilt = call('inspect', ['--authoring', 'second.json', '--part', doorway]);
  assert.equal(rebuilt.parts[0].id, doorway);
  assert.equal(rebuilt.parts[0].parameters.width, .94);
  assert.equal(rebuilt.parts[0].seed, opening.seed);
  assert(rebuilt.parts[0].anchorFrame.p[0] > restored.parts.find(part => part.id === doorway).anchorFrame.p[0]);
});

test('a blocked route prevents writes and optional generated parts can be suppressed and restored', t => {
  const { call, edit, file } = session(t);
  const blocked = edit('block.json', [{ op: 'update', id: cabinet,
    patch: { parameters: { position: [0, .42, -.50] } } }]);
  const preview = call('preview', [blocked, '--image', 'blocked.png'], 2);
  assert.equal(preview.valid, false);
  assert.equal(preview.checks.find(check => check.id === 'walk-to-landing').pass, false);
  const result = call('apply', [blocked, '--out', 'blocked.json'], 2);
  assert.deepEqual(result, preview);
  assert(!fs.existsSync(file('blocked.json')));
  assert(!fs.existsSync(file('blocked.png')));

  const suppress = edit('suppress.json', [{ op: 'suppress', id: cabinet }]);
  const hidden = call('apply', [suppress, '--out', 'hidden.json']);
  assert.deepEqual(hidden.changes.removed, [cabinet]);
  assert.match(call('inspect', ['--authoring', 'hidden.json', '--part', cabinet], 1), /Unknown part/);
  const allow = edit('allow.json', [{ op: 'allow', id: 'wall', rule: 'parts', key: 'cabinet' }]);
  const shown = call('preview', [allow, '--authoring', 'hidden.json']);
  assert.deepEqual(shown.changes.added, [cabinet]);
});

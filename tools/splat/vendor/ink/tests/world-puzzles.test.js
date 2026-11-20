const { test } = require('node:test');
const assert = require('node:assert/strict');
const { KIT: { world: W } } = require('..').load();
const gate = require('../examples/world-puzzle-gate.json');
const actions = require('../examples/world-puzzle-gate.actions.json');

const input = (tick, port, value, id) => ({ tick, action: 'world/input', args: { port, value }, ...(id && { id }) });
const trace = (run, name, args) => run.query().trace(name, {}, args).value;
const json = value => JSON.parse(JSON.stringify(value));
const lockSpec = gate.systems.lock.config;
const world = (config = lockSpec) => ({ causality: true, systems: { lock: { kind: 'puzzle', config } } });

test('ordered pulses, reset and timer expiry produce inspectable, replayable decisions', () => {
  const recipe = world({ ...lockSpec, nodes: {
    ...lockSpec.nodes, 'timed-switch': { ...lockSpec.nodes['timed-switch'], ticks: 3 }
  } });
  const run = W.runtime.create(recipe);
  const why = () => trace(run, 'lock/why');
  const expected = () => why().blockers.find(item => item.node === 'ordered-switches')?.expected;
  assert.equal(expected(), 'prime');
  assert(why().blockers.some(row => row.node === 'plate' && row.reason === 'inactive-input'));

  run.schedule([
    input(1, 'lock/switch', [true], 'wrong-order'),
    input(2, 'lock/prime', [true]),
    input(2, 'lock/switch', [true]),
    input(3, 'lock/prime', [true], 'prime'),
    input(4, 'lock/plate', true, 'plate'),
    input(4, 'lock/switch', [true], 'switch'),
    input(8, 'lock/reset', [true]),
    input(8, 'lock/prime', [true]),
    input(9, 'lock/prime', [true]),
    input(10, 'lock/switch', [true])
  ]);
  run.advance(1);
  assert.equal(expected(), 'prime');
  run.advance(2);
  assert.equal(expected(), 'prime');
  run.advance(3);
  assert.equal(expected(), 'switch');
  run.advance(4);
  assert.deepEqual(why(), { output: 'open', active: true, blockers: [] });
  const fork = W.runtime.create(recipe, { checkpoint: json(run.checkpoint()) });
  run.advance(6);
  assert.equal(why().active, true);
  run.advance(7);
  fork.advance(7);
  assert.deepEqual(fork.checkpoint(), run.checkpoint());
  assert.deepEqual(why().blockers, [
    { node: 'timed-switch', reason: 'window-expired', trigger: 'ordered-switches', ticks: 3 }
  ]);
  const causal = trace(run, 'world/cause', { port: 'lock/open' });
  const expiry = causal.nodes.find(row => row.tick === 7 && row.kind === 'puzzle-evaluated');
  assert.equal(expiry.data.blockers[0].reason, 'window-expired');
  for (const id of ['prime', 'switch', 'plate'])
    assert(causal.nodes.some(row => row.data.commandId === id));
  run.advance(8);
  assert.equal(expected(), 'prime');
  run.advance(10);
  assert.equal(why().active, true);
  assert.deepEqual(W.runtime.replay(json(run.recording())).checkpoint(), run.checkpoint());

  const tampered = json(run.checkpoint());
  tampered.states.lock.memory['timed-switch'] = 70;
  assert.throws(() => W.runtime.create(recipe, { checkpoint: tampered }), /Invalid puzzle window/);
});

test('repeated sequence symbols, boolean edges, latch and logical blockers compose', () => {
  const run = W.runtime.create(world({
    inputs: { press: 'event', turn: 'bool', clear: 'event', lever: 'bool', safe: 'bool' },
    nodes: {
      sequence: { op: 'sequence', steps: ['press', 'press', 'turn'], reset: 'clear' },
      stored: { op: 'latch', set: 'sequence', reset: 'clear' },
      either: { op: 'any', inputs: ['stored', 'lever'] },
      quorum: { op: 'count', inputs: ['stored', 'lever', 'safe'], min: 2 },
      unsafe: { op: 'not', input: 'safe' }
    },
    outputs: { open: 'either', alarm: 'unsafe', second: 'quorum' }
  }));
  run.schedule([input(1, 'lock/press', [true]), input(2, 'lock/press', [true]),
    input(3, 'lock/press', [true]), input(4, 'lock/turn', true),
    input(5, 'lock/clear', [true]), input(6, 'lock/press', [true]),
    input(7, 'lock/press', [true]), input(8, 'lock/turn', false),
    input(9, 'lock/turn', true), input(9, 'lock/safe', true)]);
  assert.equal(trace(run, 'lock/why', { output: 'open' }).blockers[0].reason, 'no-alternative-active');
  run.advance(4);
  assert.equal(trace(run, 'lock/why', { output: 'open' }).active, true);
  assert.deepEqual(trace(run, 'lock/why', { output: 'second' }).blockers, [
    { node: 'quorum', reason: 'too-few-active', needed: 2, active: ['stored'], alternatives: ['lever', 'safe'] }
  ]);
  run.advance(7);
  assert.equal(trace(run, 'lock/why', { output: 'open' }).active, false);
  run.advance(9);
  assert.equal(trace(run, 'lock/why', { output: 'second' }).active, true);
  assert.deepEqual(trace(run, 'lock/why', { output: 'alarm' }).blockers, [
    { node: 'unsafe', reason: 'must-be-inactive', input: 'safe' }
  ]);
});

test('bounded search distinguishes a reachable witness, exhausted state space and a search limit', () => {
  const run = W.runtime.create(gate);
  const same = run.checkpoint();
  const result = trace(run, 'lock/solve');
  assert.deepEqual(result.witness.map(({ move }) => move), ['stand-on-plate', 'prime-switch', 'throw-switch']);
  assert.equal(result.ticks, 3);
  assert.equal(trace(run, 'lock/solve', { maxTicks: 2 }).status, 'limit');
  assert.equal(trace(run, 'lock/solve', { maxTransitions: 1 }).status, 'limit');
  assert.deepEqual(run.checkpoint(), same);

  run.schedule(result.witness.flatMap(row => [
    ...Object.entries(row.set).map(([pin, value]) => input(row.tick, 'lock/' + pin, value)),
    ...row.pulse.map(pin => input(row.tick, 'lock/' + pin, [true]))
  ]));
  run.advance(60, { scenario: true });
  assert.equal(run.scenario.status, 'win');
  assert(run.query().probe('scout/agents').value.scout.position[0] > 1.25);

  const locked = W.runtime.create(gate);
  locked.schedule(actions.filter(command => command.id !== 'prime-switch'));
  locked.advance(60);
  assert.equal(locked.scenario.status, 'timeout');
  assert(locked.query().probe('scout/agents').value.scout.position[0] < 0);
  const impossible = W.runtime.create(world({ ...lockSpec, moves: { press: { pulse: ['switch'] } } }));
  assert.equal(trace(impossible, 'lock/solve').status, 'unreachable');
});

test('prefab instances expose stable ports and keep their switch progress independent', () => {
  const seed = W.manifest({ prefabs: { gate: {
    params: { duration: 45 }, systems: { lock: { kind: 'puzzle', config: {
      ...lockSpec, nodes: {
        ...lockSpec.nodes, 'timed-switch': { ...lockSpec.nodes['timed-switch'], ticks: { $param: 'duration' } }
      }
    } } },
    ports: { plate: 'lock/plate', prime: 'lock/prime', switch: 'lock/switch', open: 'lock/open' }
  } } });
  const east = W.stamp(seed, 'gate', 'east', { params: { duration: 2 } }).world;
  const run = W.runtime.create(W.stamp(east, 'gate', 'west').world);
  run.schedule([input(1, 'east/plate', true), input(1, 'east/prime', [true]), input(2, 'east/switch', [true])]);
  run.advance(2);
  assert.equal(trace(run, 'east.lock/why').active, true);
  assert.equal(trace(run, 'west.lock/why').active, false);
  run.advance(4);
  assert.equal(trace(run, 'east.lock/why').blockers[0].reason, 'window-expired');
});

test('a scheduled puzzle buffers a connected control pulse and counts its own evaluations', () => {
  const run = W.runtime.create({
    systems: {
      button: { kind: 'control', config: { op: 'pulse' } },
      lock: { kind: 'puzzle', schedule: { every: 2 }, config: {
        inputs: { press: 'event' },
        nodes: { timer: { op: 'window', trigger: 'press', ticks: 2 } },
        outputs: { open: 'timer' }
      } }
    },
    connections: [{ from: 'button/value', to: 'lock/press' }],
    commands: [input(1, 'button/value', true)]
  });
  const active = () => trace(run, 'lock/why').active;
  run.advance(1);
  assert.equal(active(), false);
  run.advance(2);
  assert.equal(active(), true);
  run.advance(5);
  assert.equal(active(), true);
  run.advance(6);
  assert.equal(trace(run, 'lock/why').blockers[0].reason, 'window-expired');
});

test('puzzle manifests reject invalid operations, references, timers, moves and cycles', () => {
  for (const [overrides, reason] of [
    [{ inputs: { plate: 'number' } }, /bool or event/],
    [{ nodes: { a: { op: 'unknown' } } }, /Unknown puzzle operation/],
    [{ nodes: { a: { op: 'not', input: 'absent' } } }, /Unknown puzzle reference/],
    [{ nodes: { a: { op: 'window', trigger: 'prime', ticks: 0 } } }, /window duration/],
    [{ nodes: { a: { op: 'not', input: 'b' }, b: { op: 'not', input: 'a' } }, outputs: { open: 'a' } }, /dependency cycle/],
    [{ moves: { bad: { set: { prime: true } } } }, /Invalid puzzle move/]
  ]) assert.throws(() => W.runtime.validate(world({ ...lockSpec, ...overrides })), reason);
});

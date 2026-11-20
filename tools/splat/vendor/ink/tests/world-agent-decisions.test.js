const { test } = require('node:test');
const assert = require('node:assert/strict');
const { KIT: { world: W } } = require('..').load();
const example = require('../examples/world-resident-shelter.json');

const json = value => JSON.parse(JSON.stringify(value));
const why = (run, entity = 'resident') => run.query().trace('folk/why', { entity }).value;
const actor = run => run.query().probe('folk/agents').value.resident;
const input = (tick, port, value) => ({ tick, action: 'world/input', args: { port, value } });
const at = [0, .13, 0];

test('a resident rejects a locked destination, arrives at shelter and resumes work after returning', () => {
  const run = W.runtime.create(example);
  run.advance(12);
  assert.equal(why(run).choice.activity, 'work');
  assert.equal(why(run).phase, 'complete');
  run.advance(13);
  const picked = why(run);
  assert.equal(picked.choice.destination, 'porch');
  assert.equal(picked.phase, 'traveling');
  assert.deepEqual(picked.evidence.rejected, [{
    activity: 'shelter', destination: 'shed', reason: 'destination-condition',
    checks: [{ field: 'world/signal', status: 'ok', pass: false, observed: false, reason: 'Door is locked' }]
  }]);

  const selected = run.history.find(event => event.tick === 13 && event.kind === 'activity-selected');
  const cause = run.query().trace('world/cause', {}, { event: selected.id }).value;
  assert(cause.nodes.some(node => node.kind === 'activity-selected-decision'));
  assert(cause.nodes.some(node => node.data.field === 'weather/rain' && node.data.result.value === 5.2));
  assert(cause.nodes.some(node => node.data.field === 'world/signal' && node.data.result.value === false));

  const fork = W.runtime.create(example, { checkpoint: json(run.checkpoint()) });
  run.advance(50);
  assert.equal(why(run).phase, 'complete');
  assert(actor(run).position[0] < -4.8);
  assert(run.history.some(event => event.kind === 'activity-started' &&
    event.choice.activity === 'shelter' && event.tick > selected.tick));
  run.advance(65);
  assert.equal(why(run).choice.activity, 'work');
  assert.equal(why(run).phase, 'traveling');
  assert(actor(run).position[0] < -4);
  run.advance(100);
  assert.equal(why(run).phase, 'complete');
  const completed = run.history.filter(event => event.kind === 'activity-completed' && event.choice.activity === 'work');
  assert.equal(completed.length, 2);
  assert(completed.at(-1).tick > 65 && Math.abs(completed.at(-1).position[0] + 1.72) < .15);
  assert.deepEqual(run.query().probe('folk/decisions').value.resident, why(run));
  fork.advance(100);
  assert.deepEqual(fork.checkpoint(), run.checkpoint());
  assert.deepEqual(W.runtime.replay(json(run.recording())).checkpoint(), run.checkpoint());
});

test('a nominally available destination still needs a collision route', () => {
  const cut = W.runtime.create({ ...example, connections: [] });
  cut.schedule([input(1, 'lock/key', true)]);
  cut.advance(14);
  const fallback = why(cut);
  assert.equal(fallback.choice.destination, 'porch');
  assert.equal(fallback.evidence.rejected[0].reason, 'route-rejected');
  assert.equal(fallback.evidence.rejected[0].obstacle.body, 'shed-door');

  const open = W.runtime.create(example);
  open.schedule([input(1, 'lock/key', true)]);
  open.advance(50);
  assert.equal(why(open).choice.destination, 'shed');
  assert.equal(why(open).phase, 'complete');
  assert(actor(open).position[0] > .65);
});

test('a door that closes during travel blocks the attempt and the agent tries another site', () => {
  const scene = json(example);
  delete scene.systems.folk.config.decisions.activities.shelter.destinations.shed.when;
  scene.commands = scene.commands.filter(command => command.id !== 'rain-clears');
  const run = W.runtime.create(scene);
  run.schedule([input(1, 'lock/key', true), input(14, 'lock/key', false)]);
  run.advance(13);
  assert.equal(why(run).choice.destination, 'shed');
  assert.equal(why(run).phase, 'traveling');
  run.advance(80);
  const blocked = run.history.find(event => event.kind === 'activity-blocked' && event.choice.destination === 'shed');
  assert.equal(blocked.reason, 'movement-blocked');
  assert.equal(why(run).choice.destination, 'porch');
  assert.equal(why(run).phase, 'complete');
  assert(!run.history.some(event => event.kind === 'activity-started' && event.choice.destination === 'shed'));
});

function workshop() {
  return {
    dt: .1,
    entities: { resident: { position: at }, rover: { position: [0, .13, 1] } },
    systems: {
      timer: { kind: 'fields', config: { fields: { ready: { default: 0 }, safe: { default: 1 } } } },
      folk: { kind: 'agents', config: {
        bounds: { min: [-2, 0, -2], max: [3, 2, 2] }, ground: at[1],
        species: { walker: { mode: 'walk' } },
        agents: { resident: { species: 'walker', position: at }, rover: { species: 'walker', position: [0, .13, 1] } },
        decisions: { interval: 7, members: { resident: ['work'] }, activities: {
          work: { duration: 3, destinations: { here: { at } },
            when: [{ field: 'timer/safe', when: { value: 1 } }],
            completeWhen: [{ field: 'timer/ready', when: { value: 1 }, reason: 'Waiting for tools' }] }
        } }
      } }
    }
  };
}
const set = (tick, field, value) => ({ tick, action: 'timer/set', args: { field,
  region: { bounds: { min: [-2, -1, -2], max: [3, 2, 2] }, value } } });

test('work needs continuous eligibility and an observed completion condition', () => {
  const run = W.runtime.create(workshop());
  run.schedule([set(2, 'safe', 0), set(3, 'safe', 1), set(8, 'ready', 1),
    { tick: 1, action: 'folk/seek', args: { agent: 'rover', to: [1, .13, 1] } }]);
  run.advance(2);
  assert.equal(why(run).blockers[0].reason, 'conditions-changed');
  run.advance(7);
  assert.equal(why(run).phase, 'acting');
  assert.equal(why(run).blockers[0].reason, 'Waiting for tools');
  assert.equal(run.history.filter(event => event.kind === 'activity-completed').length, 0);
  run.advance(12);
  assert.equal(why(run).phase, 'complete');
  assert.deepEqual(run.history.filter(event => event.kind === 'activity-started').map(event => event.tick), [1, 3]);
  assert.deepEqual(run.history.filter(event => event.kind === 'activity-completed').map(event => event.tick), [8]);
  assert(run.query().probe('folk/agents').value.rover.position[0] > .9);
  assert.throws(() => run.schedule([{ tick: 13, action: 'folk/seek',
    args: { agent: 'resident', to: [2, .13, 1] } }]), /activity policy owns/);
});

test('policy validation reports unknown members and fields and leaves old agents compatible', () => {
  const badMember = workshop(), badField = workshop(), plain = workshop();
  badMember.systems.folk.config.decisions.members.unknown = ['work'];
  badField.systems.folk.config.decisions.activities.work.when[0].field = 'absent';
  assert.throws(() => W.runtime.validate(badMember), /activity list for unknown/);
  assert.throws(() => W.runtime.validate(badField), /Unknown activity condition field/);
  delete plain.systems.folk.config.decisions;
  const run = W.runtime.create(plain);
  assert.equal(run.query().probe('folk/decisions').status, 'unavailable');
  assert(!Object.hasOwn(run.checkpoint().states.folk, 'decisions'));
  assert.deepEqual(W.runtime.create(plain, { checkpoint: json(run.checkpoint()) }).checkpoint(), run.checkpoint());
});

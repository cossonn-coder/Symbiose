const test = require('node:test');
const assert = require('node:assert/strict');
const studio = require('../index.js');
const kit = studio.load();
const { KIT: K, LookInputs, RenderStages, makeBuilder } = kit;
const { authoring: A, world: W } = K;

const id = 'driven/steel';
const matrix = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
const pack = {
  format: 'ink-studio/asset-pack', id: 'driven', title: 'Driven looks', version: 1, revision: 1,
  looks: [{ id, label: 'Steel heat', stage: 'lit', params: { red: .3, count: 0 }, stack: {
    name: 'Steel heat', steps: [{ type: 'channelMix', matrix, offset: [{ $param: 'red' }, 0, 0] }]
  } }]
};
const catalog = A.assetPacks.create({ packs: [pack] });
const time = { source: 'time', keys: [[0, 0], [2, 1]] };
const select = { object: 'steel' };
const small = { w: 65, h: 65, px: 1, ortho: true };
const center = (32 * 65 + 32) * 3;

test('time drives a material look on the same baked geometry in any frame order', () => {
  const binding = { asset: id, strength: 0, params: { red: 1 }, inputs: { strength: time } };
  const B = makeBuilder(1, [0, 0x404040]);
  const { surface } = A.looks.material({}, binding, catalog);
  B.surfaceNext(surface, 0, 0, 1, [0, 1, 0]);
  B.disc(0, 0, 0, [0, 0, 1], .8, .026, B.P[1], 3);
  B.describeSplats(0, 1, { object: 'steel' });
  const scene = B.finish({ cam: { target: [0, 0, 0], dist: 4, yaw: 0, pitch: 0 } });
  const frame = t => studio.render(scene, { ...small, t });
  const hot = frame(2), cold = frame(0), warm = frame(1);
  assert.deepEqual(hot.rgb, frame(2).rgb);
  assert(cold.rgb[center] < warm.rgb[center] && warm.rgb[center] < hot.rgb[center]);
  const result = W.query.fromScene(scene, 1).probe('look/output', select, { stage: 'lit', rgb: [0, 0, 0] });
  assert.equal(result.value.targets[0].stages.lit[0].inputs.strength, .5);
});

test('look input tables validate, preserve typed values, and use authored fallbacks for missing reads', () => {
  const driver = A.looks.bind({ asset: id, strength: .22, inputs: {
    strength: { source: 'signal', port: 'heater/value', keys: [[0, 0], [1, 1]] },
    params: {
      red: { source: 'query', field: 'field/temperature', target: { entity: 'steel', socket: 'probe' },
        path: ['value'], keys: [[0, .1], [100, .8]], interpolation: 'step' },
      count: { source: 'query', field: 'field/count' }
    }
  } }, catalog).driver;
  const seen = [];
  const session = LookInputs.session(0, () => ({ probe(field, site, args) {
    seen.push([field, site, args]);
    return field === 'world/signal' ? { status: 'ok', value: true } :
      field === 'field/temperature' ? { status: 'ok', value: { value: 100 } } : { status: 'missing' };
  } }));
  const first = LookInputs.resolve(driver, session);
  assert.equal(first.strength, 1);
  assert.deepEqual(first.params, { red: .8, count: 0 });
  assert.deepEqual(seen[0], ['world/signal', undefined, { port: 'heater/value' }]);
  assert.deepEqual(seen[1][1], { entity: 'steel', socket: 'probe' });
  assert.equal(LookInputs.resolve(driver, session), first);
  assert.equal(seen.length, 3);
  assert.equal(LookInputs.resolve(driver, LookInputs.session(0)).strength, .22);

  for (const inputs of [
    { params: { imaginary: time } },
    { strength: { source: 'time', keys: [[1, 0], [1, 1]] } },
    { params: { red: { source: 'query', field: 'look/output' } } },
    { params: { red: { source: 'time', keys: [[0, 'red']] } } }
  ]) assert.throws(() => A.looks.bind({ asset: id, inputs }, catalog), /look input|look parameter/i);
});

test('a restored tick reproduces field, signal, and elapsed-time inputs and exact rendered RGB', () => {
  const input = {
    dt: .25, seed: 14, assetPacks: [pack],
    entities: { steel: { position: [0, .7, 0], visual: { half: [.54, .4, .3], ramp: [3, 4, 5], surfaceId: 'steel' } } },
    systems: { thermo: { kind: 'fields', config: { fields: { temperature: { default: 20 } } } },
      heater: { kind: 'control', config: { op: 'pass' } } },
    visual: { bounds: { min: [-1.2, -.2, -1], max: [1.2, 1.7, 1] }, camera: { target: [0, .5, 0], dist: 4, yaw: .12, pitch: .25 },
      look: { renderStages: [{ select: { surface: 'steel' }, asset: { asset: id, strength: 0, inputs: {
        strength: { source: 'signal', port: 'heater/value' },
        params: { red: { source: 'query', field: 'thermo/temperature', target: { entity: 'steel' }, keys: [[20, .1], [1000, 1]] },
          count: { source: 'time' } }
      } } }] } }
  };
  const run = W.runtime.create(input);
  const view = () => W.visual(kit, run.view(), run.query());
  const cold = studio.render(view(), small).rgb;
  run.schedule([
    { tick: 2, action: 'world/input', args: { port: 'heater/value', value: .8 } },
    { tick: 3, action: 'thermo/set', args: { field: 'temperature', region: { bounds: { min: [-1, 0, -1], max: [1, 1, 1] }, value: 1000 } } }
  ]);
  run.advance(5);
  const checkpoint = JSON.parse(JSON.stringify(run.checkpoint()));
  const resumed = W.runtime.create(checkpoint.world, { checkpoint });
  const frame = studio.render(view(), small).rgb;
  assert.notDeepEqual(frame, cold);
  assert.deepEqual(studio.render(W.visual(kit, resumed.view(), resumed.query()), small).rgb, frame);
  const probe = source => source.query().probe('look/output', { surface: 'steel' }, { stage: 'lit', rgb: [0, 0, 0] }).value;
  assert.deepEqual(probe(resumed), probe(run));
  assert.deepEqual(probe(resumed).targets[0].stages.lit[0].inputs, { strength: .8, params: { red: 1, count: 1.25 } });
});

test('a driven optical palette honors strength at a saved sample time', () => {
  const palette = '#ff0000';
  const looks = { ...pack, looks: [{ id, label: 'Optical steel', palette: { palette: [palette] } }] };
  const registry = A.assetPacks.create({ packs: [looks] });
  const scope = { medium: 'pool' };
  const look = A.looks.scene({ optics: [{ select: scope, asset: { asset: id, strength: 0, inputs: { strength: time } } }] }, registry);
  const transform = t => RenderStages.optics(look.optics, { lookInputs: LookInputs.session(t) }).transform(scope)([0, 0, 0]);
  assert.deepEqual(transform(.8), [0, 0, 0]);
  assert.deepEqual(transform(1), [1, 0, 0]);
});

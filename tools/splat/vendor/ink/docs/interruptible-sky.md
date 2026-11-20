# Interruptible sky and weather transitions

Trigger a transition while a sky track or another transition is playing. The new transition takes its starting values from the exact sample at its trigger time. A storm can inherit the current dusk colours, sun direction, daylight, wind, rain, and fog before blending to its own values. Sky colours still blend in linear light.

The [squall example](../examples/interruptible-sky.js) interrupts dusk at three seconds and takes 2.4 seconds to reach the storm.

```sh
ink-studio clip examples/interruptible-sky.js --from 1 --to 6 --fps 12 --w 200 --h 120 --px 1 --raw --out squall.png
ink-studio transition-review examples/interruptible-sky.js --w 200 --h 120 --raw --out trigger-review.png
```

Use [Conditional weather tracks](conditional-weather.md) to trigger the same transition from a scene cue, a region, or a simulation condition.

## Author or trigger a transition

Put a `transitions` array next to `profiles`, `sequences`, and `tracks` in a sky definition. It works in JSON dioramas and in the `skyEnvironment` of an environment pack.

```json
{
  "transitions": [
    { "at": 3, "profile": "storm", "duration": 2.4 },
    { "at": 4.5, "profile": "clearing", "duration": 2, "ease": "linear" }
  ]
}
```

Use the same seconds as the sky clock. A destination can contain only the channels it needs to change. Each of those channels needs a starting value of the same type in the defaults or tracks. Other channels continue their existing motion. A channel holds its destination after the fade until another transition supplies a value for it. For events at the same time, the later entry takes precedence on shared channels.

A live host can keep a compiled sky and schedule an interruption when a cue happens.

```js
let sky = K.skyEnvironment.compile(definition);
sky = sky.interrupt({ at: skySeconds, profile: 'storm', duration: 2.4 });
world.skyEnvironment = sky;
```

`interrupt()` returns a new clock. Keep `sky.transitions` with the original sky definition to replay the same cues. A host that owns its own weather binding can rebind it to the returned clock with `K.weather.bind(sky, settings)`. The headless renderer does this automatically, including retained weather replay during seeks.

Pass a replacement cue list with `--sky-transitions file.json` or `render(world, { skyTransitions: cues })`. The file contains the array itself. Use `--sky-transitions off` or `skyTransitions: false` to compare against the underlying tracks. A track pin supplies the underlying values for both ordinary playback and the starting samples of any transitions.

# Authored lightning

Use `K.weather.lightning({ events, cues })` to compile timed world-space flashes. Pass the result as `lightning` in `B.finish`. A scene can also supply the descriptor directly, including under `finish.lightning` in a JSON diorama. Lightning is enabled when the scene has events.

```js
const cues = [K.anim.cue('thunder-over-water', 'sound', 1.2)];
const lightning = K.weather.lightning({
  cues,
  events: [{
    id: 'western-flash',
    cue: 'thunder-over-water',
    at: [-6, 8, -18],
    duration: 0.5,
    radius: 24,
    falloff: 2.4,
    intensity: 2.8,
    color: '#b6c1ff',
    attack: 0.08
  }]
});
return B.finish({ ...sceneSettings, lightning });
```

| Field | Description |
| --- | --- |
| `id` | Unique name for the flash. |
| `at` | World-space position as `[x, y, z]`. |
| `time` or `cue` | Start in scene seconds, or the ID of a cue in `cues`. Cues can come from `K.anim.cue`, a retimed clip sequence's `cues`, or `[time, id]` pairs. Referenced IDs must resolve to a single enabled cue. |
| `duration` | Seconds from start through decay. Defaults to 0.35. |
| `radius` | Reach of the light in world units. Defaults to 18. |
| `falloff` | Positive exponent controlling attenuation inside the radius. Higher values concentrate the light near its source. Defaults to 2. |
| `intensity` | Peak brightness. Defaults to 2.5. |
| `color` | Light color in `#rrggbb`. Defaults to `#cfe6ff`. |
| `attack` | Fraction of the duration used for the rise, from 0 inclusive to 1 exclusive. Use 0 for an instant onset. Defaults to 0.08. |

A flash adds a sky halo, lights the existing cloud field and lit volumes, and illuminates nearby scene surfaces. Foreground objects can read as silhouettes against the brighter clouds. Reflections with `source: 'scene'` sample the same flash, including from the surface position when looking across water. The renderer evaluates the track at the scene time. Overlapping events add together, and you can sample times in any order. Hosts can read `lightning.markers` or `lightning.eventsBetween(from, to)` to synchronize sound or other effects. The second argument is included and the first is excluded.

Use `lightning: false` in render options to disable it, or pass a replacement descriptor. The headless CLI accepts the same choices via `--lightning on|off|file.json`.

```sh
node cli/ink-studio.js render examples/lightning-headland.js --raw --t 1.28 --out flash.png
node cli/ink-studio.js render examples/lightning-headland.js --raw --t 1.28 --lightning off --out quiet.png
```

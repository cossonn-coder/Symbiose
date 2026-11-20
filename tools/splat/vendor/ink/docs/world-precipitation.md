# World-space rain and snow

Set `worldSpace: true` when laying out rain or snow with `K.weather.fall`. Ink’s CPU renderer draws each drop and flake at its animated world position using the scene’s splat depth order. Foreground geometry can hide precipitation, and nearby drops can pass in front of it. The emitters work in perspective and orthographic views.

```js
const occluder = K.atmosphere.occluder(S.modelSource().field.sdf, {
  bias: .008, step: .018, steps: 56
});
S.bake();
K.weather.fall(B, {
  kind: 'rain', worldSpace: true, profile: true,
  box: [-8, 8, -6, 6], top: 6, ground: () => 0,
  n: 900, cols: [18, 19, 20], speed: 9, len: .13
});
const world = B.finish({
  cam, skyEnvironment, weatherBinding: { rainFull: .6, snowFull: .7 },
  precipitation: { occluder, lightStrength: .65 },
  lights
});
```

Use `occluder` to stop particles at roofs or other geometry. Capture the sculpt field before baking to use the same shapes visible in the scene. The renderer traces from the spawn point along the particle’s flight so reaching the side of a roof after a hit does not bring that particle back. A custom query takes `(x, y, z, unitDirection, distance, time)` and returns true for a hit. Increase `flightSegments` for highly curved paths or use a smaller march step for thin blockers.

Rain aligns its streaks with the current wind. Rain and flakes integrate recent profile wind from their birth to the current time, so gusts bend their paths and frames can be rendered in any order. With `profile: true`, `rain` and `snowfall` drive emission opacity through the [weather binding](weather-binding.md). `rainFull` and `snowFull` set the rates at which opacity reaches full strength. Emitters without `profile` use their own coverage. Supply wind from the environment track, `world.anim.wind`, or an explicit render `wind` override.

Particles pick up color from the scene’s point lamps and its [volume point lights and spotlights](fog-lighting.md). The geometry query also shadows ordinary lamps. Volume lights use their own shadow setting.

Use [rain impacts and runoff](rain-impacts.md) to bind the flight contacts to water, paving, and roof drains.

## Compare and configure

```sh
ink-studio render examples/lantern-squall.js --t 1.9 --raw --out squall.png
ink-studio render examples/lantern-squall.js --t 1.9 --raw --world-precipitation off --out clear.png
```

Use `--world-precipitation on|off|file.json` or the `precipitation` render option. A JSON override can set `rain` and `snow` opacity multipliers from 0 to 1, `lightStrength`, `flightSegments`, and `occlusion`. Use `"occlusion": false` to compare unchecked flight against roof blocking at the same time. The [lantern squall example](../examples/lantern-squall.js) transitions from snow through sleet to rain.

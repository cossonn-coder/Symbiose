# Weather profiles for rendering and simulation

Enable `weatherBinding: true` on a scene with a [sky environment](shared-sky-reflections.md) to use profile channels for weather. Each render reads the active track values at scene time or `--sky-time`. A profile selection with `--sky-profile weather=storm` applies to the same track across sky rendering, precipitation, atmosphere, and the retained surface simulation.

| Profile channel | Effect |
| --- | --- |
| `rain` | Rain rate for the solver. Mark rain splats with `K.weather.fall(B, { kind: 'rain', profile: true, ... })` to drive their opacity from this rate. |
| `windGust` | Optional gust multiplier from 0 to 3 for the [shared wind field](wind-field.md). |
| `windX`, `windZ` | Horizontal world velocity in scene units per second. Moves and tilts bound rain, bends airflow-enabled materials, transports wind-driven fog density fields, and contributes to drying. |
| `humidity`, `airTemperature`, `daylight` | Humidity and daylight are fractions. Air temperature is in degrees Celsius. All three feed the retained moisture and thermal model. |
| `snowfall` | Deposition rate for retained snow and opacity for profile-bound [world-space flakes](world-precipitation.md). |
| `fogDensity` | Multiplier on the authored densities of local atmosphere volumes. |
| `surfaceWetness` | Optional minimum wetness for weather-masked finishes, combined with any retained wetness. |

For a numeric channel that’s absent, the matching subsystem uses its ordinary defaults. Rain tagged with `profile: true` appears in the CPU renderer when the binding provides a positive rain rate. An explicit render `wind` value overrides the profile velocity for that render.

Use [moving fronts](weather-fronts.md) to carry a named profile along a world-space route.

## Configure the binding

```js
const weatherBinding = {
  channels: { rain: 'showerRate', windX: 'coastalWind', windZ: false },
  rainFull: .6,
  windDryingSpeed: 5,
  fogVolumes: ['valley-mist'],
  surface: {
    width: 32, height: 24, cell: .25, origin: [-4, -3],
    step: .125,
    forcing: (x, z) => ({ precipitationExposure: underRoof(x, z) ? 0 : 1 })
  }
};
const world = B.finish({ cam, skyEnvironment, weatherBinding, atmosphere });
```

Map any supported channel to a name in your profiles, or set it to `false` to detach it. The mapping keys use the names above except `air` for air temperature, `wetness` for surface wetness, and `light` for daylight. `rainFull` sets the simulation rain rate that gives full visual rain opacity. `windDryingSpeed` sets the velocity at which the solver reaches its strongest wind-driven drying. Specify `fogVolumes` to choose which named volumes follow the profile.

The optional surface grid accepts [the existing surface weather settings](procedural.md#weather-and-retained-materials). Its `forcing(x, z, time, state, signal)` callback can override the uniform forcing locally with shelter, runoff, or exposure to precipitation. Fixed simulation steps start at time zero. Seeking back replays the same steps, so exported frames have the same wetness as forward playback. Use a fresh binding descriptor when editing a scene’s configuration.

To render the retained values on a material, put a weather mask on any finish layer. Select `wetness`, `snow`, or `frost`. Grids with [standing water enabled](retained-weather.md) also expose `standingWater`. Use increasing `low` and `high` values to map the retained amount to a smooth blend.

```js
const wetStone = K.surface.material(stone, { layers: {
  rainSheen: { type: 'reflection', source: 'scene', f0: .42, strength: .76,
    mask: { type: 'weather', channel: 'wetness', low: .12, high: .7 } }
} });
```

Hosts can use the source outside rendering with `K.weather.bind(skyEnvironment, weatherBinding, { profiles })`. Read it through `binding.sample(time)`, call `binding.surfaceAt(time)` for the retained snapshot, or pass `binding.forcing(local)` to a solver you advance yourself.

## Compare a render

```sh
ink-studio sheet examples/weather-courtyard.js --t 0,2.5,5.1 --raw --out weather.png
ink-studio render examples/weather-courtyard.js --t 2.5 --raw --weather-binding off --out atmospheric-sky.png
```

The [courtyard example](../examples/weather-courtyard.js) keeps sheltered paving mostly dry. Exposed stones remain wet as the clouds lift. The CPU renderer and CLI accept `--weather-binding on|off|file.json` for a per-render override. JSON descriptors can also be supplied as `finish.weatherBinding` in data-authored dioramas.

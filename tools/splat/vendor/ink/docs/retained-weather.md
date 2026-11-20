# Weather that leaves a trace

A [weather-bound](weather-binding.md) surface grid remembers wetness, snow, and frost after the weather changes. Enable `standingWater` on that grid to retain excess rain and meltwater in low areas. Pools keep the underlying stone wet, can freeze in cold conditions, and release their water again when they thaw.

```js
const weatherBinding = {
  surface: {
    width: 40, height: 30, cell: .2, origin: [-4, -3],
    capacity: .28,
    standingWater: {
      capacity: (x, z) => lowStone(x, z) ? .35 : 0,
      drainage: .045,
      evaporation: .5
    },
    forcing(x, z) {
      const exposure = K.procedural.overheadCover.exposure(cover, [x, groundY(x, z), z]);
      return { precipitationExposure: exposure, shelter: 1 - exposure };
    }
  }
};
```

The grid’s `capacity` controls the wet film. The standing-water capacity controls how much extra liquid a cell can hold. Set it to zero at high points, use a number for a uniform surface, or provide a function for sculpted basins. `drainage` is a loss rate per second and `evaporation` scales the atmosphere’s effect on pooled water relative to the wet film. The same configuration works with `K.procedural.motion.surfaceWeather` directly. Each opt-in snapshot exposes a `standingWater` grid and includes that value in `sample(x, z)`.

Use `precipitationExposure` to keep a roofed area dry. Use `shelter` to reduce incident light and snow capture. The active profile’s `daylight`, `airTemperature`, wind, and humidity control warming and drying. Puddles freeze into the retained frost field and snowmelt can refill them. The surface solver also accepts a local light override for cast shadows or a directional clock.

## Put it on a material

Use weather masks with `wetness`, `standingWater`, `snow`, or `frost`. A puddle can use a stronger reflection finish than the surrounding damp stone. Set increasing `low` and `high` values to map the local depth or amount to a smooth blend.

```js
const paving = K.surface.material(stone, { layers: {
  puddles: { type: 'reflection', source: 'scene', strength: .85, f0: .7,
    mask: { type: 'weather', channel: 'standingWater', low: .02, high: .25 } }
} });
```

Puddles appear as finish layers on the authored surface in the CPU renderer. The grid tracks the local amounts of liquid and frozen water.

## Compare a render

```sh
ink-studio sheet examples/weather-traces.js --t 2.95,5.62,7.5,9.85 --raw --out traces.png
ink-studio render examples/weather-traces.js --t 2.95 --raw --retained-weather off --out before.png
```

In [the terrace example](../examples/weather-traces.js), rain fills the basins, colder air freezes the paving and adds snow, and sunlight thaws the exposed stones first. Set `--retained-weather on|off` or pass the boolean `retainedWeather` to the renderer to compare at the same time. This toggle controls the retained grid, so the profile continues to drive airborne weather. Use a `--weather-binding file.json` override to change the storage controls for a render.

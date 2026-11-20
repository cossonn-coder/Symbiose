# Shared wind and local shelter

Add `windField` to a scene to give clouds, flexible foliage and cloth, drifting particles, and density-field smoke the same wind. Connect directional wind and gust strength to environment profiles with [weather binding](weather-binding.md). Configure cliffs, walls, or other windbreaks with a geometry query.

```js
const occluder = K.atmosphere.occluder(S.modelSource().field.sdf);
const windField = {
  velocity: [1.2, .3],
  gust: { amplitude: .24, period: 1.7 },
  shelter: { occluder, reach: 7.5, strength: .88, spread: .22, spacing: .28 },
  clouds: 1
};
const world = B.finish({ cam, skyEnvironment, weatherBinding: true, windField });
```

`windX` and `windZ` supply the horizontal velocity in scene units per second. `windGust` multiplies it, from zero for calm to three for a stronger gust. Set these channels in named profiles or [moving fronts](weather-fronts.md). Use `velocity` as a fallback and `gust` for an additional periodic variation. Its amplitude is a fraction, period is in seconds, and optional phase is in radians.

The field looks upwind from the sample height. A nearby wall or cliff cuts the wind within its wake. Wind recovers with distance over `reach`, and samples beside or above the blocker can stay exposed. `strength` sets the maximum reduction. `spread` softens the edges with side samples, and `spacing` controls the world-space sampling grid. Capture the sculpt’s field before baking to use the scene geometry as the occluder.

## Connect effects

- Clouds integrate the open-air wind over time. The coverage grid and its shadows move together. Use `clouds` to scale that displacement, or set `clouds: false` to keep the cloud field’s own velocity.
- Foliage and cloth use the local wind at their splats. Author flexibility with `K.procedural.airflow.pinned` or the sculpt’s `motionAt` callback.
- Spray and smoke particles use the existing rising motion with `{ k: 3, wind: true }`. They travel with the gust history at their launch position. World-space precipitation uses the same field.
- Shape-density smoke uses `windInfluence` on `K.procedural.density.fromSdf` to move its density pattern. The pattern’s displacement reflects the local shelter.

Hosts can use `K.procedural.airflow.field(settings, { ambient, local, gust, localGust })` to share the sampler with a simulation. `sample(x,y,z,time)` returns wind in XZ. Pass `field.xyz` to an [XPBD cloth solver](../src/kit/ks-xpbd.js) for the XYZ callback, or use `travel(x,y,z,from,to)` to integrate wind at a fixed world position.

## Compare a render

```sh
ink-studio render examples/windbreak.js --t 2.45 --raw --out lee.png
ink-studio render examples/windbreak.js --t 2.45 --raw --wind-field off --out base.png
```

Use `--wind-field on|off|file.json` or the matching renderer option. A JSON override of `{"shelter": false}` keeps the gust profile active for comparing sheltered and exposed behavior. The [windbreak example](../examples/windbreak.js) places similar flags, reeds, pools, and smoke sources on either side of a stone wall.

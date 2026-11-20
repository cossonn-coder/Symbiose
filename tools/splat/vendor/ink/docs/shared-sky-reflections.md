# Shared sky reflections

A finish can use the same directional sky as the backdrop. Water ripples, wet stone, and metal sample it along their reflected world direction. That means a changing horizon colour, moving sun, or directional accent affects both the background and its reflection at the same time.

```sh
node cli/ink-studio.js render examples/shared-sky-reflections.js --sky-time 7 --sky-reflections scene --raw --out shared.png
node cli/ink-studio.js render examples/shared-sky-reflections.js --sky-time 7 --sky-reflections material --raw --out material.png
```

## Choose a reflection source

Add `source: 'scene'` to a `reflection` layer, including the `sky` layer on the rippling-water preset. Omit the field or set `source: 'material'` to use the finish's own three-colour sky. Keep these colours if you want the shared finish to fall back gracefully in a scene without an environment.

```js
const water = K.surface.preset('rippling-water', { r: [6, 7, 8, 9] }, {
  layers: { sky: { source: 'scene', strength: 0.8 } }
});
```

Use `K.reflection.material(water, 'pool', options)` to layer a planar geometry capture over that sky. The sky shows through where the capture has no geometry. Fresnel settings, bump normals, masks, and planar distortion still apply. Set `skyReflections: 'scene' | 'material'` on the world or render options to force a source for all environment reflection layers. The CLI spelling is `--sky-reflections scene|material`.

The headless renderer supports scene sampling in perspective and orthographic views. Transparent exports retain the sky in reflective materials and keep the backdrop transparent.

## Choose the active sky

Set `world.skyEnvironment`, pass an override in the Node render options, or use `--sky-environment file.json` in the CLI. JSON dioramas accept the definition as `finish.skyEnvironment`. This is an example of a single sky profile:

```js
world.skyEnvironment = K.skyEnvironment.compile({
  defaults: {
    zenith: '#584876', horizon: '#ff996c', ground: '#353a55',
    sunColor: '#ffe2a2', sunAzimuth: 3.08, sunAltitude: 0.084, sunStrength: 1.13
  }
});
```

- `profiles` names sets of parameters. `sequences` names `{ duration, loop, keys }` clips. Keys use `{ at, profile, ease }`, begin at zero, and increase strictly before their duration. The outgoing segment uses `smooth`, `linear`, or `hold`. A looping sequence blends from its last key back to its first.
- `tracks` lists `{ id, sequence, offset, speed }` in evaluation order. Each track samples `time * speed - offset`. A later track supplies the value for shared parameters. RGB values interpolate in linear light. See the [example profile file](../examples/shared-sky-profiles.json).
- `--sky-time seconds` scrubs the sky independently of scene animation. Use `--sky-profile light=sunset` to pin a compatible profile on one track. The corresponding Node options are `skyTime` and `skyProfiles`.
- Azimuth and altitude are in radians. Azimuth starts along +Z and increases towards +X. Optional directional accents in `sky.splats` use world angles `at: [azimuth, elevation]`, and sample the same way in both views. Optional `sky.orthoFov` sets the orthographic backdrop's virtual vertical lens in degrees. A flat mirror in an orthographic shot samples a single direction until its surface normals vary.

Use [Interruptible transitions](interruptible-sky.md) to start a weather or lighting change from the currently sampled sky.

`--sky-environment off` disables the directional backdrop and restores the material colours for opted-in layers. `--sky-reflections material` leaves the directional backdrop visible during a comparison.

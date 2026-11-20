# Live sun lighting

## Relight baked color and detail

Set `finish.relighting` in a JSON diorama or `relighting` in `B.finish()`. Both renderers can change the light on baked swatches, fine detail tiles, per-pixel patterns, and edge sprites while preserving the original geometry and texture data. This mode uses the baked shadow detail as part of the surface color.

| Field | Behavior |
| --- | --- |
| `lights` | Up to 32 named point lights. Each has an XYZ `at`, `range`, hex `color`, `intensity`, optional `enabled`, and optional target `select`. Lights fall off with distance and follow the surface normal. |
| `sun` | Defaults to `"environment"`, which follows the primary celestial sun or sky profile. Supply `direction`, `color`, and `intensity` for a fixed sun. Use `false` for ambient and point lights. |
| `referenceTime` | Time in seconds for the baked daylight look, defaulting to zero. The sun's contribution is relative to that reference. Use `skyTime` to seek the daytime independently of scene motion. |
| `ambient` and `strength` | Ambient light defaults to 0.45. Strength runs from zero to one and controls how much the lighting changes the bake. |
| `select` | Limit the rig to named surfaces with the existing target selectors. |

Pass a `relighting` override to either renderer to move or recolor lights without rebaking. Light changes merge by ID, and a `null` entry removes a light for that frame. Pass `false` to disable the mode. The CLI accepts `--relighting on|off|file.json` and `--sky-time seconds`. Emissive splats keep their authored colors.

## Headless directional relighting

The Node renderer and CLI can relight sculpted objects with one directional sun at render time. A light-space depth map is rebuilt from posed opaque splats. Move the light to change illumination and cast shadows while keeping the same sculpt.

```sh
node cli/ink-studio.js render examples/live-sun.js --t 4 --raw --px 1 --out live.png
node cli/ink-studio.js render examples/live-sun.js --t 4 --live-sun off --raw --px 1 --out baked.png
node cli/ink-studio.js render examples/beacon-pool.js --live-sun --sun-direction 0.7,0.55,0.2 --out pool.png
```

For a JavaScript scene, set `S.captureAlbedo = true` before baking. Use a material's `albedo` field to author the unlit colour explicitly. The capture otherwise uses the last colour of the material's primary ramp. Direct builder dabs can supply the same information with `B.describeAlbedo(first, end, color)` and a surface normal. Older pixel-material bakes can use their existing ramps. Rows with missing lighting data keep their baked colour. CLI overrides capture albedo during the scene build.

```js
const light = {
  direction: seconds => [Math.sin(seconds), 0.72, Math.cos(seconds)],
  ambient: 0.32,
  intensity: 0.88,
  shadows: true,
  mapSize: 512,
  bias: 0.02,
  filter: 1
};

const image = ink.render(world, { t: 2, liveSun: light });
```

Set `world.liveSun` in the finished scene for a default. Per-render settings can override individual scene fields. Baked lighting is the default for other scenes. Pass `liveSun: false` or `--live-sun off` to compare the baked result. A direction is a vector from the scene towards the sun, or a function of render time in seconds. It is normalized once per frame.

| Option | CLI | Default |
| --- | --- | --- |
| `direction` | `--sun-direction x,y,z` | `[-0.52, 0.64, 0.57]` |
| `ambient` | `--sun-ambient n` | 0.32 |
| `intensity` | `--sun-intensity n` | 0.88 |
| `shadows` | `--sun-shadows off` | true |
| `mapSize` | `--shadow-map-size n` | 512, with a range of 32–2048 |
| `bias` | `--shadow-bias n` | 0.02 scene units |
| `filter` | Library option | 1 texel, with a range of 0–2 |

The map fits opaque scene splats independently of the viewing camera, so perspective and orthographic views can reuse the same authored light. Glass and outline-free particles do not cast shadows. Emissive colours keep their emission. Pixel-material renders sample their original ramps with the live light level. Raw renders use captured albedo with ambient and direct lighting. Highly specialized baked material effects may look different under live lighting. This version runs in the headless renderer.

## Art-directed shadows

Set `finish.look.shadowArt` in a JSON diorama or pass `shadowArt` in the third argument to `makeBuilder` before sculpting. The same settings guide baked lighting and headless live sun. The CLI accepts `--shadow-art file.json` for JSON bakes and live-sun renders.

| Setting | Behavior |
| --- | --- |
| `ramp` | Select evenly spaced steps of visibility and map each to a direct-light gain. Supply 2 to 16 nondecreasing gains from zero to one, ending at one for clear light. The material's own palette ramp supplies the colours. |
| `cast` | Choose which geometry casts shadows with `include` and `exclude` selector arrays. |
| `receive` | Choose which surfaces respond to those shadows, using the same mask fields. |
| `small` | Choose a `belowPixels` threshold and a `referenceSize` in world units, which defaults to one. When that span projects to fewer pixels on the camera target plane, use an optional simpler `ramp` and `strength` from zero to one. Zero strength suppresses the cast shadow. |

Masks accept object, entity, material, surface, prefab, and tag selectors. A target matches a mask if it passes any supplied include selector and no exclude selector. Include is unrestricted when omitted. Masks leave the visible geometry and ambient occlusion intact.

The CPU and WebGL renderers select the small-size variant for baked surface splats as camera scale changes. Headless live sun evaluates the same rule against its current depth map. Programmable point lights that use a cached visibility map can use the masks and regular ramp through `K.light.shadow`. Set the programmatic render option `shadowArt: false` to use the regular baked variant or the unstyled live sun.

## Sky and ground bounce

Choose extra diffuse fill from above and below in either the Node API or CLI. Each side can use a preset, a hex colour, or `off`.

```sh
node cli/ink-studio.js render examples/bounce-light.js --sky-bounce clear-sky --ground-bounce sand \
  --ground-bounce-intensity 0.55 --raw --px 1 --out sand.png
node cli/ink-studio.js render examples/bounce-light.js --sky-bounce clear-sky --ground-bounce water \
  --ground-bounce-intensity 0.55 --raw --px 1 --out water.png
```

Presets are `clear-sky`, `overcast`, `sand`, `snow`, and `water`. Quote a custom hex colour in the shell, such as `--ground-bounce '#ec885f'`. Either side defaults to intensity 0.4 when enabled, with an adjustable range of 0–4. An intensity-only override keeps the scene colour and uses clear sky or sand if that side has no authored colour. Set either choice to `off` to disable it independently.

```js
ink.render(world, {
  liveSun: {
    ambient: 0.24,
    skyBounce: { color: '#92b6ff', intensity: 0.48 },
    groundBounce: { color: 'sand', intensity: 0.32 }
  }
});
```

The same fields can live in `world.liveSun`. To animate them, supply a function of render seconds for either field. It can return a preset, a settings object, or `false`. Omit both to use the original neutral ambient light. Set `intensity: 0` on the sun to use hemisphere fill without direct sunlight.

Bounce follows each posed world normal. Upward faces receive the upper fill, undersides receive the lower fill, and vertical faces receive a mix. Bounce adds diffuse light in shadows independently of the directional shadow map. Pixel materials read their normal ramp brightness and carry the bounce tint into colour resolution. A fixed export palette limits the available tints, so use `--raw` to preview a new colour choice.

# Animated splat fields

Animated splat fields are optional world-space Gaussian splats in the headless renderer. They sort against solid geometry, appear in planar reflection captures, and support perspective and orthographic views. Emissive splats can also feed the emission pass and its art effects. Births sample a seeded clock, so scrubbing and rendering frames in parallel produce the same effect at the same time.

The [four-effect scene](../examples/animated-splat-fields.js) accepts an `effect` of `aurora`, `embers`, `dust-wall`, or `wake`.

```sh
ink-studio clip examples/animated-splat-fields.js --params '{"effect":"wake"}' --from 0 --to 4.6 --fps 10 --raw --out wake.png
ink-studio render examples/animated-splat-fields.js --splat-fields off --t 2 --raw --out clear.png
```

Use `--splat-fields on` to use the scene's authored fields, `off` to hide them, or `--splat-fields fields.json` to replace them for a render. The library equivalents are `render(world, { t, splatFields })`, where `splatFields` can be a configuration object, a compiled field, `true`, or `false`. To author fields on a world, supply the configuration as `splatFields` in `B.finish(...)` or `finish.splatFields` in a JSON diorama. Fields are enabled when authored.

## Configuration

A configuration is a `{ "fields": [...] }` object. Give each entry a unique `id`. Choose a preset to fill in the defaults, or provide the four groups directly for a custom effect. Groups override individual properties, so multiple fields can layer with their own locations, lifespans, and style.

```json
{
  "fields": [
    {
      "id": "kiln-sparks",
      "preset": "embers",
      "shape": { "at": [2, 0.5, -3], "size": [1.4, 0.2, 0.9] },
      "motion": { "velocity": [0.25, 1.2, 0], "wind": 0.8 },
      "life": { "start": -2, "end": 6, "rate": 64, "lifetime": [0.6, 1.8] },
      "style": { "size": 0.045, "endScale": 0.3, "emissive": true },
      "seed": 43
    }
  ]
}
```

| Group | Controls |
| --- | --- |
| `shape` | A `box` scatters births inside its XYZ `size`, centered on `at`. A `ribbon` scatters births along a polyline of XYZ `points`, with `height` above the route and `depth` across it. A `path` moves the source along `points` over `duration` seconds at constant speed. Use `loop` to close and repeat a path. Paths scatter births around their current source position using the same height and depth controls. For routes, `at` offsets all points. |
| `motion` | `velocity` in world units per second, `gravity` in units per second squared, and randomized `spread` in velocity per axis. Specify `wave` amplitudes per axis and `frequency` in cycles per second for coherent movement. `wind` scales advection from scene wind, gusts, and shelter where configured. |
| `life` | Births run from `start` through optional `end` at `rate` births per second. A negative start prewarms the effect. `lifetime` is a minimum and maximum age in seconds. `fadeIn` and `fadeOut` are fractions of each particle's life. Existing particles finish their lives after the final birth. |
| `style` | `color` and `endColor` are packed sRGB integers (for example, `16744448` is `0xff8000`). `size` is a standard deviation in world units, `endScale` controls growth, and `stretch` lengthens the splat along its motion or the supplied XYZ `axis`. Set `opacity` for blending and `emissive` for the emission pass. |

To sample from a host, use `K.splatFields.compile(config)`. The result exposes a fixed `count` of reusable slots. `frame(time)` returns packed native splats in a `Float32Array`, with zero alpha for inactive slots. Use `write(buffer, firstSlot, time)` to fill an existing buffer. Either method accepts `{ travel(at, birth, time) }` as its final argument to supply XZ wind displacement over a particle's lifetime. The CLI automatically uses scene wind. A field can reserve up to 4,096 slots and a scene can reserve up to 16,384 across its fields.

# Art direction

Ink’s optional art-direction profile groups four controls for the headless renderer. Choose `painted-pixel` for firmer cloud edges and stepped tones, `storm-silhouette` for hard silhouettes and held motion, or `soft-dawn` for softer edges, lighter shadows, and continuous motion. Mix any of the controls independently.

The [Estuary Watch example](../examples/art-direction-estuary.js) uses the same geometry, authored sky, and camera for all three looks.

```sh
ink-studio render examples/art-direction-estuary.js --art-direction storm-silhouette --t 2 --px 1 --out storm.png
ink-studio clip examples/art-direction-estuary.js --art-direction soft-dawn --from 0 --to 4 --fps 24 --px 1 --out dawn.png
```

Set `look.artDirection` on the world, `finish.look.artDirection` in a diorama, or `visual.look.artDirection` in a simulation world. Use `--art-direction on|off|painted-pixel|storm-silhouette|soft-dawn|file.json` to select a preset, publish a custom profile, or toggle the authored choice. The library accepts the same settings through `render(world, { artDirection })`. The optical controls also work in raw renders.

```json
{
  "preset": "painted-pixel",
  "cloudEdge": 0.85,
  "atmosphereBands": 5,
  "foreground": { "contrast": 1.6, "pivot": 0.57, "near": 8, "far": 24 },
  "cadence": { "scene": 12, "environment": 6 }
}
```

- `cloudEdge` runs from 0 for softer coverage to 1 for a harder edge. Use 0.5 for the authored cloud coverage. It affects sheets, cloud volumes, and cloud impostors, including their sky reflections.
- `atmosphereBands` sets 2–64 evenly spaced levels in the sky gradient and optical fog or aerial-perspective coverage. Use 0 for continuous shading. Celestial disks, cloud coverage, and water absorption retain their own controls.
- `foreground` adjusts the contrast of visible nearby surfaces around the `pivot` luminance. A contrast above 1 darkens shadows and brightens highlights. A contrast below 1 compresses that range. The adjustment is full through `near` world units of camera depth and fades to zero at `far`. Emissive details retain their colors. Use `foreground: false` to bypass the preset’s contrast.
- `cadence.scene` and `cadence.environment` hold the respective animation clocks at the given frames per second. Use 0 for a continuous clock. The environment clock follows sky profiles and their associated effects. The view still samples the authored camera on every output frame.

`ArtDirection.prepare(config)` and `ArtDirection.time(prepared, seconds, channel)` are available from the library. Ink’s CLI poses animated dioramas at the held scene time. Hosts that manage their own stage updates can sample their stage at the same held time and pass the original time to the renderer. Simulation snapshots keep their requested tick.

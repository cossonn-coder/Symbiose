# Environment inspection

Use the headless environment inspector to explain the sky and local weather for a scene, world manifest, checkpoint, or recording. It uses the same sampling path as the renderer and reports JSON.

```sh
ink-studio environment inspect examples/weather-front.js --t 4.4 --at 0,1,0 --out front.json
ink-studio environment inspect examples/world-conditional-weather.json \
  --asset-pack examples/coastal-environment-pack.json --t 3.5 --at 2.55,.6,2.38 --out station.json
```

`--at` is a world XYZ position. `--t` sets scene seconds. A simulation samples the committed tick at or before that time. The report gives the requested time, sampled tick, motion time, and sky time. `--sky-time` scrubs the environment clock independently. Use `--json` for compact output, and omit `--out` to print to standard output.

The report includes these sections.

- **Sky.** The pack ID and revision appear alongside sampled defaults, track order, key times and profile IDs, easing weights, and channel values. `sky.source` identifies the winning track or transition for each channel. A pinned track shows its selected profile. An interrupt shows its trigger, destination, and captured starting values, including the key pair or prior transition that supplied them.
- **Local weather.** Global values precede the regional stack. Every enabled front lists its route keys, current center, influence weight at XZ, and each channel’s value before and after its contribution. The report also shows effective local weather and retained surface state.
- **Regional modifiers.** Exposure zones and volume cutouts report their gains at XYZ. Wind reports open and local velocity and, when configured, the regional velocity, gust, geometric shelter, and exposure factors.
- **Lighting and fog.** Celestial key weights, resolved sky and sun, point cloud coverage and shadow visibility, lightning contribution, aerial settings, and each authored volume’s weather density scale describe the inputs to the frame.

Use the ordinary render choices to isolate an effect. For example, `--sky-profile light=dusk` pins a track and `--weather-fronts off` samples the global profile at the same position. `--weather-tracks off` uses the authored schedule. The Node equivalent is `ink.inspectEnvironment(world, { t, at: [x, y, z] })`.

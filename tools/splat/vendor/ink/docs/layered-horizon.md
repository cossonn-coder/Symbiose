# Layered horizon art

Paint a distant vista with transparent RGBA artwork on concentric cylinders. Large radii give distant peaks little positional parallax. Use smaller radii for foothills, treelines, and other nearer bands. The art composites over the directional sky and behind the world, including close splat effects and atmosphere. Perspective views use the scene lens. Orthographic views use the sky lens and the nominal camera position.

The [Waystation above the pine line example](../examples/layered-horizon.js) layers snow peaks, foothills, and a repeating pine bank behind a sculpted lookout.

```sh
ink-studio clip examples/layered-horizon.js --w 224 --h 140 --px 1 --raw --from 0 --to 3 --camera-orbit 42 --out orbit.png
ink-studio render examples/layered-horizon.js --horizon-bands off --out baseline.png
ink-studio render examples/layered-horizon.js --horizon-bands vista.json --out vista.png
```

A separate profile can reference PNGs beside its JSON file. Use alpha to draw irregular skylines and leave gaps between shapes.

```json
{
  "origin": [0, 0, 0],
  "camera": {
    "yaw": [-55, 65],
    "pitch": [-12, 22],
    "distance": [6, 20],
    "fade": { "yaw": 12, "pitch": 4, "distance": 2 }
  },
  "bands": [
    { "id": "peaks", "radius": 105, "height": [-25, 24], "azimuth": [105, 270], "image": "peaks.png" },
    { "id": "pine-bank", "radius": 28, "height": [-7, 3], "azimuth": [120, 250], "image": "pines.png", "repeat": 4 }
  ]
}
```

- **Camera window.** The yaw and pitch ranges are required and use degrees. Distance is the nominal eye-to-target distance in world units. Use increasing yaw bounds such as `[325, 395]` to cross zero, or `[0, 360]` for a full orbit. Optional fade widths soften the window from the inside. Full-turn yaw has no fade.
- **Band placement.** The origin anchors the artwork in the world. Each radius and height range uses world units, with height measured relative to the origin. Put each shell beyond the foreground it depicts and leave the camera inside the smallest radius. The outer tenth of each radius fades the band as the eye approaches the cylinder.
- **Repeats.** Azimuth starts along world +Z and turns toward +X. The texture runs left to right as azimuth increases. The default is a full turn. `repeat` divides the authored arc into that many copies. Paint matching horizontal texture edges for continuous tiling.
- **Compositing.** Bands draw far to near by radius using the image alpha and optional `opacity`. At the same radius, later entries draw on top. Bands are backdrop art. Use scene geometry or a depth-aware impostor for scenery that needs to intersect the foreground, cast shadows, or appear in reflections. Transparent sprite exports omit the backdrop.
- **Sky transitions.** Set `gain` to a numeric sky-profile channel to animate opacity, or `tint` to a colour channel to multiply the paint. Shared sky sequences interpolate these channels. A render without a sky environment uses full gain and a white tint.

Use `look.horizonBands` in the library, `finish.look.horizonBands` in a JSON diorama, or `visual.look.horizonBands` in a simulation. Embed pixels in data as `image: { width, height, pixels }` with top-down straight RGBA bytes in row order. JavaScript scenes can use `Uint8Array` or `Uint8ClampedArray`. The renderer accepts a config or compiled profile via `render(world, { horizonBands })`. Compile once with `ink.load().HorizonBands.compile(config, { readImage })`, or use `ink.readHorizonBands('vista.json')` to decode a PNG-based profile in Node. Use `--horizon-bands on|off|file.json` to choose a profile for a CLI render. With no authored or supplied profile, the horizon option is off.

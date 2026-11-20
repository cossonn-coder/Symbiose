# Celestial tracks

Celestial tracks add independent paths for suns, moons, stars, and eclipses to Ink’s headless renderer. Bodies are angular disks at infinity and share the sky clock with environment profiles. Camera rotation changes where they appear. Camera translation leaves their directions fixed. Clouds and scene geometry can occlude them, and scene-sky reflections sample the same disks.

The [Estuary Watch example](../examples/celestial-estuary.js) holds an oversized sun at the horizon, crosses it with a moon, and brings up two moons and a drifting star field at dusk.

```sh
ink-studio clip examples/celestial-estuary.js --from 0 --to 9 --fps 12 --raw --out estuary.png
ink-studio render examples/celestial-estuary.js --t 3.18 --celestial-tracks off --raw --out clear.png
```

Use `--celestial-tracks on` for the scene setting, `off` to hide the tracks, or `--celestial-tracks file.json` to replace them for the render. The library accepts the same choices through `render(world, { celestialTracks })`, using booleans, a config object, or a compiled track set. Set `celestialTracks` on the world or use `finish.celestialTracks` in a JSON diorama. Tracks are active when authored. Sky profiles remain separately configurable. Use `--sky-time` to seek or freeze both sky profiles and celestial tracks for a shot.

## Authoring paths

```json
{
  "primarySun": "west",
  "bodies": [
    {
      "id": "west",
      "kind": "sun",
      "radius": 0.07,
      "color": "#ffd69a",
      "glow": 0.45,
      "keys": [
        { "at": 0, "azimuth": 2.96, "elevation": 0.04, "ease": "hold" },
        { "at": 5, "azimuth": 2.96, "elevation": 0.04 },
        { "at": 8, "azimuth": 2.82, "elevation": -0.12 }
      ]
    },
    {
      "id": "transit",
      "kind": "eclipse",
      "target": "west",
      "radius": 0.055,
      "start": 1,
      "end": 5,
      "keys": [
        { "at": 1, "azimuth": 3.2, "elevation": 0.08 },
        { "at": 3, "azimuth": 2.96, "elevation": 0.04 },
        { "at": 5, "azimuth": 2.76, "elevation": 0.02 }
      ]
    }
  ]
}
```

- Give each body a unique `id` and choose `sun`, `moon`, `star`, or `eclipse` for `kind`. Add multiple bodies of any kind. `distance` orders overlapping disks, farthest first. Defaults put stars behind suns and moons in front. Equal distances follow authoring order.
- Each key specifies `at` in seconds and `azimuth` and `elevation` in radians. Zero azimuth points along +Z. π/2 points along +X. Set `ease` to `linear`, `smooth`, or `hold` for the outgoing interval. Keys clamp at both ends by default. Set a `period` in seconds to repeat the path. If the final key arrives before the end of the period, Ink uses the remaining time to return to the first key. Set `azimuthMode: "unwrapped"` for a long sweep, such as 0 to 2π over one period.
- `radius` is the disk’s angular radius in radians. `softness` is the fraction of the radius used for the soft edge. Use `opacity`, `color`, `glow`, and `glowRadius` for the silhouette and halo. Keys can override `radius`, `opacity`, and `phase`. Use `start` and `end` to bound visibility, with `end` excluded.
- A moon’s signed `phase` sets the lit fraction and which side is lit. `0` is dark, ±0.5 is half, and ±1 is full. `roll` rotates the terminator. Set `darkColor` and `darkOpacity` to art-direct the unlit side.
- An eclipse masks the named sun or moon. Set `radius` smaller than the target for a ring at alignment. The target’s authored halo remains visible. Add a dark moon track with the same keys when the crossing body should also appear as a silhouette.
- An authored sun takes over the default sky disk. The optional `primarySun` binds a named sun to atmospheric glow, cloud light direction, and any enabled live or volume sun. Its opacity and approximate visible disk area scale the direct live and volume light through eclipses and horizon crossings. Ambient, bounce, and authored lights retain their settings.

From the library, call `K.celestialTracks.compile(config).frame(time)`. A frame exposes `body(id)` for a body’s direction, angular radius, opacity, and phase, and `shade(ray, rgb)` to composite its disks into an existing RGB sample. Pass the frame to `K.skyEnvironment.withCelestials(sky, frame)` to combine it with a sampled sky profile.

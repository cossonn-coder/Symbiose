# Atmosphere emitters

Attach smoke, steam, spray, or fog to a scene socket through `K.atmosphere.emitters`. Each birth takes the position and direction of the socket at that instant. Released particles age and move through world space. A train can leave smoke along its route while its stack keeps moving. All four presets use the same socket, timing, and motion controls.

The [Alder Gorge railway example](../examples/atmosphere-railway.js) uses a rigged train stack, a waterfall lip and splash zone, a lantern vent, and a strip of river mist.

```sh
ink-studio clip examples/atmosphere-railway.js --from 0 --to 6 --fps 8 --raw --out alder-gorge.png
ink-studio render examples/atmosphere-railway.js --t 3 --atmosphere-emitters off --raw --out clear.png
```

Use `--atmosphere-emitters on` to show the scene's emitters, `off` to hide them, or `--atmosphere-emitters file.json` to replace the set for a render. The library accepts the same choices through `render(world, { atmosphereEmitters })` as booleans, a config object, or a compiled set. `--atmosphere off` removes the volume rendering while preserving socket-born droplets.

## Authoring an emitter

Provide `atmosphereEmitters` in `B.finish(...)`, in `finish.atmosphereEmitters` for a JSON diorama, or in `visual.atmosphereEmitters` for a simulation world.

```json
{
  "sockets": {
    "waterfall-lip": { "p": [3.5, 2.3, -4], "dir": [0, 0.3, 1] }
  },
  "emitters": [
    {
      "id": "lip-spray",
      "preset": "spray",
      "socket": "waterfall-lip",
      "motion": { "speed": 2.2, "sourceRadius": 0.7, "wind": 0.2 },
      "life": { "start": -1, "rate": 96, "lifetime": [0.4, 1] },
      "style": { "color": "#c9eeef", "size": 0.03 }
    }
  ]
}
```

- A named socket in `sockets` can be a fixed `{ p, dir }` in world space, or `{ keys: [{ at, p, dir }, ...] }` with increasing times in seconds. In JavaScript it can also be a function of time that returns a pose or `null` while unavailable. Keyed and function sources can be sampled directly at any birth time.
- A name outside `sockets` can refer to an existing stage socket registered with `stage.socket(name, position, part, direction)`. The stage records relevant poses as it advances. For a library override, register the replacement with `stage.trackAtmosphere(compiled)` before advancing. The CLI does this when it builds the scene. Births on tracked sockets begin when their history starts.
- For a simulation entity socket, set `"socket": { "entity": "train", "socket": "stack", "dir": [0, 1, 0] }`. The direction is local to the entity. The simulation CLI records the needed transforms while advancing to the render tick. A runtime host can supply the same history through `world.atmospherePose(target, time)`. A single snapshot can resolve the current transform through its world query.
- `motion` sets axial launch `speed`, velocity `spread`, the spawn disk’s `sourceRadius`, world-space `drift` and `gravity`, and `wind` influence. Wind uses the same scene airflow as Ink’s splat fields. Configure simulation airflow under `visual.windField`.
- `life` sets `start`, optional `end`, `rate` in births per second, and `lifetime` as minimum and maximum age in seconds. `fadeIn` and `fadeOut` are fractions of a particle’s lifespan. A negative start prewarms fixed and seekable sockets.
- `style` sets `color` as hex, `size` in world units, `growth` as a size multiplier at the end of life, and optional `emissive`. Volumes use `density`, `breakup`, `lit`, `anisotropy`, and ray-march `step`. Splats use `opacity` and `stretch`. Set `representation` to `volume` or `splat` to override the preset’s rendering method.

Smoke, steam, and fog use bounded density by default. They respect occlusion, local volume lighting, and volume cutouts. Spray defaults to world-space Gaussian droplets, which sort against geometry and can appear in planar captures. Emitted density uses the emitter’s own settings. Weather fog strength continues to control the scene fog.

Library hosts can call `K.atmosphere.emitters.compile(config).frame(time, { socket, travel })`. The optional `socket(target, birth)` resolver returns `{ p, dir }` for an external socket. `travel(origin, birth, time)` supplies XZ wind displacement. The result provides `volumes`, `count` reserved native splat rows, and `write(buffer, firstSlot)` for a packed `Float32Array`.

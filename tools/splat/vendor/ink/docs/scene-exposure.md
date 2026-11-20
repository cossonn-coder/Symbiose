# Indoor and outdoor exposure

Use `K.weather.exposure({ zones })` to mark spaces sheltered from outdoor weather. Pass the compiled exposure or its descriptor to `B.finish({ sceneExposure })`. In a JSON diorama, put the descriptor under `finish.sceneExposure`.

```js
const sceneExposure = K.weather.exposure({
  zones: [{
    min: [-0.02, -1.5, -2.02],
    max: [6.81, 4.29, 2.02],
    fade: 1.26,
    rain: 0,
    fog: 0.04,
    light: 0.22,
    wind: 0.06
  }]
});
return B.finish({ ...sceneSettings, sceneExposure });
```

Sketch each enclosure with one or more world-space boxes. Put the face at the doorway or roof edge where rain should stop. Extend the box past the floor and walls wherever those faces should be fully sheltered. `fade` is the distance inward from a box face over which fog, light and wind ease from full exposure to their authored values. Use 0 for a sharp boundary. Overlapping boxes use the lowest gain at the sampled point.

| Setting | Effect | Default |
| --- | --- | --- |
| `fade` | Transition width in world units | 1 |
| `rain` | Precipitation and rain contacts inside the box. At 0, a drop that enters the zone stops for that flight. Values above 0 allow partial precipitation. World-space snow can use the same control. | 0 |
| `fog` | Atmospheric density. The renderer accumulates fog along the view ray, so a clear passage can still look into outdoor mist. | 0.12 |
| `light` | Outdoor light and scene-sky reflection strength. Live sun retains its ambient level. Baked surfaces retain a small ambient floor, and authored emissive splats, local volume lights, and runtime lanterns can still light the interior. | 0.25 |
| `wind` | Local airflow. Wind-driven foliage, cloth, and smoke can settle inside while cloud movement continues outdoors. | 0.08 |

All channel gains range from 0 through 1. Use 1 to leave a channel at full exposure. Precipitation can still use geometry occlusion along with authored exposure. The field is independent of the camera and sky profile, so the same passages work while the weather changes.

Library consumers can query `sceneExposure.sample(x, y, z)` for all four gains. To sample airflow for simulation, use `K.procedural.airflow.field(settings, { exposure: sceneExposure })`. The same exposure gain applies to sampled velocity, accumulated travel and volume advection.

The headless renderer accepts `sceneExposure: false` to disable the field or a descriptor to replace it. The CLI accepts `--scene-exposure on|off|file.json`. Compare the open-ended [stone gate](../examples/sheltered-arch.js) with the camera inside and looking out through the far arch.

```sh
ink-studio render examples/sheltered-arch.js --t 2.6 --target 7.3,1.59,0.04 --raw --out sheltered.png
ink-studio render examples/sheltered-arch.js --t 2.6 --target 7.3,1.59,0.04 --scene-exposure off --raw --out open.png
```

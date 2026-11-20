# Local lights in fog

Add `spots` to a scene’s `volumeLighting` to aim a beam through bounded mist. Add `points` for omnidirectional sources such as pier lanterns. Both arrays can contribute to the same volume along with the existing `point` and `sun` settings.

```js
const volumeLighting = {
  ambient: .25,
  spots: [{
    at: [-5, 5, 0],
    direction: t => [1, -.07, .2 * Math.sin(t)],
    innerAngle: 6,
    outerAngle: 12,
    radius: 20,
    color: '#ffe0a3',
    intensity: 7
  }],
  points: [
    { at: [0, 1.6, 1], radius: 2.5, color: '#ffae63', intensity: 4 },
    { at: [2, 1.6, 1], radius: 2.5, color: '#ffae63', intensity: 4 }
  ],
  shadow: K.atmosphere.occluder(S.modelSource().field.sdf, { steps: 48 })
};
```

`at` is a world-space XYZ position and `direction` points from the source into the scene. Both can be functions of scene time, as can `intensity`. Ink evaluates them when it prepares the lighting for a frame. Cone angles are measured from the axis in degrees. The core keeps full angular intensity through `innerAngle`, then fades to zero at `outerAngle`. Set the angles equal for a hard edge. Point lights and spots fade with distance up to their world-space `radius`.

Put one or more lit [bounded density fields](scene-optics.md#bounded-density-and-lit-volumes) in the scene’s `atmosphere`. The CPU renderer adds local scattering while keeping fog density and transmittance independent. It skips temporal accumulation for animated local lights to keep a moving beam sharp.

Capture the sculpt’s field before baking to use its geometry as an occluder, as shown above. The shared `shadow` query checks the segment from each fog sample toward the light and stops at the emitter. Set `castsShadow: false` on an individual lamp to let that light pass through blockers. Place emitters in open space or use a ghost for the glowing mesh.

## Compare a render

```sh
ink-studio render examples/lighthouse-mist.js --t 2.8 --raw --out lighthouse.png
ink-studio render examples/lighthouse-mist.js --t 2.8 --raw --volume-local-shadows off --out unoccluded.png
ink-studio render examples/lighthouse-mist.js --t 2.8 --raw --volume-local-lights off --out ambient.png
```

In the [lighthouse scene](../examples/lighthouse-mist.js), the pilot hut cuts through the rotating beam and three warm lanterns light the low mist over the pier. Both CLI options accept `on` or `off`. In `ink.render`, use `volumeLocalLights` and `volumeLocalShadows` as booleans. The toggles leave directional lighting and its shadow query available.

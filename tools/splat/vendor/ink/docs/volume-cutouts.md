# Volume cutouts

Put a clear pocket inside fog or cloud density. The authored shape is the core. The feather grows outward from that core and brings the surrounding density back smoothly. Cutouts work with local fog, [shaped atmosphere](geometry-shaped-atmosphere.md), and cloud fields including their [card, impostor, and volume views](cloud-representations.md).

```js
const route = K.anim.path([[-1.7, 0.5, 6], [0.3, 0.5, 0.2], [0, 0.5, -3]]);
const volumeCutouts = K.atmosphere.cutouts({
  zones: [
    { type: 'path', path: route, radius: 0.8, aspect: 0.7, feather: 0.5 },
    { type: 'box', min: [-1.2, 0, -3.1], max: [1.2, 2.1, -2.2], feather: 0.4 },
    { type: 'sphere', at: time => facePositionAt(time), radius: 0.7, feather: 0.4 }
  ]
});
return B.finish({ ...sceneSettings, volumeCutouts });
```

| Shape | Use |
| --- | --- |
| `path` | Follow an Ink spline or terrain route. Provide `path` or a list of XYZ `points`. Set `radius` to a number or a start/end pair, and `aspect` for the vertical radius multiplier. |
| `box` | Clear a doorway or interior using `min` and `max` world XYZ corners. |
| `sphere` | Clear a face or other point of interest. Supply an XYZ position in `at`, or a function of scene time that returns the current world position. |
| `sdf` | Reuse a signed-distance function or sculpt field. Supply `bounds` and `field`. Negative distances define the clear core. The function receives X, Y, Z, and scene time. |

Each zone accepts a nonnegative `feather` width (default 0.32), `retain` from 0 to 1 (default 0, fully clear), and `affects` set to `fog`, `cloud`, or `both` (default). Overlapping cutouts use the lowest retained density. Shelter from [scene exposure](scene-exposure.md) and the cutout multiply where they overlap. Cloud cutouts are applied at render time so a moving pocket does not require rebaking an impostor. Projected cloud shadows use the cutout along the existing cloud height or layer.

Use `volumeCutouts: false` in render options to compare the same view without cutouts. The CLI accepts `--volume-cutouts on|off|file.json`. A JSON file can use static spheres, boxes, and XYZ path points. Put the same descriptor under `finish.volumeCutouts` to author it in a JSON diorama.

The [mist gate](../examples/volume-cutout-gate.js) clears the curved route, entrance, interior, and a moving guide's face.

```sh
ink-studio render examples/volume-cutout-gate.js --raw --t 1.4 --out clear-passage.png
ink-studio render examples/volume-cutout-gate.js --raw --t 1.4 --volume-cutouts off --out misted-passage.png
```

# Cloud recipes

Choose a recipe when you want a procedural cloud field that you can art-direct and reuse. Ink builds a deterministic world-space coverage grid from the seed and recipe settings. The headless renderer uses that field for the sky, scene-sky reflections, and optional [moving cloud shadows](cloud-shadows.md).

| Recipe | Shape |
| --- | --- |
| `cirrus` | High, thin streaks with curved filaments. |
| `coastal-stratus` | Low sheets with a soft underside and breaks along the band. |
| `cumulus` | Rounded clusters with thick cores and fragmented edges. |
| `storm-front` | A dark, elongated shelf with an irregular leading edge. |

```js
const cloudField = K.clouds.recipe('storm-front', {
  seed: 29,
  shape: { scale: 26, stretch: 2.8, heading: 0.36, center: [-9, -24] },
  coverage: 0.67,
  height: 11,
  thickness: 7.5,
  edgeBreakup: 0.65,
  velocity: [1.2, 0.2],
  color: '#29334e',
  lighting: { color: '#acadb9', ambient: 0.12, strength: 0.55, rim: 0.25 }
});
return B.finish({ ...sceneSettings, cloudField, cloudShadows: true });
```

A scene can use a recipe name as `cloudField`, or put the settings above in `finish.cloudField` with a `recipe` key. Use `K.clouds.recipe(name, options)` to compile once when rendering many frames. `K.clouds.recipes` lists the names.

- `shape.scale` is the size of the cloud structures in world units. `stretch` lengthens them along the heading. Heading is in radians from +X towards +Z, and `center` anchors the pattern in world XZ.
- `coverage` controls how much of the pattern becomes cloud. Set it to 0 for clear air. `edgeBreakup` controls the amount of detail near cloud boundaries. Both range from 0 to 1.
- `height` sets the layer's world Y and the shadow projection height. `thickness` adds a vertical volume around that height. Set it to 0 for a single plane. Volume lighting uses density along the view ray, including when the camera is inside the cloud layer.
- `velocity` specifies drift in XZ units per second. Any displacement from the shared wind field adds to recipe drift. `--sky-time` changes the sampled time.
- `color` is the shaded cloud color and `opacity` controls its blend into the sky. `lighting.color` sets the lit color. `ambient`, `strength`, and `rim` range from 0 to 1. Lighting follows the scene's sun direction by default. Supply `lighting.direction` for an explicit XYZ direction or `lighting: false` for unlit clouds.
- `bounds` limit the XZ footprint. The pattern tapers into the outer margin. Use `repeat: true` to tile the field with filtered edges. `resolution` sets the coverage grid from 2 to 256 samples per axis. Thicker layers use `steps` ray samples from 2 to 32, with 12 for thin decks, 28 for cumulus, and 20 for storm fronts.
- `visible: false` keeps cloud shadows while hiding the cloud in the sky and its reflections. Set `cloudField: false` or use `--cloud-field off` to disable the field for a render.

Compare the recipes over the same [coast](../examples/cloud-recipe-coast.js). The CLI also accepts a JSON file with the recipe descriptor.

```sh
ink-studio render examples/cloud-recipe-coast.js --cloud-field cirrus --raw --out cirrus.png
ink-studio render examples/cloud-recipe-coast.js --cloud-field storm-front --raw --out storm.png
ink-studio render examples/cloud-recipe-coast.js --cloud-field my-clouds.json --raw --out custom.png
```

Use [cloud assets and distance transitions](cloud-representations.md) when a bounded recipe needs a distant card, a directional impostor, and an enterable volume.

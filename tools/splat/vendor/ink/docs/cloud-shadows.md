# Moving cloud shadows

A cloud field is a low-resolution coverage grid on a horizontal plane in 3D. Its wind moves the grid over time. Ink uses the same grid to draw the clouds, sample them in scene-sky reflections, and project their shadows onto splats, local fog, and water. Softer shadows spread the coverage before projection while preserving the visible cloud shape.

Compare the [Cloud pass example](../examples/cloud-shadows.js) at the same instant with and without clouds blocking the light.

```sh
ink-studio render examples/cloud-shadows.js --t 1.5 --raw --cloud-shadows off --out clear.png
ink-studio render examples/cloud-shadows.js --t 1.5 --raw --cloud-shadows on --out shadow.png
ink-studio render examples/cloud-shadows.js --t 1.5 --raw --cloud-shadow-softness 1.2 --out soft.png
```

## Authoring a field

Use [cloud recipes](cloud-recipes.md) for configurable cirrus, coastal stratus, cumulus, and storm fronts.

```js
const cloudField = K.clouds.compile({
  bounds: { min: [-12, -18], max: [12, 6] },
  resolution: [32, 32],
  coverage: (x, z) => K.clamp(1.35 - Math.hypot((x + 2) / 4, (z + 7) / 6), 0, 1),
  height: 6,
  velocity: [1.8, -.3],
  color: '#eee7dd',
  opacity: .85
});
const world = B.finish({
  cam,
  cloudField,
  cloudShadows: { strength: .8, softness: .6 }
});
```

Bounds and velocity use world XZ coordinates. Height is world Y and velocity is scene units per second. Coverage ranges from zero for clear sky to one for full cloud. Data-authored dioramas can put the same fields under `finish.cloudField` and supply coverage as a row-major array with X varying fastest. Pass a standalone grid as JSON with `--cloud-field clouds.json`. Compiling a grid once lets repeated renders reuse the filtered coverage. Grids support two to 256 samples per axis, with 48 per axis by default.

Use `repeat: true` to tile the coverage in both axes, or leave a margin around bounded clouds to give their shadows room to soften. Use `visible: false` for shadow-only fields. `color` and `opacity` control how the clouds appear in the sky and its reflections. `--cloud-field off` removes the field for a render.

## Lighting controls

- Set `cloudShadows: true` to opt in, or use `--cloud-shadows on` for a single render. Use `--cloud-shadows off` to compare while keeping the clouds visible.
- `strength` is the maximum fraction of directional light the cloud can block, from 0 to 1. The default is 0.72. Override it with `--cloud-shadow-strength`.
- `softness` is the Gaussian standard deviation in scene units. The default is 0.7. Set it to 0 for the grid's native filtered edge. Override it with `--cloud-shadow-softness`.
- The direction toward the light comes from `cloudShadows.direction`, the live sun, the active sky, the volume sun, or Ink’s default sun direction, in that order. Receivers below the cloud plane can be shaded when the light is above the horizon.
- Put `cloudShadowStrength` and `cloudShadowSoftness` in [sky profiles](shared-sky-reflections.md) to animate them through a day-night cycle. Enable shadows with `cloudShadows: true` to use the profile values. Explicit scene and render settings override those values. The grid uses `--sky-time` when supplied and scene time otherwise.

Relightable surfaces and lit fog with a directional light lose its direct contribution under cloud cover. Ambient and local lights still contribute. Baked surfaces, simple fog and water tint use a softer brightness multiplier. Fog and water keep their authored density and extinction. Emissive splats and volume emission retain their source intensity. This pass is available in the CPU renderer and CLI in perspective and orthographic views.

The coarse directional shadow map is inspired by the approach in [Epic’s Volumetric Cloud documentation](https://dev.epicgames.com/documentation/unreal-engine/volumetric-cloud-component-in-unreal-engine).

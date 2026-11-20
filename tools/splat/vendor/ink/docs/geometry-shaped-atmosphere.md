# Clouds and fog shaped by geometry

Use a path, signed-distance shape, or terrain sampler to define the space that fog, smoke, or cloud can occupy. The same bounded density works with Ink's field-volume renderer and its [cloud asset](cloud-representations.md) system.

## A river of mist along a path

```js
const route = K.anim.path([[-3, 0.2, 6], [0, 0.2, 0], [3, 0.2, -8]]);
const river = K.atmosphere.shaped({
  id: 'river-mist',
  source: { type: 'path', path: route, radius: [1.1, 0.7], aspect: 0.35, feather: 0.25 },
  step: 0.16, density: 1.2, color: '#d8e9e4', lit: false
});
```

`path` accepts an Ink spline or a procedural terrain route. Use `points` instead for an XYZ polyline in JSON. The ribbon surrounds the route in world space. `radius` is the horizontal radius, either constant or tapered from start to end by distance traveled. `aspect` multiplies the radius on the vertical axis. A small aspect keeps the mist low over the river.

## A sculpted smoke plume

```js
// plume is an unbaked sculpt made of overlapping shapes.
const smoke = K.procedural.density.fromSdf({
  field: plume.modelSource().field,
  bounds: { min: [2, 3, -8], max: [5, 7, -5] },
  feather: 0.2
});
const cloudField = K.clouds.asset({
  field: smoke, density: 2.2, bakeTime: 0,
  densityResolution: [40, 52, 36], color: '#6d7988'
});
```

Any bounded density can supply `cloudField.field`. A serializable path or terrain descriptor also works in this slot. The cloud bakes a 3D snapshot at `bakeTime`. Its card, directional impostor, enterable volume, and projected coverage all use that snapshot. Adjust `densityResolution` to keep fine shapes in the bake. The field supplies the cloud bounds and altitude. You can still animate placement with `velocity` and the shared wind field, or change lighting across the day.

For a live shape, use `K.atmosphere.shaped({ source: { type: 'sdf', bounds, field }, ...optics })` or pass `smoke` as the bounded source. The fog renderer samples the field at scene time. The SDF uses negative values inside its shape and may come from an unbaked sculpt or any XYZ distance function.

## Fog trapped in a ravine

```js
const ravine = K.atmosphere.shaped({
  id: 'ravine',
  source: {
    type: 'terrain',
    bounds: { min: [-7, -0.5, -21], max: [7, 1.1, 9] },
    terrain: terrainFrame.heightAt, depth: 2.6, ceiling: 1.0, feather: 0.36
  },
  color: '#bad9e7', density: 0.9, step: 0.2, lit: false
});
return B.finish({ ...sceneSettings, shapedAtmosphere: [river, ravine], cloudField });
```

`depth` sets the maximum height above the ground. `ceiling` limits the world-space elevation, so the fog pools in low places and clears above that level. Pass a height callback, an object exposing `heightAt` or `sample`, or a JSON grid with `resolution: [width, rows]` and row-major `values` with X varying fastest. Grid samples include the endpoints of the XZ extent. The grid may provide its own XZ bounds, or it can use the footprint of the XYZ volume. A terrain sampler can return a number or a watershed record with `terrainHeight`.

`K.procedural.density.fromPath` and `fromTerrain` expose the bounded density without render settings. All three sources accept edge `feather` and the existing density `noise`, `breakup`, `drift`, and `windInfluence` controls in JavaScript.

## Enable and compare

Put effect descriptors in `finish.shapedAtmosphere` in a JSON diorama. Use `--shaped-atmosphere on|off|file.json` to enable authored effects, disable them, or supply a replacement JSON array. With the switch off, ordinary fog still renders. Disable shaped clouds separately with `--cloud-field off`. Both options use the headless renderer and its existing depth, local lighting, and volume controls.

The [ravine crossing](../examples/shaped-mist-ravine.js) includes all three shapes. Use `--params` to inspect any one.

```sh
ink-studio render examples/shaped-mist-ravine.js --params '{"effect":"river"}' --raw --out river.png
ink-studio render examples/shaped-mist-ravine.js --params '{"effect":"plume"}' --raw --out plume.png
ink-studio render examples/shaped-mist-ravine.js --params '{"effect":"ravine"}' --raw --out ravine.png
```

# Depth-map import

```sh
node cli/ink-studio.js depth depth.png --image concept.png --out-dir studio/out/relief
```

The command writes `preview.png`, `splats.json`, `mesh.obj` and `sdf.json`. The colour image is optional and must align pixel-for-pixel with the depth map. The preview keeps the projected RGB by default. Use `--palette` to render through the scene palette or `--relight` to shade the projected colour using surface normals.

Use the CLI preview for the original CPU-rendered export. The imported world can also be drawn by the [WebGL canvas renderer](browser-renderer.md) after restoring its packed splat buffer.

## Depth and camera

- **Grayscale PNG** supports 8-bit or 16-bit depth. By default black maps to 1 world unit from the camera and white maps to 2. Set `--near` and `--far` to change the interval, and use `--white-near` for the opposite convention. For raw measurements such as millimetres, use `--depth-scale 0.001` instead. `--depth-offset` adds a constant after scaling.
- **Numeric JSON** supplies `width`, `height`, and a flat row-major `depth` array. Values are camera-space depth. An optional `camera` object sets the projection and calibration. Null and nonpositive scaled values create empty space. `--invalid` picks an additional raw numeric sentinel, useful for zero-filled PNG backgrounds.
- **Orthographic projection** makes a relief with parallel rays. `--world-height 2` sets how many scene units the full raster height represents.
- **Perspective projection** uses `--projection perspective`. Supply `--fx`, `--fy`, `--cx` and `--cy` in pixels when you know the camera intrinsics, or set the vertical `--fov` in degrees. The calibrated coordinates are in camera space with X right, Y up, Z negative in front of the camera. The preview camera automatically frames the result for inspection. Use the source calibration when reprojecting the export into its original camera.
- **Edges and holes** use transparent pixels in a depth PNG, an optional `mask` array in JSON or the API, or `--alpha-mask` to use transparency in the optional colour image. An explicit `--max-jump` caps the allowed depth difference across adjacent mesh samples. The default estimates a threshold from nearby depth differences. Increase `--stride` to sample a large raster more sparsely.

PNG inputs must be non-interlaced. Grayscale stored in RGB is supported. For data stored in a specific PNG channel, choose `--channel r`, `g`, `b`, or `a`. RGB images can be decoded into byte arrays outside the CLI and passed to the API, including a browser's `ImageData`.

## Use the outputs

One view measures the visible surface and its depth. The direct splats carry that surface's normals and projected colours, so you can orbit it and see the relief. As the view turns farther, surfaces occluded in the original view become visible as missing areas. The closed mesh and SDF add an adjustable backing behind the measured surface. Use `--thickness` to set the backing depth and `--cells` to set the sampled field resolution. At low resolutions thin details may occupy less than a grid cell.

- `mesh.obj` contains the front triangles, sides and backing, with RGB vertex colours. The library also exposes the open front mesh as `model.front` for applications that want the measured surface alone.
- `sdf.json` contains the sampled signed field in world units. `origin` is the first grid sample, `spacing` is the distance between samples, `dimensions` are XYZ sizes, and `values` run X fastest, then Y, then Z. Negative values are inside. `K.depth.readField()` turns an exported grid back into a callable `sd(x, y, z)`.
- `splats.json` is an Ink Studio world with its standard 16-float splat layout. It also records the source raster dimensions and camera calibration. Restore `data` with `Float32Array.from(saved.data)` when loading into an Ink Studio renderer. If colours are projected from an image, their full values are in the buffer.

Use `K.procedural.geometry.implicitSurface()` to extract an isosurface after editing or combining the SDF. The directly triangulated front and backed OBJ are available from the same original depth samples.

## JavaScript

```js
const { KIT: K } = require('@shapeshift-labs/ink-studio').load();
const model = K.depth.fromMap({
  width, height, depth,
  camera: { type: 'perspective', fx, fy, cx, cy },
  image: { width, height, data: rgba, channels: 4 },
  alphaMask: true,
  thickness: 0.12
});
const world = model.world();
const field = model.field({ cells: 72 });
const polygonal = K.procedural.geometry.implicitSurface(
  point => field.sd(...point),
  { min: field.lo, max: field.hi },
  { resolution: field.h, maxCells: 1000000 }
);
```

Use `model.splat(builder)` to emit the observed splats into an existing world. Use `model.addSolid(sculpt, material, { cells })` to add the backed surface to a sculpt for carving, lighting, collisions or other field operations. A browser bundle exposes the same `K.depth` API.

```sh
node cli/ink-studio.js render examples/depth-map.js --ortho --raw
node cli/ink-studio.js render examples/depth-map.js --ortho --raw --yaw 0.77 --pitch 0.2
```

## Converting a signed field back to geometry

`K.sdf.toMesh(field, options)` polygonizes a bounded field at its zero surface. Pass a function
`sd(x, y, z)` with `bounds: { min, max }`, or pass a field object with `sd`, `lo` and `hi` such as
the result of `model.field()`, `K.depth.readField(grid)` or `K.mesh.field(mesh)`. Leave room around
the surface in the sampling bounds when you need a closed mesh.

```js
const signedDistance = (x, y, z) => Math.hypot(x, y, z) - 1;
const options = { bounds: { min: [-1.2, -1.2, -1.2], max: [1.2, 1.2, 1.2] }, resolution: 0.12 };
const mesh = K.sdf.toMesh(signedDistance, options);
const world = K.sdf.toSplats(signedDistance, { ...options, res: 0.08 });
K.sdf.solid(S, signedDistance, { r: [1, 2, 3] }, options);
```

`resolution` is the meshing cell size. `maxCells` bounds the sampling work, and `color` sets the mesh
material's 0–1 RGB. `K.sdf.solid` adds the sampled surface to an existing sculpt and retains the original
distance function for sculpt operations. `K.sdf.toSplats` bakes a standalone world with an inspection
camera. Its optional `res` controls splat spacing, and `palette`, `material` and `cam` customize the world.
Use the depth importer's `front`, `mesh` or `splat()` directly when you want the projected image colours.

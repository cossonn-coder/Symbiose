# Textured surfaces

SDF sculpting and Gaussian splats remain the default authoring and rendering path. A scene may opt into a textured patch for ground, paving, a façade, or a curved channel. It may also use textured surfaces for its entire visible geometry. Opaque and transparent cutout pixels share the same atlas batch and depth-test with splats.

`TexturedSurface` and `SpriteSurface` are available from `studio.load()` and the plain-script bundle.

```js
const terrain = TexturedSurface.heightfield({
  bounds: [-8, 8, -6, 6],
  segments: [64, 48],
  height: (x, z) => 0.4 * Math.sin(x * 0.3) * Math.cos(z * 0.4)
});
const atlas = SpriteSurface.make(1024);
atlas.mesh(terrain, 256, 192, (x, y) =>
  (x + y) % 9 === 0 ? 0x74924d : 0x486638);

// Both attachments and an optional solid foundation use the drawn triangles.
const rootY = terrain.height(2, 3);
S.ground(grassMaterial, { rad: 8, h: terrain.height, res: 0.2 });
const world = B.finish({ spriteSurfaces: atlas.finish() });
```

`heightfield` accepts increasing `[minX,maxX,minZ,maxZ]` bounds and a height function or a row-major grid of `(columns+1)*(rows+1)` heights. Array rows start at `maxZ`, matching image rows. Heights are baked once. `height(x,z)` uses triangle interpolation and clamps queries at the bounds. `sample(u,v)` returns `{point,normal}` on the same triangles. Its coordinates and the image UVs range from zero to one. UV `(0,0)` is the upper-left image corner, at `[minX,height,maxZ]` for heightfields.

Use the same sampler when an SDF foundation needs to agree with the texture. A visible patch alone supplies rendering geometry. The sculptor continues to own authored solid volume, carving, support and fracture behavior.

## Path profiles

```js
const channel = TexturedSurface.sweep({
  path: K.anim.path(points, { steps: 24 }),
  segments: 120,
  profile: [[-0.5,0.15],[-0.35,0],[0.35,0],[0.5,0.15]]
});
atlas.mesh(channel, 64, 512, paintChannel);
const attachment = channel.sample(0.5, 0.4);
```

Profiles are `[sideOffset,heightOffset]` pairs. U follows profile edges and V follows arc length along the path. The default frame uses `up: [0,1,0]`. A vertical tangent needs a custom `frame(distance)` that supplies `{p,tan,right,up}`. This permits banking and inverted paths. `closed: true` joins the final station to the first exactly. Samples interpolate the tessellated triangles, including between stations.

For an arbitrary façade, skirt, or parameterized patch use `TexturedSurface.grid({segments:[columns,rows], point:(u,v)=>[x,y,z]})`. For an existing mesh call `atlas.mesh({points,uvs,triangles}, width, height, paint)`. Points are flat XYZ coordinates, UVs are flat normalized pairs, and triangles contain vertex indices. `atlas.face(...)` continues to work with the same layout.

## Rendering and limits

The native WebGL renderer and software renderer read `world.spriteSurfaces`. Set `spriteSurfaces: false` in render options to bypass the optional surfaces. A custom browser host may use `createSurfacePipeline` from the WebGL entry point with a depth attachment shared with the splat pass. The Rebirth host uses the same atlas representation.

Paint returns a 24-bit RGB integer or `undefined` for a transparent cutout. Sampling uses nearest texels. Fractional alpha is reserved for splats and the existing sprite-atlas effects. Texture RGB is authored surface color, so bake surface shading into the paint when desired. The software renderer's resolved-frame looks also affect the result. Surface color is baked. Material-selector and live-relighting channels continue to use SDF splats.

Grids default to a 200,000-triangle budget. Raise `maxTriangles` explicitly up to 2,000,000. The atlas has its existing configurable width and maximum height. Invalid geometry or paint leaves the atlas allocation unchanged. Treat finished geometry and atlas data as immutable and create a new atlas when editing them.

Run `ink-studio render examples/textured-surfaces.js` for a mixed example. Its `build(seed,{textured:false})` also exercises the SDF and splat rendering path.

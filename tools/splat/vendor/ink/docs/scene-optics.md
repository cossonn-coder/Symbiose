# Scene optics

Ink Studio can capture the objects around a planar mirror, move their reflected colours with a ripple field, and composite fog, mist or beams against scene depth. Each tool works independently. The [beacon pool](../examples/beacon-pool.js) uses all three with sculpted geometry.

```sh
ink-studio render examples/beacon-pool.js --t 0.94 --raw --out pool.png
ink-studio sheet examples/beacon-pool.js --t 0.4,0.94,1.5 --raw --out pool-motion.png
```

Use `--reflections off` or `--atmosphere off` to inspect each effect separately. The software renderer supports perspective and orthographic views, and the effects run before palette quantization.

The [WebGL canvas renderer](browser-renderer.md) supports the shared glass-beam pass. Planar capture, ripple-driven reflection, and volume integration in this guide use the CPU renderer unless a host implements those passes explicitly.

For moving directional light and cast shadows on solid geometry, see [Live sun lighting](live-sun.md). See [Moving cloud shadows](cloud-shadows.md) for a shared coverage grid that shades the terrain, fog, and water. Use [Authored lightning](lightning.md) to time flashes that light clouds, appear in water reflections, and reveal nearby geometry. See [Indoor and outdoor exposure](scene-exposure.md) for rain boundaries and shelter for fog, light, and wind.

Use [Animated splat fields](animated-splat-fields.md) for drifting particles, aurora curtains, dust walls, and wakes that follow a route.

Use [Celestial tracks](celestial-tracks.md) to key authored suns, moons, stars, and eclipses on the same clock as sky profiles.

Use [Atmosphere emitters](atmosphere-emitters.md) to release smoke, steam, spray, or fog from fixed or moving scene sockets.

Use [Effect palette ramps](effect-palettes.md) to reserve tone steps for fog, clouds, night skies, and emissive details.

Use [Art direction](art-direction.md) to control cloud edges, atmospheric bands, foreground contrast, and held motion.

Use [Silhouette protection](silhouette-protection.md) to tune fog and contrast on a selected subject and review it across the export directions.

Use [Layered horizon art](layered-horizon.md) to paint a distant vista with depth-dependent parallax, bounded tiling, and camera fades.

Use [Transition review](transition-review.md) to compare native export frames through changes in weather, lighting, and camera. Save a [shot recipe](shot-recipes.md) to replay a review from the same camera path and weather state. The [environment review shots](environment-review-shots.md) cover wet stone under a moving sun, offshore cloud parallax and a fog crossing, and localized rain and reflections at a sheltered market.

Use [Environment packs](environment-packs.md) to share versioned sky, weather, and atmosphere settings across scenes.

Use [Interruptible transitions](interruptible-sky.md) to carry the current sky and weather values into a new transition.

Use [Conditional weather tracks](conditional-weather.md) to drive sky transitions from cues and simulation state.

Use the [environment inspector](environment-inspector.md) to report which keys, profiles, and regional overrides contribute at a world position.

Export [environment passes](art-passes.md#environment-passes-for-compositing) for downstream compositing of sky, fog, precipitation, reflections, and foreground coverage.


## Measured render budgets

Run the headless benchmark from the repository root. It covers the fog observatory, the shaped-mist ravine, sparse illuminated mist pockets, and the lens workshop's transparent layers.

```sh
node scripts/benchmark-render.js 7 > render-budgets.json
```

The report records median and 95th-percentile frame time, translucent fragments, optical ray samples, density and cloud lookups, and skipped work. It measures warmed render calls at 128 × 80 art pixels before image encoding. The uncached and dense reference lanes use the same camera, lighting and sampling quality. The benchmark checks identical RGB bytes.

In Node, pass `renderStats: true` to `render(world, options)` and read `frame.renderStats`. Its `frameMs` measures the render with counters enabled, including any internal color and reflection passes. The benchmark records its timing samples with counters disabled and captures the work totals separately.

- `fragments` counts blended splat and sprite contributions. `translucentFragments` counts contributions with opacity below one that leave the surface depth buffer unchanged.
- `volume.raySamples` counts optical solves at pixel ray depths. `densitySamples` and `cloudSamples` count primary optical density lookups during the frame. Light and shadow probes and asset baking are outside those lookup counts. Analytic bounds, cached fog, and empty march steps have separate counters.
- `volumeQuality.cacheBounds: false` bypasses the per-ray volume bounds and full-fog caches for comparison. `volumeQuality.skip: false` bypasses conservative field skipping and evaluates the same march grid densely.

## Planar reflections

```js
const mirror = K.reflection.plane({ id: 'pool', at: [0, 0, 0], normal: [0, 1, 0] });
const water = K.reflection.material({ r: [1, 2, 3], a: 0.65 }, 'pool', {
  f0: 0.3,
  color: '#b8e0ea',
  distortion: 10,
  blur: 0.7
});
// Use water when adding the flat basin surface to S, then bake.
const world = B.finish({ cam, reflections: [mirror] });
```

The receiving material limits the reflected area, including irregular outlines. Put the receiving surface on the mirror plane and point the plane normal toward the objects and camera. The renderer samples a single mirrored view per visible, referenced plane. Splat centres behind the plane are excluded. Use `bias` in world units to exclude splats very close to the plane, or use `select(index, x, y, z, world)` to control which animated splats appear in the capture.

`K.reflection.material` adds a `planarReflection` layer named `mirror`. The layer takes the usual finish tint, `strength`, Fresnel `f0` and `power`, and optional finish masks. `distortion` controls how much a normal perturbation shifts the reflection in art pixels. `blur` is a small reflection filter radius in art pixels. Any finish normal, including `waves`, `noise` and ripple rings, can perturb the capture. Empty reflected pixels reveal the other finish layers and the base colour.

For finishes that use the scene sky and its active profile, see [Shared sky reflections](shared-sky-reflections.md).

The existing `reflection` finish type supplies a three-colour sky. It can be layered underneath a planar mirror. `K.reflection.reflectedView(matrix, plane)` supplies the mirrored column-major world-to-view transform to other renderers. `K.reflection.captureView(matrix, plane, eye)` also supplies the clipping equation `[nx, ny, nz, -dot(at, normal)]` and the clip bias. It returns `null` if the eye is on or behind the reflecting side's bias. Use `SurfaceLook.shade` with a `reflection(layer, normal, geometricNormal)` callback returning `{ rgb, coverage }` in 0–1.

## Ripple sources

```js
const ripples = K.ripple.field({ scale: 0.48, amplitude: 0.4, speed: 1.2, damping: 0.25 });
const finish = K.surface.preset('rippling-water', { r: [1, 2, 3] }, { normal: ripples.normal });
// This can also be called later, after the world is baked.
const drop = ripples.add({ at: [1, 0, -0.5], start: 0.3, strength: 1 });
```

Drop coordinates use the material's pattern space, which defaults to the sculpt's rest coordinates. The optional material `origin` and `scale` shift and scale that space. The ripple plane defaults to XZ. Set `axis` and `cross` to two perpendicular XYZ directions for another plane. `scale` sets the wavelength, `width` sets the width around the travelling wavefront, and `speed` is distance per second. Set `repeat` on a drop for a repeating source.

Add and remove sources while rendering without rebaking. `remove(drop)` removes one source, `clear()` removes all, and `prune(time, reach)` retires non-repeating drops whose last rings have travelled beyond the given maximum radius. `sample(position, time, footprint)` returns the normal offset. Use a declarative `{ type: 'rings', amplitude, scale, drops }` normal for data-authored scenes.

A renderer can call `field.frame(time, storage)` once per frame and upload the
result. `axes` contains the two world-space tangents, `shape` contains
`[amplitude, wavelength, packetHalfWidth, damping]`, and each of the first
`count` entries in `drops` packs `[u, v, wavefrontRadius, strength]`.
Optional `Float32Array` storage needs four slots per active source. A field's
`capacity` defaults to 64 and can be lowered to fit a host's buffer.
`K.ripple.sampleFrame(frame, position, footprint, out)` evaluates the same
world-space slope as the surface normal sampler, within float packing precision.
Shader hosts can include `K.ripple.glsl` and sum `inkRippleSlope` for each drop
at a tangent-plane position. The host chooses how that slope affects its
material or reflected view.

## Atmosphere

For sky-coloured extinction at scene depth, see [Aerial perspective](aerial-perspective.md).

```js
const world = B.finish({
  cam,
  atmosphere: [
    K.atmosphere.fog({ top: 0.2, near: 3, density: 0.14, color: '#6e889f' }),
    K.atmosphere.sphere({ at: [-1, 0.3, -2], radius: 1.4, density: 0.3, color: '#93a4b0' }),
    K.atmosphere.box({ min: [-2, 0, -1], max: [-0.3, 0.5, 3], density: 0.2 }),
    K.atmosphere.shaft({ from: [0, 3, -0.8], to: [1.4, 0, 1], radius: 0.22,
      density: 0.5, color: '#ffdb94' })
  ]
});
```

Fog can occupy a height slab with `bottom` and `top`, or cover the whole view. Sphere and box volumes let mist stay around an object or in a defined region. A shaft is a capped cylinder of tinted atmosphere. Combine volumes freely. Integration accounts for overlaps in camera-depth order and stops at the nearest opaque surface. Use `near` or `far` to bound a volume by camera ray distance. Colours accept a palette index, a hex string, or 0–1 RGB.

Hosts can use `K.atmosphere.prepare(world.atmosphere, world.pal)` and `K.atmosphere.trace(volumes, eye, unitDirection, distance)`. Trace returns premultiplied RGB and remaining transmittance `[r, g, b, t]`, so the final colour is the returned RGB plus `t` times the scene RGB.

## Bounded density and lit volumes

Use [geometry-shaped atmosphere](geometry-shaped-atmosphere.md) to fit clouds and fog to paths, signed-distance shapes, or terrain. [Volume cutouts](volume-cutouts.md) clear feathered pockets in those volumes.

```js
const D = K.procedural.density;
const shape = D.fromSdf({
  bounds: { min: [-2, 0, -2], max: [2, 1.4, 2] },
  field: (x, y, z) => Math.hypot(x / 1.6, (y - .55) / .52, z / 1.4) - 1,
  feather: .20,
  breakup: .65,
  noise: (x, y, z, t) => .5 + .5 * Math.sin(4 * x + t + z),
  drift: [.10, .04], windInfluence: .6
});
const volume = K.atmosphere.field({
  field: shape, density: .8, step: .14, ramp: ['#435969', '#769599', '#adc5bd'],
  anisotropy: .22, emissive: '#5cb3aa', emissiveGain: .14
});
const volumeLighting = {
  ambient: .4,
  sun: { direction: [-.4, .8, .4], intensity: .7 },
  point: { at: [0, 1.4, -1], color: '#ffc984', radius: 4, intensity: 2 },
  shadow: K.atmosphere.occluder(sceneSdf)
};
```

Put `volume` in `finish.atmosphere`, and pass `volumeLighting` and optional `volumeQuality` to the finished world. The integrator clips each ray against opaque geometry, evaluates bounded density through overlapping media, and adds single scattering, geometry shadowing and emission before palette resolution. Use `windInfluence` to let live airflow advect the density pattern. Directional light is defined as a vector from a sample toward the light. Set `lit: false` on a volume to use its density ramp and emission without scene scattering.

`D.bounded({ bounds, sample, skip })` accepts a custom density. A skip callback returns a conservative distance to the next possible nonzero sample. `D.sparse(field, { resolution, brick, time })` caches occupied bricks at one time and includes conservative interpolation-aware skipping. `D.toMesh(field, { iso, resolution })` extracts a threshold surface. `D.scatter(field, { minDensity, radius, seed })` places deterministic points inside density.

Use `--atmosphere off` to disable the pass. `volumeQuality` controls `scale` (1–4), `depthTolerance`, `steps`, `stepScale`, `skip`, `samples`, `seed`, and `jitter`. The coarser pass only reuses nearby samples with compatible depth. Set `stats: true` to inspect `frame.volumeStats` ray and fallback counts. Set `jitter: 'blue-noise'` for stable spatial offsets, or `jitter: 'spatiotemporal'` with an explicit `volumeHistory: K.atmosphere.history()` for frame-varying offsets and filtered accumulation. The history resets across a changed camera, a time discontinuity, or incompatible opaque depth. CLI options include `--volume-scale`, `--volume-steps`, and `--volume-jitter`.

Render `examples/art-pipeline.js` to see sculpted pool mist, a local light, and emission coloring at art resolution. For aimable beams and multiple lamps, see [Local lights in fog](fog-lighting.md).

## Pixel budgets and upload profiling

Give a scene a soft internal raster budget through `look.pixelBudget`.
The headless renderer chooses an integer scale that fits the budget before
upscaling. An explicit `--px` controls the scale for an individual render.
Ordinary scenes that omit the budget use their existing scale. Browser hosts
can apply the same limit with `FrameBudget.artScale` from the studio bundle.

`FrameBudget.uploadRows(rows, upload, gap)` visits half-open dirty row runs and
clears rows after a successful upload. A gap of one can batch two small
transfers together. The visitor receives the first row and the exclusive end
row and can transfer directly from the original typed array.

Use `ink-studio perf <scene> --secs 10 --fps 60 --json` to compare animation
step time, p95, peak upload bytes and planned upload calls. Use
`--upload-gap 1` for a browser host that batches adjacent ranges across a
single clean row. These are animation and transfer measurements. Measure
compositor time and frame rate in the browser at the intended viewport.

For densely sculpted dioramas, `FrameBudget.staticGroups` builds conservative
boxes for consecutive splat ranges. Pass the ranges that the host or an
animation can move as `mutable`. Mark shader-driven translations that the
planner cannot infer as mutable too. `visibleIndices` writes the original
indices for each retained group using a column-major view-projection matrix.
Use its returned count as the instance count for color, ID and mask passes.

## Ordered ink coverage

`InkVeil.footprint(bounds, size, signedDistance, feather)` bakes an R8 mask
for a horizontal receiving surface. Positive world-space distance is inside
the shape. Use the mask bounds to map the ray-plane intersection to texels.

`InkVeil.glsl` applies the same ordered thresholds as `InkVeil.rank`.
Shaded pixels below the coverage threshold return black. Light intensity,
a feathered shoreline, and projected caustics drive coverage on the plane.
The view depth occludes the plane behind foreground geometry. Each of the up to
eight light sources supplies world X and Z, radius and signed intensity. Use the
internal art-pixel coordinates so the pattern stays sharp at integer scales.

For an optional scene reveal, attach a track to `world.inkVeil.reveal`.
The track works with or without a receiving surface. Each cue opens an
ellipsoid centered at `at` with positive XYZ radii in `extent`. Its opening
starts and ends at the supplied times in seconds. The settle interval ramps
the whole scene to full coverage.

```js
world.inkVeil = {
  reveal: InkVeil.reveal([
    { at: [0, 1, 4], extent: [4, 3, 5], start: 0.25, end: 2 },
    { at: [1, 7, 0], extent: [6, 5, 5], start: 1.5, end: 3.5 }
  ], [3.5, 4.5])
};
```

Sample the track once per frame with seconds since playback started and
upload the returned `centers`, `extents`, and `settled` before compositing.
Use the surface depth and camera to evaluate coverage in world space.

`InkVeil.sweep({ from, to, start, end, feather })` moves a single ordered
edge through the scene. Use world-space endpoints beyond the foreground
and rear silhouettes. Upload `frame.plane` to `u_inkSweep` and
`frame.feather` to `u_inkSweepFeather` while the track plays. Zero disables
the sweep. A negative feather holds the frame at black before the edge starts.

Use `InkVeil.flow(keys, { period, delay, rise, wake, distortion })` for a
cyclic reveal that follows action and closes behind it. Keys use `time`,
`at`, and `extent`. The first time must be zero and later times must fall
inside the period. The track holds black during its initial delay and then
grows the moving area over `rise` seconds. The `wake` option gives the
area a trailing edge in seconds, and `distortion` bends the contour in world
units. Send `frame.warp` to `u_inkRevealWarp` alongside the cue uniforms.
`track.coverage(seconds, point)` lets overlays share the scene's visibility.

## Pixel art on flat surfaces

`SpriteSurface.make()` batches world-space rectangles into an RGBA atlas.
Each rectangle specifies its bottom-left corner and two span vectors in world
units. The paint callback receives integer column and row coordinates from
the upper-left texel and returns a packed RGB value or `null` for a cutout.

```js
const signs = SpriteSurface.make();
signs.face([-1, 1, 2], [2, 0, 0], [0, 1, 0], 48, 24, (x, y) =>
  x < 2 || x >= 46 || y < 2 || y >= 22 ? 0x36e4ff : 0x131a2c);
world.spriteSurfaces = signs.finish();
```

The batch contains the atlas bitmap and interleaved XYZ and UV-in-texels
vertices. Inkwell Rebirth draws those triangles once into the scene color and
depth before drawing the splats. Use nearest filtering to keep the art sharp.

## Look bindings for media and reflection captures

Use `finish.look.optics` on a diorama, `visual.look.optics` on a simulation
world, or `look.optics` on a JavaScript scene. Rules accept inline RGB
stacks, palette swatches, or a versioned look asset. They share look
selectors, `order`, and `weight`. These bindings adjust uniform
optical colors. Author spatial variation with volumes, water columns,
or coverage-aware material rules.

```json
{
  "optics": [
    { "select": { "medium": "cistern-water", "mediumKind": "water" }, "asset": "cistern/verdigris" },
    { "select": { "medium": "drift" }, "asset": "cistern/mauve" },
    { "select": { "medium": "inspection-pane", "mediumKind": "glass" }, "palette": ["#cd8e56", "#edd6a0"] },
    { "select": { "medium": "cistern-mirror", "mediumKind": "reflection" }, "asset": "cistern/mirror-wash" }
  ]
}
```

- **Water.** Bind a native water body or span medium by ID. Its bound
  tint enters the existing channel-wise extinction calculation. In the
  headless renderer, the camera ray crosses the published columns or
  spans, subtracts air pockets, and accumulates absorption and color
  up to each splat's depth. A simulation view with a matching optical
  rule builds the water frame from `visual.fields.water`. It can
  also specify base coefficients in `visual.waterOptics`.
- **Fog.** Match the volume ID or its kind. The binding grades its color,
  density ramp colors, and emission before the volume integrator uses
  them. With native water, air volumes are integrated through the dry
  parts of the ray and water through the wet parts.
- **Glass.** Match `mediumKind: "glass"`, or add the pane's surface or
  object name as `medium`. The glass flag comes from the material or
  splat. The optical binding grades that pane's own contribution,
  preserving its coverage and the other looks behind it.
- **Reflections.** Match the reflection plane ID with
  `mediumKind: "reflection"`. Materials and scoped splat looks are
  evaluated in the mirrored capture. An optional capture look then
  grades its RGB while preserving capture coverage, before the
  receiving material uses it.

Water bindings work in the standard WebGL renderer when the host
supplies the bundled `RenderStages` toolkit. The headless renderer
supports all four bindings. It uses the native water frame for
transmission, and separate surface materials for effects like ripples
and planar reflections. Fog-only views can use the separate coarser
and temporal atmosphere pass.

```sh
node cli/ink-studio.js render examples/optical-look-bindings.js --ortho --out cistern.png
node cli/ink-studio.js render examples/optical-look-bindings.js --ortho \
  --params '{"variant":"reflection"}' --out cistern-reflection.png
node cli/ink-studio.js probe examples/optical-look-bindings.js \
  --select '{"medium":"cistern-water"}' --args '{"stage":"optics","rgb":[0.2,0.21,0.24]}'
```

Use `--water off`, `--atmosphere off`, or `--reflections off` to
inspect individual passes. The optical probe reports the coefficient
mapping supplied to the integrator.

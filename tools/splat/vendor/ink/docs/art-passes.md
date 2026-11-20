# Art-pixel render passes

`ink-studio passes <scene>` writes CPU-rendered color and diagnostic PNGs on the same art grid. Use `--channels depth,normal,emission` to select passes, `--px1` for native resolution, and `--out directory` to choose the destination.

In Node, call the library's `render(world, { passes: true })` or supply an array of channel names. The result includes `frame.passes` with `w`, `h`, and typed arrays in top-down row-major order. A caller can request any subset. `passes: true` requests the standard art passes. Request environment passes by name or with `['environment']`. A render without passes skips the per-pixel buffers. `--colored` returns passes from its native render grid.

| Channel | Data |
| --- | --- |
| `coverage` | One float per pixel. The combined opacity of splat and edge-sprite layers, independent of the background. |
| `depth` | One float per pixel. Camera-axis distance to the owning splat's center, in scene units. Empty pixels use infinity. |
| `normal` | Three floats per pixel. The owning sample's normalized world-space surface normal. Samples with no surface normal use zeros. |
| `objectId`, `materialId` | Unsigned integers. Zero means unassigned. The `objects` and `materials` arrays give authored labels, where supplied. |
| `target` | Index into `targets` for the dominant splat or frame look at each pixel. Scoped bindings take precedence over scene-wide grades. Zero means no recorded binding. The table identifies the asset, stage, and selector when available. |
| `mask` | A scalar between zero and one. The pass shows sampled spatial mask weights composited with surface coverage, including transparent splats, followed by applied frame and palette masks. |
| `emission` | Three floats per pixel. Premultiplied visible emissive RGB. Nearer layers attenuate emission. |
| `splatId` | Unsigned integers. One-based splat index of the owner, with zero for an empty pixel. Stable while the world preserves its splat slots. |
| `position`, `objectPosition` | Three floats per pixel for the owned point in world or rest-space coordinates. |
| `protected` | Per-pixel detail protection used by the stable resolve. |
| `emissionDepth` | Approximate depth of the nearest contributing emissive layer. |
| `motion`, `emissionMotion` | Two floats per pixel for XY displacement in art pixels, with positive Y downward. |

The owner is the nearest depth-writing fragment with effective opacity above 0.5. A layer drawn later wins a depth tie. Opaque edge sprites carry their anchor's splat ID. Coverage and emission also account for soft layers. These rules keep the depth, ID, and normal attached to the same surface.

Pass a solid's `objectId` or `tag` and its material's `materialId` to attach names. Unnamed sculpted objects and materials get anonymous IDs local to the build. For direct builder splats, use `builder.describeSplats(first, end, { object, material })` with a half-open range. A directly authored emissive splat can set `emission: false` alongside `em: true` to keep the legacy shading behavior while excluding it from the emission buffer. Construct the builder with `{ renderMetadata: false }` as its third argument to skip storing these fields.

Browser hosts receive `ArtPasses` in the toolkit bundle, including the channel names and GLSL helpers for ownership and blending. The default [WebGL canvas renderer](browser-renderer.md) draws the image. Node's render API provides the diagnostic buffers described here.

For motion channels, request `captureMotion: true` on the prior frame and pass its `motionReference` as `motionFrom` when rendering the next frame. The two frames must use the same art dimensions and preserve their splat slots. The emission variant also tracks translucent sources.

The PNG writer includes a `passes.json` manifest with the art dimensions,
image scale, and available previews. Read `position` and `objectPosition`
directly from Node's typed arrays for floating-point coordinates.

## Environment passes for compositing

```sh
ink-studio passes examples/weather-front.js --t 5.8 --channels environment --px1 --out weather-passes
ink-studio clip examples/weather-front.js --from 4 --to 6 --fps 12 --passes environment --px1 --out storm.png
```

Use `environment` to request all five passes. Replace it with a comma-separated list to select individual channels. `render`, `sheet`, `clip`, and `sim render` write the requested passes beside the main export when you use `--passes`. Clips write synchronized animated PNGs. [Shot recipes](shot-recipes.md) verify each sidecar when replaying a render or clip.

| Channel | Node data per pixel | Export |
| --- | --- | --- |
| `sky` | RGB of the unobstructed backdrop, including authored sky, celestial objects, clouds, and horizon art. | RGB image |
| `fogTransmittance` | Fraction of light transmitted through fog and aerial perspective to the resolved surface or background. | Grayscale, white is fully clear |
| `precipitation` | Premultiplied RGBA of visible rain and falling snow, with depth occlusion and particle lighting. | Straight-alpha RGBA |
| `reflections` | Premultiplied RGB contributed by visible material, scene sky, and planar reflection layers. | RGB image with zero where no reflection contributes |
| `foregroundCoverage` | Coverage of scene splats and sprites, with falling precipitation and ray-traced media omitted. | Grayscale, white is fully covered |

Node returns these buffers as `Float32Array` values on the native art grid. PNGs encode each channel at 8 bits and the manifest records the encodings. Color passes are captured before volume fog, final palette mapping, and frame-wide effects. The fog channel excludes water absorption, cloud extinction, and the legacy per-splat haze tint.

## Selective ink and stable pixels

Supply these in a scene's `finish.look` or pass `ink` and `stable` overrides to `render`.

```js
const look = {
  ink: {
    silhouette: { shadow: '#101a29', highlight: '#a48d64' },
    crease: { steps: 1, litSteps: 0 },
    boundary: { color: '#243d4c' },
    light: [-.5, .8, .45],
    depthGap: .17,
    creaseCosine: .58,
    litAt: .52,
    suppressSameMaterial: true,
    materials: {
      stone: { ramp: [1, 2, 3, 4], boundary: false },
      spell: { palette: 'magic' }
    },
    reserved: {
      emission: ['#c46c38', '#fca35e', '#fff4cc'],
      fog: ['#1f303b', '#536f79', '#94b5bd'],
      magic: ['#472a64', '#a964c5', '#f5d5ee']
    },
    emissionThreshold: .25,
    fogThreshold: .27
  },
  stable: {
    snap: true,
    anchor: [0, 0, 0],
    dither: 'object',
    spacing: .08,
    resolve: 'clusters',
    threshold: .4,
    protect: ['eyes', 'spell']
  }
};
```

Use [Effect palette ramps](effect-palettes.md) to author independent fog, cloud, sky, and emission colors using the rendered effect coverage.

Give a line a fixed color, separate highlight and shadow colors, or steps along its authored material ramp. A material rule can override or disable any line independently. A palette reserved for a named material applies only to that material. The emission and fog ramps are keyed by their render signals.

See [Stable dithering and camera review](stable-dithering.md) for per-object anchors and native-resolution pan and orbit clips. Camera snapping applies to orthographic projection. World-space dithering samples at the visible surface. Object-space dithering maps the sample back to the splat's rest frame, using the rig transform where available. Screen-space dithering follows the art grid. Use `--ortho --snap`, `--dither-space screen|world|object`, and `--resolve native|coverage|clusters`. The coverage and cluster modes render four subpixels per art pixel and can protect named objects, materials, glints and small emissive details.

## Art-pixel effects

Set `finish.look.effects`, or pass `artEffects` to `render`. Each effect accepts `false`. Use `--effects off` to disable the whole stack.

| Effect | Controls |
| --- | --- |
| `emitter`, `reflection` | Separate `colors`, `threshold`, `rate` and `phase` for visible emitters and their planar reflections. |
| `glow` | `radius` in art pixels, one or two `bands`, palette, timing, emission threshold and `depthBias`. |
| `heat` | Emitter threshold, `radius`, upward offset `up`, displacement `pixels`, `rate`, `phase` and `depthBias`. Samples and destinations are both depth checked. |
| `cycle` | `colors`, discrete `rate` and `phase`, with an optional named `material`. Multiple cycle rules can be supplied. |
| `trail`, `smear` | Independent palettes and timing, prior frame count, duration and depth bias. Smears also expose discrete `steps` and maximum `reach`. |

Call `studio.load().ArtEffects.history()` and reuse the result as `artHistory` for consecutive frames of the same view. The CLI creates a history for sheets and animation clips. Call `clear()` after a camera cut. Art effects leave the source emission and geometry passes available for inspection.

## Local splat ordering

Set `look.splatOrder = 'surface'` or pass `--splat-order surface` to sort overlapping fragments by an estimated intersection with each splat's surface plane. `center` uses the ordinary global order. The queue has a configurable `fragmentBudget` and replays the original order if the budget is exceeded. The result sets `orderFallback` in that case.

Run `node scripts/experiment-splat-sampling.js <output-directory>` to reproduce the independent footprint and ordering experiments. The four-tap footprint experiment increased short-sequence flicker in the tested scenes. The surface-order test with crossed planar splats corrected all 576 misordered opaque overlap pixels in that fixture.

## Directional sprite atlas

```sh
ink-studio atlas examples/art-pipeline.js --t 1.2 --w 92 --h 76 --directions 8 --cols 4 --maps depth,normal,emission
ink-studio atlas examples/art-effects.js --from 0 --to 1.2 --fps 12 --directions 8 --pivot 0,0,0
```

`color.png` contains straight RGBA. Optional maps share its layout. `atlas.json` includes the registered pivot, camera direction, rectangle, timestamp, duration, file names and map encodings. Depth uses a shared scene-unit range encoded into RGB24. Normals are signed world-space axes mapped into RGB. Emission stores visible premultiplied emissive RGB.

Use [artist-authored cards and impostors](impostor-atlases.md) to place the resulting atlas back into a scene.

In Node, use `spriteAtlas(world, { width, height, directions, times, fps, pivot, view, maps, pose })`. Supply a `pose(world, time)` callback for scenes that need to advance a stateful timeline or pose a rig. A separate effect history is kept for each direction.

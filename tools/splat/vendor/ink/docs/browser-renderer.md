# Browser renderer

The package's browser entry selects WebGL 2. Bundlers that honor the `browser`
field can use the package name. With native browser modules, import
`webgl.mjs` by URL and serve its relative `src/webgl/` modules. Both entry
points export `createRenderer` as a default and named import. Prepare the
authoring toolkit with [the browser bundle](../README.md#embedding-and-custom-scene-collections).
Node's `render()` and the `ink-studio` CLI provide CPU image export.

```js
import createRenderer from '@shapeshift-labs/ink-studio';

const renderer = createRenderer(canvas, { toolkit: { KIT, PixelLook } });
renderer.render(world, { width: 320, height: 200, time: 0 });
```

The factory needs a canvas or `OffscreenCanvas`, a toolkit that exports
`PixelLook`, and an available WebGL 2 context. Include `KIT` to use
per-pixel materials and blue-noise tone generation. The renderer manages
the canvas context and can rebuild GPU resources after context restoration.
Call `renderer.dispose()` when the canvas is removed.

## Frames

Pass the world returned by `builder.finish()`. The drawing buffer is the art
resolution. Choose `width` and `height` to resize it, then enlarge visually
with CSS such as `image-rendering: pixelated`. The host controls input and
calls `world.anim.update(dt, time)` before drawing. Supply `time` and optional
`bornAt` in seconds. A camera override can set `target`, `dist`, `yaw`,
`pitch`, `fov`, and `ortho`. Angles are in radians.

Pass `changedRows` as an array of changed 512-splat texture row indices.
Omit it to upload all packed splat data, or pass `[]` when the data is
unchanged. Initial uploads and changes in the world's buffer or count still
upload the complete data. Replace pixel-material and fine-tile buffers or
their material tables when editing them. An explicit `order` can provide
one `Int32Array` of back-to-front splat IDs for the frame.

The browser defaults reuse depth order when the caller marks the rows
unchanged and the view, depth-dependent time, and ordering inputs match.
Scenes with bone buffers sort again. The canvas also uses a smaller palette
resolve shader when per-pixel materials, ambient occlusion, glass beams,
tone mapping, and grading are inactive. Pass `reuseOrder: false` or
`specialize: false` to the factory to compare the corresponding full path.

| Frame control | Effect |
| --- | --- |
| `raw` | Show the directly blended RGB instead of the palette resolve. |
| `colored` | Use higher-resolution contours over native-size interiors. On by default for scenes without per-pixel materials. |
| `outline`, `dither`, `tone` | Control outline and palette treatment. Use `tone: false` to disable an authored tone. |
| `paletteRemap` | Override a world's [palette remap](pixel-look.md#palette-remaps), or pass `false` to disable it. |
| `colorCurves` | Override a world's [scene color curves](pixel-look.md#color-ramps-and-channel-curves), or pass `false` to disable them. |
| `colorLut` | Override a world's [3D color LUT](pixel-look.md#3d-color-luts), or pass `false` to disable it. |
| `colorStack` | Override a world's [named color stack](pixel-look.md#named-color-stacks), or pass `false` to disable it. |
| `clean`, `lineClean`, `damp` | Control isolated-pixel cleanup, line cleanup, and per-pixel flicker damping. |
| `edges`, `lightShape` | Toggle surface edge sprites and per-pixel line shading. |
| `scale`, `stepAnimation` | Change the splat size or disable the shared per-pixel animation clock stepping. |
| `water: false` | Compare the scene with water optics disabled. |
| `portal`, `fade` | Render an oriented destination view or apply a scene fade. See [place travel and portals](portals.md). |

Set `frame.target` to a same-context framebuffer descriptor with `framebuffer`,
`width`, and `height` to draw offscreen. Its dimensions supply the defaults for
the frame. The [screen transition compositor](transitions.md#render-ink-studio-worlds-directly-into-a-transition)
can create these targets and reuse their color textures on the GPU.

## Shared baked splat instances

Use `createSplatInstances(prototypes, placements)` when a scene repeats finished,
stationary assets such as trees, doors, or crates. Prototypes are ordinary
`builder.finish()` worlds drawn around their local origin. The renderer stores one
copy of each prototype's packed geometry. It culls offscreen placements and
sorts the remaining splats together with the base world before blending.

```js
import { createRenderer, createSplatInstances } from './webgl.mjs';

const copies = createSplatInstances({ oak: bakedOak }, [
  { id: 'oak-west', prototype: 'oak', position: [-2, 0, 0] },
  { id: 'oak-east', prototype: 'oak', position: [2, 0, 0], scale: 1.2 }
]);
const renderer = createRenderer(canvas, { toolkit });
renderer.render(terrain, { instances: copies, changedRows: [] });

copies.update('oak-east', {
  palette: { '#517046': '#936540' },
  damage: { center: [0, 1.4, .2], radius: .5 }
});
renderer.render(terrain, { instances: copies, changedRows: [] });
```

A placement also accepts a right-handed row-major 3-by-3 `rotation`, a positive
uniform `scale`, an `opacity` multiplier for native splat density, and
`visible`. Palette replacements match the original baked RGB exactly. A
damage sphere hides splats whose local centers lie inside it. Clear the sphere
with `damage: null`. Transforms update only the placement table and draw order.
Palette and damage edits preserve the order when the camera stays still.
`changedRows` still describes rows edited in the **base** world.

`copies.get(id)` returns the authored placement. `copies.owner(index, terrain.count)`
maps a logical renderer splat index to the stable placement ID, prototype ID,
and local splat index. Placement IDs and logical ranges stay fixed while you
edit or hide copies. Create a new collection to change its membership.
`copies.flatten(terrain)` produces ordinary expanded world data with placement
provenance for tooling that requires packed per-placement rows.

This path uses baked lighting. Use `S.template()` and `S.place()` when each
placement needs lighting or burial tested against its surroundings during
sculpting. Shared prototypes require stationary splats without fine-tile or
per-pixel surface payloads. The renderer uses expanded rows when the frame
supplies an explicit draw order or uses per-pixel material or palette-constraint
passes. The base scene can contain animated splats.

Run `node scripts/benchmark-splat-instances.js` to compare the same authored
woodland and street scenes with shared and expanded geometry on Chrome's
hardware WebGL backend. The benchmark reports readback-fenced frame times,
texture storage, submitted splats, edit uploads, and framebuffer parity. Use
`--software` to run the same comparison on SwiftShader.

## Scoped looks and transparent contributions

Palette targets use the same object, material, and surface selectors in
WebGL and in headless renders. WebGL supports axis masks and planar raster
masks on palette policies. Masks can read world coordinates or baked local
coordinates, with stepped, linear, or smooth transitions. Raster masks can
select a color or alpha channel and use animated frames. Query-backed
masks, projected simulation fields, and custom projections use the
headless renderer.

Set `look.coverageAware: true` or pass `{ coverageAware: true }` to grade each
splat before blending. Each glass pane can have its own target palette or
color stack. A mask blends the pane's own color over the mask range.
With refraction enabled, the displacement samples the already graded
backdrop and leaves the glass and foreground contributions at their original
pixel. This pass needs four color attachments, or five when native water
is also active. Plain scenes and scenes with refraction off use the usual
color pass.

### Contribution picking

Use `renderer.pick(world, ray, frame)` in a WebGL host. In Node, create a
reusable picker with `ink.createSplatPicker(world, { time })` and call
`picker.ray(ray)`. Both use the same indexed geometric ray query.

```js
const result = renderer.pick(world, {
  origin: [0, 1, 6],
  direction: [0, 0, -1],
  maxDistance: 20,
  limit: 32
});
```

Results list front-to-back splats, glass, and water intervals. Each reports
its distance, opacity, and surviving contribution weight, with object,
material, and stable splat IDs when available. The result also names the
dominant contribution and the first solid receiver. Water reports spectral
transmission in the `media` list, including fully clear intervals. The query
follows the supplied straight ray in world space, so its distances describe
the underlying geometry.

For packed geometry edits, recreate a standalone picker after updating
its input. The WebGL picker follows the draw's data and instance revisions.
Use `changedRows: []` on draws with unchanged geometry to retain the index.

```sh
ink-studio trace examples/coverage-aware-glass.js world/contributions --at -1,1,6 --args '{"direction":[0,0,-1],"maxDistance":12}'
ink-studio look parity --strict
node scripts/benchmark-contributions.js
```

## Water optics

Attach a [water scene](procedural.md#water-bodies) as `world.water`.
The renderer traces water along each perspective or orthographic ray before
the background, and before each splat at its drawn depth. RGB extinction
depends on the distance traveled through water. Foreground splats and
translucent layers composite in the existing back-to-front draw order, so
water behind an object cannot tint the object's own color. A frame can
contain rays above, below, and crossing the waterline.
Air pockets on the water snapshot subtract their shared XYZ bounds from
each optical path, so a chamber can stay clear inside a flooded body.
Layered bodies trace each wet interval in ray order. Caves can share the
same XZ columns with water at other heights, and solid ceilings suppress the
waterline highlights where no air touches the top of the water.
Scenes above eight bodies or with per-medium optical profiles use a spatial
index in the water texture atlas. Up to 256 bodies share the atlas, which is
capped at 2048 × 2048 texels including metadata.

Water bodies have optional `optics` controls. `tint` and `surfaceColor`
take 0–1 RGB triples. `extinction` is a nonnegative RGB coefficient per
world unit. `surface`, `foam`, and `caustics` take strengths in [0, 1].
`refraction` takes a maximum displacement of 0–4 art pixels. Surface
highlights are stronger at grazing angles, foam favors shallows, and
stylized caustics fall off with depth. Screen-space refraction samples
pixels that also see the same interface through the splat layers. The art
palette still controls final quantization when `raw` is off.

`deepTint` is an optional RGB triplet blended in between the two world-unit
depths in `depthRange`. `sediment: {color, strength, height, scale}` adds
stylized drifting grains. `height` sets their falloff above the bed, and a
higher `scale` makes the grains finer. A span scene can choose these profiles
per medium to grade a clear lake and a darker flooded cavern independently.

Run the [Sunken gate example](../examples/water-bodies.html) from the repository
root with the commands below, then open the example through the local server.
The camera controls show the same shallow-water snapshot from above, at the
waterline, and underwater. The arrow keys swim against its sampled current.

```sh
node -e 'const fs = require("node:fs"); fs.mkdirSync("dist", { recursive: true }); fs.writeFileSync("dist/ink-studio.browser.js", require(".").bundle())'
python3 -m http.server 8080
```

## Environment rendering

Include the Ink Studio `KIT` in the renderer toolkit. Authored `skyEnvironment`, horizon bands, cloud cards and analytic `atmosphere` volumes are picked up from the same world used by the CLI. Both renderers evaluate profile tracks, interrupted transitions, and conditional weather cues with the shared clock. Pass `skyTime`, `skyProfiles`, or `skyTransitions` on a WebGL frame to override the authored playback.

Cloud cards use the same baked optical-depth projection as the CLI and clip against scene splats. Set `cloudRepresentation: 'card'` in the world or frame to use a card throughout a shot. Automatic selection draws the card where the asset's card weight reaches one. Impostors, near-volume blends, cloud cutouts and lightning remain on the software path.

WebGL integrates overlapping constant-density height, box, sphere, and shaft volumes before the palette resolve. Uniform weather profile density bindings apply. The WebGL pass supports up to 16 enabled analytic volumes per frame. Density fields, regional fog fronts, volume lighting, cutouts, and coupled water–air integration use the software renderer. Use `atmosphere: false` to bypass analytic fog, `cloudField: false` to hide clouds, or `environment: false` to bypass the WebGL environment passes.

Run the fixed-camera comparison with a local Chrome or Chromium executable.

```sh
ink-studio environment-parity --out studio/out/environment-parity
```

The command writes matched raw CLI and WebGL frames at the same art resolution, camera and time, plus amplified pixel differences and JSON error measurements. Sky-only cases isolate the directional background. Card and fog cases use matching soft splat edges to compare the media and depth compositing.

### Fog observatory test scene

The [compact 3D fixture](../examples/environment-test-scene.js) puts a baked cloud card behind an opaque tower, with a translucent pane in front of a bounded fog box. Illuminated markers make the depth changes visible. The 6.75-second camera track orbits the tower, pitches down, pans laterally, and advances from outside the box to inside it and past the far boundary.

```sh
ink-studio clip examples/environment-test-scene.js --to 6.75 --w 192 --h 128 --px 1 --raw --out perspective.png
ink-studio clip examples/environment-test-scene.js --to 6.75 --w 192 --h 128 --px 1 --raw --ortho --out orthographic.png
ink-studio environment-parity --fixture observatory --out observatory-review
```

The comparison renders the same seven camera checkpoints in each projection. An orthographic fog ray starts at the renderer's setback eye, so the orthographic view can retain fog after the nominal camera has passed the box.

## Feature coverage

| Feature | WebGL canvas renderer | Node and CLI renderer |
| --- | --- | --- |
| Packed splats, animation poses, palette and tone | Supported | Supported |
| Fine ink tiles, per-pixel patterns and edge sprites | Supported | Supported |
| Oriented live portal views with fragment clipping and foreground occlusion | Supported | Travel and camera mapping |
| Contours, cleanup, and camera-dependent glass beams | Supported | Supported |
| Selective ink, diagnostic buffers, stable art resolves, and frame-history effects | Host integration | Supported |
| Directional environment sky, parallax horizon bands, and baked cloud cards | Supported | Supported |
| Constant-density height, box, sphere, and shaft fog | Supported | Supported |
| View-dependent surface finishes, projected layers, reflection captures, and marched density fields | Host integration | Supported |
| Water-column extinction, surface highlights, foam, caustics, and refraction | Supported | Water data and queries |
| Text rendering, PNG/APNG, scene reviews, and sprite atlases | Host integration | Supported |

Pixel output can differ across the CPU and GPU backends. Use the same
backend for both sides of a pixel-exact comparison.

## Integrate a custom draw pipeline

Hosts that manage their own framebuffers and effects can import
`createSplatPipeline`, `splatShaderSources`, and `pixelShaderSources` from the
same entry. Pass `{ ascii: KIT.ascii?.glsl }` to the pipeline if the host
implements the text passes. Shader sources are available to hosts that
compile and bind independent programs.

Call `pipeline.programFor({ lamps, fine, textZones })` and bind its returned
`p` before setting uniforms. Uniform locations are in `u`. The full shader
is selected when any feature is active or unspecified. The shader can omit
those paths when all three are explicitly false.

Upload order IDs with `setOrder(ids)` and call `draw()` after binding the
framebuffer, textures, and blend state. To use host-owned geometry, pass
`draw(count, vao)`. That VAO needs the two-component quad corners at
attribute 0 and the integer splat ID with instance divisor 1 at attribute 1.
Call `pipeline.dispose()` to release the pipeline's own resources.

# Tone and stipple

The stipple look maps the lit frame to a small palette on a fixed screen grid.
Try it with the [polished seal](../examples/stipple.json).

```sh
node cli/ink-studio.js render examples/stipple.json --w 1024 --h 1024 --t 1.5
node cli/ink-studio.js clip examples/stipple.json --w 1024 --h 1024 --from 0 --to 3 --fps 24
node cli/ink-studio.js shimmer examples/stipple.json --mode still --t 0 --frames 15 --step 0.2
```

In JSON, set `finish.look.tone` to `"stipple"` or an object that overrides
preset settings. In JavaScript, pass the same `look` object to `B.finish()`.
The CLI can preview the preset on any scene with `--tone stipple`.
Use `--tone off` to switch to the scene's regular palette.

```json
{
  "finish": {
    "look": {
      "pixelSize": 2,
      "tone": {
        "preset": "stipple",
        "cutoff": 0.2,
        "stops": [[0, "#000000"], [0.22, "#176bfa"], [0.8, "#ff8d27"], [1, "#fff1cd"]],
        "pattern": "blue-noise",
        "seed": 17,
        "amount": 0.85,
        "preserveDots": true
      }
    }
  }
}
```

- `pixelSize` fixes the number of screen pixels per art pixel. At 1024 × 1024,
  a size of 2 produces a 512 × 512 art grid. The CLI uses nearest-neighbor
  enlargement. `--px` overrides the scene's size.
- `cutoff` maps luminance at or below that value to black. The renderer
  remaps the range above the cutoff to 0–1 before looking up `stops`.
  Provide 2–48 strictly increasing stops. Start with `[0, "#000000"]`
  and end at position 1. The stops define an output palette independent
  of the sculpt's material palette.
- `pattern` selects a repeating 4 × 4 `bayer` tile or the toolkit's
  `blue-noise` tile. The blue-noise `seed` changes the pattern.
  Both tiles are anchored to the top-left of the art grid.
  `amount` ranges from 0, a hard transition between stops, to 1, the full
  threshold pattern.
- `preserveDots` skips the scene's pixel cleanup by default. `--clean`
  explicitly enables cleanup. `--raw` bypasses the tone mapping.
  An enabled tone mode takes precedence over `--colored`.

Use the [surface light track](surface-materials.md#animate-the-finish-light) to
move the highlights between color bands. The threshold pattern stays fixed
across frames.

## Host integration

The [WebGL canvas renderer](browser-renderer.md) reads the world's `look.tone`.
Pass `tone` in the frame options to override the look, and set the canvas
drawing buffer dimensions to the desired art resolution. The headless
renderer derives that grid from its viewport and `look.pixelSize` or `--px`.

`PixelLook.prepareTone(settings, KIT.procedural.materials.blueNoise)`
returns the ordered stops, packed output palette, tile dimensions and an
array of normalized thresholds. Prepare it once per look. A CPU host can use
`PixelLook.toneIndex(prepared, r, g, b, x, y)` to look up a palette index.

A WebGL 2 host can include `PixelLook.toneGlsl` in its fragment shader and
call `inkToneResolve(litRgb, artPixel)` before enlargement. Pass normalized
lit RGB composited over black and integer art-pixel coordinates measured
from the top-left. Set `u_inkToneCount` to the number of stops,
`u_inkToneCutoff` and `u_inkToneAmount` to the prepared settings, and
`u_inkToneStops` to the normalized RGB colors with stop positions in alpha.
Upload the threshold array as an `R32F` texture with nearest filtering and
bind it to `u_inkToneRanks`.

## Palette remaps

Use `finish.look.paletteRemap` on a JSON diorama or `look.paletteRemap`
in `B.finish()`. The renderer selects a color from the original palette
with the usual lighting and dithering, then looks up its replacement.

```json
{
  "rules": [
    { "from": "stone.shadow", "to": "#16152e" },
    { "from": "#474d57", "to": "#424789" },
    { "from": 4, "to": "#6380ba" }
  ],
  "protect": [0, "signal", "beacon.highlight"]
}
```

`from` and `protect` accept zero-based palette indices, exact `#rrggbb`
swatches, full role names, and role stops such as `stone.shadow`,
`stone.midtone`, `stone.highlight`, or `stone.1`. A full role addresses
every entry in its ramp. For a ramp with an even number of stops,
`midtone` picks the lower middle stop. `to` accepts a packed RGB integer
or `#rrggbb` string. Rules always match the original palette. The last
rule for an entry wins, and protection restores the original color even
when an animation grade is active.

Role names refer to entries in the existing material ramps. Two surfaces
that share an entry receive the same color. JSON dioramas supply roles
from their style and `roles` table. For a custom JS builder, pass
`paletteRoles: { stone: [1, 2, 3] }` to `B.finish()` if needed.

The CLI and the WebGL renderer use the remap during scene palette
resolve. Stipple, projected layers with their own output palette, and
raw rendering use their own color paths. Pass `paletteRemap: false` to
a render call or `--palette-remap off` in the CLI to preview the base
palette. `K.fx.grade(stage).setRemap(definition, amount)` drives a stage
grade from JavaScript, with strength from zero to one.

```sh
node cli/ink-studio.js validate examples/palette-remap.json
node cli/ink-studio.js render examples/palette-remap.json --ortho --palette-remap off --out before.png
node cli/ink-studio.js render examples/palette-remap.json --ortho --out after.png
```

## Color ramps and channel curves

A ramp maps a scalar to an RGB color. Stops use the source's own units
and must increase strictly. Samples outside the stops use the nearest
endpoint. `step` holds each stop until the next. `linear` blends between
stops. `smooth` eases in and out between stops without overshoot.

Use `finish.look.colorCurves` in JSON or `look.colorCurves` in `B.finish()`.

```json
{
  "ramp": {
    "interpolation": "smooth",
    "stops": [[0, "#11172a"], [0.45, "#708b9f"], [1, "#fbe8cb"]]
  },
  "channels": {
    "blue": { "stops": [[0, 0.08], [0.5, 0.62], [1, 1]] }
  }
}
```

The scene ramp reads the luminance of each selected palette color.
You can use a ramp, channel curves, or both. Channel curves take inputs
and outputs in [0, 1]. Each uses its own channel, after the ramp when
present. Unspecified channels pass through. Animation grades feed into
the curves, and authored palette remaps and their protections apply last.
Stipple and raw output bypass the scene curves.

The library exposes `ColorCurves.scalar(definition)`,
`ColorCurves.ramp(definition)` and `ColorCurves.prepare(transfer)`
as reusable samplers. Standalone ramp colors accept six-digit hex,
packed RGB integers, or normalized RGB triples. Pass an output array
to a ramp sampler to reuse storage. The perceptual
`KIT.procedural.materials.ramp(anchors, options)` also accepts
`interpolation` and keeps its existing color space and default blend.
See [surface curves](surface-materials.md#color-curves-on-surfaces)
to bind a ramp to depth or a field.

## 3D color LUTs

A 3D LUT samples all three input channels together. Use one to shift
blue shadows toward violet while keeping an equally bright red in its
original hue.

```sh
node cli/ink-studio.js lut import examples/blue-shadow.cube --out blue-shadow.json
node cli/ink-studio.js render examples/rgb-lut.js --ortho --lut examples/blue-shadow.cube --out violet.png
node cli/ink-studio.js render examples/rgb-lut.js --ortho --lut blue-shadow.json --out from-json.png
node cli/ink-studio.js render examples/rgb-lut.js --ortho --lut off --out before.png
```

Import standalone 3D `.cube` tables with `LUT_3D_SIZE`, optional
`TITLE`, and either per-channel `DOMAIN_MIN` and `DOMAIN_MAX` or
`LUT_3D_INPUT_RANGE`. The CLI can print the native JSON to stdout.
Both formats store triplets with red varying fastest, then green,
then blue. [Adobe Cube specification](https://kono.phpage.fr/images/a/a1/Adobe-cube-lut-specification-1.0.pdf) · [Resolve range header reference](https://github.com/AcademySoftwareFoundation/OpenColorIO/blob/main/src/OpenColorIO/fileformats/FileFormatResolveCube.cpp)

This is an identity table in native JSON.

```json
{
  "format": "ink-studio/lut",
  "version": 1,
  "size": 2,
  "domainMin": [0, 0, 0],
  "domainMax": [1, 1, 1],
  "interpolation": "tetrahedral",
  "data": [
    0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0,
    0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1
  ]
}
```

Use `size³` RGB triplets in one flat array. The domain defaults to
[0, 1] on all three axes and out-of-domain inputs use the nearest
boundary. Choose `tetrahedral` (the default) or `trilinear`.
`ColorLUT.parseCube(text)` returns the same immutable JSON shape from
JavaScript, and `ColorLUT.prepare(definition).sample(rgb, out)` samples
it with an optional reusable output array. The sampler keeps finite
output values outside [0, 1], and the renderers clamp display colors.

Put a native definition in `finish.look.colorLut`, `look.colorLut`
in `B.finish()`, or `visual.look.colorLut` on a simulation manifest.
Scene LUTs run during palette resolve in the CLI and standard WebGL
renderer. They follow the animation grade and channel curves. Palette
remaps and protected swatches apply last. Raw output and stipple use
their own resolve paths. See [surface LUTs](surface-materials.md#3d-luts-on-surfaces)
to transform a material sample before compositing.

## Named color stacks

Use `finish.look.colorStack` in a JSON diorama, `look.colorStack`
in `B.finish()`, or `visual.look.colorStack` in a simulation manifest.
A stack has a `name` and ordered `steps`. Give a step an `id` to identify it
while editing. Set `enabled: false` to skip a step or set an `amount`
from zero to one to blend its result into the color entering that step.

```json
{
  "name": "Cool dusk",
  "steps": [
    { "id": "shade", "type": "exposure", "stops": -0.25 },
    { "id": "cool", "type": "hue", "degrees": 20, "amount": 0.6 },
    { "id": "lantern", "type": "paletteRemap", "remap": { "rules": [], "protect": ["glow"] } }
  ]
}
```

| Step type | Editable settings |
| --- | --- |
| `exposure` | `stops` scales RGB by `2 ** stops`. |
| `contrast` | `factor` scales each channel's distance from `pivot`, which defaults to 0.5. |
| `saturation` | `factor` scales the distance from luminance. Zero gives grayscale and one is neutral. |
| `hue` | `degrees` rotates the hue with the channel minimum and maximum held fixed. |
| `channelMix` | `matrix` contains RGB weights for each of the three output channels. Optional `offset` adds an RGB triple. |
| `curves` | `curves` takes the same luminance ramp or RGB channel curves as `look.colorCurves`. |
| `lut` | `lut` takes a native 3D LUT, including a JSON import from `.cube`. |
| `paletteRemap` | `remap` addresses the original palette slots by swatch, index, or role. Rules blend against the color at this point in the stack. Protected slots retain their original colors through the entire grade. |

The scene stack uses Ink Studio's working RGB values. The renderer clamps
the final stack color for display. Curves and LUTs use their own domains
when they sample an intermediate value. Palette resolution feeds the
animation grade, standalone curves and LUT, then the stack. A standalone
palette remap applies last, with protections from both definitions honored.
The CLI and WebGL share the same scene stack evaluation. Raw and stipple
output use their existing resolve paths.

The JavaScript bundle exposes `ColorStack.prepare(stack).sample(rgb, out)`
for RGB-only stacks. A [material stack](surface-materials.md#color-stacks-on-surfaces)
uses that same evaluation before compositing.

```sh
node cli/ink-studio.js render lab/data-shrine.json --t 4 --pitch .31 --yaw .55 --target 0,1.15,0 --color-stack off --out before.png
node cli/ink-studio.js render lab/data-shrine.json --t 4 --pitch .31 --yaw .55 --target 0,1.15,0 --color-stack examples/lantern-dusk.json --out dusk.png
```

The same `--color-stack` option works with `sim render`. A JSON file
overrides the authored scene stack. `off` bypasses scene and surface stacks.

## Color spaces and numeric ranges

Add `color` to a LUT, curves definition, palette remap, or stack step to
declare how that operation reads and writes RGB. Ink Studio converts its
working sRGB values into the declared input and converts the result from the
declared output back to working sRGB.

```json
{
  "color": {
    "input": { "space": "srgb-linear", "range": [16, 235], "outOfRange": "clamp" },
    "output": { "space": "srgb-linear", "range": [16, 235], "outOfRange": "preserve" }
  }
}
```

Each endpoint accepts `srgb`, `srgb-linear`, `display-p3`, or
`display-p3-linear`. Use a shared `[min, max]` or give each channel its
own bounds with `{ "min": [r, g, b], "max": [r, g, b] }`. The bounds
map to normalized zero and one in the declared space. `preserve` keeps
finite values beyond the bounds, `clamp` limits them to the bounds,
and `error` rejects them. Omitted endpoint settings default to `srgb`,
`[0, 1]`, and `preserve`. Definitions without `color` keep their
existing behavior. RGB conversions use the D65 matrices and extended
sRGB transfer functions in the [CSS Color 4 conversion reference](https://www.w3.org/TR/css-color-4/#color-conversion-code).

LUT entries, numeric ramp colors, RGB channel curves, and numeric remap
targets use the declared code values. A luminance ramp derives its scalar
from the input RGB. A material ramp driven by a scene field reads the
field in its own units. Hex colors and palette swatches are authored in
sRGB and converted as needed. The parametric stack steps use normalized
values in the declared spaces, so a contrast pivot of 0.5 stays at the
middle of the input range. A step's own `color` replaces the nested
definition's declaration for that step.

A LUT's table domain defines where the grid is sampled, independently of
the input encoding's numeric range. The sampler uses `domainPolicy` to
`clamp` to the grid by default, report an `error`, or `extrapolate`
with the nearest edge cell. Use `ColorLUT.prepare(lut).sample(rgb, out)`
to work directly in table values or `.apply(rgb, out)` to work in renderer
sRGB. Use `ColorSpace.convert(rgb, from, to)` to convert between descriptors
in JavaScript.

When importing `.cube`, supply the spaces and ranges the table was
authored for. The import stores them in the native JSON. Use
`--input-out-of-range` and `--output-out-of-range` to set the endpoint
policies. The CLI and standard WebGL scene renderer use the same
declarations.

```sh
node cli/ink-studio.js lut import examples/half-gain-legal.cube \
  --input-space srgb-linear --output-space srgb-linear \
  --input-range 16,235 --output-range 16,235 --domain-policy error \
  --out half-linear.json
node cli/ink-studio.js render examples/rgb-lut.js --ortho --lut half-linear.json --out linear.png
```

## Target palettes and dithering

Use `finish.look.paletteConstraints` on a JSON diorama, `look.paletteConstraints`
in `B.finish()`, or `visual.look.paletteConstraints` on a simulation manifest.
Each target chooses the swatches that can appear on its visible surfaces.
Background pixels and unselected surfaces use the scene resolve. Use an
optional `default` policy to cover foreground surfaces without a target.

```json
{
  "targets": [
    {
      "material": "foliage",
      "palette": ["#152a2a", "#234839", "#356449", "#4c8054", "#71a260", "#a0bf77"],
      "dither": { "pattern": "blue-noise", "strength": 0.85, "seed": 74 }
    },
    {
      "object": "courier",
      "material": "status",
      "palette": ["#9c343a", "#d84a43"],
      "reserved": ["#ff654e"]
    }
  ]
}
```

- A target matches its `object`, its `material`, or both. The last
  matching rule wins. In JSON dioramas, these names come from the solid's
  `part` or `id` and the material's role. JavaScript sculpts use
  `objectId` on the shape and `materialId` on the material. For direct
  splats use `B.describeSplats(first, end, { object, material })`.
  Simulation renders expose entity, body, and agent IDs, authored body
  materials, and material names such as `terrain` and `water`.
- Swatches accept hex colors, normalized RGB triples, scene palette
  indices, and named palette roles or stops. Omitting `palette` uses the
  scene swatches. `reserved` entries preserve exact matches at 8-bit RGB
  precision and stay out of ordinary quantization and dithering.
  A policy samples lit color by default. Use `source: "graded"` to
  sample the graded scene swatches before the final palette selection.
- `none`, `checker`, `bayer`, and seeded `blue-noise` set the threshold
  pattern. Strength 0 picks the nearest swatch. Increasing strength lets
  more art pixels pick the second swatch near a transition. CLI renders
  can use the existing screen, world, or object dither coordinates.
- Explicit target palettes take precedence over a surface layer's
  `outputPalette` in CLI renders. Layer palettes take precedence over
  `default`. Outlines and finish overlays use their existing paths.
  Standard WebGL targets use solid splat ownership and screen art pixels.

In JavaScript, `PixelLook.preparePalette(policy, { palette, roles, blueNoise })`
returns packed swatches and `index(rgb, x, y)` for sampling normalized
RGB at a chosen position. Pass `KIT.procedural.materials.blueNoise` when
preparing a blue-noise policy.

```sh
node cli/ink-studio.js render examples/palette-constraints.js --ortho --palette-constraints off --out before.png
node cli/ink-studio.js render examples/palette-constraints.js --ortho --out constrained.png
```

Use `--palette-constraints rules.json` to override the authored rules
in `render` or `sim render`. `off` bypasses the target policies.

## Look assets and overrides

An `ink-studio/asset-pack` can carry named `looks`, either on their own or
alongside geometry families. A look has a namespaced `id`, a `label`, and a
color `stack`, a `palette` policy, or both. Declare named JSON defaults in
`params`. Use `{ "$param": "name" }` for values in the stack or palette
policy. Packs and bundles carry the look data as JSON, including any LUTs
in the stack.

Bind a look by its ID or use an object to pin the pack revision and
override one use of the look. A pin must match the installed revision.
Without a pin the binding follows the installed pack.

```json
{
  "asset": "relay/glazed-enamel",
  "revision": 1,
  "strength": 0.88,
  "params": { "shadow": "#4d2435", "mid": "#ae5653", "highlight": "#f4bc86" },
  "palette": ["#4d2435", "#783747", "#ae5653", "#d48562", "#f4bc86"]
}
```

Strength blends the whole completed stack. A strength of zero bypasses the
look. At any positive strength the palette remains a discrete constraint.
A swatch list replaces the asset's swatches while keeping its dither and
reserved settings. Use `palette: false` to omit the palette, or use
`false` as the binding to omit the look. Parameter overrides must use
declared names and match the JSON types of the defaults.

- Set `finish.look.asset` on a JSON diorama or `visual.look.asset` on a
  simulation world. The look supplies the scene stack and a default
  foreground palette, with inline scene settings taking precedence.
  When the asset supplies both, the stack grades the source swatches
  before quantization. The CLI and standard WebGL scene renderer use
  the resolved look.
- Set `mat.lookAsset` on a JSON diorama material or `visual.lookAsset`
  on a simulation entity. The look runs after its other surface layers
  in the CLI. Simulation terrain also accepts `visual.terrainLookAsset`.
  Material evaluation is available to custom hosts via `SurfaceLook`.
  Indexed palette remap steps need a scene binding.
- Set `lookAsset` on a prefab to give its rendered descendants a
  shared look. Pass a partial `lookAsset` in stamp arguments to override
  that instance. An entity with its own binding takes precedence.
  Capturing an assembly preserves the instance binding.

Add installed packs to `assetPacks` in the scene or world, or install
a pack or bundle for a CLI invocation using `--asset-pack`.
`scene stamp` carries the installed pack in the resulting world so it
can be rendered and checkpointed independently.

```sh
node cli/ink-studio.js render examples/look-assets.json \
  --asset-pack examples/relay-look-pack.json --ortho --out relay.png
node cli/ink-studio.js scene stamp examples/look-prefabs.json relay \
  --asset-pack examples/relay-look-pack.json --as north \
  --args '{"lookAsset":{"strength":0.65}}' --out placed.json
node cli/ink-studio.js sim render placed.json --out placed.png
```

JavaScript hosts can create a catalog with
`KIT.authoring.assetPacks.create({ packs })`. Pass it to
`KIT.authoring.looks.scene(look, catalog)` before `B.finish()`, or use
`KIT.authoring.looks.material(base, binding, catalog)` when defining a
material. `looks.bind(binding, catalog)` returns the resolved immutable
stack and palette. Use `assetPacks.bundle` to share packs and
`assetPacks.reviseLook` to publish a new revision.

## Import and export looks

`look import` wraps a standalone 3D LUT, color stack, or palette in an
installable JSON asset pack. Use `--id pack/look` to name the asset and
`--label "Display name"` to set its label. Existing JSON packs and
bundles keep their IDs, revisions, parameters, and bindings. The
import accepts the same LUT color-space, range, and domain-policy
options as `lut import`.

```sh
node cli/ink-studio.js look import examples/blue-shadow.cube \
  --id color/blue-shadow --out color-pack.json
node cli/ink-studio.js look export color-pack.json \
  --out blue-shadow.cube --exact
node cli/ink-studio.js look export examples/relay-look-pack.json \
  --look relay/glazed-enamel --size 33 --out enamel.cube --report enamel-report.json
```

`look export` infers the target from `--out`. Omit the path and
use `--format json|cube|gpl|pal|hex` to write conversion data to stdout.
For external formats, use `--look pack/look` to select an asset from
a multi-look pack or bundle and `--params '{"name":value}'` to supply
overrides.

- **3D LUTs.** Compatible tables retain their RGB rows and input domain.
  Other continuous stacks are sampled into a normalized sRGB grid.
  Choose a grid edge length of 2–65 using `--size` (default 33) and
  optionally set per-channel bounds with `--domain-min r,g,b` and
  `--domain-max r,g,b`. The default is the unit cube or the original
  domain of a standalone sRGB LUT. The destination application chooses
  its own interpolation and behavior outside the domain.
- **Palettes.** Supported text formats are GIMP `.gpl`, JASC-PAL 0100
  `.pal`, and `.hex` with one six-digit RGB swatch per line. Native JSON
  can also supply a swatch array or a palette constraint. Use
  `--swatches reference.gpl` to evaluate a stack at those swatches or
  resolve palette indices. Scene role names need their scene's role
  definitions. Native looks support up to 48 swatches.
  [GIMP palette format specification](https://developer.gimp.org/core/standards/gpl/)

The summary goes to stderr. Save the full JSON report with `--report`.
It marks the conversion as `exact`, `lossy`, or `sampled` and lists any
omitted settings or metadata. RGB grid reports measure maximum channel
error and RMSE at cell midpoints using Ink Studio's interpolation.
Palette sampling reports 8-bit clipping and rounding. Use `--exact`
to reject lossy or sampled conversions before the output is written.

## Bake a static color stack

`look bake` produces an installable asset bundle containing the
editable original and a compiled sibling in a separate pack. Existing
pack IDs and revisions are preserved. Select the sibling with
`--look pack-baked/look` when rendering or exporting, or name it
explicitly with `--as new-pack/look`. Parameter overrides passed with
`--params` are fixed in the bake. Re-bake from the editable source
after editing the look or changing those parameters.

```sh
node cli/ink-studio.js look bake examples/relay-look-pack.json \
  --look relay/glazed-enamel --format lut --size 33 \
  --out enamel-bundle.json --report enamel-error.json
node cli/ink-studio.js render examples/look-assets.json \
  --asset-pack enamel-bundle.json --look relay-baked/glazed-enamel --out enamel.png
node cli/ink-studio.js look export enamel-bundle.json \
  --look relay-baked/glazed-enamel --out enamel.cube
```

- `--format palette` bakes an unstaged stack into an indexed remap
  for the ordered `--swatches` palette. Supply `--roles roles.json`
  when the source uses named palette roles. The bake tests every
  source swatch and preserves protection. Ink Studio uses the
  editable stack when the palette, roles, or original sample color
  differs from the bake's reference.
- `--format lut` samples a continuous RGB stack on a grid. The
  default edge length is 33. Set `--size` and optional per-channel
  `--domain-min` and `--domain-max` to change it. Ink Studio evaluates
  the editable stack outside the sampled domain. Exporting a
  sampled bake to `.cube` copies the table and reports the measured
  source error and the loss of that fallback.

`auto` uses a palette remap when an unstaged look has a reference
palette and no grid options. Use explicit hex or RGB ramp stops in
bakeable looks because numeric stops depend on the render context.
The bundle and optional JSON report record maximum channel error
and RMSE in normalized sRGB. LUT measurements use cell midpoints.
`--max-error` rejects a bake that exceeds the measured channel
tolerance, and `--exact` requires an exact representation.

## Profile looks and check renderer parity

```sh
node cli/ink-studio.js look profile --renderer both --frames 60 --warmup 5 \
  --splats 256 --w 160 --h 100 --out look-profile.json
node cli/ink-studio.js look parity --out look-parity.json
```

The profiler renders identical geometry and views with no look, a
global LUT, and a scoped palette. The JSON report includes fixture
construction, renderer initialization, first-frame time, and a
separate measurement of look planning and target assignment. First-frame
time includes each renderer's lazy setup. Warmed frame timings include
p50, p95, min, max, and mean, with deltas from the no-look case.
WebGL waits for submitted work to finish each frame. It averages up
to four consecutive frames per timing sample to improve precision on
fast GPUs. Set `--batch 1` for individual WebGL frame timings. Pixel
readback runs only during parity checks.

The parity command samples matching pixels in both renderers. Fixtures
cover tetrahedral and trilinear LUT interpolation, linear-light
conversion through a declared numeric range, scoped palette selection,
spatial mask blending, and overlapping glass. Reports include both RGB
values, the expected sample colors, and the maximum absolute difference
in 8-bit channel values. The spatial mask and per-splat glass cases use
control renders to identify known WebGL gaps. Unexpected differences
exit with status 1. Add `--strict` to fail on known gaps as well.

Profiling defaults to the headless renderer. WebGL runs require Chrome
or Chromium. Use `--chrome` or `INK_TEST_CHROME` to select an executable.
WebGL uses SwiftShader by default. Pass `--hardware` to let Chrome choose
its normal backend and check the graphics driver recorded in the report.

## Inspect and validate looks

`look inspect` accepts a scene, simulation world, saved checkpoint, run
recording, or standalone look file. It reports authored rules in JSON with
their stages, masks, asset and field dependencies, and matched targets.
Inspecting a scene uses baked target IDs and counts from the same index
as `inspect --select` and `probe`. Driven rules also show the parameters
and strength sampled at that time or tick.

```sh
node cli/ink-studio.js look inspect examples/driven-look-forge.json --ticks 32
node cli/ink-studio.js look inspect examples/relay-look-pack.json --look relay/glazed-enamel
node cli/ink-studio.js validate examples/render-stages.js --renderer headless
node cli/ink-studio.js validate examples/shared-look-selectors.js --renderer webgl
node cli/ink-studio.js validate examples/blue-shadow.cube
```

Use `--renderer headless` (the default) or `--renderer webgl` to check
compatibility. The report lists explicit stages and surface look layers
that WebGL cannot evaluate, along with spatial masks, unsupported media,
and coverage-aware compositing. `validate` exits nonzero for invalid
bindings, including malformed LUTs, missing scene swatches, and selectors
with no eligible targets at the inspected tick.

Standalone packs report named parameters, pack revisions, and palette
references. Scene validation resolves those references against the
palette and roles of the consuming scene. Use `--asset-pack` to supply
external packs for a JSON scene and `--out` to save an inspection report.
JavaScript callers can use `query.inspectLook({ renderer: 'webgl' })`.

## Apply look bindings with scene patches

Use `bind-look` in a `scene apply` patch to attach a named look to a
shared target selector. Select by material, surface, entity, prefab
instance, tag, or a combination. A binding accepts an asset ID or the
usual object with parameters, strength, stage, and other overrides.

```json
[
  {
    "op": "bind-look",
    "select": { "surface": "west-enamel" },
    "binding": { "asset": "relay/glazed-enamel", "params": { "mid": "#ae5653" } }
  }
]
```

The same selector replaces the existing rule in place. Set `binding`
to `null` to remove it. If several authored rules use the same selector,
edit the specific rule by path. Ordinary `set`, `merge`, and `remove`
operations also support scene-wide and per-instance bindings, such as
`/visual/look/asset` and `/entities/west/lookAsset` in a world, or
`/finish/look/asset` and `/solids/0/mat/lookAsset` in a JSON diorama.

Add `--dry-run` to preview the changed paths and affected material,
surface, entity, and instance IDs. The preview compares the bindings
matched by the starting and edited scenes, so it includes targets that
lose a binding. Edits are checked together against the final scene.
Supply `--asset-pack` to install a pack in the saved result and
`--renderer webgl` to check WebGL compatibility.

## Sample colors and probe a scene

Use `look sample` with a LUT, color stack, palette, or look asset. Pass a
JSON array of hex colors and RGB triples in normalized sRGB units, or
use `--chart` for a set of grays, hues, shadows, and highlights. JSON
results include the input, transformed RGB, and selected swatch when
the look quantizes the color. Save a PNG to see each input on the left
and the corresponding result on the right.

```sh
node cli/ink-studio.js look sample examples/blue-shadow.cube \
  --colors '["#182c55",[0.8,0.1,0.05]]'
node cli/ink-studio.js look sample examples/relay-look-pack.json \
  --look relay/glazed-enamel --chart --out enamel-chart.png
node cli/ink-studio.js probe examples/wet-spillway.js \
  --select '{"surface":"spillway-wall"}' --at 1,0.55,0
```

Standalone sampling accepts `--params` for look assets and `--swatches`
to supply a reference palette for indexed looks. Indexed RGB samples
use the nearest reference swatch. Use `--at` or `--rest` to evaluate a
standalone axis or texture mask in its declared space. Without a
position or scene field, the standalone sampler shows the full
look and reports an unknown mask weight.

`look/sample` reads an actual baked splat from the scene or saved
simulation tick. `--at` selects the nearest matching splat center,
and `--radius` bounds the search. Use `--entity` or `--select` to
restrict the search. With no point, `--field look/sample` picks the first
matching splat. The result gives the material, baked RGB, sampled
positions, matched looks and mask weights, and the resulting RGB for
that isolated splat. A continuous color or a blend between swatches
has `swatch: null`. Art pixel coordinates for palette dithering can
be passed in `--args '{"pixel":[8,7]}'`. Use `look/output` to supply
your own RGB for an individual stage.

## Render look previews and diagnostic passes

`render`, `sheet`, and `clip` accept `--look pack/look` to preview a
named asset in place of the scene-wide color look. Supply the pack
with `--asset-pack` or use an asset already installed in a JSON scene.
Use `--look-select JSON` to apply the asset only to matching targets.
`--look-params JSON` and `--look-strength N` override that binding.

`--look file.json` accepts a scene look object with fields such as
`asset`, `targets`, `renderStages`, or `paletteConstraints`. Fields
you supply replace the corresponding scene settings for the preview.
With an `asset` binding the preview starts with a fresh scene-wide
color look. `--look off` bypasses authored scene and surface color
looks for a baseline.

```sh
node cli/ink-studio.js render examples/wet-spillway.js \
  --passes target,mask,materialId --out spillway.png
node cli/ink-studio.js sheet examples/look-assets.json \
  --asset-pack examples/relay-look-pack.json --look relay/glazed-enamel \
  --look-select '{"entity":"sea-glaze"}' --t 0,0.5,1 \
  --passes target,materialId --out relay-sheet.png
node cli/ink-studio.js clip examples/look-blending.js \
  --to 1 --fps 12 --passes mask --out runoff.png
```

Each pass is saved beside the color output with the pass name in its
filename. Sheets use the color sheet's time grid. Clips write an
animated PNG for each pass at the same frame rate. The `-passes.json`
file lists the outputs and maps false colors to the bindings and
material IDs. See [art pass formats](art-passes.md).

## Compare looks on a fixed view

Give `compare` a case file with two or more entries. The first is the
baseline. A row with only an ID uses the authored scene look. A row's
`look` can be an asset binding with strength, parameters, and palette
overrides, an inline scene look object, a look JSON file relative to the
case file, or `"off"`.

```json
[
  { "id": "authored" },
  { "id": "softer", "look": { "asset": "relay/glazed-enamel", "strength": 0.45, "select": { "entity": "sea-glaze" } } },
  { "id": "warmer", "look": { "palette": ["#391e21", "#ad603f", "#f0bc86"], "select": { "entity": "sea-glaze" } } }
]
```

```sh
node cli/ink-studio.js compare examples/look-assets.json --looks cases.json \
  --asset-pack examples/relay-look-pack.json --t 0 --ortho \
  --out comparison.png --report comparison.json
node cli/ink-studio.js sim sweep checkpoint.json cases.json \
  --asset-pack examples/relay-look-pack.json --out comparison.json
```

Every case renders the same baked scene and camera. For a simulation,
the cases share one saved tick, or a tick chosen with `--ticks`. Common
simulation actions can be passed with `--actions`. Put the camera and
render settings on the command.

The report includes changed-pixel counts and signed and absolute RGB
deltas in 8-bit channel units. It groups the results by visible scene
target and by the dominant look binding. Pixels without a solid owner
are grouped under `target: null`. Cases that switch render stages can
change palette resolution across the frame.

Clipping tracks out-of-range samples at renderer clamp sites and lists
clipped palette inputs separately. Swatch usage counts exact RGB
matches in the saved color frame after blending and masks.
`swatches.unused` lists available swatches with zero matches.

## Per-object detail budgets

Set `finish.look.detailBudgets` in a JSON scene or pass `{ detailBudgets }`
as the third argument to `makeBuilder(seed, palette, options)` in JavaScript.
The builder carries the rules into the finished scene. Each rule has a
`select` using `object`, `entity`, or `tag`. The first matching rule
supplies the settings for that subject. Omitted settings use the scene defaults.

| Setting | Effect |
| --- | --- |
| `spacing` | Multiplies each selected solid's sampling spacing during the bake. The range is 0.25 to 4. Smaller values create more splats. Blended solids can contribute samples to a shared surface. |
| `fine` | Enables or disables baked 4 × 4 surface color tiles for the subject. Enabling it needs a bake. Disabling it also suppresses existing tiles for matching splats in both renderers. |
| `cleanup` | Enables or disables pixel cleanup on pixels owned by the subject, independently of scene-wide cleanup. |
| `protectSilhouette` | Preserves the subject's visible outer edge and adjacent fringe during cleanup, while allowing cleanup inside the shape. |

JSON solids use `id` for `entity`, `part` or `id` for `object`, and
`tags` for tag matching. JavaScript solids use `objectId` and
`target: { entity, tags }`. Native splats created directly can supply labels
with `builder.describeSplats`. Template spacing is resolved on the source
solids when the template is baked. Placed copies can have independent fine-tile
and cleanup settings through `objectId` and `target`. Raw rendering skips
scoped cleanup and fine-tile overrides.

The browser renderer expands shared GPU instance groups when scoped cleanup
or fine-tile rules need to resolve their individual splats. Spacing-only rules
apply at bake time and can use the shared instance path.

## Material-specific pixel styles

Set `pixelStyle` on a JavaScript sculpt material or inside a JSON solid's
`mat` object. Each setting is optional.

| Setting | Effect |
| --- | --- |
| `edgeHardness` | Controls the coverage transition of solid splats. Use 0 for a broad soft edge and 1 for a sharp cutoff. |
| `dither` | Selects `bayer`, `checker`, or `diagonal` interpolation between neighboring ramp shades on the art-pixel grid. `none` uses discrete ramp shades. |
| `highlight` | Shapes the baked highlight as a `spot`, `streak`, or `rim`. An object with `shape` and `strength` sets a strength between 0 and 1. The default strength is 0.75. |
| `shadeSteps` | Limits lighting to 2–64 evenly spaced steps in the material's ramp, up to the number of available swatches. |

Highlights use the sculpt's light and view direction at bake time.
Headless and WebGL renders apply the authored coverage and ramp dithering.
Raw views keep the baked shading and bypass those two render-time controls.
The separate scene-wide palette dither still applies at palette resolve.
Explicit texture colors and fine tiles keep priority over ramp dithering.

## Shared look selectors

Use `finish.look.targets` in a diorama, `visual.look.targets` on a world,
or pass the same look object to `KIT.authoring.looks.scene` in JavaScript.
Each rule binds an asset to a selector. The last matching rule wins.

```json
{
  "targets": [
    {
      "select": { "tag": "paint-sample", "material": "bone" },
      "asset": { "asset": "relay/glazed-enamel", "strength": 0.8 }
    }
  ]
}
```

Selectors combine exact names. Every supplied field must match.
Use `inspect <scene> --targets` to list the names in a scene or snapshot.

| Field | Name to use |
| --- | --- |
| `entity` | Scene solid ID or simulation entity ID, such as `west.box`. |
| `material` | Scene material role, authored material ID, or a simulation entity's `visual.material`. |
| `surface` | A solid's `surfaceId`, an entity's `visual.surfaceId`, or a bound surface settings ID. |
| `prefab` | A placed assembly ID. Rendered descendants also match. |
| `tag` | A value from a solid or simulation entity's `tags` list. |
| `medium` | A named atmosphere volume, a water body ID, or a simulation water field ID. |
| `mediumKind` | A medium kind, such as `water` or a volume type such as `sphere`. |

Use the same `select` object in `paletteConstraints.targets` to supply a
palette or stack directly. Existing `object` and `material` rules keep
their original syntax. JavaScript sculpts can pass `target` metadata in
the shape options or in `B.describeSplats`. Use `entity`, `surface`,
`tags`, `prefabs`, `medium`, and `mediumKind` to describe the splats.

Scoped stacks grade the source scene swatches before an optional target
palette. The CLI and standard WebGL use the same selectors for splats.
Atmosphere volume tints resolve in the CLI and native water optics
resolve in WebGL. Optical tints use the selected color without dithering.

```sh
select='{"tag":"paint-sample","material":"bone"}'
node cli/ink-studio.js inspect examples/shared-look-selectors.js --select "$select"
node cli/ink-studio.js validate examples/shared-look-selectors.js --select "$select"
node cli/ink-studio.js probe examples/shared-look-selectors.js --select "$select" \
  --args '{"rgb":[0.6,0.6,0.6],"pixel":[8,7]}'
```

JavaScript callers can use `query.select(select)` and
`query.probe('look/output', select, args)`. The probe reports the matched
IDs, winning rule, and output swatches. Supply normalized shaded RGB and
optional art pixel coordinates to sample the look's palette resolve
without a viewport. A selector with no matches reports `missing`. Validation
checks against the requested scene or simulation tick.

## Spatial and field masks

Give a look asset or its binding a `mask` to blend the finished look over
the underlying surface color. A binding can replace the asset's mask or
set `mask: false` to use the look across the entire target. A selector
rule can also supply its own `mask`.

```json
{
  "select": { "surface": "spillway-wall" },
  "asset": "spillway/damp-stone",
  "mask": { "type": "query", "field": "runoff/wetness", "space": "world", "range": [0.02, 0.9] }
}
```

| Mask type | Scalar source |
| --- | --- |
| `axis` | Distance along `axis` from `origin`. Use `x`, `y`, `z`, or an XYZ vector. |
| `query` | A numeric scene query field. Optional `path` selects a value inside a record, `args` passes query arguments, and `fallback` supplies a value for unavailable samples. |
| `field` | A named projected field and `channel` in `surfaceEffects.fields`. |
| `texture` | An alpha, red, green, blue, or luminance channel in an existing RGB or RGBA `raster` frame set. Optional two-component `scale` and `offset` place one texture repeat. |

Projected fields and textures use the existing plane, cylinder, or
ribbon `projection`. `space: "world"` anchors the mask in the scene.
`space: "rest"` attaches it to the surface's rest coordinates so it
travels with a moving part. Queries default to world space. The other
masks default to rest space.

`range` maps the sampled scalar to a weight between zero and one. The
default interpolation is `smooth`, with `linear` and `step` also
available. Use `invert` to reverse the weight. A missing query sample
contributes zero weight unless it has a numeric fallback. At zero
weight the renderer uses the underlying color, and at one it uses the
full looked color. Intermediate weights can introduce colors between
the base and target swatches.

Use `probe --select` with an `at` world point or `rest` point inside
`--args` to report the mask weight. Supply `rgb` to sample the blended
output and optional `base` RGB to specify its underlying color.

```sh
node cli/ink-studio.js render examples/wet-spillway.js --ortho --look-masks off --out dry.png
node cli/ink-studio.js render examples/wet-spillway.js --ortho --out damp.png
node cli/ink-studio.js probe examples/wet-spillway.js --select '{"surface":"spillway-wall"}' \
  --args '{"at":[1,0.55,0],"rgb":[0.65,0.65,0.65],"limit":1}'
```

The CLI resolves masked bindings on splats at their sampled surface
positions. JavaScript renderer hosts can evaluate the same masks with
`KIT.splatEffects.prepareMask(settings, context)`. Standard WebGL
currently evaluates unmasked look rules.

## Explicit render stages

Set `finish.look.renderStages` on a diorama, `visual.look.renderStages`
on a simulation world, or `look.renderStages` on a built JavaScript scene.
Use a color stack at `material`, `lit`, or `frame`, and a palette policy
at `palette`. The headless renderer runs these stages in fixed order.

| Stage | Input |
| --- | --- |
| `material` | Base paint before lighting. Sculpt materials use `albedo` (a palette index, hex swatch, or normalized RGB triple) or the last swatch in their authored ramp. The renderer carries the baked ramp's light response onto the new paint and then adds runtime surface lighting. |
| `lit` | The shaded splat or surface fragment, including its highlights, before it blends into the scene. |
| `frame` | The resolved frame after compositing, including the background, ink, and art effects. |
| `palette` | The graded frame. The palette policy picks the final swatches, with optional dithering and reserved colors. |

```json
{
  "renderStages": [
    {
      "stage": "material",
      "select": { "material": "steel" },
      "stack": {
        "name": "Cobalt",
        "steps": [{
          "type": "channelMix",
          "matrix": [[0.52, 0.05, 0], [0.12, 0.67, 0], [0.25, 0.18, 0.66]],
          "offset": [0.025, 0.075, 0.22]
        }]
      }
    },
    {
      "stage": "palette",
      "palette": {
        "palette": ["#131d33", "#38537d", "#77a6c6", "#dce9df"],
        "dither": { "pattern": "bayer", "strength": 0.65 }
      }
    }
  ]
}
```

A versioned look asset can declare a default `stage`. A binding or a
`look.targets` entry can override it. If the asset contains a stack and a
palette, the stack runs at its assigned stage and the palette runs at
`palette`. Assigning `palette` directly uses just the asset's palette.
Matching rules within a stage can be [ordered and blended](#stack-order-and-blending).

The stages share [look selectors](#shared-look-selectors) and
[spatial masks](#spatial-and-field-masks). Material masks use the splat
center, or the surface hit when a per-pixel pattern is resolved. Lit
masks follow the fragment hit when a normal is available. Scoped frame
and palette rules use the visible splat owner's metadata. Unscoped,
unmasked frame rules also reach pixels without an owner. Palette masks
gate quantization at 50% coverage, so affected pixels remain exact
swatches. The `look/output` probe reports matched stage rules. To sample
one stage, supply `stage` and the RGB entering that stage in `--args`.

JavaScript sculpt builds can set `S.captureAlbedo = true` before baking
if a scene-level material rule will be applied. JSON dioramas and
simulation views capture it automatically. Use
`B.describeAlbedo(first, end, color)` for a baked range of custom splats.
For direct splats without a separate albedo, their packed RGB is treated
as the base paint. The plain JavaScript bundle exposes `RenderStages`
for custom hosts. The standard WebGL renderer still uses its existing
palette path.

Explicit rules opt the CLI and software renderer into continuous RGB
through frame grading, followed by quantization only when a palette
stage is present. Use staged bindings for any scene stack and palette
you want in this pipeline. Indexed remaps and the legacy tone and
coverage palette resolves use the legacy pipeline. `--raw` bypasses
authored stages. `--look-masks off` bypasses masked rules.

```sh
node cli/ink-studio.js render examples/render-stages.js --ortho \
  --params '{"stage":"material"}' --out material.png
node cli/ink-studio.js render examples/render-stages.js --ortho \
  --params '{"stage":"lit"}' --out lit.png
node cli/ink-studio.js render examples/render-stages.js --ortho \
  --params '{"stage":"frame"}' --out frame.png
node cli/ink-studio.js render examples/render-stages.js --ortho \
  --params '{"stage":"palette"}' --out palette.png
```

## Stack order and blending

Give a render stage rule an integer `order` (default `0`) and a
`weight` from `0` to `1` (default `1`). Lower orders run first within
each stage. At equal orders the inline scene rules run in declaration
order, followed by the scene's `look.asset`, its `look.targets`, and
then the material's rules in their declaration order.

Each RGB rule receives the previous rule's output. It transforms that
color and blends the result back over its input in working sRGB. The
effective weight is the rule's weight multiplied by its mask coverage
and the color stack's `amount`. When using a look asset, binding
`strength` is already folded into that amount. Palette rules apply in
the same order, quantizing when weight times mask coverage reaches
`0.5`. Their output is an exact swatch.

Use either an inline stack or an asset reference in a scene's
`renderStages`. A named look can set default order and weight in its
pack. The asset binding can override them, and fields on the outer rule
take precedence. Asset rules in `renderStages` default to `lit` if the
asset and binding leave the stage unspecified. Giving a scene, target,
or material binding an explicit order or weight also opts that binding
into stages. Legacy bindings use their existing palette pipeline.

```json
{
  "renderStages": [
    { "asset": "spillway/sandstone", "select": { "surface": "spillway-wall" }, "order": 10, "weight": 0.85 },
    { "asset": "spillway/runoff", "select": { "surface": "spillway-wall" }, "order": 20, "weight": 0.9 },
    { "asset": "spillway/blue-hour", "stage": "frame", "weight": 0.75 }
  ]
}
```

The `look/output` probe lists matching rules in evaluation order. With
`stage` and `rgb`, the requested stage shows each rule's effective
weight, input RGB, full transformed RGB, blended output, and whether
the rule applied. Supply `at` for world-space masks and `rest` for
rest-space masks. A mask with no sample position is reported as
unknown and its rule is skipped in the trace.

```sh
node cli/ink-studio.js probe examples/look-blending.js --select '{"surface":"spillway-wall"}' \
  --args '{"stage":"lit","at":[1,0.55,0],"rgb":[0.65,0.65,0.65],"limit":1}'
node cli/ink-studio.js render examples/look-blending.js --ortho \
  --params '{"variant":"layered"}' --out layered.png
node cli/ink-studio.js render examples/look-blending.js --ortho \
  --params '{"variant":"reversed"}' --out reversed.png
```

## Coverage-aware grading

Set `finish.look.coverageAware` on a diorama or
`visual.look.coverageAware` on a simulation world to `true`, or pass
`--coverage-aware on` to `render` or `sim render`. This applies scoped
looks and local palettes at
each splat's shaded contribution. A glass look changes the pane's RGB
at its own opacity. The visible objects behind it contribute their own
graded colors. Masks are sampled at each contribution's surface point.
The blend can contain RGB values between the authored swatches. The
`look/output` probe reports the sampled contribution color. Supply
`rgb` and a point for a masked rule.

The `material` and `lit` render stages already grade contributions
independently. In the CLI and software renderer, both paths retain
translucent layers in front of per-pixel patterns and apply glass
refraction to the backdrop contribution. Use a `frame` rule to grade
the resolved image or a `palette` stage to quantize the final blend.
These coverage-aware paths use the software renderer.

```sh
node cli/ink-studio.js render examples/coverage-aware-glass.js --ortho --out glass.png
node cli/ink-studio.js render examples/coverage-aware-glass.js --ortho \
  --params '{"glass":"clear"}' --out clear.png
```

## Animation and simulation inputs

A look asset binding can drive its strength and named parameters
with an `inputs` object. This works in scene, target, material, and
optical bindings. Give the asset defaults for each driven parameter,
then use `inputs.params` to say where its value comes from.

```json
{
  "asset": "forge/hot-steel",
  "strength": 0,
  "inputs": {
    "strength": { "source": "signal", "port": "heater/value" },
    "params": {
      "red": {
        "source": "query",
        "field": "forge/temperature",
        "target": { "entity": "billet" },
        "keys": [[20, 0.08], [420, 0.52], [1080, 0.88]]
      }
    }
  }
}
```

- `time` reads elapsed render seconds, such as CLI `--t`.
- `signal` reads a typed port or its public alias through `world/signal`.
- `query` uses the same field name and arguments as `probe`. Set an
  optional `target` point or entity/socket selector, `args`, and a
  `path` through a returned record or array.

Use `keys` for an input-to-value mapping. Keys are strictly increasing
in their first column. Linear interpolation is the default for numbers.
Set `interpolation: "step"` for discrete values, including boolean,
color strings, or JSON arrays. Values hold at the ends of the table.
Without keys, the source value supplies the parameter directly.
Missing reads and values of the wrong type use the binding's static
value or the asset default. Strength is clamped to `[0, 1]`. A driven
palette strength multiplies the palette rule's coverage weight.

A driven binding with no stage uses `lit`. Use `stage: "frame"` for a
whole-frame grade. Simulation rendering samples the clock, signals, and
fields from the rendered tick. Previewing other frames in between
does not affect these values. The `look/output` probe lists the sampled
strength and parameters under each rule's `inputs`. Driven optical
water also works in WebGL with the bundled render-stage toolkit.

```sh
node cli/ink-studio.js sim run examples/driven-look-forge.json \
  --actions examples/driven-look-forge-actions.json --ticks 64 --checkpoint hot.json
node cli/ink-studio.js sim render hot.json --w 1800 --h 1240 --out forge-hot.png
node cli/ink-studio.js probe hot.json --select '{"surface":"heated-workpiece"}' \
  --args '{"stage":"lit","rgb":[0.6,0.6,0.6]}'
```

## Material and surface provenance

Use stable names in a selector across bakes. A JSON diorama solid can
supply `surfaceId` and `mat.materialId`, including on a material
defined with an inline ramp. A simulation entity uses
`visual.surfaceId` and `visual.materialId` or `visual.material`.
When stamping a prefab, an instance keeps its own entity ID and the
local surface and material names. Appearance overrides can change
the finish independently.

JavaScript sculptors can set `surfaceId` on a solid or its material
and `materialId` on the material. The solid's surface name takes
precedence. If a top material supplies its own material ID, the baked
samples on that material carry it. For direct splats, use
`B.describeSplats(first, end, { object, material, target: { surface } })`.

The native buffer stores integer slots locally. Their meanings come
from dictionaries that carry the authored names. Use
`KIT.procedural.splatProvenance.join(chunks, sceneSettings)` to assemble
static native splat chunks with one palette. It remaps those local slots,
including bound surface settings and pixel patterns. Joining chunks
also retains normals, albedo references, and sample IDs when present.
The biome compiler uses the same assembly path and publishes each
terrain stratum's material on the `terrain` surface. Set
`renderMetadata: false` when requesting geometry without provenance.

`KIT.procedural.lod.packSplats` preserves the names in reduced records.
Use `lod.reduceWorld(world, options)` for static native bakes. Different
owners, materials, surfaces, and authored target scopes stay in their
own groups. Samples with individual surface shaders, per-pixel
patterns, or animation flags keep their exact rows. Interactive
representatives likewise keep their original indices and respect
provenance boundaries. Native previews may change the sample count
and surface detail.

Use `query.probe('look/provenance', selector)` or the CLI equivalent to
read stable IDs and splat counts. The same selector can also diagnose
a look with `look/output`.

```sh
node cli/ink-studio.js probe examples/provenance-relays.js \
  --params '{"variant":"lod"}' --field look/provenance \
  --select '{"prefab":"east","surface":"housing","material":"enamel"}'
node cli/ink-studio.js render examples/provenance-relays.js --ortho \
  --params '{"variant":"lod"}' --out reduced.png
```

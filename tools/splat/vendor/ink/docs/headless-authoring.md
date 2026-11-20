# Headless procedural authoring

These APIs are available through `KIT.procedural` in Node and the browser bundle. Graph specifications are JSON data. Register executable operations in host code and share their typed inputs and outputs with the specification.

For image review and export, pass the finished world to Node's CPU `render()`. For interactive review, pass the world and authoring toolkit to the [WebGL canvas renderer](browser-renderer.md).

## Edit generated parts from the CLI

From the checkout, inspect the [editable passage](../examples/editable-passage.js)
and try its [edit batch](../examples/editable-passage.edits.json).

```sh
node cli/ink-studio.js authoring inspect examples/editable-passage.js --part '@/wall/parts/doorway'
node cli/ink-studio.js authoring preview examples/editable-passage.js examples/editable-passage.edits.json --image passage-preview.png
node cli/ink-studio.js authoring apply examples/editable-passage.js examples/editable-passage.edits.json --out passage.json
node cli/ink-studio.js render examples/editable-passage.js --authoring passage.json --out passage.png
```

`inspect` returns JSON with the current revision and entity records. Generated
records include the owner, rule, and key. A scene with a spatial context also
reports registered bounds and surfaces and resolves any authored anchor into a
world-space frame. Omit `--part` to list the whole scene.

Edit files contain an `operations` array and can pin the base by copying the
`revision` from `inspect`. Use these operations.

| Operation | Fields | Effect |
| --- | --- | --- |
| `update` | `id`, `patch` | Merge `parameters`, `anchor`, `parent`, or `styleRef` into the part. Generated edits become retained overrides. |
| `suppress` | Generated part `id` | Hide the part and suppress its slot on regeneration. |
| `allow` | Owner `id`, `rule`, `key` | Clear suppression so the rule can emit the part again. |

The batch reconciles its generation rules after staging all operations.
Both commands return added, removed and updated IDs, changed part records,
and checks from the scene's realization. The passage example rebuilds the
splats and colliders from the same geometry and checks whether a character
can still walk through the doorway and up the stairs. A failed scene check
returns exit code 2 and leaves the snapshot and image unwritten. Bad input
or a stale revision returns exit code 1.

Pass `--authoring passage.json` to inspect or edit a saved snapshot. Each
`apply` takes a new output path, so the previous snapshot remains available
for rollback. The output uses the existing retained-document format.
Preview can save a PNG to a new path with `--image`.

### Enable the CLI for a scene

Add `authoring(seed, {snapshot, controls})` to a JavaScript scene descriptor.
Return a retained `document`, an optional authoring `context` bound to it,
and `realize(snapshot)`. Initialize the default document when no snapshot is
supplied. The CLI passes any `--params` JSON as `controls` and uses the saved
seed when loading a snapshot.

The CLI reconciles the context, stages edits in one document transaction,
and calls `realize` with the immutable candidate. Return `{world, checks}`
or a promise for that result. A check contains `id`, Boolean `pass`, and
optionally a message and JSON evidence. Every check must pass before the
CLI writes an output. Successful realization supplies a packed render world.
A rejected realization can omit the world. Use the same realization in the
scene's normal `build` hook to render the saved snapshot.

## Fixed-size image framing

`KIT.captureFrame.fixed(viewWidth, viewHeight, options)` returns the centred
crop, exact output size, art raster dimensions and a lens multiplier. `aspect`
accepts `view`, `wide`, `square`, `portrait` and custom ratios from .25 through
4. `edge` is the longest PNG side in pixels. `scale` controls whole art-pixel
blocks from 1 to 8. A crop changes the lens around the same camera target.

```js
const studio = require('@shapeshift-labs/ink-studio');
const { captureFrame } = studio.load().KIT;
const frame = captureFrame.fixed(480, 360, { aspect: 'wide', edge: 1920, scale: 4 });
const art = studio.render(world, { w: frame.renderWidth, h: frame.renderHeight,
  px: 1, colored: true, lensScale: frame.lensScale });
const rgb = captureFrame.pixels(art.rgb, frame, { channels: 3 });
```

`pixels` expands each art pixel by an integer factor and trims any fractional
block at the output border. Use `flipY: true` for a bottom-up framebuffer
readback. The software renderer's `lensScale` also works independently with
either perspective or orthographic cameras.

## Graphs and reusable groups

```js
const graph = K.procedural.graph.create({
  inputs: { offset: { type: 'number', default: 2 } },
  nodes: {
    width: {
      op: 'add',
      inputs: {
        a: { input: 'offset' },
        b: { keys: [{ time: 0, value: 0 }, { time: 2, value: 1 }] }
      }
    }
  },
  outputs: { width: { node: 'width' } }
}, {
  operations: {
    add: {
      inputs: { a: 'number', b: 'number' },
      outputs: { value: 'number' },
      run: ({ a, b }) => ({ value: a + b })
    }
  }
});
const frame = graph.evaluate({ offset: 3 }, { time: 1, seed: 7 });
frame.outputs.width;
frame.preview('width');
frame.status.width;
```

Connections read an exposed `input`, a `node` and optional `port`, a keyframe track, or a literal `value`. Types include scalars, vectors, geometry, fields, points and raster images. A node's inputs, seed and optional clock control its cache. Returned preview handles see the outputs of their own run. Wrap a graph using `graph.group(spec, { operations, groups, outputs })` and register it as an operation in another graph. Each group instance owns its cache. Preview an inner node with a path such as `frame.preview('groupName/innerNode')`. Use `clear()` after changing resources in place. Built-in operations include `meshPaths`, `attributeTransfer`, `densityMesh`, `densityPoints`, `materialSample`, `rasterLayer`, and `tiles`.

`graph.repeat(value, count, step, { seed })` iterates a value. `graph.each(items, fn, { seed })` gives each item a reproducible seed based on its ID. `graph.simulation({ initial, step, dt, checkpoint, cache, maxSteps })` advances states using fixed timesteps. Sample with `simulation.sample(time, { inputs, version })` to retrieve an exact fixed-step state, the number of steps replayed, and the cached checkpoints. Bump the version when the simulation inputs change.

## Geometry and attributes

`geometry.meshPaths(mesh, { sources, edgeCost, maxCost })` supports native and imported indexed meshes. It returns per-vertex distances and predecessors, plus `path(vertex)`, `curves(vertices)` and a sampled `distanceAt(point)` field. The cost function receives positions, vertex IDs, length and adjacent faces. Return infinity to block an edge.

`attributes.mesh(mesh, { vertex, face })` builds a nearest-surface sampler. Use `{ type: 'number' | 'vec2' | 'vec3' | 'label', values }` per channel. Numeric values interpolate across triangles. Labels and stable IDs are assigned from the dominant vertex or authored face. `attributes.sdf(field, callback)` projects a point onto a signed field. `attributes.carrier(carrier, callback)` samples a named surface chart. Use `attributes.transfer(sampler, domain, entities)` for points, faces, vertices, curve control points or instances. Use `attributes.paths` to retain curve IDs and per-control-point attributes, `attributes.nearest` to sample another captured table, and `attributes.splats(world, sampler)` to generate a table indexed by splat slot.

## Materials, artwork and animation signals

`graph.material({ height, wetness, ink, palette })` returns coordinated sample functions for height, normal, wetness, ink and palette roles. Connect individual outputs to masks, finishes or layered materials. `graph.tiles({ bounds, cell, mask, vector, scale, seed })` uses stable tile IDs and per-tile sampling to vary density, alignment and size.

`graph.raster({ width, height, layers, tags, fps })` takes named layers with RGBA frame arrays. Tags define half-open frame ranges, loop behavior and rate. Use `layer(name, time, tag)` for one image, or `composite(time, { tag, layers })` to composite selected layers in order. The payload is independent of the tool used to paint the source frames. In Node, `studio.readRasterAsset(file)` also accepts the same manifest with relative PNG paths as frame entries.

`KIT.anim.stateGraph.create(spec).instantiate()` runs keyframed states. Declare named inputs and triggers, timeline keys and optional cues per state, and ordered transition rules. A rule can check a trigger, minimum state age and input comparisons, with an optional blend. Advance on a monotonically increasing clock, calling `trigger(name)` and `advance(time, inputChanges)`. A returned sample includes the active state, mixed channels, cues and the transition taken. The host can bind those channels and cues to any effect or scene property.

Try `ink-studio sheet examples/graph-study.js --from 0 --to 2.6 --n 4 --ortho` for a layered signal animation that drives a cached growth effect across field-aligned tiles.

## Incremental authoring context

`ctx.collection` can match exact scalar values in `parameters` alongside
type and relationship filters. For a fact computed from multiple records,
`ctx.watch(select)` tracks a pure selector against the immutable document
view. Descriptors and rules rerun when the result changes by `Object.is`.
Use a scalar or stable immutable reference for the result. Spatial queries
made by a rule retain their type, tag and exclusion filters when deciding
whether a change affects it.

## Flooded Shrine

`procedural.floodedShrine.create({ seed, controls, snapshot })` owns a retained authoring document with an entrance, a hero silhouette and generated parts. Use `pin`, `setControls` and `regenerate` to steer the layout. Work with generated parts via the document's ordinary update, suppress, promote and undo APIs. The waterline, age, vegetation and path clearance can change while pinned anchors and authored overrides persist.

```sh
ink-studio render examples/flooded-shrine.js --ortho --params '{"waterline":0.3,"age":0.65,"vegetation":0.8,"clearance":1.3}'
ink-studio variants examples/flooded-shrine.js --seeds 6,19,27,30,47,71 --group openness --motion
```

The variant sheet is sorted by silhouette, openness or wear. The JSON sidecar includes art-resolution crisp and lint measures, and short-orbit shimmer when `--motion` is supplied. Existing snapshots can be used with `--authoring file.json`.

## GLB cutouts and UV surface stamps

`await studio.readAsset(file, {size: 3})` reads a portable GLB asset on Node, with the bundled PNG decoder. Supply `decodeImage` for embedded JPEGs. Embedded images retain RGB and optional alpha up to 128 pixels per edge, within the existing 16,384-texel budget.

The texture sampler exposes `opacityAt(face, u, v)` and `opacityAtPoint(face, x, y, z)`. Material samples also include `opacity`. glTF `OPAQUE` ignores alpha, `MASK` applies `alphaCutoff`, and `BLEND` multiplies texture, base-color factor and vertex alpha. Older RGB recipes remain opaque. Thumbnails composite visible layers in depth order.

`KIT.authoring.assetSurfaces.splat(builder, asset, options)` emits planar surface stamps carrying a UV shader. Atlas color, normal, roughness, emission and coverage are sampled at each art pixel. Texture detail therefore survives coarse splat spacing. The stamps retain underlying geometry behind cutouts and can be added to an existing scene.

`assetSurfaces.world(asset, options)` wraps the same path in a standalone world. Options include `size`, `at`, `turn`, `up`, `res`, `maxSplats`, `light`, `ambient`, `palette`, `hues`, `shades` and `cam`. Splats use the renderer's usual translucent blending. Save the portable asset or scene factory to preserve UV shaders, whose functions cannot be retained in a plain JSON world dump.

`assetSurfaces.field(asset, {size, cells, thick, alphaCutoff})` excludes invisible triangle patches before distance-field conversion. Visibility is sampled at twice the atlas texel density, with bounded triangle work. Fractional opacity is classified at the supplied cutoff (default 0.5). The result is a geometric signed field, so its resolution and shell thickness determine the smallest retained opening. Supply `thick` when converting open clothing or overlay surfaces.

The headless CLI automatically uses UV stamps for GLBs that fit the portable asset budgets. Use `--uv` to require that path and report unsupported imports, or `--uv off` to select the existing geometry importer.

```sh
ink-studio render character.glb --uv --res .06 --ortho --out character.png
```

### Textured SDF reconstruction

Pass `geometry: 'sdf'` to `assetSurfaces.world` or `assetSurfaces.splat` for the complete mesh → alpha-aware SDF → reconstructed surface → UV/material transfer → splat pipeline. The default remains `geometry: 'mesh'`.

The alpha field retains the original face that owns each visible patch. The reconstructed splats use that ownership to sample the original atlas at each rendered pixel, while their positions and normals come from the reconstructed surface. This preserves the source color, alpha, roughness, normal and emission channels through remeshing. Small cutouts and closely spaced layers remain limited by field resolution and shell thickness.

```js
const surfaces = studio.load().KIT.authoring.assetSurfaces;
const asset = await studio.readAsset('character.glb', {size: 3});
const world = surfaces.world(asset, {
  geometry: 'sdf', size: 6, cells: 112, thick: .065, res: .045
});
```

`cells` controls field resolution, `resolution` optionally controls reconstruction spacing, and `res` controls splat spacing. `world.sdf` records field dimensions, spacing, source triangle count and reconstructed triangle count for inspection. An optional `field` can supply a modified asset field, retaining its `sourceFace` lookup. This supports SDF carving before textured splat baking. A plain distance grid without source-face ownership needs that attribution restored before UV transfer.

```sh
ink-studio render character.glb --uv --geometry sdf --cells 112 --thick .065 --res .045 --ortho --out character-sdf.png
```


### Background transaction resolution

After collecting a draft with `document.begin(label)`, a caller can use
`await document.scheduleCommit(resolveDraft)` to resolve it in a worker.
The callback receives a frozen draft and returns the complete resolved document
snapshot. Configure the worker with the same generation rules and commit hooks
as the owning document. The result records one undo step and one autosave
revision. The document exposes the draft for rendering during resolution.

A new write, undo, or explicit commit settles the pending transaction using
the local hooks. Cancellation discards the draft, and late replies are ignored.
A failed resolver falls back to local hooks and ordinary rollback behavior.

### Immutable document patches

Use `A.data.documentView(snapshot)` to validate and freeze a worker's initial
snapshot. `A.data.patchDocumentView(view, {metadata, upserts, removed})` applies
later revisions to that view. `metadata` replaces supplied top-level JSON
values, `upserts` maps entity IDs to complete records, and `removed` lists
entity IDs to delete. The result validates references across the change and
shares unchanged entity and style records with the previous view. This lets
workers retain compiled geometry and material caches between messages.

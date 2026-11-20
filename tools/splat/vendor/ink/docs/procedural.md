# Procedural primitives

`KIT.procedural` is available through both `load().KIT` and the plain-script
browser bundle. Its operations take coordinates, fields, metadata, and
callbacks. They can be composed without a scene, an editor, or WebGL.

```js
const { KIT } = require('@shapeshift-labs/ink-studio').load();
const P = KIT.procedural;

const ground = {
  height: (x, z) => .2 * x,
  slopeBound: .2,
  bounds: { min: [-2, -.4, -1], max: [2, .4, 1] }
};
const carrier = [[-2, 1, -1], [2, 1, -1], [2, 1, 1], [-2, 1, 1]];
const support = P.supportSkirt({ outline: carrier, ground });
const geometry = support.mesh({ material: 'concrete' });
const mesh = P.geometry.toKitMesh(geometry, (owner, material) => [.6, .64, .61]);
```

| API | Contract |
| --- | --- |
| `spatial`, `transforms` | World bounds, ray box intersection, affine frames, point and normal transforms, conservative distance scaling |
| `surface.plane(spec)`, `surface.cylinder(spec)`, `surface.transform(surface, pose)` | Named carrier charts with `sample([u,v])`, `project(point)`, `closest(point)` and `raycast(origin, unitDirection, max)` |
| `geometry.builder()`, `geometry.toKitMesh(geometry, materialResolver)` | Triangle streams with positions, normals, UVs, bounds and owner/surface/material groups. Material resolution takes `(owner, role)` and returns normalized RGB |
| `geometry.samplePatch(spec, emit)` | Adaptive sampling of a bounded UV patch, using world spacing and an optional acceptance mask |
| `geometry.triangulate2D(points)` | Index triples for a simple concave or convex 2D polygon |
| `geometry.clipConvex(mesh, planes, capMetadata)`, `geometry.clipSurface(mesh, planes)` | Clip to half spaces `dot(normal, point) <= offset`. Closed convex shells receive caps, open triangle streams retain interpolated UVs/normals |
| `geometry.clipConvexFaces(faces, planes, {capTag})` | Clip a closed convex shell of outward-wound planar faces. Keep polygons intact through clipping and tag each cap with its plane tag or the supplied default |
| `geometry.clipPlanarFaces(faces, planes)` | Crop existing planar polygons against half spaces while retaining face attributes and leaving the cut open. |
| `geometry.clipHeightMesh(mesh, height, {slopeBound, resolution, budget})` | Keep the part of a triangle surface above a world-space height field (height(x, z)). Subdivision near the cut follows the supplied grade bound and resolution. UVs, normals and surface metadata carry through to the uncapped result |
| `geometry.implicitSurface(field, bounds, options)` | Marching tetrahedra for negative-inside fields, with column preparation and bounded edge refinement |
| `geometry.implicitTriangles(field, bounds, options, emit)` | Stream outward triangles from the same bounded field sampler |
| `pieces.convex`, `pieces.box`, `pieces.beam`, `pieces.tube`, `pieces.union` | Reusable solid pieces and query unions. Union meshes contain constituent shells |
| `pieces.union(parts).projectedIntervals(a, b, direction, {outward, inward})` | Merged intervals of material within a bounded strip projected onto a segment, with gaps preserved |
| `pieces.union(parts).faceOcclusion(exclude, corners, tolerance)` | Prepare one interior-occlusion predicate for points on a convex face, or return null if the face has no possible occluders |
| `pieces.union(parts).clearanceWithin(point, reach)` | Query local solid clearance with a world-space bounds check per piece. Returns Infinity when every piece's bounds lie beyond reach |
| `pieces.uprightSpan(a, b, {width, height, up, extension}, meta)` | Closed pitched band with upright ends and constant width and height |
| `fittedCourses(spec)` | Exact span fitting with stagger, periodic seams, material joints and logical cell identity |
| `logicalParts.compile(pieces, identify)` | Group clipped pieces of one stock part and partition visible and omitted pieces from retained keys |
| `courseRelief(layout, {profile, rise, slope})` | Give fitted cells independent relief with stable local coordinates when clipped or wrapped |
| `panelFrames(spec)` | Keyed rails, posts and braces that fit chart dimensions, with optional openings and fitted surrounds |
| `panelRelief({outline, layers, base, depthScale, budget})` | Fit keyed relief layers, hardware and trim around the contours of a convex panel |
| `fittedRibbon({inner, outer, pitch, gap, closed, phase, sections, measure, budget})` | Fit repeating bands along paired 2D or 3D rails. Each logical cell contains quadrilateral footprints split at source edges |
| `profileBand({profile, width, side, closed, pitch, gap, sections})` | Offset one side of a directed 2D profile and fit keyed cells along it. Width can vary by station. |
| `fittedRailBand({inner, outer, pitch, gap, closed, phase, sections, measure, depth, profile, direction, cellStyle, budget})` | Fit closed solid pieces with a rectangular or authored cross section along paired 3D rails. |
| `clippedLattice({panels, runs, edges, edgeWidth, budget})` | Fit bar families and frames to convex chart patches, keeping gaps and member identities across patches. |
| `surfaceCells.clip(cells, {boundary, holes, budget, work})` | Intersect convex cell footprints with a convex chart boundary and subtract convex holes. Group fragments by logical cell key |
| `surfaceCells.fieldMask(sample, {bounds, cell, maxCells})` | Convert a bounded signed chart field into convex cuts and a distance query against the same polygonal regions |
| `surfaceCells.loft(layout, {sample, levels, step, metadata, budget}, builder?)` | Map each fitted footprint onto two levels of a curved carrier. Emit closed, outward-wound fragments with shared cap and side vertices |
| `panelFrames({width, height, unit, beam, braceWidth, braces, periodic, budget})` | Fit posts, rails and optional diagonal braces to rectangular bays. Get stable keyed footprints and a signed chart query |
| `planarCells.layout(bounds, mask, options)`, `planarCells.prism(cell, options)` | Stable planar cells clipped to a mask, including disconnected fragments and holes. Prisms provide distance, ray, sampling and closed mesh operations |
| `supportSkirt({outline, ground, embed, overlap, maxDrop})` | Fill vertically below a convex planar carrier and above the supplied height field, up to the configured drop |
| `supportCourses(skirt, {unit, joint, depth, budget, omit, anchors})` | Fit recessed courses around a closed gravity support and retain facing omissions by key or surface position |
| `basins.surface(carrier, mask, options)`, `terraces.surface(carrier, configuration)` | Masked level cuts and configurable height bands. Carrier provides bounds, height, normal and domain predicates |
| `spans.catenary(a, b, options)` | Gravity-aware sagging curve with arc-length sampling, finite frames and closest-point queries |
| `proximity.connect(sockets, options)` | Deterministic matching of named sockets with reach, degree and compatibility limits |
| `attachments.layout(slots, families, options)` | Stable weighted selection for framed, typed attachment slots, with fit and clearance callbacks |
| `attachments.row({range, spacing, inset, maxPairs})` | Centered attachment stations at a fixed pitch, with persistent indices and bounded ranges for local adjustment |
| `attachments.fitRow(rowSpec, {occupied, gap, fits})` | Fit centered attachment stations around occupied distance intervals and validate support |
| `fitSurfaceBands({domain, panels, opening, edges, obstructions, clearance})` | Keep bands mounted to a chart feature's edges and shorten or omit them to fit nearby boundaries and obstructions |
| `alignedFeatureGroups(features, {axis, chartAxis, periods, separation})` | Group nearby aligned features on a measured chart and return ordered members and shared extents. |
| `fitFootprintContact({center, tangent, size, height, blocked, maxSpread, samples, interval, includePoints})` | Seat an upright footprint on a sampled support and check space above it |
| `footprintFromBounds(bounds, pose)` | Project a local box into an upright reservation with its origin offset preserved |
| `createFootprintReservations({clearance, cellSize})` | Reserve space for oriented upright objects and test nearby candidates |
| `placeFootprintRequests(requests, {obstacles, clearance, cellSize})` | Resolve priority-ordered fitters with one oriented clearance field |
| `assetCatalog.create(entries)` | Search lightweight asset metadata by name, keywords and collection without loading geometry |
| `fitAlongLane({range, start, pointAt, fit, maxDistance, spacing, precision})` | Find a nearby accepted station on a sampled 3D carrier line |
| `matchIntervals(previous, next, {maxShift, accept})` | Match spans across an edit using overlap and optional center displacement |
| `environmentFields.evaluate(settings, elapsed)`, `environmentFields.opticalDepth(from, to, medium)`, `environmentFields.scatter(from, to, light, medium)`, `environmentFields.deposition(sample)` | Cyclic sun and sky tint, height-dependent fog, local scattering, and slope-sensitive surface loads |
| `populations.layout(boundsList, evaluate, options)` | Seeded world-space candidates ranked by density. Expanding the work region preserves existing candidate identities |
| `sampling.poisson(options)` | Seeded Bridson samples in finite 2D and 3D bounds, with masks, variable radii, pins and axis scaling |
| `sampling.eliminate(points, options)`, `sampling.lloyd(points, options)`, `sampling.patch(spec)`, `sampling.geodesicSpacing(points, links, options)` | Progressive point subsets, centroidal layout, stratified surface sampling and surface-neighbor separation |
| `surfaceGrowth.trace(options)` | Seeded, bounded branching paths over caller-supplied surfaces, with a link query for seams and obstacles |
| `materialBands(spec)` | Nonoverlapping intervals with material and pattern metadata, plus optional spatial projection and period |
| `masks.stroke(spec)`, `masks.compose(specs, options)` | Tapered and feathered swept discs, ordered addition and erasure, signed distance and visible source ownership |
| `surfaceMasks.compile(strokes, {size, periodic})` | Ordered surface brush coverage in retained UVs with measured width and optional seam wrapping |
| `surfaceMasks.dirtyBounds(before, after, options)` | Bounded UV rectangles for repainting changed stroke coverage, including across chart seams |
| `surfaceMasks.compileLoop(strokes, {charts, height})` | Brush masks that cross an ordered loop of unequal surface charts while retaining each point's chart and UV |
| `surfaceMasks.loopDirtyBounds(before, after, options)` | Changed UV rectangles keyed by affected chart in a joined loop |
| `profileCut({profile, span, frame})` | Bounded extrusion of a simple 2D profile in an affine frame. `subtract(hostField)` forms an opening and `lining(thickness, hostField)` returns its material band |
| `geometry.profilePlaneSection({outline, span, frame, plane})` | Find the world-space edge intersections of a swept profile with a plane. Use the vertices for projected bounds, including concave outlines |
| `geometry.profileCylinderSection({outline, span, frame, cylinder})` | Intersect a swept profile with a closed elliptical cylinder chart and return contact bands and per-station vertical intervals |
| `geometry.recessedProfile({outline, recess, center, span, inset})` | Closed XY profile extruded along Z with a blind front recess, shared mesh edges and a solid backing |
| `geometry.fitMonotoneOutline({outline, required})` | Fit a horizontal span at each height while preserving authored ledges and cutbacks where they have clearance |
| `geometry.fitExteriorOutline({outline, required})` | Join two planar rings into one exterior while keeping exposed cutbacks, including profiles with multiple spans at a height |
| `surfaceSection(chart, options)` | Convert between world coordinates and a section measured through the varying thickness of a surface chart |
| `geometry.profileDistance(points)` | Compile a closed 2D ring into a reusable signed distance function `(x, y) => distance`. Concavity and either winding are supported |
| `volumeCuts.compile(specs)` | Union keyed XZ profiles extruded along Y. Provides a signed field, host subtraction, bounded exposed-boundary sampling and ray hits |
| `clearance.field(solids).probe(bounds, options)` | Bounded sampled volume contacts for supplied solids with `id`, bounds, and distance functions |
| `traversal.create({supports, clearance, ...body})` | Ground-following body with bounded displacement, head clearance, step limits and wall sliding |
| `supportSweep.segment(from, to, patches, options)` | Check continuous support across level footprints with height differences and cutouts |
| `routes.follower(route, options)` | Distance-based position and a look-ahead frame for cameras or assemblies on sampled routes |
| `ambientMotion.create(members, {place, move, destination?, step?})` | Seeded roaming, local avoidance, temporary attraction and habitat revalidation |
| `layerMix.create(layers, {budget})` | Combine continuous controls into bounded per-layer gains with optional fades |
| `inputActions.compile(contexts)` | Map physical keys and analog controls to semantic actions in named contexts |
| `inputActions.permutation(controls, overrides)` | Swap physical assignments without leaving actions unbound |
| `inputActions.axisMapping(controls, options)` | Reassign and invert signed analog inputs |
| `emitters.compile(spec)` | Deterministic looping samples with configurable emission direction and local drift. Set `windborne: true` and pass `{wind: [x, z]}` when sampling to advect by particle age. |
| `routes.polyline(points, options)`, `routes.aroundConvex(outline, start, end, options)` | Arc-length routes with frames and closest queries. Convex XZ routes project endpoints onto an offset perimeter and interpolate world Y |
| `geometry.inclinedPerimeter(outline, pose, {offset, below, above})` | Offset a convex affine extrusion for a world-upright swept section. Project and lift between the height-independent outline and world space |
| `geometry.convexPerimeter(outline, options)` | Offset a convex XZ outline with bounded corner joins and source-edge identities |
| `routes.terrain(start, end, options)` | Bounded, terrain-aware search between pinned points with slope, signed clearance, keep-out regions and turn costs |
| `hydrology.analyze(height, options)` | Priority-Flood, D8 catchments, stream orders, channel routes, wetness and optional D-infinity flow |
| `hydrology.breach(basin)`, `hydrology.incise(basin)`, `hydrology.meander(route)`, `hydrology.corridor(routes, height)`, `hydrology.habitat(basin)` | Watershed edits, river migration and cutoff routes, levees, floodplain masks and climate fields |
| `biomes.create(options)` | Shared XYZ sampling of normalized biome weights, air, solid or water membership, and local conditions |
| `waterBodies.create(options)`, `waterBodies.fromShallowWater(snapshot, options)`, `waterBodies.scene(bodies)` | Water frames shared by shoreline placement, current and depth queries, and WebGL visibility |
| `biomeRecipes.create(options)` | Retained biome recipes, brush strokes, placement pins, and explained habitat and population queries |
| `biomeWorld.create(options)` | Headless chunk realization with sampled terrain and cave collision, traversal, placements, splats, and local rebuilds |
| `routes.visibility(start, end, obstacles)`, `routes.spline(route, options)`, `routes.travelTime(sources, options)` | Polygon visibility paths, clearance-tested corner fitting and fast-marching travel-time fields |
| `geometry.delaunay(points, options)`, `geometry.triangulatePolygon(rings)`, `routes.network(points)`, `routes.steiner(points, edges, terminals)` | Constrained planar triangulation, graph layouts with optional loops, and shared branch networks |
| `routes.tensor(components)`, `routes.followTensor(field, seeds)`, `routes.growStreets(seeds, options)`, `routes.parcels(outline)`, `routes.medial(rings)` | Directional street systems, connected seeded roads, frontage lots and medial paths |
| `routes.layout(route, options)` | Fit bounded intervals on a polyline, catenary, or compatible curve. Place caller-chosen pieces using gapped endpoints and midpoint frames |
| `routes.fitStairApproach(options)` | Fit a short stair flight from an exposed landing to a sampled carrier surface. |
| `routes.uprightMotion(before, after, tolerance)` | Check whether paired guide points share an upright rigid transform |
| `edgeClearance.strip(a, b, options)`, `edgeClearance.ranges(a, b, strips)` | Split a straight edge into retained and removed ranges where it crosses sloped clearance strips. |
| `edgeClearance.clipFieldPath(points, fields, {padding, spacing, tolerance})` | Split a polyline around bounded signed fields, preserving its unblocked vertices and bends. |
| `snapping.resolve(point, features, options)` | Project to a bounded point or segment and return the winning feature with its caller-supplied identity. |
| `planSnapping.compile(outline)`, `planSnapping.align(moving, translation, targets, options)` | Align convex footprints along finite faces or corners, with an optional retained contact and release distance. |
| `planSnapping.compileMotion(plan, velocity)`, `planSnapping.alignMotion(motion, value, targets, options)` | Align a convex plan whose vertex positions change linearly with one parameter. Applies to anchored scaling and other parameterized edits. |
| `railGuard(options, meta)` | Build closed rail and upright post pieces with adjustable height, spacing and rail levels. |
| `cantileverSupports.sites(options)`, `cantileverSupports.fitMount(options, distance)`, `cantileverSupports.bracket(site, options, meta)` | Fit bearing sites along an edge or to a nearby solid field and build support profiles. |
| `traceSignedIntervals(sample, options)` | Find where a signed field is negative along a bounded curve parameter. Supply a slope bound to skip homogeneous regions. |
| `styles.catalog(definitions)`, `styles.compose(...layers)` | Caller-defined profiles, named inheritance, and deep composition. `styles.material(profile, role)` resolves aliases and normalized colors |
| `chunks.create({preview, refine})` | Cache realized chunks by key and revision, retain unrelated payloads, send bounded replacement patches, and cancel obsolete work |
| `chunks.createScheduler({budgetBytes, describe, load})` and `chunks.grid(options)` | Prioritize independent streaming requests and keep a bounded set of chunks from procedural grids |
| `contacts.index(mesh, options)`, `contacts.intersections(a, b, options)`, `contacts.clipCurve(points, solids)` | Index named triangle groups, trace noncoplanar contacts, and trim contact or authored curves against closed indexed solids |
| `contacts.index(mesh).raycast(origin, direction, max)` | Find the nearest triangle hit and report its point, normal, distance, owner and named surface. Reach is measured in world units. |
| `contacts.traceSdf(chart, sd, options)`, `contacts.expose(curves, occluder, options)`, `contacts.field(curves)`, `contacts.runoff(curves, project, options)` | Trace SDF contacts, expose visible runs, derive distance masks and follow downhill paths |
| `tiles.compile(definitions)`, `tiles.solve(model, options)`, `tiles.learn(swatch)`, `tiles.overlap(bank, options)`, `tiles.wang(model, options)`, `tiles.refine(coarse, model, options)` | Weighted matched sockets, example-based synthesis, world-stable patterns and coarse-to-fine layouts |
| `fields.simplex(options)`, `fields.periodic(options)`, `fields.compile(expression, options)` | Seeded analytic noise and serializable field composition for SDFs, materials and placement |
| `grammar.expand(scope, rules, options)`, `grammar.children(layout)` | Bounded shape grammar with named partitions, fitted repeats, pinned spans, sockets and retained child specs |
| `grammar.rewriteGrid(rows, rules)`, `grammar.rewriteGraph(graph, rules)` | Seeded weighted pattern replacement on scalar grids and directed graphs |
| `layouts.bsp(options)`, `layouts.cave(options)`, `layouts.pack(items, options)`, `layouts.floorPlan(rooms, options)` | Connected room partitions and caves, constrained rectangle packing and named room adjacencies |
| `growth.lsystem(axiom, rules, options)`, `growth.turtle(tokens, options)`, `growth.venation(outline, options)`, `growth.roots(starts, options)`, `growth.pipe(nodes, options)` | Growth grammars, SDF branch runs, venation, obstacle-aware roots and pipe taper |
| `growth.aggregate(options)`, `growth.grayScottGrid(options)`, `growth.grayScottSurface(points, links, options)`, `growth.dispersal(options)`, `growth.succession(options)` | Grid and surface patterns, seed dispersal and habitat competition |
| `forms.superquadric(spec)`, `forms.loft(sections)`, `forms.skeleton(nodes)`, `forms.periodic(spec)`, `forms.shell(host, options)` | Bounded analytic forms and locally variable shells for the sculptor |
| `measureSculptBounds(build)` | Measure a finite rest-pose recipe without generating splats |
| `grammar.symmetry(scope, rules, options)` | Reflected or radial grammar instances with optional variations and stable copy keys |
| `fracture.power(spec)`, `fracture.separate(graph, options)`, `fracture.crack(options)` | Anisotropic power cells, cumulative bond failure and stress-guided crack paths |
| `grammar.assemble(route, modules, options)`, `construct.loadPaths(sockets, spans, options)`, `construct.supportGraph(parts)`, `construct.damage(parts, options)` | Dimensioned, socket-connected assemblies, stylized supports, support propagation and seeded part damage |
| `construct.profile(rings)`, `construct.offset(profile, distance)`, `construct.extrude(profile, options)`, `construct.weightedRoof(rings, options)` | Signed footprints, planar offsets, extrusions and roof wavefronts with per-edge pitches |
| `geometry.distanceTransform(mask, options)`, `materials.outline(mask, options)` | Exact Euclidean distances over pixel or voxel centers, including anisotropic spacing and inside/outside masks |
| `materials.triplanar(sample, options)`, `materials.tangent(sample, options)`, `materials.threshold(field, options)`, `materials.ramp(colors, options)` | Surface-aligned patterns, pixel-footprint filtering and perceptual palettes |
| `materials.quilt(swatch, options)`, `materials.patchMatch(source, target, options)`, `materials.synthesize(source, target, options)`, `materials.blueNoise(options)` | Swatch quilting, exemplar matching and fill, and periodic blue-noise ranks |
| `materials.paintMixer(layers)` | Ordered paint and erasure over scalar coverage masks. Sample provenance weights or select one material with a stable caller-supplied rank. |
| `geometry.dualContour(field, bounds, options)`, `geometry.surfaceNets(field, bounds, options)` | Cell-local surface samples, optional indexed preview triangles and tagged mesh output |
| `geometry.octree(field, bounds, options)`, `geometry.stitchVoxelLevels(tree, options)`, `geometry.adaptiveSurface(field, bounds, options)` | Sparse field sampling, 2:1 voxel levels and stitched adaptive previews |
| `geometry.simplifyQEM(mesh, options)`, `lod.mergeSplats(records, options)`, `lod.packSplats(result)` | Error-driven previews with retained material seams, ownership and protected samples |
| `sampleVisibility.create(count)`, `splatOrder.compile(indices, depthAt)` | Packed visibility updates and reusable depth buckets for retained samples |
| `splatCodec.encode(data, count, options)`, `splatCodec.decode(bytes, options)` | Compact, ordered native splat rows for offline delivery |
| `motion.streamline(field, start, options)`, `motion.obstacleWake(sdf, options)`, `motion.loopTrajectory(points, options)`, `motion.surfaceAdvection(chart, seeds, options)` | Field integration, wake and curl sampling, closed tracks and UV-attached motion |
| `motion.stableFluid(options)`, `motion.shallowWater(options)` | Persistent density and velocity grids, and conservative terrain-aligned water |
| `motion.surfaceWeather(options)`, `motion.materialStateGraph(machine, entities, options)` | Persistent wetness and thermal fields, and event-driven material changes |
| `motion.transportSplats(source, target, options)` | Balanced mass correspondences and barycentric splat targets |
| `contours.march(field, options)` | Bounded marching-squares paths at a scalar level |

Heights and distances use world units. Planar masks take XZ and use negative
distance for the interior. Compiled carrier callbacks should be deterministic.
Primitive operations with sampling or tessellation expose work limits so the
caller can choose the appropriate detail for the use case. Mesh output is
approximate where a curved field is sampled. A support requires a conservative
height and slope declaration over its footprint.

`geometry.implicitSurface` accepts an optional `prepareColumn(x, z)` that
returns a signed field of `y` for the lattice at that horizontal position.
Use it when height, material layers, or a planar mask can be prepared once
per column. The values must match the ordinary three-dimensional field.
`edgeRefinements` from 0 to 12 use the ordinary field between lattice
points to bisect nonlinear crossings within the same cell budget.

`geometry.implicitTriangles(field, bounds, options, emit)` shares the
field, column preparation, refinement and cell budget of `implicitSurface`.
It calls `emit(a, b, c, normal)` for each outward nondegenerate triangle
and returns the lattice sampling metadata. Vertices and normals use the
same Float32 precision and traversal order as the finished mesh. Use the
stream for consumers such as pixel sampling that only need one triangle
at a time.

Build the browser gallery with `node examples/procedural/build.js`. Open
`dist/procedural-gallery.html` and move the View angle slider to inspect the
actual meshes. The HTML contains the library and all the examples.

A mask stroke takes a unique `id`, 2D `points`, optional `radii`, `width`,
`softness`, `layer`, and `order`. Use `operation: 'erase'` to subtract a stroke.
A mask's signed distance is independent of its feathered coverage. Empty masks
return positive infinity. Clearance probes approximate contact at the selected
spacing. Choose spacing and padding in relation to the smallest obstruction
the caller needs to detect. Emitters describe visual trajectories and do not
perform particle collision or fluid simulation.

Long swept-disc strokes index contiguous segment runs by their bounds and
maximum radius. A query evaluates the original segment geometry for candidate
runs and keeps the earliest segment's radius on equal distances. The same
queries drive signed coverage, feathering, radius blending, and ordered
paint and erase composition.

Use `surfaceMasks.compile(strokes, {size: [width, height], periodic})` to
keep paint attached to a changing surface chart. Each stroke has normalized
`points`, a physical `width`, optional `softness`, and an `operation` of
`'add'` or `'erase'`. Recompile with the new chart dimensions to move the
stroke centers with the surface while keeping the brush width in chart units.
With `periodic: true`, successive U stations join by the shortest arc and the
footprint continues across the seam. The chart supplies the metric, so
`width` for a closed carrier is its full measured circumference.

Call `mask.weight(u, v, initial = 0)` to compose strokes in their supplied
order over existing coverage. Outside the finite chart it returns `initial`.
One surface allows up to 256 strokes and 8,192 points. Use the weight for
paint, coating loss, habitat, or other application-specific fields.

`surfaceMasks.dirtyBounds(before, after, options)` returns conservative
unit UV rectangles for the changed suffix of two retained stroke lists.
The rectangles include brush width and feathering and split across periodic
seams. An unchanged list returns an empty array. Test a sample's full
footprint against these rectangles when updating its color or coverage.

`surfaceMasks.compileLoop` joins charts of the same height into a closed
run. List them in travel order as `{key, length}`, where `length` is the
physical distance along U. Joined strokes use `{chart, uv: [u, v]}` for each
point. For a stroke clipped to one chart, set `chart` on the stroke and
use ordinary `[u, v]` points. The mask applies both forms in their supplied
order. Call `weight(chart, u, v, initial)` to query a point. Recompiling
with different chart lengths moves the stroke centers with their own
charts. The brush keeps its physical width and uses the shortest path
around the loop between successive points. `loopDirtyBounds` returns
conservative `{chart, min, max}` rectangles in the affected charts.

Route layout takes a positive `pitch`, optional physical `gap`, a normalized
`from` / `to` range, and a `distribution` of `ceil`, `floor`, or `round`.
For polylines the default policy fits independently across each straight
segment, so an interval never bridges a bend. A route has `length` and
`sample(t)` returning a `point` and optional frame metadata. For custom curves,
the caller owns arc-length parameterization. The sample contract is shared
with `spans.catenary`.

For fitted ribbons, corresponding inner and outer vertices define a strip.
Pitch and gap are distances along the inner rail. The pitch is fitted to the
total length and a corner splits a cell into fragments with the same key.
`closed: true` connects the last and first vertices. A fractional `phase`
shifts the joints around that seam. The result contains footprints in the
input coordinate system so callers can extrude, clip or sample them.

`panelFrames({width, height, unit, beam, braceWidth, braces, periodic, openings})`
fits a panel of rails and posts and optional per-bay diagonal bracing. Use
`openings: [{key, min, max, rim, rimEdges}]` to cut rectangular clear areas through the
layout. Each cut can add a keyed header, sill and jambs. Set `rim: false` for
clearance alone. `rimEdges` optionally lists the enabled members from
`sill`, `header`, `start` and `end`. A panel sharing an opening with the
next panel can omit the intervening jamb without filling the opening. A
wrapped cut keeps the same member keys across both ends of
the chart. A cut exactly one period wide uses continuous sill and header
rings and omits both end jambs. The result exposes convex member footprints and a distance
sampler. Call `openingEdges()` for merged segments of exposed member
boundaries along the cutouts. Each segment has chart-space `start`, `end`
and a `normal` pointing into the opening. A periodic opening preserves its
real edges across the seam. Callers can extrude these segments through the
relief depth to render cut faces, then set their materials and infill.

`geometry.profileCylinderSection` intersects a simple profile, including a
concave outline, swept from `span[0]` to `span[1]` in its affine frame. The
cylinder chart has four world-space vectors: `origin`, `cosine`, `sine`, and
`axis`. At normalized coordinates `[u,v]`, its point is
`origin + cosine*cos(2πu) + sine*sin(2πu) + axis*v`. The axis covers the full
chart height from zero to one. The result's `at(u)` gives ordered, disjoint
vertical intervals. Its `bands` give a bounds rectangle for each connected
angular span. A contact through the seam has an upper station greater than
one. Rectangular surrounds can use those bounds. Applications that need the
actual vertical contour can query `at(u)`.

`panelRelief({outline, layers, base, depthScale, budget})` fits convex
ornaments, panel surrounds and other layered shapes to an existing planar or
surface-local XY panel outline. Each layer supplies a stable `key`, a
`material` role, a convex `polygon`, optional convex `holes`, and two
ordered `levels`. The polygons are normalized to the outline's bounding
rectangle with coordinates from 0 to 1. The outline accepts up to 128
vertices. Each returned part carries its source `key` and `fragment`
index, its clipped convex `outer` polygon, and the `lo` and `hi` depths
computed as `base + level * depthScale`. Feed the footprints to a cell
loft or a chart-local distance field. The existing panel supplies backing.

`surfaceSection(chart, {center, units, thickness, periodicU, offset})` uses
the chart's `sample(uv)` and `project(point)` contract. Supply the two local
chart scales in world units per chart unit, and a positive thickness sampler
`thickness(uv)`. `map([x, y, z])` and `project(point)` place and recover local
coordinates. Depth zero is the front surface plus the optional offset.
Depth `-referenceDepth` follows the back across the chart, while positive
depth keeps its world scale for trim projections. Chart projection must
locate the corresponding surface point along the normal throughout the band.
Turn on `periodicU` to keep local coordinates continuous across a closed seam.

Use `section.aperture(profileDistance, {front, back})` to intersect a signed
profile in local XY with the section's thickness band. The optional
nonnegative extensions `front` and `back` use the section's local depth units.
`distance(worldPoint)` and `distanceLocal([x,y,z])` are negative inside the
cut. `mouths([x,y])` returns the unextended `entry` and `exit` at a profile
coordinate, using the actual thickness there. Apply the host's spatial
bounds when the chart projects points outside its own domain.

Convex face clipping accepts face records with `points` in outward cyclic
order and an optional `tag`. Supply half spaces with `normal` and `offset`
and optionally attach a `tag` to any plane. The output has the same face record
shape, with a cap for each plane which intersects the volume. Triangulate the
result after clipping if the consumer uses triangle geometry.

`geometry.clipPlanarFaces(faces, planes)` clips each existing convex face
independently, including an open group or a single face. It preserves extra
face fields such as material, normal and owner. Original faces on a clip
plane remain, and the cut creates no new cap polygons.

`surfaceCells.clip` takes records with a string `key` and convex 2D
`polygon`, or cells from `fittedCourses` with `id` and `inset` bounds.
Either polygon winding is accepted. The output has counterclockwise convex
fragments in the same chart coordinates. Shared cell keys are grouped across
chart seams and split pieces. Material assignment and mapping chart points
onto the host are caller policies. The work budget counts vertices visited
by the clip operations.

`surfaceCells.index(plan)` indexes the result of clipping by logical cell
key. Use `get(key)` for every surviving fragment and `contains(key, [u, v])`
to pick it on the chart, including points on the fragment boundary.
`excluding(keys)` returns another clipped plan with the specified logical
cells omitted and the fragment count adjusted. The original index retains
those fragments for restore picking. Pass either plan to lofting, sampling
or contact generation.

`surfaceCells.fieldMask` traces the negative regions of a signed chart
field. It returns closed boundary `rings`, convex `holes` for cell clipping
and `distance(u, v)` against those boundaries. Disconnected regions and islands are
preserved at the chosen sampling resolution. A clear field returns `null`.

`surfaceCells.loft` takes the clipped layout and calls `sample([u, v], level, key)`
for each position. Supply an ordered pair of finite levels whose samples
enclose a solid. Use `step` to subdivide in chart coordinates before mapping.
Each convex fragment emits a closed shell. A metadata callback can assign
owner, material and surface roles by the original logical cell key.

`courseRelief` takes a `fittedCourses` layout. Its `profile(u, v, cell)`
callback receives coordinates normalized to a cell's inset and returns a
number from zero to one. A wrapped seam uses the same logical cell on both
sides. Multiply by the configured `rise` to get the height above the carrier.
Pass `slope` as the pair of derivative bounds of the normalized profile.
The result reports their conservative values in chart units. Use
`height(u, v, key)` with the loft's cell key to retain the original profile
after clipping. Use `top(u, v)` to query the raised surface including joints.

`fitSurfaceBands` takes two-dimensional chart bounds with `min` and `max`
coordinates. Configure any of the left, right, bottom, and top edges with
`reach`, optional `minReach`, and a `gap` from the opening. Set `span` and
`minSpan` along the edge for fittings of a particular height or width.
Each result has a stable edge key, a mount midpoint in `hinge`, and fitted
`bounds`. An obstruction shortens the band along its outward axis. The planner
omits the band when its remaining space falls below the configured minimum.

For a segmented carrier, pass `panels: [{id, min, max}, ...]` in place of
`domain`. Panels, obstructions and the feature share one unfolded chart.
Bands independently fit each panel and report its `panel` ID. A span that
crosses a seam splits at the panel bounds while keeping the original mount
coordinate along the outward axis. A band only extends into a panel that
contains its mount. Leave a gap between panel bounds for seams or stock
overhang. The caller maps each result back onto its physical surface.

`materialBands({layers, fallback, direction, origin, period})` can repeat
layers along any direction. The direction is normalized. Spatial lookup
projects `point - origin` onto that direction. Without a direction, `axis`
selects X, Y, or Z. The default origin is zero. Pass a scalar to `at` when
a coordinate is already projected, or use `atXYZ(x,y,z)` to avoid packing
a point. In a periodic band, interval endpoints are measured within
`[0,period]`, and queries on either side of zero wrap. `segments(min,max)`
returns the ordered, clipped intervals across seams and rejects
subdivisions beyond the work budget. Layer metadata can carry palette roles,
shading offsets or other consumer-defined properties.

`alignedFeatureGroups(features, options)` groups nearby features with
compatible dimensions. Supply one compatible family with records
`{id, at, units, size, gap, alignment, sizeTolerance, limit}`. `at` is a
chart coordinate, `units` gives world distance per chart unit, and `size`
is the feature's world width and height. The distance limits `gap` and
`alignment` are in world units. `sizeTolerance` is the maximum fractional
difference in the perpendicular size. `limit` caps how many members may
share a group. Choose the feature's dimension with `axis` and the host
coordinate with `chartAxis` if those axes differ. Set a nonzero value in
`periods` for each cyclic chart coordinate. `separation` defaults to a
quarter of the shorter feature's along-axis size.

Connections are transitive. Ordered components split at the smallest
member limit, and singleton results are omitted. Each group supplies
`members` in chart order, world-distance `stations`, shared `units`,
the occupied station `range`, array `size`, and a chart `anchor`.
Cells, trim, and attachments can consume the same layout and independently
choose their owners and appearance.

`fitFootprintContact` samples an oriented rectangular footprint in world XZ.
The `center` supplies the horizontal origin and `tangent` sets the width
axis. `size` gives the width, height and depth. Supply a `height(x, z)`
function that returns the support height or `null` for a hole or excluded
surface. Choose an allowable height `interval`, the maximum height
difference `maxSpread`, and `samples` per axis. An optional `blocked(point)`
predicate can reject sample columns at three heights above the fitted base.
An accepted fit returns the upright frame with its origin at the highest
sample, the height `range`, and the sampled XZ `points`. Set
`includePoints: false` when only the fitted frame and range are needed.
The checks still use the full sample grid. A footprint with
missing support, excessive height variation or blocked space returns `null`.

`footprintFromBounds({min, max}, {R, t})` converts local bounds and an
affine pose into the `{point, tangent, size}` accepted by both footprint
services. The tangent follows the projected local X axis, with local Z
available when X is vertical. The point is the center of the base of the
resulting upright box. To seat a model, compute this claim at the original
pose, fit the claim to the support, and apply the difference between the
fitted and original base points to the model translation. This preserves
an asset's original pivot even for off-center geometry or a raised base.

`createFootprintReservations` manages a temporary set of oriented volume
claims. Each claim takes `{point, tangent, size}`, where `point` is the
center of the base. Pass a contact result's point and tangent with the
original size to reuse the fitted frame. `fits(spec)` checks for a free
volume. `reserve(spec)` inserts a claim if it fits and returns whether it
was inserted. `occupy(spec)` inserts a preexisting obstacle even if it
overlaps another obstacle. The optional `clearance` pads the horizontal
footprints. Heights must overlap for a conflict, so the same XZ footprint
can fit on multiple decks. Insert claims in your preferred order to settle
competing candidates deterministically. The `cellSize` changes lookup
granularity and keeps the overlap test identical.

`footprintCorridor(points, {width, headroom, below, step, maxVolumes})`
turns an XYZ polyline into reservation claims. Supply waypoints on the
walking surface. The claim width runs across the guide and the vertical
range runs from `below` the lower point to `headroom` above the upper point
in each interval. `step` bounds the horizontal length of an interval.
A shared claim at turns keeps corners clear. Pass the claims as
`obstacles` to `placeFootprintRequests`, or insert them with `occupy`.

`freeIntervals(spec, direction, [start, end])` on the reservation field
returns the ranges of signed distances that keep the footprint clear when
translated in the supplied XZ direction. The direction is normalized and
the footprint retains its orientation and vertical range. The solver
intersects the separating-axis limits of nearby oriented rectangles
analytically. Touching endpoints are allowed, including a singleton
interval between two reservations. Use a support or geometry test at the
chosen location if the surface changes along the interval.

`nearestTranslation(spec, {reach, margin, maxObstacles, maxTests, test})`
searches in XZ across all headings while keeping the footprint orientation
and vertical range fixed. It considers the nearest points on reservation
boundaries, their corners, and the intersections of overlapping
boundaries. `reach` limits the distance in world units. `margin` defaults
to one millionth of a world unit and offsets the sampled faces outward to
avoid floating-point contact errors.

For each clear candidate, the optional `test(offset, distance)` can check
terrain, constrain the search to one side of a surface, or return a
caller-specific placement. Return `false` or `null` to reject. Candidates
are tested in increasing distance order. The result has `status` and
`tests`, plus `offset`, `distance` and `value` when the status is `ok`.
Use `maxObstacles` and `maxTests` to limit the work. The search reports
`budget` when either limit stops it and `unreachable` when the candidate
set is exhausted. The callback verifies these candidates against the
support geometry.

`assetCatalog.create(entries)` accepts stable IDs, display labels, and
optional `subtitle`, `categories` and `keywords`. Geometry and recipes are
outside the index. `search({query, category, offset, limit})` returns a total
and a page of metadata. Search ignores case and accents, matches across
words and ranks display labels ahead of metadata matches. Filter with
`catalog.categories` and retrieve one entry with `catalog.get(id)`.

`attachments.fitRow(rowSpec, {occupied, gap, fits})` adjusts each existing
center-relative station only within its range. `occupied` supplies open
distance intervals. Touching their endpoints is allowed. Accepted stations
reserve `gap` units on either side for subsequent stations. An optional
`fits(distance, station)` tests physical support at the preferred point,
obstacle edges and a finite set of points within the station band. Unfitted
stations are omitted. Surviving stations report `preferred` and actual
`distance` with their original index.

`placeFootprintRequests(requests, {obstacles, clearance, cellSize})` shares
the field across candidate sources. Each request supplies a numeric
`priority` (default zero) and a synchronous
`fit({fits, freeIntervals, nearestTranslation})`
callback. Return `{footprint, value}` for one proposal or `null` to skip
the request. Higher priorities fit first and ties keep input order.
Obstacles reserve their space before the first request. Each accepted
footprint becomes visible to later fitters. A rejected proposal leaves
the field unchanged. Results keep the original request and its value.

`fitAlongLane` searches both sides of a starting parameter within the
supplied range. `pointAt(parameter)` returns XYZ or `null` where the
carrier ends. Candidate spacing and travel bounds use the measured
polyline length. `fit(parameter)` returns a result or rejects with
`false`, `null` or `undefined`. Its accepted result is returned with
the selected parameter and distance. Use `segments` to control curve
measurement, and `maxTests` to cap fit calls. Sample spacing controls
which clear intervals can be discovered. The solver refines a detected
transition to `precision` in measured distance.

`matchIntervals` compares two lists of disjoint `[low, high]` spans in the
same units. An entry in its result points to the original index of the
previous span paired with that next span. An unmatched entry is `-1`.
Each previous span can be paired once. Greater overlap takes precedence,
followed by smaller center displacement and earlier station. Use
`maxShift` to allow disjoint spans to match within a center displacement,
or `accept(previousIndex, nextIndex)` to filter candidate pairs.

`panelFrames` fits to the carrier dimensions and exposes its member footprints
as `parts`. Pass those to `surfaceCells.clip` for openings, then loft the
remaining pieces onto the carrier. Posts and rails run continuously. Braces
fit inside individual bays and can be ascending, descending, alternating,
crossed or omitted. A callback can choose any of those policies per bay.
Set `periodic: true` for a shared post key across a wrapped chart seam.

Catalog definitions may name one or several parents using `extends`. A
resolved profile merges named or inline layers in order. Object keys compose
recursively, while arrays and scalar values replace earlier values.
Material role values accept aliases, RGB colors, and attribute records.
Use a complete material record or an inherited color when setting shades.

The field returned by `masks.compose` also offers `distanceAt(x, y, ceiling)`.
It computes the exact signed distance up to the optional ceiling. This is
useful for a containment test or for subtraction that already has a distance
bound. Normal array-based `distance([x, y])` queries remain unbounded. A bounded
query preserves ordered add and erase operations and never changes ownership.

Each volume cut has a stable `key`, a simple planar `profile` of XZ pairs,
and a `span: [low, high]` in Y. Compile up to 256 cuts in a common caller-provided
frame. `distance(point, ceiling)` clamps the union distance to its optional
ceiling. `subtract(hostField)` returns a field that removes the union from
only that host. `sample(spacing, emit, {maxSamples})` emits boundary points
with cutter normals and ownership keys. The normals face into the remaining
material after subtraction. `raycast(origin, direction, max, accept)` reports
the first exposed cutter surface accepted by the caller. Keep the keyed specs
as intent and remove or restore them to repair the host.

### Ground traversal

`routes.follower(route, {loop, lookAhead, up})` accepts a route with a finite
world length and `sample(t)` on normalized arc distance. Its
`sample(distance, direction)` returns a point, orthonormal frame, lap and
end-of-route status. Distances and look ahead are in world units. Give a
repeating route coincident endpoints. The caller supplies elapsed time, speed
and any offsets for the camera or assembly.

`traversal.create` accepts a `supports(x, z, low, high)` query returning
candidate `{y, normal, id?, material?}` surfaces and a `clearance(point, radius)` query
returning a signed distance to obstacles, positive in free space. The
clearance query can ignore solids outside the supplied radius and return
positive infinity for open space. Heights and distances share the scene's
coordinate units. Normal vectors need not be unit length.

`body.stand([x, y, z], {rise, drop})` returns the highest stable support
that fits the body in its search interval, or `null`. The result has
`foot`, `support`, `normal`, and the support's optional `material` tag.
`body.move(foot, [dx, dz])` follows
supports in increments. It limits the rise and drop per increment and
tries sliding along an axis when a diagonal is blocked. It also returns
`blocked`, horizontal `progress`, and the planned number of increments
as `steps`.

An optional `transition(from, to, support)` can reject a candidate move
between otherwise valid seats. It runs for direct increments and slide
attempts. Use `supportSweep.segment(from, to, patches, {verticalTolerance})`
for level walking surfaces with known footprints. Each patch has a constant
`height`, convex XZ `footprint`, and optional convex `holes`. The query
returns `start` and `end` for endpoints supported at their own elevations,
and `covered` when the entire segment rests on the union of eligible
patches. Intermediate patch heights must lie within the endpoints' vertical
range. The caller supplies other policies for slopes and sampled surfaces.

Use `body.move(foot, [dx, dz], {trace: true})` to collect accepted supports
in travel order as `contacts`. A slide contributes its actual distance.
Blocked increments contribute no contact. Pass the starting `foot` and
the returned `contacts` to `traversal.cadence({spacing, first, budget})`
via its `advance(foot, contacts)` method. Each event has an interpolated
position, the increment's support and optional material, a zero-based
`index`, and an alternating `side` of `left` or `right`. Cadence carries
unused horizontal distance across calls. `reset()` starts a new cadence
after teleporting or switching movement modes. The defaults are .62 units
between events and .217 units to the first one.

The default body is 1.64 units tall with radius .18, a .34 rise limit
(`stepUp`), and a .48 drop limit (`stepDown`). `minimumNormal` sets the
minimum upward component of a normalized support normal. The body leaves
room for a step below its sampled collision volume. Set `stride` to resolve
smaller features and `budget` to limit the number of increments in a move.
Callers define which surfaces carry weight and which solids obstruct motion.

### Ambient motion

Each member has a stable `id`, an XYZ `home`, and optional `kind`, `seed`,
`speed`, `radius`, `range`, `rest: [min, max]`, `turn`, `yaw`, and `arrival`.
Lengths and speeds use caller units and units per second. Angles are in
radians. A kind can select a ground, water, or air policy.

`arrival` is how close the member gets to a roaming destination before
stopping. It defaults to the smaller of its separation radius and .12.
Use a smaller value for a precise perch or docking point while retaining
the same separation radius. Attraction cues use their own `stop` distance.

- `place(point, member, context)` projects a request onto valid habitat.
- `move(point, delta, member, context)` resolves movement against the
  caller's world. It can use ground traversal, a fluid surface, or a flight
  volume. Both queries return an XYZ point or `null`.
- `destination(point, member, serial, context)` optionally chooses a
  waypoint, perch or other destination. The default samples the member's
  home range with a seeded sequence.

Call `reconcile(context)` to seat the initial roster and after habitat edits.
An invalid member tries nearby positions before going dormant. Advance time
with `advance(seconds, context)` using up to one second per call. The solver
uses a fixed step, tries alternate directions at obstacles, and keeps members
apart by their radii. Render `poses()` for each member's interpolated position,
yaw, distance traveled and current mode.

`attract(id, target, {hold, duration, stop})` introduces a bounded cue. Its
hold interval exposes an `engaged` pose before pursuing the target. Use
`retarget(id, point)` during the cue to follow a moving marker. The caller
controls how contacts are picked, which cues are available, and how the
result is animated or rendered.

`suspend(id)` temporarily puts a member under external control. Its pose
has mode `suspended` and no point. The member keeps its identity and no
longer participates in habitat queries or separation. Use
`resume(id, context, point?)` to project a release point back onto the
current habitat. Omitting the point starts the search from the member's
last position. Both methods return whether the state changed. The caller
can use the same member on a moving platform or during a scripted scene.

### Layer gains and crossfades

`layerMix.create(layers, {budget: 1})` compiles layers with IDs and optional
`gain`, `curves`, `fadeIn` and `fadeOut`. Each curve maps a named control
through increasing `[input, gain]` stops in the range zero to one. The mixer
interpolates between stops, clamps at the ends, and multiplies the curves
for each layer. When the sum exceeds the budget it scales all gains together.

`sample(controls)` returns the target gains by layer ID.
`state(initialControls)` returns a mixer with `gains()` and
`advance(controls, seconds)`. Fades are exponential time constants in
seconds. A zero fade applies the layer target immediately. Feed the same
gains to synchronized audio stems or to any other independently weighted
layers. The mixer has no clock, playback engine, or scene dependency.

### Input actions

`inputActions.compile({edit: {select: ['key:Enter', 'pad:South']}, menu:
{confirm: ['key:Enter', 'pad:South']}})` binds inputs to named actions. The
same physical control may be reused across contexts. Within one context,
each control and exact modifier combination belongs to one action. A
binding such as `{input: 'key:KeyX', modifiers: ['Shift', 'Alt']}` requires
both modifiers, in either order. A binding with no modifiers matches the
unmodified control. Configure analog bindings with
`{input: 'pad:RightX', deadZone: .18, scale: -1}` to remove stick drift and
reverse its direction.

`resolve(context, input, value, modifiers = [])` returns an action and its normalized value,
or `null` for an unbound control. `sample(context, sources)` accepts one
input-to-value object per source for unmodified polling, keeping the strongest
absolute value per action. The first source wins ties. Unpressed actions are zero.
`bindings(context, action)` provides the same binding information for
tooltips or settings. The caller owns polling, key edges, focus, and
persisted overrides. A caller can recompile a changed profile and keep the
previous one if the update contains conflicting bindings.

`inputActions.permutation(controls, overrides = {})` maps each configured
logical control name to a distinct physical control from the same list.
`remap(input)` looks up the physical assignment and passes through controls
outside the list. `swap(logical, physical)` returns a new permutation and
gives the former owner that logical control's old physical assignment.
Persist the returned `overrides` object to restore just the assignments that
differ from the defaults. A caller can apply the same permutation across its
contexts before compiling the action map.

`inputActions.axisMapping(controls, {overrides, inverted})` creates an
immutable mapping for signed analog controls. `project(source)` returns a
sample with all configured axes read from their assigned physical inputs
in one pass. Missing axes read as zero, and buttons and other channels
pass through. Call `swap(logical, physical)` to exchange assignments or
`invert(logical, enabled)` to change direction on a logical axis. Both
return new mappings. Persist `overrides` and `inverted` to restore them.
Project each device sample before applying radial dead zones to logical
axis pairs, then pass it to the context's action map.

`inputActions.radial(x, y, deadZone = 0)` remaps a pair of signed analog
axes together. The pair is zero inside the circular dead zone and reaches
unit length at full deflection. Heading is preserved and diagonal input is
capped to the same maximum as cardinal input. Use it for two-axis movement,
camera control, or any other directional action. Each input axis is in
`[-1, 1]`.

### Ordered paint coverage

`materials.paintMixer([{id, coverage, operation}, ...])` accepts layers in
oldest-to-newest order. Each `coverage(x, y)` returns a scalar in `[0, 1]`.
An add layer contributes that fraction over what remains from older layers.
An erase layer commits its fraction to the background. Subsequent add
layers can paint back over it.

`sample(x, y)` gives the visible `contributions` as `{id, weight}` pairs
and the remaining `background` weight. `pick(x, y, rank)` samples one
ID, or `null` for background, using a rank in `[0, 1)`. Use a stationary
spatial rank for dithered surfaces, or consume the weights directly in a
renderer. The mixer does not impose a brush shape, a material, or a layout.

### Signed intervals on a curve

`edgeClearance.strip(a, b, {halfWidth, extension, above, below})` creates a
constant-width corridor along the XZ projection of two 3D points. The height
band follows their linear grade. `extension` adds distance at both ends and
defaults to zero. `above` and `below` default to .20 world units.
`edgeClearance.footprint(outline, {padding})` defines a clearance region
at all heights from a convex XZ polygon. Padding moves the sides outward
and defaults to zero.
`edgeClearance.ranges(a, b, strips)` clips a 3D edge against the union of
sloped strips and convex footprints, and returns ordered normalized `{kept, removed}` intervals. Sample
these intervals on the original edge to build separate guard, trim or fence
pieces. For piecewise-linear edges, apply the query to each segment.

`edgeClearance.clipFieldPath` accepts a polyline and fields with world
`bounds` and `distance(point)`. It reserves `padding` world units on either
side of each crossing. `spacing` controls discovery and `tolerance` refines
the cut locations. It returns the retained polylines, an empty array when
the whole guide is blocked, or `null` when the guide is clear. If a trace
uses its entire work budget, it omits that field's bounded intersection.

`snapping.resolve(position, features, {tolerance, axes})` returns the eligible
feature, projected point, distance and segment parameter `t`, or `null`.
A feature has a unique `id`, a world point `from`, and optional `to` for a
finite segment. A feature can override `tolerance` or set a numeric `priority`.
After the distance check, higher priority wins, followed by closest distance
and then feature ID. Supply `axes: [0, 2]` to snap in plan and preserve height.
Attach an owner or product-specific data to the feature for use after the snap.

`planSnapping.compile` prepares a convex 2D outline in either winding.
Call `align(moving, [x, y], [{id, plan}], {capture, release, latch})` during
a translation gesture. Candidate corrections put the outlines in contact
along a supporting face and respect the finite extent of that face. The
result includes the corrected translation, contact endpoints and a latch.
Pass that latch back on the next frame to keep the same contact within the
larger release distance. Skip the call and clear the latch when free
placement is active. Targets and plans can be reused for each pointer event.

Use `compileMotion(plan, (point, index) => [vx, vy])` when each vertex has a
constant velocity per parameter unit. Its position at `t` is
`point + velocity * t`. Keep the outline convex with its original winding
through the edit range. `alignMotion` takes the requested parameter and
returns the contact's resolved `value`, guide endpoints and latch. The
`capture` and `release` distances use parameter units, and `min` and `max`
can limit the solved range. It finds both moving points on fixed faces and
fixed points on moving faces, including faces that rotate during the edit.

`railGuard({path, up, height, thickness, postWidth, postSpacing, levels,
maxPieces}, meta)` returns closed construction pieces with the owner, material
and key prefix from `meta`. Posts follow the supplied up direction. The layout
puts posts at ends and corners, then divides each run at or below the given
spacing. The `levels` array gives the rail heights as fractions of guard height.
Call it with retained spans from `edgeClearance` to leave an approach opening.

`pieces.uprightSpan` joins two points on the baseline of a pitched band.
Width is measured perpendicular to the projected run and height is measured
along `up`. The caps stand upright. An optional `extension` extends the
same grade beyond each end by the given projected distance. The default
zero extension keeps a cap at each input point for fitting around openings.

`cantileverSupports.sites({path, outline, spacing, width, seat, minReach,
maxReach, outward, maxSites})` fits stable station indices on a wall path
against a convex XZ footprint. Both sides of the bracket must have bearing
behind the wall before the site is accepted. `outward: -1` reverses which side
of the path is probed. Returned sites include the point, tangent, outward
direction and available reach.
`cantileverSupports.fitMount({origin, tangent, toward, minReach, maxReach,
width, drop, embed, overlap, spacing}, distance)` fits one site against the
first solid surface within a reach interval. The supplied horizontal tangent
and direction form a perpendicular unit frame. The distance callback returns
negative values inside a candidate solid. The fit also probes the width and
height of the embedded pad, so apertures or insufficient backing can reject
the mount. Pass the result directly to `bracket` with the same dimensions.
`cantileverSupports.bracket(site, {width, drop, embed, overlap, profile}, meta)`
extrudes a convex side profile into a closed piece. Positive profile coordinates
scale by reach and overlap. Negative coordinates scale by embed and drop.
`cantileverSupports.intersects(piece, planes)` tests the result against a
convex keep-out volume. These functions share the existing convex pieces and
clipping code.

`traceSignedIntervals(sample, {range, maxSlope, step, tolerance, maxSamples})`
returns ordered pairs `[low, high]` where `sample(t)` is negative. The
parameter range defaults to `[0, 1]`. The sampler may be a signed distance
evaluated along a route or a surface chart, or any signed scalar function.
Supply a conservative `maxSlope` in field units per parameter unit to
skip ranges that cannot cross zero. Without the bound, the trace refines
uniformly to the discovery scale.

`step` limits the undiscovered interval width and `tolerance` refines the
endpoints of detected crossings. Features smaller than the discovery step
may be missed. The result also reports `samples` and `complete`. When the
trace exhausts `maxSamples`, it returns its best bounded approximation
with `complete: false`.

### Terrain routes between pins

`routes.fitStairApproach({landing, direction, height, outline, width, accept, inside,
rise, tread, minRise, maxRise, minRun, maxRun, step, budget})` scans out from a
landing along a horizontal direction. It finds the shortest sampled run that
meets the tread and rise constraints and clears the sampled ground. Give
`outline` as a convex XZ polygon with `width` to seat the full width of the
landing on a platform. `accept(point)` restricts the search to a connected
approach. `inside(point)` allows initial overlap before the run leaves a
carrier. The result gives `landing`, `toe`, `axis`, `run`, `climb`,
`risers`, `tread` and `rise`, or `null` if the constraints cannot be met.
The default probe spacing is .06 with a budget of 256.

`routes.terrain(start, end, options)` takes exact `[x, y, z]` pins with
distinct XZ coordinates. Supply `bounds: {min, max}` to limit the XZ search,
and `height(x, z)` to set the candidate centerline elevation. Add any intended
offset above the ground to this callback. Pin elevations are supplied
independently.

- `cell` controls the grid spacing. `sampleStep` controls checks along an
  edge and defaults to a third of the cell size.
- `maxSlope` is rise over horizontal run. It applies to the segment grade
  and to changes in the terrain sampled along each edge. `slopeCost` penalizes
  both uphill and downhill travel.
- `clearance(x, y, z)` supplies a signed obstacle distance at the route
  centerline. Set `minClearance` to account for the half-width and any margin.
  `keepOut(x, z, y)` blocks authored areas when it returns true.
- `cost(x, y, z)` supplies a nonnegative penalty per unit of horizontal
  travel. Positive infinity marks an impassable point. `turnCost` adds a
  penalty per radian of heading change.
- `maxDeviation` limits how far a segment can leave the height field.
  `lookAhead` bounds simplification. Use zero to keep the grid turns.

Callbacks should be deterministic. Clearance, grade, and keep-out checks
are sampled, including on shortcuts. Choose `sampleStep` and a clearance
margin for the smallest feature you need to avoid. A route can be unreachable
at a coarse grid spacing if the grid misses an available corridor.

An `ok` result includes a `route` compatible with `routes.layout` and a
weighted `cost`. Other statuses are `blocked-pin`, `unreachable`, and
`budget`. A budget result names the exhausted limit. Configure `maxCells`,
`maxVisits`, and `maxSamples` to bound work. The result reports counts in
`work`.

The runnable example uses ordinary SDFs for the ground, boulders, and
paving, then bakes two versions of the scene as splats. The pins are identical
in both versions.

```sh
node cli/ink-studio.js render examples/terrain-route.js --seed 13 --ortho --colored
node cli/ink-studio.js render examples/terrain-route.js --seed 14 --ortho --colored
```

### Visibility, corner fitting, and travel time

`P.routes.visibility(start, end, obstacles)` finds a shortest path in plan
between XYZ pins. Each obstacle is a simple polygon of XZ points. The path
can touch polygon boundaries. Convex obstacles use half-plane clipping.
Use expanded obstacle outlines to leave room
for the width of the realized path. Intermediate elevations interpolate
along the route.

`P.routes.convexFootprint(samples, {margin})` builds a counterclockwise XZ
hull from unordered samples, with interiors, duplicate samples and
collinear edges removed. A positive margin expands it by a circumscribed
octagon. This conservatively bounds a disk of that radius swept around the
hull. Use it for plans around projected solids, clearance for a swept deck
or an agent radius. Select the obstacles that intersect the relevant height
range before passing their footprints to `visibility`.

Use `visibility(start, end, obstacles, {links})` to admit a bridge,
gate or other certified crossing. Each link supplies
`{start: [x,z], end: [x,z], through: obstacleIndex}`. A composite obstacle
can use a nonempty array of distinct obstacle indices for `through`.
The link contributes two graph vertices and a connection that skips the
specified polygons. The ends should sit outside those polygons. Link
`direction` defaults to `'both'`. Use `'forward'` for start to end or
`'reverse'` for end to start when the crossing was checked in one direction.
Elevation links in `prismVisibility` use the same option with the first and
last supplied points as their ends.
Optional `via: [[x, z], ...]` passes through up to sixteen private waypoints.
Each leg checks the other obstacles. The complete length contributes to the
shortest-path cost and to the interpolated grade. Waypoints count toward the
vertex budget and appear in the returned route as part of the link's
`{link, from, to}` point range. The caller checks the lifted section because
the chosen route determines the final elevations.

Use `waypoints: [[x, z], ...]` to supply ordinary graph vertices from a
sketch, medial path or sampled field. With `domain: {clearance, spacing,
minClearance}`, the planner probes every candidate leg against a signed XZ
clearance field, including legs inside passage links. Values at least
`minClearance` (default zero) permit passage. Probes count against
`maxTests`, and waypoints count against `maxVertices`. This supports
clearance fields composed from paint, erasure, and other masks. Probe
spacing governs the smallest feature the search can detect.

`P.routes.sweep(start, end, {halfWidth, below, above, spacing, minClearance,
clearance, maxSamples})` checks a sloped rectangular section with a horizontal
side axis and vertical height. Its callback returns a signed distance
with positive values in open space. The result reports `ok`, `blocked`
or `budget`, a sample count and the first failing point when blocked.
Sampling resolution governs the smallest obstruction it can detect.
Use tighter spacing or explicit obstruction checks for thin objects.

Pass `sectionBands` to give the sweep up to sixteen rectangular parts.
Each has `lateral: [min, max]` and `vertical: [min, max]` measured from
the route center in world units. Positive lateral distances follow the
horizontal left axis of travel, so reversing a route reverses those bands.
Bands can describe a floor, one or two guards, or overhead equipment.
All occupied probes share the same sample limit.

`P.routes.sweepPath(points, options)` takes the same section controls and
sample budget. It checks each leg and the joins at changes of heading. A
rectangular section uses full rounded joins. Banded sections sweep their
lateral intervals through the turn, including the bevel between legs.
Clearance checks can use the point range returned for a bent link.

`P.routes.profileSection(profile, start, end, options)` fits a straight
section of a world-space route into an extrusion of a convex profile.
Supply an affine `project([x,y,z]) => [u,v]` into the profile's chart and
XZ endpoint positions. The section stays horizontal across its width with
`halfWidth`, `below` and `above` in world units. `clearance` insets the
profile in chart units. Set `minHeight`, `maxHeight` and `maxGrade` for
the route. A grade of zero fits only level sections. You can also supply
`sectionBands` to fit the occupied parts of an asymmetric section.

The result contains a convex set of feasible `heights: [[startY,endY], ...]`
and `closest([startY,endY])` for fitting toward a preferred pair. The set
can be a segment or point. A missing fit returns `null`. The plane
constraints cover the whole swept section along the leg. Apply additional
solid and terrain checks for the rest of the scene.

`P.routes.sectionHeightBands(path, options)` samples a planar guide made from
XZ points. Supply a section with `halfWidth`, `below` and `above`, or supply
`sectionBands`. The callback `clearHeights(x, z, low, high)` receives one
part's vertical offsets at a point in the footprint. Return the permitted
interval for the route's center height, or `null` when the point adds no
constraint. For an open vertical interval `[floor, ceiling]`, return
`[floor - low, ceiling - high]`. Either end can be unbounded.
The function intersects these intervals with `minHeight` and `maxHeight`,
using the same angular footprint as `sweepPath` at bends.

Set `spacing` and bound the work with `maxStations` and `maxSamples`.
An `ok` result includes the sampled `stations` and the number of probes.
Every station has an XZ `point` and is ready for `fitHeightBands`, with the
original guide points marked `keep`. Contradictions return `blocked` and
an exhausted limit returns `budget`. Verify the finished 3D route with
the clearance field used for the final sweep.

`P.routes.fitHeightBands(samples, {maxGrade, maxPoints})` fits a grade-limited
height profile through ordered stations. Each record supplies `at`, `min`,
`max`, and optional `preferred` height and `keep` flag. A fixed-height
station has equal bounds. The result contains the selected sample `indices`
and their `elevations`; interpolate between them to satisfy every sampled
band. Set `keep: true` at horizontal bends and other required joints.
`null` indicates contradictory bands, insufficient grade, or insufficient
point budget. Use the caller's geometry to verify clearances between samples.

`P.routes.elevationProfile(length, startY, endY, barriers, options)` finds
a grade-limited route in the distance and elevation plane of a fixed guide.
Each forbidden band is `{from, to, min, max}`, where `from` and `to`
are stations along the guide and `min` and `max` are elevations. Reserve
deck thickness, stair rise and any overhead fixtures in those bands before
solving. `maxGrade` is rise per unit of horizontal run. `minHeight` and
`maxHeight` restrict how far the profile can dip or climb. Successful
results return `points: [[station, elevation], ...]` with exact endpoint
heights. Forward-only edges keep route stations ordered. Search limits
`maxVertices` and `maxTests` apply as in visibility routing.

`P.routes.elevationFrame({drift, datum})` describes a guide plane whose
XZ origin shifts by `drift: [dx, dz]` per unit of elevation above its
`datum`. Use `project(worldPoint)` before planning and `lift(framePoint)`
to recover world positions. Both retain the input Y. `prismFootprint(ring,
min, max, options)` projects the convex horizontal footprint over the
active height band and returns a conservative hull. `grade(maxWorldGrade)`
returns a reference-frame grade limit that stays within the requested
world grade after lifting. Measure final path lengths in world space.

`P.routes.guideElevation(guide, startY, endY, prisms, options)` fits the
elevation profile of a fixed piecewise-linear XZ guide. It clips each span
against convex prism footprints and runs the grade solver in accumulated
horizontal station space. Use `minHeight`, `maxHeight`, `maxGrade` and
`maxLength` for route limits. The output retains each original bend.
`flights: [{first, last}]` gives inclusive point indices for continuous grades
or level intervals. These let a stair builder keep one tread sequence across
several bends. `stations` contains horizontal run, `distances` contains 3D
arc length, and `crossings: [{prism, from, to}]` identifies the projected
obstacle intervals by input prism index and horizontal station. The
profile reports blocked pins, unreachable routes and budget limits.

`P.routes.uprightMotion(before, after, tolerance = 1e-5)` takes equal-length
arrays of paired 3D points. It returns `{R, t}` for a yaw and translation
that fit every pair within the given world-space tolerance. A vertical guide
can translate with identity rotation. The result is `null` when spacing
or rise changes, so a caller can refit treads or parts that need to stay level.

`P.routes.stripFootprint(start, end, halfWidth, extension = 0)` returns the
four corners of a constant-width strip in a planar chart. The extension adds
the same length at each end. A collapsed span returns an empty array. Use
the outline as a fitted surface, a convex keepout or the input for a join.

`P.routes.fitReturn(approach, destination, options)` fits a finite-width
planar route from the first approach point to a fixed destination. Supply
the occupied `occupiedHalfWidth`, the returning `halfWidth`, and optionally
`toeExtension`, `clearance`, `maxLength`, and obstacle polygons. Obstacles
use their outlines before widening. The solver reserves the approach in an
aligned frame and widens the reservation by the returning width. Its
entrance and any exit close to the reservation keep straight leads.
It can route around either open side. Success returns `{status:'ok',
points, length}`. A failure reports `blocked-pin`, `unreachable`, or
`budget` while leaving the input coordinates unchanged.
When both pins need straight leads, give an `endApproach` starting at
the destination. The same search reserves both approach footprints and
tests both leads against the other approach and the supplied obstacles.

`P.routes.stripJoin(previous, corner, next, halfWidth, options)` joins
two equal-width strips at three planar points. It returns `null` for
collinear or collapsed legs. Its `exterior` polygon fills the outside gap
between the two cross sections. `maxArcAngle` sets the greatest angle
between successive points on the arc and defaults to π/8. Use π for a
straight bevel. `join.clip(polygon, 'incoming' | 'outgoing')` partitions
a convex footprint by the turn bisector. A caller can clip sloped or
stepped parts independently, then extrude the corner at the required
height so neighboring parts keep their own profiles.

`P.routes.landingFootprint({center, tangent, width, depth, approaches})`
fits a level rectangular pad in the world XZ plane. Depth defaults to width.
Each approach provides a 3D `point` and a `direction` pointing into a space
the pad must leave clear. The function clips the pad by those planes and
returns its remaining convex XZ outline. A plane can begin beyond the node
to keep a short level approach before a downhill run. Use the same outline
for the pad's rendered solid and support volumes. An empty outline means the
approaches use all of the room at that node.

`P.routes.guideVisibility(guide, obstacles, options)` repairs blocked
intervals of a piecewise-linear XZ guide. Supply convex clearance footprints
and optional `reserved` footprints for regions the route must stay outside,
such as the host of an offset route. The planner adds `lead` units at both
ends of each blocked interval before merging overlaps. Each replacement
stays within `maxDeviation` of its original interval, including the interiors
of the returned segments.

The pins and guide vertices outside the replacement intervals stay fixed.
Successful results supply XZ `points`, `length` and
`splices: [{from, to, first, last}]`. Distances `from` and `to` are measured
along the original guide. Indices `first` and `last` identify the inclusive
range in the replacement route. Apply `maxLength`, `maxVertices` and
`maxTests` to bound the solve. The search uses a finite graph of rejoin
points, guide bends and obstacle corners.

`P.routes.prismVisibility(start, end, prisms, options)` plans in three
dimensions through a finite visibility graph. Each prism supplies a convex
XZ `ring` and vertical bounds `min` and `max`. Expand these bounds to reserve
space for the object traveling the route. The graph considers footprint
corners, straight-guide intersections, obstacle elevations, and optional
XYZ `waypoints`. Edges use exact clipping against the convex prisms and
respect `maxGrade`, `minHeight`, `maxHeight`, and `maxLength`. An optional
`floor(x, z)` supplies a sampled ground constraint. The result gives
`ok`, `blocked-pin`, `unreachable`, or `budget` with work counters, and
frozen XYZ points on success. Tangency to the clearance boundary is allowed.

`geometry.inclinedPerimeter` projects an affine extrusion's convex local
XZ ring into a horizontal reference plane. As the world height changes, the
cross-section drifts along the extrusion axis. Each edge of `poly` is
padded by `offset` plus the maximum outward drift between `below` and
`above` relative to a guide point. `raw` holds the reference section.
Use `project(worldPoint)` and `lift(referencePoint, worldY)` to move
between frames. `allows(points, tolerance)` clips each XYZ leg in the
reference frame and tests that it stays outside the expanded section.
The local extrusion axis must have a positive world Y component at least
one fifth of its length.

`geometry.convexPerimeter(outline, {offset, drift, below, above, miterLimit})`
returns a contour in XZ and a `sections` entry for each contour segment.
The `edge` index identifies the input edge. A section marked `bevel`
belongs to the input vertex at that index. When a convex miter exceeds
the specified ratio, the contour adds a tangent plane at the bisector.
The tangent encloses the same spatial clearance as the neighboring planes
while shortening the join. The optional section drift pads all three
planes for the same vertical sweep. `inclinedPerimeter` accepts the same
`miterLimit` option and returns those section identities alongside `poly`.

Supply `links: [{points, through}]` to attach explicitly cleared XYZ
polylines to the graph. `through` lists zero-based indices of prisms whose
clearance is already accounted for by the link, such as a door through a
wall. Both endpoints must be outside the interiors of all prisms. The
link is bidirectional and satisfies the same grade, height, floor and
length checks as ordinary edges. Every unlisted prism is still tested.
An accepted route includes `links: [{link, from, to}]` with the input link
index and inclusive indices into the returned point list. Any bends within
the link are preserved in traversal order.

For dense rounded obstacles, supply `maxSides` to `P.routes.convexFootprint`.
It caps the number of support planes and keeps the entire margin-expanded
hull inside the result, so the planner can use fewer vertices while
preserving clearance.

`P.foldedRibbon.compile(faces, {origin, offset})` builds a continuous chart
around an oriented planar loop. Each face supplies a keyed edge `a` and
`b`, an `up` direction, and its outward `normal`. `origin` selects the
zero station along the closed perimeter. `offset` moves the frontage
along its mitered normal, and `inset` gives a bound for inward extrusion.

`ribbon.region(min, max)` returns the occupied bands over a station interval.
Use `map([station, height, depth])`, `project(worldPoint)`, and `bounds(box)`
for shared surface coordinates. `mesh(localMesh)` clips triangles at the
band boundaries and maps their positions, normals, UVs and material groups.
Affine mirrored contours retain outward winding. The chart can carry any
swept detail whose bounds fit the region and the safe inset.

`P.routeStations.remap(before, after, edits)` returns a function mapping an old
normalized route station to a new one. Supply ordered `{key,length}` sections
and optional `{from,to,fromRange,toRange}` interval mappings. Ranges default to
`[0,1]`. Use a descending `toRange` to map onto a reversed section.
Dividing one old range among new sections models a split, and
dividing one new section among old spans models a join. Sections whose keys
persist keep their local fraction. An empty or removed section with no
target yields `null`, so an attachment host can choose its geometric fallback.

`P.routes.spline(route, {radius, spacing, clearance, minClearance})`
rounds corners using quadratic splines, shrinking the trim when needed.
Unfit corners stay in the route. The result contains the fitted control points
and a checked, sampled polyline. Optional `keepOut`, `height`,
`maxDeviation`, and `maxSlope` limit the centerline. Finite resolution
controls the clearance guarantee.

`P.routes.travelTime(sources, {bounds, cell, speed})` solves a travel-time
field with fast marching. The sources and bound vectors are XZ. A
`speed(x, z)` of zero or less blocks travel. Query `time(x, z)` for
interpolated arrival time or `trace([x, z], {height})` to trace an XYZ route
toward a source. The traced route uses continuous descent when available
and passable grid links where interpolation cannot descend. Traversal and
boundary accuracy depend on the lattice spacing.

The SDF example compares a short visibility path with a travel-time route
that prefers firmer ground, using the same pinned trailheads.

```sh
node cli/ink-studio.js render examples/route-fields.js --seed 0 --ortho --colored
node cli/ink-studio.js render examples/route-fields.js --seed 1 --ortho --colored
```

### Triangulation and branching networks

`P.geometry.delaunay(points, {constraints})` takes distinct planar points.
It returns indexed triangles, edges, and recovered constraint segments.
Each constraint is a pair of point indices. Segments can meet at sites,
including sites on a longer input segment. A proper crossing requires an
explicit shared site. The collinear case returns a connected edge chain.
`P.geometry.triangulatePolygon(rings)` uses even-odd fill for outer
boundaries and holes. Its indexed output can cap a solid or serve as an
interchange representation.

`P.routes.network(points, {loops, minStretch, cost})` derives candidate
links from the XZ site positions and chooses a minimum spanning tree
over their costs. Extra links reduce detours. `cost(a, b, aIndex, bIndex)`
can reject a link with infinity. Pass retained breaklines through
`constraints` to include them in the candidate graph.

`P.routes.steiner(points, edges, terminals)` uses shortest paths between
terminal indices, shares their links, then prunes non-terminal leaves.
Supply candidate edges as `{a, b, cost}`; omitted costs use XYZ lengths.
Both tools return individual routes for realization as SDF sweeps, pipes,
or terrain-aware connectors.

The two versions of `examples/branching-networks.js` show a road tree
with extra loops and shared conduits serving a terminal subset.

### Street systems, parcels, and medial paths

- `routes.tensor(components)` blends `grid`, `radial` and `ring` direction
  fields. A component has an XZ `origin`, optional orientation `angle`,
  `strength` and falloff `radius`. The sampler gives orthogonal major
  and minor directions.
- `routes.followTensor(field, seeds, {bounds, height, mask})` traces
  streets in both directions. A seed can be an XZ point or a record
  with `point`, `family` and `id`.
- `routes.growStreets(seeds, options)` grows a connected road graph
  from seeds with `point` and `angle`. An optional tensor biases the
  heading. Terrain grade, allowed areas, and a travel penalty affect
  proposals. Crossing roads split at a shared junction. Segment and
  work limits return the valid graph realized up to that point.
- `routes.parcels(outline, {edge, pitch, depth, gap})` fits lots along
  one road-facing edge of a simple block. It clips strips to the outline
  and keeps fragments connected to the frontage. Each lot has a stable
  slot ID, area and XZ fragments usable as SDF extrusion profiles.
- `routes.medial(rings, {spacing, minRadius, height})` approximates an
  interior medial graph from nearest boundary samples, including holes.
  Nodes report clearance radii and edges provide world routes.

`examples/street-layouts.js` compares street traces and seeded growth beside
the same street-front lots.

### Watersheds and river networks

Pass `P.hydrology.analyze(height, {bounds, cell, origin, channelArea, lakeAt})`
a deterministic `height(x, z)` callback and a bounded XZ work region. The
lattice is aligned to the world coordinates in `origin`, which defaults
to `[0, 0]`. Drainage uses Priority-Flood depression filling and D8
steepest descent. Interior flats follow the flood path towards an outlet.
The boundary represents the extent of the drainage model. Re-run the analysis
when the extent, elevation, or rainfall changes. The optional
`rain(x, z, y)` supplies a nonnegative multiplier for each cell's area.

- `fields` contains row-major typed arrays, X first. Elevation is the authored
  surface, drainage height is the filled surface, and terrain height applies
  fills only outside authored lakes. `receiver` is the downstream sample
  index or `-1` at an outlet. Treat the arrays as analysis results when
  reusing them with the point queries.
- `sample(x, z)` interpolates scalar data such as accumulation and wetness.
  Catchment and lake IDs, lake level, and stream order use the nearest
  lattice sample. It returns `null` outside the sampled region.
- `reaches` contains ordinary arc-length routes separated at stream starts,
  junctions, lakes, and outlets. The first directed world-lattice edge
  determines a reach ID. The same edge keeps its identity while the lattice
  alignment and that section of the graph agree. Set `channelArea` to the
  minimum contributing area for a visible channel.
- `lakeAt(x, z, y)` may return a lake ID, `{id, level}`, or `null`.
  An authored lake keeps its bed in `terrainHeight` and its specified water
  level. The drainage grid routes through it, and internal lake channel
  segments remain submerged. Its network node connects incoming and outgoing
  reaches. `wetness(x, z)` returns one on sampled lake interiors.
- `distributed: true` also returns D-infinity area accumulation with
  `receiver`, `secondary`, and `secondaryShare` arrays. Flow may split
  between adjacent downhill directions adjoining the steepest facet.
  The reach and catchment APIs describe the D8 network.

The splat example uses the network to place river surfaces and the wetness
field to darken banks and place reeds around an authored pond.

```sh
node cli/ink-studio.js render examples/watershed.js --ortho --colored
```

### River editing and habitats

- `P.hydrology.breach(basin, {grade, maxDepth, maxLength})` finds filled
  depressions and follows their spill paths. A successful cut lowers the
  channel to a continuous grade. Over-budget cuts report their cause before
  any height is changed. Lakes may receive flow without being excavated.
- `P.hydrology.incise(basin, options)` uses contributing areas and local
  grades to lower unlocked downstream-facing cells. Use `strength`,
  `areaExponent`, `slopeExponent` and `maxDepth` to control the edits.
  Both editors return gridded heights and an interpolating `height(x, z)`.
- `P.hydrology.meander(route, options)` resamples a route and migrates
  its curves while keeping the pins and the longitudinal elevations.
  `curvatureGain` and `smoothing` shape the migration. Optional seeded
  `amplitude` starts bends on straight reaches. If `cutoffDistance` is positive,
  nearby sections separated by a long loop can detach as cutoff routes.
- `P.hydrology.corridor(routes, height, options)` returns `floodplain`
  and `levee` fields from plan distance, relative elevation, and local
  slopes. `channelWidth` and `floodWidth` are distances from the centerline.
  Levee height fades out on steep or elevated banks.
- `P.hydrology.habitat(basin, {wind, sun, humidity, uplift, waterDistance})`
  advects vapor along the lattice, drops precipitation on windward slopes,
  and returns interpolated fields for moisture, exposure, temperature, and
  proximity to water. `lapse` cools terrain with elevation. Use these
  fields in density or material callbacks.

`examples/river-processes.js` bakes the same endpoints as a straight channel
or a migrated river with floodplain vegetation. Seed 1 enables the terrain edits.

### World-space biome queries

`P.biomes.create({fallback, regions, media, solid, conditions})` prepares a
query for the same world coordinates used by terrain, placement and gameplay.
It is available through the Node toolkit and browser bundle.
`sample(x, y, z, time = 0)` returns `{biome, weights, medium, conditions}`.
`mediumAt(x, y, z, time = 0)` returns the medium alone and skips biome and
condition sampling.
`inspect(x, y, z, time = 0)` adds the IDs, biome IDs, and raw weights of all
regions whose bounds contain the query, including zero-weight regions.

- Each region has a unique `id`, inclusive XYZ `bounds: {min, max}`, and
  an optional `biome` ID that defaults to the region ID. `weight` defaults
  to 1 and accepts a number in [0, 1] or a callback
  `(x, y, z, time, conditions, medium)`. Overlapping regions of the same
  biome contribute their maximum. The fallback (default ID `default`)
  fills any weight left below a total of 1. Totals above 1 are normalized.
  The result lists positive `{id, weight}` entries from highest to lowest,
  with ties resolved by ID. `biome` is the first ID in that list.
- Each medium has a unique `id`, inclusive XYZ `bounds`, and `kind` of
  `water` or `air`. Its optional `sdf(x, y, z, time)` restricts its
  interior to negative samples. Water also requires a `surface` height
  (a number or `(x, z, time)`) and occupies points strictly below it.
  Its `current` is an optional XYZ velocity or `(x, y, z, time)` callback.
  Overlapping media resolve by highest integer `priority` (default 0)
  and then by ascending ID. Use an air volume of higher priority for a
  pocket inside water.
- A negative sample from the optional `solid(x, y, z, time)` terrain
  field takes precedence over all media. Open space defaults to air.
  `medium` returns `{kind, id, surface, depth, current}`. Water depth is
  the vertical distance below the selected surface. Open air and solid
  have a null ID. All non-water samples have a null surface, zero depth
  and zero current.
- `conditions(x, y, z, time, medium)` can return a record of finite scalar
  values such as moisture, exposure and temperature. A nullish result
  supplies an empty record. Both the returned condition record and the
  medium are read-only. Use `hydrology.habitat(...).sample(x, z)` as an input
  for open terrain, or return a different profile inside sheltered volumes.

Use conservative bounds covering a region's full blend and a medium's
full extent over the sampled time range. The query captures definitions
and bounds when created and skips region and medium callbacks outside their
bounds. Supply deterministic callbacks and the same definitions, world
coordinates and time to adjacent chunks. Create a new query when editing
the definitions or changing their bounds. A callback can sample external
fields, so their revision must stay consistent across consumers.

```js
const bounds = { min: [-2, -6, -2], max: [2, -2, 2] };
const cave = (x, y, z) => Math.hypot(x, y + 4, z) - 2;
const world = P.biomes.create({
  fallback: 'forest',
  solid: (x, y, z) => Math.max(y, -cave(x, y, z)),
  conditions: (x, y, z, time, medium) => ({
    moisture: medium.kind === 'water' ? 1 : 0.3,
    exposure: y >= 0 ? 1 : 0
  }),
  regions: [{ id: 'cavern', bounds, weight: (x, y, z) => Number(cave(x, y, z) < 0) }],
  media: [
    { id: 'aquifer', kind: 'water', bounds, sdf: cave, surface: -3, current: [0.3, 0, 0] },
    { id: 'air-pocket', kind: 'air', priority: 1, bounds,
      sdf: (x, y, z) => Math.hypot(x, y + 3.5, z) - 0.25 }
  ]
});
world.sample(0, 1, 0);       // forest, air
world.sample(0, -4, 0);      // cavern, water with depth 1
world.mediumAt(0, -3.5, 0); // air pocket within the cavern
```

In [river-processes.js](../examples/river-processes.js), the same biome query
drives the ground's splat palette and the placement of floodplain reeds.

### Water bodies

A water body captures wet intervals and current for each cell of an XZ grid.
Use the same water frame for world queries and the
[WebGL renderer](browser-renderer.md#water-optics).

```js
const W = K.procedural.waterBodies;
const inlet = W.create({
  id: 'inlet',
  bounds: { min: [-5, -5], max: [5, 5] },
  resolution: [24, 24],
  sample(x, z) {
    const bed = terrainHeight(x, z);
    return { bed, surface: 0.5, current: [0.15, -0.2] };
  }
});
const water = W.scene([inlet]);
const environment = K.procedural.biomes.create({ media: water.media, solid: terrainSdf });
const world = builder.finish({ water });
const bodyMedium = environment.mediumAt(...bodyCenter);
const eyesMedium = environment.mediumAt(...eyePosition);
```

- `create` samples column centers once. Use `null` or `surface <= bed`
  for a dry cell. The default resolution is `[1, 1]`. Each axis supports up
  to 64 cells. Heights are constant inside each cell and captured at Float32
  precision for WebGL. A wet cell owns its lower XZ edges and excludes its
  upper edges. Medium membership is strictly between bed and surface.
- `inlet.columnAt(x, z)` returns `{bed, surface, depth, current}` for a
  wet column and `null` elsewhere. Column depth measures the whole water
  column. The biome query instead reports depth from the sampled XYZ point
  to the surface and returns currents as XYZ vectors. A host controller can
  sample the body center for swimming and current drift, and sample the eyes
  separately for submersion.
- `inlet.shoreline()` returns world-space segment endpoint pairs along wet
  cell edges bordering dry cells or the grid exterior.
  `inlet.particles({seed, count})` returns seeded `{position, current}`
  samples inside wet cells. Emit Gaussian splats there for suspended detail.
- `W.fromShallowWater(solver.snapshot(), {id, optics})` captures the existing
  solver's bed, level, and XZ velocity. A solver larger than 64 cells on either
  axis requires an explicit render `resolution` within that limit. Publish a
  new scene and build its biome query from the same revision when the solver
  advances. Previous frames remain readable.
- A scene supports up to 256 bodies with distinct IDs and nonoverlapping
  XYZ bounding interiors. Larger scenes use a spatial ray index in the WebGL
  texture atlas, with a total budget of 2048 × 2048 texels including metadata.
  The overlap check uses the full span grid bounds for layered
  bodies so tagged air and water agree across tiles. Bodies can sit at
  different heights at the same XZ.
- `W.fromSpans(grid, {id, optics})` packs up to 32 wet intervals per column
  from a [vertical span grid](#vertical-spans). Interval IDs, XYZ flow and
  named air are available in `scene.media`. Reuse a medium ID across
  neighboring layered bodies to keep it continuous in gameplay queries.
  Depth is measured to the top of each contiguous water run. The renderer
  highlights a waterline only where air meets the top of the run. All
  intervals share the default optical settings when given a profile object.
  Pass `optics(mediumId, grid)` to choose a profile per water medium in a
  tile. Return `undefined` to select the built-in defaults. Treat the
  resolver and captured data as immutable for each revision.
- `W.sceneFromSpans(tiles, {previous, optics})` publishes a collection of
  span tiles. Up to 256 tiles with water or named air can enter one scene.
  A previous scene from this helper retains bodies for unchanged grids. If
  the set of rendered grids and their optics match, it returns the same scene.
- `W.scene(bodies, {airPockets: [{id, bounds}, ...]})` accepts up to eight
  axis-aligned XYZ air pockets. Their strict interiors override water
  membership and subtract dry intervals from the WebGL light path. Overlapping
  pockets subtract their union. The body surface still drives ripples, foam
  and refraction. Use the scene's `media` to share the same pocket geometry
  with the biome query.
- `next.changesFrom(previous)` returns conservative dirty bounds for
  physical column or pocket changes. Layered bodies report adjacent columns
  as runs within each grid row. Single-interval bodies return a bounding box
  over their modified columns. Optics-only edits use the new render snapshot
  directly.

### Vertical spans

`P.verticalSpans.create({bounds, resolution, sample, maxSpans})` captures
ordered `{min, max, kind, id?, material?, current?}` intervals per XZ column.
`sample(x,z,i,j)` receives the world-space cell center and grid indices.
Kinds are `solid`, `air`, and `water`. Gaps are air. Each interval owns its
lower Y boundary through to its upper boundary, exclusive. `grid.at(x,y,z)`
returns the interval and `grid.column(i,j)` returns all intervals in ascending
Y order. `grid.pack()` copies offsets, Float32 height pairs, label indices and
the label palette for host processing.

`P.verticalSpans.bake({bounds, resolution, solid, volumes, step, refine,
maxSamples, maxSpans})` samples a solid SDF and signed volume fields at each
column center. Each volume supplies `{id, kind, field, priority?, material?,
current?}`. Negative samples are inside. Solid wins over every volume, then
higher priorities win, with IDs breaking ties. Water currents can be an XYZ
vector or an XYZ function sampled inside each interval. The baker refines sign
changes between vertical samples. Choose a `step` small enough to sample the
thinnest feature that must survive, and choose XZ resolution to fit the
smallest relevant horizontal detail.

`P.verticalSpans.bakeTiles({tiles, solid, previous, dirtyBounds, ...controls})`
accepts tile descriptions with stable `id`, XYZ `bounds` and XZ
`resolution`. Supply conservative XYZ `dirtyBounds` covering all changed
solid or volume samples to retain unchanged grids from `previous`. An empty
array declares that the fields are unchanged. Sampling controls and explicit
`volumes` must also match for reuse. Omitting `dirtyBounds` requests a full
bake. The result's `ids` and `tiles` follow input order, and `work` reports
solid samples, rebaked tile IDs, grids that actually changed, and removals.

### Retained biome recipes

`P.biomeRecipes.create({seed, fallback, recipes, regions, media, solid, conditions})`
combines recipe data with the shared XYZ biome query. It returns an authoring
object and its retained `document`. `author.view()` gives a read view of one
document revision. Baking, placement, and inspection can share that view.
Edits become visible on the next view and earlier views continue to read their
captured definitions. Keep external terrain and environment samplers stable
for the lifetime of a view.

Recipes are JSON records with an `id` and at least one named `materials` ramp.
The other fields are optional.

| Field | Meaning |
| --- | --- |
| `landform: {kind, height}` | A named landform and a height offset given as a number or [procedural field](#composable-procedural-fields). Shared biome weights blend the offsets. Apply the result to a host terrain carrier. |
| `materials: {role: [color, ...]}` | Named ramps with up to 32 colors each. Colors accept hex strings, 24-bit integers, or normalized RGB triples. |
| `strata: {fallback, layers}` | Material role names selected by height relative to the carrier surface. A layer has `min`, `max` and `material`, with an optional `id` and `pattern`. Negative heights are underground. The fallback defaults to the first role by ID. |
| `habitat: {media, ranges}` | Optional allowed medium kinds and scalar conditions. A range supplies `min`, `max`, or both. Optional `fade` is the distance outside the range over which its weight falls to zero. Missing condition values contribute zero. |
| `populations` | Records with `id`, `species`, `asset`, `density` in [0, 1], and optional `habitat`. Each rule scales its density by its recipe weight, habitat weight, and paint exclusion. |
| `landmarks` | Records with `id`, `asset`, and `at` as normalized XYZ coordinates in a region. Optional seeded `jitter` and population `clearance` are in world units. |
| `routes` | Records with `id`, `points`, and optional population `clearance`. A point is normalized XYZ or `{landmark: 'id'}`. Unpinned routes follow pinned landmark references. |
| `ambient`, `traversal` | Ambient cue records `{id, gain}` have a gain in [0, 1]. Views blend gains across recipes. Traversal tags are strings from the highest-weight recipe. The host maps IDs and tags to assets and behavior. |

Regions name an `id`, a `biome` recipe and inclusive XYZ `bounds`. An
optional `weight` in [0, 1] defaults to 1. An optional seeded `field` expression
contributes a second weight clamped to [0, 1]. Medium and conditions use
the existing biome sampler. Habitat ranges can refer to any condition the host
supplies, as well as `elevation` (world Y) and `depth` (from the local medium).
The fallback recipe fills unused biome weight. Its population rules still
test their own habitat.

- `setRecipe(recipe)` and `setRegion(region)` add or replace the named JSON
  records. `removeRegion(id)` removes the region and leaves its authored pins
  available if the region returns. `setSeed(seed)` reseeds fields and generated
  placements. Paint and pins stay in world space.
- `paint({id, channel, target, operation, points, width, softness, radii,
  strength, height})` uses the `masks.stroke` swept-disc shape.
  Points are XZ. Optional `height: [minY, maxY]` restricts the stroke vertically.
  `strength` defaults to 1. A `biome` add stroke blends toward its target
  recipe; an erase blends back toward the procedural weights. A
  `population` stroke adds or erases a species exclusion, with `*` for all
  species. Global and species exclusions combine multiplicatively on the
  remaining density. Strokes apply oldest to newest. Reusing an ID edits
  that stroke in place. `removePaint(id)` deletes it.
- `pinLandmark(regionId, landmarkId, point)` and
  `pinRoute(regionId, routeId, points)` override generated positions with world
  XYZ. `unpinLandmark` and `unpinRoute` restore generation. `view.layout`
  gives the realized positions and paths. Clearance around each is 3D.
- `view.sample(x,y,z,time)` returns the current weights, medium, and
  conditions. `view.appearanceAt(x,y,z,{surfaceY,time})` returns the height
  offset, chosen stratum and ramp, traversal tags, and weighted ambient cues.
  `view.inspect(x,y,z,{surfaceY,time,species})` adds procedural region weights,
  individual habitat checks, applied strokes, exclusions, and nearby
  reservations. Set `species` to explain a rule even when its recipe has zero
  weight at the point. A failed check has weight zero and a missing
  measurement has value `null`.
- `view.populate(bounds,{height,layer,time,...placementOptions})` returns
  seeded instances using the stable population grid. The height callback
  returns world Y or `null` for no surface. Use distinct layer names for the
  surface, sea bed, and cave floor. Use the same world-space height sampler,
  time, and placement options across chunks, including any neighbor halo.
  Instance IDs combine layer and stable candidate key. Each sample supplies
  its world position, species, asset, and recipe.
  Pass the same optional `habitatOffset` to `populate` and `inspect` to
  sample conditions and paint a fixed distance above or below the placement
  point. A positive offset lets a sea-bed plant anchor at the bed and test
  the water around its leaves. Output bounds and reservation checks still
  use the anchor. Inspection reports the height it sampled as `sampleY`.

Group edits with `document.transact(label, callback)` to share one undo step.
`document.serialize()` saves intent. Pass the saved data as `snapshot` to
`create` and supply the same external `media`, `solid`, and `conditions`.
These runtime sources can come from a published water snapshot.

The [headless example](../examples/biome-recipes.js) defines an alpine ridge,
a tidal marsh, a clear kelp bed, and a flooded cave beneath the kelp.

```js
const { KIT } = require('.').load();
const world = require('./examples/biome-recipes')(KIT);
const view = world.view();
view.inspect(-3, 0.5, 3);                        // marsh moisture and elevation checks
view.inspect(7, -2, 3, { species: 'kelp' });       // kelp blocked by low water clarity
view.inspect(7, -9, 3, { species: 'glow-moss' });  // cave pool at the same XZ
```

### Headless biome world realization

`P.biomeWorld.create({height, caves, cell, chunkCells, verticalCells,
terrainSlope, layers, project, emit, palette, materialRamps, dependencyHalo, maxSplats, surfaceScatter, shadeSurface})`
realizes a retained biome recipe view against caller-supplied terrain.
The [headless coast example](../examples/biome-world.js) walks from a ridge
through a marsh, dives through a flooded passage, and surfaces in an
underground air pocket. It uses one water snapshot for each tide revision.

```js
const { KIT } = require('.').load();
const coast = require('./examples/biome-world')(KIT);
const { compiler, author, indices } = coast;
const frame = compiler.prepare(author.view(), { water: coast.water(0.38) });
await compiler.update(frame, indices);
const world = compiler.makeWorld(frame, compiler.chunks());
const trip = frame.traceRoute(coast.itinerary(frame));
```

- The carrier `height(x,z)` plus the recipe's blended height offset gives
  the terrain. Each cave supplies `{bounds, sdf(x,y,z)}` with negative values
  inside the carve and conservative bounds. The frame's `heightAt`,
  `distance` and `supports` use the same solid field as the chunk bake.
  `terrainSlope` bounds the realized terrain grade for conservative
  distance queries. For a valid distance field, `traceRoute` reserves half
  a sample stride past the requested sphere radius and reports medium changes
  or the first sample that fails clearance. Use `frame.traversal(body)`
  for the shared ground walker.
- A chunk index is `[x,z]` on the world lattice. Each chunk spans
  `chunkCells` by `chunkCells` horizontally and the fixed, inclusive
  endpoints in `verticalCells` vertically. `build(frame,index)` can run
  independently. `chunk.field.sample(x,y,z)` interpolates the signed
  lattice from the bake and returns `null` outside the chunk.
  `chunk.field.values()` copies the lattice in X-fastest order.
  Use the frame's continuous field for precise traversal. Chunk splats
  use stable IDs keyed by world cell or placement. Chunks also expose
  placements, clipped route segments, and bake work counts.
  Optional `surfaceScatter` takes a fraction of a cell in [0, 0.35].
  It spreads splat centers in the tangent plane, projects them onto the
  continuous solid field, and compensates for coverage with wider splats.
  The world seed and lattice coordinates determine the offsets.
  `shadeSurface(rgb, {point, normal, frame})` can return a new RGB triplet
  in [0, 255] before the splat is packed. Use
  `P.biomeWorld.pointLighting({ambient, lights})` as a shader callback for
  finite-radius lights. Each light has `point`, `radius`, and optional
  normalized `color`, `strength` and `wrap`. A custom callback can read
  the same medium and biome snapshot as the population rules.
- Each population layer supplies `{id, height?, habitatOffset?, options?}`.
  Its optional height sampler receives `(x,z,frame)` and selects a support
  or returns `null`. The default uses the remaining surface of the carrier
  after carving. Unpinned landmarks and route points project to the nearest
  support by height. Supply `project(point,feature,geometry)` for explicit
  swim waypoints or other placement policies. XYZ pins retain their positions.
  Use `emit(builder,placement,frame)` to bake the actual asset's splats.
  The default emits one placeholder splat per placement.
- Use `prepare` with the same water snapshot that the renderer should show.
  The frame takes its recipe media and air pockets from that snapshot.
  `geometryFrom` can supply a prepared dry frame with the same recipe view,
  bricks and time, so geometry stays identical when water is attached.
  Optional `bricks` supply sparse edits to the solid field and material
  overrides with an entry in `materialRamps`. Each override is an array of
  packed RGB colors. `frame.bakeSpans(options)` and
  `frame.bakeSpanTiles(options)` sample the same solid field.
  `frame.traversalGraph(options)` uses it for clearance checks.
  `update` accepts the full desired index set and publishes a patch of
  replaced chunks and removed keys. It compares retained recipe edits,
  old and new route spans, water changes, and changed bricks, then checks the dependency
  halo of each chunk. Unchanged chunks retain their payloads. Updates
  serialize and publish only complete builds. Use `dependencyHalo` when
  a custom layer sampler, feature projection, or emitter reads beyond the
  default spacing and surface sampling halos. Keep these callbacks
  deterministic over their captured inputs.
- `makeWorld(frame,chunks,meta)` assembles an ordered packed splat world
  from independently built chunks or the currently published chunk set.
  It accepts normal render metadata such as `cam`. Assemble on chunk
  changes and reuse the packed world across render frames. Water optics
  use the [WebGL renderer](browser-renderer.md#water-optics).

### Surface state through remeshing

Store paint and scalar surface values in rest chart coordinates with
`P.surfaceState.prepare(stamps, {size, definitions})`. Supply the rest
chart width and height in `size`, then call `sample([u, v])`. The
[headless surface state guide](headless-worlds.md#surface-state-that-follows-geometry)
documents the stamp schema and the default channels. Use
`P.surfaceState.channels(extra)` for additional scalar and color channels.

Keep a `{chart, uv}` reference on each source corner as its position
deforms. When a remesher supplies a source triangle and barycentric
weights for a new sample, interpolate its reference with
`P.surfaceState.correspondence(corners, weights)`. It returns a chart
address when all three corners share a chart. Keep chart seams split and
give new interior faces their own charts with the default state.

### Sparse bricks

`P.sparseBricks.create({cell, brickSize, base})` makes an empty snapshot around
a stable negative-inside `base(x,y,z)` field. Bricks live on a signed integer
XYZ lattice. Only edited bricks are stored. Each channel can collapse to a
constant throughout a brick. `setBrick([i,j,k], {offset, material, medium})`
sets uniform values and leaves omitted channels alone.

`edit({bounds, sdf, operation, smooth, material, medium, maxSamples})` returns
a new snapshot. `union` and `subtract` combine the current field with the
signed brush and store the offset from the base at each edited lattice point.
Pad `bounds` enough to contain the sculpt's full influence. `smooth` controls
the blend distance. The default operation `paint` changes the material and
medium IDs inside the brush or throughout the bounds when no brush is given.
Pass `null` for a channel to clear its paint. Older snapshots share untouched
brick data and remain readable.

- `distance(x,y,z)` adds interpolated offsets to the analytical base,
  reading neighboring bricks at seams.
- `attributes(x,y,z)` returns the nearest sample's material and medium IDs.
  `mediumField(id)` converts a painted label to a signed membership field
  for a vertical span bake. A new water scene can then publish the result to
  gameplay and WebGL together.
- `changesFrom(previous)` returns bounds with the interpolation halo.
  `stats` counts retained, uniform, dense and sculpted bricks.
- For a biome world edit, create the brush snapshot with an unedited frame's
  `distance` as its base, then call `prepare(view, {bricks, water})`. The
  compiler samples its continuous field, applies the brick offsets and emits
  Gaussian splats at the resulting zero crossings.

### Traversal graph

Pass aligned, nonoverlapping XZ span tiles to
`P.traversalGraph.create({tiles, radius, height, stepUp, maxDrop, maxClimb,
canClimb, swimStep, clearance, origin, maxNodes, maxChecks, previous, dirtyBounds})`. The graph
samples capsule-sized standing and swimming positions and checks paths across
neighboring columns and tile seams. A supplied `clearance(x,y,z)` SDF checks
the capsule axis with its radius. Without it the graph uses the occupied
spans and an enclosing box. `canClimb(from,to)` authorizes climbs upward when
the height change exceeds a step. Drops are directed. Use a common XZ
`origin` for stable column IDs in streamed regions.

Pass the previous graph to retain nodes and links for unchanged tiles.
Changed span grids and added or removed neighbors refresh the affected
boundary links. If the clearance field is a new revision, supply
`dirtyBounds` covering all of its changes. The graph expands these bounds
by the capsule radius and link reach in XZ. A new clearance function without
dirty bounds rebuilds the graph. `graph.work` counts clearance and graph
checks and lists rebuilt node tiles and relinked tiles.

`graph.route(start,end,{allow, maxSnap, weights})` accepts node IDs or XYZ
agent centers and returns the ordered nodes, movement edges, waypoint
positions and cost. `allow` limits the route to selected modes and `weights`
sets positive per-mode cost multipliers. `next.changesFrom(previous)` reports
changed edges with old and new modes and their endpoint media, including when
a rising tide changed a walk into a swim.

```js
const { frame, tiles } = coast.layered(0.38);
const graph = frame.traversalGraph({ tiles, radius: 0.14, height: 0.48 });
const ridge = graph.nodes.find(node => node.supported && node.medium === 'air');
const chamber = graph.nodes.find(node => node.mediumId === 'chamber-air');
const route = graph.route(ridge.id, chamber.id);
```

### Biome revisions

Use `P.biomeRevisions.create({compiler, tiles, indices, sources, optics, span,
flood, agent, meta, brushGrid, historyLimit, derive})` as the entry point for
an editable biome world. It stages the continuous terrain, span bake,
connected water, traversal graph, splat chunks and packed render world.
`current()` advances when every stage succeeds.

```js
const world = K.procedural.biomeRevisions.create({
  compiler, tiles, indices,
  sources: [{ id: 'spring', point: [1.25, -2, 0.25], level: -1.5 }],
  optics: mediumId => waterStyles[mediumId],
  agent: { radius: 0.14, height: 0.5, origin: [0, 0] },
  brushGrid: { cell: 0.25, brickSize: 4 }
});
const first = await world.commit({ view: author.view() });
const after = await world.sculpt({
  operation: 'subtract', bounds: passageBounds, sdf: passageShape
});
const medium = after.frame.view.mediumAt(...feet);
const route = after.graph.route(start, end);
renderer.render(after.world, cameraOptions);
await world.undo();
```

- `commit(patch)` accepts changes to `view`, `bricks`, `time`, `tiles`,
  `indices`, `sources`, `optics`, or JSON render `meta`. Fields omitted from
  a patch carry forward. A function receives the last published revision
  and returns the patch. Commits, brushes, and history operations run in order.
- `sculpt(brush)` applies a sparse brush to the current revision, creating
  a brick grid from the current solid field if needed. Supply an existing
  snapshot with `commit({bricks})` to replace the sculpt layer.
- `undo()` and `redo()` restore the published snapshots directly. A successful
  commit after undo starts a new branch and clears redo. `historyLimit`
  defaults to 16. Past packed buffers may be shared, so handle them as
  read-only render inputs.
- `span`, `flood`, and `agent` pass author controls to their respective
  stages. Set `agent: false` for a world without navigation. The render world
  carries water and the traversal graph for `K.world.query.fromScene`.
- A creator may supply `derive(staged, previous)` for additional build
  products. Its return value appears as `revision.extra`. A thrown error
  or rejected promise leaves publication and history unchanged. Keep
  callbacks deterministic over captured inputs. Per-commit `clock` returns
  a stage profile in `revision.timings`.
- The lower-level compiler offers `realize(frame, indices, {previous})` to
  stage an independent branch of chunk data. Colliders and sampled surfaces
  are reused when the edit only changes water in that chunk. Use `update`
  for the compiler-only publishing API.

A committed revision includes `dependencies`, which records the fields
and regions that changed, causes linking derived changes to their inputs,
and the actual span, flood, water, traversal, and splat work. Run the
[headless dependency report](headless-worlds.md#spatial-dependency-reports)
to inspect a local edit from the command line.

### Connected flooding

`P.spanFlood.create({tiles, sources, previous, origin, opening, maxChecks})`
fills aligned **dry** solid/air span grids from explicit sources. Each source
supplies an `id`, an XYZ `point` below its `level`, and optional XYZ
`current`. Water passes between adjacent columns where their free intervals
overlap below that level by at least `opening` (default 0.02 world units).
An unreachable or above-head sill blocks the fill. If reservoirs connect,
the higher head wins, with source ID breaking ties. This is a fixed-head
occupancy solver. Flow rates, pressure and time evolution belong to the host.

The result retains unchanged geometry topology and keeps unchanged filled
grids by identity. Source reachability is evaluated through the connected
wet intervals each revision. `work` reports topology rebuilds, wet relabels,
and visited intervals. Use the resulting tiles for both the traversal graph
and `waterBodies.sceneFromSpans` so gameplay and WebGL publish the same water.

The [headless flood valley](../examples/biome-flood.js) has a surface lake
above a separate underground reservoir. One sparse brush opens a passage at a
chunk boundary. The lower route floods, and a dry route over the sill remains
walkable between the same endpoints.

```js
const { KIT } = require('.').load();
const valley = require('./examples/biome-flood')(KIT);
const before = await valley.build();
const after = await valley.cut();
const flooded = after.graph.changesFrom(before.graph).filter(change => change.reason === 'flooded');
```

Run `node scripts/benchmark-biome-flood.js` from the checkout. It reports
CPU time and work counts for rebuilding the same post-cut world with local
updates and from scratch. It alternates order after a warmup pair, checks the
two outcomes for equality, and reports median and p95 times. Setup,
brush authoring and WebGL drawing are outside the timed rebuilds. The local lane also
reports the single brush stroke from entry through publication.
`--runs=N` changes the sample count, `--styled` enables the authored cave
look, and `--json` emits raw timing samples.

### Stable spacing and finite Poisson sampling

Opt in to minimum-distance placement with
`P.populations.layout(regions, evaluate, {exclusion: {distance}})`.
The higher-priority eligible candidate blocks lower-priority candidates within
the exclusion distance. Candidate identity and the decision are based on world
coordinates and a bounded neighbor halo. Use the same seed, settings, and
world-space evaluator in every chunk. The evaluator also sees candidates just
outside the output regions so splitting a region produces the same placements.
The optional fourth argument to `layout(regions, evaluate, options, include)`
filters emitted samples with `include(sample)` before counting them against
the instance budget. Eligible neighbors still participate in spacing.

Set `exclusion.maxDistance` to bound variable `minDistance` values returned
by the evaluator or values in `exclusion.species`. An evaluator may return
a `species` name. Supply a nested table such as `{oak: {moss: 0.6}}` to add a
symmetric pair separation. A pair uses the maximum of its two sample distances
and any matching species rules. Candidate and comparison budgets include work
in the halo.

`P.populations.mix([{key, weight}, ...], {seed, patchSize, coherence})` returns
a sampler that takes an XZ point and an integer individual seed and returns
a choice key. Weights are relative. Zero disables a choice. Keyed sampling
preserves the ordering of the remaining choices if one choice is removed.
Use the same inputs for overlapping regions. With coherence above zero,
that fraction of individuals draws from the shared choice in its nearest
jittered patch centre. Patch size is in world units.

Use `P.sampling.poisson({bounds: {min, max}, radius, seed})` for a finite
patch. Bounds and points have two or three coordinates. `mask(point)` can
restrict the domain. `seeds` pins starting samples. `reseed` allows a bounded
number of extra random seeds in disconnected regions after a patch finishes.
For variable spacing, supply `radius(point)`, `minRadius`, and `maxRadius`.
Pair separation is the larger radius. With `axisScale`, distance is measured
after dividing each coordinate difference by that axis scale. The result
contains each `point` and `radius`, plus a work report and status.
A `budget` or `point-limit` result contains the samples inserted so far.

The splat example compares two independently populated chunks with one finite
Bridson patch at the same exclusion distance.

```sh
node cli/ink-studio.js render examples/poisson-patches.js --seed 0 --ortho --colored
node cli/ink-studio.js render examples/poisson-patches.js --seed 1 --ortho --colored
```

### Progressive samples and surface detail

- `P.sampling.eliminate(points, {count, progressive, weights})` removes
  points with the highest local crowding until an exact count remains.
  Higher preference weights favor retention. `progressive` thins again
  at larger spacing scales and puts the coarse subsets first. Use the
  reported `levels` as prefix lengths.
- `P.sampling.lloyd(points, {bounds, spacing, iterations, density, mask,
  fixed})` uses sampled planar Voronoi centroids. Bounds are two-dimensional.
  `fixed` holds point indices in place. Smaller `spacing` improves the
  centroid approximation. A mask can constrain movement to the legal domain.
- `P.geometry.samplePatch` can jitter samples within its adaptive UV strata
  with `jitter` and `seed`. Positive `curvature` spends more samples where
  the carrier bends. `P.sampling.patch(spec)` returns the same sample points
  and UVs, with jitter enabled by default.
- `P.sampling.geodesicSpacing(points, links, {distance, candidates})`
  selects in candidate priority order using shortest paths along surface links.
  A link is `[a, b]` or `[a, b, worldLength]`; points on different surfaces
  remain independent even where they lie close in XYZ space.
- `P.sampling.triangles(positions, {count, seed})` adapts the sampling
  vocabulary to an imported triangle stream. It stratifies by area and
  returns world points with triangle indices and barycentric coordinates.
- `P.sampling.centeredGridRange([min, max], count, [lo, hi])` finds the
  half-open index range for cell centers within an inclusive region. The
  center at index `i` stays at `min + (max - min) * ((i + .5) / count)`.
  Apply it independently to each axis to regenerate a patch of an
  existing lattice while preserving its spacing and phase.

`examples/sampling-detail.js` uses seed 0 for centered strata, seed 1 for
curvature-weighted jittered splats, and seed 2 for a ranked point set whose
coarser prefixes are shown with larger dabs.

### Environment fields

`P.environmentFields.evaluate(settings, elapsed)` resolves a cyclic solar
clock. Configure local `hour`, advance in hours per second with `rate`, and
set `latitude`, `declination`, and scene orientation (`north`) in degrees.
Read a unit `sun` direction, daylight and twilight weights, ambient gain,
RGB tint, and retained wind and surface parameters. A zero rate holds time.

`opticalDepth(from, to, medium)` integrates a fog ray over a density field
that mixes a constant medium and a ground-clinging exponential. Set
`density`, `floor`, `height` and `cling` in world coordinates and convert
optical depth to transmittance with `exp(-depth)`. `scatter(from, to, light,
medium)` estimates a local light's contribution along the visible segment
up to its endpoint. A light supplies `p`, `radius`, and `intensity`.

`deposition({normal, load, exposure, shelter, texture, slope})` computes a
surface load from the upward normal, incoming supply, exposure and shelter.
Callers provide the coverage mask and material treatment. Snow, ash and
windblown dust can all use the same query.

`environmentFields.coating.profile(spec)` prepares a color treatment for
a temporary surface coat. Configure `slope` and `bias` for how readily it
settles on inclines, `variation` for texture response, `retention` by
material role, and `shadow`, `highlight`, and `blend` for the resulting
appearance. Each role may use its own normalized retention. Unlisted
roles use `other`. Bias peaks at a midrange slope and leaves flat
and vertical surfaces unchanged.

Pass `{normal, load, texture, exposure, material}` to `coating.amount(sample,
profile)`, then shade a normalized substrate color with `coating.color(rgb,
amount, profile)`. `coating.glsl` supplies the same amount and color
curves. For GPU use, supply the upward component of the normalized normal,
multiply load by the scene's exposure mask, and pass the substrate's
retention. A different palette and retention map lets the same curves
represent ash, frost or a dusting of sand.

Set `depth` to a maximum thickness in scene units. It defaults to zero.
`coating.thickness(amount, profile)` uses the same blend ramp as the color.
`coating.shape({point, normal, covariance, amount}, profile)` extends a
Gaussian splat along its surface normal and returns its adjusted point,
row-major 3×3 covariance and depth. The lower three-sigma boundary stays
at the substrate. `coating.glsl.shape` implements the same transform on the GPU.

### Overhead cover

`P.overheadCover.rasterize({meshes, surfaces}, options)` projects opaque
geometry from above. Each mesh supplies a flat `positions` buffer with
nine world coordinates per triangle, or XYZ vertices and a flat
`triangles` index buffer. Each analytic surface supplies
two-element XZ bounds `min` and `max` and a `heightAt(x, z)` function that
returns the upper height or `null` outside its footprint. The highest
intersection at each XZ cell center becomes a texel in a single-channel
Float32 height field. Use `spacing` to set the cell size and
`maxSize` to bound the longest axis in texels. The field also carries
`origin` (minimum X and Z), `step`, `width`, `height` and `samples`.

`P.overheadCover.exposure(field, point, normal)` gives the exposed fraction
for a surface. The optional normal estimates the surface height at neighboring
texels to avoid shading a sloped surface with its own heights. `clearance`
keeps an exposed surface clear of its rasterized height and `softness`
sets the vertical transition from exposed to covered. Empty geometry
returns a null field with full exposure. A caller can pass this exposure
to coating, deposition, or other surface effects without regenerating the
field when their intensity changes. For WebGL 2, upload the samples as
`R32F` and use the matching `overheadExposure` GLSL function with
`vec3(origin, step)` and `vec2(clearance, softness)`.

### Attachment slots

`P.attachments.layout(slots, families, {seed, fits, sizeFor, budget})` selects a family
for each named slot. A slot supplies a stable `id`, a `point`, independent
`normal` and `tangent` axes, and a three-component `room` in the caller's
semantic size order. Optional `tags`, `chance`, `priority`, `variant`, and
`pin` select compatibility, occupancy, order, seed offset and an explicit
family, respectively. Families declare `id`, `size`, optional positive
`weight` and required tags in `requires`. Slots and families can carry JSON
`data` such as chart anchors or asset recipe keys.

For compatible choices, seeded weighted ranking provides deterministic
fallbacks. Use `sizeFor(family, slot)` to supply three finite, positive
dimensions for the room check when a slot applies a size override or its
frame changes the projected footprint. The family and seed in the result
retain their original meaning. `fits(proposal, accepted)` can test scene clearance or reserve
nearby space. `budget` bounds slot-family comparisons. Output entries contain
`key`, the normalized `slot` frame, a `family`, and a local `seed`.
For a retained scene, use that key in `doc.derive()` and let document
overrides, promotion, and suppression carry authored edits.

### Surface growth

`P.surfaceGrowth.trace({roots, project, connect, step, steps, branchEvery,
tips, budget, bias, attraction, spread, seed})` builds a graph of rooted walks.
Each root has a unique string `key`, an XYZ `point`, and an optional starting
`direction`. The `project(point, previous, step, root)` callback returns
an accepted XYZ `point` and `normal`, or `null`. The previous frame is null
at a root. Optional JSON frame metadata, such as a chart or host ID, is
copied into the output. Root and branch keys depend on authored identity and traversal
order, so an unchanged path keeps its keys when surface IDs change.

The optional `connect(from, to, step)` callback can reject a segment with
`null` or accept it with up to eight intermediate surface frames. Use it
to reject crossings through holes or to insert transition points along a
seam. Output contains `nodes`, `edges` with ordered `frames`, and terminal
`ends`. `tips` bounds the active paths per root, and `budget` caps total
nodes. Callers provide the surface, branching parameters, and rendering
or manufacturing rules for the resulting edges.

For growth over assembled solids, cast a short ray along the chart normal
to seat each frame on the exposed solid. A convex union's
`projectedIntervals(a, b, direction, {outward, inward})` reports material
support along the whole segment. Both reaches are nonnegative world
distances. The returned intervals use segment coordinates from 0 to 1.
A link callback can apply its own allowable gap when deciding whether to
continue across a joint.

`P.surfaceGrowth.transport(heading, fromNormal, toNormal)` carries a tangent
through the shortest turn between two unit normals. A projection callback can
use it to continue a walk onto an adjacent chart.

`P.spatial.probeFootprint({cell, budget})` records the regional reads of a
projection, growth trace, or other sampled result. Call `record(point, radius)`
for each point or neighborhood the result queried, including unsuccessful
queries. `seal()` produces an immutable snapshot with `intersects(bounds)`.
The recorder merges nearby reads and keeps an overflow box when it reaches
the budget. A clear result certifies that the given bounds missed every
recorded read. Include both the old and new bounds of changed geometry when
deciding whether to reuse results.

`P.landingContact.create({sill, facing, width, near, far, fraction,
verticalTolerance, elevationSpread})` samples an approach at two depths
and three positions across its width. Pass `match()` candidates with a
stable `id` and `height(x,z)` sampler. A missing sample, an elevation
outside the requested sill range, or too much variation across the
approach disqualifies the candidate. The closest fit returns its ID,
highest supported elevation, and sampled range. Equal fits use ID order.
Use the exposed `bounds` to query nearby surfaces before sampling. The
same query can fit a ramp transition, a platform threshold, or an
equipment loading area according to the caller's tolerances.

Use `matchPatches()` for level floors with known outlines. Pass records
with an `id`, a constant `height`, a convex XZ `footprint` and optional
convex `holes` in that footprint. The query clips the approach against
the union of the patches in each eligible height band. Abutting patches
can support a single approach, and gaps between probe points still
reject the fit. The result gives the highest elevation and elevation
range of the overlapping patches, plus sorted `ids` when the band uses
multiple carriers. An equal-distance tie prefers the lower elevation.

`P.viewClearance.compile({eye, target, radius, feather, endFade, opacity,
reach})` creates a camera-relative opacity field. Apply `opacityAt(point)`
to the geometry you want to yield when it blocks the view. The effect
feathers around the viewing axis and releases as it approaches the focus.
`reach` optionally sets a fixed depth for views that use a direction in place
of a physical focus point. The included GLSL function takes the same axis
and profile and works on transformed sample positions.

### Contact fields, runoff, and contours

`P.contours.march(field, {bounds, cell, iso})` extracts open paths and closed
loops from a bounded 2D scalar field. The default level is zero. Use it for
shorelines, isolines, or curves in a carrier chart. The callback receives two
coordinates and returns a finite scalar or `null` where the domain ends.

`P.contacts.traceSdf(chart, sd, options)` runs the contour calculation on
`sd(...chart.sample([u, v]).p)`, then lifts the paths onto the chart in world
space. The default chart bounds are `[0, 1] × [0, 1]`. Typical carriers are
`P.surface.plane()` and `P.surface.cylinder()`. Use finer `cell` values for
smaller intersections. The result can also be built from authored world-space
polylines or the existing triangle-contact API.

- Pass an `occluder(x, y, z)` to `traceSdf`, or call
  `P.contacts.expose(curves, occluder, {step, clearance})` directly, to trim
  hidden segments against a signed field. Resolution is controlled by `step`.
- `P.contacts.field(curves)` indexes curve segments. Query `nearest(point)`
  for distance, closest point, tangent, source ID, and position along the
  curve. Use `distance(x, y, z)` for an unsigned field or `sdf(radius)` for
  a tubular signed distance function.
- Use `field.mask({inner, outer, weight})` to produce a feathered coverage
  callback. The optional `weight(hit, point)` can limit paint to one side
  of a seam or fade it along the curve. Use it in a material's `tex` or
  `mod`, a surface layer's `mask`, decal placement, or a relief operation.
- `P.contacts.runoff(curves, project, {spacing, step, distance})` starts
  evenly spaced downhill traces on a carrier. The projection callback
  receives a point and returns `{p, n}` for the projected point and normal,
  or `null` outside its domain. Feed the trails into the same distance field
  to make streaks. Change `direction` to trace another environmental flow.

The SDF example compares the same sandstone wall with and without contact
stains and seam-driven moss.

```sh
node cli/ink-studio.js render examples/contact-masks.js --seed 0 --ortho --colored
node cli/ink-studio.js render examples/contact-masks.js --seed 1 --ortho --colored
```

### Socket tiling and learned swatches

Compile tile IDs, positive weights, and directional sockets with
`P.tiles.compile(definitions)`. Set sockets using `north`, `east`, `south`,
and `west` keys. Omitted sockets are `null`. Opposite sides must match.
A JavaScript `matches(a, b, direction)` option can define other compatibility.

`P.tiles.solve(model, {width, height, seed, pins, ports})` uses weighted
minimum-entropy selection, arc consistency and bounded backtracking.
Coordinates are integer `x` and `z`. A pin names a `tile` or an allowed
`tiles` list. A port supplies `{x, z, direction, socket}`. Use ports to
carry the edges of an authored connectivity graph into the tiling.
Optional `boundary` sockets apply at outer edges and next to masked cells.
`wrap` is a boolean or separate X and Z booleans.

An `ok` result contains row-major tile IDs and an `at(x, z)` query. Empty
cells contain `null`. An inconsistent set of constraints reports
`contradiction`, with a conflict cell when known. Limits on `maxWork` or
`maxBacktracks` report `budget`.

- `tiles.learn(swatch, {size, periodic, symmetry})` learns overlapping
  square patterns from rows of scalar values. `tiles.overlap(bank, options)`
  synthesizes a new swatch. Its pins are `{x, z, value}` in the output.
- `tiles.wang(model, {width, height, labels, origin, seed})` hashes edges
  using integer world coordinates so independent regions agree on shared
  seams. Supply variants for every signature used by the label alphabet.
  Incomplete sets return `missing` with the required signature.
- `tiles.refine(coarse, model, {size, template})` expands each coarse cell
  into a square block, then solves all fine cells together. Templates supply
  fine tile IDs or allowed lists, or `null` for free cells. The coarse mask
  carries through to the fine result.

Use the chosen IDs to emit signed solids or splats, or interpret swatch
values as material masks. The example bakes an authored three-way path with
weighted socket tiles, and a ceramic panel generated from a small swatch.

```sh
node cli/ink-studio.js render examples/constraint-tiles.js --seed 0 --ortho --colored
node cli/ink-studio.js render examples/constraint-tiles.js --seed 1 --ortho --colored
```

### Composable procedural fields

`P.fields.compile(expression, {seed})` returns a function
`field(x, y, z, time = 0)`. Pass the function to a terrain sampler, scalars
in a material, or a population evaluator. The compiled `spec` and `seed`
can be saved and recompiled as JSON. Use `field.sample(x, y, z, time)` for a
value, XYZ gradient, and time derivative. Analytic derivatives are
propagated through the expression. Clamps, folds, and nearest-feature ties
use one selected derivative at corners.

| Node | Controls |
| --- | --- |
| Number or `constant` | A scalar number or `{type: 'constant', value}` |
| `axis` | Read `x`, `y`, `z`, or `time` with optional scalar `scale` |
| `simplex` | Seeded noise. `axes` selects two or three spatial coordinates. `scale` is a world length or XYZ lengths |
| `periodic` | Gradient noise with XYZ world `period` lengths. Use `null` on axes that should have no explicit period. Scale selects the approximate lattice size |
| `loop` | Two spatial coordinates, selected by `axes`, and a circle in a four-dimensional noise field. Set the time `period` and circle `radius` |
| `fbm`, `ridge`, `billow` | `source`, `octaves`, `gain`, and `lacunarity`. Ridge also has `offset` and `feedback` |
| `warp` | `source`, `strength`, `iterations`, and `decay`. Supply three component fields in `vector` or use seeded default components at `scale` |
| `terrace` | `source`, height `step`, `offset`, and transition width as a fraction of a step |
| `distance` | XYZ `point` or XYZ polylines in `paths`, with optional signed `radius`. Set `axes: 'xz'` for plan distance |
| `add`, `multiply`, `min`, `max` | Compose two or more `inputs` |
| `clamp` | Limit `source` to `min` and `max` |

The raw `fields.simplex({dimension, seed})` and
`fields.periodic({dimension, seed, periods})` APIs expose `value`,
`gradient`, and `sample` in two to four dimensions. Raw periodic lattice
periods are integer cell counts. Noise has nominal unit amplitude, and
`clamp` can constrain the final range.

The sculpt node `S.displace(heldSolid, expression, amplitude, options)`
compiles a JSON expression once and clamps its samples to the node's
zero-to-one input range. The original callback signature still accepts a
numeric field. The example applies the same field vocabulary to terrain
heights, shading, and displaced solids.

```sh
node cli/ink-studio.js render examples/composed-fields.js --seed 0 --ortho --colored
node cli/ink-studio.js render examples/composed-fields.js --seed 1 --ortho --colored
```

### Shape grammar and pinned bays

`P.grammar.expand({id, symbol, bounds}, rules, options)` lays out named,
axis-aligned scopes in local XYZ units. A production can reference another
rule by its name. Use `null` to reserve an empty scope. The result contains
parts and sockets with stable keys and a work count.

- `split` divides a scope on an `axis`. Give each `parts` entry a `key`
  and a production in `use`. A fixed `size` reserves world units.
  `weight` shares the remaining space among flexible parts.
- `repeat` fits cells at a nominal `pitch` on an `axis`. Supply `use`
  for each bay and optional `gap` between bays. Pass inline `pins` or
  use a `pinSet` name with `options.pinSets`. Each pin has a stable
  `id`, absolute `at` coordinate and `span`. It can specify its own
  `use` or use the operation's `pinUse` production.
- `inset` moves the faces inwards by `margin`, or different XYZ `min` and
  `max` margins. An `optional` inset may omit a scope too small to fit.
- `group` evaluates named `children` in the same scope. A `choice`
  picks one named production from positive weighted `options` using
  the seed and scope lineage.
- `emit` returns the scope's `bounds`, `center` and `half` dimensions
  with a material or geometry `role`. Emitters are supplied by the caller.
  A `socket` returns a `name`, point, and normal on the selected `axis`
  and `side`. The other two positions come from normalized XYZ `at`.
  Both can carry JSON `data`.

Around a pin, bay keys count out from the pinned end of the span. When
resizing adds bays towards an outer edge, the nearby keys stay stable.
Call `grammar.children(layout)` and pass those child specs to
`doc.derive(owner, rule, children)` so the existing authoring document
preserves hand edits. Emit geometry with standard SDF nodes such as
`S.box(part.center, part.half, material)`.

The sample changes the width of a façade around a pinned entrance.
The edited blue window, neighboring trim and socket attachments are
realized from the retained document and baked to splats.

```sh
node cli/ink-studio.js render examples/pinned-facade.js --seed 0 --ortho --colored
node cli/ink-studio.js render examples/pinned-facade.js --seed 1 --ortho --colored
```

### Grid and graph rewriting

`grammar.rewriteGrid(rows, rules, {steps, seed, pinned, wrap})` selects
a weighted match on each step and applies it to the current grid. A rule
has an `id`, optional `weight`, and same-sized `find` and `replace` patterns.
Use `*` to match any cell and `=` to keep a cell. Pins use integer XZ
indices. The result includes the current grid and rule history.

`grammar.rewriteGraph(graph, rules, options)` uses the same weighted
selection on directed graphs. The source has `nodes: [{id, type, data}]`
and `edges: [{from, to, type, data}]`. Each rule has `find` and
`replace` graphs whose nodes use local `key` names. Existing keys preserve
identity, omitted matched nodes disappear, and new keys create nodes.
Edges matched by the rule are replaced. Outside edges of retained nodes
remain attached. Both APIs expose work budgets.

### Rooms, caves and packing

- `layouts.bsp({width, height, minRoom, margin, corridorWidth, seed})`
  partitions the grid recursively, fits a room inside each leaf, and
  joins sibling regions. It returns room bounds and corridor routes.
- `layouts.cave({width, height, seed, steps, open, solid, repair})`
  evolves a cellular grid. It removes small unpinned regions and can
  carve connections among the remaining components. Pin or mask cells
  to protect authored features. A protected barrier can leave the result
  `disconnected`.
- Both grid layouts return row-major `cells` with one for open space.
  The same cells can drive a voxel shape, a floor mask, or an SDF cut.
- `layouts.pack(items, {width, height, gap, pins, blocked})` fits
  footprints supplied as `{id, size: [width, depth], rotate}`. Pins
  specify an `id`, integer `at` and optional `rotated` flag.
- `layouts.floorPlan(rooms, options)` accepts the same room shapes.
  Pass `adjacencies: [{a, b, span}]` to request shared walls and minimum
  door openings. The result supplies room bounds and door positions.
  Infeasible programs and search-budget exhaustion are reported separately.

In `examples/rooms-and-caves.js`, seeded room and cave grids are passed
to the voxel sculpt node. A grid grammar marks floor accents in both layouts.

### Vegetation and colony patterns

`growth.lsystem(axiom, rules, {generations, seed, frame, environment})`
rewrites a string or a tape of tokens in parallel. Tokens are strings or
`{symbol, args}` objects. A production specifies `from`, `to`, and
optional `weight` and `when`. An argument such as `{arg: 0, scale: 0.7}`
uses the first input argument and shrinks it on each rewrite. Rules can
read the local turtle frame and any caller-defined environmental value.

`growth.turtle(tokens, frame)` returns branch runs and marked frames.
Use `F` to draw, `f` to travel, `!` to set radius, brackets to save
and restore state. The rotation commands turn about the three local axes.
It emits marks at `L` by default. Pass the result directly to
`K.grow.limbs(S, result, material, options)` for SDF tubes.

- `growth.venation(outline, {root, toward, seed, sourceSpacing})` grows
  a planar network through interior attractors. Its branch runs use XY
  with zero Z, so they can be mapped onto a leaf or other host.
- `growth.roots(starts, {moisture, obstacle, clearance, seed})` traces
  tapered roots with gravity, local moisture and optional branching. The
  obstacle field is positive outside. Accepted segments check the field
  at quarter steps, so choose a small step for thin obstacles.
- `growth.pipe(nodes, {tipRadius, exponent})` accepts parent indices
  in growth order, with `-1` for roots.
- `growth.aggregate({width, height, seeds, target, stick, mask, seed})`
  returns occupied cells and their parent links. It reports a partial
  pattern if it reaches the walker or work limit.
- `growth.grayScottGrid({width, height, steps, feed, kill, mask, wrap})`
  evolves two scalar buffers on a lattice. Use the same integration on
  arbitrary curved domains with `growth.grayScottSurface(points, links, options)`.
  Supply surface-local links as `[indexA, indexB, weight?]` to control
  where diffusion crosses. The returned `u` and `v` buffers can drive
  material masks, relief, or sample density.
- `growth.dispersal({model, radius, spread, drift, aspect, angle})`
  returns normalized weights on XZ offsets. `growth.succession` uses
  those kernels to model stylized turnover and competition among named
  populations. Each species can specify habitat, seed pressure, maturity,
  lifespan, and competitive strength. The result provides final occupancy
  and age along with counts from each completed year.

`examples/vegetation-growth.js` bakes branch runs, root paths, and leaf
veins. `examples/colony-patterns.js` uses aggregation and reaction–diffusion
to color native voxel tiles.

### Implicit forms

Each form returns a signed, negative-inside field `sd(x, y, z)` and
finite `bounds`. `S.implicitForm(form, material, options)` adds it to
the sculptor as a native solid and samples its zero crossings for the
splat bake. Use `cell` to resolve small openings or thin walls. The sampler
checks its work budget and needs enough resolution to detect the feature.

`measureSculptBounds(sculpt => { ... })` runs a finite recipe against
the regular sculpt API and returns XYZ `min` and `max` bounds. It takes
per-axis extents for boxes, ellipsoids, tubes and bounded lathes.
For a lathe with a radius function, pass `maxRadius` with a conservative
radius bound. Custom finite solids can use their existing enclosing sphere.
The result includes the positive geometry before subtraction and allows
for blends and surface bumps. It returns `null` for an empty recipe.
The measurement does not generate surface samples or change the recipe's
rendering resolution.

- `forms.superquadric({radii, exponents, pose})` controls the XZ and
  vertical exponents independently. Values below one give concave
  profiles, two gives an ellipsoid, and large exponents approach a box.
- `forms.loft(sections, {pose})` blends polygon distance fields along
  increasing Y. Each input has `y`, an XZ `profile`, and optional `center`,
  `scale`, and `roll`. Profiles can have different vertex counts.
- `forms.skeleton(nodes, {blend, pose})` sweeps linearly varying spheres
  between points supplied as `{point, radius, parent}`. Parents precede
  their children. Set `blend` for smoother junctions.
- `forms.periodic({bounds, type, period, phase, mode, thickness, host})`
  makes gyroid, Schwarz P, and diamond sheets or solid phases in a bounded
  volume. An optional signed host field clips the result.
- `forms.shell(host, {inner, outer, maxOuter})` selects a band on either
  side of the host's zero surface. Each thickness can be a scalar or a
  world-space callback. Callback outer thickness requires an explicit
  maximum for conservative bounds. Re-distance the host when a physical
  shell thickness is important and the input is only an implicit field.
- `grammar.symmetry(scope, rules, {mode, axis, count, origin, copies})`
  mirrors a grammar or repeats it radially. Custom copies can use their
  own symbol, seed, offset, turn, or scale. Parts carry oriented axes and
  handedness. Sockets carry transformed normals and stable keys.

`examples/sculptural-fields.js` combines an open pottery loft, a
gyroid inside a rounded carrier, and a mirrored medial ornament.

### Implicit fracture and crack paths

`fracture.power({host, seeds, stretch, rotation, gap, cell, bond})`
partitions a signed host into weighted, negative-inside fragments. A site
is `{id, point, weight}`, and raising its weight grows its power cell.
`stretch` stretches the local distance metric. `rotation` orients that
metric in world space. For a callback host supply finite `bounds`.

Each cell exposes an implicit `form` for the splat bake. `owner(x, y, z)`
identifies the un-gapped partition winner, and the cell fields include
the specified gap. A voxel pass estimates material volume and the area
of bonds between adjacent cells. Lower `cell` to resolve small fragments
in the graph. Each bond has an ID, endpoint IDs, contact area, and capacity.
Set `bond` to derive capacity from material or another field.

`fracture.separate(graph, {loads, previous})` accumulates nonnegative
loads against bond capacities and returns the remaining connected
components. Each map is indexed by the emitted bond IDs.

`fracture.crack({width, height, starts, stress, toughness, mask, seed})`
advances connected fronts with seeded branching. A start specifies
`{at, angle, energy}`. Stress is a scalar load or
`{load, direction: [dx, dz]}`. Toughness and the mask can keep cracks
away from authored zones. Use the returned chains for relief cuts and
material marks. Results follow the supplied fields as artistic rules.

`examples/fracture-studies.js` displays weighted slab fragments and
a stress-guided surface crack. Both are realized as SDFs for the splat bake.

### Socket assemblies, supports and damage

`grammar.assemble(route, modules, {start, end, pins, joins, seed})` fits
an ordered catalog between endpoints and optional pinned joins on an
arc-length carrier. Modules have `id`, nominal `length`, optional `min`
and `max` lengths, `in` and `out` socket names, and a positive `cost`.
`reversible` lets the solver swap the two ends. Matching socket names
connect by default. `joins` accepts additional directed compatible
pairs. Pins are `{id, at, socket}` or `{id, at, in, out}`, with `at`
normalized over the carrier length.

The solver fits exact span lengths within each module's tolerance and
returns keyed modules with geometry frames. Pinned intervals reserve
enough slots for the whole route. The result reports a contradiction or
a search budget separately. If a feasible plan was found before price
optimization uses the budget, the layout indicates this in its work data.

`construct.supportGraph([{id, links, grounded}, ...])` resolves which
parts connect to a bearing. A link points from a dependent part to a part
it can lean on. Mark direct bearings with `grounded: true`. Unresolved IDs
can remain in the links while a part is absent. A cycle with a path to a
bearing is supported, and an isolated cycle is floating. Results retain
input order with resolved `grounded` and `state` values. Each part and
contact is visited a bounded number of times. Callers choose how to find
contacts and how to present either state.

`contacts.verticalPrism(footprint, bottom, top, {origin, gradient})` constructs a closed
volume from a convex polygon in the XZ plane and two ordered Y heights.
Caps are level by default. An optional XZ `origin` gives the datum for
both heights and `gradient: [dx, dz]` applies the same slope to both caps
while keeping the sides upright.
It owns its frozen `footprint` and world `bounds`. Use `containsPlan(x, z)`
to restrict external samples to the footprint.
`contacts.volumeContact(a, b, tolerance = 0)` accepts these prisms and
`contacts.orientedBox` volumes in any combination. It tests their face
normals and the required edge cross axes. A tolerance gives the maximum
allowed separation along those axes. Use the boolean result to connect
parts in a support graph.

`contacts.volumeSet(volumes)` builds a reusable bounding-volume tree
over boxes and prisms. It owns the list of up to 16,384 volumes and
exposes `size` and `bounds`. An empty set has null bounds.
`contacts.volumeSetsContact(a, b, tolerance = 0)` tests only pairs whose
bounds can meet and applies the same contact rule as `volumeContact`.
Keep a set for a stationary compound shape and query it against new
sets as other shapes move.

`construct.loadPaths(sockets, spans, {ground, clear, maxSpan, maxDrop})`
places beams, supporting columns and braces. Sockets use `{id, point}`
with an optional `bearing` to indicate an existing support. Spans use
`{id, a, b, load}` with a distributed line load. Ground can return
`null` to leave a void. `clear(a, b, info)` lets an authored scene
reject a proposed member. The plan reports unsupported spans and the
load assigned to each bearing. Its rules are for visual plausibility.

`construct.damage(parts, {rules, supports, pins, exposure, seed, steps})`
rewrites named part states under seeded, ordered conditions. Rules have
`id`, `from`, `to` and optional role, chance, weight and condition.
Dependencies are `{child, by: [key, ...], required}`. A missing support
can collapse dependents in the same tick. Pinned states persist, with a
flag when their support is gone. The result includes state-change events
and retains part keys for authoring.

`examples/socket-walkway.js` fits deck modules between a pinned join,
places a braced timber load path, and applies damage rules to a railing.

### Footprints and weighted pitched roofs

`construct.profile([exterior, ...holes])` validates simple XZ rings and
compiles a negative-inside distance field. The outer ring and holes can
arrive in either winding. `construct.offset(profile, distance)` adds or
removes material by signed distance, with rounded outer offsets. It can
produce closed boundary paths at a caller-chosen contour spacing.
`construct.extrude(profile, {low, high})` creates a vertical implicit
form directly from either profile, including its holes.

`construct.weightedRoof(rings, {pitch, pitches})` advances polygon
edges inward at the rate set by their pitch. Set a default angle in
radians, or pass nested arrays with one angle per original edge. Edge
collapses, reflex splits, and courtyard joins produce pitched face
patches and ridge and valley arcs. `query(x, z)` samples the height and
source edge. The solver reports exhausted budgets or unresolved
degeneracies. `roof.solid({base, thickness})` makes a thin implicit
roof from a completed result.

`examples/weighted-roof.js` bakes an L-shaped roof with unequal pitches,
offset stonework, and a roof valley. Its alternate seed uses a uniform
pitch over the same footprint.

### Material mapping, ramps and distance ink

`materials.triplanar(sample, {origin, scale, sharpness})` blends
planar samples by the surface normal. A sampler takes `(u, v, info)`
and returns a scalar or RGB. It receives the signed projection axis
and a two-component footprint in chart units. Supply one sampler or
a separate sampler for each projected axis.

`materials.tangent(sample, {origin, scale, angle, coordinates})`
wraps a planar sample in the local tangent frame. Set different scales
along and across the grain. An optional coordinate callback can use an
existing sweep chart. Both mapping helpers return functions that take
`(x, y, z, frame)`.

`materials.threshold(field, {level, feather, samples, seed})` converts
a scalar field to coverage. It integrates samples over a pixel footprint
in the tangent plane when supplied with a material frame. Sample
positions stay in the material's rest coordinates.

`materials.ramp(colors, {steps, space, hue})` accepts normalized sRGB
triples or hex colors and optional explicit `{at, color}` stops. Use
OKLab (`lab`) or OKLCh (`lch`) interpolation. It provides normalized
`rgb`, packed `hex`, and a continuous `sample(t)` function.

`geometry.distanceTransform(mask, {size, spacing, signed, indices})`
finds exact center-to-center Euclidean distances in a 2D or 3D binary
grid. Store X as the fastest-moving axis. In signed mode occupied
centers measure a negative distance to the nearest vacant center.
Use the optional indices to retrieve the corresponding sample. Empty
feature sets have infinite distance. `materials.outline` uses the same
calculation to produce separate inset and outer ink coverage.

`examples/material-masks.js` uses wrapping glazes, a tangent-aligned
grain, and distance ink on a voxel stamp.

### Swatch synthesis and threshold ranks

Raster input is `{width, height, channels, data}` with row-major,
interleaved channels. Use one channel for palette indices or several
for colors and masks.

- `materials.quilt(swatch, {width, height, patch, overlap, candidates,
  tolerance, seed})` assembles matched swatches and cuts minimum-error
  seams through the overlaps. The result includes a covered-cell mask
  and each placed patch's source coordinates.
- `materials.patchMatch(source, target, {radius, iterations, weights, seed})`
  estimates which source patch matches each target center. It alternates
  propagation directions and uses a shrinking randomized search. It
  returns source indices and errors in target order.
- `materials.synthesize(source, target, {mask, radius, cycles, blend, seed})`
  fills cells marked one, holding the other cells fixed. It estimates an
  initial guide from known pixels where the budget permits and refines
  with overlapping patch votes. The default `blend: 'sample'` retains
  exemplar pixel values. Use `'average'` for a continuous-color fill.
- `materials.blueNoise({width, height, sigma, density, seed})` ranks a
  tile with void-and-cluster relaxation and progressive thresholding.
  `sample(x, y)` wraps in both directions and returns a value in zero
  to one. Compare it with a coverage field for deterministic stipple.

`examples/texture-synthesis.js` shows a quilted motif, an exemplar
repair, and a blue-noise density ramp on native voxel tiles.

### Dual surface samples and reinitialization

`geometry.surfaceNets(field, bounds, {cell})` takes the mean of
zero crossings in each active voxel. `geometry.dualContour` uses the
same crossings and fits their surface planes in a constrained
least-squares solve. Both take a negative-inside XYZ callback and
optionally a `normal(x, y, z)` callback. Results provide `points`,
`normals`, cell keys, and fit errors. Those samples can feed a custom
sculpt solid. Preview consumers can use `quads`, indexed `triangles`,
or `mesh({owner, surface, material})`.
Supply integer XYZ `latticeBounds` to place corners at global indices
times `cell`, which keeps coordinates identical across neighboring tiles.
`topology: false` skips face construction for splat builds.
`captureField: true` exposes `fieldSamples()` to copy the signed lattice.

`K.sdfgrid(sd, lo, hi, cell).reinitialize({passes: 2})` starts fast
sweeping from interpolated subcell crossings. It preserves field sign
and restores distance units after editing or scaling a signed field.
`S.smooth(held, {cell, reinitialize: true})` applies the same step before
baking a held sculpt. The bounded grid samples drive the zero surface.

`examples/dual-surface-studies.js` bakes a pair of carved blocks
using cell samples from the two extractors.

### Adaptive voxel levels

`geometry.octree(field, bounds, options)` samples a signed field on
dyadic cells. It prunes uniform cells when the configured Lipschitz
bound certifies that the zero surface is outside the cell. A true SDF
can use the default bound of one. Set `lipschitz: 0` to disable that
pruning on an arbitrary field. The tree refines around surface error,
normal changes, and ambiguous corners, and balances neighboring leaves
at a maximum 2:1 size ratio. Supply `surfaceDepth(point, info)` to
request more resolution in authored regions. `lookup` returns a leaf
and `at` reconstructs a local trilinear scalar estimate.

`geometry.stitchVoxelLevels(tree)` splits shared primal edges where
finer cells meet them. It joins those edges to the same neighboring dual
vertices on both levels, producing transition triangles and quads. Mesh
output is available for previews and interop. The cell vertices and
normals also feed native splats. `geometry.adaptiveSurface` runs both
steps and exposes the tree alongside the surface.

`examples/adaptive-surface.js` uses two voxel levels in one baked ring.
The alternate seed highlights the transition edges.

### Preview reduction

`geometry.simplifyQEM({points, triangles}, {ratio, target, groups,
locked, maxError})` reduces indexed triangles by quadric error. A
collapse must preserve the local mesh link and avoid reversed or
duplicate faces. Open boundaries and group seams are locked by
default. Pass one owner, surface, and material record per face in
`groups`. The result maps source vertices to surviving indices.

`lod.mergeSplats(records, {ratio, target, maxDistance, maxRadius,
viewDirections, silhouette, lockSeams, seamDistance})` reduces native Gaussian samples.
Each record has `id`, `position`, `normal`, `color` in normalized RGB,
optional `opacity`, and a `radius` or symmetric six-component
`covariance`. Owner, material, and surface names define independent
groups. The merger matches weighted centers and covariances, keeps
group boundaries, and can lock near-grazing samples for specified
view directions. Use `protect: true` for individually authored dabs.
Constraints may stop reduction above the requested count.

`lod.packSplats(result)` returns the static `data` and `count` fields
used by the renderer. `examples/preview-lod.js` packs an original and
reduced shield side by side.

The search ranks up to `candidateLimit` nearest candidates per survivor
(default 8) within each group and merges disjoint pairs in rounds. Set
`maxPairs` to bound candidate and cross-group pair checks. Increase
`candidateLimit` if close samples have incompatible normals or colours.
Use `seamDistance` to set the width of the protected area around boundaries
independently of the merge distance. It defaults to `maxDistance`.
A result with status `budget` may still contain valid merges. If the seam
scan stops early, the original rows are retained.

To protect a screen-space result, pass `guard(splats)`. It receives the
candidate records and returns a boolean. A failed guard returns status
`coverage` and retains the input. For example, render the original and
candidate using `studio.render(world, { captureCoverage: true, ...camera })`
and pass their coverage arrays to
`lod.compareCoverage(original, candidate, { threshold, maxMissing, maxExtra })`.
This measures holes and silhouette growth relative to the original foreground.
Repeat at the cameras and zoom levels the preview is intended for.
The packed output is static. Authoring data indexed by the original samples
must be rebuilt or remapped through each survivor's `members`.

### Delivery of baked rows

`KIT.procedural.splatCodec.encode(world.data, world.count, options)` returns a
`Uint8Array`. `decode(bytes, { maxRows })` returns `{ data, count }`.
Row order is preserved. Rig IDs, light captures, per-sample arrays, scene
settings and palettes travel with the host's scene data.

The position error limit defaults to `maxPositionError: 0.0001` world units
per axis. Each block uses 16-bit local bounds when the requested limit can be
met after reconstructing float32 positions. Other positions are stored exactly.
Axial covariances use a quantized direction and two logarithmic variances, when
the reconstructed float32 matrix passes the relative Frobenius error limit
(`maxCovarianceError: 0.004` by default) and keeps variance along the encoded
axis within 1%. Other covariances retain their original bits. Set both limits
to zero for bit-exact encoding. Colour, density, kind and motion fields always
retain their bits. NaN and infinite positions are rejected.

The little-endian stream starts with the four version bytes `IRC1` followed by
a 32-bit row count. Rows are grouped into blocks of up to 2,048 without
reordering. Within each block, fields are stored as constants or transposed
byte planes, with dedicated modes for position deltas and axial covariance.
Gzip or Brotli is applied by the host. The decoder validates its section bounds
and defaults to a four-million-row limit. Set a smaller `maxRows` for the
maximum size of the scene you expect to load. Use
`node scripts/benchmark-splat-codec.js` to compare size and decode time.

### Currents and surface motion

`motion.streamline(field, start, options)` traces a finite XYZ vector
field with fourth-order integration and optional local error control.
The field takes `(x, y, z, time)`. Supply a signed obstacle, clearance,
and optional bounds or mask. With normalization enabled, time advances
with arc step. Set `normalize: false` for a physical time step. In
bidirectional mode the length cap applies to each end of the path.

`motion.obstacleWake(sdf, {origin, flow, radius, length, width,
circulation, eddies, period})` adds an analytic downstream wake around a
signed obstacle. The result supplies a time-dependent `velocity` and
`vorticity`. The wake is an artistic field for currents, trails, and
local circulation.

`motion.loopTrajectory(points, {period, tension})` creates a closed
Hermite track with continuous position and velocity. Points can be XYZ
triples or `{at, point, velocity}` knots, where `at` is a normalized
phase. Sample the loop at any time, including negative times.

`motion.surfaceAdvection(chart, seeds, {velocity, step, boundary})`
stores UV coordinates for seeded particles or splats. The chart can
be a carrier or a time-to-carrier function. The solver projects each
world velocity into the chart metric and advances the UVs. The output
provides position, normal and tangent on the current deformed carrier.
Periodic carrier axes wrap, and other boundaries can clamp or stop
particles. Explicit `du` and `dv` on a chart sample avoid finite
differences.

`examples/flow-wake.js` traces the current around a river stone.
`examples/surface-advection.js` draws moving pigment on a changing
banner surface.

### Fluid grids

Both solvers take `{width, height, cell, origin, mask, initial}` for
an XZ lattice. `cell` can be a scalar or an XZ pair. A mask identifies
where the fluid may flow. A completed step returns independent typed
buffers and a world-space `sample(x, z)` function.

`motion.stableFluid` stores velocity on staggered grid faces. It
projects pressure on a closed domain, diffuses implicitly, and advects
velocity and density with a semi-Lagrangian backtrace. Pass
`{force, source, viscosity, diffusion, dissipation}` to `step(dt, options)`.
The snapshot includes density, velocity components and residual
divergence. Semi-Lagrangian density is intended for ink and fog effects.

`motion.shallowWater` takes a `terrain(x, z)` height field and initial
depth or `{depth, velocity}`. It advances water by conservative face
fluxes with hydrostatic reconstruction and CFL-limited substeps.
Optionally supply `rain`, `drain`, and `friction` to each step. The
snapshot supplies depth, water level, flow and a source-adjusted mass
balance. Flat water levels remain at rest over uneven terrain.

`examples/fluid-grids.js` uses the two grids to show suspended ink and
water flowing through a lowered point in a berm.

### Daylight-dependent sources

`KIT.procedural.lightSchedule.gain(daylight)` gives dusk strength. It is
zero above .58 daylight, one below .16 and eases between them.
`lightSchedule.select(lights, eye, {daylight, duskOnly, limit})` scales
sources declaring `schedule: 'dusk'` and chooses the strongest nearby
sources. Lights have world position `p`, positive `radius`, `intensity`,
normalized RGB `color` and an optional unit `normal` pointing toward
the illuminated side. `transfer(lights, x, y, z)` evaluates the bounded
spill from previously selected sources. Reuse `lightSchedule.glsl` for
radial falloff and the facing term on the GPU.

Use `lightSchedule.marker` as a splat motion descriptor for the source's
visible emitter. The offline renderer reads `lightDaylight` or the
environment daylight option and applies the live sources in `world.lights`
over the retained world.

### Weather and retained materials

Use [weather bindings](weather-binding.md) to run the rendering and retained fields from the same environment tracks. Use [world-space precipitation](world-precipitation.md) for rain and snow that can hit scene geometry and catch local light.

`airflow.frame([x, z])` converts horizontal scene velocity into raw transport
and a bounded displacement vector for flexible materials. A [shared wind field](wind-field.md) adds gust profiles and local shelter. Use
`airflow.bend(time, phase, frequency, reach)` for a scalar gust in scene
units. The matching GLSL function is available in `airflow.glsl`. Cloth,
foliage or other flexible surfaces can give each sculpt sample its own reach via
the material callback `motionAt(x, y, z)`. Return
`{k: 11, wind: true, ph, sp, rg}` to pack phase, angular frequency and
reach. Use zero reach at attachment points. The flag on the baked splat lets a
renderer apply the current wind without changing the sculpt.

`airflow.pinned({reach, phase, frequency, phaseTravel})` creates that
coefficient callback from normalized surface coordinates. Call it with
`(station, freedom = station)`. Freedom zero pins a sample and freedom one
gives the full reach. The separate station controls phase along the cloth.
Use a single station or set `phaseTravel: 0` for a surface that bends
uniformly parallel to its attachment. The offline `render(world, options)`
accepts `options.wind: [x, z]` or defaults to `world.anim.wind`. It uses the
same flexible displacement and windborne particle transport as the shader.

`motion.surfaceWeather({width, height, cell, origin, mask, initial,
normal, clock})` tracks wetness, temperature, accumulated light
exposure, snow and frost. Use `step(dt, {forcing})` to supply rain,
snowfall, air temperature, humidity, wind, shelter and runoff.
The forcing callback takes `(x, z, time, state)`. Optional `light`
overrides the illumination from the existing scene clock. Set
`precipitationExposure` to a fraction from zero to one to attenuate rain and
snowfall independently of thermal shelter. For instance, use
`P.overheadCover.exposure` with the local ground height in the forcing callback.
Wetness
moves across the grid and dries as the surface warms. Ice and snow
release moisture as they melt. Enable [standing water](retained-weather.md)
to store overflow in local basins and feed puddle finishes from the retained depth.

`motion.materialStateGraph({initial, states, transitions}, entities)`
tracks the state and material data of each named entity. Transitions
specify `id`, `from`, `to`, and `event`, with optional priority,
minimum age, a guard and an entity data patch. Dispatch a named
event at a time or call `advance(time, events)` to apply a timeline.
Omit the target for a broadcast. A snapshot can seed another controller,
preserving entry times and revisions.

`examples/persistent-weather.js` shows the same ground before and
after thaw and uses rain, footfall and sun events to change four
paving materials.

### Splat transport

`motion.transportSplats(source, target, {normalize, epsilon, iterations,
positionWeight, normalWeight, colorWeight, featureWeight})` builds a
balanced transport plan. Pass XYZ points or records with `id`,
`position`, and optional `weight`, `normal`, `color`, and `feature`.
An optional callback can supply a custom cost. The returned row-major
`mass` meets the normalized source and target masses, with forward and
reverse barycentric positions in world space. The status and residual
report whether the regularized solve converged within its work budget.

Set `correspondence: 'transport'` on `K.morph` to use those positions in
the existing stage effect. It can take contiguous dab ranges or explicit
dab ID lists. Pass solver settings through `transport`. The normal
correspondence mode uses nearest samples. `examples/transport-morph.js`
shows a leaf, an intermediate stage, and the resulting flower.

## Optional retained authoring

`KIT.authoring.document(snapshot?, options?)` stores JSON intent. Transactions
share stable identifiers, deterministic seeds, anchors, generated children,
overrides, undo/redo, and an optional storage adapter. Call `derive(owner,
rule, children)` with stable per-rule keys. Editing a derived child preserves
its overrides through regeneration. `promote(id)`, `suppress(id)`, and
`allow(owner, rule, key)` control its relationship to the rule. Pass `getItem`
and `setItem` to `doc.autosave(storage, key)` to keep a recovery journal.
Transactions and history checkpoints share unchanged scene records.
Undo, redo, and cancel can reuse their immutable read values, including
compiled field caches associated with those values. Autosave keeps the
version-one full-snapshot journal and reuses the encoding of earlier entries.
`projectDerived(snapshot, jobs)` runs the same derivations on a shared
immutable view without changing the document or its history.

`KIT.authoring.context(doc)` indexes spatial descriptors supplied by
`context.register(type, { describe, raycast? })`. Descriptors provide world
bounds and may expose named surfaces. `context.query`, `nearest`, `raycast`,
and `anchor` use those descriptors. A callback registered with
`context.rayFilter(id, callback)` receives the hit, entity, context and a
read-only copy of that raycast's options. Return `false` to reject the hit.
Applications can pass their own JSON-compatible options to choose a filter
policy for one query. `rayFilters: false` bypasses the registered filters for that ray.
A rule registered with
`context.rule({id, types, generate})` returns child specifications and can
read named entities, related collections, and spatial regions. Changes
invalidate affected descriptors and rules. The context reconciles within
the transaction and rolls back a rule chain that fails to converge.

`KIT.authoring.worldFrame(context, id)` composes local transforms and resolves
surface anchors. `context.style(id)` combines the environment, related hosts
and entity overrides through the same style catalog as the pure API.

`KIT.authoring.groups.select(source, ids)` resolves selected IDs, independent
transform roots, and the closure of parented, anchored, and generated children.
Capture the roots with `groups.capture(source, ids, {frame, pivot})` and apply
`groups.apply(doc, capture, {translate, yaw, pivot}, {write})`. Reuse one
capture for a drag to measure each preview against the original state. The
default writes the document's free-root transform format. A custom
`write(entity, worldPose, change, source)` supplies an entity patch for
terrain binding or an application-specific frame.

`groups.copy(doc, ids, {change, plan, remap})` duplicates the closure in one
transaction. It keeps seeds, generated overrides, and locally named surfaces.
Parent, anchor, and generation links within the copied set receive new IDs.
`remap(fields, lookup, original, source)` can map references stored in
type-specific parameters. The result lists copied member IDs and a mapping
from source IDs. `groups.remove(doc, ids)` batches normal retained deletion.

`groups.remember(doc, ids, {id, name})` stores a named selection in
`environment.presentation.groups`. `groups.bookmarks(source)` reports saved
membership and currently active IDs, so a deleted member can reappear after
undo. `groups.forget(doc, id)` removes just the saved selection.

`KIT.authoring.appearanceTransfer.create({describe, compatible?, validate?})` binds
portable finish samples to an application's own fields. The descriptor
receives `(entity, source, incoming?)` and returns `{family, label?, slots}`.
Each named slot has an effective `value` and an array `path` into the target
entity's appearance or parameters. A slot can supply `encode(value)` to
write a receiver-specific JSON value while keeping the sample in its
semantic form. For example, a sampled frame color can map to a material
reference with local overrides. A slot with `stored` compares that target
value against the encoded write when deciding whether the edit changes
anything. The default compatibility policy matches descriptor families.
For a finish that spans related records, set a slot's optional `target` to
an existing entity ID in the receiver's document. The descriptor chooses
that ID from the current scene. Plans merge writes for each entity,
reject conflicting paths, and apply all related patches in one undo step.

`capture(source, id)` returns a JSON-safe sample. `plan(source, ids, sample)`
resolves target patches and reports skipped IDs for callers that need a live
preview. `apply(doc, ids, sample)` applies the patches in one transaction.
`validate(source, edits, sample)` receives the complete plan before it can
be returned or applied. Use it to check target-specific constraints together
and throw when the plan is invalid.
Callers choose the target set and which fields to expose. Shared finishes
can use the separate document style catalog and `styleRef`.

`KIT.procedural.appearanceMemory({storage?, key?, normalize?})` holds immutable
JSON settings under caller-chosen names. Call `set(id, profile)`, `get(id)`,
`snapshot()`, or `clear(id?)`. The optional normalizer validates settings
on write and reload. An adapter with `getItem` and `setItem` enables persistence.
A failed adapter write leaves the previous in-memory state available. A caller
can use names for tool families, material roles, or another placement scope.

Material roles can refer to another role with a string or with an object
such as `{alias: 'timber', color: '#428d9f'}`. Object properties override
the referenced material. If the shared material changes later, fields
without local overrides continue to follow it.

`KIT.procedural.styles.recolor(profile, role, color)` prepares the material
patch for a local color edit. It retains a string reference as `alias` so
other fields still resolve through it. Apply the result as
`{materials: {[role]: patch}}`. Both forms of references reject cycles.

## Incremental realization

`P.chunks.create({preview, refine})` accepts synchronous builders or promises.
Call `await chunks.update(descriptors, options)` with the complete desired
descriptor set. Each descriptor has a stable `key`, a string or integer
`revision`, caller-owned `input`, optional `bounds`, and optional dependency
IDs. Bump the revision whenever the input changes, or supply `changedIds`
and `regions` for external dependencies. Treat inputs and committed outputs
as immutable while in use. The runtime retains payloads by reference.

Set `quality: 'preview'` for the fast builder and `quality: 'final'` for
refinement. The callback receives the descriptor, an abort signal, and
the previous payload and quality. Updates publish a patch with replacement
chunks, removed keys, and old and new affected regions. Submitting another
update or calling `cancel()` aborts obsolete work and suppresses publication
even if the builder ignores the signal. Builders can use a worker or another
async backend supplied by the caller. Achievable frame times depend on the
builders and renderer.

The gallery's **Retained assemblies** example combines these APIs. Resizing
the left mount changes generated attachments and replaces that mount's visual
chunk. The right payload is reused. Undo and Redo operate on the retained
document and trigger the same realization path.

### Shared chunk scheduling

`P.chunks.createScheduler({budgetBytes, concurrency, describe, load, sizeOf, release})`
keeps chunks resident for any number of independent consumers. Each
consumer opens an `interest(id, {priority})` and calls
`interest.update(requests, {priority})` with its current keys. A request is
a string key or `{key, priority}` with a relative priority offset.
The strongest request sets a shared key's priority. Higher numbers win,
and keys break ties. A missing or evicted key can be requested again.

```js
const grid = P.chunks.grid({dimensions: 2, size: cell * chunkCells});
const scheduler = P.chunks.createScheduler({
  budgetBytes: 16 * 1024 * 1024,
  describe(key) {
    const {place, index} = grid.address(key);
    const {revision, frame} = worlds.get(place);
    return {revision, bytes: 512 * 1024, input: {place, index, frame}};
  },
  load({input}, {signal}) {
    signal.throwIfAborted();
    return worldBuilders.get(input.place).build(input.frame, input.index);
  }
});

const player = scheduler.interest('player-collision', {priority: 100});
const viewer = scheduler.interest('camera', {priority: 30});
const underfoot = grid.key('heath', grid.index([playerX, playerZ]));
player.update([underfoot]);
viewer.update(grid.cover(visibleXZ).map(index => grid.key('heath', index)));
const [ground] = await player.ready();
```

Use `grid({dimensions: 3, size})` for XYZ chunks or two dimensions for
planar grids such as XZ biome columns. `grid.cover({min, max}, {limit})`
enumerates only the requested half-open window. Keys encode a place ID
and signed safe-integer indices, with no authored world boundary or
preallocated grid. Generate chunks from the place seed and address.
Use local coordinate origins when a geometry provider or packed splats
reach their numeric precision limits.

`describe(key)` returns a revision, a conservative byte reservation, and
caller-owned input, or null for an unavailable chunk. Revisions identify
immutable build inputs. Call `scheduler.refresh()` to reread descriptions
for current requests after an edit or to retry a failed build. Matching
revisions keep their resident objects. `load` accepts synchronous generators
or asynchronous loaders, including worker adapters. The default concurrency
is two. Cancelled jobs keep their reservations until they settle. A
superseded result is released instead of being published.

Once loaded, a chunk costs its full reservation or the byte count returned by
optional `sizeOf(value, descriptor)`. A measured chunk that exceeds its
reservation fails admission. This budget covers scheduler-owned chunks
and in-flight reservations. Use `release(value, descriptor)` to free
resources owned by a dropped, failed, or late result.

`interest.ready({keys, signal})` waits for the requested keys, or all keys
in that interest by default. The optional signal cancels the wait, and
`interest.close()` withdraws the requests. A closed interest, aborted
wait, or removed key resolves to null. A failed, unavailable, or
currently over-budget key rejects the wait. Synchronous interest changes
are reconciled together on the next microtask. Inspect a key with
`scheduler.status(key)` and look up its current payload with
`scheduler.get(key)`. `scheduler.snapshot()` returns a stable resident
view until publication changes, so hosts can rebuild packed splat inputs
only on resident changes. Call `scheduler.dispose()` to close every interest.

The [streamed places example](../examples/streamed-places.js) runs two
procedural places without a UI. The player and camera have separate
interests. A doorway starts with a small destination window. On crossing,
the same interests gain priority and expand around the arrival, keeping
overlapping chunks by reference as the outgoing place releases its interests.

Contact curves follow the input mesh resolution. `contacts.index` can restrict
the index to named surface groups and exposes bounds queries and segment
crossings. Use a closed shell for point containment and curve occlusion.
`intersections` returns paired surface names and stitched world points.
`clipCurve` returns exposed runs with source segment coordinates and blocker
IDs. The caller can send those runs to a route, sweep, or trim material.

### Incremental splat visibility and depth order

`P.sampleVisibility.create(count)` creates a one-bit-per-sample mask. Pass a
sorted, unique `Uint32Array` of hidden sample indices to `set`. It returns
whether the mask is active. Supply an empty array to clear it. Read
`changedRows` after each call for the changed texture span with exclusive
`end`, or null when the words are unchanged. `words` holds the integer
texture data in rows of `P.sampleVisibility.width` 32-bit words. Treat the
buffer as read-only. The optional `glsl` snippet shares the same addressing
for consumers using an R32UI texture.

`P.splatOrder.compile(indices, depthAt, behind?)` stores a depth order and
its bucket keys for fixed sample centers. Supply increasing nonnegative
sample indices and a finite depth callback. The optional `behind(index)`
predicate sends a sample to the far bucket. Rebuild the bank when its depths
or membership change.

`P.splatOrder.merge(bank, transientIndices, depthAt, behind, result, keys)`
sorts disjoint transient indices in place and writes the combined order into
the caller's result buffer. Use `Uint16Array` scratch storage for `keys`,
large enough to index each transient sample. Bucket ties follow ascending
sample index. A false return leaves the output untouched and signals that
the full depth range needs to be recomputed.

`KIT.splatInteractionDetail.compile(world, cell, {preserveOwners})` builds a
display-only density plan from a packed splat world. Use `indices` for the
increasing list of original representatives. `scale[i] / scaleUnits + 1`
is the covariance radius multiplier for representative index `i`.
Groups stay within the same owner, material, flags, and quantized normal.
The plan keeps animated, transparent, fine-tiled, and specially ordered
samples individual. It retains the full baked data for editing or capture.

`KIT.splatInteractionDetail.restore(level, edited, hidden, isHidden?)`
returns `representatives` that should draw at their original size and
`extras` to add at full resolution. Pass a visibility predicate to omit
hidden extra samples. The host still owns visibility tests for the
representative indices and decides when to draw each density level.


### Keyframe tracks

`KIT.anim.keyframeTrack.create(schema, keys)` compiles a portable timeline once
for repeated sampling. Each key has a time in seconds, a complete value
object, and an optional outgoing ease. Tracks have sorted immutable
`keys`, a `duration` in seconds, and a `sample(seconds)` method. Sampling
clamps to the first and last poses, or returns null for an empty track.

Channel modes are `number`, `vector` (fixed length), `radians` (continuous
shortest-arc interpolation), and `positive` (logarithmic interpolation).
Use `keyframeTrack.eases` for supported segment curves. A `step` segment
holds its pose until the next key. For a turn longer than half a revolution,
place intermediate keys. A camera is one configuration of the same track.

```js
const track = KIT.anim.keyframeTrack.create(
  { target: 'vector', yaw: 'radians', distance: 'positive' },
  [
    { time: 0, value: { target: [0, 1, 0], yaw: 0.25, distance: 24 }, ease: 'linear' },
    { time: 3, value: { target: [1, 2, 0], yaw: 1.2, distance: 17 } }
  ]
);
const pose = track.sample(1.5);
```

Persist `track.keys` and the channel mapping in the application's own document.
Sampling has no clock, rendering, document, or storage dependency.

### Named scene library

`KIT.authoring.sceneLibrary.create(storage, {key, backups, prepareSnapshot})` indexes named
documents and assigns each its own autosave journal. `create(name, snapshot)`
and `open(id)` return `{slot, doc}`, with autosave already bound. Use
`state()` for the active ID and slot metadata. Rename or archive a slot
without changing the document or its recoverable revisions. Unarchive
it before opening it again.

Use `adopt({id, name, journal, initial})` to register an older journal in
place. The optional initial snapshot initializes a missing journal.
The storage adapter follows `getItem / setItem`. An optional atomic
`compareAndSet(key, expected, next)` provides cross-session write protection.
Otherwise the library checks for changes before writing. Failed or stale
saves leave local edits available through the document so callers can export
them. The index stores metadata and references to journals. Documents keep
their authoring data and recovery revision format.

Pass a synchronous `prepareSnapshot(snapshot)` to the scene library or to
`KIT.authoring.document(initial, options)` to prepare imported and recovered
data. It receives an immutable validated view and returns a valid snapshot.
Opening a saved scene prepares the working document without adding an undo
step or rewriting the journal. A later save persists the prepared records.
Restoring a backup prepares that snapshot within the undoable restore.

### Asset packs and portable meshes

Use `KIT.authoring.assets` for versioned families with bounds, named
attachment sockets, and weighted declarative variants. Compatible
replacements share a kind and compatibility key, and provide every socket
required by the original family.

`KIT.authoring.assetPacks.create({families, packs})` builds a catalog from a
base family array and one or more manifests. An `ink-studio/asset-pack`
manifest at version 1 declares an `id`, `revision`, `title`, `families`,
and an optional `replacements` map. Additions are addressable by their
namespaced family ID. Compile an ordered list of active pack IDs for each
scene. Later entries take precedence. The resulting resolver keeps the
authored family IDs intact, validates cycles, and reports missing packs.

Packs can also ship `looks`, with or without families. The catalog exposes
their IDs and pack revisions through `getLook(id)`. Use
`assetPacks.reviseLook(pack, lookId, patch)` to update a look's label,
parameters, stack, or palette while keeping its ID. The revision advances
when the content changes. See [look asset bindings](pixel-look.md#look-assets-and-overrides).

Packs can also ship [environment presets and horizon artwork](environment-packs.md). Scene bindings can pin the same pack revision and apply local overrides.

`assetPacks.bundle(packs, ids)` creates one versioned JSON payload for
sharing packs. Omit `ids` to include all packs. If a selected pack
replaces a family owned by another installed pack, the bundle includes
that pack and follows its replacement dependencies as well.
`assetPacks.merge(installed, payload)` takes a single pack or a bundle,
as data or JSON text, and returns the proposed pack list and the
`added`, `updated`, `unchanged`, and `keptNewer` IDs. It preserves pack
order, keeps newer installed revisions, and rejects differing content
that claims the same ID and revision. Compile the proposed list with the
receiving catalog and its active selection before committing it. The
bundle carries pack assets and replacement declarations. Each scene
keeps its own active replacement order.

`assetPacks.reviseFamily(pack, familyId, patch)` prepares a portable
replacement for a family in an installed pack. The patch can update its
variants, bounds, sockets, label, and tags. A changed family advances
its version and the pack revision while keeping the stable IDs and
required sockets. Identical content keeps the current revision. Hosts
can use this operation with a file watcher or a manual replacement.

`KIT.authoring.assetMeshes.fromGLB(bytes, {size})` imports a small static
triangle model into a self-contained JSON recipe with fitted ground
coordinates and bounded face colors. `assetMeshes.recipe(mesh, {size})`
uses an already parsed mesh. The recipe carries geometry and base colors.
The caller selects the placement, material and rendering rules.

`await assetMeshes.importGLB(bytes, {size, socketNodes, decodeImage})`
also imports embedded PNG and JPEG textures for base color, normal,
roughness, and emission. The decoder takes
`(bytes, mime, {width, height, maxEdge})` and returns or resolves to
`{width, height, pixels}` with RGBA bytes. A plain color GLB needs no decoder.
Decoded images are fitted to at most 64 pixels on their longest edge.
The asset recipe retains the texels, UVs and color factors in JSON.

`assetMeshes.colorSampler(recipe)` returns `at(face, u, v)` for
barycentric weights of the face's second and third vertices and
`atPoint(face, x, y, z)` for a point in fitted asset coordinates.
Both return normalized sRGB. Sampling applies repeat, mirror or clamp,
nearest or linear filtering, and material and vertex factors in linear
space. UVs respect the binding's coordinate set and texture transform.
The matching `materialAt` and `materialAtPoint` methods also return the
shading normal, linear roughness and linear RGB emission. Pass the
geometric normal as the final optional argument for two-sided surfaces.
The normal channel uses authored vertex normals and tangents when
present. Its fallback derives a tangent frame from each triangle's UVs.
Roughness uses the green channel multiplied by its factor. Emission uses
the emissive factor and optional emissive strength.

`assetMeshes.shadeMaterial(sample, {irradiance, light, view})` applies
a diffuse gain, a roughness-dependent highlight and additive emission.
`light` and `view` are normalized directions in the sample's frame.

For camera-dependent shading, bake the diffuse color and emission by
omitting `light` and `view`. Keep the sample's shading normal and
roughness alongside that color. Each frame, use
`assetMeshes.highlight(normal, roughness, light, view)` to get the
additive linear highlight. Renderers can include
`assetMeshes.highlightGLSL` for the matching `assetHighlight` kernel
and `assetAddHighlight` to apply it to an sRGB color. Keep geometric
normals separately for shape, collision, and surface coating.

`assetMeshes.thumbnail(recipe, {size, padding, yaw, pitch, light})`
renders the asset's materials into a transparent square RGBA buffer.
The returned `{width, height, pixels}` uses orthographic framing and
depth testing. It works without a document, browser or renderer and can
be used for picker icons, previews or contact sheets.

Pass `socketNodes: { seat: 'Ride Seat', hook: 'Hook' }` to map names in
the active glTF scene to asset socket IDs. Matching nodes may be empty.
Each matching socket is saved as `{p,dir}` in the recipe's fitted
coordinates, including parent transforms. The node's local +Z defines
its forward direction. Absent node names are omitted. Duplicate matches
for a requested name report an error. The named sockets can be reused in
an asset family or interpreted by a placement system.

### Surface lighting overrides

`KIT.procedural.surfaceLighting.override(options)` prepares an immutable
material override for an inspection view. Configure a normalized RGB
`albedo`, a `fallback` irradiance for surfaces without lighting data, and
an optional RGB `background`. The boolean `preserveEmission` and
`preserveLiquid` settings default to true so a renderer can preserve
light sources and water. A renderer applies these settings to its own
surface classifications.

`surfaceLighting.shade(irradiance, style)` multiplies the configured
albedo by the attributed irradiance and clamps the output channels.
Pass `undefined` to use the fallback. The override can change independently
of the original model, material palette, and recorded lighting values.

### Paint domains

`KIT.procedural.clipPaintDomain(field, domain, { mode })` limits a resolved
paint field to a signed XZ domain. Both inputs supply `distanceAt(x, z)`
with negative distances inside. A paint field may also accept an upper
bound as its third argument. The result clamps its distance to that bound.
The domain may supply an equivalent `inside(x, z)` predicate for faster
membership checks and a world-space `bounds: { min, max }` box to tighten
the result's horizontal bounds.

The default `intersect` mode uses the larger of the stroke and boundary
distances. `gate` preserves the original distance inside and returns an
empty field outside, which lets a depth or height profile keep its shape
up to the edge. Outside the domain, the result reports zero coverage and
no paint owner. The original field is available as `raw`, so moving the
domain can expose previously retained portions of a stroke.

### Ordered height layers

`KIT.heightLayers.sample(layers, x, z)` evaluates ordered height edits and
returns a delta from the base surface, an owning layer ID, and coverage.
Each layer supplies `entity.id`, `parameters.operation`, `parameters.height`,
world-space `bounds: {min, max}`, and a `weight(x, z)` in `[0, 1]`.
Operations are `add`, `max`, `min`, `replace`, and `erase`. An erase fades
earlier edits toward zero. Full erasure clears ownership, and later layers
can make new contributions at the same point.

Provide a signed `support(x, z)` for each layer to query
`KIT.heightLayers.distance(layers, x, z, ownerId?)`. Negative values mark
the support interior. For an eraser, use the support of its fully erased
region. Passing an owner ID clips that layer by later layers and erasers.
The caller owns ordering, mask construction, and selection of spatial
candidates. Swept masks are one way to build the layer functions.

`KIT.heightLayers.reorder(records, id, toIndex)` plans an edit to composition order. Pass records with unique `id` strings and nonnegative integer `order` values. The index is zero-based in application order. Apply the returned `{ id, order }` updates together. It keeps the existing ranks where possible and compacts tied ranks when the desired order cannot fit. `compareOrder` orders records by rank and then identity, matching legacy scenes with tied ranks.

Use `KIT.heightLayers.mask(layer, edits)` to cut and repair only the
supplied height layer before it enters the stack. Each edit supplies an
`operation` of `cut` or `repair`, a fractional `weight(x, z)`, and a
signed `support(x, z)`. A cut's support is its fully opaque interior.
A repair's support covers its entire nonzero feather. The wrapper
preserves the original height operation and applies the edits in order.
Repair restores coverage removed from that layer, including partial
coverage around the edge of a cut.

### Fitted profile runs

`KIT.procedural.fittedProfileRun({path, profiles, pitch, gap, up, budget})`
fits repeated sections along an open 3D polyline. Pass one or more convex
2D cross sections in lateral and up coordinates. Sections use the length of
the run to fit their pitch. The gap is a fraction of the fitted pitch, and the
first and last ends reach the ends of the path. At a turn, fragments of the
same section retain the same station index.

`run.pieces({key, owner, material})` returns closed convex pieces with stable
keys, mesh, distance, intersection, and surface-sampling methods. Use one
profile for a cap or multiple profiles for an open channel. The up vector
sets the profile orientation. Each path segment needs an extent perpendicular
to it. Use a backing strip when the chosen treatment needs continuous
coverage through joints and turns.

### Offset rail pairs

`KIT.procedural.roundedPath(path, { radius, chordError, maxDeviation, budget })` fits
tangent circular bends to an open 3D polyline. Each bend cuts back at most
45% of either adjacent leg. Closely spaced turns contract their radii without
overlap. Collinear stations and reversals retain their original points.
The result contains the sampled `points` and `bends` with each source index,
sample range, actual radius, center and cutback. Chord error controls arc
resolution. Set `maxDeviation` to limit how far the arc can cut inside the
original corner. The function rejects a result that exceeds the sample budget.

`KIT.procedural.offsetRails({ path, halfWidth, up, closed, miterLimit, shareSpan })`
returns matching `left` and `right` rails around a sequence of 3D points.
`halfWidth` can be one positive distance or an array for a tapered run.
The solver measures lateral offsets in the plane perpendicular to `up`
without flattening station heights. Closed paths use a single shared seam
station, so supply each point once. Miters contract on very short or acute
segments. Use `shareSpan: true` to let both corners draw from the same
length allowance, so an isolated corner can use the free part of a short
straight lead. The result flags contractions in `contracted`; split the run
at any station listed in `reversals` before extruding the ribbon.

Pass the original spine as `measure` to `fittedRibbon` or `fittedRailBand`
to space joints along the center. It must have one point of the same
dimension for every rail station. Each fragment still interpolates both
actual rails. The same operation works for caps, strips, paths and bands.

### Ribbon sections

`KIT.procedural.profileBand` converts a directed 2D profile into paired rails
and fits a ribbon between them. Supply a positive scalar width or a width for
each point. The default right side runs outside a counterclockwise closed
profile. Set `closed: false` for an open run, or use `side: 'left'` to reverse
the offset. Fitted cells retain source edge indices and share exact vertices
where a piece crosses a corner. The result exposes the outer rail and marks
any stations contracted to keep the local miters within the adjacent edges.

`KIT.procedural.fittedRibbon({ inner, outer, pitch, gap, sections })` accepts
landmarks as ordered sections. Each entry has a unique `id` and a normalized
`end` station along the inner rail. The first section starts at zero and the
last ends at one. A section can override `pitch` and `gap`, or specify a
positive integer `count` to fit exactly that many cells over its span. A
single cell can span several rail edges and retains the same key through the
join. Use this to control joints at shoulders, corners or other intentional
breaks. On a closed ribbon with sections, the seam is a section boundary and
phase must be zero.

Each sectioned cell reports `section`, `unit`, `from` and `to`; the overall
`unit` is the mean pitch. Gap setbacks also apply at interior section
boundaries, using the gap from each side. Omit sections to use the established
uniform fit.

### Fitted rail bands

`KIT.procedural.fittedRailBand({inner, outer, pitch, gap, closed, phase, sections, measure, depth, profile, direction, cellStyle, budget})`
fits repeated solids between two matching 3D rails. Layout uses the inner rail's
length or the optional measuring spine, with a pitch and joint gap in the same units. `depth` is a pair of signed
offsets along the normalized vector returned by `direction(point, fragment, cell)`.
Optional `cellStyle(cell)` can provide a different `depth` pair and `material`
role for the entire logical cell. A planar convex footprint produces one prism. Warped footprints are split into
prisms with the same logical cell and fragment.

Supply `profile` to loft a strictly convex cross section between the paired
rails. Write the outline in boundary order as 3 to 12 `[fraction, depth]`
points. Fraction runs from 0 on the inner rail to 1 on the outer rail, so
the section follows changes in width. Depth is signed along the sampled
direction, in world units. Each fragment encloses the convex hull of its
two sections. Matching rails and a common direction give adjoining
fragments the same end section through turns and at a closed seam.
`cellStyle(cell)` can also select a profile and material for that cell
or use a rectangular `depth` override.

`band.layout` exposes the fitted ribbon. `band.pieces({owner, key, material})`
returns closed convex pieces with bounds, a mesh, signed distance, ray
intersections and surface samples. Piece keys include the cell, fragment and
split index. Callers supply rails, normals and any clearance fields to compose
with the band, for example along an opening, on a curved wall or at a deck edge.

### Clipped lattices

`KIT.procedural.clippedLattice({panels, runs, edges, edgeWidth, budget})`
fits strips across a group of convex polygons in a common 2D chart. Each
panel supplies a unique `key` and `polygon`. A run supplies `axis` (a
2D vector perpendicular to its bars), `pitch`, `width` and an optional
`phase` in fractions of the fitted pitch from `-.5` to `.5`. Each run
fits a whole number of evenly spaced bars. Optional `edges` are pairs of
chart points. They become frame strips of `edgeWidth` before clipping.
Specify the exposed edges when multiple panels share a seam.

`lattice.members` contains stable keys, bar or frame roles, and convex
`{panel, polygon}` fragments. `lattice.pieces({map, direction, depth,
owner, key, material, frameMaterial})` extrudes each fragment.
`map(panel, point)` supplies a 3D position and keeps each panel planar.
The direction can be a vector or a function of the panel key and need
not be perpendicular to the panel. `depth` contains the two signed
offsets along the normalized direction. Solid pieces support meshes,
distance queries, ray hits and sampling. Use a panel per facet to map
the same layout onto a curved carrier. The caller supplies the profile
and decides when to insert the lattice.

### Bounded field probes

`KIT.boundedFields.halfspaces(planes)` compiles convex plane fields into
a scalar probe. With no limit it returns the maximum plane distance. With
a finite limit it can return early once a plane proves the result exceeds
that limit. A caller can compare the result with the limit to cull the
solid during a union or shadow query.

`KIT.boundedFields.heightMask({height, mask, scale, minimumHeight, minimumScale})`
returns the maximum of a signed horizontal mask and a scaled height distance.
Supply a conservative minimum height and a distance scale in
`[minimumScale, 1]`. The probe skips the height and scale callbacks whenever
the horizontal mask determines the exact result.

`KIT.boundedFields.unionFloor(first, second)` returns a probe that evaluates
`max(floor, min(first(point), second(point)))` for finite signed fields.
Pass the cheaper field first. If its value is already at or below the floor,
the second field cannot change the result.

Pass a world-space `lowerBound(x, y, z, limit)` callback to a sculpt
primitive to apply a conservative probe during field traversal. Include all
geometry that can affect the primitive's raw signed distance in the bound.
The traversal accounts for the primitive's blend width and bump amplitude.

### Chart positions and normals

Planar, cylindrical and affine-transformed charts expose
`samplePointNormal(uv)` for callers that need only the position and normal
from `sample(uv)`. Transformed planes reuse their constant world normal,
including when multiple transforms are applied. A planar chart also
provides `planePoint(uv)` when a caller only needs the position.
Context adapters can supply the same optional method on their own charts.

### Closed extrusions with blind recesses

`geometry.recessedProfile` forms a solid from two XY rings and a Z span
`[back, front]`. Supply a center visible from every edge of both rings.
Each ring can use either winding, and the recess ring must lie strictly
inside the exterior ring. The inset is measured back from the front and
must leave positive backing thickness. Use `distance([x, y, z])` for
inside/outside queries, `mesh(metadata)` for a closed surface, and
`sample(spacing, emit)` for points on the same surface.

Use `mesh(metadata, surfaces)` to override metadata by face. The keys are
`front`, `back`, `outer-wall`, `reveal`, and `recess-back`. The reveal forms
the sides of the recess between the front and its backing. For an analytic
renderer, `surfaceAt([x, y, z])` identifies the nearest face with the same keys.
The caps take precedence at shared edges.

Pass `center: null` to triangulate the caps of arbitrary simple nested
rings. The front cap has the recess ring as a hole. The recess and rear
caps share their boundary vertices with the side faces. This mode
supports outlines without a point visible from every edge. Sampling covers
the filled intervals on each cap and spaces side samples by edge length
and depth, independent of the cap triangulation.

`geometry.fitMonotoneOutline` takes an authored XY ring and an optional
required XY ring. Each must have one contiguous interior span at each
height. The required ring must fit within the authored height range.
The fitter extends the left and right traces only where required, adding
exact intersections where one sloped side overtakes the other. It keeps
horizontal ledges and returns a counterclockwise exterior ring.

`geometry.fitExteriorOutline` takes simple authored and required XY rings.
Each can have several spans at one height. It splits edges at intersections,
keeps the exposed boundary of the union, and returns one closed exterior
ring in counterclockwise order. Enclosed holes are filled. The rings may
overlap or share edges. A disconnected union or a point contact is invalid.
With no required ring, it validates and normalizes the authored ring.

### Retained environment profiles

`KIT.authoring.environmentProfiles.create({key, profiles, defaultId, defaults,
validate})` builds a catalog over caller-defined environment values. Each
profile supplies an ID, label and values. It inherits defaults and merges
its own saved overrides. Supply a validator for the resolved value shape.

`select(doc, id)`, `edit(doc, patch)` and `reset(doc)` are undoable and
store data under `environment.presentation.profiles[key]`. The active
profile and each profile's adjustments persist with the document. The
catalog leaves entities, authored construction settings, and other
presentation channels intact. When a saved profile is unavailable,
`resolve(source)` returns the default with `missing: true` and the saved
requested ID so callers can show the fallback.

### Camera pivots

`P.cameraPivots.choose(mode, { cursor, pick, fallback, radius })` resolves a world point from normalized viewport coordinates running left to right and top to bottom. `pick(u, v)` returns the app's chosen surface point or null. Modes are `target` (return the fallback), `cursor` (use the supplied coordinates), `center` (one center sample), and `region` (center followed by nearby samples until a hit). The cursor defaults to the center. The selection includes at most nine samples so an app can reuse a pivot across an input gesture.

`P.cameraPivots.orbit(view, yaw, pitch, pivot)` rotates the view around a world point while keeping that point at the same screen position. `P.cameraPivots.zoom(view, dist, pivot)` keeps the same screen position as the distance changes. A view supplies `{ yaw, pitch, dist, target }` with angles in radians, positive camera distance, and a three-component world-space target. Both functions return a new view. Passing a null pivot keeps the target fixed. The caller supplies camera limits, picking rules, and input bindings.

### Chain joins

`P.chainJoins.plan(first, second, { tolerance, firstEnd, secondEnd })` determines how to stitch two open chains in 3D. Each chain supplies world-space `start` and `end` points and its positive arc `length`. The default chooses the nearest pair within `tolerance`, or returns null. Pass a specific end (0 for start, 1 for end) to honor a known snap target.

The plan puts the first chain before the second. It supplies `reverseFirst`, `reverseSecond` and the normalized join station `split`. `mapFirst(u)` and `mapSecond(u)` transfer positions from either input's normalized arc to the concatenation. Use the direction flags to handle sided attributes, cross-section coordinates, or directional metadata. Geometry construction and attribute precedence belong to the caller.

### Linear profiles

`P.linearProfile.compile([[coordinate, value], ...])` compiles a
piecewise-linear scalar field. Coordinates increase strictly, and values
can rise or fall. `at(coordinate)` interpolates within the domain and clamps
outside it. The frozen `knots` supply explicit breaks for tessellation.
`slopeBound` is the greatest absolute slope, useful for adaptive contact
queries on composed surfaces.

### Coordinates on closed carriers

`P.periodicCoordinates.wrap(value, period = 1)` returns a station in the half-open interval from zero to the period. `delta(value, origin, period = 1)` measures the signed shortest displacement, with a half-turn choosing the negative direction. Supply finite stations and a finite positive period.

`unwrap(values, period = 1)` returns stations in the smallest continuous interval covering the supplied positions. It cuts the loop at the largest empty gap and preserves the input order. This lets tools order nearby objects, measure distances or compute centers without splitting a group at the chart seam. Wrap the result of an average to store it as a station on the original chart.

`P.periodicCoordinates.loop([{key, length}, ...])` measures an ordered,
closed chain of keyed spans. `station(key, fraction)` converts a
span-local fraction to distance along the chain and accepts extrapolated
fractions. `locate(station)` wraps that distance and returns
`{key, fraction}` on the span containing it. At an exact seam, the next
span owns the station. Use the same chart to group or move features across
face boundaries while storing their local attachment coordinates.

### Path clearances for fitted cells

`surfaceCells.pathMask(paths, { facets })` buffers chart-local polylines into convex strips with rounded polygonal caps. Each path supplies `{ points, radius }`. The result exposes `holes` for cell clipping and `distance(u, v)` for field evaluation against the same footprints. The default uses four edges on each cap. Distance is negative inside the union. A single point creates a round clearance, and consecutive collinear stations share one strip.

### Height surface rays

`P.heightSurface.raycast(surface, origin, direction, options)` finds the first crossing of a bounded height graph. Supply `bounds`, `height(x, z)` and optionally `inside(x, z)` and `normal(x, z)`. The result contains a world point, normal (when supplied), and distance along the normalized ray. A miss returns null.

`P.heightSurface.ceiling(level, regions)` prepares a proof of empty space
above a height graph. The supplied regions must enclose every location
that can rise above the level. Pass the result as the `ceiling` ray option
to skip the empty prefix of a descending ray. `withNormal: false` skips
normal sampling when the consumer needs only position and distance.

Use `P.heightSurface.rangeOverPlan(height, outline, {spacing, budget})` for
sampled `{min,max,samples}` over an XZ ring. The function samples every
vertex, the boundary between vertices, and cell centers inside the ring.
It throws when the candidate count exceeds the budget. Use a smaller
spacing or extra clearance for sharply varying surfaces. Intersect the
query ring with the heightfield's footprint first when it is bounded.

`P.heightSurface.seatSites(origin, sites, height, {offset, maxDelta})` seats
independent supports or roots of a footprint. Pass a world XYZ reference
point and keyed sites of the form `{key, offset: [x,z]}`. Each offset is
relative to the reference point in the horizontal plane. The height sampler
may return null for an excluded site. A finite `maxDelta` rejects sites
whose sampled height differs from the reference Y by too much. The optional
vertical offset is added after that check. Results contain `{key, point}` in
input order, so surrounding relief and masks can change while keys and
horizontal positions remain stable. The function makes one height query per
site, with a limit of 4,096 sites.

A caller can pass a certified `slopeBound` on the horizontal gradient. This allows steep rays to solve one bracket and other rays to skip intervals that cannot cross the surface. Without a bound the query samples at regular intervals. Vertical rays evaluate the height directly. `maxDistance` defaults to 10000 world units.

### Edit assembled parts

Use `P.logicalParts.compile(pieces, piece => piece.stockId)` to index fragments
of the same edit target. A caller can use the logical cell ID from a fitted
strip, a manufactured kit ID, or another stable key. Supply a nullish key
for backing or other always-visible pieces. `index.groups` lists distinct
keys and their fragments. `index.get(key)` returns all fragments of a single
part. `index.partition(hiddenKeys)` returns `{ visible, omitted }` in input
order. Retain the hidden keys alongside the generator input. Unknown keys
can stay dormant until a future realization contains the part again.

Use `P.logicalParts.edits(keys, anchors, locate)` when a rebuilt layout can
assign a different key to the same place. `anchors` contains `{key, site}`
records with a finite two-component chart coordinate. The caller resolves
`locate(site, key)` to a current part key or returns null while the site is
out of range. Keys without anchors still identify parts directly. The
returned `keys` and `has(key)` describe current omissions. Call
`setVisible(key, visible, site)` to get a new pair of serialized `keys` and
`anchors` arrays, or null when the edit changes nothing. Supply the chart
point of the part when erasing. A restore clears all sites currently
mapped to that part. If several erased sites resolve to one coarse part,
the original sites remain stored and can resolve to separate parts again.

To capture positions for older key-only edits, call
`P.logicalParts.captureAnchors(keys, anchors, siteFor)`. `siteFor(key)`
returns a site in the loaded layout or null when the part is unavailable.
Existing positions are preserved. Pass the returned anchors and original keys
to the next layout. The function returns the original anchor array when
there are no new sites.

### Courses on a variable strip

`KIT.stripCourses({ sections, unit, joint, stagger, datum, closed, offset,
columnPeriod, budget })` fits rectangular stock to a strip whose lower and upper
edges can vary independently. Supply an ordered list of `{ s, lower, upper }`
in strip coordinates, beginning at `s: 0`, and a nominal pair `unit: [width,
height]`. Each convex fragment is clipped to one piecewise-linear section and
reports its polygon, section index and logical row and column. A cell can span
several sections without adding a joint at their boundaries.

Use `unit: [width, null]` for full-height stock such as boards or louvers.
Each column spans from the lower edge to the upper edge. The joint applies
along the strip and the stock keeps one logical ID across section breaks.
The vertical datum and row staggering apply to the rectangular stock mode.

A closed strip fits a whole number of columns and shares the logical cell ID
across its seam. Retain the fitted width, `columnPeriod` and `offset` of a
surviving portion when cutting a closed strip into open fragments. `datum`
anchors the row elevations and `offset` sets the starting coordinate of the
stock along the run. An open strip keeps the nominal width. `stockColumn`
identifies the unwrapped column even when two fragments share a logical ID.
Exceeding the bounded fragment or work budget raises a `RangeError`.

The layout is independent of geometry, style and rendering. A consumer can
map the polygons onto a carrier, extrude them into physical blocks, or use the
same layout for materials and coverage on a sloped surface.

`layout.bandAt(s)` returns the interpolated `{lower, upper}` across the
strip. `layout.keyAt(s, y)` returns the nominal logical cell at a point,
including positions in joints. Both return null for points outside their
domain. Use the key with your emitted stock index to check that the cell
has physical fragments. This lookup can resolve a retained edit when a
new pitch or datum changes the layout.

### Editable support facing

`supportCourses(skirt, {omit})` uses the periodic row/column IDs from
`plan.lookup(point).cell.id`. All fragments of that logical cell are recessed
to the backing, including fragments on either side of the perimeter seam.
`plan.lookup(point).omitted` reports the saved choice. `plan.frontage(id)`
returns face outlines with outward normals, clipped between the terrain and
carrier. The signed field and sample emitter both include the recesses.

For a location-based edit, pass `plan.stockSite(id)` to
`plan.edits.setVisible(id, false, site)`. Save the returned arrays and pass
them as `omit` and `anchors` to the next support layout. The first site
coordinate describes an edge index and fraction in a normalized outline
interval. The second is distance down from the top course datum. Keep the
same ordered outline edges to follow a particular side during resizing.

### Convex keepout subtraction

`KIT.procedural.geometry.subtractConvexFaces(faces, planes, { capTag, budget })`
removes a keepout described by half spaces from a closed, convex polygon shell.
Each plane keeps points whose signed value `normal · point - offset` is
nonpositive for points inside the volume to remove. The result contains closed
convex shells with disjoint interiors. The operation keeps polygon face tags,
and newly cut caps get the plane's tag or the supplied `capTag`.

An empty or missed keepout returns the original shell, and a full cover
returns an empty array. The default fragment budget is 256. Larger outputs
raise a `RangeError`. The supplied half spaces and shell need to be finite.

### Convex height prisms

`KIT.procedural.geometry.heightPrismPlanes({ lower, upper })` describes
a convex volume between planar height caps. Pass corresponding 3D rings
with the same convex XZ footprint and with the upper ring at or above
the lower ring. Either winding is accepted. The two heights can slope
independently.

The result contains normalized outward half spaces. Planes identify the
`lower` and `upper` caps and the lateral `side` faces. Side planes also
give their original edge index. Use the planes for intersection,
occupied-volume sampling or keepout subtraction. Joining several prisms
can approximate a shaped height field while assigning clearance only
to exposed faces.
### Intersecting convex plans

`KIT.procedural.geometry.intersectConvexPlans(subject, boundary)` returns the
shared XZ footprint of two convex rings. Both inputs accept either winding.
The result is a fresh counterclockwise ring, or an empty array if the domains
have no shared area. Use the shared plan when a projected part must stop at a
carrier edge. For a vertical fit, lift that ring onto the part and pass it to
`supportSkirt` with the carrier's height field.

### Transitioning retained samples

`KIT.procedural.sampleCoverage.cohort(x, y, z, spacing, seed)` assigns a stable
integer rank to a point in a local grid. Pass that rank as `{coverage:rank}`
alongside a dab's animation options. Drawing with a `sampleWithdrawal` between
zero and one progressively hides marked samples. Unmarked samples remain visible
at full withdrawal. The packed rank preserves the existing motion flags. Hosts
can use `sampleCoverage.visible(code, amount)` or inject `sampleCoverage.glsl`
into a vertex shader. The offline renderer accepts the same amount as a render
option or world property.

Pass `{coverage:rank, coverageEnter:true}` to reveal a cohort at the same
threshold where an ordinary cohort disappears. Entering samples start hidden.
Both populations share a bake, retain their own motion flags and reverse when
the amount decreases. The WebGL renderer accepts `frame.sampleWithdrawal` with
the standard toolkit. A low-level pipeline can receive
`{sampleCoverage: KIT.procedural.sampleCoverage}` and set
`u_sampleWithdrawal` directly.

Keep independent layers in a single sculpt template. Mark a structural part
with `{whole:true}` in the solid's options to retain samples behind other parts
of its own instance. This still clips against neighboring solids. Set
`omitFromProxy:true` on a material whose geometry draws in the template but
should stay out of the placed instance's static field and shadows.

### Contact volumes for surface cells

`KIT.procedural.surfaceCells.prisms(layout, { sample, levels, step, budget, planar })`
returns convex contact pieces with a logical cell key, bounds, and unit-normal
planes. It uses the same tessellation as `surfaceCells.loft`. Sample the two
levels on the same local XZ footprint with increasing Y, then transform the
resulting volumes into the surrounding assembly. The footprint can contain
clipped gaps or holes already represented by the layout's fragments.

The optional `planar` flag or `(key, polygon) => boolean` predicate keeps
a known affine fragment in one prism. Otherwise `step` controls tessellation.
`budget` limits the number of pieces. Plane records mark the upper, lower
and fragment perimeter as `exterior`. Triangulation seams stay unmarked
so callers can add contact clearance without widening the seams.

### Captured lighting for a host renderer

Call `KIT.light.capture(B, S)` before baking and `KIT.light.pack(stage, capture,
{ sun })` after the stage's rig is bound. The pack supplies one entry per native
row and a palette ramp table. Both arrays are interleaved float32 vectors:

| Buffer | Components |
| --- | --- |
| `normalLevel` | Baked normal x, y, z and ramp level |
| `rigRamp` | Ramp index (−1 for uncaptured), part ID (0 for static), live-sun flag, reference term |

`step(packed, row, position, normal, lights, flash)` returns the palette index
the lighting calculation selects, or −1 for an uncaptured row. Supply the
current position and a unit normal matching that pose. A host using the stage
rig's convention applies the normal's part matrix and normalizes the result.
Part IDs are those of the bound stage rig. Repack after changing part ownership,
the capture, the baked reference lighting, or the selected sun parts.

Include `KIT.light.glsl` in a high-precision GLSL shader. Start with the stored
ramp level. Where the live-sun flag is set, evaluate `capturedSun` and add any
baked lamp shares with `capturedLampShare`. Pass this value, the reference term,
and the host's shade factor to `capturedBase`. A host must provide an equivalent
shade when `sun.shade` is a JavaScript function. Add active dynamic lamp shares
and flash. Pass each lamp's visibility as its per-splat mask divided by 255,
or 1 when there is no mask. Find the largest share among the lights with their
own colour ramp. Use its ramp when `capturedOverride` is true. Index the selected
ramp with `capturedStep`.

`sun.keep` defaults to 0.09 and limits the residual from the bake. With
`sun.keep: Infinity`, `packed.delta` is true, the reference term is the
rest-pose lighting, and `baked` is an extra array of original palette indices
(−1 when a row has no delta mode). Pass `packed.delta` to `capturedBase`.
When there is no dominant lamp ramp and `capturedAtRest` is true, use that
original palette index if available. `sun.lights` optionally specifies the
bake's lamps for the live sun calculation. Baked lamp ramps are already
represented in the baked colour. Dynamic lamps with their own ramp can change
the output ramp. The CPU stage painter still composes with other painters in
stage order. The host is responsible for composing its own render passes.

Set `INK_TEST_CHROME` to the Chrome executable and run
`node --test tests/captured-light.test.js` to verify the GLSL against the CPU
reference using WebGL2 transform feedback.

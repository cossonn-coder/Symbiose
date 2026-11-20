# Destruction bindings

`K.destruction(stage, options)` gives existing splats structural names and
transfers their **current** geometry to owned `K.rubble` or `K.debris` solvers.
It adds no replacement geometry and does not change the SDF/splat workflow.
Scenery, rigs, rides and moving props can use the same binding.

The [siege garden](../examples/destruction.html) is an interactive cannon and
catapult example. Its [scene module](../examples/destruction.js) also works
with the CLI and headless tools. Build the browser bundle with
`require('fs').writeFileSync('dist/ink-studio.browser.js', require('.').bundle())`
and serve the repository over HTTP to open the page.

```js
const stage = K.stage(world);
// Register kinematic animation before destruction.
const destruction = stage.add(K.destruction(stage, {
  gravity: 18,
  maxPieces: 96,
  groups: [
    { id: 'pier', selector: { material: 'pier-stone' },
      anchor: true, mass: 20, strength: 8, fragmentSize: 0.7 },
    { id: 'deck', ids: deckSplats, mass: 15, strength: 12 },
    { id: 'roof', ids: roofSplats, mass: 5, mode: 'debris' }
  ],
  links: [['pier', 'deck'], ['deck', 'roof']]
}));

// A swept sphere catches thin structures even at cannonball speeds.
const ball = destruction.launch({
  p: [-8, 2, 0], v: [35, 3, 0], radius: 0.2, mass: 6
});
// Render ball.p with a frame splat, model or another host-owned visual.

// A scheduled ride failure can use the same handoff without a projectile.
const car = route.vehicle(event.time, { offset: carOffset });
destruction.release('car', { v: car.velocity, w: [0, 0, 0], origin: car.p });

// Restore the binding's creation snapshot and animation ownership.
destruction.reset();
```

## Groups, ownership and motion

Each group needs a distinct `id` and either a nonempty `ids` array of stable
splat indices, or a shared `selector` such as `{ object: 'gate' }`,
`{ material: 'stone' }` or `{ tag: 'breakable' }`. Selectors are resolved once
at creation. Selection shares the same metadata as rendering and look tools.
A splat cannot belong to two groups or two destruction bindings on a stage.
Do not also hand these splats to another physics writer. Released rows are
marked in `stage.physicsOwned`. Rigs, frame splats and pool writes/hides respect
this mask, so their kinematic animation cannot erase physics-owned geometry.
Frame and pool writers also keep their paint baselines current, so repainting
a detached model preserves its appearance. Custom animation writers should skip masked rows. Keep frame-model calls in a
stable order, or reserve a separate pool per bound model; do not compact or
reuse those slots for unrelated models after a release. Bind a frame model
after its initial pose has been drawn so reset can capture that pose.

| Group option | Default and behavior |
| --- | --- |
| `mass` | `max(1, splatCount * 0.02)`. Positive mass, distributed among fragments by sample count. Independent of later rendering detail. |
| `strength` | 2. Positive cumulative impulse threshold. Damage increases by applied impulse magnitude divided by strength. |
| `breakable` | true. If false, impacts cannot damage this group. Explicit release or loss of its supports can still detach it. |
| `fragmentSize` | 0, meaning one rigid piece. A positive world-space cell size partitions the current geometry into spatial lumps. |
| `mode` | `'rubble'` for lasting rigid pieces, or `'debris'` for temporary fading fragments. |
| `anchor` | false. An intact anchor is a root of the optional support graph. |
| `static` | false. Set true for unmoving scenery to cache its bounds. Dynamic groups refresh bounds and estimate motion each update. |
| `motion` | Optional `(stageTime, groupId) => ({ v, w, origin })`. World linear velocity at `origin`, and world angular velocity in radians/sec. Prefer exact route/rig data when available. |
| `solid` | Optional world-space signed distance function for precise intact collision shapes. It should fit the rendered group's bounds. |

By default, successive samples estimate the centroid's velocity and rigid
rotation from three spread-out guide points. The first sample has zero
velocity. Collinear or single-point geometry cannot reveal all rotation;
provide `motion` for those cases. This estimator is for approximately rigid
motion. Deforming bodies should supply their intended rigid handoff motion.

Use `sync(dt)` once after external animation when driving this system without
its stage update. `sync()` refreshes dynamic bounds without estimating a new
velocity. Static groups require `static: false` or explicit recreation when
edited. Release always reads their current positions and covariance, including
an animated pose, rather than substituting their rest geometry.

A fragment inherits the velocity at its center, including `w × offset`.
Additional linear and off-center angular impulses apply before handoff.
Optional scatter has its mass-weighted mean removed, preserving net linear
momentum. The existing rubble solver uses sampled contacts and scalar inertia;
this is interactive scene physics rather than a structural stress solver.

## Structural support

`links` is an array of distinct, undirected `[groupA, groupB]` connections.
Providing links enables support checking unless `support: false` is specified.
Every supported group must initially have a path to an anchor. Destroying one
of several supports leaves the remaining paths intact. Once its final path is
lost, a group releases with its own geometry and motion in the same operation.

`sever(a, b)` removes one connection and releases newly unsupported groups.
Calling it again is harmless. Reset restores all links. `release` events name
whether a group failed directly or through loss of support. Anchors are logical
supports, not constraints on an already released body.

## Handoffs, damage and queries

- `release(id, options)` explicitly detaches a group and its unsupported
  dependents. Returns the spawned bodies/chunks. A second release returns `[]`.
  Options override `v`, `w`, `origin`, `mode` and `fragmentSize`, and can add
  `impulse`, its world application point `p`, `scatter` speed, or debris `life`.
- `impact({ p, impulse, radius: 0, group? })` accumulates damage and breaks
  groups above their strength threshold. Without `group`, it tests actual
  collision samples and applies linear radial falloff. An explicit group
  targets that binding directly, useful for collision integrations.
  Returns `{ hits, released, pieces }`, plus `blocked: true` if the piece
  budget prevents a safe handoff. Blocked impacts leave damage unchanged.
- `sweep(from, to, radius, { environment: false, dynamic: false, exclude })`
  returns the first contact or `null`, without applying damage. The contact
  contains `group`, `fraction`, center position `center`, surface point `p`,
  and outward `normal`. Dynamic contacts also include a `body` handle.
- `inspect(id)` returns name, state, damage, mass, center, estimated motion,
  owned sample count and current piece count. `intact(id)` is a cheap guard
  for external animation writers: only redraw the group while it is intact.
- `stats` reports group, intact, piece and projectile counts, physics time,
  and pending events. `rubble`, `debris` and `projectiles` expose owned runtime
  handles for host visuals or effects. Do not add the owned solvers separately
  to the stage or update them a second time.

The default collision proxies are spheres enclosing each splat covariance.
Group bounds provide broad-phase rejection; narrow-phase tests preserve gaps
between samples. An authored group `solid` replaces that narrow phase with SDF
tracing. Optional environment tracing uses the system `solid` field, defaulting
to `y - ground(x, z)`. SDF tracing is bounded and requires finite signed distances.

## Cannonballs, catapults and secondary impacts

`launch({ p, v, radius: 0.2, mass: 1, life: 12, restitution: 0.15, id? })`
creates a physics projectile and returns its live handle. The binding does not
allocate its visual. Sample its world `p` in your splat or sprite renderer.
`active` becomes false when it expires or is reset. IDs must be unique among
live projectiles. A projectile uses swept contacts against intact structures,
existing rubble and the environment. It exchanges linear/angular impulses,
wakes sleeping rubble, and can cross several contacts within a physics step.

Catapults use the same API with an arcing launch velocity. For a target `q`
and chosen flight time `t`, start with `(q - p) / t` and add `gravity * t / 2`
to its vertical velocity. The example compensates for the solver's fixed-step
gravity integration as well. No per-scene impact detection is needed.

Released rubble can strike intact groups and start secondary collapses.
Temporary debris remains cosmetic and does not act as another rigid projectile.
The binding disables rubble's legacy automatic landing fracture, so only the
configured structural partitions release and ownership remains bounded.

`drainEvents()` returns and removes ordered records. Event kinds include
`impact`, `release`, `sever`, `projectile-hit`, `piece-hit` and `budget-blocked`.
Use these for sound, dust, fire, score or other simulation responses. The
binding dispatches no callbacks during physics mutation. Events carry local
physics `time`; reset starts this clock at zero.

## Budgets, stepping and reset

The defaults are 128 pieces, 64 projectiles, 250,000 bound splats, 1,024 event
records and 12 rubble contact points per body. Override with `maxPieces`,
`maxProjectiles`, `maxSplats`, `maxEvents` and `points`. Maximum group count is
4,096 and maximum support-link count is 16,384.

Fragmentation coarsens to fit the piece budget before any ownership changes.
When the budget can accommodate all groups, it reserves at least one body for
each remaining structure. Explicit release/sever throws before mutation if
even whole-group pieces cannot fit. Impact-driven releases instead report
`blocked`, retain the collider and allow physics to continue. Projectile budget
overflow rejects the launch. The bounded event queue retains the newest records.

Physics advances at 120 Hz with a retained accumulator. `update(dt)` accepts
0–0.25 seconds; a host driving it directly should subdivide longer gaps.
The ordinary stage already clamps frame deltas. Render rates do not change the
fixed-step projectile/collapse result for static geometry and identical inputs.

`reset()` cancels projectiles, empties only this binding's solvers, clears damage
and events, restores every owned 16-float splat row, restores rig `free` flags,
reinstates links, and marks affected upload rows dirty. Unrelated particles,
physics systems and splats remain untouched. The snapshot is the geometry at
binding creation. External animation resumes when the caller redraws its pose.

`dispose()` resets, removes the binding from its stage and frees its ownership
reservation. It is safe to call twice. Create another binding to use those
splats again. Reset does not seek a host timeline or automatically replay
stateful effects after a backward scrub; the caller owns replay and scheduling.

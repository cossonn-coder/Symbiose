# Headless worlds

Ink Studio can advance a declarative world, apply timed actions, inspect the
result, and replay or compare runs. A scene uses the same query descriptors
from JavaScript and the CLI. Each query reads one published revision.

For editable SDF-biome scenes, the
[biome revision API](procedural.md#biome-revisions) stages terrain, water,
navigation and splats together. Its packed render world can also be read
with `K.world.query.fromScene`.

[Place travel and portals](portals.md) connect separate authored places with
prepared destination views, actor and camera handoffs, and fade-based travel.

## Run and compare a watershed

Save the starting checkpoint after the reservoir has settled.

```sh
ink-studio sim run examples/world-watershed.json --ticks 30 --checkpoint filled.json
```

Save an action list as `spillway.json`.

```json
[
  {
    "tick": 31,
    "action": "river/bed",
    "args": {
      "bounds": {"min": [-1.55, -0.75], "max": [-0.55, 0.75]},
      "height": -0.25
    }
  }
]
```

Run both branches to the same tick. The baseline remains dry at the bridge.
The edited bed releases the reservoir and the downstream probe reports flow.

```sh
ink-studio sim fork filled.json --ticks 120 --record hold.run.json
ink-studio sim fork filled.json --ticks 120 --actions spillway.json --record lower.run.json
ink-studio probe lower.run.json --field river/water --entity footbridge --json
ink-studio sim diff hold.run.json lower.run.json --field river/depth --entity footbridge
ink-studio sim replay lower.run.json
ink-studio sim render lower.run.json --out lowered.png
```

In a simulation render, put [surface color curves](surface-materials.md#color-curves-on-surfaces)
in `visual.terrainSurface` or `entities.<id>.visual.surface`. Field sources
sample the rendered checkpoint or tick. Set `visual.look.colorCurves` for a
scene-wide palette treatment, and pass `--color-curves off` to preview the
scene with those layers disabled.

`sim resume` and `sim fork` both start a new process from a checkpoint. Keep
their output paths distinct to retain both branches. A run file contains its
starting checkpoint, added commands, and ending checkpoint. Replay verifies the
result against the recorded ending state. Sign differences between positive
and negative zero follow JSON numeric equality. `sim reset` on a recording
returns to its starting checkpoint. `--ticks` selects an absolute tick,
`--steps` advances relative to the current tick, and `--t` converts seconds
to a tick using the scene timestep. Use one of these per invocation.

`sim sweep <world> <cases.json>` runs an array of cases. Each entry accepts
`id`, `seed`, `edits`, `ticks`, `actions`, `probes`, and `assert`.
For sweeps from a checkpoint, use actions to vary the branches. A probe entry
contains `field`, optional `at`, and optional `args`.

When a case supplies `look`, the sweep renders every case from the same
simulation snapshot. [Look cases and color metrics](pixel-look.md#compare-looks-on-a-fixed-view) use the same format as `compare`.

`--assert checks.json` accepts an array of field checks with `field`, optional
`at`, optional `args`, optional expected `status` (default `ok`), and a
`when` condition. Use `tick` to check one earlier frame or `byTick` to allow
the condition to become true by a deadline. The default checks the final frame.
`--profile` reports per-system calls, total milliseconds and peak tick time.
A check may use `{"profile":"river","metric":"calls","max":90}`. Failed
assertions return exit code 2.

## Query a revision

```sh
ink-studio inspect lower.run.json
ink-studio inspect lower.run.json --near 2,0,0 --radius 2
ink-studio probe lower.run.json --field world/position --entity footbridge --socket north
ink-studio trace lower.run.json river/flow --at 1,0,0 --args '{"steps":30}'
ink-studio probe lower.run.json --field world/history --args '{"where":{"path":["kind"],"value":"bed-edit"}}'
```

Fields and traces are named `system/name`. Use the short name when only one
system exports it. A probe reports `ok`, `dry`, `outside`, `missing`, or
`unavailable` as appropriate. Runtime scene files, checkpoints and run files use
the same field registry. The existing diorama loader also adapts published water
volumes, material sandboxes and exposed traversal graphs for inspection. A scene
can supply its own query adapter using `world.query(world, time)`.

Use `field <file> <name> --spec samples.json` with one of these sample specs.

```json
{"grid":{"min":[-5,0,-1],"max":[5,0,1],"counts":[21,1,5]}}
```

```json
{"line":{"from":[-5,0,0],"to":[5,0,0],"count":41}}
```

```json
{"ticks":[10,20,30],"at":{"entity":"footbridge"}}
```

An explicit `points` array is also supported. A time series may carry a
`spatial` sample spec to export each frame on the same grid. Grid rows are
X-fastest. The field descriptor supplies units. Conditions accept `path` as a
path array or JSON pointer, `op` as one of `eq`, `ne`, `exists`, `lt`,
`lte`, `gt`, `gte`, or `in`, and `value` where needed. Combine conditions
with `all`, `any`, or `not`.

## Typed spatial fields

The `fields` system publishes numeric scalars (`number`), vectors
(`vec2` and `vec3`), and named categories (`category`). Each field
can declare `units`, a coordinate `space`, domain `axes`, and `bounds`.
Existing scalar definitions with `default` and `regions` still work.

- Probe points and field export positions are XYZ in world space. Use
  `axes` to select the coordinates the field uses, such as `xz` for a
  ground map or `y` for a height profile. Domain and region bounds use
  those axes in order.
- The default coordinate space is `"world"`. Use
  `{"entity":"station","socket":"vane"}` to sample relative to the live
  pose of an entity or socket. `vec3` values authored in that frame are
  rotated into world space on read. `vec2` values use world space, with
  `components` identifying their axes (`xz` by default).
- A field can read its default value, winning region, or an authored grid.
  Grid values are a flat array ordered by the first axis fastest.
  Grid nodes span the declared bounds, and an axis with one node is
  constant along that axis. Numeric grids default to linear interpolation.
  Set `"sampling":"nearest"` for nearest-node reads. Categories declare
  their allowed strings and use nearest-node or region sampling.
- Regions override the underlying default or grid, with the last match
  winning. Use `system/set` with `{field, region}` to append a region at a
  scheduled tick. State and checkpoints carry those edits.
- Bounds include both ends by default. A field can declare
  `"boundary":"half-open"` to exclude the upper end. An out-of-domain
  probe returns `outside`. The built-in water depth, bed, and XZ flow
  use the same contract with half-open cell bounds.

`inspect` exposes the type, units, and spatial contract. Add `--explain`
to `probe` or `field` to get the source of each sample, including its
grid nodes and weights, the winning region, or the solver cell. The
report includes the revision tick and the position in both coordinate
spaces. JavaScript callers pass `{explain:true}` as the probe's third
argument.

The [harbor station world](../examples/world-spatial-fields.json) uses
one wind field for a raft's sail, a flag, and smoke. It also defines a
temperature gradient and a shelter field attached to a socket.

```sh
ink-studio probe examples/world-spatial-fields.json --field weather/wind --entity brazier --explain
ink-studio probe examples/world-spatial-fields.json --field weather/cover --entity station --socket vane --explain
ink-studio probe examples/world-spatial-fields.json --field weather/temperature --at 0,2,0
ink-studio field examples/world-spatial-fields.json weather/wind --spec examples/spatial-wind-transect.json --explain
ink-studio probe examples/world-spatial-fields.json --field weather/wind --entity brazier --ticks 60 --explain
ink-studio render examples/spatial-field-wind.js --params '{"tick":120}' --t 1.55 --out harbor.png
```

A query can bind a reusable XYZ sampler to its snapshot. Supply the
consumer's expected type and units to validate the binding. An optional
typed fallback is returned when a sample is unavailable.

```js
const wind = run.query().sampler('weather/wind', {
  type: 'vec3', units: 'world/s', fallback: [0, 0, 0]
});
const velocity = wind(0.4, 0.55, 0.35);
```

Pass the same callable directly as an XPBD wind function, adapt it to
the particle flow callback, or use its velocity to step a seed
trajectory. Bind from the current query when a simulation advances.
In a mechanics system, a force of kind `sail` samples a vector wind
field, takes the apparent wind along the sail's local `axis`, and
applies a two-sided pressure force. Set `field` to the field name and
`units` to the expected velocity unit (default `world/s`).

## Conservative transfers between systems

Systems can expose named accounts. A transfer debits one account and
credits another with the same accepted quantity. A request names two
`system/account` endpoints and an amount. Both endpoints must agree
on the resource, unit string, and quantity type. Accounts support
continuous numbers, safe integers for countable items, and signed
`vec2` or `vec3` quantities such as momentum.

- `store` defines accounts with `resource`, `units`, `initial`, and
  optional `type`, `min`, and `max`. Numeric accounts default to a
  zero lower bound. Vector accounts default to signed, unbounded
  components. Specify vector bounds per component, using `null` for
  unbounded components.
- `exchange` defines named links with `from`, `to`, and either an
  `amount` per tick or a `rate` per second. A Boolean input named
  after each link controls whether it submits requests. It starts
  enabled unless the link declares `"enabled":false`.
- A `water` system can expose named cells with
  `"accounts":{"outlet":[0.5,0.5]}`. Each account reads and writes a
  cell's actual water volume in `world^3`. The basin's mass probe counts
  account transfers in `received` and `sent`. Incoming water starts
  at rest, and withdrawing volume preserves the remaining water's
  velocity. The solver can then evolve the basin normally.

The default `partial` mode moves as much as the source can supply and
the destination can hold. Use `"mode":"exact"` to require the whole
amount. A clipped vector keeps its direction. If a move would round
away at either endpoint, both balances stay intact and the receipt
reports the precision limit.

The runtime applies ordinary commands, then settles scheduled
`world/transfer` requests in command order. System-generated requests
follow in system ID order and preserve each producer's own order.
Each request sees the balances left by earlier requests in that tick.
Producers all read the same pre-transfer snapshot and the input
values available at the start of the tick. Solvers step from the
settled snapshot. A failed endpoint write aborts the tick, including
any earlier transfers. Checkpoints and replay preserve receipts.

The [transfer station](../examples/world-transfers.json) requests
five cubic world units from a shallow-water basin. The cistern has
room for two, so the basin drops from eight to six while the tank
rises from eight to ten. The next pump request moves zero. The same
scene demonstrates capped heat storage, exact and partial integer
shipments, and signed vector transfers.

```sh
ink-studio inspect examples/world-transfers.json
ink-studio probe examples/world-transfers.json --ticks 1 --field world/transfers
ink-studio probe examples/world-transfers.json --ticks 1 --field basin/mass
ink-studio probe examples/world-transfers.json --ticks 2 --field world/account --args '{"account":"cistern/water"}'
ink-studio render examples/conservative-transfer.js --out transfer-station.png
```

`world/transfers` reports the latest tick's receipts with requested
and applied quantities, status, and limiting endpoint. The runtime
also emits a `transfer` event for each receipt, so `world/history` can
filter earlier transfers even after the run advances.

A custom system exposes the same interface through its factory. An
account's `read` returns its balance and current bounds. Its `write`
receives the new absolute balance and returns the updated JSON state.
Both functions operate on the supplied snapshot. A writer updates
only its account and any associated bookkeeping.

```js
accounts: {
  heat: {
    resource: 'thermal-energy',
    units: 'J',
    type: 'number',
    read: state => ({balance: state.joules, max: state.capacity}),
    write: (state, balance) => ({...state, joules: balance})
  }
}
```

To drive requests from a model, implement
`requestTransfers(state, context)` and return an array of
`{from, to, amount, mode?, id?}` objects. Use `checkTransfers(validate)`
to validate fixed endpoint references during world validation.

## Spatial dependency reports

Registered simulation systems can declare the fields and regions
they read and write. A declaration can name a whole field or a
bounded region. Use `axes` for lower-dimensional domains such as
`xz` on a terrain grid. A read can add `padding` for nearby samples.

```js
dependencies: {
  reads: [{field: 'river/bed', bounds: {axes: 'xz', min: [0, 0], max: [8, 4]}, padding: 0.25}],
  writes: ['route-cost']
}
```

An action or step calls `ctx.spatial.write(field, bounds, reason)`
after changing a declared field. Use `null` for a whole-field
change. Short write names belong to the system publishing them.
Action writes are visible to readers on the same tick. Step writes
become visible on the next tick alongside the new state, and
checkpoints preserve any pending writes.

A consumer can call `ctx.spatial.changes(bounds)` to get the
overlapping writes that match its read declaration. Call
`ctx.spatial.rebuilt(kind, detail, bounds)` after doing the work.
The report lists affected readers independently of the recorded
rebuilds. Built-in field region edits and water bed edits publish
spatial writes. Active agents replan when a reported change overlaps
their remaining route. Routine simulation and unreported changes
still use each solver's normal update rules.

```sh
ink-studio sim dependencies examples/world-watershed.json --ticks 31 \
  --actions examples/spatial-bed-edit.json --out runtime-dependencies.json
ink-studio sim dependencies examples/spatial-rebuild.js --out retained-dependencies.json
```

The runtime report includes the changed field and bounds, affected
systems, and measured work such as the number of water bed cells
sampled and changed. A recorded run is played from its starting
checkpoint to recover this timeline. A retained driver exports
`dependencies(kit)` and supplies its own edit sequence.

The retained biome pipeline uses the same tracker for terrain spans,
connected flooding, water boundaries, traversal links, and splat
chunks. The report links recorded work to its input changes using
`because` IDs. Flooding can publish changes beyond the edited region.
Painting a material can rebuild nearby splats using retained surface
geometry. Physical spans and route links can stay cached. Ordinary
`sim render` still assembles a fresh headless render scene.

## Multi-rate simulation

Declare a system's `schedule` on the system record. The world's `dt`
still defines command times, scenario evaluation, and checkpoint
ticks.

| Schedule | Solver cadence |
| --- | --- |
| Omitted | One step per world tick with `ctx.dt = world.dt`. |
| `{"substeps":4}` | Four evenly spaced steps per tick, each with a quarter of the world timestep. |
| `{"every":4}` | One step on ticks 4, 8, 12, and so on, with four world timesteps of elapsed time. |

The runtime aligns fast solvers on an integer grid. It limits the
combined subdivision to 64 and the slow interval to 3600 ticks.
Solvers due at the same boundary read the same state snapshot.
A stateful publication is visible at the following boundary.
Combinational connections can deliver values at a shared boundary
in dependency order.

A connection's `sample` sets the crossing rule.

| Rule | Behavior |
| --- | --- |
| `hold` | Read the most recent available value when the consumer runs. This is the default for level signals. |
| `average` | Time-weight the held number or vector over the consumer's interval. The initial output covers the interval before the first publication. |
| `sum` | Add each published number or vector increment once. Consume the accumulated total on the next solver call. |
| `events` | Queue event entries in publication order and deliver them once. Event connections use this rule when multi-rate scheduling is active. |

Connection delays are measured in world ticks. Delayed levels hold
the selected tick's final value. Delayed sums and events carry all
publications from the selected tick as a batch. Manual numeric inputs
hold their latest command value. Manual events accumulate in command
order and wait for the scheduled consumer. Initial outputs seed held
levels, while sums and event wires collect solver publications.

`ctx.time` is the end of the current solver step. `ctx.baseDt`,
`ctx.every`, `ctx.substep`, and `ctx.substeps` describe the schedule
when multi-rate mode is active. `ctx.tick` is the containing world
tick. Peer state and field queries read the snapshot at the start
of the current boundary. Fast steps use distinct deterministic
random streams. Commands and conservative transfer settlement run
once at the world tick boundary. Spatial writes emitted by a step
become visible on the next world tick. Slow spatial readers keep
matching notices until their next step.

Checkpoints preserve pending signal samples and spatial notices.
Only completed world ticks publish state. If a substep fails, the
run retains its previous checkpoint, inputs, and pending commands.
Profile `calls` counts actual scheduled solver calls. `maxMs` is
the largest total time spent on that system in one world tick.

The [multi-rate yard](../examples/world-multi-rate.json) runs a
native cart at 80 Hz, weather controls at 20 Hz, and terrain wear
at 5 Hz. Set `contactEvents:true` on mechanics and wear to connect
their `contacts` ports across rates. The wear system applies a
batch of wheel contacts at its update boundary. The example also
shows a slow temperature average alongside a held temperature
signal for the heater.

```sh
ink-studio sim run examples/world-multi-rate.json --ticks 4 --profile --record yard.run.json
ink-studio probe yard.run.json --field world/signal --args '{"port":"trail/contacts"}'
ink-studio sim replay yard.run.json
```

## Causal traces

Enable `"causality": true` on a world to record causal evidence during
simulation. `"causality": {"limit": 4096}` sets the retained node count.
The default is 2048 and the maximum is 20000. Causal recording has its
own retention and captures emitted events even if the world timeline
filters them out.

The [mill example](../examples/world-causal-mill.json) records a pump
load of 12 at tick 3. The breaker trips at its threshold of 8 on tick 4,
the motor sets drive to zero on tick 5, and the shaft stops on tick 6.

```sh
ink-studio sim run examples/world-causal-mill.json --ticks 8 --record mill.run.json
ink-studio trace mill.run.json world/cause --entity mill-wheel --args '{"kind":"machine-stop","system":"mill"}'
ink-studio trace mill.run.json world/cause --args '{"event":"6.0"}'
ink-studio trace mill.run.json world/cause --args '{"port":"mill/speed.shaft","atTick":5}'
ink-studio sim replay mill.run.json
```

Select a trace root by causal node `id`, timeline `event` ID, signal
`port`, or event or decision `kind`. The port and kind lookups choose
the latest matching node at or before `atTick`. Filter by `system` or
entity where applicable. A port lookup prefers its output when both
directions exist. Set `"direction":"input"` to trace the input sample.
Edges point from effects to their recorded causes. The report gives
each node's tick, readings and details. A
`partial` status and `gaps` identify missing evidence when retention,
`maxDepth`, or the returned node `limit` cuts off a branch.

Signal traces carry the actual samples a solver used, including delayed
samples and the publications behind multi-rate averages, sums, and
event batches. An output or event may be attributed to a declared
decision, the current command, observed solver inputs, or a held
publication. The `basis` identifies that attribution. Observed inputs
establish what was available to the solver. Systems can record exactly
which evidence contributed to a decision. Checkpoints and run recordings
preserve causal evidence through resume, replay, and forks.

In an opted-in world, custom systems can use `ctx.causal.input(key)`
and `ctx.causal.previous(key)` to reference an input sample or previous
output. `ctx.causal.read(field, at, args)` returns the query `result`
and a `cause` ID, recording the measured value and available provenance.
Call `ctx.causal.record(kind, detail, {inputs, causes, outputs})` to
record a decision with its selected input keys, evidence IDs, and output
keys. Pass the returned decision ID in `ctx.emit(kind, detail, [id])`
to explain a specific event.

## Physical material assets

A versioned asset pack can carry a `materials` list alongside families
and looks. Give each material an ID such as `earthworks/clay`. Use
`world/material` to resolve its pack revision and effective properties
for a specified wetness. Most numeric properties accept a constant or
`{"dry": 0.82, "wet": 0.10}` to interpolate over the moisture range.

| Property | What uses it |
| --- | --- |
| `friction` | Mechanics uses the coefficient to reduce sliding and cap driven wheel traction. If both contacting materials supply a coefficient, their geometric mean is used. |
| `permeability` | Potential water loss through the bed in world units per second. Surface water caps the loss by available water and reports it in its drainage ledger. |
| `thermal.heatCapacity`, `thermal.conductance`, `dryingRate` | Lumped heat capacity in J/K and conductance in W/K use the same reference area. Each cell approaches its ambient temperature at their ratio. The drying rate is in inverse seconds at 20 °C. Dry cells lose moisture faster as their temperature rises. |
| `erosion.threshold`, `erosion.rate` | For cells covered by water, the bed lowers at `rate × (flow speed − threshold)` above the threshold in world units per second. Each water system exposes the removed bed volume in its `eroded` field. |
| `fracture.energy`, `fracture.parts` | The mechanics fracture action checks supplied impact energy against the threshold. Fragments inherit the material. `parts` is the default number of pieces and can be overridden by the action. |
| `fatigue.endurance`, `fatigue.life`, `fatigue.exponent` | Stress amplitude threshold, reference life in cycles and the stress-to-life exponent for structural bodies and worn joints. |
| `plastic.yield`, `plastic.creep`, `plastic.limit` | Yield stress, creep rate above yield and a cap on permanent curvature over the normalized beam span. |
| `sounds` | Names the `step`, `roll`, `impact` and `fracture` cues. Foot and wheel contacts carry cue IDs. Impacts and fractures expose their cues in the event record for a host to play. |
| `contactEffects` | Scales ruts, spray, positional sound and camera shake from one measured [material contact](contact-effects.md). |
| `appearance.dry`, `appearance.wet` | Equal-length hex color ramps mapped to the scene palette. The ground renderer interpolates them from the same moisture field. |

Bind `materialAsset` and optional `materialWetness` to an entity or
mechanics body. A body binding takes precedence over its entity binding.
A `fracture` command without energy directly edits the body.

For terrain, declare a `materials` system with an XZ `grid` containing
`width`, `height`, optional `cell` and optional `origin`. Set the default
`material`, initial `wetness` and `temperature`, and optional bounded
`regions`. A region covers cells whose centers lie inside its bounds.
Use `airTemperature` or a numeric `ambientField` in `degC`. Point
`water` at a water-column field to wet submerged soil. The wetness
field measures surface condition on a scale from zero to one.

Use the same `soil/surface` field as `surface` in water and mechanics
config, and as `visual.fields.surface` for rendering. The system also
exposes `soil/material`, `soil/wetness`, and `soil/temperature` as typed
spatial fields. Water publishes erosion through its existing bed field
and spatial dependency reports. Checkpoints save soil conditions and
the original asset packs for replay.

In the [clay yard](../examples/world-physical-materials.json), both
lanes use the same [physical material pack](../examples/physical-materials.pack.json).
Their moisture changes grip and color. An impact energy of 5 breaks
the dry clay and leaves the wet clay intact.

```sh
ink-studio sim run examples/world-physical-materials.json --asset-pack examples/physical-materials.pack.json --ticks 22 --record yard.run.json
ink-studio probe yard.run.json --field soil/surface --at -1.15,0,-2 --explain
ink-studio probe yard.run.json --field world/material --args '{"id":"earthworks/clay","wetness":0.5}'
ink-studio sim render yard.run.json --colored --out clay-yard.png
```

## Live cuts, fills, and material layers

A `volume` system defines a bounded editable solid. Set `bounds`, align
their endpoints to `cell`, and choose a `chunkCells` size. Its `initial`
array takes the same shape arguments as the live actions, with an
`op` field for each entry. Entries are applied in order. Material IDs
can name an inline RGB ramp or a physical material in an installed pack.

| Action | Effect |
| --- | --- |
| `quarry/cut` | Removes the part of the solid inside the brush. Newly exposed surfaces take the material from the surviving interior. |
| `quarry/fill` | Adds solid and assigns the supplied `material` to the new volume. Existing solid retains its material. |
| `quarry/layer` | Changes the `material` of existing solid inside the brush. Geometry and water topology keep their cached data. |

Every action takes a `shape`. A box uses `at`, `half`, and optional
`round`. A sphere uses `at` and `radius`. A capsule uses `from`,
`to`, and `radius`. Brushes can cross chunk seams and are clipped to
the editable domain. Use a cell size fine enough to represent the
features you want to see or flood.

`clearance`, `support`, and `height` expose the current collision
shape. Existing navigation and movement systems can bind those fields.
`material` samples the surviving solid and `segment` traces a swept
sphere against the current clearance field. Add `sources` with a
point and water level to fill connected open spans at a fixed head.
`medium` and `water` query that occupancy. The fixed-head source supplies
newly connected passages and stops supplying disconnected ones.

Set `visual.volume` to the system ID to render its retained splats and
water. Edits rebuild intersecting chunks plus the sampling halo.
Unaffected chunk payloads keep their identity. `work` reports the last
edit's rebuilt and reused chunks and the separate water work. Spatial
dependency reports include water changes beyond the brush where a
connection opens or closes. Checkpoints save the ordered edits and
reconstruct the same solid, material and water state on restore.

The [spillway quarry](../examples/world-live-volumes.json) opens a
copper-lined passage at tick 2, applies a limestone layer at tick 4,
and closes the passage with a fill at tick 6.

```sh
ink-studio sim run examples/world-live-volumes.json --ticks 2 --record quarry.run.json
ink-studio probe quarry.run.json --field quarry/material --at 0,0.4,0
ink-studio probe quarry.run.json --field quarry/work
ink-studio trace quarry.run.json quarry/segment --at -3.1,1,0 --args '{"to":[3.1,1,0],"radius":0.12}'
ink-studio sim render quarry.run.json --colored --out quarry.png
```

## Surface state that follows geometry

Add `surfaceState` to a mechanics body to attach state to its original
faces. Face keys are `-x`, `+x`, `-y`, `+y`, `-z`, and `+z`. Each
entry in `surfaceState.faces` is an ordered array of stamps in unit UV.
The default channels are `paint` in RGB, `heat` in degrees Celsius, and
`grime`, `scar`, and `wear` on a scale from zero to one. Mechanics
`surfaceChannels` can add named color or scalar channels with bounds,
defaults, and units.

Use `rig/surface-stamp` with `body`, `face`, and `stamp` at a scheduled
tick. A stamp selects a `channel`, a `brush`, and a `value` for `set`
or scalar `add`. `clear` restores the channel's default. `strength`
scales the coverage. Use a `rect` brush with `min` and `max`, a `bitmap`
with those bounds and rows of dots and hashes, or a `stroke` with
UV `points`, `width`, and optional `softness` measured in the rest chart.
On a fragment, a stamp uses that face's local UV and affects only the
chosen piece.

`rig/reshape` changes the body's XYZ `half` sizes while keeping its
chart coordinates. When `rig/fracture` splits a body, its pieces keep
the correct regions of the original faces. New faces start at the
channel defaults and can use `surfaceState.fresh.material` and a
`surfaceState.fresh.ramp` of palette indices. The renderer retains the
original surface ID on the exterior splats, including after a rebake.

Probe `rig/surface-state` by body ID and face UV, or pass a world-space point
and body ID to resolve the local face and original UV. `rig/surface-charts`
returns the atlas data. Checkpoints save the chart windows and stamps.
For a custom mesh, use [surface chart correspondences](procedural.md#surface-state-through-remeshing).

The [split sign](../examples/world-surface-state.json) keeps the same
lettering through a reshape and fracture. Each broken edge exposes a
separate, unmarked wood surface.

```sh
ink-studio sim run examples/world-surface-state.json --ticks 11 --record sign.run.json
ink-studio probe sign.run.json --field rig/surface-state --args '{"body":"sign.0","face":"+z","uv":[0.44,0.5]}'
ink-studio probe sign.run.json --field rig/surface-state --args '{"body":"sign.0","face":"+x","uv":[0.5,0.5]}'
ink-studio sim render sign.run.json --colored --out sign.png
```

## Constraint-based construction

A `construction` system solves placements for named points and their
sockets. A point has a preferred `position` and optional `sockets` with
XYZ offsets in world-axis directions. Constraint references take a
point name or `point/socket`. The solver keeps each preferred coordinate
as close as the hard bounds allow, in sorted point-ID order.

| Constraint | Arguments and result |
| --- | --- |
| `pin` | `point` and `position` fix a point or socket in XYZ. Override the position by constraint ID when refitting. |
| `align` | `a` and `b` coincide, or `b` stays at the optional XYZ `offset` from `a`. |
| `level` | The named `points` share the same world Y. |
| `range` | Bounds the directional difference from `a` to `b` along `axis` using `min`, `max`, or both. |
| `opening` | Requires a minimum `width` along X or Z and a minimum `height` along Y. Each uses `a`, `b`, and `min`. Width also uses `axis`. Optional `passage: {a, b}` checks that a level corridor with those dimensions clears the fitted parts. |

Attach `blocks` to references with `at`, `offset`, and `half`. Each
entry in `spans` stretches a box between `a` and `b` using its
`width`, `depth`, and optional `rise` and `lateral` offsets. Render
the resulting `bodies` field and use `support` and `clearance` for
collision and navigation. `visual.fields.bodies` accepts a single field
or a list of fields when a scene includes more than one body provider.

`bridge/refit` accepts a `pins` map and publishes the layout when the
constraints and passage checks pass. A failed attempt leaves the last
accepted layout in place. `bridge/fit` reports the last attempt or
previews a specified `pins` map without publishing it. A
`conflict` includes a contradictory chain of authored constraints
for each affected axis. The bounds in the chain sum to a negative
number even though the coordinate differences around a closed cycle
sum to zero. A `blocked` passage reports the constraint ID and the
parts obstructing its corridor. Use `bridge/layout` for the current
published parts and sockets.

The [canal bridge](../examples/world-construction-bridge.json) refits
at tick 2 and rejects a height mismatch, an overlong span, and an
obstructed passage at later ticks.

```sh
ink-studio sim run examples/world-construction-bridge.json --ticks 8 --record bridge.run.json
ink-studio probe bridge.run.json --field bridge/layout
ink-studio probe bridge.run.json --field bridge/fit --args '{"pins":{"east-anchor":[6,1.43,0]}}'
ink-studio sim render bridge.run.json --colored --out bridge.png
```

JavaScript callers can also use
`KIT.procedural.construct.constraints.compile(points, constraints)`
and call `solve(pins)` to fit the coordinate constraints.

## Author a world

A manifest has `format: "ink-studio/world"`, `version: 1`, a stable `id`,
`seed`, `dt`, and tables of `entities` and `systems`. A system record
declares a `kind`, a `config`, and optionally a [solver schedule](#multi-rate-simulation). Optional sections include `connections`,
`prefabs`, `assetPacks`, `commands`, `history`, `causality`, `metadata` and
`scenario`. See [the watershed](../examples/world-watershed.json) and
[the quarry crossing](../examples/world-crossing.json) for working manifests.

`scene apply <world> <edits>` applies an ordered array of `set`, `remove`,
`merge` and `test` operations atomically. Paths accept arrays or JSON
pointers. Existing branches are shared until changed. `--dry-run` reports
changed paths and the targets affected by look edits. World manifests
and JSON dioramas also accept [`bind-look` edits](pixel-look.md#apply-look-bindings-with-scene-patches).
`--out` writes the validated result. The path-based operations also
accept retained authoring documents and JSON dioramas. `validate` checks a
world directly, or accepts `--world manifest.json --kind edits|actions` to
check a separate file against a world.

Entity positions are relative to their parent or host socket when attached.
Use `scene stamp <world> <prefab> --as id` to instantiate a reusable assembly.
The optional JSON `--args` accepts `position`, `params`, and local edit
`overrides`. In prefab declarations, `{"$param":"name"}` reads a parameter,
`{"$local":"id"}` refers to an internal object or system, and
`{"$port":"system/output"}` refers to a local port. Stamp rewrites internal
connections and exposes public ports as `assembly/port`. Prefabs can require
asset-pack IDs or exact revisions. `scene remix` modifies a definition and
`scene capture` saves a placed, edited assembly under a new prefab ID.

`world/input` drives an unconnected typed input, `world/patch` edits live
entity and metadata records, `world/event` emits a named event, and
`world/transfer` queues a conservative account transfer. Each
scheduled command has a positive integer `tick`, an `action`, and an
optional `args` object. Commands scheduled for one tick run in order. All
stepping systems read a common snapshot after that tick's commands. A
combinational control block can pass its result in the same tick. Stateful
outputs feed the next tick. Set a connection's `delay` to queue its signal
for a fixed number of ticks. The validator rejects instantaneous cycles.

A scenario accepts an initial patch in `start`, `commands`, an `allow` list
for external actions, an `until` tick, and ordered `rules` of kinds
`score`, `metric`, `win` and `fail`. A rule can probe a field and apply a
condition to its value. Run with `--scenario` to stop at an outcome. The quarry
example awards points when the sheep crosses an opening and ends when it
reaches the feeder.

## Built-in systems

| Kind | State, queries and actions |
| --- | --- |
| `fields` | Typed spatial fields with defaults, grids, regions and a `set` action. |
| `materials` | Grid of versioned surface materials with local moisture, temperature, coefficients, and appearance. |
| `volume` | Editable 3D solid with material layers, collision and support queries, fixed-head water, retained splats, and optional local relighting. |
| `construction` | Constraint-fitted points, sockets, blocks, spans, and passage clearance with live refits and conflict reports. |
| `control` | Typed arithmetic, thresholds, selection, binary logic, pulses, latches, timers and hysteresis. |
| [`puzzle`](puzzles.md) | Ordered switches, timed windows, reusable recipes, blocker traces and bounded solution witnesses. |
| `store` | Bounded numeric, integer, or vector accounts with named resources and units. |
| `exchange` | Enabled links that request a fixed amount per tick or a rate per second. |
| `logistics` | Resource stocks, atomic recipes, scheduled shipments, conservative accounting, and upstream shortage traces. |
| `water` | Bounded XZ shallow water with live bed edits, fractional face openings, conservative pump transfer, and optional sediment transport, deposition and gate silting. An `obstacle` field may supply signed solid clearance. |
| `mechanics` | Boxes, capsules and convex compounds with swept contact and shared clearance and support queries. Fixed and powered mounts, transmission ratios and stall reports, physical separation, configurable box fracture, wheel traction, buoyancy, thrust and sail forces. |
| `deformables` | Checkpointed XPBD cloth and rope with scene attachments, terrain and solid contact, loads, tears, support queries and rain collection. |
| `routed-links` | Socket-to-socket cables, hoses and belt loops with guide points, slack, tension, break limits, typed signals, torque transmission and conservative transfers. |
| `navigation` | Bounded walking, swimming or flying route traces. Ground search can take depth, clearance and wear into account. Hosts can also expose the volumetric traversal graph. |
| `habitat` | Authored species rules evaluate world fields and nearby or reachable resources. Probes return a score, suitability and the reasons behind the decision. |
| `agents` | Ground, swim and flight movement with replanning, scene-aware destinations and optional limb contacts. Agents publish their real movement contacts for other systems. Add [activity decisions](agent-decisions.md) for prioritized goals and confirmed arrivals. |
| `wear` | Optional wear from contact-producing systems or submitted contact batches. Track local accumulation and recovery, and use `enabled` to control updates. Trace a durable route and promote it with `scene promote <run> <trace> --as id`, supplying its endpoints through `--at` and JSON `--args`. |

Water handles one surface column per XZ cell. Keep a simulation's resolution
and bounds appropriate to the models it uses. Use the same query names to
provide richer implementations for individual scenes.

`history.where` defines which events are meaningful to the world.
`history.limit` bounds retention, and the readout reports how many events
rolled off. `scene history <world> <rules.json>` adds seeded backstory.
A rule supplies `id`, a negative starting tick in `start`, optional
`count`, `interval` and `chance`, an `event`, and optional `edits`.
String values can reference `{id}`, `{index}` and `{tick}`. A
`{"$choose":[...]}` value selects from authored alternatives by seed.
The earlier events and their world edits survive in the derived manifest.

## Shaped colliders and swept movement

Use `half` for a box body or `collider` for a shape defined in the body's local
XYZ coordinates. The body's position and rotation apply to the whole shape.

| `collider.kind` | Shape parameters |
| --- | --- |
| `capsule` | Segment endpoints `a` and `b` and a `radius`. Matching endpoints make a sphere. Set `flatBottom: true` with distinct endpoints to put a flat sole at `a` and keep the rounded cap at `b`. |
| `box` | `half` extents with optional local offset `at` and yaw `turn` in radians. |
| `convex` | `vertices` and ordered `faces` made of vertex indices. Supply one closed convex shell with planar faces. A hull can have up to 24 vertices and 32 faces. |
| `compound` | `parts` with up to 12 boxes, capsules or convex hulls. The gaps between the parts remain open. |

For a centered upright flat-bottom capsule, put `a` at minus half the desired
height and `b` one radius below the top. For example, a 1.2-unit tall capsule
with radius 0.3 uses `a: [0, -0.6, 0]` and `b: [0, 0.3, 0]`. Mechanics uses a
convex hull with a planar sole and a faceted dome for collision and rendering.

Add `continuous: true` to a mechanics system to sweep translations in impact
order. A system with any authored `collider` enables sweeps by default. Set
`continuous: false` to use discrete movement with shape-aware overlap
correction. A box-only system defaults to its original solver. Set
`contactIterations` from 1 to 32 to tune simultaneous contact resolution in
the shape-aware solver. The default is 10.

Sweeps use the current orientation during translation. Angular and joint
motion use pose integration followed by overlap correction. Flat ground and
body colliders participate in the sweeps. Terrain heightfields use sampled
ground contact. Box bodies support live reshape, fracture and box surface
charts.

Clearance and support sample the collider geometry, including openings between
compound parts. Wheel contacts can report the ID and material of the supporting
body. The built-in body renderer bakes the authored collider silhouette.

`rig/impacts` in the workshop example contains the last tick's swept contacts.
Each entry has body IDs `a` and `b`, zero-based `parts`, an A-to-B `normal`, an
approach `speed` in world units per second, and `at`, a fraction of the tick.
Flat-ground contacts use `b: null` and `-1` for its part index. If `limited` is
true, the solver exhausted its contact budget and stopped the remaining
translation for that tick. Checkpoints and replays retain the report.

```sh
ink-studio sim run examples/world-continuous-colliders.json --ticks 1 --record workshop.run.json
ink-studio probe workshop.run.json --field rig/impacts
ink-studio sim render workshop.run.json --colored --out workshop.png
```

## Cloth and rope in a simulation

A `deformables` system stores point positions, velocities, broken links,
attachments and collected water in the world checkpoint. Each shape has a
stable ID under `config.shapes`. A `cloth` uses an origin `at`, edge vectors
`u` and `v`, and grid counts `nu` and `nv`. A `rope` uses an ordered `points`
polyline. Set `mass` for the whole shape, `radius` for point clearance, and
`stretch`, `shear` and `bend` for constraint compliance where applicable.
`tear` is the stretch ratio at which a link breaks. `style: "net"` draws the
structural strands of a cloth grid. Support is evaluated on its intact faces.

An `attachments` record maps names to a `node` index and either a world
`point` or an `entity` with an optional `socket` and local `offset`. Cloth
indices advance across `u` first. Attachments follow the target frame on each
tick. They act as kinematic pins. The `attach` and `detach` actions emit
events, and an attachment releases with reason `target-lost` if its target
disappears. Use `load` with a shape, a node and an impulse vector to apply a
scripted load. `cut` breaks structural links within a radius of a world point
and opens the affected cells for queries and rendering. Stretch tears and
scripted cuts emit `deformable-tear` with the link index.

Bind `bed`, `clearance` or `wind` to shared height, signed-distance or vector
fields. Point contacts use the same obstacle geometry as other world systems.
`support` publishes the upper side of intact cloth triangles and the upper
surface of rope strands. Set a shape's `support` to `false` for a handline or
other visual or moving accessory. The system's `supports` list can combine
these records with existing support fields such as `rig/support`.

To catch a rigid body, add the deformable `surfaces` field to a mechanics
system's `deformables` array. Mechanics sweeps a bottom-center support point
per body against the upper cloth faces. The preceding snapshot provides the
surface geometry, and a typed event connection applies the reaction to the
face's nodes on the following solver step. A walking agent can use the same
`support` field. Set `contactEvents: true` on its `agents` system and connect
its `contacts` output to the deformable `traffic` input. A footfall's `weight`
acts as a mass and `trafficDuration` sets the impulse duration in seconds.

```json
[
  { "from": "rig/deformable-loads", "to": "fabric/loads" },
  { "from": "traffic/contacts", "to": "fabric/traffic" }
]
```

A cloth shape with `water` collects rain at a rate of depth per second from
`water.rain`, the system's numeric `rain` field, or both. Each intact face
catches rain according to its horizontal projected area. `water.capacity`
sets its maximum retained depth, `water.density` converts volume to mass,
and `water.drain` is a drainage rate per second. The `water` probe reports
captured, retained, drained and spilled volumes, a balance error, and the
latest runoff positions. The retained mass loads the cloth. Runoff is exposed
to the host for routing into other systems.

Set `visual.fields.deformables` to the `surfaces` field to render the current
shape. The yard example includes a catch net, a rain tarp and a rope bridge.

```sh
ink-studio sim run examples/world-deformable-yard.json --ticks 70 --record yard.run.json
ink-studio probe yard.run.json --field fabric/water
ink-studio sim render yard.run.json --colored --out yard.png
ink-studio sim fork yard.run.json --actions examples/world-deformable-yard.commands.json --ticks 83 --record cut.run.json
ink-studio probe cut.run.json --field world/history
```

## Routed cables, hoses and belts

Give a `routed-links` system a table under `config.links`. Each entry has
`from` and `to` anchors and optional ordered `guides`. An anchor can be an
XYZ point or an `entity` with an optional `socket` and local `offset`.
Anchors follow the entity's current pose. Add `returnGuides` for a closed
belt. The route goes through `to` and the return guides before closing at
`from`. A pulley arc can use several closely spaced guides.

Set the installed `length` or supply `slack` to add to the distance at the
initial posed sockets. Loose spans sag in the configured `gravity` direction.
The model uses the length difference and `stiffness` to calculate tension
when the route is taut. Set `breakTension`, `breakStrain` (fractional stretch),
or both. Exceeding a limit latches a break and records the segment, point,
threshold reading and tick in world history. A missing socket interrupts
delivery until the anchor resolves again. Add `routes/reactions` to a
mechanics system's `routedLoads` list to apply taut-link forces at the
moving sockets and guides.

Choose a `carry` record based on the payload.

| `kind` | Configuration and runtime interface |
| --- | --- |
| `signal` | Set `type` to `bool`, `number`, `vec3`, `record` or `event`. Wire `in.<link>` and `out.<link>` as ordinary typed ports. Disconnection publishes the type's zero value or the configured `idle` value. |
| `transfer` | Bind two compatible `system/account` endpoints using `from` and `to`. Supply `rate` per second or `amount` per update. Fluid and energy use the same conservative accounting, capacity checks and receipts as other transfers. A slow route scales its rate by its solver interval. |
| `drive` | Wire the driving shaft speed to `speed.<link>` and the driven shaft's resistance to `load.<link>`. `speed-out.<link>` sends the speed times `ratio` and `load-out.<link>` reflects torque times the absolute ratio. `capacity` limits delivered torque and `engageTension` sets the minimum grip. `slipping.<link>` reports a loose or overloaded drive. Use `externalLoad: true` on a mechanics joint to expose `load.<joint>` and `external-load.<joint>`. |

`enable.<link>` switches the carrier while the installed route remains
under tension. `active.<link>` and `tension.<link>` publish the sampled
state. Ports follow the runtime's ordinary stateful timing. The `links`
field reports the current geometry, installed length, status and latest
transfer receipt. It can show `over-limit` after a machine moves in the
current tick, with the break applied when the route next steps. `route`
traces the same geometry for one link. For rendering set
`visual.fields.routedLinks` to the `links` field.

Use `cut` with a link and optional zero-based `segment` and `fraction`.
`repair` rejoins a cut or snapped link and can set a new installed `length`.
`pay-out` changes that length. `reroute` replaces selected endpoints or guide
lists. All four actions can be scheduled and replayed.

```sh
ink-studio sim run examples/world-routed-workshop.json --actions examples/world-routed-workshop.commands.json --ticks 40 --record workshop.run.json
ink-studio trace workshop.run.json routes/route --args '{"link":"hose"}'
ink-studio probe workshop.run.json --field world/transfers
ink-studio sim render workshop.run.json --colored --out routed-workshop.png
```

## Material fatigue and permanent deformation

Set `structure` on a box body to divide its primary axis into bending
sections. `axis` is `0`, `1` or `2` and defaults to X. `sections` ranges
from 2 to 12 and defaults to 8. `bearings: "ends"` holds both ends level
while `"fixed-start"` models a cantilever anchored at its negative end.
The body uses its physical material's `fatigue` and `plastic` laws. You can
also set either law directly under `structure` with numeric coefficients.

The beam model estimates local bending stress from transverse force and
the rectangular cross section. Normal collision impulses, actuator loads
and configured routed loads contribute at their points of application.
Collision load positions use the touching shapes' overlapping bounds.
Structure enables the shape-aware mechanics solver. The model uses the
authored bearings as the reference for calculating moment arms.

Each stress reversal closes a half cycle. Its amplitude is half the
stress change between successive turning points. At or above `endurance`,
damage increases by `0.5 × (amplitude / endurance)^exponent / life`.
A steady load can cause plastic creep when its stress exceeds `yield`.
The accumulated curvature persists after unloading. It changes the beam's
collider, rendered shape, sockets and support surface. Material changes in
world space also publish bounded dependency updates. Surface charts map
back to their rest coordinates as the beam bends and when it fractures.

Add `wear` to a hinge, shaft or slider. Its fatigue law comes from the
child's material or an inline `wear.fatigue` law. `sectionModulus` scales
the joint's applied load into a stress value. `travelRate` adds wear during
loaded travel. `maxPlay` caps the total backlash in radians for a hinge or
shaft, or world units for a slider. The realized pose can hold while the
drive changes direction and takes up the gap. Set `failure: "detach"` to
release the joint when its damage reaches one.

`material-yield` records the onset of permanent bending. `material-failure`
records the first section or joint to reach unit damage. Use `rig/fatigue`
to read current and peak stress, damage, counted cycles, curvature and
world positions. Pass `body` and optional `section`, pass `joint`, or
probe a world point to find the nearest live beam section. The joint
readout includes commanded and realized positions, speed and play.

```sh
ink-studio sim run examples/world-material-fatigue.json --actions examples/world-material-fatigue.commands.json --ticks 64 --record fatigue.run.json
ink-studio probe fatigue.run.json --field rig/fatigue --args '{"body":"cycle-beam"}'
ink-studio probe fatigue.run.json --field rig/fatigue --args '{"joint":"hinge"}'
ink-studio sim render fatigue.run.json --colored --out fatigue-bench.png
```

## Live sediment transport

Set `sediment` on a water system to track suspended solids and an erodible
bed. All sediment quantities are solid-equivalent thicknesses or volumes.
`erodibleDepth` sets the initial depth of loose bed material over bedrock.
`erodible` overrides that depth in XZ regions. `initial` seeds suspended
thickness in regions, and `sediment-feed` adds a timed pulse using `bounds`
and `depth`.

Suspended material moves with the same fluxes that move water across cell
faces. Hydraulic substeps limit transfers to the source's available material.
Internal pumps carry the source concentration. `drainFraction` controls
how much of the drain's sampled sediment is exported, with zero retaining
the solids. An external water account transfers filtered water.

`capacity` scales the concentration the current can carry with its speed.
`maxConcentration` caps that capacity. Water with room for more material
can erode the loose bed. A physical `surface` can supply the erosion
`threshold` and `rate`, with `sediment.erosion` as the fallback. A loaded
cell deposits the excess at the `settling` rate per second. Dry cells settle
their suspension directly. Bed changes preserve local water volume and
affect the next hydraulic substep. Live height edits account for removed
or added solids and establish a new local reference bed.

Set a gate's `siltClearance` to the bed rise that closes a fully obstructed
face. Deposits on either side narrow the opening in proportion to the rise
above the reference bed. `gates` and `effective-opening.<gate>` report the
most obstructed face. The existing `gate.<gate>` signal reports the command.
`gate-silted` and `gate-cleared` record threshold crossings in world history.

`sediment` reports the solid volume ledger, including bed material,
suspension, cumulative erosion, deposition, face transport, pump transport,
drain export, and balance error. Probe or export `suspended`, `concentration`,
`bed-change`, and `erodible-depth` over the water grid. Mechanics, traversal
and rendering can bind the same `bed` field. Bed changes publish bounded
spatial updates so route consumers can reconsider a crossing. Set
`visual.fields.sediment` to `bed-change` to color the changed terrain.
The standard water preview colors suspended sediment by concentration.

```sh
ink-studio sim run examples/world-sediment-gate.json --ticks 65 --record sluice.run.json
ink-studio probe sluice.run.json --field river/gates --args '{"gate":"sluice"}'
ink-studio probe sluice.run.json --field river/sediment
ink-studio sim run examples/world-sediment-ford.json --ticks 65 --record ford.run.json
ink-studio trace ford.run.json nav/route --at 3.6,0.43,0.62 --args '{"to":[3.6,0.43,1.88],"radius":0.115,"maxWade":0.18,"maxSlope":2.6}'
ink-studio sim render ford.run.json --colored --out ford.png
```

## Pressurized pipe networks

A `pipe-network` system stores liquid in a graph and moves it along edges
in response to hydraulic head. Author the storage vessels and junctions
as named `nodes`. A node needs `capacity` in cubic world units and accepts
`initial` volume, `area` (defaults to capacity), `precharge` in units of
head, and an XYZ `position`. Its hydraulic `elevation` defaults to the
position's Y. A small effective area gives a stiff storage response.

Pressure head is `precharge + volume / area`. Total head adds elevation.
The reported gauge pressure multiplies pressure head by `specificWeight`
(defaults to 9810 for water, yielding pascals when world units are metres).
Each pipe's `conductance` is the volume per second per unit of head at full
opening. Flow responds to the head gap with a damped, capacity-limited step.
This is a lumped model for slow storage and flow changes. It represents
compressible storage through effective area and precharge.

| Table | Configuration |
| --- | --- |
| `pipes` | Each row has `from`, `to`, and `conductance`. Optional `opening` scales conductance. `boost` adds head in the forward direction, `oneWay` acts as a check valve, and `maxFlow` caps the rate in either allowed direction. |
| `leaks` | Each row has a `node`, `conductance`, optional `opening`, `maxFlow`, and `outsideHead` (defaults to node elevation). Open leaks discharge to the environment according to their head gap and count toward the loss ledger. |
| `boundaries` | Each row binds a `node` to an external `account` with `conductance`, optional `opening` and `maxFlow`, and `direction` of `in`, `out`, or `both`. Supply a constant `head` or a scalar `headField` in world units and sample point `at` (defaults to node position). |

For a pond intake or irrigation outlet, expose a water grid cell as an account
and sample the water system's `surface-height` field at that cell. It is bed
elevation plus depth and reports the bed elevation at a dry cell. Endpoint
availability still limits the transfer. A pressurized drain can use a boundary
to deposit its discharge into a surface-water cell. Each node is itself a
transfer account, with `resource` defaulting to `water` and units of
`world^3`. Boundaries reuse the world transfer ledger and request from the
pre-step snapshot once per scheduled update.

To make a hydraulic actuator, add `piston` with `area`, `stroke`, and
optional `position` and resisting `load` to a pipe. The piston travels
only as far as actual accepted flow permits, stops at the ends of its
stroke, and can reverse with the pressure gap. Its ports report
`position.<pipe>`, `speed.<pipe>`, and available `force.<pipe>`.
Connect position to a mechanics slider's position drive. The mechanical
load can be authored or supplied on `load.<pipe>`.

Use `world/input` or signal connections to drive the numeric
`valve.<pipe>`, `boost.<pipe>`, `leak.<leak>`, and
`boundary.<boundary>` inputs. Opening values range from zero to one and
default to one. The network publishes `head.<node>`, `pressure.<node>`,
`volume.<node>`, signed `flow.<pipe>` (positive from `from` to `to`),
and outward `leak-flow.<leak>`. Rates are in cubic world units per second.
Leak flow beginning or ending emits `pipe-leak-start` or `pipe-leak-stop`.
Probe `nodes`, `pipes`, `leaks`, or `boundaries` by name. Boundary
probes show actual transfer receipts and signed flow into the network.
`mass` reports initial and current volume, imports, exports, leaks, and
balance error. `trace <system>/flow` follows the directions of recently
accepted pipe flow. Add pipe `guides`, `radius`, and `look`, and bind
`visual.fields.pipes` to the network's `pipes` field for a splat render.

The [hydraulic yard](../examples/world-hydraulic-yard.json) draws from a
pond, raises a platform, and feeds a separate irrigation channel. Timed
commands open a leak, isolate the pump, and restore service.

```sh
ink-studio sim run examples/world-hydraulic-yard.json --actions examples/world-hydraulic-yard.commands.json --ticks 94 --record yard.run.json
ink-studio probe yard.run.json --field network/nodes --args '{"node":"header"}'
ink-studio probe yard.run.json --field network/mass
ink-studio trace examples/world-hydraulic-yard.json network/flow --ticks 48 --args '{"from":"intake","to":"sprinkler"}'
ink-studio sim replay yard.run.json
ink-studio sim render yard.run.json --colored --out hydraulic-yard.png
```

## Stacked and enclosed water

Use an `enclosed-water` system for chambers, tunnels, shafts, and
reservoirs that can overlap in XZ at different elevations. Each named
`chamber` has XYZ `bounds`, an optional initial water volume `initial`,
and optional absolute `airPressure` at the start. Chambers have
axis-aligned footprints and level surfaces. Their interiors must be
disjoint in XYZ. Split a stepped space into adjoining chambers and
connect them with openings.

| Table | Configuration |
| --- | --- |
| `openings` | Bind `from` and `to` chambers. `sill` and `crown` describe the vertical aperture. For a shaft or drop, set `fromSill`, `fromCrown`, `toSill`, and `toCrown` independently. The default aperture spans the chamber height. |
| `vents` | Bind a `chamber` to the atmosphere at `height`, which defaults to the ceiling. `open` defaults to true. A submerged vent below the ceiling stops breathing. A roof vent can admit air as a full chamber drains. |
| `boundaries` | Bind a `chamber` to an external water `account`. Use `head` or a numeric `headField` sampled at an XYZ `at`, plus `sill`, `crown`, and `direction` of `in`, `out`, or `both`. Use a shallow-water account with `surface-height` sampled at the account's cell for a pond or canal. |

Openings and boundaries use `conductance` to scale liquid flow by the head
difference and wetted aperture. Optional `opening` scales the exchange from
zero to one and defaults to one. `maxFlow` caps volume per second. An
optional `gate` samples a world-space clearance `field` at its `points`.
Exchange occurs when every sample exceeds `radius` (default zero). Bind this
to a live solid's `clearance` field to let a cut or fill open or close a
passage at the authored location. The same chamber volume is carried forward
through the edit.

Air shares pressure across openings with headspace on both sides. A connected
vent holds that air at ambient pressure. In sealed chambers the trapped air
amount is conserved and its pressure rises as the headspace shrinks. The
simulation uses isothermal air and hydrostatic water. The default constants
are `ambientPressure: 101325` and `specificWeight: 9810` in metre-based worlds.
Pressure is absolute in pascals. Capped liquid transfers preserve volume.
Chambers expose `water` transfer accounts in cubic world units, including
for exchange with [pressurized pipes](#pressurized-pipe-networks).

Drive `opening.<id>`, `vent.<id>`, and `boundary.<id>` with typed signals
or `world/input` commands. Read `level.<chamber>`, `volume.<chamber>`,
`pressure.<chamber>`, and `vented.<chamber>` or follow signed
`flow.<opening>` and `effective-opening.<opening>`. Probe `chambers`,
`openings`, `vents`, and `boundaries` by name. XYZ probes expose `phase`,
`depth` (water above the probe point), `pressure` (including the water
column above a submerged point), `head`, `medium`, and `water`.
`mass` reports the water balance and air exchange, with air amount
expressed as equivalent volume at ambient pressure.

Set `visual.enclosedWater` to the system ID to render its stacked spans.
It can share a splat view with a solid `visual.volume`. Use distinct
interiors when combining layered water with another rendered water source.

```sh
ink-studio sim run examples/world-cellar-flood.json --ticks 160 --record cellar.run.json
ink-studio probe examples/world-cellar-flood.json --ticks 77 --field flood/chambers --args '{"chamber":"cellar"}'
ink-studio probe cellar.run.json --field flood/phase --at 1.6,0.8,0.5
ink-studio probe cellar.run.json --field flood/mass
ink-studio sim replay cellar.run.json
ink-studio sim render cellar.run.json --colored --out cellar.png
```

## Heat, moisture, and phase changes

Set `thermal` on a `water` system to simulate temperature, liquid water,
ice, and vapor on the same XZ cells. `initialTemperature` and
`initialVapor` are bounds/value patches. An initial temperature below
`freezingPoint` starts the cell's authored water as ice. Vapor and ice
depths are water-equivalent. Ice stays in its cell and raises the floor
seen by liquid flow. `bed` still exposes the editable ground. The
`water` column exposes the floor above accumulated ice.

Shallow-water face fluxes and pumps carry liquid enthalpy. Neighboring
cells conduct heat and exchange vapor. Evaporation cools a wet cell.
Condensation returns water and latent heat when the air holds more vapor
than its temperature supports. The solver uses `latentFusion` to hold
temperature at the freezing point until the phase change uses the
available heat. `latentVaporization` sets the energy cost of drying.

| Setting | Meaning |
| --- | --- |
| `ambientTemperature`, `ambientField` | Heat exchange with the air uses the `ambient` number input, initially `ambientTemperature`. A sampled numeric `degC` field can supply local air temperature. |
| `heatCapacity`, `conductance`, `conductivity`, `waterHeatCapacity` | Ground heat capacity per area, heat exchange with air, heat exchange between neighbors, and water heat capacity per volume. |
| `saturation`, `evaporation`, `condensation`, `vaporDiffusivity` | Saturated vapor inventory at the freezing point, drying and condensation rates, and the diffusivity of near-surface vapor. |
| `materials` | Bounds and portable `material` asset IDs. A material's thermal capacity, ambient conductance, and drying rate override the corresponding defaults in its region. |
| `sourceTemperature` | Temperature credited to rain and incoming water from transfer accounts. Outgoing water carries the donor's enthalpy. |

The default heat constants are scaled for metres and joules. In scenes
with other units or compressed time, set the coefficients together.
Use `<water>/heat` with XZ `bounds` and signed `energy`
to distribute heat over the selected cells. The phase model uses a
shared cell temperature, a closed near-surface vapor inventory, and
a saturation curve that scales with temperature.

Set a gate's `iceClearance` to the ice thickness that jams it. Ice on
either side reduces the opening, and a gate with both ice and silt
clearance applies both restrictions per face. Hydraulic flow uses ice
at the start of its step. `gates` exposes the commanded and effective
opening, ice thickness, and jam state. History records `gate-frozen`
and `gate-thawed`. Traversal sees the released water through the normal
water query. Set `visual.fields.ice` to the thickness field for splats.

Probe `temperature`, `ice`, `vapor`, `humidity`, `phase`, or
`phase-state` at a point. The `heat` ledger accounts for energy added
by the air, rain, transfers, and scheduled heat commands. The `mass`
ledger still reports mobile liquid as `volume`, and adds `ice`,
`vapor`, and `total` for the full water balance.

```sh
ink-studio sim run examples/world-thawing-ford.json --ticks 140 --record thawing-ford.run.json
ink-studio probe examples/world-thawing-ford.json --ticks 35 --field river/gates --args '{"gate":"sluice"}'
ink-studio probe thawing-ford.run.json --field river/heat
ink-studio trace thawing-ford.run.json nav/route --at 1.7,0.66,-1.25 --args '{"to":[1.7,0.66,1.25],"radius":0.1,"maxWade":0.18,"maxSlope":10}'
ink-studio sim replay thawing-ford.run.json
```

## Ventilation and airborne transport

The `ventilation` system moves air through a graph of well-mixed rooms.
Each `rooms` entry has disjoint XYZ `bounds`, an optional
`temperature` in degrees Celsius, and initial `concentrations`.
The bounds set the room volume and where spatial queries read its air.
`exterior` adds named reservoirs with fixed temperature and concentration.
The default `outside` reservoir starts with zero smoke and dust,
20 °C air, and 0.008 kilograms of water vapor per cubic world unit.

| Setting | Meaning |
| --- | --- |
| `openings` | Each entry names `from` and `to` endpoints. `conductance` sets the flow response to a room pressure difference. `opening` scales conductance and mixing from zero to one. `mixing` sets equal air exchange in both directions, even at zero net flow. |
| `fan` | A signed air drive in cubic world units per second. Positive values drive from `from` to `to`. The pressure solution balances intake and exhaust in every room, so actual flow depends on the connected return path. |
| `wind` | On an opening, set a sample point `at`, a forward `direction` and optional effective `area`. Local wind projected on that direction contributes to the drive. Set the system's `windField` to a numeric XYZ or XZ vector field in `world/s`, or drive the `wind` XYZ input. |
| `gate` | Optionally bind an opening to a numeric clearance `field` and up to eight XYZ `points`. Opening is effective when each sample exceeds `radius` (default zero). A live wall cut or moving door can change these samples. |
| `tracers` | Add named airborne loads such as dust. Each tracer defines amount `units` and an optional first-order `decay` for settling or removal per second. Reads are amount per cubic world unit. `smoke` and `humidity` are built in. |
| `sources` | Add stock to a `room` with named `rates` per second. Heating uses `rates.heat` in joules per second and the system's volumetric `heatCapacity`. |

Typed controls expose `opening.<id>`, `fan.<id>`, and
`source.<id>` (zero to one). Outputs include `flow.<id>`,
`effective-opening.<id>`, and room temperature, humidity, smoke,
pressure, and quality. A change between an open and closed passage emits
`air-opening-opened` or `air-opening-closed`.

Room queries expose `temperature`, `humidity`, `smoke`, every custom
tracer, and `air-quality`. `quality` assigns concentration weights to
tracers. The score is `1 / (1 + weighted concentration)`. Use these
fields in ordinary habitat rules or bind the room temperature field
to thermal water's `ambientField`. Probe `rooms` or `openings` by
name. `budget` shows current amount, emissions, imports, exports,
removal, and balance error for each load, including heat in joules.
`trace <system>/airflow` follows the net flow direction through openings.

The same room and opening state powers [acoustic queries](acoustic-queries.md).
Agents and audio hosts can read estimated gain, arrival direction, delay and
muffling through the current apertures.

For the splat view, set `visual.air` to an object with the `rooms`
field, optional `tracer` (defaults to smoke), `scale`, `color`,
and ray-march `step`. The bounded atmosphere reads the current room
concentration. In the [ventilated shelter](../examples/world-ventilated-shelter.json),
a stove adds smoke, heat, humidity and dust. The moving door opens the
intake path so wind and an extractor can clear the room. The scout
enters once its habitat rule accepts the measured air quality.

```sh
ink-studio sim run examples/world-ventilated-shelter.json --ticks 120 --record shelter.run.json
ink-studio probe shelter.run.json --field air/rooms --args '{"room":"shelter"}'
ink-studio probe shelter.run.json --field home/suitability --at -1.33,0.15,0.17 --args '{"species":"helper"}'
ink-studio trace shelter.run.json air/airflow --args '{"from":"yard","to":"outside"}'
ink-studio probe shelter.run.json --field air/budget
ink-studio sim replay shelter.run.json
```

## Power networks and motor loads

A `power-network` system routes watts through a lossless graph of
named `buses`. Buses optionally declare XYZ `position` for rendering.
Each `lines` entry links `from` and `to` in both directions.
`closed` defaults to true and can be driven by `close.<line>`.
The graph uses deterministic shortest closed paths. Loads are served
in descending `priority`, with generator power used before batteries.
Surplus generation charges reachable batteries.

| Table | Configuration |
| --- | --- |
| `generators` | Set `bus`, a rated output `watts`, and optional `enabled`. Drive `supply.<id>` and `enable-generator.<id>`. A `wind` source samples a `world/s` XYZ or XZ vector `field` at `at` and uses a cubic response between `cutIn` and `rated`. Output holds at the rating until `cutOut`. |
| `batteries` | Set `bus`, `capacity` and `initial` in joules. `chargeWatts` and `dischargeWatts` cap bus power. `chargeEfficiency` and `dischargeEfficiency` account for conversion losses. Every battery exposes an `energy` account in `J` for standard world transfers. |
| `loads` | Set `bus`, optional `watts`, `idle`, `efficiency`, `priority`, and `enabled`. `enable-load.<id>` switches the load, and `demand.<id>` replaces its requested useful watts. Optional `idle` is electrical standby draw. The network adds standby and accounts for efficiency when calculating electrical demand. |

Add `breaker: {"watts":112,"delay":0.2}` to a line to trip after
that much time above the rated power. The breaker measures proposed
net watts through the line. A trip opens the branch and reallocates the
same tick before posting energy. The trip latches. Call the
`reset` action with `{"line":"workshop-breaker"}` after clearing the
overload. The breaker records its measured load and the contributing
machines. With `causality` enabled, the event can link to their demands.

On a root `mechanics` shaft, hinge, or slider, set `powerLimited: true`.
The joint reports `power-demand.<joint>` based on its requested speed,
reflected torque or force, and its moving `idlePower` (default 1 W).
Enable `gravityLoad` on a slider to include the weight of its mounted
mass when moving against gravity. Motion at the travel limit requests
zero power. Wire this demand to the load's `demand.<id>`. Wire
`allowance.<id>` back to `power.<joint>`. The joint caps speed by the
budget and reports `power-draw.<joint>` and `power-limited.<joint>`.
The normal stateful signal boundary applies. At a shared update rate,
an electrical dispatch reserves energy for the next mechanical update.
`delivered.<id>` reports electrical watts and `allowance.<id>` reports
the motor budget after load efficiency and standby.

Probe the `lines`, `loads`, `generators`, or `batteries` fields and
inspect the `energy` ledger. Use `trace` with `<system>/power` to see
the generation or storage paths serving a load and related trips.
Bind the `lines` field to `visual.fields.powerLines` for splats.
Lines can use `guides`, `radius`, and live, dead, and tripped palette ramps.

In the [windmill workshop](../examples/world-windmill-workshop.json),
the windmill charges the battery, and the battery supplies the lift's
shortfall. Starting the grinder trips the shared breaker until reset.

```sh
ink-studio sim run examples/world-windmill-workshop.json --ticks 96 --record workshop.run.json
ink-studio probe examples/world-windmill-workshop.json --ticks 52 --field power/lines --args '{"line":"workshop-breaker"}'
ink-studio trace examples/world-windmill-workshop.json power/power --ticks 52 --args '{"load":"lift"}'
ink-studio probe workshop.run.json --field power/energy
ink-studio sim replay workshop.run.json
```

## Local gravity and buoyancy frames

A `gravity` system defines a spatial frame with unit `up`, an
`acceleration` in `world/s^2`, a unitless `buoyancy` multiplier, and
`angular-velocity` in `rad/s`. Probe `frame` for all four together.
The system has a default `frame` and optional XYZ `regions`. The last
matching region supplies the local frame.

| Frame kind | Settings |
| --- | --- |
| `uniform` | Set a constant `acceleration`. Up defaults to the opposite direction, with world up as the zero-gravity fallback. |
| `radial` | Set `center` and `strength`. Use constant gravity or `falloff: "inverse-square"` with a `referenceRadius`. Set `outward` for gravity pointing away from the center. |
| `rotation` | Set `center`, rotation `axis`, and signed `omega` in radians per second. Apparent gravity points outward from the axis. Moving actors and bodies use the frame's Coriolis term when `coriolis` is enabled (the default). |

Every frame accepts an explicit `up` and `buoyancy`. Bind
`accelerationField`, `upField`, or `buoyancyField` to typed spatial
fields to override values where those fields provide a reading. For
example, a wind-tunnel scene can author a constant sideways gravity or
a region with a reduced buoyancy multiplier.

Set `gravityField` on `mechanics` to use a frame or an XYZ acceleration
field. Rigid bodies use the same collider contacts with this mode and
take their floors from scene colliders. Wheel supports are sampled
along local down. Wheel traction and yaw use the local tangent plane.
Set a free body's `gravityAlign` to a rate per second to turn its Y axis
toward local up. Ordinary bodies can tumble. Powered slider weight
also reads local acceleration.

A buoyancy force accepts a numeric depth field in world units, positive
below the surface, or a record with `depthAtPoint`. The old Y-up
`surface` record is also supported. Force points along local up and
scales with the frame's buoyancy multiplier. Set `displacement` and
`density` to use displaced-fluid weight, or supply a fixed
`magnitude`. The force reaches full displacement at the configured
`radius` depth.

The `characters` system wraps the same capsule controller. Configure
`gravity`, `clearance`, optional `support` (a directional trace such
as `rig/ray`), and optional `medium` (water depth or a medium record).
Each entry in `characters` supplies a starting XYZ `position`,
optional `forward`, and ordinary character `tuning`. Drive
`move.<id>` using its X and Z components as right and backward in
the transported frame. Set `worldMove` to use a world XYZ direction
projected onto the tangent plane instead. Use `vertical.<id>`,
`jump.<id>`, and `climb.<id>` for the remaining controls. Probe
`actors` or render that field with `visual.fields.characters`.

In JavaScript, pass `W.characters.fromQuery(query, bindings)` to
`controller.step`, or supply a world adapter with `gravityAt(point)`,
`clearance(point)`, and optional `supportAlong(origin, direction, distance)`
and `mediumAt(point)`. Custom movement callbacks in this mode operate
in the local tangent frame. The returned actor, contacts and motion
segments use world coordinates. Create a follow camera with
`W.cameras.follow({localUp:true})` to transport its orbit with the actor.

The [pocket moon](../examples/world-pocket-moon.json) shows a surveyor
and rover crossing the same sphere. The [rotating dock](../examples/world-rotating-dock.json)
shows a hull floating against centrifugal gravity.

```sh
ink-studio sim run examples/world-pocket-moon.json --ticks 190 --record moon.run.json
ink-studio probe moon.run.json --field crew/actors
ink-studio probe moon.run.json --field moon/frame --entity surveyor
ink-studio trace moon.run.json rig/ray --at 3,0,0 --args '{"direction":[-1,0,0],"distance":1}'
ink-studio sim run examples/world-rotating-dock.json --ticks 150 --record dock.run.json
ink-studio probe dock.run.json --field tank/depth --entity hull
ink-studio sim replay moon.run.json
```

## Resources, recipes, and logistics

A `logistics` system models resources such as ingredients, spare parts, or
nutrients with the same five configuration tables.

| Table | Entry |
| --- | --- |
| `resources` | `{ units, type, look? }`. Declare `integer` for countable items or `number` for continuous quantities. The optional `look` is a palette ramp for rendered cargo and stock. |
| `containers` | `{ position?, stocks }`. Each stock is keyed by resource and accepts `initial` (default zero) and `max` (default unlimited). Optional `display: { at, half }` grows a stock pile from its base point to full height at capacity. |
| `recipes` | `{ duration, inputs?, outputs? }`. Duration is in simulation seconds. Each side maps resource IDs to positive quantities. Leave the input side empty for a producer or the output side empty for a consumer. |
| `processes` | `{ recipe, inputs?, outputs?, enabled?, speed?, priority? }`. On each side, bind each ingredient or result to a container ID that holds it. Several processes can use the same recipe independently. |
| `links` | `{ from, to, resource, amount, travel?, slots?, mode?, enabled?, priority?, guides?, route? }`. Name containers and specify either an `amount` per update or a `rate` per second. `travel` is in simulation seconds. `slots` caps the outstanding shipments. |

Each system update unloads due shipments, advances the recipes, then
dispatches new shipments. Within each phase, higher priority goes first
and IDs break ties. A process reserves all inputs together and commits all
outputs together. If any output is full, the finished batch retains its
reserved ingredients until all outputs fit. Each process holds one active
batch and can complete up to `maxBatches` batches per update (default 32).

An instantaneous link settles both ends in the same update. With nonzero
travel, cargo remains in transit until the destination accepts it. Use
`mode: "exact"` for all-or-nothing collection and delivery. The default
`partial` mode can load or unload part of a shipment. Rate-driven integer
links carry fractional rate credit forward. A scheduled or wired
`enable-link.<id>` input controls dispatch. Cargo already in transit can
still unload with dispatch disabled. Use `enable-process.<id>` and
`speed.<id>` to control processing. Outputs include `stock.<container>.<resource>`,
`completed.<process>`, `blocked.<process>`, `delivered.<link>`, and
`link-blocked.<link>`. `completed` counts all completed batches.
`delivered` reports the quantity delivered this update.

A link can check a live navigation trace using
`route: { trace: "nav/route", at?, to?, args? }`. The positions default to the
two container positions. Departures wait for a successful trace and expose
its obstruction when available. Travel time and optional visual `guides`
are authored separately. Bind `cargo` and `stock-bodies` to the world's
`visual.fields.bodies` to render them using the existing splat renderer.

Every stock is a transfer account at `system/container.resource` and can
receive or send compatible amounts through `world/transfer` or `exchange`.
Inspect `stocks`, `recipes`, `processes`, and `links` with the usual query
tools. The `ledger` splits each resource into stored, reserved, and in-transit
amounts, with production, consumption, receipts, exports, and balance error.
The `supply` trace walks upstream from a `process`, `link`, or `account`
within the logistics system. It reports current insufficient inputs, full
destinations, and route obstructions. A trace can stop at the system boundary
where another system supplies a transfer account. Use `world/transfers` for
those receipts. Stock, work in progress, and cargo all resume from checkpoints.

The harvest example closes the grain crossing at tick 51 and reopens it
at tick 171. At tick 150 the market's missing bread traces through the
bakery and mill to the gate blocking the grain cart.

```sh
ink-studio sim run examples/world-harvest-logistics.json --ticks 250 --record harvest.run.json
ink-studio trace examples/world-harvest-logistics.json flow/supply --ticks 150 --args '{"process":"market"}'
ink-studio probe harvest.run.json --field flow/ledger
ink-studio sim replay harvest.run.json
```

## Relighting editable volumes

Enable `lighting` in a `volume` system's config. The volume shades its retained
splat positions, surface normals, and material colors when you render it.
Cuts and fills can change shadows farther from the edit than the rebuilt
geometry. Material layers can change the color bounced onto nearby surfaces.
Shadow rays follow the same solid geometry used by the editing tools. Both the headless renderer and WebGL can draw the resulting
packed splats.

```json
{
  "ambient": 0.12,
  "sun": { "direction": [-0.28, 0.92, 0.31], "color": "#fff0c2", "intensity": 1.4 },
  "sky": { "color": "#9ec2ff", "intensity": 0.23 },
  "indirect": { "distance": 1.6, "strength": 0.66, "rays": 4, "probeSize": 0.42 },
  "lamps": {
    "lantern": { "at": [3.2, 1.32, 0.65], "range": 3.1, "color": "#ff9c52", "intensity": 5.3 }
  }
}
```

Sun direction points from the receiver toward the light. Its optional
`distance` bounds the shadow ray and defaults to the volume's diagonal.
Point lights have finite range. Use `volume-id/set-light` with a lamp ID and
the position, range, color, intensity, or enabled flag you want to change.
The runtime saves lamp settings alongside the volume edits for replay.

The diffuse term combines sky visible within `indirect.distance` with one
local surface bounce. `rays` controls how many directions each probe samples
and `probeSize` controls spatial reuse. Choose a probe size near twice the
volume cell spacing to start. Set `strength: 0` to disable the bounce.
The volume's cut and fill shapes supply the shadow geometry.

The `lighting` query reports changed and reused chunks, surface samples, and
ray work. It describes the lighting work for the queried snapshot. A moved
lamp reuses the sun, sky, and bounce paths and only refreshes its local
contribution. Cuts and fills invalidate receivers whose light paths cross
the edit. A restored checkpoint starts with a fresh lighting cache.

```sh
ink-studio sim render examples/world-lightwell-workshop.json --ticks 2 --colored --out skylight.png
ink-studio probe examples/world-lightwell-workshop.json --ticks 4 --field workshop/lighting
node scripts/benchmark-volume-lighting.js
```

The benchmark compares incremental work to a full lighting refresh on
prepared geometry and verifies that their rendered splat data agree.
For another retained geometry provider, use
`K.procedural.relighting.create(settings, { bounds, cell })`. Pass
`refresh({ chunks, field, lamps, edits, previous })` the native chunk parts
with stable IDs and world bounds, a signed distance function
`field.distance(x, y, z)`, and an optional `field.albedo(x, y, z)` returning
packed RGB for bounce donors. Each edit carries world `bounds` and can mark
a material-only change with `occlusion: false`. Retain the returned frame
for the next refresh.

## Extend the runtime in JavaScript

```js
const { KIT: { world: W } } = require('@shapeshift-labs/ink-studio').load();

W.runtime.register('counter', ({ rate = 1 }) => ({
  initial: () => ({ count: 0 }),
  step: (state, tick) => ({ count: state.count + rate * tick.dt }),
  fields: {
    count: { type: 'number', read: ({ state }) => W.query.ok(state.count) }
  }
}));

const run = W.runtime.create({ systems: { meter: { kind: 'counter' } } });
run.advance(60);
console.log(run.query().probe('meter/count').value);
```

A system factory compiles its definition once per runtime instance.
`initial`, `step`, and `actions` return finite JSON state. Keep persistent
state in those values so fork and replay can recreate it. Optional hooks
include `checkAction(type,args)`, `validateState(state)`, `pose(state,id)`,
`fields`, `traces`, typed `inputs` and `outputs`, and
`output(state,context)`. A consumer can implement `checkFields(query)`
to bind and check its field references when the runtime compiles.
`settleInitial(state, context)` can resolve installed geometry against the
shared initial snapshot after all systems have created their state.
Use `W.spatialFields.define(spec, read)` to publish a custom scalar,
vector, or categorical field. The callback receives the projected
`point`, the regular query context, and an `explain` flag. Return a
regular query result with an optional `source` record for provenance.

A tick context exposes the world, peer state, shared
queries, input values, `emit(kind, detail)`, and a seeded `random(key)`.
Pose providers can also implement `poseEntities(state)` to enumerate all entity
IDs whose pose they can override or suppress in that state. The hook must return
an iterable and accept `undefined` before initialization. The query engine can
then update those entities and their attachments between snapshots. A provider
with only `pose` uses the per-snapshot index.
Load custom factories through the CLI's existing `ink-studio.config.js`
`load` hook when reading their checkpoints in a separate process.

Rill's revision and spatial lookup contracts inspired the query snapshots and
stable selectors. Frontier's path edits and Ink's state/action/query separation
inform the authoring and simulation interfaces. The implementation uses Ink
Studio's own data and solver primitives with the JavaScript standard library.

See [live world scaling](world-scaling.md) for the benchmark commands and results.

## Persistent interactables

`KIT.world.interactions.create({id, interactables, realize})` owns a
place's durable interaction state and timers alongside its published
world revision. Define stable interactable IDs with JSON initial state
and named actions. `breakable({id, point, integrity})` provides `hit` and
reports the remaining integrity. `latch({id, point, ticks})` provides
`press`. A positive duration activates the latch and schedules a reset.
Pressing again restarts that timer. A zero duration makes it toggle.
Both helpers accept cue names to select host effects.

A custom action receives `{state, states, revision, point, actor, args,
tick, timer}`. Its synchronous handler returns null to decline, or
`{state, timers?, cue?, detail?}` to apply the action. State, actor, args,
and detail use JSON data. An optional `validate(state)` can check the
initial, restored, and proposed state. Named timers use relative delays.

```js
actions: {
  strike({ state, actor }) {
    if (state.open || !actor?.tool) return null;
    return {
      state: { ...state, open: true },
      timers: { reset: { after: 90, action: 'reset' } },
      cue: 'gate-open'
    };
  },
  reset({ state, timer }) {
    return timer === 'reset' && state.open
      ? { state: { ...state, open: false }, cue: 'gate-close' }
      : null;
  }
}
```

Use `timers: {reset: null}` to cancel a timer, or write the same name to
reschedule it. A timer can pass JSON `args` to an action on the same
interactable. The host advances the absolute scene clock with
`await interactions.advance(tick)`. Timers run in deadline, interactable
ID, and timer ID order. Ticks without actions keep the current world
revision. `advance(tick, {limit})` defaults to at most 1024 due actions
per call. A result with `complete: false` can be continued by advancing
to the same target again.

The synchronous or asynchronous `realize(next, before)` callback
builds a revision from the proposed `next.states`. `next.event` describes
the proposed action, and is null for initial publication or restore.
Use a private [biome revision builder](procedural.md#biome-revisions) here
to derive colliders, navigation, and packed splats from the same state.
Read `interactions.current()` as the publication boundary. It switches
state, clocks, and the finished revision together. An error leaves the
last completed snapshot available, including any timer that was due.
Actions and timer advancement are serialized. A caller can supply
`expectedSequence` to `dispatch(id, action, {actor, args, expectedSequence})`
so a repeated command based on an old snapshot returns null.

`onEvent((event, snapshot, before) => …)` subscribes to successful
actions and returns an unsubscribe function. Each event carries the
world ID, sequence, tick, target, action, cue and any authored XYZ point
or JSON detail. Listeners run synchronously after publication. Their
errors are available in the action's `errors` array. Use the same cue
for particles, audio, and animation. Keep presentation effects outside
the durable world revision.

`checkpoint()` returns the JSON state, sequence, local tick, and pending
timers. On a fresh controller, `await restore()` publishes the initial
world, or `await restore(saved)` rebuilds the saved world. Restore
leaves the event stream quiet. Pass `checkpoint` as a [place payload
callback](portals.md#step-and-save-places) to keep these records on
departure. The host can advance the interaction clock only while the
place is active, or drive it on a background update schedule.

The [interactable locks example](../examples/interactable-locks.js)
ties a breakable wall and timed gate to one traversal graph. Its debris
uses splat samples from the wall that the committed revision removed.

## Character traversal and follow cameras

`KIT.world.characters.create({tuning, selectMode, modes, allowSupport})`
is an optional Y-up capsule solver. It uses the same support, signed
clearance, and medium queries as the rest of the world. A host can supply
`{supports(x, z, low, high), clearance(point, radius), mediumAt(point)}`
or use `characters.fromBiome(frame)` with a prepared biome frame. The
biome adapter allows a small configurable `supportPadding` search when
a conservative field requires extra clearance above a support.

Create a JSON actor with `controller.state({position, velocity, …})`.
Position is the center of the capsule. The controller preserves additional
JSON fields such as inventory. Call
`controller.step(actor, {move, vertical, jump, climb}, dt, world)` with
seconds and a world-space XZ move input. Swimming uses the vertical input,
with jump also available as an ascend button. Jumping from the ground
uses a button press edge. Set `climb: false` to disable the automatic
climb from the waterline onto a reachable, clear ledge.

Set `tuning.flatBottom: true` for a platformer-style sole. The controller
keeps the configured radius and overall height and samples support across the
flat footprint. It can land, stand and jump with its center past a ledge
while part of its foot still overlaps. The shape still has a rounded head.

The reported movement includes the next `actor`, swept `segments`,
`events`, and the body and eye media. The defaults switch between
`ground`, `air`, and `swim`, with independent swim-entry, swim-exit,
and eye probe heights. The swim solver adds the sampled XYZ current.
Tune the body dimensions, acceleration and speed, jumping and gravity,
water response, step height, ledge reach, and substep size. The controller
exposes its resolved `tuning` for inspection.

`selectMode(context)` can choose a custom mode. Return the natural mode
for the default behavior. Each custom mode receives the same actor, input,
medium, eyes, support, and timestep context. Return a `velocity` and an
optional JSON `actor` patch. The controller still applies its collision
sweep and owns position, velocity, mode, and jump-button state.
`allowSupport(actor, support, world)` can reject a support by tag or
apply a host-specific rule.

```js
const controller = KIT.world.characters.create({
  tuning: {walkSpeed: 3, climbHeight: 0.6},
  selectMode: ({input, natural}) => input.glide && natural === 'air' ? 'glide' : natural,
  modes: {
    glide({actor}) { return {velocity: [actor.velocity[0], -0.8, actor.velocity[2]]}; }
  }
});
```

`KIT.world.cameras.follow({tuning, stable})` creates a separate,
renderer-independent rig. Call `rig.start(actor)` and
`rig.step(state, actor, dt, {yaw, pitch, focus, clearance})`. Orbit inputs
are relative angles in radians. The rig steadies the focus inside a
vertical jump window and follows sustained rises, drops and swimming
at configurable rates. A custom `stable(actor)` can include other
movement modes. Supply a signed clearance query to shorten the camera
arm at an obstacle and ease it back out after the obstruction.

```js
const movement = controller.step(actor, input, dt, currentPlace.queries);
const travel = await controller.cross(session, 'garden-door', movement, {camera: camera.pose});
actor = travel?.actor ?? movement.actor;
camera = travel?.arrival
  ? rig.handoff(camera, travel.arrival)
  : rig.step(camera, actor, dt, {clearance: currentPlace.queries.clearance});
renderer.render(session.current().asset.world, {camera: {pose: camera.pose}});
```

`cross` checks the actual motion segments against a walk or drop link.
It returns null if the actor misses the opening, or reports `crossed`
or `blocked`. A blocked result keeps the actor on the source side.
For a successful crossing, use the destination's queries on the next
step. `rig.handoff` adopts the arrival camera pose and preserves the
mapped orbit frame. Use the same method with a fade arrival to reposition
the rig at the named anchor.

The [headless canal example](../examples/canal-traversal.js) follows a
traveler from a dry bank into the water, out over a ledge, and through a
rotated doorway.

# Acoustic queries

Add an `acoustics` system to a headless world. Its `layout` binds the
`acoustic-layout` field of an existing ventilation or enclosed-water
system. The field shares room bounds, endpoints, aperture positions and
effective opening fractions. A clearance-controlled hatch uses the same
open fraction for ventilation and sound. Vents, fans and pressure can make
airflow directional. Acoustic transmission through an aperture is undirected.

```json
{
  "kind": "acoustics",
  "config": {
    "layout": "air/acoustic-layout",
    "sourceLevelDb": 60,
    "thresholdDb": 38,
    "openings": {
      "hatch": { "openLossDb": [0.1, 0.35, 1.2], "closedLossDb": [18, 32, 52] },
      "vacuum-lock": { "sealed": true }
    }
  }
}
```

The opening table overrides acoustic properties by ID. `sealed` removes the
acoustic connection when the aperture is fully closed. Other closed openings
leak according to their three-band loss. The base room and opening systems
can put the mouth at an explicit `at` point. The acoustic entry can refine
that point or give the two sides separate `fromAt` and `toAt` positions.
Inferred positions use the room bounds or the opening's known gate position.
Enclosed water also constrains the mouth to the authored sill and crown.

## Query an emitter from a listener

Pass the listener as the query target and the emitter as `args.from`.
Both support XYZ and entity/socket selectors. A ventilation layout also
accepts outdoor points in its `outside` reservoir. Use `fromRoom` or
`toRoom` to select a different authored exterior reservoir.

```js
const read = run.query().probe("acoustics/audible", { entity: "listener" }, {
  from: { entity: "beacon", socket: "speaker" },
  sourceLevelDb: 62,
  thresholdDb: 36
});
if (read.status === "ok" && read.value.audible) {
  const { bands, apparentSource, direction, delaySeconds } = read.value;
  // Supply band gains, position, direction and delay to the host's audio mix.
}
```

The report includes the estimated level, linear amplitude gain, propagation
delay, distance and high-frequency loss relative to the low band
(`muffleDb`). `apparentSource` is the listener-side mouth of the last
opening, or the emitter when they share a direct path. The result reports
`audible`, `attenuated`, or `blocked` separately from the query status.
An unresolved endpoint reports `missing` or `outside`.

Use the same field in [agent activity conditions](agent-decisions.md).
For example, test `{ "path": "/audible", "value": true }` at the agent
with `args.from` set to a beacon. A contact sound event's `at` position
also works as an emitter. The query accepts a separate source level and
threshold for each sound or listener.

`trace acoustics/path` explains the route, including its apertures, their
fractions, medium segments and losses. Add `details: true` to the probe
arguments for the same path data. `band` chooses the route and the frequency
band used for the threshold. It defaults to `mid`. All three gains refer to
the selected route.

## Media, scale and cost

`metersPerWorld` sets physical scale. `referenceDistance` is the distance
in meters at which `sourceLevelDb` applies. Route selection minimizes the
chosen band's propagation loss plus `routeDistanceDb` per meter. The
reported gain then includes distance spreading along that route. This is a
single-path portal estimate with straight segments inside each room.

An enclosed-water layout supplies its live water levels automatically.
A ventilation layout can add an enclosed-water `acoustic-layout` to its
`media` list. Chamber water is clipped geometrically. Additional typed
category fields or medium/water records are sampled along each segment. For
sampled fields, `mediumStep` sets meters between samples, capped at 24
samples per segment. Regular media are `air`, `water`, and `vacuum`.
`mediumProfiles` can add named profiles with `speed` (m/s), three-band
`loss` (dB/m), three-band `interfaceLoss` (dB), and `blocked`.

The query caches room geometry, portal links and up to 24 listener searches
per acoustic state. A hatch change invalidates route costs and reuses room
links while media stay unchanged. Fields with arbitrary sampled media
are evaluated against their own world snapshot. Audio hosts can reuse a
single `run.query()` when mixing a listener's emitters.

```sh
ink-studio trace examples/world-acoustic-hatch.json acoustics/path --entity listen-post --args '{"from":{"entity":"beacon","socket":"speaker"}}' --ticks 0
ink-studio trace examples/world-acoustic-hatch.json acoustics/path --entity listen-post --args '{"from":{"entity":"beacon","socket":"speaker"}}' --ticks 8
ink-studio trace examples/world-acoustic-hatch.json acoustics/path --entity listen-post --args '{"from":{"entity":"beacon","socket":"speaker"}}' --ticks 16
node scripts/benchmark-acoustics.js
```

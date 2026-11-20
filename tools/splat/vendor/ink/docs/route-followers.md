# Route followers and events

`K.anim.route(path, options)` samples vehicle poses and event times from an
arc-length path. It works with SDF/splat models, rigid instances, meshes, or
plain simulation data. It does not add geometry or require a renderer.

```js
const path = K.anim.path(points, { closed: true });
const route = K.anim.route(path, {
  speed: 9,
  acceleration: 3,
  sections: [{ from: 4, to: 12, speed: 2.2 }],
  stops: [{ at: 0, duration: 3 }],
  bank: { gain: 3, limit: 0.35, lookAhead: 0.5 }
});
const cars = route.vehicles(time, { count: 5, spacing: 0.94, wheelbase: 0.47 });
for (const car of cars) {
  if (car.active) draw.model(carModel, car.p, { matrix: car.matrix });
}

// Arm the next reachable break at least 0.7 seconds ahead. Querying does not
// move the train. Use the returned time as the physics handoff time.
const breakEvent = route.nextEvent(time, breakSites, { lead: 0.7 });
if (breakEvent) {
  const tail = route.nextEvent(breakEvent.time - 0.00001,
    [{ at: breakEvent.at }], { offset: 4 * 0.94 });
  const launch = route.vehicle(tail.time, { offset: 4 * 0.94 });
  // launch.p, launch.matrix and launch.velocity seed the detached car.
}
```

See [the renderable loop example](../examples/route-followers.js). Render a
frame with `node cli/ink-studio.js render examples/route-followers.js --t 3`.

## Path and frame contract

Supply a path with positive finite `length` and `at(distance)` returning
`{ p: [x, y, z], tan: [x, y, z] }`. `K.anim.path` provides this contract.
Distances are world units and times are seconds. Keep the path immutable
for the lifetime of the follower. Recreate the route when editing its shape.

The default `orientation: 'transport'` carries the up axis through inversions.
It distributes residual twist around a closed loop so the seam has no roll
jump. `orientation: 'upright'` suits roads, railways and conveyors that should
track world up. It falls back toward the transported frame near vertical.
`up` defaults to `[0, 1, 0]`. Curves should have continuous positions and
nonzero tangents. Smooth the path itself to avoid sharp direction changes.

`frame(distance)` returns `p`, `tan`, `right`, `up` and `matrix`. Matrices are
row-major with local right, up and forward in their columns. `bank` is a
constant in radians, a `(distance, frame) => radians` callback, or automatic
controls `{ gain: 1, limit: 0.5, lookAhead: 0.5 }`. Automatic banking measures
the signed turn ahead of the current tangent and caps roll in radians.

## Motion and vehicles

| Option | Meaning |
| --- | --- |
| `mode` | `'loop'` for closed paths, `'once'` for open paths by default. `'pingpong'` runs an open shuttle in both directions. Loop mode requires a closed path. |
| `speed` | Positive finite world units per second, or `(distance, frame) => speed`. Default 1. This is an authored speed field, not a gravity solver. |
| `sections` | `{ from, to, speed }` caps. Use increasing distances in `[0, length]`. Overlaps use the lowest cap. Split a section across the seam into two sections. |
| `acceleration` | Positive acceleration/deceleration bound. Default Infinity. The timing table brakes ahead of slower sections and stops. |
| `stops` | Distinct `{ at, duration }` stations. Each forces zero speed with a nonnegative dwell. A closed path's endpoint is its start station. Shuttle endpoint dwells occur once per return cycle. |
| `step` | Maximum frame/timing sample spacing. Default 0.1 world units. Smaller spacing better resolves speed fields and curvature. |
| `maxSamples` | Construction budget, default 30,000. Range 4–200,000 including speed-section and stop nodes. |

`state(time)` returns `distance`, cumulative unwrapped `travel`, nonnegative
`speed`, `direction` (+1 or -1), `lap`, `stopped` and `finished`.
`distanceAt(time)` and signed `speedAt(time)` are convenience queries.
`duration` is the forward timetable, including station waits. `period` is
the repeating cycle, including the return for a shuttle. Open one-way routes
clamp before the start and after the finish with zero endpoint speed.
Looping routes also support negative time and arbitrary timeline scrubbing.

`vehicle(time, { offset: 0, wheelbase: 0 })` adds a frame, world `velocity`
and an `active` flag to the motion state. Positive offset places a car behind
the head in the current direction of travel. `wheelbase` aligns the vehicle
with the chord between two points on the track. Open-route offsets outside
the path are inactive with clamped positions. A shuttle reverses its offset
direction at a terminus. Use zero offsets for a single shuttle or explicitly
swap the lead end of a train when reversing.

`vehicles(time, { count: 1, spacing: 1, offset: 0, wheelbase: 0 })` returns
up to 10,000 vehicles at fixed **arc-length** spacing, including across a
closed seam. Independently moving cable cars, boats or traffic can instead
sample `vehicle(time + phase)` with independent phase offsets.

`timeAtDistance(distance, { departure: false })` inverts the forward timetable.
The default is arrival at a station. Set `departure: true` to include its dwell.
The terminal distance `length` returns the end time even on a closed path.

## Pure event queries

Events are plain `{ at, id?, ...payload }` records in route distance units.
Optional IDs must be distinct. Up to 10,000 definitions are accepted.

- `nextEvent(time, events, { lead: 0, offset: 0 })` finds the earliest crossing
  strictly after `time + lead`, or returns `null` after an open route is exhausted.
- `eventsBetween(from, to, events, { lead: 0, offset: 0, maxEvents: 10000 })`
  returns ordered crossings in `(from + lead, to]`, across skipped laps.
  Adjacent intervals do not duplicate a crossing. Backward intervals return `[]`.
- Both return the original payload plus `time`, cycle `lap`, `direction` and
  `wait` from the query start. `offset` targets a trailing car at the same site.
  Shuttle events include reverse crossings and one arrival at each terminus.

These methods do not dispatch callbacks or change motion. The caller owns
playback state and physics. Query intervals once during forward playback,
then dispatch their records. Seek backward by resetting application effects
or rebuilding them from the desired interval. Event output is bounded and
throws before returning partial results when `maxEvents` would be exceeded.

Construction precomputes geometry and timing. Ordinary pose queries use
binary searches and local frame interpolation. Event queries inspect the
definitions and requested crossings without stepping every intervening frame.

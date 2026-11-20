# Places and travel links

`KIT.world.portals` provides a headless session for travel between named
places. A host supplies place preparation, feeds actor movement into the
session, and decides when to step simulation. Use the same primitives with
hand-built dioramas, streamed chunks, or biome revisions.

## Publish a place

A place has a stable `id`, named `anchors`, and a `prepare(context)` callback.
Each anchor has a world-space `origin`, a `normal` pointing toward the
front of the opening, and an optional `up`. The session makes an
orthonormal frame from these axes.

`prepare({id, anchor, state, previous, time, signal, reason, link})` returns a
payload, synchronously or asynchronously. Use `anchor.origin` to choose
chunks around the arrival. `reason` is `enter`, `preview`, or `restore`.
`anchor` is null when entering without a named anchor or restoring.
`state` is the place's saved JSON value and `time` is its local elapsed
time in seconds. For a link within the active place, `previous` is the
active payload and can be returned if it also serves the destination.
The session promotes the prepared payload on successful travel. It
aborts superseded requests and disposes discarded payloads.

A payload can provide these fields and callbacks.

| Member | Purpose |
| --- | --- |
| `world` | The packed splat world to show through a doorway or render after arrival. A headless host can supply its own payload fields. |
| `canArrive(actor, link)` | An optional synchronous clearance check in destination coordinates. Return false to keep the source active. |
| `checkpoint()` | An optional synchronous callback returning the current place's JSON state. The session uses it for saves and link conditions. |
| `step({id, dt, time, active})` | An optional synchronous simulation callback. `dt` is the duration in seconds and `time` is the local clock at the end of the step. |
| `prepareArrival(context)` | An optional callback on a retained payload. It can prepare chunks around another arrival anchor while the place keeps ticking. It accepts the same context as `prepare`, with the live payload in `previous` and its current checkpoint in `state`. |
| `dispose()` | A synchronous release callback. The session releases discarded payloads, paused payloads on departure, and live payloads when the session ends. |

## Step and save places

Set `tickPolicy: 'pause'` to save and release the payload on departure.
This is the default. Set `tickPolicy: 'continue'` to keep a visited
place's live payload and simulate it while the traveler is elsewhere.
Returning to a retained place reuses that payload. The host calls
`session.step(dt)` with seconds. Each step advances the active place
and the retained places in ID order. A place prepared only as a preview
starts ticking on its first entry.

`session.place(id)` reports the named anchors, policy, local time, and
status. `active` is the current place, `away` is a retained place, and
`inactive` covers paused and unvisited places. `session.linksFrom(id)`
lists the declared outgoing links.

`session.checkpoint()` returns `{place, saved, clocks?, away?}`.
`saved` contains each place's JSON state, including current checkpoints
from retained places. `clocks` contains elapsed seconds by place ID and
`away` lists the retained place IDs. Call `await session.restore(save)`
on a new session to restore the active place and resume the retained
places. A failed load leaves the session empty. The format also accepts
older `{place, saved}` checkpoints. Save the actor and camera separately
if the experience needs their exact poses on reload.

## Use the travel lifecycle

Call `session.prepare(linkId)` to preload the destination, or let
`session.approach(position, { actor })` preload a nearby doorway. Preparation
resolves to the payload, rejects on load failure, and resolves to null if
superseded. `session.cancelPreparation(linkId)` aborts an unused preview and
releases its payload. Omit the ID to cancel the current preview. The session
keeps previously visited places configured to continue ticking.

For streamed destinations, hold a [chunk interest](procedural.md#shared-chunk-scheduling)
on the prepared payload. Wait for its required landing keys during
`prepare`. Expand that interest around the traveler in `onCross` and
close it when the payload is disposed. Overlapping keys stay resident
through promotion when they fit the new budget.

Use `session.checkArrival(linkId)` to inspect preparation. It returns a
record with `link` and one of three statuses.

| Status | Meaning |
| --- | --- |
| `unprepared` | This link has no pending destination. |
| `loading` | The destination is still preparing. |
| `prepared` | The destination payload is available. |

Pass `{ previous, actor, camera, radius }` as the second argument to also
check a proposed walk or drop. For a fade, pass `{ actor }`. The check can
report `locked` if the link's gate fails or `outside` if the proposed move
misses the trigger. With a prepared destination, it returns `ready` or
`blocked`, plus the proposed destination `actor`, `camera`, and swept
`crossing` where applicable. This check leaves the active place unchanged.
The session checks the gate and clearance again at handoff.

A link's optional `transfer({ actor, arrival, link, crossing, source,
destination })` decides what travels. `actor` is the original traveler,
`arrival` is the default mapped traveler, `source` is the current place
handle, and `destination` is the prepared payload. Return the complete JSON
actor with a finite `position`. The session moves the mapped camera with any
position adjustment, then passes the resulting actor to the payload's
`canArrive` callback. Keep both callbacks synchronous and free of side
effects so a host can check an arrival repeatedly.

```js
const gardenDoor = {
  id: 'garden-door',
  from: { place: 'court', anchor: 'arch' },
  to: { place: 'garden', anchor: 'arch' },
  aperture: { halfWidth: 1, halfHeight: 1.45 },
  transfer({ arrival }) {
    const { localProjectiles, ...traveler } = arrival;
    return traveler;
  }
};
```

Use `session.onCross(listener)` to bind sound, animations, or quests to
successful walks, drops, and fades. It returns a function that unsubscribes
the listener. The event includes the `source` place, new `place`, `link`,
arrival `actor` and `camera`, and `crossing` when applicable. The
destination is active when listeners run and the outgoing payload remains
available through the callbacks. `sourceDisposition` tells callers whether
that payload is being `released`, `retained` for background ticking, or
`reused` as the active payload. Listeners run synchronously and once per
crossing. A thrown listener or disposal error is reported in the successful
arrival's `errors` array.

```js
const unsubscribe = session.onCross(({ link, place, actor }) => {
  audio.play('door', actor.position);
  animation.play(actor.id, 'arrive');
  quests.visit(place.id, link.id);
});
```

## Walk through a door

```js
const { KIT: { world: { portals } } } = require('@shapeshift-labs/ink-studio').load();
const session = portals.create({
  places: [
    { id: 'court', anchors: { arch: { origin: [0, 1.5, 0] } }, prepare: loadCourt },
    { id: 'garden', anchors: { arch: { origin: [8, 1.5, 4], normal: [1, 0, 0] } }, prepare: loadGarden }
  ],
  links: [{
    id: 'garden-door', from: { place: 'court', anchor: 'arch' },
    to: { place: 'garden', anchor: 'arch' },
    aperture: { halfWidth: 1, halfHeight: 1.45, shape: 'rect' },
    requires: { path: '/actor/hasKey', value: true }
  }]
});
await session.enter('court');
const approach = session.approach(actor.position, { actor, distance: 10 });
await approach?.ready;
const preview = session.view('garden-door', actor);
```

Use `approach` as the actor moves to keep the nearest eligible front-facing
door prepared. A link is directed. Add a second link with its own anchors
and conditions for a return route. A `requires` condition uses the
[world query condition format](headless-worlds.md) and can address `/actor`,
`/state` (the source place's checkpoint), and `/time` (the source
place's clock). An optional `open({active, actor, link})` callback can
inspect the live payload. When both gates are supplied, both must pass.
The session checks gates when offering a preview, showing it, and
attempting travel. It rechecks them before handing off to the destination.

```js
renderer.render(session.current().asset.world, { ...frame, portal: preview });
const camera = renderer.cameraPose(session.current().asset.world, frame);
const crossed = await session.cross('garden-door', {
  previous: positionBeforeMovement, actor, camera, radius: 0.2
});
if (crossed) {
  actor = crossed.actor;
  frame.camera = { ...frame.camera, pose: crossed.camera };
}
```

`cross` tests a sweep of the actor's center from `previous` to
`actor.position` against the bounded aperture. The radius reserves
clearance around the center. The arrival preserves the distance traveled
past the plane, rotates supplied `velocity`, `forward` and `up`, and maps
the supplied camera pose through the same frame. By default, additional JSON
actor properties carry forward. A null result leaves the source active. Keep your
actor on the source side while a load or clearance check is unresolved.
A host can also use `portals.doorway({from, to, halfWidth, halfHeight, shape})`
directly for `hit`, `point`, `direction`, or `camera` operations.
The optional [character and camera rig](headless-worlds.md#character-traversal-and-follow-cameras)
can submit its swept motion segments to the session and carry the mapped
camera frame into the next place.

### Render the view

Pass `session.view()` to `renderer.render(world, { portal })`. To render
a portal without a session, supply `{ opening, destination }`. Build
`opening` with `portals.doorway()`, and use the source and destination
anchors' normals and up axes to set their orientation. WebGL supports one
live view per render, rectangular and elliptical openings, and perspective
and orthographic cameras. It supports tilted or horizontal openings along
with upright doors. Author the frame geometry as part of the source scene.

The renderer evaluates the aperture on each camera ray. Foreground splat
coverage and opaque edge sprite pixels on the near side of the source
plane occlude the opening. Thin, tilted splats can straddle the plane.
Their fragments are tested using depth estimated from the projected
Gaussian, so a splat can cover part of the opening while leaving the
rest visible. Occlusion uses a coverage threshold for soft splats.

The destination renders with the mapped camera and its own palette and
environment. Splat fragments and edge sprite pixels on the camera side of
the arrival plane are clipped. Destination water optics begin at the
arrival plane. Set `destinationFrame` on the view for destination render
options such as `time`. The same portal view works on the canvas and when
rendering to a GPU target for the [transition compositor](transitions.md#render-ink-studio-worlds-directly-into-a-transition).

## Drop through a hatch

A link with `mode: 'drop'` uses the same swept crossing as a door and
arrives at the destination anchor. Give a horizontal hatch a source
`normal: [0, 1, 0]` and `up: [0, 0, 1]` to trigger when the actor falls
through from above. The trigger defaults to a circle of radius 1. Use
`radius` to size it or supply `aperture` for custom half extents and shape.

```js
const drop = {
  id: 'cellar-hatch', mode: 'drop',
  from: { place: 'court', anchor: 'hatch' },
  to: { place: 'cellar', anchor: 'landing' },
  requires: { path: '/state/hatchOpen', value: true }
};
const result = await session.cross(drop.id, { previous: positionBeforeMovement, actor, camera });
```

Drop links preserve velocity and orientation. A supplied camera moves
by the same offset as the actor. You can prefetch the landing with
`session.prepare(drop.id)`. Drop links use the source render until
handoff. A separate door, drop, or fade link can provide a return trip.

## Fade at a ring or pool

A link with `mode: 'fade'` uses a cylindrical trigger around its source
anchor. `radius` defaults to 1, vertical `height` tolerance to 0.7, and
`duration` in seconds to 0.8.

```js
const travel = session.fade('pool', { actor });
const step = travel?.advance(dt);
if (step?.arrival) actor = step.arrival.actor;
renderer.render(session.current().asset.world, { ...frame, fade: step?.opacity ?? 0 });
```

The playback reports `out`, `hold`, `in`, `done`, or `failed`.
It holds at full black until the destination is ready, places the actor at
the arrival anchor, and reveals the new place. On preparation failure or
a blocked arrival, it reveals the original place and returns the error.
`arrival` is available after handoff. Bind one-time effects with
`session.onCross`. The host can feed opacity into its own compositor,
audio, or transition presentation.

See [the headless courtyard and lantern garden](../examples/place-portals.js)
for two-way doors, a separate fade link, and a garden that keeps time
while you're away.

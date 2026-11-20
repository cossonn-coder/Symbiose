# Cloth Review

Cloth Review uses the existing `K.cloth` grid, splat draw path, and XPBD
stretch, shear, and bend constraints. A review run starts from the currently
displayed grid pose and keeps that pose available for a before/after comparison.
It uses the panel's rest distances as the cloth's lengths.

## Author regions

Give every grid point a role in row-major order.

- **Pin** anchors a seam or attachment to its captured position or a supplied
  moving pin target.
- **Free** follows XPBD gravity, wind, collisions, and cloth constraints.
- **Protected** retains the captured position even if the pin target moves.
  Seams remain connected to neighboring free cloth.

```js
const cape = K.cloth(builder, {
  nu: 15, nv: 17,
  at: [-0.67, 2.16, 0.31], u: [1.34, 0, 0], v: [0, -1.60, 0.17]
});
const review = K.cloth.review.create(cape);
const regions = review.regions().slice();
regions[3 * cape.nu + 7] = 'protected';
review.setRegions(regions);
```

The default pins the top row and leaves the rest free. Editing regions ends
the current preview so the next run can capture the new setup. The example
shows the regions on both cloth views and the editable grid.

## Capture and simulate

```js
// Supply the current world-space XYZ grid, e.g. from the displayed puppet pose.
review.start(displayedPose, {
  sourceTime: playhead,
  wind, spheres,
  pinAt: (index, capturedPoint, elapsed) => capturedPoint
});
review.advance(elapsed);
const before = review.sample(elapsed, { before: true });
const after = review.sample(elapsed);
```

`start` takes a flat XYZ array or typed array. Frame zero matches that pose.
Optional simulation inputs include `wind`, `spheres`, `sdf`, gravity, and a
moving `pinAt` callback. Protected points stay fixed at their captured
positions. The solver uses fixed steps and records grid poses for scrubbing.
Call `advance` with absolute elapsed simulation seconds. Call `sample` to
seek through captured frames. The review leaves native stage cloth and its
running solver independent.

The default settle policy requires peak point speed at or below 0.04 world
units per second for 0.45 continuous seconds, after at least 0.6 seconds of
simulation. A renewed movement resets the quiet interval. At an unsettled
time limit, the captured frames remain available for review.

## Bake and replay

```js
if (review.state().phase === 'settled') {
  const take = review.bake();
  const json = JSON.stringify(take);
  const replay = K.cloth.review.clip(JSON.parse(json));
  cape.drawPose(stage, replay.sample(time));
}
```

Bake is an explicit action available after settling. The portable JSON take
stores fixed-rate grid positions, the region roles, and the source playhead.
Load it into a matching panel and play it through the original cloth splat
draw path. Playback uses the saved grid poses and interpolation. Hold the
character at `take.sourceTime` for the same before/after framing.

## Try it

```sh
node cli/ink-studio.js cloth-review examples/cloth-review.js --pose 0.9
node cli/ink-studio.js cloth-review examples/cloth-review.js --pose 0.9 --bake cape.json
```

For the interactive demo, [build and serve the browser bundle](pose-blocking.md#try-the-browser-example)
and open `http://localhost:8080/examples/cloth-review.html`. Scrub to the
source pose, paint the grid, and choose **Preview from current pose**.
When the preview settles, choose **Bake settled take**. Scrub, replay, or
download the bake.

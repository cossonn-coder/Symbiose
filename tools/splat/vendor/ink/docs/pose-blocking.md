# Pose blocking and reuse

Ink uses the same pose channels for the pose shelf, keyframes, and puppet
playback. A blocking timeline produces two standard `K.anim.clip` objects.
`held` displays the previous landmark until the next one. `clip` interpolates
between the same landmarks using each key's outgoing easing.

```js
const shelf = K.anim.poseShelf.create({ pairs: [['leftArm', 'rightArm']] });
shelf.save('ready', { leftArm: { rot: [0, 0, -10] }, rightArm: { rot: [0, 0, 10] } },
  { name: 'Ready' });
shelf.save('signal', { rightArm: { rot: [-15, 0, 140] } }, { name: 'Signal' });

const blocking = K.anim.poseBlocking.create(shelf, {
  duration: 1.8,
  fps: 12,
  keys: [
    { time: 0, pose: 'ready' },
    { time: 0.4, bias: 0.7, name: 'Lift' },
    { time: 1.2, pose: 'signal' }
  ]
});

// In the pose callback passed to K.puppet:
blocking.held.sample(time, puppet.pose);
```

Landmark times are seconds. A breakdown's `bias` is the fraction from the
preceding story pose toward the next story pose. In this example, Lift occurs
one third of the way through the beat and is already 70 percent of the way
toward Signal. Each breakdown uses the surrounding story poses, even when
there are several breakdowns between them. Use `blocking.markers` for names and
times in a host timeline. Compile again after editing keys or shelf assets.
Compiled clips keep their own snapshot.

## Apply a shelf pose

```js
const stamp = shelf.apply('signal');
const base = blocking.clip.sample(0.6);
const blend = shelf.apply('signal', { base, weight: 0.5 });
const leftArm = shelf.apply('signal', {
  base, parts: ['leftArm'], mirror: true
});
shelf.save('left-arm-signal', leftArm, { name: 'Left arm signal' });
```

`parts` names the destination parts. Include both the upper arm and forearm
to apply an entire two-part limb. Parts outside the scope retain their base
pose. Mirroring swaps paired parts and reflects their transforms across
local X. Unpaired parts reflect in place. Use symmetric rest pivots for
mirrored puppets. The shelf handles numeric and numeric-vector channels.
It reflects `pos`, `rot`, `turn` and `twist`; other channels retain their
values. Euler rotation blends take the shortest angular path per axis.
Missing channels use their neutral value during blends. Use `shelf.list()`
to serialize the stored poses and pass them back as `poses` when creating a
shelf. `shelf.save()` copies the input and `shelf.apply()` returns an independent
pose that can be edited or keyed.

## Review silhouettes

Expose the compiled timeline as `world.poseBlocking` and sample its clip in
the world's normal animation callback. The review uses the scene's regular
pose evaluation, the atlas camera, and the requested art resolution.

```sh
node cli/ink-studio.js pose-review examples/pose-blocking.js --w 96 --h 96 --directions 8
```

Open `color.png` and `silhouette.png` from the output folder. Rows correspond
to named story poses or breakdowns, and columns to the evenly spaced export
directions. `atlas.json` lists landmarks and reports silhouette pixel counts,
tile-local bounds, and whether the silhouette touches a sprite edge. Use the
same width, height, direction count, yaw, and pivot for review and export.
For a moving asset, `atlas --maps silhouette` exports the same mask for every
frame.

## Try the browser example

From the repository root, build the browser bundle and serve the workspace.

```sh
node -e 'const fs = require("node:fs"); fs.mkdirSync("dist", { recursive: true }); fs.writeFileSync("dist/ink-studio.browser.js", require("./index.js").bundle());'
python3 -m http.server 8080
```

Open `http://localhost:8080/examples/pose-blocking.html`. Click a landmark to
inspect it, switch between held and interpolated playback, or move the Lift
breakdown while adjusting its pose bias separately. The shelf previews full
and scoped poses. **Key pose** writes the preview to the example's timeline
at the playhead.

# Headless animation timeline

`K.anim.timeline.create` mounts a shot on an existing `K.puppet` and its
world. The primitive takes a native clip, a pose-blocking plan, or a clip
sequence. It uses the same pose callback for regular world playback and
headless frame sampling.

- **Block** samples held story poses and breakdowns. A plain clip holds the
  whole pose at its preceding keyed time.
- **Spline** samples the native interpolation and any sequence trims,
  timing curves, placement, and optional [Motion Layers](motion-layers.md).
- **Polish** adds accepted Motion Review corrections, keyed Motion FX,
  and placed cloth takes. Contacts and prop switches run in every stage.

Every lane uses seconds on the output clock. A sequence can use a compiled
pose-blocking plan directly as a source. Its named landmarks then follow
the same trims and retiming as keys and cues. Contacts, FX envelopes, and
cloth placements use authored shot times. Use the native FX stack to edit
an envelope in place. Build a new shot when replacing other definitions or
the source plan.

## Library

```js
const studio = require('@shapeshift-labs/ink-studio');
const { KIT: K } = studio.load();
const puppet = K.puppet(world, { parts });

const timeline = K.anim.timeline.create({
  world,
  puppet,
  sequence,                             // or clip, or blocking
  motionLayers,                         // timed override stack. Optional.
  contacts: contactSpec,                // sockets, contacts, and prop. Optional.
  fx: motionFx,                         // a stack allocated on the builder. Optional.
  cloth: [{ id: 'cape', panel: cape, take: savedBake, start: 2.2 }],
  review: { height: 3, probes },          // rest-space Motion Review probes. Optional.
  sprite: { width: 96, height: 96, directions: 8, fps: 12 }
});
world.animationTimeline = timeline;

timeline.set({ time: 1.4, part: 'head', loop: { start: 1, end: 2 }, direction: 2 });
timeline.set({ stage: 'spline' });      // retains the playhead, part, loop, and direction
const state = timeline.snapshot();
const { lanes } = timeline.report();

timeline.set({ stage: 'polish' });
timeline.focus(lanes.findings[0].id);
const atlas = studio.previewTimeline(world);
timeline.clearFocus();
```

`snapshot()` is JSON-safe and `restore(snapshot)` can reopen it on a
compatible shot. `timeAt(elapsed)` starts at the loop's in point when a
loop is set or advances from the playhead otherwise. `sample(time)`
returns the solved pose without drawing. `frame(time)` evaluates the same
pose, updates the world's splats, and returns the contact, attachment, FX,
and cloth state. Both accept a stage override and `before: true` for a
source comparison. Sampling and exporting leave the saved context intact.

The world and its animation systems should support seeking for headless
previews. A cloth take can be a decoded bake or the JSON from Cloth Review.
It is sampled in its recorded world space from the placement's start
time. Its final pose holds until another take begins on that panel.
An optional `before(time, puppet)` returns an authored grid pose for
earlier stages and comparisons. Without a callback, the captured first
frame serves as the before pose. Bake and place takes explicitly using
[Cloth Review](cloth-review.md).

Motion Review analyzes the solved Spline pose. Accept, mute, or remove
corrections through `timeline.motionReview()`. In Polish, accepted
corrections feed the existing contact and prop solvers so authored holds
and switch timings still apply. `focus(id)` jumps to the finding and its
part and opens a temporary loop. `clearFocus()` restores the prior
playhead, selected part, and loop. `previewTimeline` uses the directional
sprite atlas renderer, including the actual final and first poses for a
seam finding. The returned frame metadata records both preview time and
shot time.

## CLI

The [courier example](../examples/animation-timeline.js) includes story poses,
retimed keys and cues, a planted foot, a lantern handoff, FX, and a settled
cape take on the same timeline.

```sh
ink-studio animation-timeline examples/animation-timeline.js --state shot.json --stage block --at 1.4 --part head --loop 1,2 --direction 2
ink-studio animation-timeline examples/animation-timeline.js --state shot.json --stage spline
ink-studio animation-timeline examples/animation-timeline.js --state shot.json --stage polish --finding loop-pop --preview seam-before --before
ink-studio animation-timeline examples/animation-timeline.js --state shot.json --fix accept --preview seam-after
ink-studio animation-timeline examples/animation-timeline.js --state shot.json --finding off
```

The command prints a JSON report with the lanes and current context. Use
`--out report.json` to write it to disk. `--at` also reports the contact,
attachment, FX, and cloth state for that frame. `--state` preserves the
context and accepted corrections across invocations. `--fix mute`,
`--fix enable`, and `--fix remove` act on the focused finding.

`--preview` writes `color.png`, `silhouette.png`, and `atlas.json`.
It renders the playhead by default or samples the active loop when one is
set. Use `--frames 1` for the exact playhead, including a focused finding.
Output uses the shot's sprite dimensions unless `--w` or `--h` is set.
Directions are zero-based and use the shot's export yaw and direction count.

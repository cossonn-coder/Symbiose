# Motion Review

Motion Review samples a puppet's solved clip at equal time intervals. Mark
rest-space points on parts you want to track. Use hands and other extremities
for spacing and arcs, and mark sole points with `foot: true` to review drift
during inferred ground contact. The final and first poses are sampled
independently for looping clips.

```js
const review = K.anim.motionReview.create({
  clip,
  puppet,
  height: 3,
  fps: 24,
  ground: (x, z) => 0,
  probes: [
    { id: 'hand', label: 'Right glove', part: 'rightForearm', point: [0.57, 1.08, 0] },
    { id: 'foot', label: 'Left sole', part: 'leftBoot', point: [-0.25, 0, -0.1], foot: true }
  ]
});
world.motionReview = review;
```

`height` is the puppet's standing height in world units. The optional
`ground(x, z)` returns world Y or a non-finite value where there is no
support. Foot drift is an advisory result for slow, sustained movement near
the ground. Review the beat before accepting a fix for an intentional slide.

The analyzer uses the authored clip, its existing layers and follow-through,
and the puppet hierarchy. Per-frame procedural maps applied by the scene
after clip evaluation are outside the analysis. Run `create` again after
changing the source clip or probe definitions.

## Focus a finding

```js
const issue = review.findings.find(finding => finding.kind === 'foot-drift');
if (issue) {
  const focus = review.focus(issue.id);
  const sourceTime = focus.timeAt(elapsed);
  review.sample(sourceTime, puppet.pose, { sourceTime: true });
}
```

`focus.timeAt(elapsed)` repeats only the affected interval and its immediate
context. A loop-pop focus crosses from the tail to the beginning of the
clip. For loop pops, `focus.evidence` contains the exact source times of the
last and first poses for a ghost comparison. Other findings expose one
world-space path with evenly timed points for the affected probe.

## Apply and compare

```js
review.accept(issue.id);
review.sample(time, puppet.pose); // use this in the normal puppet pose callback
review.sample(time, {}, { before: true }); // compare with the source
review.focus(issue.id, { before: false }); // corrected evidence
review.setEnabled(issue.id, false); // mute while retaining the accepted layer
review.remove(issue.id);
```

Fixes become native additive pose layers with `phase: 'corrective'`. Accepting
a fix leaves the source keys intact. `review.layers()` provides the applied
layer definitions and their source clips for a host inspector.

- **Loop pop** eases a channel offset into the tail to meet the first pose.
  The layer closes the pose seam while keeping the original clip timing.
- **Spacing spike** redistributes nearby samples along the original path
  while keeping the ends of the correction window in place.
- **Arc kink** rounds a local corner with a bounded position correction.
- **Foot drift** holds the horizontal position of the first planted sample
  and eases out during release. The layer preserves the foot's vertical
  motion.

Path and foot corrections translate the marked part in its parent's space.
They suit authored part motion and use the existing puppet transforms.

## Try it

Print the findings, focus ranges, and evidence as JSON.

```sh
node cli/ink-studio.js motion-review examples/motion-review.js
node cli/ink-studio.js motion-review examples/motion-review.js --finding foot-drift --out drift.json
```

For the interactive demo, [build and serve the browser bundle](pose-blocking.md#try-the-browser-example).
Open `http://localhost:8080/examples/motion-review.html`. Select a finding,
play or scrub its focus loop, and use **Apply fix**, **Correction layer**,
and **Compare source** to review the change.

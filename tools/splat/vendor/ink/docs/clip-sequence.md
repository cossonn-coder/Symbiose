# Clip sequencing and retiming

A sequence places reusable Ink clips on one clock. Each instance owns its
source range, output duration, and timing curve. Edits return a new
sequence and leave the source clips and the earlier plan intact.

```js
let sequence = K.anim.sequence.create({
  clips: { walk, stop, wave }, // native K.anim.clip objects
  root: 'body',
  steps: [
    { id: 'stride-a', clip: 'walk' },
    { id: 'stop-a', clip: 'stop', in: 0.18, out: 0.9, duration: 0.8 },
    { id: 'wave-a', clip: 'wave' }
  ]
});
sequence = sequence.edit('stride-a', { out: 1.1, duration: 1.45, ease: 'in-out-sine' });
sequence.sample(time, puppet.pose);
```

Trims use source seconds. Omitting `duration` on a trim preserves the
instance's rate. Set `ease` to `linear`, `in-sine`, `out-sine`, or
`in-out-sine`. Clip layers and follow-through are evaluated at the mapped
source time. Time-changing presentation cues are returned as cues for the
host, with the sequence's instance timing driving the pose sampler.

`sequence.steps`, `sequence.keys`, and `sequence.cues` use the same output
time map. An edit maps the affected keys and cues within their source
range, then ripples all later instances by the duration difference. A cue
at a retained endpoint is included. Use `sequence.eventsBetween(from, to,
{ mode })` to dispatch cues in `(from, to]`, including across cycles.
Start from a small negative time to include a cue at time zero. Use
`sequence.arrange(steps)` to change order, add repeated sources, or remove
instances. Each instance needs its own ID.

After an edit, `sequence.change` contains a focus window with the changed
instance and nearby context. Sample `sequence.change.timeAt(elapsed)`
with Once playback to audition only that window.

## Handoffs and alignment

`sequence.handoffs` reports pose and velocity gaps, horizontal root
separation, and a continuity score for every adjacent pair. Velocity is
measured on the output clock, so retiming and easing affect the score.
The score assesses spatial continuity at the cut.

```js
const suggestion = sequence.suggestCut(0); // zero-based handoff index
if (suggestion) {
  console.log(suggestion.currentScore, suggestion.score, suggestion.out, suggestion.in);
  sequence = sequence.applyCut(0); // explicit edit of both instance trims
}
```

The search examines nearby frames and charges for moving the cut. It returns
`null` unless the continuity score improves enough. Playback keeps the
chosen cuts as authored. A suggested cut leaves both source clips intact.

- `sequence.align('source')` uses the recorded placement.
- `sequence.align('root')` moves each incoming root to the outgoing root on
  X/Z. It keeps the authored height and rotation.
- `sequence.align('foot')` matches a shared planted sole at the boundary.
  Supply `puppet`, standing `height`, and `feet: [{ id, part, point }]` on
  creation. Each point is in the puppet's rest space and its part belongs to
  the top-level root. Supply `ground(x, z)` for ground height, or use the
  default of zero. Ink samples the same sole on both sides of the cut and
  uses root matching when it cannot establish a stable shared contact.

## Playback

```js
sequence.sample(time, puppet.pose, { mode: 'once' });
sequence.sample(time, puppet.pose, { mode: 'loop' });
sequence.sample(time, puppet.pose, { mode: 'travel-loop' });
```

**Once** clamps at the final pose. **Loop** repeats with the specified
root held at its starting X/Z position. **Travel loop** adds the sequence's
net X/Z displacement on each wrap, keeping the within-cycle root path.
Both modes keep authored vertical motion. Use a matching start and end
body pose for a seamless traveling cycle.

## Try it

```sh
node cli/ink-studio.js clip-sequence examples/clip-sequence.js --handoff 0
node cli/ink-studio.js clip-sequence examples/clip-sequence.js --params '{"edit":{"step":"walk","duration":1.5}}'
```

For the interactive demo, [build and serve the browser bundle](pose-blocking.md#try-the-browser-example)
and open `http://localhost:8080/examples/clip-sequence.html`. Select an
instance to edit its timing, inspect the cue stamps, then play the changed
section. Use **Find cleaner cut** to inspect a candidate before applying
it. Switch the preview to **Stride cycle** to compare the three playback
modes.

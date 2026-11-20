# Motion Layers

Use timed overrides to combine performances on an Ink puppet. For example,
a base walk can keep driving the hips and legs while one layer lifts a
lantern and another turns the head and torso toward its light.

## Author a stack

```js
let motionLayers = K.anim.motionLayers.create({
  duration: walk.dur,
  sources: { lift, glance }, // native K.anim.clip objects
  parts: puppet.names,
  layers: [
    {
      id: 'lift', clip: 'lift', start: 0.2, end: 0.9,
      parts: ['jacket', 'sleeve-r', 'glove-r', 'lantern'],
      weight: [[0.2, 0, 'bezier', [0.25, 0, 0.4, 1]], [0.5, 1], [0.9, 0]]
    },
    {
      id: 'glance', clip: 'glance', start: 0.45, end: 0.82,
      parts: ['jacket', 'hood'],
      weight: [[0.45, 0], [0.63, 0.75], [0.82, 0]]
    }
  ]
});

const timeline = K.anim.timeline.create({ world, puppet, clip: walk, motionLayers });
timeline.set({ stage: 'spline', time: 0.63 });
const frame = timeline.frame();
```

A layer's `start`, `end`, and weight keys use shot seconds. Use a scalar
weight or keys written as `[time, weight, easing?, bezierHandles?]`.
Weights range from zero to one. The key's easing controls the segment that
follows it. A layer is inactive outside its window. Use zero-weight keys at
the ends for a smooth release back to the underlying motion.

Optional `in` and `out` trim the source clip in source seconds. The trimmed
range fits the window by default. Set `speed` to play at an explicit rate,
and `loop: true` to repeat the trimmed range. The source is sampled with
its own pose layers and follow-through.

With an explicit part list, each layer affects those parts' authored
position, orientation, scale, and visibility channels. Other channels keep
the current pose. Omit `parts` for the whole rig. Parts retain their usual
hierarchy, so attached children follow their parents. Fractional orientation
weights blend by the shortest rotation. Visibility switches at weight 0.5.

The stack evaluates from first to last. A later layer blends its keyed
channels over the accumulated pose. At weight one it owns those channels.
At lower weights the result includes the earlier performance. Source
clips remain reusable.

## Edit and audition

```js
motionLayers = motionLayers.edit('lift', {
  parts: ['sleeve-r', 'glove-r', 'lantern'],
  weight: [[0.2, 0], [0.6, 1], [0.9, 0]]
});
motionLayers = motionLayers.arrange(['glance', 'lift']);
```

Edits, reordering, and `enabled: false` return a new stack. Pass the new
stack when building a revised shot. The timeline's `lanes.motionLayers`
reports the order, masks, and weight curves. `frame.motionLayers` reports
the effective weights and source sample times at the playhead. Spline and
Polish apply the stack before contacts and prop handoffs. Block plays the
held base pose.

The same stack is also usable outside a timeline. Call
`motionLayers.apply(pose, time)` to layer a sampled pose in place, or include
`motionLayers.native` beside additive layers in a clip's `tools.layers`
array. Both use Ink's native layer evaluator.

## CLI

Preview two strides with the lantern lift and overlapping glance.

```sh
ink-studio animation-timeline examples/motion-layers.js \
  --loop 0,2 --frames 12 --preview lantern-walk
```

Render the same beat with the base walk, or audition an edited part mask
and weight at one frame. The example reads these controls through the
standard scene `--params` option.

```sh
ink-studio animation-timeline examples/motion-layers.js \
  --params '{"baseOnly":true}' --loop 0,2 --frames 12 --preview walk-only

ink-studio animation-timeline examples/motion-layers.js \
  --params '{"layerEdits":{"lantern-lift":{"parts":["sleeve-r","glove-r","lantern"],"weight":0.8}}}' \
  --at 1.13 --preview edited-lift
```

# Motion FX

Motion FX is a stack of keyed effects on an Ink puppet. Give each layer a part
mask, its own timing envelope, and an intensity multiplier. Layers can overlap.
The same stack drives the browser and headless renderer.

```js
const fx = K.anim.motionFx.create(builder, {
  duration: clip.dur,
  capacity: 8000,
  effects: [
    { id: 'stretch', kind: 'stretch', parts: ['body'], axis: [1, 0, 0],
      keys: [[0.8, 0], [1.06, 1], [1.30, 0]] },
    { id: 'echoes', kind: 'trail', parts: ['cape'], lookback: 0.34, copies: 3,
      keys: [[1.09, 0], [1.37, 1], [1.79, 0]] },
    { id: 'sweep', kind: 'sweep', parts: ['lantern'], color: 11,
      base: [0.61, 1.08, -0.045], tip: [0.61, 0.60, -0.045],
      width: 0.09, keys: [[1.26, 0], [1.43, 1], [1.73, 0]] }
  ]
});
const world = builder.finish();
function source(time, actor) {
  clip.sample(time, actor.pose, { sourceTime: true });
}
const puppet = K.puppet(world, { parts, pose(time, dt, actor) {
  source(time, actor);
  fx.apply(time);
} });
fx.bind(world, puppet, source);
world.motionFx = fx;
```

Allocate the splat pool before finishing the world and bind before playback.
Use the same source pose callback for normal rendering and historical
samples. It may apply authored contacts or sample a sequence, and should be
safe to call at any time in any order. Historical samples read the source pose
and keep their lookback inside the clip. Scrubbing needs no warm-up frames.

## Time and mask each effect

Each key is `[seconds, amount, ease]`. Amounts run from zero to one and
easing shapes the segment after the key. Outside the keyed range the layer
is inactive. Omit `parts` to use the full puppet, or list the exact part
names. Stretch and smear affect the selected splats' shapes while keeping
child joints on the authored rig pose.

```js
fx.edit('echoes', { intensity: 0.65, parts: ['cape'] });
fx.edit('sweep', { enabled: false });
fx.apply(time, { before: true }); // compare the source and clear transient FX
```

`fx.at(time)` reports keyed amounts. `fx.apply(time)` also reports affected
parts, emitted splats, and splat budget misses. Use `fx.effects()` to read the
authored stack or `fx.setEffects(effects)` to publish an edited stack.

## Effect settings

- **Stretch** uses the native volume-preserving squash and stretch map.
  The direction comes from the part's motion or an explicit `axis`.
  `strength` sets its maximum change and can be negative for squash.
- **Smear** uses the native trailing deformation with velocity, `gain`,
  maximum `length`, and `lookback`. Its chosen part is pulled back along
  the motion.
- **Trail** stamps copies of the selected part at earlier poses. Control
  `copies`, `lookback`, `opacity`, and optional palette `color`.
  The shared `trailLimit` caps the number of rest splats per copy.
- **Solid sweep** samples a span on the selected part at earlier times.
  Ink joins those sections, caps both ends, and fills the shell with
  depth-writing splats. Set `base` and `tip` in puppet rest coordinates,
  or use the part's height axis. Use `lookback` and `samples` for the
  sweep history, `width` for half-thickness, and `spacing` for surface
  resolution. Intensity scales its thickness.

Motion-based effects can set `threshold` in world units per second.
The splat pool is shared across layers. Increase `capacity` or reduce
trail copies or sweep resolution if a layer reports a budget miss.

## Try it

```sh
node cli/ink-studio.js motion-fx examples/motion-fx.js --at 1.42
node cli/ink-studio.js render examples/motion-fx.js --t 1.42 --ortho --w 288 --h 192
```

For the interactive demo, [build and serve the browser bundle](pose-blocking.md#try-the-browser-example)
and open `http://localhost:8080/examples/motion-fx.html`. Click a layer to
jump to its peak, edit its beat and part mask, or use **Compare source**
to inspect the same pose with FX muted.

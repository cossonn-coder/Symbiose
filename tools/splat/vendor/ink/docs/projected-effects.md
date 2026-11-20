# Projected splat effects

Projected effects draw animated pixel images and procedural patterns on
splat surfaces. A layer can read a shared field for its color, coverage, or
coordinate warp. Particle emitters can use the same path or read that field
to decide where to spawn. All of the effects render on the scene's art-pixel
grid before the optional text pass in the CPU renderer. Browser hosts can
use the shared fields and material samplers to integrate these layers into
their own pipeline. See the [WebGL renderer coverage](browser-renderer.md#feature-coverage).

Try [Tidal signal](../examples/surface-effects.js) for a moving projected
image, a revealing ribbon, ripples and sparks. [Edge shedding](../examples/edge-shedding.js)
shows particles leaving the lit edges of a solid.

```sh
node cli/ink-studio.js clip examples/surface-effects.js --from 0 --to 4.4 --fps 12
node cli/ink-studio.js clip examples/surface-effects.js --from 0 --to 4.4 --fps 12 --text braille --tg 1
node cli/ink-studio.js clip examples/edge-shedding.js --from 0 --to 3 --fps 16
```

The text pass accepts `ascii`, `symbols`, `braille` and `blocks` in
`render`, `sheet` and `clip`. The still renderer writes a text file beside
the PNG. The clip writes an animated PNG and a text file with form feeds
between frames. In scene-color mode the text pass uses the frame's output
palette, including local effect colors. A layer's `ink: true` marks fine
details for the text pass. Emitter dots are marked automatically. Smaller
`--tg` values give the text more spatial detail.

## Fields

Call `K.splatEffects.field(options)` to create a bounded grid of named scalar
channels in `[u, v]` coordinates. A JSON scene can put the same options under
`finish.surfaceEffects.fields` and include both `stamps` and `strokes`.
In JavaScript, `B.finish({ surfaceEffects: { fields: { wake } } })` accepts
either a constructed field or its definition.

```js
const wake = K.splatEffects.field({
  width: 96,
  height: 48,
  origin: [-2.4, -1.2],
  cell: 0.05,
  channels: {
    reveal: { decay: 0.12 },
    wake: { decay: 1.6 },
    flowU: { combine: 'sum', decay: 2 },
    flowV: { combine: 'sum', decay: 2 }
  }
});
wake.stamp({
  at: [0, 0], time: 0.5, radius: 0.16,
  shape: 'ring', speed: 0.8, width: 0.10, lifetime: 1.5,
  values: { wake: 0.8 }
});
wake.stroke({
  keys: [[0.5, 0, 0], [2.5, 1.8, 0.24]], spacing: 0.04,
  radius: 0.48, velocity: [-0.16, 0.05],
  values: { reveal: 1, wake: 0.6, flowU: -0.1, flowV: 0.04 }
});
```

Stamps have a time, radius, and one or more channel values. A disk covers
its interior. A ring spans a band around its radius. In both cases `speed`
grows the radius and `velocity` moves the center. Channels use exponential
`decay` per second and max or sum blending. Use sum for signed values such
as flow components. A stroke interpolates between timed UV keys and stamps
the result. Give transients a lifetime when they should stop contributing.

`field.frame(time)` is independent of earlier render times. Read a named
channel with `frame.sample(name, u, v)`, or copy its grid with
`frame.data(name)` for a host renderer. Calling `stamp`, `stroke`, or
`clear` invalidates future snapshots. The revision number lets an effect
detect a change even while the scene is paused. Hosts can also provide their
own field with `channels`, `revision` and `frame(time).sample(name, u, v)`,
including a wrapper around an existing fluid solver.

## Surface layers

Set `type: 'projected'` on an ordinary named material layer. The ray sample
supplies its unwarped position on the surface. `space: 'rest'` pins paint
to the object, including rigidly posed parts. `space: 'world'` keeps the
projection in scene coordinates so objects can move through it. A browser
host can supply both `position` and `worldPosition` to `SurfaceLook.shade`.

- **Projection** can be a plane, cylinder, or ribbon. Plane axes default to X
  and Z. A cylinder uses its up axis and returns distance around its
  circumference and height. A ribbon takes 2–64 XYZ centerline points and
  returns station and signed distance across the closest segment. A JS
  projection callback can provide coordinates from any available chart.
- **Field sampling** uses `field` with optional `maskChannel`,
  `revealChannel`, `contourChannel`, or `warpChannels: [u, v]`.
  `maskChannel` fades the paint, while `revealChannel` also fades the
  underlying surface. `range: [low, high]` controls the transition.
  `warp` scales the coordinate distortion and `scroll` adds motion.
  Existing surface finishes can also use
  `mask: { type: 'field', field, channel, projection, range }`.
- **Patterns** include `solid`, `stripes`, `hatch`, `chevrons`, `rings`,
  `dots`, `checker`, and `contour`. Contours read `contourChannel`.
  `scale` sets the repeat in projection units. `width` and the art-pixel
  footprint control line coverage. `colors` maps a field channel through
  an ordered ramp. Use `blend: 'mix'`, `'add'`, or `'multiply'`.
- **Output palette** optionally limits the dominant paint at a pixel to its
  own set of colors after depth compositing. Different layers can have
  different palettes. `--raw` exposes the blended lighting and paint
  before output palette selection. In ordinary color and stipple, dominant
  local palette regions use the same art grid as the rest of the scene.

To project animated pixel art, use `pattern: 'raster'` and
`raster: { width, height, frames, fps, channels, repeat, wrap }`. Frames are
RGB or RGBA byte arrays, in row-major order, with the default of four
channels. Each frame maps to one unit tile after applying `scale`. Samples
use nearest texels and honor RGBA transparency. `repeat` loops frame time
and `wrap` repeats the tile in the projection.

### Author a shader in JavaScript

A layer can name a shader from `surfaceEffects.shaders` or use a function as
`pattern`. The same surface sampler runs in the Node toolkit and in the
browser bundle.

```js
function wakeInk({ x, y, time, field }, out) {
  const stripe = Math.sin((x + y) * 12 - time * 5);
  out[3] = Math.max(0, stripe) * Math.min(1, field('wake'));
}
```

The function receives projected `u`, `v`, scaled and warped `x`, `y`,
`time`, the full surface sample, the color so far as `base`, and
`field(name)` for the unwarped location. It writes
`[r, g, b, amount, coverage, ink]` into a supplied array. The initial RGB
comes from the layer tint or ramp. Return synchronously and leave
components you don't need at their initialized values. For GPU hosts,
field snapshots expose the grid data and dimensions. A host shader can
upload those grids and pass the resulting composited color to the existing
ASCII shader. The JavaScript callback API runs on the CPU.

## Emitters

Create `K.splatEffects.emitter(B, options)` before finishing the builder and
add it to the stage. Its `source(birthTime, serial, random)` supplies a
position, optional surface normal, and optional normalized RGB. It can
return null for a rejected birth. Use an analytic path when the source
itself moves. Size, rate, birth interval, lifetime, outward speed, drift,
gravity, spread and density are configurable. The same seed and birth
time reproduce the same particle on a later render.

Use `K.splatEffects.surfaceSource(world, options)` to select baked splats
with surface bindings. Select by binding ID, material `surface.name`, or
explicit indices. Supply an eye and `grazing` for visible grazing normals,
`minLuma` for bright regions, and `lit: true` to evaluate the finish.
An optional `weight(hit)` callback can also read a field or evaluate a
material mask. The emitter inherits the source RGB unless `color`
supplies a scene palette index or an index callback. The source sampler
can also be used independently of the emitter.

For one-shot debris, `K.deform.burst({pieces, from, speed, gravity, drag,
life, shrink})` already computes analytic motion for authored piece
centers. Sample it directly with `burst.piece(index, seconds)` to get a
`{point, scale}` without a nearest-piece search. Sample times can be in
any order. For packed splats, move the center to `point` and multiply
the covariance by `scale * scale`. The [interactable locks example](../examples/interactable-locks.js)
uses this on an effects frame after publication and keeps the collision
and navigation revision independent of the airborne fragments.

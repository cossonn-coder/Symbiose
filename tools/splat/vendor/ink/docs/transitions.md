# Screen transitions

Ink Studio's browser entry includes a WebGL 2 compositor for timed, full-screen
effects. It accepts already-rendered frames, so the same effects work with Ink
Studio worlds, canvas drawings, still images, video frames, or another renderer's
textures. Current Node and CLI image exports use the CPU renderer. Timeline
planning and cue dispatch work independently of WebGL.

Run the [interactive gallery](../examples/transitions/index.html) from the
repository root with a local server, then open
`http://localhost:8000/examples/transitions/`.

```sh
python3 -m http.server 8000
```

Use [Transition review](transition-review.md) to inspect native headless scene frames around environment changes and authored camera cuts.

## Play a preset

Browser bundlers resolving the package's `browser` entry can import these APIs
from `@shapeshift-labs/ink-studio`. Native browser modules can import `webgl.mjs`
and its relative modules by URL.

```js
import {
  createTransition, createTransitionComposer, createTransitionPlayback
} from './ink-studio/webgl.mjs';

const composer = createTransitionComposer(canvas);
composer.setSource('from', preloadedOverworld);
composer.setSource('to', preloadedArena);

const effect = createTransition('tile-flood', {
  duration: 0.78,
  anchor: [0.72, 0.51],
  cellSize: 10,
  seed: 14
});
const playback = createTransitionPlayback(effect);
let started;
function tick(now) {
  started ??= now;
  const frame = playback.update((now - started) / 1000);
  composer.draw(frame);
  if (frame.progress < 1) requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
```

`plan.sample(seconds)` clamps to the ends and returns a deterministic frame.
Use it for scrubbing or capturing. `createTransitionPlayback(plan, { onCue })`
returns `update(seconds)`, `seek(seconds)`, and `reset()`. Forward updates emit
every cue crossed, once per crossing. Seeking moves the playhead silently.
Reset before a replay. Cues are objects with `name`, normalized `at`, `time` in
seconds, and optional `detail`. The host owns audio and scene changes. For
example, `wake-in-darkness` emits `rain` over black by default. Override
`cue`, `cueAt`, and `cueDetail` to play another sound. The gallery plays a
synthesized rain cue when sound is enabled.

`freeze-flash-swap` posts `freeze`, `flash`, and `swap` at the three stage
boundaries. Capture the outgoing image once before playback to keep it frozen.
Waking presets can start on the cover color. `drift-off` and `faint` finish on it.
To lead into or follow one of these presets, render an ordinary scene frame on
the corresponding side of the effect.

## Presets

Use `transitionPresets` to list the 49 definitions with display names, groups,
durations, stage spans, and preset-specific default overrides.

| Group | Preset IDs |
| --- | --- |
| Blackouts and fades | `hard-blackout`, `fade-out-cut-in`, `cut-out-fade-in`, `stepped-fade`, `fade-through-white`, `fade-through-color`, `silhouette-to-black`, `last-light-out` |
| Waking, sleeping, and coming to | `first-slit-of-light`, `eyelid-reveal`, `sleepy-double-blink`, `squint-into-daylight`, `come-to-in-fragments`, `drift-off`, `faint`, `wake-from-a-dream`, `wake-in-darkness` |
| Irises, wipes, and room changes | `character-centered-iris`, `destination-iris`, `diamond-iris`, `horizontal-squeeze`, `vertical-split`, `side-wipe`, `diagonal-wipe`, `stair-step-wipe`, `clock-wipe`, `blind-wipe`, `doorframe-wipe`, `stairwell-blackout` |
| Tiles, dissolves, and encounters | `checkerboard-swap`, `random-block-blackout`, `tile-flood`, `spiral-blackout`, `scanline-build`, `pixelate-and-rebuild`, `dither-dissolve`, `color-by-color-dissolve`, `strip-pull-apart`, `rush-to-black`, `freeze-flash-swap`, `threat-centered-blackout` |
| Dreams, memories, and time jumps | `bright-memory-wash`, `palette-drift`, `same-room-time-jump`, `alternating-era-bands`, `lingering-afterimage`, `ripple-into-a-vision`, `ink-soak`, `black-between-fragments` |

| Option | Meaning |
| --- | --- |
| `duration` | Total time in seconds. |
| `timing` | Positive relative spans for each authored stage, including holds. The spans are normalized to the duration. |
| `easing` | Override the preset's curves with `linear`, `smooth`, `in`, `out`, `inOut`, or a function receiving the local stage fraction. |
| `anchor`, `target` | Normalized `[x, y]` coordinates measured from the top-left. Set the character or threat for a closing iris or tile flood. Set `target` for an opening iris, with `anchor` as its default. |
| `color` | Cover or effect pigment as normalized `[r, g, b, a]`. |
| `direction` | Signed `[x, y]` components in top-left coordinates. Used by directional effects and the fainting offset. |
| `cellSize`, `bands`, `steps` | Art-pixel cell size, band count, or brightness and timing levels, depending on the effect. |
| `seed` | Deterministic pattern seed for scattered tiles, streaks, and ink. |
| `strength`, `softness`, `width` | Effect amplitude, normalized reveal edge softness, or width, depending on the shader. |
| `cues` | Replace the authored markers with an array of `{ at, name, detail }` objects. |
| `uniforms` | GLSL uniform overrides as an object or a function returning an object. The function receives `{ time, phase, progress }`. |

`createTransition(id, options)` accepts the same controls for each preset.
Only the shaders using a given control respond to it. To keep a time jump
aligned, render both sources from the same camera before applying the dissolve.

## Sources and masks

`composer.setSource(name, image, options)` uploads an `HTMLCanvasElement`,
`OffscreenCanvas`, loaded image, video, bitmap, or
`{ width, height, data }` with a byte RGBA array. Frame dimensions may differ.
The compositor fits each full image into its destination. The default
`filter: 'nearest'` retains hard pixel edges. Use `'linear'` for smoothing
uploaded sources. Call `setSource` again when an uploaded image changes.

A texture created on the composer's context can be passed as `{ texture }`.
The host controls that texture's filtering, contents, and lifetime. Pass
`origin: 'top-left'` or `origin: 'bottom-left'` explicitly when needed. Uploaded
sources default to top-left and WebGL textures to bottom-left. The built-in
shader coordinates use the WebGL bottom-left convention.

| Source name | Usage |
| --- | --- |
| `from`, `to` | Outgoing and incoming images. Only the sources sampled by the active stage are required. |
| `subject` | White subject on black or transparent for `silhouette-to-black` and `lingering-afterimage`. Without it those effects use a brightness or local mask. |
| `light` | White light shape for `last-light-out`. Otherwise it uses a patch centered on `anchor`. |
| `threat` | White enemy shape for `threat-centered-blackout`. Otherwise it uses a patch centered on `anchor`. |
| `fragment1`, `fragment2` | Optional consecutive glimpses. They default to `from` and `to`. |
| `jamb` | Optional doorframe texture used by `doorframe-wipe`. Give its opaque pixels the desired material and use the alpha channel for cutouts. |
| `cover` | Reserved solid fill produced from `u_color`. |

Use `removeSource(name)` to release a source. Call `composer.dispose()` when
unmounting; it also disposes its shaders and render targets. DOM and byte-array
sources are uploaded again after context restoration. The host must supply new
external GL textures and redraw its render targets after a context restore.

### Render Ink Studio worlds directly into a transition

Create the renderer first so its canvas context options take effect. Create the
compositor on the same canvas. Rendering to a target keeps both sources and
the effect on the GPU.

```js
const renderer = createRenderer(canvas, { toolkit: { KIT, PixelLook } });
const composer = createTransitionComposer(canvas);
const previous = composer.createTarget(320, 180);
const next = composer.createTarget(320, 180);

renderer.render(worldA, { target: previous });
renderer.render(worldB, { target: next });
composer.setSource('from', previous);
composer.setSource('to', next);

const door = createTransition('doorframe-wipe');
composer.draw(door.sample(0.35), { width: 320, height: 180 });
```

To use a live doorway view as a transition source, include the
[portal descriptor](portals.md#render-the-view) in the corresponding
`renderer.render` call. The target captures the composed view with its
world-space aperture and foreground occlusion.

`composer.draw(frame, { target, width, height, uniforms })` renders to a
composer target, a compatible host framebuffer descriptor, or the canvas.
Target draws default to the target dimensions and keep the canvas dimensions.
Use `target.resize(width, height)` to reallocate and `target.dispose()` to
release an owned buffer. Draws cannot sample their own output texture, so
alternate two targets when chaining passes. Like the main browser renderer,
the compositor controls the viewport, blend and test state, framebuffer,
texture bindings, VAO, and program during a draw. Other renderers sharing
the context set their own draw state when they resume.

## Add custom shader stages

Register a name with a GLSL ES 3.00 function body returning `vec4`. The framework
provides the vertex shader, standard uniforms, and texture sampling helpers.
`transitionShaders` lists the built-in shader names you can reuse in stages.

```js
composer.registerShader('slanted-reveal', {
  uniforms: 'uniform float u_slope;',
  source: `
    float edge = uv.x + (uv.y - 0.5) * u_slope;
    return swapAt(uv, edge);
  `
});

const custom = defineTransition({
  duration: 1.1,
  cues: [{ at: 0.82, name: 'door-close' }],
  stages: [
    { from: 'from', to: 'from', span: 1, start: 0, end: 0 },
    { shader: 'slanted-reveal', span: 4, easing: 'smooth',
      uniforms: ({ phase }) => ({ u_slope: 0.4 + 0.2 * phase }) }
  ]
});
composer.draw(custom.sample(0.4));
```

A stage accepts `{ shader, span, from, to, mask, start, end, easing, uniforms,
samplers }`. Missing source names default to the respective `from`, `to`, and
`mask` slots. The default `mix` shader crossfades. `start` and `end` map local
eased progress into the shader's `u_value`. Stages may run backward or hold
the same value. Uniform callbacks run at sample time.

Standard uniforms include `u_value`, `u_phase`, `u_progress`, `u_time`,
`u_size`, `u_color`, `u_anchor`, `u_direction`, `u_cells`, `u_bands`,
`u_steps`, `u_strength`, `u_seed`, `u_softness`, and `u_width`. UVs passed to
the shader body run from bottom-left to top-right. Use `sourceFrom(uv)` and
`sourceTo(uv)` for correctly oriented samples, `maskAt(uv)` for the optional
mask, and `swapAt(uv, rank)` for a threshold reveal in `u_value`. For
additional images use a shader declaration such as
`uniform sampler2D u_overlay; uniform int u_overlayFlip;` and a stage
binding `samplers: { u_overlay: { source: 'title', flipUniform: 'u_overlayFlip' } }`.
Then sample `texture(u_overlay, oriented(uv, u_overlayFlip))`. Raw string
bindings are also supported for textures already in WebGL orientation.

Shader programs compile on the first draw. Re-register a custom name to
replace its program, or call `composer.unregisterShader(name)` to release
it. Built-in names are reserved. Supply preset-compatible custom stages
with `defineTransition` and use the same playback, cues, and draw methods.

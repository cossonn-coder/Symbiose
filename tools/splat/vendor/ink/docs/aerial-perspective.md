# Aerial perspective

Aerial perspective gives distant geometry colour and extinction from the active sky. Near geometry stays clear up to the chosen start distance. The effect is available in the Node renderer and CLI.

```sh
node cli/ink-studio.js render examples/aerial-perspective.js --sky-time 7 --raw --out dusk.png
node cli/ink-studio.js render examples/aerial-perspective.js --sky-time 7 --aerial-perspective off --raw --out clear.png
node cli/ink-studio.js render examples/aerial-perspective.js --aerial-start 15 --aerial-density 0.06 --aerial-contrast 0.25 --raw --out controlled.png
```

Enable it with `world.aerialPerspective = true` or set `finish.aerialPerspective` in a JSON diorama. You can also enable, override, or disable it at render time.

```js
const image = ink.render(world, {
  t: 7,
  aerialPerspective: { start: 15, density: .06, contrast: .25 }
});
```

| Setting | CLI | Default |
| --- | --- | --- |
| Enable or disable | `--aerial-perspective on\|off` | Off |
| `start` | `--aerial-start units` | 8 scene units |
| `density` | `--aerial-density per-unit` | 0.065 per scene unit |
| `contrast` | `--aerial-contrast fraction` | 0.15 |

`contrast` is the fraction of the original surface contrast retained at long distances. Zero allows the surface to fade completely into the atmosphere. One or zero density gives a clear render. The CLI controls enable the effect unless you pass `--aerial-perspective off`. `--atmosphere off` turns off aerial perspective and local atmosphere.

Timed sky profiles can provide `aerialStart`, `aerialDensity`, and `aerialContrast`. They fill values the scene and render options omit. The render settings override the scene settings. The [canyon example](../examples/aerial-perspective.js) uses different densities for daylight, sunset, and blue hour. Without a directional sky, the scene background colour supplies the air colour.

## Rendering

The headless renderer samples the shared sky gradient and sun glow for the colour of scattered air. The solar disk and other directional accents stay in the background and reflections. Downward rays use the horizon colour in their direction. This follows the use of transmittance and in-scattered light in [Hillaire's sky and aerial perspective paper](https://onlinelibrary.wiley.com/doi/abs/10.1111/cgf.14050), with an analytic exponential curve for Ink's artist-authored skies.

Distances follow perspective rays or the nominal orthographic eye, so the orthographic renderer's internal setback leaves the authored range intact. In air beyond the start distance, transmission is `contrast + (1 - contrast) * exp(-density * distance)`. The effect is evaluated at each contributing surface before blending. Existing water segments remain distinct from air. Local fog and volumes use depth-specific sampling when combined with aerial perspective. Reflected geometry receives aerial perspective along the path to the visible reflector. An empty transparent export pixel stays transparent.

The Node option `captureFog: true` includes aerial opacity at the nearest opaque surface in the existing fog buffer. It also includes any local media affecting that surface.

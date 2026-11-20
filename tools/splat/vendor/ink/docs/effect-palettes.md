# Effect palette ramps

Give fog, clouds, sky, and visible emissive details their own palettes at Ink’s native art resolution. Each ramp uses the rendered coverage of its effect. Fog uses bounded and height fog, aerial perspective, and distance haze on surfaces. Clouds use their visible coverage, including card, impostor, and volume representations. Sky uses the unobscured backdrop, including celestial tracks. Emissive details use the existing emission pass for splats and sprite atlases.

Ramp swatches are available to pixels selected for that effect. Colors already in the scene palette remain available to its materials. Scene geometry, material bindings, and local palette constraints continue to color all other pixels.

The [Saltgate night watch](../examples/effect-palettes-night-watch.js) uses a blue night palette, mauve cloud steps, cool sea fog, warm beacon highlights, and protected navigation markers.

```sh
ink-studio render examples/effect-palettes-night-watch.js --t 2 --effect-palettes on --out saltgate.png
ink-studio render examples/effect-palettes-night-watch.js --t 2 --effect-palettes off --out saltgate-standard.png
```

Set `look.effectPalettes` on the world, `finish.look.effectPalettes` in a diorama, or `visual.look.effectPalettes` in a simulation world. Use `--effect-palettes on|off|file.json` to use the scene setting, disable it, or replace it with a JSON file. The headless library accepts `render(world, { effectPalettes })` with the same choices. Raw rendering bypasses the ramps.

```json
{
  "protect": { "objects": ["courier"], "materials": ["waypoint"] },
  "fog": {
    "colors": ["#233b4c", "#417b89", "#9fbab0"],
    "geometry": true,
    "threshold": 0.58,
    "range": [0.25, 0.72]
  },
  "clouds": ["#251e44", "#514062", "#9d7694"],
  "sky": {
    "colors": ["#0b122e", "#25386b", "#aab8e3"],
    "when": { "channel": "daylight", "max": 0.35 }
  },
  "emission": {
    "colors": ["#a43b30", "#f3884e", "#fff1c2"],
    "threshold": 0.27
  }
}
```

- Give a ramp 1–64 hex swatches or scene palette indices. The array shorthand uses the default settings.
- The default `luma` mode interprets `colors` from dark to light. `range: [low, high]` fits the steps to the effect’s measured tones in 0–1. Set `dither` from 0 to 1 for ordered transitions between steps. The `nearest` mode selects the closest swatch by RGB distance.
- `threshold` controls the minimum visible coverage or emission intensity required. Defaults are 0.58 for fog, 0.46 for clouds, 0.48 for sky, and 0.24 for emission. Overlaps resolve in the order emission, fog, clouds, sky.
- Fog and clouds default to backdrop pixels. Set `geometry: true` on either ramp to include opaque surfaces they cover. Add object or material names to `protect` so those visible surfaces keep the scene’s original colors. Selective ink outlines are preserved.
- A `when` gate reads a numeric sky profile channel at the active sky time. Supply `min`, `max`, or both. A missing channel leaves the ramp inactive.

The ramps run after scene palette and art styling. Set `captureEffectPalettes: true` when rendering from the library to receive an `effectPaletteMask` for an active set. Its top-down pixel values are 0 for unassigned, 1 fog, 2 clouds, 3 sky, and 4 emission. The returned palette and usage counts include the selected swatches.

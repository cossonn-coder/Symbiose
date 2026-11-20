# Transition review at export size

Review a shot at the exact frame rate and art dimensions you plan to export. Ink writes a contact sheet and a JSON report with adjacent-frame measurements. Each image tile is rendered at one output pixel per art pixel. The sheet includes a difference map for the strongest adjacent change in each event. Orange shows where the most visible difference occurs.

```sh
ink-studio transition-review examples/transition-review.js --w 160 --h 100 --out review.png
```

The [headland example](../examples/transition-review.js) checks a sky clock wrapping at midnight, a storm front reaching the headland, and a hard cut to the beacon. The storm intentionally steps its sky look and activates a reserved palette on the arrival frame.

## Author the events

Set `world.transitionReview` in a JavaScript scene, or use `--plan file.json` with any diorama. This plan uses scene seconds and samples two frames before and two frames from each event.

```json
{
  "fps": 12,
  "neighbors": 2,
  "preroll": 4,
  "events": [
    { "id": "Midnight", "kind": "midnight", "at": 1.25, "skyTime": 24 },
    { "id": "Storm arrival", "kind": "storm", "at": 4.4 },
    {
      "id": "Cut to the beacon", "kind": "cut", "at": 7.25,
      "incomingCamera": { "target": [-5.8, 2, -0.3], "yaw": -0.46, "pitch": 0.18, "dist": 10.8 }
    }
  ]
}
```

- **Timing.** The zero-offset tile is the event frame. Set `neighbors` to 2–6 frames on each side. Leave at least `neighbors / fps` scene seconds before an event. Use `preroll` to let temporal paint and volume history build before the visible window. Poses advance in chronological order even when windows overlap.
- **Sky clock.** `skyTime` sets the environment time at the event. The default `skyRate` is 1 sky unit per scene second. Use 0 for a held environment, or set a different rate for an accelerated day cycle. The ordinary scene clock continues to drive poses.
- **Framing.** `camera` can set `yaw`, `pitch`, `target`, `dist`, `zoom`, `lensScale`, and `ortho`. Angles are in radians. These settings are held through the window. Cuts require `incomingCamera`, which inherits omitted camera fields from the outgoing shot. Use `kind: "transition"` for other markers.
- **Export look.** Normal view options such as `--raw`, `--ortho`, `--art-direction`, or `--effect-palettes` also apply to the review. `--scale 2` enlarges the sheet by repeating pixels after measurement. The JSON tile rectangles describe the native sheet.

## Read the results

| Flag | What it measures | Default threshold |
| --- | --- | --- |
| `pop` | Share of pixels whose largest RGB channel change exceeds `pixelDelta`. | `popFraction: 0.18`, with `pixelDelta: 0.12` |
| `lighting-jump` | Magnitude of the signed mean luma change across the image. Negative report values indicate darkening. | `lightingDelta: 0.065` |
| `palette-change` | Mean change in red–green or blue–green colour balance, or the share of pixels affected by entries added to or removed from the resolved output palette. The larger value drives the flag. | `paletteDelta: 0.055` |

Put any of these 0–1 values under `thresholds` in the plan. The metrics describe the rendered result. Inspect the source frames and difference map to identify the authored cause.

For a camera cut, the first row shows the actual framing change and its screen measurements. The matched row shows the preceding and event frame from the outgoing camera, then the same pair from the incoming camera. Flags at the cut come from those locked comparisons. The actual incoming shot starts with fresh temporal history.

Save a [shot recipe](shot-recipes.md) with `--recipe <shot.json>` to replay and verify the sheet and metrics.

Use `--fail-on-flags` to return exit status 2 after writing both files when a threshold is exceeded. Node hosts can call `ink.transitionReview(world, { plan, width, height, view, pose })` to get `{ image, report }`. Supply the host's `pose(world, seconds)` callback for stateful or rigged scenes.

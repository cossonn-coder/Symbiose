# Reproducible shot recipes

Add `--recipe <shot.json>` to `render`, `clip`, `transition-review`, or `sim render` to save the inputs behind a review. The recipe records the effective camera at each rendered sample, scene and sky times, profile pins, seed, frame rate, and native art dimensions and pixel scale.

```sh
ink-studio clip examples/interruptible-sky.js \
  --from 2.6 --to 4.6 --fps 8 --camera-orbit 14 \
  --w 192 --h 112 --px 2 --out squall.png --recipe squall.shot.json
ink-studio shot replay squall.shot.json --out squall-replayed.png
```

Replay renders from the original inputs and checks the camera, art resolution, and SHA-256 of the PNG or animated PNG. It also verifies and reproduces transition metrics, text, and diagnostic passes when present. Pass manifests use the new filenames if you rename the replay output. The replay publishes files after verification.

## Project files

The version 1 JSON recipe keeps paths relative to the project directory used for capture. Keep the scene and its assets with the project revision used for review. When sharing a recipe with someone who has the same project in another location, they can supply `--root /path/to/project`. Explicit scene and override files are checked by hash. Indirect assets loaded by the scene are checked through the rendered output.

## Weather and simulation

The recipe saves the retained surface weather grid at the first rendered sample when the scene uses one. This includes the accumulated wetness, standing water, snow, frost, temperature, and exposure fields. Replay restores that checkpoint and advances the same fixed weather ticks.

A simulation recipe also embeds an Ink world recording. It replays scheduled commands from the starting checkpoint so moving emitter sockets, conditional weather, and the final world checkpoint can be reconstructed.

```sh
ink-studio sim render examples/world-conditional-weather.json \
  --asset-pack examples/coastal-environment-pack.json --ticks 20 \
  --out station.png --recipe station.shot.json
ink-studio shot replay station.shot.json --out station-replayed.png
```

# Environment review shots

Run the three authored perspective shots through the headless renderer from the repository root.

```sh
node scripts/render-environment-reviews.js studio/out/environment-reviews
```

Each shot exports a 192×128 animated PNG at 10 fps, the matching [environment passes](art-passes.md#environment-passes-for-compositing), and a [shot recipe](shot-recipes.md) that can verify and replay the capture.

| Shot | Seconds | What to inspect |
| --- | --- | --- |
| Beacon after rain | 0, 2.4, 4.7 | The rising sun moves the tower shadow across the courtyard. The stone keeps a reflective wet patch as the shower clears. |
| Clouds at the cliff path | 0, 3.1, 5.0 | The offshore cloud card shifts behind the railing as the camera tracks down the path, crosses the bounded fog, and comes out the other side. |
| Rain at the sheltered market | 0, 2.3, 4.5 | A local squall moves through the exposed aisle. The produce stalls sit under dry awnings while the courtyard pool carries reflected lanterns and rain ripples. |

## Isolate an effect

Use the same time and image settings when rendering a comparison. Omit a disabling option to render the authored shot.

```sh
node cli/ink-studio.js render examples/review-beacon.js --t 2.4 \
  --w 192 --h 128 --px 1 --raw --sun-shadows off --out studio/out/beacon-unshadowed.png
node cli/ink-studio.js render examples/review-cliff-path.js --t 3.1 \
  --w 192 --h 128 --px 1 --raw --atmosphere off --out studio/out/cliff-clear.png
node cli/ink-studio.js render examples/review-sheltered-market.js --t 2.3 \
  --w 192 --h 128 --px 1 --raw --scene-exposure off --out studio/out/market-unsheltered.png
```

Use `--retained-weather off` to view dry beacon paving, `--cloud-field off` to isolate the offshore cloud card, and `--reflections off` to isolate the market’s planar reflections. For the market, compare the local weather and exposure at the produce stall and in the aisle.

```sh
node cli/ink-studio.js environment inspect examples/review-sheltered-market.js --t 2.3 --at -2.70,1,-.84
node cli/ink-studio.js environment inspect examples/review-sheltered-market.js --t 2.3 --at 1.91,1,.88
```

Replay a capture and its diagnostic passes with the same scene revision.

```sh
node cli/ink-studio.js shot replay studio/out/environment-reviews/review-beacon.json \
  --root . --out studio/out/beacon-replay.png
```

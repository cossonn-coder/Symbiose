# Conditional weather tracks

A conditional track turns a scene cue, a region entry, or a simulation condition into an [interruptible sky transition](interruptible-sky.md). Each transition starts with the light and weather sampled at its trigger time. The same result drives the sky, fog, wind, and retained weather through the existing environment bindings.

Set `finish.weatherTracks` in a JSON diorama, `visual.weatherTracks` in a simulation, or `settings.weatherTracks` in an environment pack. JavaScript scenes can pass `weatherTracks` to `builder.finish()`. Destination profiles use the scene’s `skyEnvironment`.

```json
{
  "cues": [[1.1, "warning-bell"]],
  "rules": [
    {
      "id": "warning-bell",
      "trigger": { "cue": "warning-bell" },
      "transition": { "profile": "squall", "duration": 2.25 }
    },
    {
      "id": "path-entry",
      "trigger": {
        "enter": {
          "entity": "courier",
          "socket": "eye",
          "bounds": { "min": [1.8, 0, 1.5], "max": [4.6, 2, 3.5] }
        }
      },
      "transition": { "profile": "mist", "duration": 1.3 }
    },
    {
      "id": "pressure-rises",
      "trigger": {
        "condition": {
          "field": "station/pressure",
          "at": [0, 0, 0],
          "when": { "op": "gte", "value": 1012 }
        }
      },
      "transition": { "profile": "clearing", "duration": 2.5 }
    }
  ]
}
```

- **Cue.** Use a `[time, id]` marker, a `{ time, id }` marker, or a cue from the scene’s animation timeline. In a simulation, schedule `world/event` with `{ "kind": "cue", "cue": "warning-bell" }` in its args. An optional `where` uses the standard world predicate on the cue record.
- **Region entry.** Test an entity’s resolved world position or a named socket against an inclusive XYZ box. A simulation measures membership at each committed tick. Starting inside establishes the initial membership. Leaving and entering again provides the next entry edge.
- **Simulation condition.** Run a world predicate on a successful field probe, or omit `field` to test the committed tick record, including its `signals` and `events`. The initial true sample and later false-to-true edges can fire. Use the same `at`, `args`, and `when` shapes as simulation probes and conditions.
- **Ordering.** Rules fire once by default. Set `repeat: true` for later cues or edges. If multiple rules fire at the same time, later rules supply shared channels. Authored cue markers retain their exact seconds. Region entries and simulation conditions use the committed tick time.

## Review and export

The [headland station example](../examples/world-conditional-weather.json) uses the Tideline pack. Its bell begins a squall at 1.1 s, the courier’s entry increases fog at 3 s, and rising station pressure starts clearing at 4.5 s. The runtime records the actual firing times in checkpoints and includes them in replay.

```sh
ink-studio probe examples/world-conditional-weather.json --asset-pack examples/coastal-environment-pack.json --t 5 --field world/weather-tracks
ink-studio sim render examples/world-conditional-weather.json --asset-pack examples/coastal-environment-pack.json --t 4 --out mist.png
```

Keep exact shot timings in `skyEnvironment.transitions` or pass `--sky-transitions shot.json`. Use `--weather-tracks off` on a render to play the authored schedule by itself. Set the authored `weatherTracks` value to `false` to disable the simulation evaluator for that scene.

Library hosts can call `K.weather.tracks.compile(sky, settings)` and advance the returned program with `step(previous, { time, cues, query, view })`. Supply scene cues as IDs or records, and pass the host’s current world query and tick view for dynamic rules. `transitions(state)` returns ordinary sky cues to combine with the authored clock. The simulation runner and headless renderer perform these steps for their normal entry points.

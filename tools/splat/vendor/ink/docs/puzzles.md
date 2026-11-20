# Puzzle recipes

A `puzzle` system combines named inputs into Boolean outputs for doors,
floodgates, animations, and other world systems. Recipes are JSON and run
through the same world scheduler as `control`, mechanics, and water. Switch
progress and timers are part of the normal checkpoint and replay.

The [gate example](../examples/world-puzzle-gate.json) holds a pressure plate
while two switches arm a timed opening. A native slider lifts the door and
an agent must walk through before it drops. The example supplies the plate
and button inputs as commands. A game host can instead drive them from
collision or interactable events. Wire an existing Boolean output to a
puzzle input for a sustained condition, or an event output for a pulse.

## Write a recipe

```json
{
  "kind": "puzzle",
  "config": {
    "inputs": {"plate": "bool", "prime": "event", "switch": "event", "reset": "event"},
    "nodes": {
      "ordered": {"op": "sequence", "steps": ["prime", "switch"], "reset": "reset"},
      "timed": {"op": "window", "trigger": "ordered", "ticks": 45, "reset": "reset"},
      "ready": {"op": "all", "inputs": ["plate", "timed"]}
    },
    "outputs": {"open": "ready"}
  }
}
```

Nodes can reference inputs or other nodes in any declaration order.
References must exist and cannot form a cycle. A stateful puzzle publishes
its outputs for consumers on the next scheduler boundary. Use a `control`
block such as `choose` to turn an open flag into a numeric drive or water
opening.

| Node | Fields | Result |
| --- | --- | --- |
| `all`, `any` | `inputs` | Whether all or any of the listed signals are active. |
| `count` | `inputs`, `min` | Whether at least `min` of the signals are active. |
| `not` | `input` | Whether the input is inactive. |
| `sequence` | `steps`, optional `reset` | Advances when listed signals activate in order. Completion stays active until reset. |
| `window` | `trigger`, `ticks`, optional `reset` | Activates for `ticks` evaluations, including the triggering evaluation. Another activation restarts the window. |
| `latch` | `set`, optional `reset` | Stays active after the set signal activates. |

An event input is active on an evaluation that receives a nonempty batch.
A Boolean input or node activates on its false-to-true edge. A sequence
counts at most one activation per evaluation. Two distinct step signals
activating together clear unfinished progress because the sample has no
order. An incorrect step keeps the longest matching prefix at the end of
the input history, so repeated patterns work. Reset takes precedence over
activation on the same evaluation. A latched sequence can arm its window
again after reset and a fresh completion.

Window duration is measured in evaluations of the puzzle system. With the
default schedule this is one evaluation per world tick. With an explicit
solver schedule, duration follows that cadence.

Put the system in a [world prefab](headless-worlds.md#author-a-world) to
stamp independent copies. Expose the inputs and outputs as prefab ports.
Use a `$param` for settings such as the window duration. Each stamped
instance keeps separate progress, timers, and output history.

## Inspect a blocked output

```sh
ink-studio trace examples/world-puzzle-gate.json lock/why --json
ink-studio sim run examples/world-puzzle-gate.json --ticks 4 \
  --actions examples/world-puzzle-gate.actions.json --record primed.run.json
ink-studio trace primed.run.json lock/why --args '{"output":"open"}'
```

`why` reads the current revision and lists blockers such as an inactive
plate, the next expected step in a sequence, or an expired window. An
`any` blocker lists alternative signals and a `count` blocker reports
which options are active and how many are needed. Choose the output with
`--args` when a recipe publishes several. Probe `lock/state` for all output
diagnostics and the sampled values and state of the nodes.

With world causality enabled, a `puzzle-evaluated` decision links published
output or blocker changes to the recipe's sampled inputs and prior
evaluation. Use `world/cause` for that history. The current `why` report
is available even with causal recording disabled.

## Check reachability and replay a solution

Add named `moves` under `config` to describe the actions available in the
puzzle. A move can `set` Boolean inputs or `pulse` event inputs. The optional
guard `"when": {"signal":"plate"}` checks the last evaluated signal before
applying a move. Add `"is": false` to require an inactive signal. For example:

```json
{
  "stand-on-plate": {"set": {"plate": true}},
  "throw-switch": {"pulse": ["switch"], "when": {"signal": "plate"}}
}
```

`solve` searches from the current puzzle state using those moves and waits.
It returns a shortest witness in puzzle evaluations when it finds one.
Witness rows include their relative tick, the move name, and its input
changes. Missing ticks represent waits. The statuses are `solved`,
`unreachable` when the declared move model's reachable states are exhausted,
and `limit` when the search runs out of budget. The defaults are
`maxTicks: 32` and `maxTransitions: 4096`. Supply overrides with `--args`.

The search checks the logic and authored move guards. To verify that a
player or agent can reach a switch or pass through a real opening, replay
the witness against a world scenario with the relevant geometry and
movement checks. The gate example's win condition uses the agent's
position on the far side of the door.

```sh
ink-studio trace examples/world-puzzle-gate.json lock/solve --json
ink-studio sim run examples/world-puzzle-gate.json --ticks 60 --scenario \
  --actions examples/world-puzzle-gate.actions.json --record gate.run.json
ink-studio trace gate.run.json world/cause --args '{"port":"lock/open"}'
ink-studio sim replay gate.run.json
ink-studio sim render gate.run.json --out gate.png
```

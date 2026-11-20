# Agent activity decisions

An `agents` system can give selected agents a list of activities. The policy
chooses an eligible activity and reachable destination. The existing mover
follows the route, and the policy confirms arrival using the actual position.
The same policy can govern walking, swimming, or flying agents.

The [resident example](../examples/world-resident-shelter.json) starts at a
workbench. When rain starts, the agent checks the nearer shed, reads its locked
door state, and walks to an open porch. Work resumes when the weather clears and
the agent reaches the bench again. The scene uses a typed rain field and a
[puzzle output](puzzles.md) for the door. Activities can use any exposed world
field.

## Author a policy

Add `decisions` to an existing `agents` system's `config`. The
`members` keys are IDs from `config.agents`. Activities are shared by all
members that reference them.

```json
{
  "interval": 3,
  "members": {"resident": ["work", "shelter"]},
  "activities": {
    "work": {
      "duration": 6,
      "when": [{"field": "weather/rain", "when": {"op": "lte", "value": 0.1}}],
      "destinations": {"bench": {"at": {"entity": "workbench"}}}
    },
    "shelter": {
      "priority": 100,
      "duration": 0,
      "when": [{"field": "weather/rain", "when": {"op": "gt", "value": 0.1}}],
      "destinations": {
        "shed": {
          "at": {"entity": "locked-shed"},
          "when": [{
            "field": "world/signal",
            "args": {"port": "lock/unlocked"},
            "when": {"value": true},
            "reason": "Door is locked"
          }]
        },
        "porch": {"at": {"entity": "open-porch"}}
      }
    }
  }
}
```

- Higher `priority` wins. Ties follow the member's activity list. For a new
  selection, the policy checks destinations by distance with IDs breaking ties.
  Each destination must pass its conditions, fit the body, and have a route.
  A valid current destination takes precedence within its activity to avoid
  switching between equivalent sites while traveling.
- Activity conditions default to sampling at the agent. Destination conditions
  default to sampling at the destination. A condition can supply `at`, `args`,
  a [query condition](headless-worlds.md#query-a-revision), and a readable
  `reason`. A read must return `ok` and satisfy `when`. Destinations and
  explicit sampling locations accept XYZ or an entity selector with an optional
  socket.
- `interval` is the normal time between selections in world ticks and defaults
  to 8. Each selection tries up to `routeLimit` paths, which defaults to 12.
  A blocked movement wakes the policy for the next world tick and lets it try
  alternatives. With no valid choice, the member waits for the next selection.
- The agent must be observed within arrival range before the activity starts.
  A missing `duration` gives an ongoing activity. An integer duration gives the
  number of world ticks at the destination while eligible. A zero duration can
  complete on arrival. Optional `completeWhen` conditions require an observed
  result before completion. They default to sampling at the arrived agent.
  The member stays at the destination after completion until a new choice
  replaces it or the member loses access.
- The policy owns destinations for its members. Agents outside `members` can
  still use the regular `seek` action.

## Inspect choice and outcome

```sh
ink-studio sim run examples/world-resident-shelter.json --ticks 14 --record choosing.run.json
ink-studio trace choosing.run.json folk/why --entity resident --json
ink-studio trace choosing.run.json world/cause --entity resident --args '{"kind":"activity-selected"}'
ink-studio sim run examples/world-resident-shelter.json --ticks 100 --record shift.run.json
ink-studio sim replay shift.run.json
```

`why` accepts `--entity` for the scene entity ID or
`--args '{"agent":"resident"}'` for the agent ID. It returns the selected
activity and destination, current phase and blockers, and evidence from the
last selection. `decisionTick` dates the evidence. Route rejections include
the obstacle reported by the movement planner when available. Probe
`folk/decisions` for all managed agents.

The phases are `idle`, `traveling`, `acting`, `complete`, and `blocked`.
The event timeline distinguishes `activity-selected`, `activity-started`,
`activity-completed`, `activity-blocked`, and `activity-idle`. Hosts can
use those events for presentation or to drive other systems. Enable world
causality to attach the sampled field readings to activity events. Checkpoints
retain the activity, phase, timing, and decision evidence for replay and forks.

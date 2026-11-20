# Contact effects

A material contact is one measured interaction with a surface. Mechanics wheel
forces and walking agents publish these records when their system sets
`"contactEvents": "material"`. Each record carries a stable ID, source tick, speed,
normal load, point, normal, heading, and material ID. Physical material
readings include wetness and the asset revision, plus friction and temperature
when available. Wheel load is estimated from the supported assembly weight
shared across grounded wheels. Walking profiles can author `contactLoad`
(default 10).

The `contact-effects` system consumes these records through its `contacts`
event port. Connect more producers using `config.channels` to declare
additional event inputs. Scripts and game hosts can submit the same records
with `world/input`. For a custom record supply `point` and `speed` in world
units and world units per second. Optional fields include `id`, `entity`,
`interaction` (`roll`, `step`, or `impact`), `load`, `weight`, `normal`,
`heading`, `support`, `material`, `surface: { "wetness": 0.7 }`, and
`cue`. Use an ID unique to the physical contact when supplying the same
record to more than one channel. Rated simulation uses the usual buffered
event connections.

## Author the material

Add a `contactEffects` recipe to a physical material in a versioned asset
pack. Omit an effect to leave it off for that material. `contact-effects`
can supply a `fallback` recipe for materials without one. Numeric strength,
count, and gain accept a constant or `{ "dry": 0, "wet": 1 }`, sampled from
the original contact's surface reading. `minSpeed`, `speedReference`, and
`loadReference` set how speed and load scale the output.

| Effect | Authoring and output |
| --- | --- |
| Rut | `rut` scales the contact's wear weight by load and material response. Wire the `ruts` event output into a `wear` system's `contacts` input. |
| Spray | `spray.count` controls emission, scaled by speed and load. The recipe can set `color`, `speed`, `life`, and `radius`. |
| Sound | Use material `sounds.roll`, `sounds.step`, and `sounds.impact`, or a scripted contact's `cue`. `sound.gain` sets gain and `sound.interval` limits repeated playback per wheel or contact source. Hosts play the positional cue using its gain and pitch. |
| Shake | `shake.strength`, `shake.life`, and `shake.frequency` control the camera impulse. Shake falls off from the contact point over the system's `range` and is capped by `maxKick`. |

With `wear.config.rutDepth` set, `wear/rutDepth` exposes the depth and
`wear/ruttedBed` returns the base bed minus interpolated wear. Bind that
field to visual terrain, support, or water boundaries as needed. Set
`wear.config.bed` to a base height field or `ground` to a constant.
Avoid also feeding the unscaled source contacts to the same wear system
if its wear should come exclusively from the authored rut recipe.

## Use in a run

`feedback/contacts` explains the effects triggered by each contact and
records the tick it was processed. `feedback/sounds` and the
`material-sound` events expose cue, position, gain, pitch, and contact ID.
Set `soundEvents: false` when the host reads cues directly and does not need
them in world event history. `feedback/frame` samples active splat particles
and a world-space camera kick. Sample it at a camera position or focus for
local shake. The world baker uses its focus when
`visual.fields.contactEffects` names this field.

The contact stream is carried by the fixed-tick runtime. Checkpoints keep
active impulses, their birth seeds, and sound cooldowns. Frame samples
derive particle positions from their age. `maxContacts`, `maxBursts`,
`maxParticles`, and `maxShakes` bound the work. Probe `feedback/dropped`
for inputs beyond the current step's contact budget.

The example drives two carts over wet and dry clay with identical wheel
settings. The wet lane takes deeper tracks, throws droplets, and makes a
stronger cue and camera impulse.

```sh
ink-studio probe examples/world-contact-effects.json --field feedback/contacts --ticks 22
ink-studio probe examples/world-contact-effects.json --field tracks/rutDepth --at -1.08,0,-1.55 --ticks 22
ink-studio sim render examples/world-contact-effects.json --ticks 22 --out contact-effects.png
node scripts/benchmark-contact-effects.js
```

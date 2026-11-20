# Motion retargeting

Retargeting uses the rest pivots of two Ink puppets and a shared role profile.
A role maps each puppet's part name to the same job. Ink re-expresses
rotations in the target's rest frame, scales positional offsets from the
matched rest segments, and estimates root travel scale from the profile's
support chains. The target keeps its own pivots and hierarchy.

## Profiles and rig maps

| Profile | Carrier and chains |
| --- | --- |
| `biped` (default) | Hips, two legs, arms, spine, and head. |
| `quadruped` | Hips, two forelegs, two hindlegs, chest, neck, head, and tail. |
| `avian` | Body, two wings, two legs, neck, head, and tail. |
| `serpentine` | Body, head, neck, spine, and tail. |

Use `K.anim.retarget.profiles` or `ink-studio retarget --profiles` for exact
role names. Without a rig map, Ink uses exact role names found among the
puppet's parts. With a map, Ink uses the supplied bindings. Each rig can
supply independent `forward` and `up` axes in its rest coordinates. They
default to +Z and +Y.

```js
const source = {
  puppet: courier,
  roles: {
    hips: 'body',
    leftThigh: 'trouser-l',
    leftShin: 'calf-l',
    leftFoot: 'boot-l',
    leftSole: { part: 'boot-l', point: [-0.24, 0, 0.08] },
    leftWrist: { part: 'glove-l', point: [-0.49, 1.14, 0], marker: true }
    // Add the remaining roles for this character.
  }
};
```

A string uses the part's rest pivot. A `point` uses the same rest-world XYZ
coordinates as Ink's contact probes. Marker roles, such as soles and wing
tips, measure points and can guide a segment's length and orientation. They
can share a part with a transform role. A transform binding can supply
explicit rest `axis` and `up` vectors to guide its local frame. An ordinary
binding gets its direction from the profile's `aim` role when available.

A creator-defined profile is a plain JS object or JSON file. For example,
this profile describes a body swinging a hooked appendage.

```json
{
  "id": "hooked-creature",
  "root": "body",
  "roles": {
    "body": {},
    "hook": { "required": true, "aim": "tip" },
    "tip": { "required": true, "marker": true },
    "crest": {}
  },
  "scaleChains": [["hook", "tip"]]
}
```

Both puppets use the same profile with their own names and points. Mark the
controls the profile requires with `required: true`; the root is required
automatically. The scale chains describe corresponding rest distances.
If the rigs should use a particular scale, set a positive `unit` on both
rig maps. Ink uses their ratio.

## Retarget and bake

```js
const plan = K.anim.retarget.create({
  clip: walk,
  source,
  target,
  profile: 'biped',
  travel: 'scaled'
});
const report = plan.report();
const points = plan.landmarks(0.4);
const baked = plan.bake({ fps: 30 });
const reusable = K.anim.clip(JSON.parse(JSON.stringify(baked.definition)));

const timeline = K.anim.timeline.create({ world, puppet: target.puppet, clip: reusable });
timeline.set({ stage: 'spline' });
```

`sample(time)` returns target pose channels. `landmarks(time)` measures
the source and target role points on the solved puppets. The report
flags missing bindings, skipped source tracks, and incompatible marker
bindings. **Partial** can bake the mapped controls. **Unsupported** means
one of the puppets lacks a mapped root.

- `scaled` adjusts root displacement to the target's proportions.
- `unscaled` keeps the root displacement in source units, aligned to the target.
- `in-place` keeps the scaled vertical root motion for a stationary preview.

The bake contains ordinary Ink `pos`, `rot`, `scale`, and `show` keys,
including converted rotation-matrix channels. It samples the source pose
at the requested rate and at authored key times, and preserves the clip's
duration, loop intent, and cues.
For strongly different proportions, inspect the soles and use Ink's
authored contacts wherever an exact plant matters. The bake works with
the [shared timeline](animation-timeline.md) and [contacts](authored-contacts.md).

## CLI

Both JS scenes publish `world.retargetRig` with `puppet` and any role-map
fields. The source can also publish a `clips` object keyed by clip name.
Use `--clip name` to choose a published clip or `--motion clip.json` to
read a native Ink clip definition for that rig.

```sh
ink-studio retarget examples/retarget-courier.js examples/retarget-guard.js \
  --clip walk --bake guard-walk.json --preview walk-review --direction 0
```

`walk-review/source` and `walk-review/target` contain synchronized color and
silhouette atlases and shot-time metadata. Use `--at 0.4` to measure one
pose's landmarks and render a single frame when previewing. Use
`--frames`, `--w`, and `--h` to specify the preview frame count and tile size.
To author mappings outside scene code, pass `--source-map map.json` or
`--target-map map.json` with overrides such as `roles`, `forward`, `up`,
and `unit`. Use `--profile custom-profile.json` for a creator-defined
profile and `--out report.json` to save the report.

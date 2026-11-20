# Reusable environment packs

An environment preset is a named asset in Ink Studio’s existing version 1 asset-pack format. It can carry sky profiles, their sequences and tracks, weather fronts, cloud recipes, celestial tracks, atmosphere layers, wind, and related art controls. Each of those settings uses the same data format as the corresponding render primitive.

The [Tideline pack](../examples/coastal-environment-pack.json) supplies a sky clock, a moving coastal squall, and a horizon band with shared artwork. The jetty changes the dawn horizon colour. The beacon raises aerial extinction and cools its dusk horizon. Both use revision 1 of the same pack.

```sh
ink-studio render examples/coastal-pack-jetty.json --asset-pack examples/coastal-environment-pack.json --t 0 --w 224 --h 140 --px 1 --raw --out jetty.png
ink-studio render examples/coastal-pack-beacon.json --asset-pack examples/coastal-environment-pack.json --t 6 --w 224 --h 140 --px 1 --raw --out beacon.png
```

## Bind a preset

Set `environmentPreset` at the top of a diorama or in a simulation’s `visual` block. Load the package through the scene’s `assetPacks` array or the CLI’s existing `--asset-pack` option. JavaScript scenes can pass `assetPacks` and `environmentPreset` to `builder.finish()`.

```json
{
  "environmentPreset": {
    "asset": "tideline/coast",
    "revision": 1,
    "overrides": {
      "skyEnvironment": { "profiles": { "dusk": { "horizon": "#8aa2b1" } } },
      "aerialPerspective": { "density": 0.056 }
    }
  }
}
```

Objects in `overrides` merge by key. Arrays replace the corresponding list. Use an empty list to clear a track or a set of layers, or use `false` for a primitive that supports being switched off. Explicit `finish` or `visual` settings take precedence by setting, including individual fields inside `look`. Render flags can still override the resolved settings. Native scene geometry, sockets, and precipitation sources continue to use their existing authoring tools.

A string binding such as `"tideline/coast"` follows the installed revision. Include `revision` to pin the binding. Ink reports a missing asset or revision mismatch before building a scene. Saved simulation checkpoints keep the original pack data and binding.

## Package artwork and revise a pack

Put named presets in the manifest’s `environments` array. Each entry has `id`, `label`, and `settings`. A pack can supply environment presets, artwork, and the existing families, looks, and materials together.

A horizon band can set `image` to `{ "asset": "tideline/headland" }`. The owning pack’s `environmentImages` array supplies the namespaced `id`, `width`, `height`, and top-down straight RGBA `pixels`. In Node, `ink.readEnvironmentImage("tideline/headland", "ridge.png")` prepares a PNG for embedding. The image bytes travel with the pack. Use an optional `revision` on an image reference to pin the owning pack, especially for artwork shared from another pack. An image in the same pack can follow that pack’s revision with its preset.

- `KIT.authoring.assetPacks.bundle(packs, ids)` includes packs that own referenced images, following dependencies across the bundle.
- `KIT.authoring.assetPacks.merge(installed, incoming)` preserves the existing same-revision conflict and downgrade rules.
- `KIT.authoring.assetPacks.reviseEnvironment(pack, id, { label, settings })` keeps the preset ID and increments the pack revision when content changes. Pass the complete settings when revising a definition. Scene overrides remain on the scene.
- `KIT.authoring.environments.bind(binding, catalog)` returns immutable resolved settings, the installed pack revision, and the referenced image revisions. Use these settings directly with Ink’s sky, weather, or render APIs. Built scenes expose the resolved identities as `environmentSource`.

Environment `settings.look` can carry horizon bands, effect palettes, art direction, stable dithering, and silhouette protection. Use portable JSON settings and literal swatch colours for presets meant to travel across scene palettes.

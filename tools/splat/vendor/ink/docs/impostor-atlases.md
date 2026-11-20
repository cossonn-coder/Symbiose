# Artist-authored cards and impostors

Place a sprite atlas in a scene as a camera-facing card or as a directional impostor. One atlas can supply color, depth, normals, and emission. With directional placement, Ink chooses the closest authored heading and elevation. A card uses the first view for its frame and faces the camera throughout a turn.

```js
const atlas = studio.readSpriteAtlas('drone/atlas.json');
const sprite = K.sprite.placeAtlas({
  atlas,
  at: [0, 1.2, 0],
  mode: 'impostor',
  yaw: 0,
  scale: 1
});
return B.finish({ ...sceneSettings, spriteAtlases: [sprite] });
```

Use `K.sprite.atlas({ metadata, images })` with decoded RGBA byte buffers. `images.color` is required. `depth`, `normal`, and `emission` are optional and use the same dimensions and view rectangles. `at` and `frame` can be functions of scene time in JavaScript. Each placement can disable depth, relighting, or emission with `depth: false`, `lighting: false`, or `emission: false`.

## Map and view conventions

| Channel | Encoding |
| --- | --- |
| Color | Straight RGBA. Color alpha defines the silhouette. |
| Depth | RGB24 stores the normalized value `(R × 65536 + G × 256 + B) / 16777215`. Set `depthFormat: 'gray'` to use the red channel for grayscale depth. `depthRange` maps the image values from near to far in scene units, and `depthOrigin` gives the value at the pivot plane. Depth increases away from the viewer. Alpha zero uses the pivot plane. |
| Normal | Signed XYZ in RGB, mapped from [-1, 1] to [0, 255]. Alpha zero marks a missing normal. `normalSpace: 'view'` is the default for an authored atlas, with X right, Y up, and +Z toward the viewer. `'asset'` uses object axes. Normals respond to live sun in the headless renderer. |
| Emission | `emissionMode: 'add'` adds emission RGB weighted by the map alpha. `'baked'` describes an atlas with emission already included in its color, using premultiplied emission RGB. Emission is also available as an art pass. |

The manifest has the sheet `width`, `height`, a `files` object with relative PNG paths, and `frames` with view rectangles. Each entry can specify `frame`, `yaw`, `pitch`, `pivot`, `unitsPerPixel`, and `depthOrigin`. Angles use radians. Rectangles and pixel pivots use top-down atlas coordinates. Put shared `unitsPerPixel` and `depthOrigin` at the top level when they apply to every view.

```json
{
  "width": 192,
  "height": 64,
  "unitsPerPixel": 0.035,
  "depthRange": [-0.7, 0.7],
  "files": { "color": "color.png", "depth": "depth.png", "normal": "normal.png", "emission": "emission.png" },
  "frames": [
    { "yaw": 0, "pitch": 0.14, "rect": { "x": 0, "y": 0, "width": 64, "height": 64 } },
    { "yaw": 1.57, "pitch": 0.14, "rect": { "x": 64, "y": 0, "width": 64, "height": 64 } },
    { "yaw": 1.57, "pitch": 0.84, "rect": { "x": 128, "y": 0, "width": 64, "height": 64 } }
  ]
}
```

Ink's [atlas exporter](art-passes.md#directional-sprite-atlas) writes registered scale and depth for each view. Use `--pitches` to bake additional elevation rows. Older manifests can specify `unitsPerPixel`, `depthOrigin`, and `pitch` when the original export camera is known.

```sh
ink-studio atlas my-prop.js --directions 12 --pitches 0.14,0.48,0.84 --maps depth,normal,emission --out drone
ink-studio render my-scene.js --sprite-atlas drone/atlas.json --sprite-at 0,1.2,0 --live-sun on --raw --out scene.png
ink-studio render examples/relightable-impostor.js --t 3 --sprite-atlas-mode card --raw --out card.png
ink-studio render examples/relightable-impostor.js --t 3 --sprite-atlas-mode impostor --raw --out impostor.png
```

A JSON diorama can put an array of placements in `finish.spriteAtlases` and refer to each `atlas` by a path relative to the diorama. Use `--sprite-atlas off` to hide the authored placements in a comparison. A manifest passed with `--sprite-atlas` replaces the scene's placements for that render and defaults to the world origin. Set `--sprite-at x,y,z` and `--sprite-scale n` to place it.

Depth positions each texel along its draw ray and participates in the scene's depth, fog, and emission passes. The renderer uses the silhouette of the selected view. The [survey drone example](../examples/relightable-impostor.js) demonstrates both placement modes under changing camera and lighting angles.

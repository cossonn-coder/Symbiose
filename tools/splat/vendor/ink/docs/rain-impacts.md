# Rain impacts and runoff

Add `rainImpacts` to a scene that uses [world-space rain](world-precipitation.md). Give the rain named receiving planes in world space. A hit at a water plane launches a ripple. A hit at a paving plane leaves a brief splash. A hit on a roof can feed wet streaks along authored drain paths.

```js
const rainImpacts = {
  receivers: [
    { id: 'pool', kind: 'water', y: .10, min: [0, -2], max: [4, 3] },
    { id: 'court', kind: 'paving', y: .18, min: [-4, -2], max: [0, 3] },
    { id: 'awning', kind: 'roof', y: 2.87, min: [-4, -1.7], max: [-1, .45],
      drains: [{ from: [-2.8, .18, .45], to: [-2.4, .18, 2.2],
        width: .16, delay: .27, travel: .76 }] }
  ],
  ripple: { amplitude: .32, speed: 1.5, lifetime: .82 },
  paving: { radius: .17, lifetime: .25, strength: 1 },
  runoff: { lifetime: 2.3, strength: .25 }
};
const world = B.finish({ cam, skyEnvironment, weatherBinding, precipitation, rainImpacts });
```

Each receiver is a horizontal patch with XZ bounds and a world Y height. Match that height to the top of the surface. Rain uses its wind-driven flight path and hits the first receiving plane it reaches. The precipitation occluder checks for upstream blockers along the flight. A drain is an authored three-dimensional line. Place it below an eave or down a wall, then adjust its width, delay, and travel time. Roof hits feed the drain and the stain fades after its last deposits arrive.

Bind surfaces to the receiver IDs. Set `rainRipple` on the water finish to perturb its normals through Ink’s ripple field. The result is visible in reflection and specular layers. Use `rainImpact` masks on paving or other finishes to color splashes and wet streaks.

```js
const water = K.surface.material(waterBase, {
  rainRipple: 'pool',
  layers: { sky: { type: 'reflection', source: 'scene', f0: .7, strength: .8 } }
});
const paving = K.surface.material(pavingBase, { layers: {
  splash: { type: 'directionalColor', color: '#e3f6fa', crossColor: '#e3f6fa',
    mask: { type: 'rainImpact', receiver: 'court', channel: 'splash' } },
  wet: { type: 'directionalColor', color: '#304e5c', crossColor: '#304e5c',
    mask: { type: 'rainImpact', receiver: 'awning', channel: 'runoff' } }
} });
```

`ripple` accepts the existing wave amplitude, wavelength (`scale`), speed, width, and damping controls plus a lifetime in seconds. Splash radius and drain width use scene units. `maxSources` controls how many recent impacts each receiver uses, up to 64. The CPU renderer reconstructs recent impacts at the requested time using the weather track and wind history, so jumping to a frame gives the same result as playing forward.

```sh
ink-studio render examples/rain-cistern.js --raw --t 1.85 --out rain-cistern.png
ink-studio render examples/rain-cistern.js --raw --t 1.85 --rain-impacts off --out rain-only.png
```

Use `--rain-impacts on|off|file.json` or the matching `rainImpacts` render option. An override can tune the ripple, paving, or runoff controls while using the scene’s receivers. The [cistern example](../examples/rain-cistern.js) shows water rings and pale paving splashes during a shower, followed by wet streaks below the roof.

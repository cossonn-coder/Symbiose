# Moving weather fronts

A front carries a named weather profile over the world in XZ. Rain, snow, wind, local fog, and the retained surface solver read the front at their own positions. A headland can dry out while a valley is still inside the storm.

```js
const skyEnvironment = K.skyEnvironment.compile({
  defaults: {
    rain: 0, fogDensity: 0, windX: .1, windZ: 0,
    humidity: .4, airTemperature: 12, daylight: .8
  },
  profiles: {
    storm: {
      rain: .72, fogDensity: 1.6, windX: 1.9, windZ: .6,
      humidity: .97, airTemperature: 7, daylight: .24
    }
  }
});
const weatherBinding = {
  fogVolumes: ['valley-mist'],
  fronts: [{
    id: 'coastal-squall', profile: 'storm',
    radius: [6, 5.8], feather: .43,
    route: [
      { at: 0, xz: [-14, .45] },
      { at: 2, xz: [-5.7, .22] },
      { at: 6.2, xz: [5.6, -.15] },
      { at: 8.6, xz: [16, -2.3] }
    ]
  }]
};
```

Each route key specifies scene seconds and a world XZ position. Set `ease` on a key to control the following segment. The choices are `linear`, `smooth`, and `hold`. A route holds its endpoint before and after the keyed interval. Start and end beyond the view for a front that enters and leaves the scene. Use `loop: true` with matching endpoints for a closed route.

`radius` accepts a single distance or separate X and Z radii. `feather` controls the fraction of the radius used for the soft edge. It defaults to .4 and accepts zero for a hard boundary. Inside the front, specified weather channels blend over the current environment values. A small front can override one channel, such as rain, and share humidity or temperature with a larger front. Overlapping fronts apply in the order listed.

## Connect it to the scene

- Mark emitters with `profile: true` to use local rates. [World-space emitters](world-precipitation.md) integrate the wind history at their launch sites and sample the rain or snowfall rate at the moving particle. [Rain impacts](rain-impacts.md) read the rate at the contact position and time.
- Name the atmosphere volumes that should respond in `fogVolumes`, and use the profile’s `fogDensity` as a density multiplier within those volumes.
- Add the [retained surface grid](retained-weather.md) to record the weather at each cell. Material finishes can show wet stone, puddles, snow, or frost after the front has moved past.
- Hosts can call `K.weather.bind(skyEnvironment, weatherBinding).sample(time, x, z)` to inspect local conditions. Omitting XZ returns the background weather at that time.

Use the [environment inspector](environment-inspector.md) to inspect a front’s route keys, weight, and channel changes at a world position.

## Compare a render

```sh
ink-studio sheet examples/weather-front.js --t 2.4,6.2 --raw --out crossing.png
ink-studio render examples/weather-front.js --t 6.2 --raw --weather-fronts off --out clear.png
```

Use `--weather-fronts on|off` or the renderer’s boolean `weatherFronts` option. Configure routes in `weatherBinding.fronts` or supply them through `--weather-binding file.json`. The [headland and valley example](../examples/weather-front.js) shows the crossing in the CPU renderer.

/* kc-data: a diorama written down as data. Plain objects and lists (it can live in a JSON file): what solids there are and what they are made
   of, which of them are moving parts and how they move, what lamps and loose particles there are, what a tap does. Materials are named by
   role (stone, moss, ember ...) and a style says what colours those roles are, so the same diorama can be put in another style by one word.
     K.diorama.check(spec, env)   -> [{ level: 'error' | 'warning', path, problem, hint }]     nothing is built; every mistake is listed at once
     K.diorama.build(spec, env)   -> the world (throws, with the whole list, if check finds errors)
     K.diorama.scene(spec, env)   -> scene descriptor with build, model and drawing authoring hooks
     K.diorama.styles             the looks by name; add your own: { palette: [hex ...], roles: { stone: [1, 2, 3], ... }, sun, amb, sky, finish }
     K.diorama.kinds              what each kind of solid needs and may have (the checker reads this; so can an editor)
   env: { assets: { name: mesh } } for solids of kind 'mesh'. See lab/data-shrine.json for a whole one. */
(function (K) {
  const V = K.V,
    M = K.M,
    TAU = Math.PI * 2,
    DIO = (K.diorama = {});
  const ROLES = [
    'stone',
    'dark',
    'pale',
    'earth',
    'wood',
    'moss',
    'leaf',
    'water',
    'metal',
    'bone',
    'ember',
    'glow',
    'accent'
  ];
  DIO.styles = {
    slate: {
      palette: [
        0x07080b, 0x15171c, 0x2a2e36, 0x474d57, 0x6d747c, 0x9aa09c, 0xcfd2c8, 0x1f3a22, 0x356b36, 0x66a640, 0xa8d05a,
        0x3a2416, 0x5e3b22, 0x8a5a30, 0xb8844a, 0x7a2a1e, 0xc8321e, 0xff7a2a, 0xffd24a, 0xfff3c0, 0x16324a, 0x24567a,
        0x4a9aa0, 0xa8e0d8, 0x4a2760, 0x7a4296, 0xb070c4, 0x6a5a2a, 0xa88a3a, 0xe0c060
      ],
      roles: {
        stone: [1, 2, 3, 4, 5],
        dark: [1, 1, 2, 3],
        pale: [3, 4, 5, 6],
        earth: [11, 11, 12, 13],
        wood: [11, 12, 13, 14],
        moss: [7, 8, 9, 10],
        leaf: [7, 8, 9, 10],
        water: [20, 21, 22, 23],
        metal: [27, 28, 29, 29],
        bone: [4, 5, 6, 6],
        ember: [15, 16, 17, 18],
        glow: [18, 19],
        accent: [24, 25, 26]
      },
      sun: [-0.5, 0.8, 0.45],
      amb: 0.14,
      sky: 0.26,
      finish: { detail: 14, dither: 0.25 }
    },
    moss: {
      palette: [0x0b1114, 0x1c3626, 0x356b36, 0x82b552, 0xdff0c4, 0x4a0d1a, 0xad1f36, 0xff6474],
      roles: {
        stone: [1, 2, 3, 4],
        dark: [0, 1, 1, 2],
        pale: [3, 4, 4],
        earth: [1, 1, 2],
        wood: [1, 2, 2, 3],
        moss: [1, 2, 3],
        leaf: [2, 3, 4],
        water: [5, 5, 6],
        metal: [2, 3, 4],
        bone: [3, 4, 4],
        ember: [5, 6, 7],
        glow: [7, 4],
        accent: [5, 6, 7]
      },
      sun: [-0.45, 0.75, 0.5],
      amb: 0.16,
      sky: 0.3,
      finish: { detail: 12, dither: 0.35 }
    },
    ember: {
      palette: [
        0x0c0708, 0x1e1216, 0x38202a, 0x5a3440, 0x86525a, 0xb88a80, 0xe6c8a8, 0x2a2416, 0x4a4420, 0x7a6e2c, 0x4a1418,
        0x9c2a24, 0xe6772e, 0xffc24a, 0xffeeb0, 0x1a2238, 0x2c3c5e, 0x52688c, 0x8aa6c0, 0x6a3a12, 0xa86a22, 0xe0a640
      ],
      roles: {
        stone: [1, 2, 3, 4, 5],
        dark: [1, 1, 2],
        pale: [4, 5, 6],
        earth: [1, 2, 7, 8],
        wood: [2, 19, 19, 20],
        moss: [7, 8, 9],
        leaf: [8, 9, 21],
        water: [15, 16, 17, 18],
        metal: [19, 20, 21, 21],
        bone: [5, 6, 6],
        ember: [10, 11, 12, 13],
        glow: [13, 14],
        accent: [16, 17, 18]
      },
      sun: [-0.7, 0.45, 0.4],
      amb: 0.12,
      sky: 0.2,
      finish: { detail: 14, dither: 0.3 }
    }
  };

  // ---------------- what may be written ----------------
  const COMMON = {
    id: 'str',
    surfaceId: 'str',
    tags: 'list',
    mat: 'mat',
    res: 'pos',
    part: 'str',
    group: 'str',
    carve: 'bool',
    ghost: 'bool',
    separate: 'bool',
    turn: 'vec3',
    bump: 'vec2',
    hold: 'bool'
  };
  DIO.kinds = {
    ground: { need: {}, may: { rad: 'pos', stretch: 'pos' } },
    ball: { need: { at: 'vec3', r: 'num|vec3' } },
    rock: { need: { at: 'vec3', r: 'num|vec3' } },
    box: { need: { at: 'vec3', half: 'vec3' }, may: { round: 'num' } },
    lathe: { need: { at: 'vec3', h: 'pos', r: 'num|vec2|profile' } },
    torus: { need: { at: 'vec3', R: 'pos', r: 'pos' } },
    tube: { need: { pts: 'pts', r: 'num|vec2' } },
    stroke: {
      need: { points: 'list' },
      may: { surface: 'obj', axis: 'vec3', width: 'pos', depth: 'pos', taper: 'vec2', pressure: 'list', offset: 'num' }
    },
    fill: { need: { rings: 'list' }, may: { surface: 'obj', frame: 'obj', depth: 'pos', offset: 'num' } },
    regular: { need: { shape: ['d4', 'd6', 'd8', 'd12', 'd20'], at: 'vec3', r: 'pos' }, may: { round: 'num' } },
    extrude: { need: { outline: 'outline', at: 'vec3', depth: 'pos' }, may: { round: 'num' } },
    revolve: { need: { outline: 'outline', at: 'vec3' } },
    puff: { need: { outline: 'outline', at: 'vec3', height: 'pos' } },
    mesh: {
      need: { asset: 'str' },
      may: { size: 'pos', at: 'vec3', spin: 'num', cells: 'pos', thick: 'num', up: ['y', 'z'], hues: 'pos' }
    },
    join: { need: { how: 'join', a: 'solid', b: 'solid' }, may: { size: 'num', steps: 'pos' } },
    fold: {
      need: { of: 'solid' },
      may: { polar: 'pos', mirror: ['x', 'y', 'z'], repeat: 'vec3', count: 'vec3', centre: 'vec3', axis: 'vec3' }
    },
    warp: { need: { of: 'solid' }, may: { twist: 'num', bend: 'num', taper: 'num', centre: 'vec3', wide: 'pos' } },
    shell: { need: { of: 'solid', t: 'pos' } },
    swell: { need: { of: 'solid', by: 'num' } },
    rough: { need: { of: 'solid', by: 'pos' }, may: { scale: 'pos' } },
    bubbles: { need: { of: 'solid' }, may: { cell: 'pos', h: 'pos' } },
    pillar: { need: { at: 'vec3', h: 'pos' }, may: { r: 'pos', bay: 'pos', flutes: 'num' } },
    arch: {
      need: { at: 'vec3' },
      may: { span: 'pos', height: 'pos', depth: 'pos', thick: 'pos', block: 'pos', face: 'vec2' }
    },
    stairs: { need: { at: 'vec3', dir: 'vec3', rise: 'pos' }, may: { width: 'pos', riser: 'pos', tread: 'pos' } },
    fence: { need: { a: 'vec3', b: 'vec3' }, may: { h: 'pos', bay: 'pos', pickets: 'num' } },
    pipe: { need: { pts: 'pts' }, may: { r: 'pos', wall: 'pos', collar: 'pos' } }
  };
  const MOTION = {
    turn: {
      need: { part: 'str' },
      may: { axis: 'vec3', amount: 'num', period: 'pos', phase: 'num', keys: 'list', loop: 'pos' }
    },
    spin: { need: { part: 'str' }, may: { axis: 'vec3', speed: 'num' } },
    bob: {
      need: { part: 'str' },
      may: { axis: 'vec3', amount: 'num', period: 'pos', phase: 'num', keys: 'list', loop: 'pos' }
    },
    squash: {
      need: { part: 'str' },
      may: { axis: 'vec3', amount: 'num', period: 'pos', phase: 'num', keys: 'list', loop: 'pos' }
    }
  };
  const EFFECT = {
    lamp: { need: { at: 'vec3' }, may: { r: 'pos', strength: 'pos', flicker: 'num', follow: 'str' } },
    reveal: { need: {}, may: { dur: 'pos', block: 'pos' } },
    dust: { need: { at: 'vec3' }, may: { every: 'pos', n: 'pos', colours: 'mat', spread: 'pos' } },
    embers: { need: { at: 'vec3' }, may: { every: 'pos', n: 'pos', colours: 'mat' } },
    smoke: { need: { at: 'vec3' }, may: { every: 'pos', n: 'pos', colours: 'mat' } },
    sparks: { need: { at: 'vec3' }, may: { every: 'pos', n: 'pos', colours: 'mat', dir: 'vec3', speed: 'pos' } },
    rain: { need: { box: 'box' }, may: { rate: 'pos', colours: 'mat' } },
    wind: { need: { v: 'vec3' }, may: { swirl: 'num' } }
  };
  const TOP = {
    id: 'str',
    name: 'str',
    blurb: 'str',
    seed: 'num',
    style: 'style',
    palette: 'list',
    assetPacks: 'list',
    environmentPreset: 'obj',
    roles: 'obj',
    camera: 'obj',
    light: 'obj',
    finish: 'obj',
    groups: 'obj',
    parts: 'obj',
    solids: 'list',
    motion: 'list',
    effects: 'list',
    tap: 'obj',
    spare: 'pos'
  };

  // ---------------- checking ----------------
  const isNum = v => typeof v === 'number' && Number.isFinite(v),
    isVec = (v, n) => Array.isArray(v) && v.length === n && v.every(isNum);
  const lev = (a, b) => {
    const d = [];
    for (let i = 0; i <= a.length; i++) {
      d[i] = [i];
      for (let j = 1; j <= b.length; j++)
        d[i][j] =
          i === 0 ? j : Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    }
    return d[a.length][b.length];
  };
  const nearest = (word, list) => {
    let best = null,
      bd = 3;
    for (const w of list) {
      const d = lev(String(word), w);
      if (d < bd) {
        bd = d;
        best = w;
      }
    }
    return best;
  };
  const styleOf = spec => {
    const s = spec.style === undefined ? 'slate' : spec.style,
      base = typeof s === 'string' ? DIO.styles[s] : s && s.extends ? DIO.styles[s.extends] : s;
    if (!base) return null;
    const own = typeof s === 'object' ? s : {},
      out = {
        palette: (spec.palette || own.palette || base.palette).slice(),
        roles: Object.assign({}, base.roles, own.roles, spec.roles),
        sun: own.sun || base.sun || [-0.5, 0.8, 0.45],
        amb: own.amb !== undefined ? own.amb : base.amb,
        sky: own.sky !== undefined ? own.sky : base.sky,
        finish: Object.assign({}, base.finish, own.finish, spec.finish)
      };
    if (spec.light) {
      if (spec.light.sun) out.sun = spec.light.sun;
      if (spec.light.amb !== undefined) out.amb = spec.light.amb;
      if (spec.light.sky !== undefined) out.sky = spec.light.sky;
    }
    return out;
  };
  DIO.sceneLook = spec => styleOf(spec)?.finish.look;
  function applySurface(material, definition) {
    if (typeof definition === 'string') return K.surface.preset(definition, material);
    if (!definition || typeof definition !== 'object' || Array.isArray(definition))
      throw new TypeError('A surface is a preset name or a settings object');
    const { preset, ...settings } = definition;
    return preset === undefined ? K.surface.material(material, settings) : K.surface.preset(preset, material, settings);
  }
  const lookCatalog = spec => spec.assetPacks === undefined ? undefined :
    K.authoring.assetPacks.create({ packs: spec.assetPacks });
  function materialLook(base, settings, catalog) {
    const surface = settings.surface === undefined ? base : applySurface(base, settings.surface);
    return K.authoring.looks.material(surface, settings.lookAsset, catalog);
  }
  DIO.check = (spec, env) => {
    const out = [],
      bad = (path, problem, hint) => out.push({ level: 'error', path, problem, hint: hint || '' }),
      warn = (path, problem, hint) => out.push({ level: 'warning', path, problem, hint: hint || '' });
    if (!spec || typeof spec !== 'object' || Array.isArray(spec)) {
      bad('', 'a diorama is an object', 'start with { "id": ..., "solids": [ ... ] }');
      return out;
    }
    const keys = (o, path, allowed) => {
      for (const k of Object.keys(o))
        if (!(k in allowed)) {
          const n = nearest(k, Object.keys(allowed));
          bad(
            path + (path ? '.' : '') + k,
            'nothing is called "' + k + '" here',
            n ? 'did you mean "' + n + '"?' : 'what may be written: ' + Object.keys(allowed).join(', ')
          );
        }
    };
    keys(spec, '', TOP);
    if (typeof spec.id !== 'string' || !/^[a-z0-9-]+$/.test(spec.id))
      bad('id', 'a diorama needs an id of small letters, digits and dashes', 'for example "old-shrine"');
    const st = styleOf(spec);
    if (!st) {
      bad('style', 'there is no style called "' + spec.style + '"', 'styles: ' + Object.keys(DIO.styles).join(', '));
      return out;
    }
    let surfaceEffects, catalog;
    try {
      catalog = lookCatalog(spec);
    } catch (error) {
      bad('assetPacks', error.message);
    }
    if (catalog || spec.assetPacks === undefined) {
      try {
        st.finish = K.authoring.environments.apply(st.finish,spec.environmentPreset,catalog,st.palette);
      } catch (error) {
        bad('environmentPreset',error.message);
      }
    }
    try {
      PaintCorrections.layers(st.finish.paint);
    } catch (error) {
      bad('finish.paint', error.message);
    }
    if (st.finish.skyEnvironment !== undefined && st.finish.skyEnvironment !== false) {
      try {
        SkyEnvironment.compile(st.finish.skyEnvironment);
      } catch (error) {
        bad('finish.skyEnvironment', error.message);
      }
    }
    try {
      CelestialTracks.settings(st.finish.celestialTracks);
    } catch (error) {
      bad('finish.celestialTracks', error.message);
    }
    try {
      SplatRelighting.settings(st.finish.relighting);
    } catch (error) {
      bad('finish.relighting', error.message);
    }
    try {
      K.atmosphere.emitters.settings(st.finish.atmosphereEmitters);
    } catch (error) {
      bad('finish.atmosphereEmitters', error.message);
    }
    try {
      K.splatFields.settings(st.finish.splatFields);
    } catch (error) {
      bad('finish.splatFields', error.message);
    }
    try {
      VolumeCutouts.settings(st.finish.volumeCutouts);
    } catch (error) {
      bad('finish.volumeCutouts', error.message);
    }
    try {
      SceneOptics.shapedVolumes(st.finish.shapedAtmosphere);
    } catch (error) {
      bad('finish.shapedAtmosphere', error.message);
    }
    try {
      SceneExposure.settings(st.finish.sceneExposure);
    } catch (error) {
      bad('finish.sceneExposure', error.message);
    }
    try {
      Lightning.settings(st.finish.lightning);
    } catch (error) {
      bad('finish.lightning', error.message);
    }
    try {
      WindField.settings(st.finish.windField);
    } catch (error) {
      bad('finish.windField', error.message);
    }
    try {
      WeatherBinding.settings(st.finish.weatherBinding);
    } catch (error) {
      bad('finish.weatherBinding', error.message);
    }
    try {
      K.weather.tracks.compile(st.finish.skyEnvironment,st.finish.weatherTracks);
    } catch (error) {
      bad('finish.weatherTracks',error.message);
    }
    if (st.finish.cloudField !== undefined && st.finish.cloudField !== false) {
      try {
        K.clouds.compile(st.finish.cloudField);
      } catch (error) {
        bad('finish.cloudField', error.message);
      }
    }
    try {
      const cloudShadows = K.clouds.shadowSettings(st.finish.cloudShadows);
      if (cloudShadows && st.finish.cloudField === undefined)
        bad('finish.cloudShadows', 'Cloud shadows need a cloud field');
    } catch (error) {
      bad('finish.cloudShadows', error.message);
    }
    try {
      SkyEnvironment.aerial(st.finish.aerialPerspective);
    } catch (error) {
      bad('finish.aerialPerspective', error.message);
    }
    if (st.finish.skyReflections !== undefined && !['scene', 'material'].includes(st.finish.skyReflections))
      bad('finish.skyReflections', 'skyReflections must be scene or material');
    if (st.finish.surfaceEffects !== undefined) {
      try {
        surfaceEffects = K.splatEffects.context(st.finish.surfaceEffects);
      } catch (error) {
        bad('finish.surfaceEffects', error.message);
      }
    }
    let look = st.finish.look;
    try {
      look = K.authoring.looks.scene(look, catalog);
    } catch (error) {
      bad('finish.look.asset', error.message);
    }
    if (look?.coverageAware !== undefined && typeof look.coverageAware !== 'boolean')
      bad('finish.look.coverageAware', 'coverageAware must be a boolean');
    if (look?.pixelSize !== undefined && (!Number.isSafeInteger(look.pixelSize) || look.pixelSize < 1))
      bad('finish.look.pixelSize', 'pixelSize must be a positive integer');
    try {
      SilhouetteProtection.prepare(look?.silhouetteProtection);
    } catch (error) {
      bad('finish.look.silhouetteProtection', error.message);
    }
    try {
      DetailBudgets.prepare(look?.detailBudgets);
    } catch (error) {
      bad('finish.look.detailBudgets', error.message);
    }
    try {
      ShadowArt.prepare(look?.shadowArt);
    } catch (error) {
      bad('finish.look.shadowArt', error.message);
    }
    try {
      HorizonBands.compile(look?.horizonBands);
    } catch (error) {
      bad('finish.look.horizonBands', error.message);
    }
    try {
      ArtDirection.prepare(look?.artDirection);
    } catch (error) {
      bad('finish.look.artDirection', error.message);
    }
    try {
      EffectPalettes.prepare(look?.effectPalettes, st.palette);
    } catch (error) {
      bad('finish.look.effectPalettes', error.message);
    }
    try {
      ArtInk.prepare(look?.ink, st.palette);
    } catch (error) {
      bad('finish.look.ink', error.message);
    }
    try {
      ArtEffects.prepare(look?.effects, st.palette);
    } catch (error) {
      bad('finish.look.effects', error.message);
    }
    try {
      ArtStability.prepare(look?.stable);
    } catch (error) {
      bad('finish.look.stable', error.message);
    }
    try {
      PixelLook.toneSettings(look?.tone);
    } catch (error) {
      bad('finish.look.tone', error.message);
    }
    try {
      ColorCurves.prepare(look?.colorCurves);
    } catch (error) {
      bad('finish.look.colorCurves', error.message);
    }
    if (look?.colorLut !== undefined && look.colorLut !== false) {
      try {
        ColorLUT.normalize(look.colorLut);
      } catch (error) {
        bad('finish.look.colorLut', error.message);
      }
    }
    if (spec.light?.surfaceDirection !== undefined)
      try {
        SurfaceLook.prepareLightTrack(spec.light.surfaceDirection);
      } catch (error) {
        bad('light.surfaceDirection', error.message);
      }
    const pal = st.palette;
    if (!Array.isArray(pal) || pal.length < 2 || !pal.every(isNum))
      bad(
        'palette',
        'a palette is a list of colours as numbers',
        'for example [460811, 1382172, ...] (or 0x07080b in a .js file)'
      );
    else if (pal.length > 48)
      bad(
        'palette',
        'a palette holds 48 colours at most; this has ' + pal.length,
        'the picture is reduced to the palette by a shader that takes 48'
      );
    for (const [name, ramp] of Object.entries(st.roles)) {
      if (!Array.isArray(ramp) || !ramp.length)
        bad('roles.' + name, 'a role is a list of palette numbers, dark to light');
      else
        for (const i of ramp)
          if (!Number.isInteger(i) || i < 0 || i >= pal.length)
            bad('roles.' + name, 'colour ' + i + ' is not in the palette (0 to ' + (pal.length - 1) + ')');
    }
    try {
      PixelLook.prepareRemap(look?.paletteRemap, pal, st.roles);
    } catch (error) {
      bad('finish.look.paletteRemap', error.message);
    }
    try {
      PixelLook.prepareColorStack(look?.colorStack, pal, st.roles);
    } catch (error) {
      bad('finish.look.colorStack', error.message);
    }
    try {
      PixelLook.preparePaletteConstraints(look?.paletteConstraints, {
        palette: pal, roles: st.roles, blueNoise: K.procedural.materials.blueNoise, context: surfaceEffects, validateOnly: true
      });
    } catch (error) {
      bad('finish.look.paletteConstraints', error.message);
    }
    try {
      RenderStages.prepare(look?.renderStages, {
        palette: pal, roles: st.roles, blueNoise: K.procedural.materials.blueNoise,
        context: surfaceEffects, validateOnly: true
      });
    } catch (error) {
      bad('finish.look.renderStages', error.message);
    }
    try {
      RenderStages.optics(look?.optics, { palette: pal, roles: st.roles, blueNoise: K.procedural.materials.blueNoise, validateOnly: true });
    } catch (error) {
      bad('finish.look.optics', error.message);
    }
    const roleNames = Object.keys(st.roles),
      ids = new Set(),
      parts = new Set(),
      groups = spec.groups || {},
      assets = (env && env.assets) || {};
    const matOk = (m, path) => {
      if (m === undefined) return;
      const role = typeof m === 'string' ? m : m && m.role;
      if (m && typeof m === 'object') {
        keys(m, path, { role: 1, ramp: 1, noise: 1, scale: 1, glow: 1, over: 1, surface: 1, model: 1, lookAsset: 1, albedo: 1, materialId: 1, surfaceId: 1, pixelStyle: 1 });
        try { MaterialPixelStyle.prepare(m.pixelStyle); }
        catch (error) { bad(path + '.pixelStyle', error.message); }
        for (const key of ['materialId', 'surfaceId'])
          if (m[key] !== undefined && !TargetSelectors.name(m[key])) bad(path + '.' + key, key + ' must be a name');
        if (m.albedo !== undefined) {
          try { RenderStages.albedo(m.albedo, pal); }
          catch (error) { bad(path + '.albedo', error.message); }
        }
        if (m.model !== undefined) {
          const q = m.model, at = path + '.model', channels = { color: 1, emission: 1, roughness: 1, metallic: 1 };
          if (!q || typeof q !== 'object' || Array.isArray(q)) bad(at, 'model material channels need an object');
          else {
            keys(q, at, channels);
            for (const [channel, value] of Object.entries(q)) {
              const valid = channel === 'color' || channel === 'emission' ?
                isVec(value, 3) && value.every(v => v >= 0 && (channel === 'emission' || v <= 1)) :
                isNum(value) && value >= 0 && value <= 1;
              if (!valid) bad(at + '.' + channel, 'invalid model material channel');
            }
          }
        }
        if (m.surface !== undefined || m.lookAsset !== undefined) {
          try {
            const { surface } = materialLook({}, m, catalog);
            if (surface) K.surface.prepare(surface, pal, st.sun, surfaceEffects,
              { paletteRoles: st.roles, blueNoise: K.procedural.materials.blueNoise, validateOnly: true });
          } catch (error) {
            bad(path + (m.lookAsset !== undefined ? '.lookAsset' : '.surface'), error.message);
          }
        }
        if (m.ramp) {
          if (!Array.isArray(m.ramp) || m.ramp.some(i => !Number.isInteger(i) || i < 0 || i >= pal.length))
            bad(path + '.ramp', 'a ramp is a list of palette numbers (0 to ' + (pal.length - 1) + ')');
          return;
        }
        if (m.over) matOk(m.over.role, path + '.over.role');
      }
      if (typeof role !== 'string')
        bad(path, 'a material is a role name, or { "role": name, ... }', 'roles: ' + roleNames.join(', '));
      else if (!st.roles[role]) {
        const n = nearest(role, roleNames);
        bad(
          path,
          'no role called "' + role + '" in this style',
          n ? 'did you mean "' + n + '"?' : 'roles: ' + roleNames.join(', ')
        );
      }
    };
    const outlineOk = (o, path) => {
      if (!o || typeof o !== 'object')
        return bad(
          path,
          'an outline is { "svg": path } or { "ngon": sides, "r": size } or { "star": points, "r": outer, "inner": inner } or { "rect": [w, h] } or { "gear": teeth, "r": size }'
        );
      const k = ['svg', 'ngon', 'star', 'rect', 'gear'].filter(q => q in o);
      if (k.length !== 1) bad(path, 'an outline is one of svg, ngon, star, rect, gear');
      if (o.svg !== undefined && typeof o.svg !== 'string')
        bad(path + '.svg', 'the path is text, as in an SVG file ("M0 0 L10 0 ...")');
    };
    const typeOk = (v, type, path) => {
      if (Array.isArray(type)) {
        if (!type.includes(v)) bad(path, '"' + v + '" is not one of the choices', 'choices: ' + type.join(', '));
        return;
      }
      const alts = type.split('|'),
        one = t =>
          t === 'num'
            ? isNum(v)
            : t === 'pos'
              ? isNum(v) && v > 0
              : t === 'vec3'
                ? isVec(v, 3)
                : t === 'vec2'
                  ? isVec(v, 2)
                  : t === 'str'
                    ? typeof v === 'string'
                    : t === 'bool'
                      ? typeof v === 'boolean'
                      : t === 'list'
                        ? Array.isArray(v)
                        : t === 'obj'
                          ? v && typeof v === 'object'
                          : t === 'pts'
                            ? Array.isArray(v) && v.length >= 2 && v.every(p => isVec(p, 3))
                            : t === 'profile'
                              ? Array.isArray(v) && v.length >= 2 && v.every(p => isVec(p, 2))
                              : t === 'box'
                                ? Array.isArray(v) && v.length === 2 && v.every(p => isVec(p, 3))
                                : null;
      if (type === 'mat') return matOk(v, path);
      if (type === 'solid') return solidOk(v, path, true);
      if (type === 'outline') return outlineOk(v, path);
      if (type === 'join') {
        if (!K.sdf.JOIN[v]) {
          const n = nearest(v, Object.keys(K.sdf.JOIN));
          bad(
            path,
            'no way of joining called "' + v + '"',
            n ? 'did you mean "' + n + '"?' : 'ways: ' + Object.keys(K.sdf.JOIN).join(', ')
          );
        }
        return;
      }
      if (!alts.some(one))
        bad(
          path,
          'this should be ' +
            alts
              .map(
                t =>
                  ({
                    num: 'a number',
                    pos: 'a number above 0',
                    vec3: 'three numbers [x, y, z]',
                    vec2: 'two numbers',
                    str: 'text',
                    bool: 'true or false',
                    list: 'a list',
                    obj: 'an object',
                    pts: 'a list of two or more [x, y, z] points',
                    profile: 'a list of [height 0..1, radius] pairs',
                    box: 'two corners [[x, y, z], [x, y, z]]'
                  })[t]
              )
              .join(' or '),
          'it is ' + JSON.stringify(v)
        );
    };
    const fields = (o, path, def, extra) => {
      const all = Object.assign({ kind: 1, do: 1 }, extra, def.need, def.may);
      keys(o, path, all);
      for (const [k, t] of Object.entries(def.need))
        if (o[k] === undefined)
          bad(path + '.' + k, 'missing', 'a ' + (o.kind || o.do) + ' needs: ' + Object.keys(def.need).join(', '));
      for (const [k, t] of Object.entries(Object.assign({}, extra, def.need, def.may)))
        if (o[k] !== undefined && t !== 1) typeOk(o[k], t, path + '.' + k);
    };
    let area = 0;
    const res0 = st.finish.res || 0.09;
    function solidOk(s, path, inner) {
      if (!s || typeof s !== 'object')
        return bad(path, 'a solid is an object with a "kind"', 'kinds: ' + Object.keys(DIO.kinds).join(', '));
      const def = DIO.kinds[s.kind];
      if (!def) {
        const n = nearest(s.kind, Object.keys(DIO.kinds));
        return bad(
          path + '.kind',
          'no kind of solid called "' + s.kind + '"',
          n ? 'did you mean "' + n + '"?' : 'kinds: ' + Object.keys(DIO.kinds).join(', ')
        );
      }
      fields(s, path, def, COMMON);
      if (K.drawing.kind(s)) {
        try {
          K.drawing.prepare(s);
        } catch (error) {
          bad(path, error.message);
        }
      }
      if (s.id !== undefined) {
        if (ids.has(s.id)) bad(path + '.id', 'two solids are called "' + s.id + '"');
        ids.add(s.id);
      }
      if (s.part && !inner) parts.add(s.part);
      if (s.tags !== undefined && (!Array.isArray(s.tags) || !s.tags.every(TargetSelectors.name)))
        bad(path + '.tags', 'tags must be a list of names');
      if (s.surfaceId !== undefined && !TargetSelectors.name(s.surfaceId))
        bad(path + '.surfaceId', 'surfaceId must be a name');
      if (s.part && inner)
        bad(path + '.part', 'a solid inside another cannot be a part of its own', 'put "part" on the outer one');
      if (s.group !== undefined && !groups[s.group])
        bad(
          path + '.group',
          'no group called "' + s.group + '"',
          'groups are declared at the top: "groups": { "' + s.group + '": { "blend": 0.2 } }'
        );
      if (s.carve && s.part) bad(path, 'a carving cannot be a moving part');
      if (s.separate && (!['ball', 'torus'].includes(s.kind) || s.carve || s.group || s.hold || inner))
        bad(path + '.separate', 'separate model geometry needs an independent ball or torus');
      if (s.kind === 'mesh' && typeof s.asset === 'string' && !assets[s.asset])
        bad(
          path + '.asset',
          'no mesh called "' + s.asset + '" was handed in',
          Object.keys(assets).length
            ? 'meshes: ' + Object.keys(assets).join(', ')
            : 'pass { assets: { "' + s.asset + '": mesh } } when building'
        );
      if (s.kind === 'warp' && s.twist === undefined && s.bend === undefined && s.taper === undefined)
        bad(path, 'a warp needs one of twist, bend, taper');
      if (s.kind === 'fold' && s.polar === undefined && s.mirror === undefined && s.repeat === undefined)
        bad(path, 'a fold needs one of polar, mirror, repeat');
      if (s.res !== undefined && isNum(s.res) && s.res < 0.03)
        warn(
          path + '.res',
          'a grain of ' + s.res + ' is very fine',
          'most solids want 0.06 to 0.15; the count goes up with the square'
        );
      const r = isNum(s.r)
          ? s.r
          : isVec(s.r, 3)
            ? Math.max(...s.r)
            : isVec(s.half, 3)
              ? Math.hypot(...s.half)
              : s.kind === 'ground'
                ? (s.rad || 8) * 0.56
                : 1,
        g = isNum(s.res) ? s.res : res0;
      if (!inner && !s.carve) area += (12.6 * r * r) / (g * g);
    }
    if (!Array.isArray(spec.solids))
      bad(
        'solids',
        'a diorama needs a list of solids',
        'for example [{ "kind": "ground", "mat": "earth" }, { "kind": "ball", "at": [0, 1, 0], "r": 1, "mat": "stone" }]'
      );
    else spec.solids.forEach((s, i) => solidOk(s, 'solids[' + i + ']'));
    for (const [g, v] of Object.entries(groups))
      if (!v || !isNum(v.blend))
        bad('groups.' + g, 'a group says how far its members melt into each other', '{ "blend": 0.2 }');
    for (const [p, v] of Object.entries(spec.parts || {})) {
      if (!parts.has(p))
        bad(
          'parts.' + p,
          'no solid is marked as part "' + p + '"',
          parts.size ? 'parts: ' + [...parts].join(', ') : 'mark a solid with "part": "' + p + '"'
        );
      if (v.joint !== undefined && !isVec(v.joint, 3)) bad('parts.' + p + '.joint', 'a joint is a point [x, y, z]');
      if (v.parent !== undefined && !parts.has(v.parent))
        bad('parts.' + p + '.parent', 'no part called "' + v.parent + '"');
      if (v.parent === p) bad('parts.' + p + '.parent', 'a part cannot hang from itself');
      keys(v, 'parts.' + p, { joint: 1, parent: 1 });
    }
    const listOf = (name, table) => {
      const l = spec[name];
      if (l === undefined) return;
      if (!Array.isArray(l)) return bad(name, 'this is a list');
      l.forEach((m, i) => {
        const path = name + '[' + i + ']',
          def = m && table[m.do];
        if (!def)
          return bad(
            path + '.do',
            'nothing called "' + (m && m.do) + '" to do here',
            'choices: ' + Object.keys(table).join(', ')
          );
        fields(m, path, def);
        for (const k of ['part', 'follow'])
          if (typeof m[k] === 'string' && !parts.has(m[k])) {
            const n = nearest(m[k], [...parts]);
            bad(
              path + '.' + k,
              'no part called "' + m[k] + '"',
              n
                ? 'did you mean "' + n + '"?'
                : parts.size
                  ? 'parts: ' + [...parts].join(', ')
                  : 'mark a solid with "part": "' + m[k] + '"'
            );
          }
        if (m.keys !== undefined && (!m.loop || !Array.isArray(m.keys) || m.keys.filter(isNum).length < 4))
          bad(
            path + '.keys',
            'keys are times and values in turn, with "loop" saying how long before they repeat',
            '"keys": [0, 0, 1, 0.5, 2, 0], "loop": 2'
          );
      });
    };
    listOf('motion', MOTION);
    listOf('effects', EFFECT);
    if (spec.tap !== undefined) {
      keys(spec.tap, 'tap', { do: 1, colours: 1, n: 1 });
      if (!['dust', 'sparks', 'embers'].includes(spec.tap.do)) bad('tap.do', 'a tap can raise dust, sparks or embers');
      matOk(spec.tap.colours, 'tap.colours');
    }
    if (spec.camera) {
      keys(spec.camera, 'camera', { target: 1, dist: 1, pitch: 1, yaw: 1, sway: 1 });
      if (spec.camera.target !== undefined && !isVec(spec.camera.target, 3))
        bad('camera.target', 'three numbers [x, y, z]');
    }
    if (area > 150000)
      warn(
        'solids',
        'about ' + Math.round(area / 1000) + ',000 splats by a rough count: heavy on a phone',
        'coarser "res" on the big solids brings it down fastest'
      );
    return out;
  };
  DIO.report = list =>
    list
      .map(
        p =>
          (p.level === 'error' ? 'error    ' : 'warning  ') +
          (p.path || '(the whole thing)') +
          ': ' +
          p.problem +
          (p.hint ? '\n           ' + p.hint : '')
      )
      .join('\n');

  // The splat runtime and GLB exporter evaluate the same authored motion.
  function partMotion(B, rig, order, joint, PI, motion) {
    const wave = (m, t) =>
      m.keys
        ? K.kf(t % m.loop, m.keys)
        : (m.amount === undefined ? 0.3 : m.amount) * Math.sin(TAU * (t / (m.period || 3) + (m.phase || 0)));
    return t => {
      for (const p of order) {
        let A = M.id(),
          off = [0, 0, 0];
        for (const m of motion) {
          if (m.part !== p) continue;
          const ax = B.norm(m.axis || [0, 1, 0]);
          if (m.do === 'turn') A = M.mul(M.rot(ax, wave(m, t)), A);
          else if (m.do === 'spin') A = M.mul(M.rot(ax, (m.speed === undefined ? 1 : m.speed) * t), A);
          else if (m.do === 'bob') off = V.mad(off, ax, wave(m, t));
          else if (m.do === 'squash') A = M.mul(M.stretch(ax, 1 + wave(m, t), true), A);
        }
        const j = joint[p];
        if (PI[p] && PI[p].parent) {
          rig.child(p, PI[p].parent, A, j);
        } else rig.set(p, A, j, V.add(j, off));
      }
    };
  }

  // ---------------- building ----------------
  DIO.build = (spec, env, modelOptions) => {
    env = env || {};
    const problems = DIO.check(spec, env),
      errs = problems.filter(p => p.level === 'error');
    if (errs.length) {
      const e = new Error(
        'diorama "' +
          (spec && spec.id) +
          '" has ' +
          errs.length +
          ' mistake' +
          (errs.length > 1 ? 's' : '') +
          ':\n' +
          DIO.report(errs)
      );
      e.problems = problems;
      throw e;
    }
    const st0 = styleOf(spec), catalog = lookCatalog(spec),
      seed = spec.seed === undefined ? 1 : spec.seed,
      effects = spec.effects || [],
      motion = spec.motion || [],
      lamps = effects.filter(e => e.do === 'lamp'),
      loose = effects.some(e => ['dust', 'embers', 'smoke', 'sparks', 'rain'].includes(e.do)) || !!spec.tap;
    st0.finish = K.authoring.environments.apply(st0.finish,spec.environmentPreset,catalog,st0.palette);
    st0.finish.look = K.authoring.looks.scene(st0.finish.look, catalog);
    let pal = st0.palette;
    const meshLooks = {};
    for (const s of spec.solids)
      if (s.kind === 'mesh' && s.mat === undefined) {
        const mesh = K.mesh.fit(env.assets[s.asset], { size: s.size || 4, at: s.at, turn: s.spin, up: s.up });
        meshLooks[s.asset] = { mesh, look: K.mesh.look(mesh, { hues: s.hues || 5, pal }) };
      }
    const { detailBudgets, shadowArt } = st0.finish.look ?? {};
    const B = (env.makeBuilder || makeBuilder)(seed, pal, detailBudgets === undefined && shadowArt === undefined ?
      undefined : { detailBudgets, shadowArt });
    let S, grp;
    function startSculpt() {
      S = K.sculpt((env.makeSculpt || makeSculpt)(B));
      S.sun = B.norm(st0.sun);
      if (st0.finish.look?.pixel) S.pixel = true;
      S.captureAlbedo = Boolean(st0.finish.liveSun) ||
        Array.isArray(st0.finish.look?.renderStages) && st0.finish.look.renderStages.some(rule => rule.stage === 'material');
      if (st0.amb !== undefined) S.amb = st0.amb;
      if (st0.sky !== undefined) S.sky = st0.sky;
      if (st0.finish.res) S.res = st0.finish.res;
      grp = {};
      for (const [g, v] of Object.entries(spec.groups || {})) grp[g] = S.grp(v.blend);
    }
    startSculpt();
    const rig = modelOptions ? null : K.rig(B, S),
      cap = !modelOptions && lamps.length ? K.light.capture(B, S) : null;
    const ramp = m => (typeof m === 'string' ? st0.roles[m] : m.ramp || st0.roles[m.role]),
      matOf = m => {
        if (m === undefined) m = 'stone';
        const r = ramp(m),
          out = { r, materialId: typeof m === 'string' ? m : m.materialId ?? m.role };
        if (typeof m === 'object') {
          const sc = m.scale || 0.7;
          if (m.noise) out.mod = (x, y, z) => m.noise * (B.n3(x * sc, y * sc, z * sc) - 0.5);
          if (m.glow) out.em = true;
          if (m.model) out.model = m.model;
          if (m.albedo !== undefined) out.albedo = m.albedo;
          if (m.surfaceId !== undefined) out.surfaceId = m.surfaceId;
          if (m.pixelStyle !== undefined) out.pixelStyle = m.pixelStyle;
          if (m.over) {
            const r2 = ramp(m.over.role),
              above = m.over.above === undefined ? 0.55 : m.over.above,
              patch = m.over.patch === undefined ? 0.5 : m.over.patch;
            out.tex = (x, y, z, ny, t) =>
              ny > above && B.n3(x * 0.9 + 3, y * 0.9, z * 0.9 + 7) > 1 - patch
                ? r2[K.clamp(Math.floor(t * r2.length), 0, r2.length - 1)]
                : undefined;
          }
          if (m.surface !== undefined || m.lookAsset !== undefined) return materialLook(out, m, catalog);
        }
        return out;
      };
    const outline = o =>
      o.svg !== undefined
        ? K.poly2.svg(o.svg, o.size || 2)
        : o.ngon !== undefined
          ? K.poly2.ngon(o.ngon, o.r || 1)
          : o.star !== undefined
            ? K.poly2.star(o.star, o.r || 1, o.inner || (o.r || 1) * 0.5)
            : o.gear !== undefined
              ? K.poly2.gear(o.gear, o.r || 1, o.depth || (o.r || 1) * 0.2)
              : K.poly2.rect(o.rect[0], o.rect[1]);
    const made = {},
      make = (s, held) => {
        const o = { res: s.res, objectId: s.part ?? s.id };
        if (s.id || s.surfaceId || s.tags?.length) o.target = {
          ...(s.id && { entity: s.id }), ...(s.surfaceId && { surface: s.surfaceId }), ...(s.tags?.length && { tags: s.tags })
        };
        if (s.res === undefined) delete o.res;
        if (s.part) {
          o.tag = s.part;
          o.whole = true;
        }
        if (s.group) Object.assign(o, grp[s.group]);
        if (s.carve) o.neg = true;
        if (s.ghost) o.ghost = true;
        if (s.separate) o.model = { separate: true, name: s.id ?? s.part ?? s.kind };
        if (s.bump) o.bump = s.bump;
        if (held || s.hold) o.hold = true;
        if (s.turn) o.ax = B.frame(s.turn[0], s.turn[1], s.turn[2]);
        const m = matOf(s.mat),
          sub = q => make(q, true),
          k = s.kind;
        let p;
        if (k === 'ground') p = S.ground(m, Object.assign({ rad: s.rad || 8 }, s.stretch ? { zs: s.stretch } : {}, o));
        else if (k === 'ball') p = S.ball(s.at, s.r, m, o);
        else if (k === 'rock') p = S.rock(s.at, s.r, m, o);
        else if (k === 'box') p = S.box(s.at, s.half, m, Object.assign(s.round ? { rd: s.round } : {}, o));
        else if (k === 'lathe')
          p = S.lathe(s.at, s.h, Array.isArray(s.r) && Array.isArray(s.r[0]) ? t => K.kf(t, s.r.flat()) : s.r, m, o);
        else if (k === 'torus') p = S.torus(s.at, s.R, s.r, m, o);
        else if (k === 'tube')
          p = S.tube(s.pts, Array.isArray(s.r) ? s.r[0] : s.r, Array.isArray(s.r) ? s.r[1] : s.r, m, o);
        else if (K.drawing.kind(s)) p = K.drawing.solid(S, s, m, o);
        else if (k === 'regular')
          p = S.regular(s.shape, s.at, s.r, m, Object.assign(s.round ? { rd: s.round } : {}, o));
        else if (k === 'extrude')
          p = S.extrude(outline(s.outline), s.at, s.depth, m, Object.assign(s.round ? { rd: s.round } : {}, o));
        else if (k === 'revolve') p = S.revolve(outline(s.outline), s.at, m, o);
        else if (k === 'puff') p = S.puff(outline(s.outline), s.at, s.height, m, o);
        else if (k === 'mesh') {
          const ml = meshLooks[s.asset] || {
            mesh: K.mesh.fit(env.assets[s.asset], { size: s.size || 4, at: s.at, turn: s.spin, up: s.up })
          };
          p = S.mesh(ml.mesh, s.mat === undefined ? ml.look : m, Object.assign({ cells: s.cells, thick: s.thick }, o));
        } else if (k === 'join') p = S.join(s.how, sub(s.a), sub(s.b), Object.assign({ r: s.size, n: s.steps }, o));
        else if (k === 'fold')
          p = S.fold(
            sub(s.of),
            s.polar
              ? { polar: s.polar, c: s.centre || [0, 0, 0], axis: s.axis }
              : s.mirror
                ? { mirror: s.mirror, c: s.centre || [0, 0, 0] }
                : { repeat: s.repeat, count: s.count || [1, 1, 1] },
            o
          );
        else if (k === 'warp')
          p = S.warp(
            sub(s.of),
            Object.assign(
              { c: s.centre || [0, 0, 0] },
              s.twist !== undefined ? { twist: s.twist } : s.bend !== undefined ? { bend: s.bend } : { taper: s.taper },
              s.wide ? { wide: s.wide } : {}
            ),
            o
          );
        else if (k === 'shell') p = S.shell(sub(s.of), s.t, o);
        else if (k === 'swell') p = S.swell(sub(s.of), s.by, o);
        else if (k === 'rough') {
          const sc = s.scale || 1.5;
          p = S.rough(sub(s.of), (x, y, z) => B.n3(x * sc, y * sc, z * sc) - 0.5, s.by, o);
        } else if (k === 'bubbles') p = S.bubbles(sub(s.of), Object.assign({ cell: s.cell || 0.5, h: s.h || 0.12 }, o));
        else {
          const mats = { stone: m, post: m, rail: m, metal: m },
            oo = Object.assign({}, s, { mats, tag: s.part, res: s.res, objectId: o.objectId, target: o.target });
          p =
            k === 'pillar'
              ? K.build.pillar(S, s.at, s.h, oo)
              : k === 'arch'
                ? K.build.arch(S, s.at, oo)
                : k === 'stairs'
                  ? K.build.stairs(S, s.at, s.dir, s.rise, oo)
                  : k === 'fence'
                    ? K.build.fence(S, s.a, s.b, oo)
                    : K.build.pipe(S, s.pts, oo);
        }
        if (s.id) made[s.id] = p;
        return p;
      };
    if (modelOptions) {
      const groups = new Map(), meshes = [];
      const { duration = 4, fps = 30, resolution, method, bounds, targetTriangles } = modelOptions;
      for (const solid of spec.solids) {
        // Ground is an infinite half-space in the sculpt API. Ghosts are render overlays.
        if (solid.kind === 'ground' || (solid.ghost && !solid.separate)) continue;
        const name = solid.part || null;
        if (!groups.has(name)) groups.set(name, []);
        groups.get(name).push(solid);
      }
      if (!groups.size) throw new Error('The diorama contains no finite model geometry');
      const parts = spec.parts || {}, names = [], visiting = new Set();
      function place(name) {
        if (visiting.has(name)) throw new Error('Scene rig has a parent cycle at ' + name);
        if (names.includes(name)) return;
        visiting.add(name);
        if (parts[name]?.parent) {
          if (!groups.has(parts[name].parent)) throw new Error('Missing export geometry for part ' + parts[name].parent);
          place(parts[name].parent);
        }
        names.push(name);
        visiting.delete(name);
      }
      for (const name of groups.keys()) if (name !== null) place(name);
      const { rig: previewRig } = names.length ? DIO.build(spec, env).lab : {};
      const joints = [], joint = {};
      for (const name of [null, ...names]) {
        if (!groups.has(name)) continue;
        startSculpt();
        for (const solid of groups.get(name)) make(solid);
        let detail = name === null ? resolution ?? 0.08 :
          Math.min(resolution ?? 0.08, ...groups.get(name).map(solid => solid.res ?? Infinity));
        const hasBody = groups.get(name).some(solid => !solid.separate && !solid.carve);
        const restBounds = (name === null ? bounds : undefined) ?? (hasBody ? S.modelBounds(detail * 2) : undefined);
        if (resolution === undefined && name === null && restBounds) {
          const volume = restBounds.max.reduce((v, high, i) => v * (high - restBounds.min[i]), 1);
          detail = Math.max(detail, Math.cbrt(volume / 400000));
        }
        const mesh = K.model.fromSculpt(S, {
          name: name ?? spec.id, palette: pal, resolution: detail, method, bounds: restBounds, targetTriangles
        });
        if (name === null) meshes.push(...K.model.mapModelMeshes(mesh, part => ({ ...part, static: true })));
        else {
          const index = joints.length, box = previewRig.box(name);
          joint[name] = parts[name]?.joint || (box ? [(box.lo[0] + box.hi[0]) * 0.5, box.lo[1], (box.lo[2] + box.hi[2]) * 0.5] : mesh.points[0]);
          joints.push({ name, parent: parts[name]?.parent ? names.indexOf(parts[name].parent) : null,
            head: joint[name], tail: V.mad(joint[name], [0, 1, 0], box ? Math.max(0.05, box.hi[1] - box.lo[1]) : 0.1) });
          meshes.push(...K.model.mapModelMeshes(mesh, part => ({ ...part, weights: part.points.map(() => [[index, 1]]) })));
        }
      }
      const animations = motion.length ? K.model.sampleClips([{ name: 'Scene motion', duration, fps,
        pose: partMotion(B, previewRig, names, joint, parts, motion) }], (pose, time) => {
        pose(time);
        return names.map(name => {
          const index = previewRig.names.indexOf(name);
          if (index < 0) throw new Error('Splat rig has no part ' + name);
          return Array.from(previewRig.M.slice(index * 12, index * 12 + 12));
        });
      }) : [];
      return { meshes, joints, animations };
    }
    const drawingBounds = new Map();
    function placeSolid(s) {
      const p = make(s);
      if (K.drawing.kind(s) && p.geometryBounds) drawingBounds.set(s, p.geometryBounds);
    }
    for (const s of spec.solids) if (!s.part) placeSolid(s);
    S.bake();
    const moving = spec.solids.filter(s => s.part);
    if (moving.length) {
      for (const s of moving) placeSolid(s);
      S.bake();
    }
    const pool = loose ? K.pool(B, spec.spare || 600) : null,
      lo = [1e9, 1e9, 1e9],
      hi = [-1e9, -1e9, -1e9];
    for (const s of spec.solids) {
      const b = drawingBounds.get(s) ?? (s.at && s.kind !== 'ground' ? { min: s.at, max: s.at } : null);
      if (b) for (let a = 0; a < 3; a++) {
        lo[a] = Math.min(lo[a], b.min[a]);
        hi[a] = Math.max(hi[a], b.max[a]);
      }
    }
    const cam = Object.assign(
      {
        target: lo[0] > 1e8 ? [0, 1.5, 0] : [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2 + 0.5, (lo[2] + hi[2]) / 2],
        dist: 16,
        pitch: 0.16,
        yaw: 0.4,
        sway: 0.3
      },
      spec.camera
    );
    const W = B.finish(
      Object.assign(
        { cam, detail: 14, palName: typeof spec.style === 'string' ? spec.style : 'Data', dither: 0.25, radius: 9 },
        st0.finish,
        { made, spec, paletteRoles: st0.roles,
          ...(spec.light?.surfaceDirection !== undefined && { surfaceLight: spec.light.surfaceDirection }) }
      )
    );
    if (!moving.length && !effects.length && !spec.tap) return W;
    const st = K.stage(W);
    rig.bind(st);
    const partNames = [...new Set(moving.map(s => s.part))],
      PI = spec.parts || {},
      joint = {};
    for (const p of partNames) {
      const bx = rig.box(p),
        j = PI[p] && PI[p].joint;
      joint[p] = j || (bx ? [(bx.lo[0] + bx.hi[0]) / 2, bx.lo[1], (bx.lo[2] + bx.hi[2]) / 2] : [0, 0, 0]);
    }
    const order = partNames.slice().sort((a, b) => {
      const depth = p => {
        let d = 0;
        while (PI[p] && PI[p].parent && d < 20) {
          p = PI[p].parent;
          d++;
        }
        return d;
      };
      return depth(a) - depth(b);
    });
    const poseParts = partMotion(B, rig, order, joint, PI, motion);
    if (partNames.length)
      st.add({
        update(dt, t) {
          poseParts(t);
          rig.apply();
        }
      });
    let lit = null;
    if (lamps.length) {
      const L = lamps.map(e => ({ p: e.at.slice(), r: e.r || 6, s: e.strength || 0.9, e, s0: e.strength || 0.9 }));
      lit = K.light.system(st, cap, L, { sun: { dir: S.sun, amb: S.amb, sky: S.sky, k: S.sunK, parts: partNames } });
      st.add(lit);
      let acc = 0;
      st.add({
        update(dt, t) {
          acc += dt;
          if (acc < 1 / 12) return;
          acc = 0;
          let moved = false;
          L.forEach((l, i) => {
            if (l.e.flicker) {
              l.s = l.s0 * (1 - l.e.flicker * (0.5 + 0.5 * Math.sin(t * 9.1 + i * 2.3) * Math.sin(t * 5.3 + i)));
              moved = true;
            }
            if (l.e.follow) {
              l.p = rig.at(l.e.follow, l.e.at);
              moved = true;
            }
          });
          if (moved) lit.touch();
        }
      });
    }
    let ps = null;
    if (loose) {
      const winds = effects.filter(e => e.do === 'wind'),
        flow = winds.length
          ? K.flow.sum(
              ...winds.map(w => (w.swirl ? K.flow.sum(K.flow.wind(w.v), K.flow.curl(0.35, w.swirl)) : K.flow.wind(w.v)))
            )
          : undefined;
      ps = K.particles(st, pool, { flow, ground: () => 0 });
      const cols = (e, role) => {
          const r = ramp(e.colours === undefined ? role : e.colours);
          return r.slice().reverse();
        },
        timers = effects.map(() => 0);
      st.add({
        update(dt, t) {
          effects.forEach((e, i) => {
            if (e.do === 'rain') {
              timers[i] += (e.rate || 60) * dt;
              const n = Math.floor(timers[i]);
              timers[i] -= n;
              if (n) ps.rain(e.box, n, cols(e, 'water'));
              return;
            }
            if (!ps[e.do] || !e.at) return;
            timers[i] -= dt;
            if (timers[i] > 0) return;
            timers[i] = e.every || 0.5;
            const n = e.n || 3;
            if (e.do === 'dust') ps.dust(e.at, n, cols(e, 'earth'), e.spread);
            else if (e.do === 'embers') ps.embers(e.at, n, cols(e, 'ember'));
            else if (e.do === 'smoke') ps.smoke(e.at, n, cols(e, 'dark'));
            else if (e.do === 'sparks') ps.sparks(e.at, n, cols(e, 'glow'), e.dir || null, e.speed);
          });
        },
        poke(hit) {
          if (!hit || !spec.tap) return;
          const t = spec.tap,
            c = cols(t, t.do === 'dust' ? 'earth' : 'ember'),
            n = t.n || 12;
          if (t.do === 'dust') ps.dust(hit.p, n, c, 1.5);
          else if (t.do === 'embers') ps.embers(hit.p, n, c);
          else ps.sparks(hit.p, n, c, null, 4);
        }
      });
      st.add(ps);
    }
    const rv = effects.find(e => e.do === 'reveal');
    if (rv) st.add(K.fx.reveal(st, { auto: true, dur: rv.dur || 1.4, block: rv.block || 0.6 }));
    W.lab = { rig, ps, lit, parts: partNames };
    return W;
  };
  DIO.scene = (spec, env) => {
    const id = 'drawing:' + spec.id, seed0 = spec.seed ?? 1;
    const editable = s => K.drawing.kind(s) && typeof s.id === 'string';
    const resolve = (seed, snapshot) => {
      if (snapshot === undefined) return { ...spec, seed: seed ?? seed0 };
      const state = K.authoring.data.validate(snapshot);
      if (state.id !== id) throw Error('Drawing snapshot belongs to a different scene');
      const marks = new Map(Object.values(state.entities).map(({ id, type, parameters, anchor, parent, styleRef }) => {
        const mark = { ...parameters, id, kind: type };
        if (!K.drawing.kind(mark)) throw Error('Invalid drawing entity: ' + id);
        if (anchor || parent || styleRef) throw Error('Set carrier, part and material in drawing parameters: ' + id);
        return [id, mark];
      }));
      const solids = [];
      for (const s of spec.solids) {
        if (!editable(s)) solids.push(s);
        else if (marks.has(s.id)) {
          solids.push(marks.get(s.id));
          marks.delete(s.id);
        }
      }
      return { ...spec, seed: seed ?? state.seed, solids: solids.concat([...marks.values()]) };
    };
    const build = (seed, { snapshot } = {}) => DIO.build(resolve(seed, snapshot), env);
    const authoring = (seed, { snapshot } = {}) => {
      const A = K.authoring;
      let document;
      if (snapshot === undefined) {
        const start = A.document({ ...A.document().snapshot(), id, seed: seed ?? seed0 });
        start.transact('Load drawings', () => {
          for (const { id, kind, ...parameters } of spec.solids.filter(editable))
            start.create(kind, { id, parameters });
        });
        document = A.document(start.snapshot());
      } else {
        resolve(seed, snapshot);
        document = A.document(snapshot);
      }
      return {
        document,
        realize(state = document.snapshot()) {
          try {
            return { world: build(seed, { snapshot: state }) };
          } catch (error) {
            if (!error.problems) throw error;
            return {
              checks: error.problems.filter(p => p.level === 'error').map(({ path, problem }) =>
                ({ pass: false, path, message: problem }))
            };
          }
        }
      };
    };
    return {
      id: spec.id,
      name: spec.name || spec.id,
      blurb: spec.blurb || '',
      seed: seed0,
      build,
      model: (seed, { snapshot, ...options } = {}) =>
        DIO.build(resolve(seed, snapshot), env, options),
      authoring
    };
  };
  DIO.roles = ROLES;
})(KIT);

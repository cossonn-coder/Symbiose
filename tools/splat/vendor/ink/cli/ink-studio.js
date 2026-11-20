#!/usr/bin/env node
// ink-studio: look at, measure and check a diorama without opening a browser.   ink-studio help
// Run inside a project that has an ink-studio.config.js ({ load: () => its built module, out, snaps }), or alone, where it shows the library's own demos.
const fs = require('fs'),
  path = require('path'),
  R = require('./render.js'),
  PNG = require('./png.js'),
  ArtDirection = require('../src/art-direction.js');
const CWD = process.cwd();
let cfg = {};
try {
  cfg = require(path.join(CWD, 'ink-studio.config.js'));
} catch (e) {
  if (e.code !== 'MODULE_NOT_FOUND' || !/ink-studio\.config/.test(e.message)) throw e;
}
const OUT = path.resolve(CWD, cfg.out || 'studio/out'),
  SNAPS = path.resolve(CWD, cfg.snaps || 'studio/snaps');
const argv = process.argv.slice(2),
  cmd = argv[0] || 'help',
  pos = [],
  opt = {};
for (let i = 1; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith('--')) {
    const k = a.slice(2),
      v = argv[i + 1];
    if (v === undefined || v.startsWith('--')) opt[k] = true;
    else {
      opt[k] = v;
      i++;
    }
  } else pos.push(a);
}
const Shot = require('./shot-recipes.js');
let shot, shotReplay, shotRender;
const outputFile = name => opt.out ? path.resolve(opt.out) : path.join(OUT,name);
const num = (k, d) => (opt[k] === undefined ? d : +opt[k]),
  list = (k, d) => (opt[k] === undefined ? d : String(opt[k]).split(',').map(Number));
let A = null;
const importedAssets = new Map();
const lib = () => A || (A = cfg.load ? cfg.load() : require('../index.js').load());
// a diorama by its id, or a file in lab/ that exports (kit) => ({ id, name, seed, build })
/* a mesh file is a diorama too: fitted to --size, coloured from its own materials, baked and looked at like the rest */
function meshScene(file) {
  const kit = lib(),
    K = kit.KIT,
    raw = require('../index.js').readMesh(path.resolve(file));
  return {
    id: path.basename(file).replace(/\W+/g, '-'),
    name: path.basename(file),
    seed: 1,
    build(seed) {
      const size = num('size', 6);
      const asset = importedAssets.get(path.resolve(file));
      if (asset) {
        const world = K.authoring.assetSurfaces.world(asset, {
          size, res: num('res', size / 70), turn: num('spin', 0), up: opt.up,
          hues: num('hues', 10), shades: num('shades', 5), geometry: opt.geometry,
          cells: num('cells', 64), thick: opt.thick === undefined ? undefined : +opt.thick,
          resolution: opt.resolution === undefined ? undefined : +opt.resolution
        });
        return world;
      }
      const mesh = K.mesh.fit(raw, { size, up: opt.up, turn: num('spin', 0) }),
        look = K.mesh.look(mesh, { hues: num('hues', 6), shades: num('shades', 4) }),
        B = kit.makeBuilder(seed, look.pal),
        S = K.sculpt(kit.makeSculpt(B));
      const sol = S.mesh(mesh, look, {
        res: num('res', size / 70),
        cells: num('cells', 64),
        thick: opt.thick === undefined ? undefined : +opt.thick
      });
      S.bake();
      const b = K.mesh.box(mesh);
      return B.finish({
        cam: { target: [0, (b.lo[1] + b.hi[1]) / 2, 0], dist: size * 2.6, pitch: 0.2, yaw: 0.5, sway: 0.3 },
        detail: 14,
        palName: 'Mesh',
        dither: 0.25,
        radius: size * 1.2,
        mesh: Object.assign(K.mesh.info(raw), { hues: look.ramps.length, sheet: sol.field.open, cell: sol.field.h })
      });
    }
  };
}
/* a diorama written as data (see lab/data-shrine.json). --style puts it in another style; meshes it names are looked for beside the file */
function dataScene(file, override, { installedPacks = false } = {}) {
  const K = lib().KIT,
    spec = override ? { ...override } : JSON.parse(fs.readFileSync(path.resolve(file), 'utf8')),
    dir = path.dirname(path.resolve(file)),
    assets = {};
  if (opt.style) spec.style = opt.style;
  if (opt['shadow-art'] !== undefined)
    spec.finish = { ...spec.finish, look: { ...K.diorama.sceneLook(spec), shadowArt: shadowArtOption() } };
  if (!installedPacks && opt['asset-pack'] !== undefined)
    spec.assetPacks = require('./asset-pack.js').install(K.authoring.assetPacks, spec.assetPacks, opt['asset-pack']);
  for (const s of spec.solids || [])
    if (s && s.kind === 'mesh' && typeof s.asset === 'string' && !assets[s.asset]) {
      const f = ['', '.obj', '.glb', '.gltf']
        .map(e => path.join(dir, s.asset + e))
        .find(q => fs.existsSync(q) && fs.statSync(q).isFile());
      if (f) assets[s.asset] = require('../index.js').readMesh(f);
    }
  const problems = K.diorama.check(spec, { assets });
  if (problems.length) console.error(K.diorama.report(problems));
  if (problems.some(p => p.level === 'error'))
    die('not built: ' + problems.filter(p => p.level === 'error').length + ' mistake(s) in ' + file);
  const descriptor=K.diorama.scene(spec,{assets});
  const atlases=new Map();
  return { ...descriptor, lookPreviewPacks:spec.assetPacks, build(...args) {
    const world=descriptor.build(...args);
    if (Array.isArray(world.spriteAtlases)) world.spriteAtlases=world.spriteAtlases.map(placement=>{
      if (typeof placement?.atlas!=='string') return placement;
      const file=path.resolve(dir,placement.atlas);
      if (!atlases.has(file)) atlases.set(file,require('./sprite-atlas.js').readSpriteAtlas(file));
      return K.sprite.placeAtlas({ ...placement, atlas:atlases.get(file) });
    });
    return world;
  } };
}
function scene(id) {
  if (!id) die('which diorama? try: ink-studio scenes');
  if (/\.(obj|gltf|glb)$/i.test(id)) return meshScene(id);
  if (id.endsWith('.json')) return dataScene(id);
  if (id.endsWith('.js')) return require(path.resolve(id))(lib());
  const s = lib().SCENES.find(q => q.id === id);
  if (!s) die('no diorama called "' + id + '"');
  return s;
}
const paintDirectory = id => path.resolve(CWD, opt.dir || path.join(cfg.paint || 'studio/paint', id));
const readPaint = file => fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : {};
function build(id, seedOverride, { paint = true } = {}) {
  if (opt.focus) {
    const f = list('focus'); // uneven detail: x,y,z then near, far, coarse
    globalThis.INK_FOCUS = { p: [f[0] || 0, f[1] || 0, f[2] || 0], near: f[3], far: f[4], coarse: f[5] };
  }
  if (opt.follow)
    globalThis.INK_FOLLOW =
      opt.follow === true
        ? {}
        : { stretch: +String(opt.follow).split(',')[0], broad: +String(opt.follow).split(',')[1] || undefined };
  if (opt.bounce) globalThis.INK_BOUNCE = true; // bounce light: every dab is also lit by the lit things round it
  if (opt.fine) globalThis.INK_FINE = true; // inked detail: dabs are baked with a tile of the surface under them
  const s = scene(id);
  // Load paint by scene ID so rendering the same file from another path finds its decals.
  const decalFile = path.join(paintDirectory(s.id), 'decals.json');
  shot?.dependency(decalFile);
  const savedPaint = paint && (fs.existsSync(decalFile) ? readPaint(decalFile) : globalThis.INK_PAINT?.[s.id]);
  globalThis.INK_DECAL_NEXT = savedPaint?.layers !== undefined || Array.isArray(savedPaint) ?
    savedPaint : savedPaint?.decals ?? null;
  const t0 = Date.now();
  const controls = opt.params ? JSON.parse(String(opt.params)) : undefined;
  const snapshot = opt.authoring ? JSON.parse(fs.readFileSync(path.resolve(opt.authoring), 'utf8')) : undefined;
  const seed = seedOverride ?? (opt.seed === undefined ? snapshot?.seed ?? s.seed : +opt.seed);
  shot?.seed(seed);
  const assemble = () => {
    const built = s.build(seed, { controls, snapshot });
    return (s.animate && s.animate(built, seed)) || built;
  };
  const w = liveSunOption() ? require('./look-preview.js').withAlbedo(assemble) : assemble();
  if (w.sandbox && !w.anim) lib().KIT.sandbox.attach(w); // and one whose stuff is a sandbox gets its grid going
  if (w.pix && lib().KIT.pixel)
    ((w.pixTex = lib().KIT.pixel.evaluators(w)),
      (w.pixCell = lib().KIT.pixel.CELL),
      (w.pixView = lib().KIT.pixel.VIEW),
      (w.pixUnfold = lib().KIT.pixel.unfold),
      (w.pixAnchors = lib().KIT.pixel.anchors)); // (colour per pixel: its patterns, to be called for each pixel; where edge sprites stand)
  w.buildMs = Date.now() - t0;
  w.id = s.id;
  if (s.lookPreviewPacks !== undefined) w.lookPreviewPacks = s.lookPreviewPacks;
  w.name = s.name;
  w.clock = 0;
  if (w.anim?.trackAtmosphere && opt['atmosphere-emitters'] !== undefined)
    w.anim.trackAtmosphere(lib().KIT.atmosphere.emitters.settings(w.atmosphereEmitters, atmosphereEmittersOption()));
  if (w.anim && w.anim.stateful) w.anim.update(0, 0);
  for (const note of w.warnings || []) console.error('warning: ' + s.id + ': ' + note);
  return w;
}
/* --poke 2:0.2,1.4,0.9 taps the diorama at 2 seconds, along the line from the camera to that point (several: 2:x,y,z;5:x,y,z) */
const POKES = String(opt.poke || '')
  .split(';')
  .filter(Boolean)
  .map(q => {
    const m = q.split(':');
    return { t: +m[0], p: m[1].split(',').map(Number) };
  });
function tap(w, t0, t1) {
  for (const k of POKES) {
    if (!(k.t > t0 && k.t <= t1) || !w.anim.poke) continue;
    const c = w.cam,
      cp = Math.cos(c.pitch),
      eye = [
        c.target[0] + c.dist * cp * Math.sin(c.yaw),
        c.target[1] + c.dist * Math.sin(c.pitch),
        c.target[2] + c.dist * cp * Math.cos(c.yaw)
      ],
      d = k.p.map((v, i) => v - eye[i]),
      l = Math.hypot(d[0], d[1], d[2]);
    w.anim.poke(
      eye,
      d.map(v => v / l)
    );
  }
}
// put the world at time t. A diorama that says it remembers the past (anim.stateful) is walked there a sixtieth of a second at a time
function pose(w, t) {
  if (!w.anim) return;
  t = ArtDirection.time(ArtDirection.prepare(w.look?.artDirection,artDirectionOption()),t);
  if (w.anim.stateful) {
    if (t < w.clock) die('this diorama cannot be run backwards: ask for times in order');
    while (w.clock < t - 1e-9) {
      const dt = Math.min(1 / 60, t - w.clock),
        before = w.clock;
      w.clock += dt;
      /* (the time before the step is kept, not worked back out: taking the step off again can land a hair to the other side of a tap) */
      tap(w, before, w.clock);
      w.anim.update(dt, w.clock);
    }
  } else w.anim.update(1 / 60, t);
  w.clock = t;
  /* splats carried by bones on the graphics card stay at rest in the data: the tools look at a copy with them put in place */
  if (w.anim.bones) {
    if (!w.rest) w.rest = w.data;
    w.data = lib().KIT.bones.posed({
      data: w.rest,
      anim: w.anim,
      get posedBuf() {
        return w.posedBuf;
      },
      set posedBuf(v) {
        w.posedBuf = v;
      }
    });
  }
}
const artPixelSize = cmd === 'compare' || cmd === 'review' ? undefined : num('px', undefined);
if (artPixelSize !== undefined && (!Number.isSafeInteger(artPixelSize) || artPixelSize < 1))
  die('--px needs a positive integer');
let horizonOverride, silhouetteOverride, artDirectionOverride, stableOverride, lutOverride, stackOverride, effectPalettesOverride, constraintsOverride, skyOverride, skyProfiles, skyTransitionsOverride, celestialOverride, cloudOverride, weatherOverride, precipitationOverride, rainImpactOverride, windFieldOverride, lightningOverride, sceneExposureOverride, shapedAtmosphereOverride, volumeCutoutsOverride, splatFieldsOverride, atmosphereEmittersOverride, inputSpriteAtlas;
function skyProfileOverrides(value) {
  if (typeof value !== 'string') die('--sky-profile expects track=profile pairs');
  const pairs = value.split(',').map(entry => entry.split('=').map(part => part.trim()));
  if (pairs.some(pair => pair.length !== 2 || pair.some(name => !name)) ||
      new Set(pairs.map(([id]) => id)).size !== pairs.length) die('--sky-profile expects distinct track=profile pairs');
  return Object.fromEntries(pairs);
}
function skyTransitionsOption() {
  const value = opt['sky-transitions'];
  if (value === undefined) return;
  if (value === 'off') return false;
  if (typeof value !== 'string') die('--sky-transitions needs a JSON array file or off');
  return skyTransitionsOverride ??= JSON.parse(fs.readFileSync(path.resolve(value),'utf8'));
}
let shadowArtOverride;
function shadowArtOption() {
  const value = opt['shadow-art'];
  if (value === undefined) return;
  if (value === 'off') return false;
  if (typeof value !== 'string') die('--shadow-art needs a JSON file or off');
  return shadowArtOverride ??= JSON.parse(fs.readFileSync(path.resolve(value), 'utf8'));
}

let relightOverride;
function relightingOption() {
  const value = opt.relighting;
  if (value === undefined) return;
  if (value === 'off') return false;
  if (value === 'on' || value === true) return true;
  return relightOverride ??= JSON.parse(fs.readFileSync(path.resolve(value), 'utf8'));
}

function liveSunOption() {
  const value = opt['live-sun'];
  if (value === 'off') return false;
  if (value !== undefined && value !== true && value !== 'on') die('--live-sun expects on or off');
  if (opt['sun-shadows'] !== undefined && !['off', 'on', true].includes(opt['sun-shadows']))
    die('--sun-shadows expects on or off');
  const overrides = {
    ...(opt['sun-direction'] !== undefined && { direction: list('sun-direction') }),
    ...(opt['sun-ambient'] !== undefined && { ambient: num('sun-ambient') }),
    ...(opt['sun-intensity'] !== undefined && { intensity: num('sun-intensity') }),
    ...(opt['shadow-map-size'] !== undefined && { mapSize: num('shadow-map-size') }),
    ...(opt['shadow-bias'] !== undefined && { bias: num('shadow-bias') }),
    ...(opt['sun-shadows'] !== undefined && { shadows: opt['sun-shadows'] !== 'off' })
  };
  for (const [flag, key] of [['sky-bounce', 'skyBounce'], ['ground-bounce', 'groundBounce']]) {
    const choice = opt[flag], strength = opt[flag + '-intensity'];
    if (choice === undefined && strength === undefined) continue;
    if (choice === 'off') overrides[key] = false;
    else {
      if (choice !== undefined && typeof choice !== 'string') die('--' + flag + ' expects a color, preset name or off');
      overrides[key] = { ...(choice !== undefined && { color: choice }),
        ...(strength !== undefined && { intensity: strength === true ? NaN : num(flag + '-intensity') }) };
    }
  }
  if (value || Object.keys(overrides).length) return overrides;
}

function aerialOption() {
  const value = opt['aerial-perspective'];
  if (value === 'off') return false;
  if (value !== undefined && value !== 'on' && value !== true) die('--aerial-perspective expects on or off');
  const pairs = [['aerial-start', 'start'], ['aerial-density', 'density'], ['aerial-contrast', 'contrast']];
  const supplied = pairs.filter(([flag]) => opt[flag] !== undefined);
  if (!value && !supplied.length) return undefined;
  return Object.fromEntries(supplied.map(([flag, setting]) => [setting, opt[flag] === true ? NaN : num(flag)]));
}

function cloudShadowOption() {
  const value = opt['cloud-shadows'];
  if (value === 'off') return false;
  if (value !== undefined && value !== 'on' && value !== true) die('--cloud-shadows expects on or off');
  const pairs = [['cloud-shadow-strength', 'strength'], ['cloud-shadow-softness', 'softness']];
  const supplied = pairs.filter(([flag]) => opt[flag] !== undefined);
  if (!value && !supplied.length) return undefined;
  return Object.fromEntries(supplied.map(([flag, setting]) => [setting, opt[flag] === true ? NaN : num(flag)]));
}

function weatherOption() {
  const value = opt['weather-binding'];
  if (value === undefined) return undefined;
  if (value === false || value === 'off') return false;
  if (value === true || value === 'on') return true;
  return weatherOverride ??= JSON.parse(fs.readFileSync(path.resolve(value), 'utf8'));
}

function windFieldOption() {
  const value = opt['wind-field'];
  if (value === undefined) return undefined;
  if (value === 'off') return false;
  if (value === true || value === 'on') return true;
  return windFieldOverride ??= JSON.parse(fs.readFileSync(path.resolve(value), 'utf8'));
}

function sceneExposureOption() {
  const value = opt['scene-exposure'];
  if (value === undefined) return undefined;
  if (value === 'off') return false;
  if (value === true || value === 'on') return true;
  return sceneExposureOverride ??= require('../src/scene-exposure.js').compile(
    JSON.parse(fs.readFileSync(path.resolve(value), 'utf8')));
}

function celestialOption() {
  const value = opt['celestial-tracks'];
  if (value === undefined) return undefined;
  if (value === 'off') return false;
  if (value === 'on' || value === true) return true;
  return celestialOverride ??= require('../src/celestial-tracks.js').compile(JSON.parse(fs.readFileSync(path.resolve(value), 'utf8')));
}

function effectPalettesOption() {
  const value = opt['effect-palettes'];
  if (value === undefined) return undefined;
  if (value === 'off') return false;
  if (value === 'on' || value === true) return true;
  return effectPalettesOverride ??= JSON.parse(fs.readFileSync(path.resolve(value), 'utf8'));
}

function atmosphereEmittersOption() {
  const value = opt['atmosphere-emitters'];
  if (value === undefined) return undefined;
  if (value === 'off') return false;
  if (value === 'on' || value === true) return true;
  return atmosphereEmittersOverride ??= require('../index.js').load().KIT.atmosphere.emitters.compile(
    JSON.parse(fs.readFileSync(path.resolve(value), 'utf8')));
}

function splatFieldsOption() {
  const value = opt['splat-fields'];
  if (value === undefined) return undefined;
  if (value === 'off') return false;
  if (value === 'on' || value === true) return true;
  return splatFieldsOverride ??= lib().KIT.splatFields.compile(JSON.parse(fs.readFileSync(path.resolve(value), 'utf8')));
}

function spriteAtlasOption() {
  const value=opt['sprite-atlas'];
  if (value===undefined) return undefined;
  if (value==='off') return false;
  if (value==='on' || value===true) return true;
  if (!inputSpriteAtlas) {
    const atlas=require('./sprite-atlas.js').readSpriteAtlas(path.resolve(value));
    inputSpriteAtlas=[lib().KIT.sprite.placeAtlas({
      atlas,at:opt['sprite-at']?list('sprite-at'):[0,0,0],scale:num('sprite-scale',1)
    })];
  }
  return inputSpriteAtlas;
}

function volumeCutoutsOption() {
  const value=opt['volume-cutouts'];
  if (value===undefined) return undefined;
  if (value==='off') return false;
  if (value==='on' || value===true) return true;
  return volumeCutoutsOverride ??= require('../src/volume-cutouts.js').compile(
    JSON.parse(fs.readFileSync(path.resolve(value), 'utf8')));
}

function shapedAtmosphereOption() {
  const value=opt['shaped-atmosphere'];
  if (value===undefined) return undefined;
  if (value==='off') return false;
  if (value==='on' || value===true) return true;
  return shapedAtmosphereOverride ??= require('../src/scene-optics.js').shapedVolumes(
    JSON.parse(fs.readFileSync(path.resolve(value), 'utf8')));
}

function cloudFieldOption() {
  const value = opt['cloud-field'];
  if (value === undefined) return undefined;
  if (value === 'off') return false;
  const clouds = require('../src/cloud-field.js');
  return cloudOverride ??= clouds.compile(clouds.recipes.includes(value) ? value :
    JSON.parse(fs.readFileSync(path.resolve(value), 'utf8')));
}

function lightningOption() {
  const value = opt.lightning;
  if (value === undefined) return undefined;
  if (value === 'off') return false;
  if (value === true || value === 'on') return true;
  return lightningOverride ??= require('../src/lightning.js').compile(
    JSON.parse(fs.readFileSync(path.resolve(value), 'utf8')));
}

function precipitationOption() {
  const value = opt['world-precipitation'];
  if (value === undefined) return undefined;
  if (value === 'off') return false;
  if (value === true || value === 'on') return true;
  return precipitationOverride ??= JSON.parse(fs.readFileSync(path.resolve(value), 'utf8'));
}

function rainImpactOption() {
  const value = opt['rain-impacts'];
  if (value === undefined) return undefined;
  if (value === 'off') return false;
  if (value === true || value === 'on') return true;
  return rainImpactOverride ??= JSON.parse(fs.readFileSync(path.resolve(value), 'utf8'));
}

function onOffOption(flag) {
  const value = opt[flag];
  if (value === undefined) return undefined;
  if (value === true || value === 'on') return true;
  if (value === 'off') return false;
  die('--' + flag + ' expects on or off');
}

function horizonOption() {
  const value = opt['horizon-bands'];
  if (value === undefined) return;
  if (value === 'off') return false;
  if (value === true || value === 'on') return true;
  return horizonOverride ??= require('./horizon-bands.js').readHorizonBands(value);
}

function silhouetteOption() {
  const value = opt['silhouette-protection'];
  if (value === undefined) return;
  if (value === 'off') return false;
  if (value === true || value === 'on') return true;
  return silhouetteOverride ??= JSON.parse(fs.readFileSync(path.resolve(value),'utf8'));
}

function artDirectionOption() {
  const value = opt['art-direction'];
  if (value === undefined) return;
  if (value === 'off') return false;
  if (value === 'on' || value === true) return true;
  if (/\.json$/i.test(value)) return artDirectionOverride ??= JSON.parse(fs.readFileSync(path.resolve(value),'utf8'));
  return value;
}

function stabilityOption() {
  const value = opt.stable;
  if (value === 'off') return false;
  const snap = onOffOption('snap');
  if (value === undefined && snap === undefined && opt['dither-space'] === undefined &&
      opt['dither-spacing'] === undefined && opt['dither-origin'] === undefined && opt.resolve === undefined) return;
  const fromFile = value !== undefined && value !== true && value !== 'on';
  const base = fromFile ? (stableOverride ??= JSON.parse(fs.readFileSync(path.resolve(value), 'utf8'))) :
    value === 'on' || value === true ? {snap:true} : {};
  if (!base || typeof base !== 'object' || Array.isArray(base)) throw new TypeError('Stable settings file needs an object');
  return {
    ...base,
    ...(snap !== undefined && {snap}),
    ...(opt['dither-space'] !== undefined && {dither:opt['dither-space']}),
    ...(opt['dither-spacing'] !== undefined && {spacing:num('dither-spacing')}),
    ...(opt['dither-origin'] !== undefined && {origin:list('dither-origin')}),
    ...(opt.resolve !== undefined && {resolve:opt.resolve})
  };
}

function clipCamera(world) {
  if (opt['camera-pan'] === undefined && opt['camera-orbit'] === undefined) return null;
  const shift = list('camera-pan',[0,0,0]), start = list('target',world.cam.target);
  const yaw = num('yaw',world.cam.yaw), degrees = num('camera-orbit',0);
  if (opt['camera-orbit'] === true || ![shift,start].every(v=>v.length===3 && v.every(Number.isFinite)) ||
      !Number.isFinite(yaw) || !Number.isFinite(degrees))
    throw new TypeError('Use --camera-pan x,y,z and --camera-orbit degrees');
  return phase => ({
    target: start.map((n,i)=>n+shift[i]*phase),
    yaw: yaw+phase*degrees*Math.PI/180
  });
}

function skyOptions() {
  const options = {
    skyEnvironment: opt['sky-environment'] === 'off' ? false : opt['sky-environment'] === undefined ? undefined :
      (skyOverride ??= require('../src/sky-environment.js').compile(
        JSON.parse(fs.readFileSync(path.resolve(opt['sky-environment']), 'utf8')))),
    skyTime: num('sky-time'),
    skyProfiles: opt['sky-profile'] === undefined ? undefined : (skyProfiles ??= skyProfileOverrides(opt['sky-profile']))
  };
  shot?.profiles(options.skyProfiles);
  return options;
}

const view = extra =>
  Object.assign(
    {
      yaw: opt.yaw === undefined ? undefined : +opt.yaw,
      pitch: opt.pitch === undefined ? undefined : +opt.pitch,
      zoom: num('zoom', 1),
      target: opt.target ? list('target') : undefined,
      w: num('w', 900),
      h: num('h', 620),
      px: artPixelSize,
      stable: stabilityOption(),
      artDirection: artDirectionOption(),
      silhouetteProtection: silhouetteOption(),
      horizonBands: horizonOption(),
      effectPalettes: effectPalettesOption(),
      artEffects: opt.effects === 'off' ? false : opt.effects,
      ink: opt.ink === 'off' ? false : opt.ink,
      tone: opt.tone === 'off' ? false : opt.tone,
      paletteRemap: opt['palette-remap'] === 'off' ? false : undefined,
      colorCurves: opt['color-curves'] === 'off' ? false : undefined,
      colorLut: opt.lut === undefined ? undefined : (lutOverride ??= require('./lut.js').override(opt.lut)),
      colorStack: opt['color-stack'] === undefined ? undefined :
        (stackOverride ??= require('./color-stack.js').override(opt['color-stack'])),
      paletteConstraints: opt['palette-constraints'] === undefined ? undefined :
        (constraintsOverride ??= require('./palette-constraints.js').override(opt['palette-constraints'])),
      coverageAware: opt['coverage-aware'] === undefined ? undefined : opt['coverage-aware'] !== 'off',
      lookMasks: opt['look-masks'] === 'off' ? false : undefined,
      ignoreLookGrade: opt.look === 'off',
      raw: !!opt.raw,
      paintCorrections: opt['paint-corrections'] !== 'off',
      colored: !!opt.colored,
      splatOrder: opt['splat-order'],
      fine: !!opt.fine,
      clean: !!opt.clean,
      ortho: !!opt.ortho,
      surface: opt.surface === 'off' ? false : undefined,
      water: opt.water === 'off' ? false : undefined,
      reflections: opt.reflections === 'off' ? false : undefined,
      skyReflections: opt['sky-reflections'],
      ...skyOptions(),
      celestialTracks: celestialOption(),
      cloudField: cloudFieldOption(),
      cloudRepresentation: opt['cloud-representation'],
      cloudShadows: cloudShadowOption(),
      weatherBinding: weatherOption(),
      retainedWeather: onOffOption('retained-weather'),
      weatherFronts: onOffOption('weather-fronts'),
      weatherTracks: onOffOption('weather-tracks'),
      windField: windFieldOption(),
      lightning: lightningOption(),
      sceneExposure: sceneExposureOption(),
      precipitation: precipitationOption(),
      rainImpacts: rainImpactOption(),
      skyTransitions: skyTransitionsOption(),
      liveSun: liveSunOption(),
      relighting: relightingOption(),
      shadowArt: shadowArtOption(),
      atmosphere: opt.atmosphere === 'off' ? false : undefined,
      shapedAtmosphere: shapedAtmosphereOption(),
      volumeCutouts: volumeCutoutsOption(),
      splatFields: splatFieldsOption(),
      atmosphereEmitters: atmosphereEmittersOption(),
      spriteAtlases: spriteAtlasOption(),
      spriteAtlasMode: opt['sprite-atlas-mode'],
      aerialPerspective: aerialOption(),
      volumeLocalLights: onOffOption('volume-local-lights'),
      volumeLocalShadows: onOffOption('volume-local-shadows'),
      volumeQuality: opt['volume-scale'] || opt['volume-steps'] || opt['volume-jitter'] ? {
        ...(opt['volume-scale'] && { scale: num('volume-scale') }),
        ...(opt['volume-steps'] && { steps: num('volume-steps') }),
        ...(opt['volume-jitter'] && { jitter: opt['volume-jitter'] })
      } : undefined,
      edges: opt.edges === 'off' ? false : undefined
    },
    extra,
    shotRender
  );
const save = (name, img) => {
  const f = outputFile(name);
  fs.mkdirSync(path.dirname(f), { recursive: true });
  PNG.write(f, img.w, img.h, img.rgb);
  console.log('wrote', f, img.w + 'x' + img.h);
  return f;
};
const asciiFrame = (image, world) => lib().KIT.ascii.draw(image, {
  set: opt.text === true ? 'ascii' : opt.text,
  g: num('tg', 2),
  px: opt.px1 ? 1 : image.px,
  colour: opt.tcolour || 'scene',
  pal: image.palette || world.pal
});
const displayFrame = (image, world) => opt.text ? asciiFrame(image, world) : R.upscale(image, opt.px1 ? 1 : image.px);
function buildPreview(id = pos[0]) {
  const Preview = require('./look-preview.js');
  const world = opt.look !== undefined && opt.look !== 'off' ? Preview.withAlbedo(() => build(id)) : build(id);
  return Preview.override(world, opt, lib());
}
const previewPasses = () => require('./look-preview.js').preview(opt);
const reviewSidecars = diagnostics => [...(diagnostics?.suffixes ?? []), ...(opt.text ? ['.txt'] : [])];
const textSidecar = file => file.replace(/\.(?:a?png)$/i, '') + '.txt';
const times = () =>
  opt.t !== undefined
    ? list('t')
    : (n =>
        Array.from(
          { length: n },
          (_, i) => +(num('from', 0) + ((num('to', 6) - num('from', 0)) * i) / Math.max(1, n - 1)).toFixed(3)
        ))(num('n', 12));
function die(m) {
  console.error(m);
  process.exit(1);
}
const worldCLI = () => require('./world.js')({kit:lib(),build,pose,dataScene,opt,renderOptions:view,atmosphereEmittersOption,effectPalettesOption,stabilityOption,artDirectionOption,silhouetteOption,horizonOption,skyTransitionsOption,
  weatherTracksOption:() => onOffOption('weather-tracks'),skyOptions,shot,shotReplay,shotRender});
const worldCommands = new Set(['inspect','probe','trace','field','scene','sim']);
const CMD = {
  help() {
    console.log(
      [
        'ink-studio <command> <diorama id | lab/file.js> [options]',
        '',
        '  inspect <scene|run>         discover fields, actions, ports and entities',
        '  environment inspect <scene|run> --at x,y,z [--t seconds] [--out report.json]   explain sky and local weather',
        '  probe <scene|run> --field name [--at x,y,z | --entity id] [--explain]  sample world state',
        '  inspect|validate|probe <scene|run> --select JSON   inspect, check, or sample a look target',
        '  probe <scene|run> --field look/sample [--select JSON | --entity ID] [--at x,y,z]   explain a baked splat',
        '  trace <scene|run> <name>    trace a route, signal or other exposed query',
        '    trace <scene|run> world/cause --args JSON   follow recorded decisions, inputs and events',
        '  field <scene|run> <name> --spec file.json [--explain]  export a line, grid or time series',
        '  authoring inspect <scene> [--authoring snapshot.json] [--part id]   inspect retained parts',
        '  authoring preview <scene> <edits.json> [--authoring snapshot.json] [--image preview.png]   stage and validate edits',
        '  authoring apply <scene> <edits.json> [--authoring snapshot.json] --out snapshot.json   save validated edits',
        '  scene apply|stamp|remix|capture|history|promote <world> ...  edit or derive a world manifest',
        '    scene apply <scene> <edits.json> --dry-run   preview edited paths and look targets',
        '  sim run|resume|fork|reset|replay|diff|sweep|render ...  run or compare fixed-tick simulations',
        '    sim dependencies <scene|run|driver.js> [--ticks N] [--actions file] [--out report.json]   report spatial rebuilds',
        '    sim sweep <world|run> <cases.json>   use look cases to compare one fixed simulation snapshot',
        '  compare <scene|run> --looks cases.json [--out sheet.png]   compare look variants on the same view',
        '  look inspect <scene|run|look-file> [--renderer headless|webgl]   list bindings, dependencies and targets',
        '  look sample <look-file> [--look pack/look] [--colors JSON | --chart] [--out file.json|chart.png]',
        '  look bake <look-file> [--format auto|palette|lut] [--swatches file] [--size N] [--out bundle.json]',
        '  look parity [--chrome path] [--hardware] [--strict] [--out report.json]   check CPU and WebGL look fixtures',
        '  look profile [--renderer headless|webgl|both] [--frames N] [--warmup N] [--splats N] [--w N --h N]',
        '    [--batch N] [--chrome path] [--hardware] [--out report.json]   benchmark look setup and frame time',
        '  look import <file> [--out pack.json] [--id pack/look]   import a LUT or palette as a versioned look',
        '  look export <file> [--out file | --format json|cube|gpl|pal|hex]   convert or sample a look',
        '    --look pack/look --params JSON --size N --swatches palette-file --report report.json --exact',
        '  lut import <file.cube|file.json> [--out file.json]  load a 3D color table as native JSON',
        '    --input-space space --output-space space --input-range min,max --output-range min,max',
        '    --input-out-of-range preserve|clamp|error --output-out-of-range preserve|clamp|error --domain-policy clamp|error|extrapolate',
        '',
        '  scenes                      list every diorama',
        '  catalog [words]             what the toolkit can do, searchable',
        '  stats <id>                  splat counts, colours used, size, cost per frame, warnings',
        '  render <id> [--t 1.5]       one PNG rendered on the CPU',
        '  render <id> --palette-constraints <file.json|off>   override target palettes and dither settings',
        '  render <id> --coverage-aware on|off   grade target contributions before compositing',
        '  render <id> --look-masks off   bypass masked look bindings',
        '  render, clip, transition-review, sim render: --recipe <shot.json>   save reproducible review inputs',
        '  shot replay <shot.json> --out <image.png> [--root project]   verify and recreate the review render',
        '  render <scene.json> --asset-pack <pack-or-bundle.json>   install look assets for this invocation',
        '  ramps <id> [--n 12]         the ramps it is shaded on, and which only get darker without turning; a turning one is offered from the same palette',
        '  values <id> [--t 1.5]       the value check: the picture sorted into dark, middle and light, and whether it reads in three tones',
        '  sheet <id> [--from 0 --to 6 --n 12 | --t 0,1,2]   the same view at several moments, on one sheet',
        '  turn <id> [--n 8] [--t 0]   the diorama from all round, on one sheet',
        '  clip <id> [--from 0 --to 6 --fps 12]   an animated PNG of it moving (also supports --text)',
        '    --camera-pan x,y,z --camera-orbit degrees --px 1   review slow camera motion at native art resolution',
        '  ghost <id> [--t 2 --spacing 0.12 --n 2 | --ghosts 1.6,1.8]   one moment with those either side laid faintly over it',
        '  acts                        the ready clips, reactions, easings and cues, by name',
        '  motion <id> [--from 0 --to 12]   numbers about how it moves: speed, jumps, what goes underground',
        '  mesh <file.obj|.gltf|.glb>  import and inspect as splats (--uv requires textured GLB stamps, --uv off uses geometry)',
        '  export-glb <scene.js|.json|.obj|.gltf|.glb> --out model.glb   write UV-mapped geometry with materials, skins and clips',
        '                              [--res 0.08 --texture-size 1024 --triangles 16000 --duration 4 --fps 30]',
        '  depth <map.png|map.json> [--image aligned.png --out-dir folder]  import a depth map as splats, a mesh and an SDF',
        '                              [--size 6 --cells 64 --res 0.09 --hues 6 --shades 4 --up z --spin 0.5 --thick 0.1]; a mesh file also works wherever an id does',
        '  validate <scene|look-file> [--renderer headless|webgl]   check scene content and look bindings',
        '                              a .json diorama also works wherever an id does; --style slate|moss|ember puts it in another style',
        '  perf <id> [--secs 5 --fps 60 --json]   animation time and planned texture upload size',
        '  selftest                    every lab module checked in numbers, and the lab dioramas run for a while',
        '  snap <id|all> [--t 0,2]     keep reference pictures',
        '  check [id ...]              draw again and compare with the reference pictures',
        '  render <id> [--text ascii|symbols|braille|blocks --tg 2 --tcolour scene|ink|mono]  drawn as text, with the characters as <id>.txt',
        '  compare <id> <ref.png> [--px 2 --colours 32]  a diorama beside a reference at true pixel size, both measured',
        '  paint export <id> [--layer name] [view options]  capture a view and the surface under each pixel',
        '  paint absorb <id> [--layer name] [--png file] [--paint-mask file]  pin the painted pixels to the surface',
        '  paint layers|tune|clear <id> [--layer name]  list, adjust or clear corrections',
        '    layer controls: --angle degrees --feather degrees --opacity fraction --region JSON|file|off',
        '  lint <id ...> [--map]              pixel-art lint: orphans, doubles, jaggies, banding, pillow shading, noise, colours',
        '  review <id> [--ref pic --px 2]     a sheet of fixed shots (four sides, top, low, far, near, close), beside the last one',
        '  variants <id> --seeds 3,7,12 [--group silhouette|openness|wear --motion]  render a ranked seed contact sheet',
        '  atlas <id> [--directions 8 --pitches 0,0.7 --w 96 --h 96 --fps 12 --maps depth,normal,emission,silhouette]  export a transparent sprite atlas',
        '  silhouette-review <scene> --directions 8 --w 96 --h 96   paired export-size views and edge contrast',
        '  transition-review <scene> [--plan file.json] --w 160 --h 90 [--out sheet.png]',
        '    compare native frames around midnight, weather beats, or cuts [--scale N --fail-on-flags]',
        '  pose-review <id> [--directions 8 --w 96 --h 96]  review named poses at sprite resolution',
        '  motion-review <id> [--finding kind-or-id] [--out report.json]  inspect motion findings and focused playback ranges',
        '  clip-sequence <id> [--handoff 0] [--out report.json]  inspect clip instances, retimed cues, and handoffs',
        '  authored-contacts <id> [--at seconds] [--out report.json]  inspect contact ranges and socket transfer timing',
        '  motion-fx <id> [--at seconds] [--out report.json]  inspect keyed FX layers and sampled effect output',
        '  cloth-review <id> [--pose seconds] [--through seconds] [--bake take.json]  preview a cloth pose and optionally bake it',
        '  animation-timeline <id> [--state context.json] [--stage block|spline|polish] [--at seconds] [--part name]',
        '    [--loop start,end|off] [--finding kind-or-id|off] [--direction index] [--fix accept|mute|enable|remove]',
        '    [--preview directory] [--frames count --w width --h height] [--before] [--out report.json]',
        '  retarget <source> <target> [--clip name|--motion clip.json] [--profile name|file.json]',
        '    [--source-map file.json --target-map file.json] [--travel scaled|unscaled|in-place] [--fps rate]',
        '    [--bake clip.json] [--preview directory] [--at seconds|--frames count] [--direction index] [--out report.json]',
        '  retarget --profiles  show built-in role templates',
        '  passes <id> [--channels coverage,depth,normal,objectId,materialId,emission]  save art-pixel render pass previews',
        '  environment-parity [--fixture observatory --out directory --chrome executable]  compare matched CLI and WebGL environment frames',
        '  passes <id> --channels environment --px1   export sky, fog transmittance, precipitation, reflections and foreground coverage',
        '  render|sheet|clip <id> or sim render <file> --passes environment   write environment passes beside the export',
        '  render|sheet|clip <id> --look pack/look|file.json|off [--passes target,mask,materialId]',
        '    --look-select JSON --look-params JSON --look-strength N   override an asset binding for the preview',
        '  shimmer <id> [--mode orbit|zoom|pan|still --frames 24]  how many pixels flicker over a move, and a GIF of it',
        '  crisp <id ...|all> [--t 2 --map]   how crisp at its own pixel size: stray pixels, specks, flat area, finest frequencies,',
        '                              against the pixel-art references (--map: where the stray pixels and drawn edges are)',
        '',
        'any command that plays a diorama takes --poke 2:x,y,z (tap it at 2 seconds, toward that point; several with ;)',
        'sun options: --live-sun on|off --sun-direction x,y,z --sun-ambient n --sun-intensity n --shadow-map-size n --shadow-bias n --sun-shadows off',
        'shadow art: --shadow-art file.json|off for baked JSON scenes and live sun',
        'detail-preserving relighting: --relighting on|off|file.json --sky-time seconds',
        'bounce options: --sky-bounce color|preset|off --ground-bounce color|preset|off --sky-bounce-intensity n --ground-bounce-intensity n',
        'cloud options: --cloud-field cirrus|coastal-stratus|cumulus|storm-front|file.json|off --cloud-representation auto|card|impostor|volume|off --cloud-shadows on|off --cloud-shadow-strength 0..1 --cloud-shadow-softness units',
        'celestial options: --celestial-tracks on|off|file.json',
        'sky options: --sky-environment file.json|off --sky-time seconds --sky-profile track=profile --sky-transitions file.json|off --sky-reflections scene|material',
        'weather options: --weather-binding on|off|file.json --retained-weather on|off --weather-fronts on|off --weather-tracks on|off --world-precipitation on|off|file.json --rain-impacts on|off|file.json',
        'wind options: --wind-field on|off|file.json',
        'lightning options: --lightning on|off|file.json',
        'exposure options: --scene-exposure on|off|file.json',
        'aerial options: --aerial-perspective on|off --aerial-start units --aerial-density per-unit --aerial-contrast 0..1',
        'view options: --surface off (no finish layers) --water off --reflections off --atmosphere off --edges off (no edge sprites) --yaw --pitch --zoom 2 --target x,y,z --w 900 --h 620 --px 2 (screen pixels per art pixel) --px1 (native art pixels) --tone stipple|off --raw (no palette) --colored (smooth body-colored contours) --fine (inked detail: colours looked up per pixel) --bounce (bounce light baked in) --focus x,y,z[,near,far,coarse] (uneven detail) --follow [stretch,broad] (dabs along the form) --clean (remove lone pixels) --ortho (orthographic: no perspective) --cols 4 --out file.png --seed n',
        'socket emitter options: --atmosphere-emitters on|off|file.json',
        'animated splat options: --splat-fields on|off|file.json',
        'sprite options: --sprite-atlas on|off|atlas.json --sprite-at x,y,z --sprite-scale n --sprite-atlas-mode card|impostor',
        'shaped fog options: --shaped-atmosphere on|off|file.json --volume-cutouts on|off|file.json',
        'fog lighting options: --volume-local-lights on|off --volume-local-shadows on|off',
        'silhouette protection: --silhouette-protection on|off|file.json',
        'layered horizon: --horizon-bands on|off|file.json',
        'art direction: --art-direction on|off|painted-pixel|storm-silhouette|soft-dawn|file.json',
        'effect palette options: --effect-palettes on|off|file.json',
        'art options: --palette-remap off --color-curves off --lut <file.cube|file.json|off> --color-stack <file.json|off> --ink off --effects off --stable on|off|file.json --snap on|off --dither-space screen|world|object --dither-spacing n --dither-origin x,y,z --resolve native|coverage|clusters --splat-order center|surface --volume-scale 2 --volume-steps 8 --volume-jitter off|blue-noise|spatiotemporal'
      ].join('\n')
    );
  },
  authoring() {
    return require('./authoring.js')(pos, opt, {
      scene,
      render(world) {
        const shot = R.render(world, view({ t: 0 }));
        const image = R.upscale(shot, opt.px1 ? 1 : shot.px);
        return PNG.encode(image.w, image.h, image.rgb);
      }
    });
  },
  environment() {
    if (pos[0] !== 'inspect' || pos.length !== 2)
      die('Usage: ink-studio environment inspect <scene|run> --at x,y,z [--t seconds]');
    if (typeof opt.at !== 'string' || opt.at.split(',').length !== 3 || opt.at.split(',').some(value=>!value.trim()) ||
        !list('at').every(Number.isFinite)) die('--at needs three finite comma-separated coordinates');
    const requested = num('t',0);
    if (opt.t === true || !Number.isFinite(requested) || requested < 0) die('--t needs nonnegative scene seconds');
    const snapshot = worldCLI().environmentSnapshot(pos[1]);
    const world = snapshot ?? buildPreview(pos[1]);
    const t = snapshot?.lookSnapshot?.time ?? requested;
    if (!snapshot) pose(world,t);
    const { inspectEnvironment } = require('./environment-inspector.js');
    const report = inspectEnvironment(world,view({t,at:list('at')}));
    if (snapshot && opt.t !== undefined) report.time.requested = requested;
    const json = JSON.stringify(report,null,opt.json ? 0 : 2)+'\n';
    if (opt.out === undefined) process.stdout.write(json);
    else {
      if (typeof opt.out !== 'string') die('--out needs a report filename');
      const file = path.resolve(opt.out);
      fs.mkdirSync(path.dirname(file),{recursive:true});
      fs.writeFileSync(file,json);
    }
  },
  look() {
    const io = require('./look.js');
    if (pos[0] === 'parity' || pos[0] === 'profile') {
      if (pos.length !== 1) die('Usage: ink-studio look ' + pos[0] + ' [options]');
      return require('./look-renderers.js').run(pos[0], opt);
    }
    if (pos[0] === 'bake') {
      if (pos.length !== 2) die('Usage: ink-studio look bake <look-file> [--format auto|palette|lut]');
      return io.bake(pos[1], opt, lib());
    }
    if (pos[0] === 'sample') {
      if (pos.length !== 2) die('Usage: ink-studio look sample <look-file> [--colors JSON | --chart]');
      return io.sample(pos[1], opt, lib());
    }
    if (pos[0] !== 'inspect') return io.run(pos, opt, lib().KIT.authoring);
    if (pos.length !== 2) die('Usage: ink-studio look inspect <scene|run|look-file>');
    const file = pos[1];
    return io.report(io.isSource(file) ? io.inspectSource(file, opt, lib()) : worldCLI().inspectLook(file), opt, file);
  },
  lut() {
    const [mode, file] = pos;
    if (mode !== 'import' || !file || (opt.out !== undefined && typeof opt.out !== 'string'))
      die('Usage: ink-studio lut import <file.cube|file.json> [--out file.json]');
    const lut = require('./lut.js'), definition = lut.read(file, lut.importOptions(opt));
    if (opt.out) lut.write(opt.out, definition);
    else process.stdout.write(JSON.stringify(definition) + '\n');
  },
  'export-glb'() {
    const id = pos[0];
    if (!id || typeof opt.out !== 'string') die('Usage: ink-studio export-glb <scene.js|.json|mesh> --out model.glb');
    try {
      let source = id;
      if (!/\.(obj|gltf|glb)$/i.test(id)) {
        const authored = scene(id);
        if (typeof authored.model !== 'function') die('This scene needs a model(seed, options) hook that exposes its rest geometry');
        const box = list('bounds');
        if (box && (box.length !== 6 || !box.every(Number.isFinite))) die('--bounds expects xmin,ymin,zmin,xmax,ymax,zmax');
        const options = {
          resolution: num('res', undefined), method: opt.method, targetTriangles: num('triangles', undefined),
          duration: num('duration', undefined), fps: num('fps', undefined)
        };
        if (opt.authoring !== undefined) {
          if (typeof opt.authoring !== 'string') throw Error('--authoring needs a file path');
          options.snapshot = JSON.parse(fs.readFileSync(path.resolve(opt.authoring), 'utf8'));
        }
        if (box) options.bounds = { min: box.slice(0, 3), max: box.slice(3) };
        source = authored.model(num('seed', options.snapshot?.seed ?? authored.seed), options);
      }
      const result = require('../index.js').exportGlb(source, {
        out: opt.out, textureSize: num('texture-size', 1024), uvMargin: num('uv-margin', 0.008)
      });
      console.log(JSON.stringify(result, null, 2));
    } catch (error) {
      die(error.message);
    }
  },
  scenes() {
    for (const s of lib().SCENES) console.log(s.id.padEnd(12), s.name.padEnd(20), s.blurb);
  },
  catalog() {
    const cat = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'catalog.json'), 'utf8')),
      words = pos.map(s => s.toLowerCase());
    const hit = e =>
        words.every(w =>
          (e.id + ' ' + e.title + ' ' + e.what + ' ' + (e.tags || []).join(' ') + ' ' + e.kind)
            .toLowerCase()
            .includes(w)
        ),
      found = cat.entries.filter(hit);
    if (found.length === 1 || opt.full)
      for (const e of found)
        console.log(
          '\n' +
            e.id +
            '  [' +
            e.kind +
            ', ' +
            e.status +
            ']\n  ' +
            e.title +
            '\n  ' +
            e.what +
            (e.use ? '\n  use:  ' + e.use : '') +
            (e.example ? '\n  e.g.  ' + e.example : '') +
            (e.where ? '\n  in:   ' + e.where : '') +
            (e.from ? '\n  after: ' + e.from : '')
        );
    else
      for (const e of found)
        console.log((e.status === 'ready' ? '  ' : '~ ') + e.id.padEnd(18), ('[' + e.kind + ']').padEnd(10), e.title);
    if (!found.length) console.log('nothing matches');
    else if (found.length > 1 && !opt.full)
      console.log('\n~ = planned, not built yet.   ink-studio catalog <id> for the details');
  },
  stats() {
    const w = build(pos[0]),
      d = w.data,
      N = w.count,
      lo = [1e9, 1e9, 1e9],
      hi = [-1e9, -1e9, -1e9],
      byCol = new Map();
    let soft = 0,
      glow = 0,
      moving = 0,
      big = 0;
    for (let i = 0, q = 0; i < N; i++, q += 16) {
      for (let k = 0; k < 3; k++) {
        lo[k] = Math.min(lo[k], d[q + k]);
        hi[k] = Math.max(hi[k], d[q + k]);
      }
      byCol.set(d[q + 7], (byCol.get(d[q + 7]) || 0) + 1);
      if (d[q + 3] < 1) soft++;
      const kr = Math.round(d[q + 11]);
      if (kr & 32) glow++;
      if (kr % 16) moving++;
      if (Math.sqrt((d[q + 4] + d[q + 8] + d[q + 10]) / 3) > 0.4) big++;
    }
    if(w.spriteSurfaces){
      const surface=w.spriteSurfaces;
      for(let i=0;i<surface.vertices.length;i+=5)for(let k=0;k<3;k++){
        lo[k]=Math.min(lo[k],surface.vertices[i+k]);hi[k]=Math.max(hi[k],surface.vertices[i+k]);
      }
      console.log('surfaces    '+surface.vertices.length/15+' triangles, '+surface.width+'×'+surface.height+' atlas');
    }
    console.log(w.id + '  "' + w.name + '"   built in ' + w.buildMs + ' ms');
    console.log(
      'splats      ' +
        N +
        '   (soft ' +
        soft +
        ', glowing ' +
        glow +
        ', shader-animated ' +
        moving +
        ', large ' +
        big +
        ')'
    );
    console.log(
      'extent      x ' +
        lo[0].toFixed(1) +
        '..' +
        hi[0].toFixed(1) +
        '   y ' +
        lo[1].toFixed(1) +
        '..' +
        hi[1].toFixed(1) +
        '   z ' +
        lo[2].toFixed(1) +
        '..' +
        hi[2].toFixed(1) +
        '   (radius ' +
        w.radius +
        ', camera ' +
        w.cam.dist +
        ' away)'
    );
    const warn = [];
    if (N > 150000) warn.push('more than 150,000 splats: heavy on a phone');
    if (w.pal.length > 48) warn.push('palette has ' + w.pal.length + ' colours; the page can only use 48');
    if (w.anim) {
      const a = w.anim,
        FR = 60;
      let rowsum = 0;
      if (a.rows) {
        for (let k = 0; k < 90; k++) a.update(1 / 30, k / 30);
        a.rows.fill(0);
      }
      const t0 = Date.now();
      for (let k = 0; k < FR; k++) {
        a.update(1 / 30, a.rows ? 3 + k / 30 : k * 0.37);
        if (a.rows) {
          for (let r = 0; r < a.rows.length; r++) rowsum += a.rows[r];
          a.rows.fill(0);
        }
      }
      const ms = (Date.now() - t0) / FR,
        rows = a.rows ? rowsum / FR : Math.ceil((a.start + a.count) / 512) - Math.floor(a.start / 512),
        mb = (rows * 8192 * 4) / 1e6;
      console.log(
        'animation   ' +
          a.count +
          ' splats in the moving span, ' +
          ms.toFixed(1) +
          ' ms of work and ' +
          mb.toFixed(1) +
          ' MB sent to the graphics card each frame' +
          (a.parts ? '   parts: ' + a.parts.length : '')
      );
      if (mb > 8) warn.push('sends ' + mb.toFixed(1) + ' MB per frame: likely to stutter on a phone');
      if (ms > 8) warn.push('animation takes ' + ms.toFixed(1) + ' ms a frame');
      pose(w, 0);
    }
    const im = R.render(w, view({})),
      hexs = (im.palette || w.pal).map(h => '#' + h.toString(16).padStart(6, '0')),
      tot = im.w * im.h;
    console.log('picture     ' + im.w + ' x ' + im.h + ' art pixels, each ' + im.px + ' screen pixels');
    console.log('colours on screen (share of the picture):');
    im.use.forEach((u, i) =>
      console.log(
        '  ' +
          String(i).padStart(2) +
          ' ' +
          hexs[i] +
          ' ' +
          ((100 * u) / tot).toFixed(1).padStart(5) +
          '%  ' +
          '#'.repeat(Math.round((40 * u) / tot)) +
          (u === 0 ? '  (never shows from here)' : '')
      )
    );
    const unused = [];
    im.use.forEach((u, i) => {
      if (!u) unused.push(i);
    });
    if (unused.length > hexs.length / 3)
      warn.push(unused.length + ' of ' + hexs.length + ' colours never show from the default view');
    console.log(warn.length ? 'warnings:\n  ' + warn.join('\n  ') : 'no warnings');
  },
  shot() {
    if (pos[0] !== 'replay') die('Use shot replay <recipe.json> --out <image.png>');
    Shot.replay(pos[1],{out:opt.out,root:opt.root,entry:__filename});
  },
  render() {
    const w = buildPreview(), diagnostics = previewPasses(),
      t = num('t', 0);
    const suffixes = reviewSidecars(diagnostics);
    shot?.destination(outputFile(w.id+'.png'),suffixes);
    pose(w, t);
    const t0 = Date.now(),
      im = R.render(w, view({ t, ...diagnostics?.settings }));
    diagnostics?.capture(im, opt.px1 ? 1 : im.px);
    console.log('drawn in', Date.now() - t0, 'ms');
    /* --text [ascii|symbols|braille|blocks]: drawn as text (K.ascii.draw), --tg screen pixels a font pixel (2), --tcolour scene|ink|mono;
       the characters themselves are written beside it, as <id>.txt */
    if (opt.text) {
      const T = asciiFrame(im, w);
      const f = save(w.id + '.png', T), ft = textSidecar(f); fs.writeFileSync(ft, T.text + '\n'); console.log('wrote', ft); console.log('as text:', T.cols, 'x', T.rows, 'characters');
      diagnostics?.write(f, { times: [t] });
      shot?.finish(f,{suffixes});
      return;
    }
    const output = save(w.id + '.png', R.upscale(im, opt.px1 ? 1 : im.px));
    diagnostics?.write(output, { times: [t] });
    shot?.finish(output,{suffixes});
  },
  variants() {
    const seeds = list('seeds', [3, 7, 12, 19, 22, 27]), group = opt.group || 'silhouette';
    if (!seeds.length || seeds.length > 48 || !seeds.every(Number.isSafeInteger) ||
        !['silhouette', 'openness', 'wear'].includes(group))
      die('variants requires up to 48 integer seeds and a valid grouping dimension');
    const C = require('./crisp.js'), critic = require('./critic.js');
    const t = num('t', 0), w = num('w', 104), h = num('h', 82);
    const results = seeds.map(seed => {
      const world = build(pos[0], seed);
      if (!world.variant || !Number.isFinite(world.variant[group])) die('this scene does not publish variant metrics');
      pose(world, t);
      const config = view({ t, w, h, px: 1, ortho: true });
      const shot = R.render(world, config);
      const { mark, bg, ...lint } = critic.lint(shot, { bg: world.pal[0] });
      const shimmer = opt.motion ? critic.flicker(Array.from({ length: 8 }, (_, index) =>
        R.render(world, { ...config, yaw: (config.yaw ?? world.cam.yaw) + index * .006 })), { bg: world.pal[0] }) : undefined;
      return { seed, shot, data: { ...world.variant, crisp: C.measure(shot, { bg: world.pal[0] }), lint, shimmer } };
    }).sort((a, b) => a.data[group] - b.data[group] || a.seed - b.seed);
    const file = save('variants.png', R.grid(results.map(row => R.upscale(row.shot, num('scale', 3))),
      num('cols', Math.min(3, results.length)), results.map(row => String(row.seed))));
    const report = file.replace(/\.[^.]+$/, '') + '.json';
    fs.writeFileSync(report, JSON.stringify({ group, variants: results.map(row => ({ seed: row.seed, ...row.data })) }, null, 2) + '\n');
    console.log('wrote', report);
  },
  atlas() {
    const w = build(pos[0]);
    const fps = num('fps', 12), from = num('from', num('t', 0)), to = num('to', from);
    if (!Number.isFinite(fps) || fps <= 0 || fps > 240 || !Number.isFinite(from) || !Number.isFinite(to) || to < from)
      die('atlas needs a positive frame rate and an ordered time range');
    const frames = Math.max(1, Math.ceil((to - from) * fps - 1e-8));
    if (frames > 512) die('atlas supports up to 512 frames');
    const times = Array.from({ length: frames }, (_, index) => from + index / fps);
    const directory = opt.out ? path.resolve(opt.out) : path.join(OUT, w.id + '-atlas');
    const { spriteAtlas, writeAtlas } = require('./sprite-atlas.js');
    const atlas = spriteAtlas(w, { width: num('w', 96), height: num('h', 96), directions: num('directions', 8),
      columns: num('cols', num('directions', 8)), maps: opt.maps ? String(opt.maps).split(',') : [],
      pivot: opt.pivot ? list('pivot') : w.cam.target, view: view(), yaw: num('yaw', w.cam.yaw),
      pitches:opt.pitches===undefined?undefined:list('pitches'),times,fps,pose });
    writeAtlas(directory, atlas);
    console.log('wrote', directory, atlas.metadata.frames.length, 'frames');
  },
  'transition-review'() {
    const world = buildPreview();
    if (opt.plan !== undefined && typeof opt.plan !== 'string') die('--plan needs a transition review JSON file');
    if (opt.out !== undefined && (typeof opt.out !== 'string' || !/\.png$/i.test(opt.out)))
      die('Transition review output needs a PNG filename');
    const plan = opt.plan === undefined ? world.transitionReview : JSON.parse(fs.readFileSync(path.resolve(opt.plan), 'utf8'));
    shot?.destination(outputFile(world.id+'-transition-review.png'),['.json']);
    const { transitionReview } = require('./transition-review.js');
    const { image, report } = transitionReview(world,{ plan, width:num('w',160), height:num('h',90), scale:num('scale',1), view:view(), pose });
    const file = save(world.id+'-transition-review.png',image);
    const reportFile = file.replace(/\.png$/i,'')+'.json';
    fs.writeFileSync(reportFile, JSON.stringify(report,null,2)+'\n');
    console.log('wrote',reportFile, '('+report.flagCount+' flags)');
    shot?.finish(file,{fps:report.fps,suffixes:['.json']});
    if (opt['fail-on-flags'] && report.flagCount) process.exitCode = 2;
  },
  'silhouette-review'() {
    const world=buildPreview(), time=num('t',0);
    pose(world,time);
    const {silhouetteReview}=require('./silhouette-review.js');
    const {image,report}=silhouetteReview(world,{time,width:num('w',96),height:num('h',96),
      directions:num('directions',8),pitches:opt.pitches===undefined?undefined:list('pitches'),
      yaw:num('yaw',world.cam.yaw),pivot:opt.pivot ? list('pivot') : world.cam.target,
      columns:num('cols',4),scale:num('scale',1),view:view()});
    const file=save(world.id+'-silhouette-review.png',image);
    const reportFile=file.replace(/\.[^.]+$/,'')+'.json';
    fs.writeFileSync(reportFile,JSON.stringify(report,null,2)+'\n');
    console.log('wrote',reportFile);
  },
  'pose-review'() {
    const w = build(pos[0]);
    const blocking = w.poseBlocking;
    if (!blocking?.markers?.length) die('pose-review needs a scene with poseBlocking landmarks');
    const { spriteAtlas, writeAtlas } = require('./sprite-atlas.js');
    const directory = opt.out ? path.resolve(opt.out) : path.join(OUT, w.id + '-poses');
    const directions = num('directions', 8);
    const atlas = spriteAtlas(w, { width: num('w', 96), height: num('h', 96), directions,
      columns: directions, maps: ['silhouette'], yaw: num('yaw', w.cam.yaw),
      pivot: opt.pivot ? list('pivot') : w.cam.target, view: view(),
      fps: blocking.clip.fps, times: blocking.markers.map(marker => marker.time), pose });
    atlas.metadata.poses = blocking.markers;
    writeAtlas(directory, atlas);
    const empty = atlas.metadata.frames.filter(frame => !frame.silhouette.pixels).length;
    const atEdge = atlas.metadata.frames.filter(frame => frame.silhouette.touchesBorder).length;
    console.log('wrote', directory, blocking.markers.length + ' poses × ' + directions + ' directions');
    if (empty || atEdge) console.log('review:', empty + ' empty, ' + atEdge + ' touching the sprite bounds');
  },
  'motion-review'() {
    const world = build(pos[0]);
    const review = world.motionReview;
    if (!review?.findings || !review.focus) die('motion-review needs a scene with a motion review');
    const findings = review.findings.filter(issue => !opt.finding || opt.finding === issue.kind || opt.finding === issue.id);
    if (opt.finding && !findings.length) die('no motion finding matches ' + opt.finding);
    const report = JSON.stringify({ scene: world.id, duration: review.duration,
      findings: findings.map(issue => ({ ...issue, focus: review.focus(issue.id) })) }, null, 2) + '\n';
    if (!opt.out) process.stdout.write(report);
    else {
      const file = path.resolve(opt.out);
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, report);
      console.log('wrote', file);
    }
  },
  'clip-sequence'() {
    const world = build(pos[0]), sequence = world.clipSequence;
    if (!sequence?.steps || !sequence.suggestCut) die('clip-sequence needs a scene with a clip sequence');
    const cut = opt.handoff === undefined ? undefined : sequence.suggestCut(num('handoff'));
    const { duration, alignment, travel, steps, handoffs, keys, cues, change } = sequence;
    const report = JSON.stringify({ scene: world.id, duration, alignment, travel, steps, handoffs, keys, cues, change, cut }, null, 2) + '\n';
    if (!opt.out) process.stdout.write(report);
    else {
      const file = path.resolve(opt.out);
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, report);
      console.log('wrote', file);
    }
  },
  'authored-contacts'() {
    const world = build(pos[0]), timeline = world.contactTimeline;
    if (!timeline?.contacts || !timeline.inspect) die('authored-contacts needs a scene with an authored contact timeline');
    const { duration, contacts, handoffs } = timeline;
    const sample = opt.at === undefined ? undefined : timeline.inspect(num('at'));
    const report = JSON.stringify({ scene: world.id, duration, contacts,
      handoffs: handoffs.map(key => ({ ...key, focus: timeline.focus(key.id) })), sample }, null, 2) + '\n';
    if (!opt.out) process.stdout.write(report);
    else {
      const file = path.resolve(opt.out);
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, report);
      console.log('wrote', file);
    }
  },
  'motion-fx'() {
    const world = build(pos[0]), fx = world.motionFx;
    if (!fx?.effects || !fx.at) die('motion-fx needs a scene with an authored Motion FX stack');
    const time = opt.at === undefined ? undefined : num('at');
    const sample = time === undefined ? undefined : world.motionFxDemo?.update?.(time) ?? { time, layers: fx.at(time) };
    const report = JSON.stringify({ scene: world.id, duration: fx.duration,
      capacity: fx.capacity, effects: fx.effects(), sample }, null, 2) + '\n';
    if (!opt.out) process.stdout.write(report);
    else {
      const file = path.resolve(opt.out);
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, report);
      console.log('wrote', file);
    }
  },
  'cloth-review'() {
    const world = build(pos[0]), review = world.clothReview, demo = world.clothDemo;
    if (!review?.bake || !demo?.start) die('cloth-review needs a scene with an authored cloth panel');
    if (opt.bake !== undefined && typeof opt.bake !== 'string') die('--bake needs a JSON output filename');
    const sourceTime = num('pose', demo.selected());
    demo.start(sourceTime);
    review.advance(num('through', 30));
    let bake;
    if (opt.bake) {
      const take = review.bake();
      bake = path.resolve(opt.bake);
      fs.mkdirSync(path.dirname(bake), { recursive: true });
      fs.writeFileSync(bake, JSON.stringify(take) + '\n');
    }
    const regions = Object.fromEntries(['pin', 'free', 'protected'].map(role => [role, review.regions().filter(value => value === role).length]));
    process.stdout.write(JSON.stringify({ scene: world.id, sourceTime: demo.selected(),
      nu: review.nu, nv: review.nv, regions, ...review.state(), ...(bake && { bake }) }, null, 2) + '\n');
  },
  'animation-timeline'() {
    const world = build(pos[0]), timeline = world.animationTimeline;
    if (typeof timeline?.report !== 'function') die('animation-timeline needs a scene with world.animationTimeline');
    for (const key of ['state', 'preview', 'out', 'stage', 'at', 'part', 'direction', 'loop', 'finding', 'fix', 'frames', 'w', 'h'])
      if (opt[key] === true) die('--' + key + ' needs a value');
    const state = opt.state && path.resolve(opt.state);
    const reportFile = opt.out && path.resolve(opt.out);
    if (state && state === reportFile) die('--state and --out need different paths');
    let saved;
    if (state && fs.existsSync(state)) {
      saved = JSON.parse(fs.readFileSync(state, 'utf8'));
      if (saved.scene !== world.id) die('Timeline state belongs to another scene');
      timeline.restore(saved.context);
    }
    const patch = {};
    if (opt.stage !== undefined) patch.stage = opt.stage;
    if (opt.at !== undefined) patch.time = num('at');
    if (opt.part !== undefined) patch.part = opt.part === 'off' ? null : opt.part;
    if (opt.direction !== undefined) patch.direction = num('direction');
    if (opt.loop === 'off') patch.loop = null;
    else if (opt.loop !== undefined) {
      const ends = String(opt.loop).split(',');
      if (ends.length !== 2 || ends.some(value => !value.trim())) die('--loop needs start,end or off');
      const [start, end] = ends.map(Number);
      patch.loop = { start, end, wraps: start > end };
    }
    if (opt.finding === 'off') timeline.clearFocus();
    timeline.set(patch);
    if (opt.finding && opt.finding !== 'off') timeline.focus(opt.finding);
    const motion = timeline.motionReview();
    for (const layer of saved?.corrections ?? []) {
      if (!motion?.accept(layer.id)) die('Saved correction is no longer available: ' + layer.id);
      motion.setEnabled(layer.id, layer.enabled);
    }
    if (opt.fix !== undefined) {
      const id = timeline.snapshot().focus?.id;
      if (!id) die('--fix needs a focused motion finding');
      if (opt.fix === 'accept') {
        if (!motion.accept(id)) die('No correction is available for ' + id);
        motion.setEnabled(id, true);
      } else if (opt.fix === 'remove') motion.remove(id);
      else if (opt.fix === 'mute' || opt.fix === 'enable') {
        if (!motion.setEnabled(id, opt.fix === 'enable')) die('Accept this correction before changing its state');
      } else die('--fix needs accept, mute, enable, or remove');
    }
    const before = !!opt.before, report = { scene: world.id, ...timeline.report({ before }) };
    if (opt.at !== undefined || report.state.focus) report.frame = timeline.frame(report.state.time, { before });
    if (opt.preview) {
      const { previewTimeline } = require('./animation-timeline.js');
      const { writeAtlas } = require('./sprite-atlas.js');
      const directory = path.resolve(opt.preview);
      if ([state, reportFile].some(file => file && ['atlas.json', 'color.png', 'silhouette.png']
        .some(name => file === path.join(directory, name)))) die('Use a different path for the timeline state or report');
      const atlas = previewTimeline(world, { width: num('w'), height: num('h'), frames: num('frames'), before,
        view: view(), yaw: num('yaw'), pivot: opt.pivot ? list('pivot') : undefined });
      writeAtlas(directory, atlas);
      report.preview = { directory, ...atlas.metadata };
    }
    const json = JSON.stringify(report, null, 2) + '\n';
    if (reportFile) {
      fs.mkdirSync(path.dirname(reportFile), { recursive: true });
      fs.writeFileSync(reportFile, json);
    }
    if (state) {
      fs.mkdirSync(path.dirname(state), { recursive: true });
      const pending = state + '.' + require('node:crypto').randomUUID() + '.tmp';
      try {
        fs.writeFileSync(pending, JSON.stringify({ scene: world.id, context: report.state,
          corrections: report.lanes.corrections.map(({ id, enabled }) => ({ id, enabled })) }, null, 2) + '\n');
        fs.renameSync(pending, state);
      } finally {
        if (fs.existsSync(pending)) fs.unlinkSync(pending);
      }
    }
    if (!reportFile) process.stdout.write(json);
  },
  retarget() {
    require('./retarget.js').run({ K: lib().KIT, build, pos, options: opt, view: view() });
  },
  'environment-parity'() {
    const parity = require('./environment-parity.js');
    const result = parity.compare({chrome:opt.chrome,hardware:opt.hardware,fixture:opt.fixture});
    const directory = opt.out ? path.resolve(opt.out) : path.join(OUT,'environment-parity');
    parity.write(directory,result);
    for (const {id,mean,p95} of result.frames) console.log(id,mean.toFixed(3),'mean RGB byte error, p95',p95);
    console.log('wrote',directory);
  },
  passes() {
    const w = buildPreview(), t = num('t', 0);
    pose(w, t);
    const passes = opt.channels ? String(opt.channels).split(',') : true;
    const im = R.render(w, view({ t, passes }));
    const directory = opt.out ? path.resolve(opt.out) : path.join(OUT, w.id + '-passes');
    require('./pass-preview.js').writePasses(directory, im, opt.px1 ? 1 : im.px);
    console.log('wrote', directory);
  },
  /* the ramps a diorama is shaded on, most used first, and what kind each is: one hue darker and lighter, or turning as it darkens.
     For a one-hue ramp a turning one made from the same palette is offered (the diorama is not changed). */
  ramps() {
    globalThis.INK_RAMPS = new Map();
    const w = build(pos[0]),
      K = lib().KIT,
      hx = i => '#' + w.pal[i].toString(16).padStart(6, '0'),
      all = [...globalThis.INK_RAMPS.entries()].sort((a, b) => b[1] - a[1]),
      total = all.reduce((s, e) => s + e[1], 0);
    let dull = 0;
    console.log(w.id + ': ' + all.length + ' ramps, ' + total.toLocaleString() + ' dabs shaded on them');
    for (const [ramp, cnt] of all.slice(0, num('n', 12))) {
      const c = K.ramp.check(w.pal, ramp);
      console.log(
        (((100 * cnt) / total).toFixed(1) + '%').padStart(6) +
          '  [' +
          ramp.join(', ') +
          ']  ' +
          ramp.map(hx).join(' ') +
          '   ' +
          c.says
      );
      if (c.says.startsWith('one hue')) {
        dull += cnt;
        const mid = w.pal[ramp[ramp.length >> 1]],
          uniq = [...new Set(ramp)],
          m = K.ramp.make(w.pal, {
            base: mid,
            n: uniq.length,
            dark: K.ramp.hsl(w.pal[ramp[0]])[2],
            light: K.ramp.hsl(w.pal[ramp[ramp.length - 1]])[2]
          });
        if (m.ramp.length === uniq.length && m.ramp.join() !== uniq.join() && Math.abs(m.travel) >= 12)
          console.log(
            '          try [' +
              m.ramp.join(', ') +
              ']  ' +
              m.ramp.map(hx).join(' ') +
              '   ' +
              m.says +
              ' (furthest reach ' +
              Math.max(...m.miss).toFixed(2) +
              ')'
          );
      }
    }
    console.log(
      Math.round((100 * dull) / Math.max(1, total)) + '% of the dabs in the ramps listed are on one-hue ramps'
    );
  },
  /* the value check: does the picture read in three tones? The picture is drawn small, the background taken out, and what is left
     sorted into dark, middle and light by how bright it is. A picture that is nearly all one of them is flat however good its colours. */
  values() {
    const w = build(pos[0]),
      t = num('t', 0);
    pose(w, t);
    const im = R.render(w, view({ t })),
      bg = (im.palette || w.pal)[0],
      bgc = [(bg >> 16) & 255, (bg >> 8) & 255, bg & 255],
      n = im.w * im.h,
      lum = new Float32Array(n),
      on = new Uint8Array(n);
    let lo = 255,
      hi = 0,
      cnt = 0;
    for (let i = 0; i < n; i++) {
      const r = im.rgb[i * 3],
        g = im.rgb[i * 3 + 1],
        b = im.rgb[i * 3 + 2];
      if (r === bgc[0] && g === bgc[1] && b === bgc[2]) continue;
      on[i] = 1;
      cnt++;
      lum[i] = 0.299 * r + 0.587 * g + 0.114 * b;
      if (lum[i] < lo) lo = lum[i];
      if (lum[i] > hi) hi = lum[i];
    }
    const a = lo + (hi - lo) / 3,
      b = lo + ((hi - lo) * 2) / 3,
      share = [0, 0, 0],
      out = { w: im.w, h: im.h, px: im.px, rgb: new Uint8Array(n * 3) },
      tone = [40, 128, 230];
    for (let i = 0; i < n; i++) {
      if (!on[i]) continue;
      const k = lum[i] < a ? 0 : lum[i] < b ? 1 : 2;
      share[k]++;
      out.rgb[i * 3] = out.rgb[i * 3 + 1] = out.rgb[i * 3 + 2] = tone[k];
    }
    const pc = share.map(v => Math.round((100 * v) / Math.max(1, cnt))),
      least = Math.min(...pc),
      most = Math.max(...pc),
      says =
        hi - lo < 90
          ? 'FLAT: the darkest and lightest things are close together (' +
            Math.round(lo) +
            ' to ' +
            Math.round(hi) +
            ' of 255)'
          : most > 72
            ? 'ONE TONE: ' + most + '% of it is ' + ['dark', 'middle', 'light'][pc.indexOf(most)]
            : least < 8
              ? 'TWO TONES: almost no ' + ['dark', 'middle', 'light'][pc.indexOf(least)] + ' (' + least + '%)'
              : 'reads in three tones';
    console.log(
      w.id +
        '  dark ' +
        pc[0] +
        '%  middle ' +
        pc[1] +
        '%  light ' +
        pc[2] +
        '%   brightness ' +
        Math.round(lo) +
        ' to ' +
        Math.round(hi) +
        '   ' +
        says
    );
    if (!opt.quiet) save(w.id + '-values.png', R.grid([R.upscale(im, im.px), R.upscale(out, im.px)], 2));
  },
  sheet() {
    const artHistory = require('../src/art-effects.js').history({ frames: 24 });
    const volumeHistory = lib().KIT.atmosphere.history();
    const w = buildPreview(), diagnostics = previewPasses(),
      ts = times(),
      cols = num('cols', Math.min(4, ts.length)),
      imgs = [];
    for (const t of ts) {
      pose(w, t);
      const im = R.render(w, view({ t, artHistory, volumeHistory, w: num('w', 600), h: num('h', 420), ...diagnostics?.settings }));
      diagnostics?.capture(im, opt.px1 ? 1 : im.px);
      imgs.push(displayFrame(im, w));
    }
    const output = save(
      w.id + '-sheet.png',
      R.grid(
        imgs,
        cols,
        ts.map(t => t + 's')
      )
    );
    diagnostics?.write(output, { times: ts, cols });
    console.log('times', ts.join(' '));
  },
  /* one picture with the moments either side laid faintly over it: what moved, and how far, at a glance */
  ghost() {
    const w = build(pos[0]),
      t = num('t', 1),
      sp = num('spacing', 0.12),
      n = num('n', 2),
      ts = opt.ghosts
        ? list('ghosts')
            .concat([t])
            .sort((a, b) => a - b)
        : Array.from({ length: 2 * n + 1 }, (_, i) => +(t + (i - n) * sp).toFixed(4)).filter(x => x >= 0),
      imgs = [];
    for (const q of ts) {
      pose(w, q);
      const im = R.render(w, view({ t: q, w: num('w', 600), h: num('h', 420) }));
      imgs.push({ t: q, im: R.upscale(im, im.px) });
    }
    const main = imgs.find(q => q.t === t) || imgs[imgs.length - 1],
      others = imgs.filter(q => q !== main),
      out = main.im.rgb.slice(),
      a = num('fade', 0.5) / Math.max(1, others.length);
    for (let i = 0; i < out.length; i++) {
      let v = main.im.rgb[i] * (1 - a * others.length);
      for (const g of others) v += g.im.rgb[i] * a;
      out[i] = Math.round(v);
    }
    save(w.id + '-ghost.png', { w: main.im.w, h: main.im.h, rgb: out });
    console.log('at', main.t + 's, with ghosts at', others.map(q => q.t + 's').join(' '));
  },
  /* the ready clips and reactions, by name */
  acts() {
    const K = lib().KIT;
    console.log(
      'squash and stretch clips (K.acts.clip):',
      K.acts.KINDS.map(k => k + ' ' + K.acts.DUR[k] + 's').join(', ')
    );
    console.log('reaction fields (K.deform.emote):', K.deform.EMOTES.join(', '));
    console.log('reactions (K.acts.emotes):');
    for (const r of K.acts.REACTIONS)
      console.log('  ' + r.id.padEnd(18) + r.motion.padEnd(11) + r.expression.padEnd(12) + r.label);
    console.log('easings (K.anim.ease):', K.anim.EASES.join(', '));
    console.log('presentation cues (K.anim.cue):', Object.keys(K.anim.CUES).join(', '));
    console.log('presets (K.anim.preset): heavy-impact, contact-impact, lightning, discovery, slow');
    console.log('actions (K.acts.clock):', Object.keys(K.acts.ACTION.duration).join(', '));
  },
  perf() {
    const secs = num('secs', 5), fps = num('fps', 60), uploadGap = num('upload-gap', 0);
    if (!(secs > 0 && Number.isFinite(secs) && fps > 0 && Number.isFinite(fps)) ||
      !Number.isSafeInteger(uploadGap) || uploadGap < 0) die('perf needs positive --secs and --fps, and nonnegative integer --upload-gap');
    const frames = Math.ceil(secs * fps);
    if (!Number.isSafeInteger(frames) || frames > 36000) die('perf can sample at most 36000 frames');
    const w = build(pos[0]), a = w.anim;
    const report = { scene: w.id, splats: w.count, buildMs: w.buildMs, frames: a ? frames : 0,
      pixelBudget: w.look?.pixelBudget ?? null, meanMs: 0, p95Ms: 0, worstMs: 0, meanBytes: 0, peakBytes: 0, meanUploads: 0 };
    if (a) {
      const { uploadRows } = require('../src/frame-budget.js');
      if (opt['gpu-signal'] && w.signal) a.gpuSignal = true;
      const timings = [];
      let bytes = 0, uploads = 0, total = 0;
      for (let frame = 0; frame < frames; frame++) {
        const start = process.hrtime.bigint();
        const changed = a.update(1 / fps, frame / fps);
        const ms = Number(process.hrtime.bigint() - start) / 1e6;
        timings.push(ms);
        total += ms;
        let frameBytes = 0;
        if (changed && a.rows) {
          uploadRows(a.rows, (first, end) => {
            frameBytes += (end - first) * 32768;
            uploads++;
          }, uploadGap);
        } else if (changed && a.count) {
          frameBytes += (Math.ceil((a.start + a.count) / 512) - Math.floor(a.start / 512)) * 32768;
          uploads++;
        }
        if (a.bones) frameBytes += Math.ceil(a.bones.length / (768 * 4)) * 768 * 16;
        bytes += frameBytes;
        report.peakBytes = Math.max(report.peakBytes, frameBytes);
      }
      timings.sort((left, right) => left - right);
      report.meanMs = total / frames;
      report.p95Ms = timings[Math.ceil(frames * .95) - 1];
      report.worstMs = timings[frames - 1];
      report.meanBytes = bytes / frames;
      report.meanUploads = uploads / frames;
    }
    if (opt.json) {
      console.log(JSON.stringify(report));
      return;
    }
    console.log(w.id + ': ' + w.count.toLocaleString() + ' splats, built in ' + w.buildMs + ' ms');
    console.log('Animation: ' + report.meanMs.toFixed(2) + ' ms/frame (' + report.p95Ms.toFixed(2) + ' ms at p95)');
    console.log('Planned uploads: ' + Math.round(report.meanBytes / 1024) + ' KiB/frame, peak ' +
      Math.round(report.peakBytes / 1024) + ' KiB, ' + report.meanUploads.toFixed(1) + ' splat uploads/frame');
    console.log('The browser measures drawing and GPU time separately.');
  },
  validate() {
    if (!pos[0]) die('validate which file?');
    const io = require('./look.js');
    if (!opt.world && (opt.kind === 'look' || io.isSource(pos[0])))
      return io.report(io.assertValid(io.inspectSource(pos[0], opt, lib())), opt, pos[0]);
    if (lib().KIT.world && worldCLI().validate(pos[0])) return;
    const report = io.assertValid(worldCLI().inspectLook(pos[0]));
    if (opt.json || opt.out) return io.report(report, opt, pos[0]);
    const label = report.scene ? ' (' + report.scene.id + ', "' + report.scene.name + '")' : '';
    console.log(pos[0] + ': sound' + label);
  },
  depth() {
    require('./depth.js')(pos[0], opt, lib(), path.join(OUT, 'depth-import'));
  },
  mesh() {
    const w = build(pos[0]),
      m = w.mesh;
    console.log(
      m.tris +
        ' faces, ' +
        m.verts +
        ' points; ' +
        (m.mode === 'uv' ? (m.geometry === 'sdf' ? 'SDF reconstruction with UV transfer and alpha' : 'UV surface stamps with alpha') : m.sheet
          ? 'open (' + (m.open * 100).toFixed(0) + '% of its edges are loose): treated as a sheet with thickness'
          : 'closed: treated as a solid') +
        '; materials: ' +
        m.mats.join(', ')
    );
    console.log(
      w.count +
        ' splats in ' +
        m.hues +
        ' colours of ' +
        (w.pal.length - 1) / m.hues +
        ' shades' +
        (m.mode === 'uv' ? ', UV-atlas detail' : ', field cell ' + m.cell.toFixed(3)) +
        ', built in ' +
        w.buildMs +
        ' ms'
    );
    opt.n = opt.n || 4;
    CMD.turn(w);
  },
  turn(w0) {
    const w = w0 || build(pos[0]),
      n = num('n', 8),
      t = num('t', 0),
      imgs = [],
      labs = [];
    pose(w, t);
    for (let k = 0; k < n; k++) {
      const yaw = w.cam.yaw + (k / n) * Math.PI * 2,
        im = R.render(w, view({ t, yaw, w: num('w', 600), h: num('h', 420) }));
      imgs.push(R.upscale(im, im.px));
      labs.push('y' + yaw.toFixed(1));
    }
    save(w.id + '-turn.png', R.grid(imgs, num('cols', 4), labs));
  },
  clip() {
    const artHistory = require('../src/art-effects.js').history({ frames: 24 });
    const volumeHistory = lib().KIT.atmosphere.history();
    const w = buildPreview(), diagnostics = previewPasses(),
      fps = num('fps', 12),
      from = num('from', 0),
      to = num('to', 6),
      n = Math.max(2, Math.round((to - from) * fps)),
      frames = [], ts = [], camera = clipCamera(w),
      f = outputFile(w.id+'-clip.png');
    const suffixes = reviewSidecars(diagnostics);
    shot?.destination(f,suffixes);
    for (let k = 0; k < n; k++) {
      const t = from + k / fps;
      pose(w, t);
      const im = R.render(w, view({ t, artHistory, volumeHistory, w: num('w', 600), h: num('h', 420),
        ...camera?.(k/(n-1)), ...diagnostics?.settings }));
      diagnostics?.capture(im, opt.px1 ? 1 : im.px);
      ts.push(t);
      frames.push(displayFrame(im, w));
    }
    fs.mkdirSync(path.dirname(f), { recursive: true });
    PNG.animate(f, frames, fps);
    diagnostics?.write(f, { times: ts, fps });
    if (opt.text) {
      const textFile = textSidecar(f);
      fs.writeFileSync(textFile, frames.map(frame => frame.text).join('\n\f\n') + '\n');
      console.log('wrote', textFile);
    }
    shot?.finish(f,{fps,suffixes});
    console.log('wrote', f, frames.length, 'frames at', fps, 'a second (an animated PNG: a browser will play it)');
  },
  motion() {
    const w = build(pos[0]);
    if (!w.anim) die(w.id + ' has no animation of its own');
    const a = w.anim,
      d = w.data,
      n0 = a.start,
      n1 = a.start + a.count,
      M = n1 - n0,
      from = num('from', 0),
      to = num('to', 12),
      dt = 1 / 30,
      prev = new Float32Array(M * 3),
      rest = new Float32Array(M * 3),
      peak = new Float32Array(M);
    pose(w, from);
    for (let i = 0; i < M; i++) for (let k = 0; k < 3; k++) rest[i * 3 + k] = prev[i * 3 + k] = d[(n0 + i) * 16 + k];
    let worst = 0,
      worstT = 0,
      worstI = 0,
      low = 1e9,
      lowT = 0,
      bad = 0;
    const jumps = [],
      JUMP = num('jump', 0.6);
    for (let t = from + dt; t <= to + 1e-9; t += dt) {
      pose(w, t);
      let stepMax = 0,
        cnt = 0,
        jx = 0,
        jy = 0,
        jz = 0;
      for (let i = 0; i < M; i++) {
        const q = (n0 + i) * 16,
          x = d[q],
          y = d[q + 1],
          z = d[q + 2];
        if (!(x === x && y === y && z === z)) {
          bad++;
          continue;
        }
        const m = Math.hypot(x - prev[i * 3], y - prev[i * 3 + 1], z - prev[i * 3 + 2]);
        if (m > peak[i]) peak[i] = m;
        if (m > stepMax) stepMax = m;
        if (m > JUMP) {
          cnt++;
          jx += rest[i * 3];
          jy += rest[i * 3 + 1];
          jz += rest[i * 3 + 2];
        }
        if (m > worst) {
          worst = m;
          worstT = t;
          worstI = i;
        }
        if (y < low) {
          low = y;
          lowT = t;
        }
        prev[i * 3] = x;
        prev[i * 3 + 1] = y;
        prev[i * 3 + 2] = z;
      }
      if (cnt)
        jumps.push(
          t.toFixed(2) +
            's  ' +
            String(cnt).padStart(6) +
            ' splats, up to ' +
            (stepMax / dt).toFixed(0) +
            ' units a second, around (' +
            (jx / cnt).toFixed(1) +
            ', ' +
            (jy / cnt).toFixed(1) +
            ', ' +
            (jz / cnt).toFixed(1) +
            ') at rest'
        );
    }
    const sorted = Float32Array.from(peak).sort(),
      pc = f => (sorted[Math.min(M - 1, Math.floor(f * M))] / dt).toFixed(1);
    let still = 0;
    for (let i = 0; i < M; i++) if (peak[i] < 1e-4) still++;
    console.log(w.id + ': ' + M + ' splats watched from ' + from + 's to ' + to + 's, thirty times a second');
    console.log(
      'fastest any splat moves   ' +
        (worst / dt).toFixed(1) +
        ' units a second, at ' +
        worstT.toFixed(2) +
        's, a splat that rests at (' +
        [0, 1, 2].map(k => rest[worstI * 3 + k].toFixed(1)).join(', ') +
        ')'
    );
    console.log(
      'peak speed by share       half are under ' +
        pc(0.5) +
        ', 90% under ' +
        pc(0.9) +
        ', 99% under ' +
        pc(0.99) +
        ' units a second'
    );
    console.log(
      'never move at all         ' +
        still +
        ' (' +
        ((100 * still) / M).toFixed(0) +
        '% of the span: these are sent to the graphics card for nothing)'
    );
    console.log('lowest point reached      y = ' + low.toFixed(2) + ' at ' + lowT.toFixed(2) + 's');
    console.log(
      jumps.length
        ? 'FAST: more than ' +
            (JUMP / dt).toFixed(0) +
            ' units a second (a strike, or something teleporting):\n  ' +
            jumps.slice(0, 12).join('\n  ') +
            (jumps.length > 12 ? '\n  and ' + (jumps.length - 12) + ' more' : '')
        : 'nothing moves faster than ' + (JUMP / dt).toFixed(0) + ' units a second'
    );
    if (bad) console.log('NOT A NUMBER: ' + bad + ' positions');
    if (a.parts) {
      const pk = new Float32Array(a.parts.length);
      for (let i = 0; i < M; i++) {
        const b = a.partOf ? a.partOf(n0 + i) : 0;
        if (peak[i] > pk[b]) pk[b] = peak[i];
      }
      console.log(
        'fastest part: ' +
          Array.from(pk)
            .map((v, i) => [v, a.parts[i]])
            .sort((p, q) => q[0] - p[0])
            .slice(0, 8)
            .map(e => e[1] + ' ' + (e[0] / dt).toFixed(1))
            .join(',  ')
      );
    }
    if (a.period) {
      pose(w, from);
      const p0 = Float32Array.from({ length: M * 3 }, (_, k) => d[(n0 + ((k / 3) | 0)) * 16 + (k % 3)]);
      if (!a.stateful) {
        pose(w, from + a.period);
        let mx = 0;
        for (let i = 0; i < M; i++)
          mx = Math.max(
            mx,
            Math.hypot(
              d[(n0 + i) * 16] - p0[i * 3],
              d[(n0 + i) * 16 + 1] - p0[i * 3 + 1],
              d[(n0 + i) * 16 + 2] - p0[i * 3 + 2]
            )
          );
        console.log('loop: after one period of ' + a.period + 's the pose is off by at most ' + mx.toFixed(3));
      }
    }
  },
  selftest() {
    process.exit(require('./selftest.js')(lib()) ? 1 : 0);
  },
  snap() {
    fs.mkdirSync(SNAPS, { recursive: true });
    const ids = pos[0] === 'all' ? lib().SCENES.map(s => s.id) : pos;
    if (!ids.length) die('snap which diorama? (or: all)');
    for (const id of ids) {
      const w = build(id),
        ts = opt.t !== undefined ? list('t') : w.anim ? [0, 1.7] : [0];
      for (const t of ts) {
        pose(w, t);
        const im = R.render(w, { t });
        PNG.write(path.join(SNAPS, w.id + '@' + t + '.png'), im.w, im.h, im.rgb);
      }
      console.log('kept', w.id, 'at', ts.join(', '));
    }
  },
  /* a diorama beside a reference picture, both at true pixel size: the reference brought down to its art pixels (--px: how many of
     its pixels make one, as 2 for a picture shown at twice its size), the diorama drawn at the same size in art pixels, the two side
     by side scaled up alike (--up, 3), and the crisp measures of each, so a look can be held to a picture it is after */
  /* pixel-art lint: the mistakes pixel artists name, at a diorama's own pixel size, beside what the references come to (the medians
     of the pixel-art references at their own size): orphan pixels, doubles (lines two pixels thick at a step), jaggies (uneven steps
     along an edge), banding (tones that only echo an edge), pillow shading (darker all round the rim, whichever way it faces), noise
     (clusters of three pixels or fewer) and colours. --map writes where each is: orphans red, doubles magenta, jaggies yellow,
     banding cyan */
  lint() {
    const Cr = require('./critic.js'),
      ids = pos.length ? pos : die('lint <id ...> [--map --ortho]'),
      keys = ['orphans', 'doubles', 'jaggies', 'banding', 'pillow', 'noise', 'colours'],
      fmt = (k, v) => (k === 'colours' ? String(v) : (v * 100).toFixed(1) + '%');
    console.log(''.padEnd(16) + keys.map(k => k.padStart(10)).join(''));
    console.log('references'.padEnd(16) + keys.map(k => fmt(k, Cr.REFERENCE[k]).padStart(10)).join(''));
    for (const id of ids) {
      const t = num('t', 2),
        w = build(id);
      pose(w, t);
      const im = R.render(w, view({ t })),
        img = { w: im.w, h: im.h, rgb: im.rgb || im.color },
        r = Cr.lint(img, { bg: (im.palette || w.pal)[0] });
      console.log(w.id.padEnd(16) + keys.map(k => fmt(k, r[k]).padStart(10)).join(''));
      if (opt.map) save(w.id + '-lint.png', R.upscale(Cr.lintMap(img, r), im.px));
    }
  },
  /* a review sheet: the diorama from a fixed set of shots (its own view, its four sides, from above, from low down, far, near and
     close), one sheet, with the lint of each under its label in the log; beside the last sheet of it (kept as -review-before.png),
     so a change can be seen. --ref picture.png --px 2 puts a reference first */
  review() {
    const Cr = require('./critic.js'),
      [id] = pos.length ? pos : die('review <id> [--ref picture.png --px 2 --ortho]'),
      t = num('t', 2),
      w = build(id),
      c = w.cam || {},
      shots = [];
    pose(w, t);
    for (const [label, dy, pitch, zoom] of Cr.SHOTS) {
      const im = R.render(
        w,
        view({
          t,
          w: num('w', 480),
          h: num('h', 340),
          yaw: (opt.yaw === undefined ? c.yaw || 0 : +opt.yaw) + dy,
          pitch: pitch === null ? (opt.pitch === undefined ? c.pitch : +opt.pitch) : pitch,
          zoom
        })
      );
      const img = { w: im.w, h: im.h, rgb: im.rgb || im.color },
        r = Cr.lint(img, { bg: (im.palette || w.pal)[0] });
      console.log(
        label.padEnd(8),
        ['orphans', 'doubles', 'jaggies', 'banding', 'pillow']
          .map(k => k + ' ' + (r[k] * 100).toFixed(1) + '%')
          .join('  ')
      );
      shots.push(R.upscale(img, im.px));
    }
    if (opt.ref) {
      const k = num('px', 1),
        src = PNG.read(path.resolve(opt.ref)),
        W = Math.floor(src.w / k),
        H = Math.floor(src.h / k),
        ref = { w: W, h: H, rgb: new Uint8Array(W * H * 3) };
      for (let y = 0; y < H; y++)
        for (let x = 0; x < W; x++) {
          const s0 =
            (Math.min(src.h - 1, Math.floor(y * k + k / 2)) * src.w + Math.min(src.w - 1, Math.floor(x * k + k / 2))) *
            3;
          ref.rgb.set(src.rgb.subarray(s0, s0 + 3), (y * W + x) * 3);
        }
      const up = Math.max(1, Math.round(shots[0].h / H));
      shots.unshift(R.upscale(ref, up));
    }
    // (the shots padded to one size, for the sheet)
    const SW = Math.max(...shots.map(q => q.w)),
      SH = Math.max(...shots.map(q => q.h)),
      pad = q => {
        const o = { w: SW, h: SH, rgb: new Uint8Array(SW * SH * 3) };
        for (let y = 0; y < q.h; y++) o.rgb.set(q.rgb.subarray(y * q.w * 3, (y + 1) * q.w * 3), y * SW * 3);
        return o;
      },
      sheet = R.grid(shots.map(pad), num('cols', 3)),
      file = path.join(OUT, w.id + '-review.png'),
      before = path.join(OUT, w.id + '-review-before.png');
    fs.mkdirSync(OUT, { recursive: true });
    if (fs.existsSync(file)) fs.copyFileSync(file, before);
    save(w.id + '-review.png', sheet);
    if (fs.existsSync(before)) {
      const b = PNG.read(before);
      if (b.w === sheet.w && b.h === sheet.h) save(w.id + '-review-vs-before.png', R.grid([b, sheet], 2));
    }
  },
  /* shimmer: the diorama over a short move of the camera (--mode orbit, zoom, pan, or still: the camera at rest while time runs),
     frame by frame at one pixel size; the share of pixels that change and change back (A, B, A over three frames), which a smooth
     move should not cause, and an animated GIF of it (--frames 24, --step: how far each frame moves) */
  shimmer() {
    const Cr = require('./critic.js'),
      [id] = pos.length ? pos : die('shimmer <id> [--mode orbit|zoom|pan|still --frames 24 --step s --ortho]'),
      t0 = num('t', 2),
      n = num('frames', 24),
      mode = opt.mode || 'orbit',
      w = build(id),
      c = w.cam || {},
      frames = [];
    const st = num('step', mode === 'orbit' ? 0.004 : mode === 'zoom' ? 0.012 : mode === 'pan' ? 0.02 : 1 / 12);
    let px = 0, bg = w.pal[0];
    for (let k = 0; k < n; k++) {
      const t = mode === 'still' ? t0 + k * st : t0;
      pose(w, t);
      const v = view({ t, w: num('w', 480), h: num('h', 340) }),
        T = (v.target || c.target || [0, 0, 0]).slice();
      if (mode === 'orbit') v.yaw = (v.yaw === undefined ? c.yaw || 0 : v.yaw) + k * st;
      if (mode === 'zoom') v.zoom = (v.zoom || 1) * (1 + k * st);
      if (mode === 'pan') v.target = [T[0] + k * st, T[1], T[2] + k * st * 0.5];
      if (px) v.px = px;
      const im = R.render(w, v);
      px = px || im.px;
      bg = (im.palette || w.pal)[0];
      frames.push({ w: im.w, h: im.h, rgb: im.rgb || im.color });
    }
    const fl = Cr.flicker(frames, { bg });
    console.log(w.id + ' ' + mode + ': ' + (fl * 100).toFixed(2) + '% of pixels flicker (change and change back)');
    fs.mkdirSync(OUT, { recursive: true });
    const f = opt.out ? path.resolve(opt.out) : path.join(OUT, w.id + '-shimmer-' + mode + '.gif');
    fs.writeFileSync(
      f,
      Cr.gif(
        frames.map(q => R.upscale(q, Math.max(1, Math.min(4, px)))),
        Math.round(num('delay', 8))
      )
    );
    console.log('wrote', f);
  },
  /* paint-over: a view of the diorama at its own pixel size, to be painted over by hand or by a script, and the painted pixels taken
     back as decals: each pinned to the place on the surface it fell on (a pixel painted just past an edge is put on the surface beside
     it, carried on), so it stays put from every view. The decals are kept in studio/paint/<id>/decals.json; the game's build puts
     them in the page, and the CLI draws them at once */
  paint() {
    const [sub, id] = pos;
    if (!['export', 'absorb', 'clear', 'layers', 'tune'].includes(sub) || !id)
      die(
        'paint export|absorb|layers|tune|clear <id> [--layer name] [--dir studio/paint/<id>]'
      );
    const Paint = require('../src/paint-corrections.js'), name = opt.layer;
    if (name !== undefined && !Paint.idOK(name)) die('Paint layer needs a lowercase ID');
    if (sub === 'tune' && name === undefined) die('Paint tune needs --layer name');
    if (sub === 'absorb' && !name && ['angle', 'feather', 'opacity', 'region'].some(key => opt[key] !== undefined))
      die('Paint controls need a named layer');
    const world = sub === 'export' ? build(id, undefined, { paint: name === undefined }) : null,
      dir = paintDirectory(opt.dir ? id : world ? world.id : scene(id).id),
      dfile = path.join(dir, 'decals.json'),
      capture = name ? path.join(dir, 'layers', name) : dir;
    function save(doc) {
      const tmp = dfile + '.' + require('node:crypto').randomUUID() + '.tmp';
      try {
        fs.writeFileSync(tmp, JSON.stringify(doc), { flag: 'wx' });
        fs.renameSync(tmp, dfile);
      } finally {
        fs.rmSync(tmp, { force: true });
      }
    }
    function controls(prior) {
      const value = option => {
        if (opt[option] === true) throw Error('--' + option + ' needs a number');
        return num(option);
      };
      const angle = value('angle') ?? prior?.angle;
      const feather = value('feather') ?? (prior && Math.min(prior.feather, angle));
      const opacity = value('opacity') ?? prior?.opacity;
      let region = prior?.region;
      if (opt.region !== undefined) {
        if (typeof opt.region !== 'string') throw Error('--region needs JSON, a file, or off');
        region = opt.region === 'off' ? undefined :
          JSON.parse(fs.existsSync(opt.region) ? fs.readFileSync(opt.region, 'utf8') : opt.region);
      }
      return { angle, feather, opacity, region };
    }
    if (sub === 'layers') {
      const { decals = [], ...doc } = readPaint(dfile);
      console.log(JSON.stringify({ permanent: decals.length, layers: Paint.layers(doc).map(({ decals, ...layer }) =>
        ({ ...layer, samples: decals.length })) }, null, 2));
      return;
    }
    if (sub === 'clear') {
      if (name) {
        const doc = readPaint(dfile), layers = Paint.layers(doc);
        if (!layers.some(layer => layer.id === name)) die('Unknown paint layer ' + name);
        save({ ...doc, layers: layers.filter(layer => layer.id !== name) });
      } else if (fs.existsSync(dfile)) fs.unlinkSync(dfile);
      console.log('cleared', dfile);
      return;
    }
    if (sub === 'tune') {
      const doc = readPaint(dfile), layers = Paint.layers(doc), slot = layers.findIndex(layer => layer.id === name);
      if (slot < 0) die('Unknown paint layer ' + name);
      layers[slot] = Paint.layer({ ...layers[slot], ...controls(layers[slot]) });
      save({ ...doc, layers });
      console.log('updated paint layer', name);
      return;
    }
    if (sub === 'export') {
      const t = num('t', 2),
        w = world;
      pose(w, t);
      const pick = {},
        vw = view({ t, pick, ...(name && { paintCorrections: false }) }),
        im = R.render(w, vw);
      if (!pick.W)
        die('paint: ' + id + ' is not drawn per pixel (its look.pixel), so there is nothing to pin paint to');
      fs.mkdirSync(capture, { recursive: true });
      const { W, H } = pick,
        buf = new Float32Array(W * H * 6).fill(NaN);
      for (let r = 0; r < H; r++)
        for (let x = 0; x < W; x++) {
          const q = (H - 1 - r) * W + x,
            i = pick.win[q];
          if (i < 0 || !pick.PIX[i * 8]) continue;
          buf.set(
            [pick.X[q], pick.Y[q], pick.Z[q], pick.PIX[i * 8 + 3], pick.PIX[i * 8 + 4], pick.PIX[i * 8 + 5]],
            (r * W + x) * 6
          );
        }
      PNG.write(path.join(capture, 'view.png'), im.w, im.h, im.rgb);
      PNG.write(path.join(capture, 'paint.png'), im.w, im.h, im.rgb);
      fs.writeFileSync(path.join(capture, 'view.bin'), Buffer.from(buf.buffer));
      fs.writeFileSync(
        path.join(capture, 'view.json'),
        JSON.stringify(
          {
            id,
            w: W,
            h: H,
            t,
            camera: pick.camera,
            view: { yaw: vw.yaw, pitch: vw.pitch, zoom: vw.zoom, target: vw.target, ortho: vw.ortho },
            detail: w.detail,
            pal: w.pal.map(c => '#' + c.toString(16).padStart(6, '0')),
            how:
              'paint over paint.png in the palette colours (#ff00ff takes paint off), then: ink-studio paint absorb ' +
              id + (name ? ' --layer ' + name : '')
          },
          null,
          1
        )
      );
      console.log(
        'wrote',
        path.join(capture, 'paint.png'),
        W + 'x' + H,
        '(paint over it, then: ink-studio paint absorb ' + id + (name ? ' --layer ' + name : '') + ')'
      );
      return;
    }
    // absorb
    const meta = JSON.parse(fs.readFileSync(path.join(capture, 'view.json'), 'utf8')),
      raw = fs.readFileSync(path.join(capture, 'view.bin')),
      buf = new Float32Array(raw.buffer, raw.byteOffset, raw.byteLength / 4),
      a = PNG.read(path.join(capture, 'view.png')),
      b = PNG.read(path.resolve(opt.png || path.join(capture, 'paint.png'))),
      W = meta.w,
      H = meta.h;
    if (b.w !== a.w || b.h !== a.h)
      die('paint: the painted picture is ' + b.w + 'x' + b.h + ', the view ' + a.w + 'x' + a.h);
    if (W !== a.w || H !== a.h || buf.length !== W * H * 6)
      die('Paint capture metadata and surface coordinates do not match the view');
    if (opt['paint-mask'] !== undefined && (!name || typeof opt['paint-mask'] !== 'string'))
      die('--paint-mask needs a PNG path and a named paint layer');
    const mask = opt['paint-mask'] && PNG.raster(path.resolve(opt['paint-mask']));
    if (mask && (mask.w !== W || mask.h !== H)) die('The paint mask must have the same dimensions as paint.png');
    const pal = meta.pal.map(h => parseInt(h.slice(1), 16)),
      nearest = (r, g, bl) => {
        let best = 0,
          bd = 1e9;
        pal.forEach((c, i) => {
          const d = (((c >> 16) & 255) - r) ** 2 + (((c >> 8) & 255) - g) ** 2 + ((c & 255) - bl) ** 2;
          if (d < bd) ((bd = d), (best = i));
        });
        return [best, bd];
      },
      ok = (x, y) => x >= 0 && y >= 0 && x < W && y < H && buf[(y * W + x) * 6] === buf[(y * W + x) * 6],
      P3 = (x, y) => Array.from(buf.subarray((y * W + x) * 6, (y * W + x) * 6 + 6)),
      px = 1 / (meta.detail || 12);
    let off = 0,
      lost = 0;
    const fresh = [],
      erase = [];
    for (let y = 0; y < H; y++)
      for (let x = 0; x < W; x++) {
        const k = (y * W + x) * 3;
        if (a.rgb[k] === b.rgb[k] && a.rgb[k + 1] === b.rgb[k + 1] && a.rgb[k + 2] === b.rgb[k + 2]) continue;
        const del = b.rgb[k] === 255 && b.rgb[k + 1] === 0 && b.rgb[k + 2] === 255;
        let at = null;
        if (ok(x, y)) at = P3(x, y);
        else {
          // (past the edge of a thing: the nearest pixel that has a surface, carried on across the picture by how it changes there)
          for (let r = 1; r <= 4 && !at; r++)
            for (let dy = -r; dy <= r && !at; dy++)
              for (let dx = -r; dx <= r && !at; dx++) {
                if (Math.max(Math.abs(dx), Math.abs(dy)) !== r || !ok(x + dx, y + dy)) continue;
                const nx = x + dx,
                  ny = y + dy,
                  q = P3(nx, ny),
                  gx = ok(nx + 1, ny)
                    ? P3(nx + 1, ny)
                    : ok(nx - 1, ny)
                      ? P3(nx - 1, ny).map((v, i) => 2 * q[i] - v)
                      : q,
                  gy = ok(nx, ny + 1)
                    ? P3(nx, ny + 1)
                    : ok(nx, ny - 1)
                      ? P3(nx, ny - 1).map((v, i) => 2 * q[i] - v)
                      : q;
                at = q.slice();
                for (let i = 0; i < 3; i++) at[i] = q[i] + (gx[i] - q[i]) * -dx + (gy[i] - q[i]) * -dy;
              }
        }
        if (!at) {
          lost++;
          continue;
        }
        if (del) {
          erase.push(at);
          continue;
        }
        const [ci, d] = nearest(b.rgb[k], b.rgb[k + 1], b.rgb[k + 2]);
        if (d > 12) off++;
        const row = [...at.map(v => Math.round(v * 1e4) / 1e4), ci];
        if (mask) {
          const i = (y * W + x) * 4, d = mask.data;
          row.push(Math.min(1, (.2126 * d[i] + .7152 * d[i + 1] + .0722 * d[i + 2]) * d[i + 3] / mask.max ** 2));
        }
        fresh.push(row);
      }
    const doc = readPaint(dfile), layers = name && Paint.layers(doc),
      slot = name ? layers.findIndex(layer => layer.id === name) : -1,
      prior = name && layers[slot], source = name && Paint.view(meta.camera),
      old = name ? prior && prior.time === meta.t && Paint.sameView(prior.view, source) ? prior.decals : [] : doc.decals ?? [],
      near = (d, e) => Math.hypot(d[0] - e[0], d[1] - e[1], d[2] - e[2]) < px * 0.45,
      kept = old.filter(d => !fresh.some(e => near(d, e)) && !erase.some(e => near(d, e))),
      decals = kept.concat(fresh);
    if (name) {
      const correction = Paint.layer({ id: name, view: source, time: meta.t, ...controls(prior), decals });
      if (slot < 0) layers.push(correction);
      else layers[slot] = correction;
      save({ ...doc, id, detail: meta.detail, layers });
    } else save({ ...doc, id, detail: meta.detail, decals });
    console.log(
      `${fresh.length} pixels painted, ${erase.length} taken off; ${decals.length} decals in ${dfile}` +
        (off ? `; ${off} were not palette colours (the nearest was taken)` : '') +
        (lost ? `; ${lost} had no surface within 4 pixels and were left out` : '')
    );
  },
  compare() {
    const [id, ref] = pos;
    if (opt.looks !== undefined || /\.json$/i.test(ref ?? '')) {
      const file = opt.looks ?? ref;
      if (!id || typeof file !== 'string') die('compare needs a scene and --looks cases.json');
      if (opt.out !== undefined && (typeof opt.out !== 'string' || !/\.png$/i.test(opt.out)))
        die('A look comparison image needs --out sheet.png');
      if (typeof opt.report === 'string' && (path.resolve(id) === path.resolve(opt.report) ||
        opt.out && path.resolve(opt.out) === path.resolve(opt.report))) die('--report needs a separate path');
      const cases = JSON.parse(fs.readFileSync(file, 'utf8'));
      const Preview = require('./look-preview.js');
      let world = worldCLI().lookSnapshot(id);
      if (!world) {
        world = Preview.withAlbedo(() => build(id));
        pose(world, num('t', 0));
      }
      const time = world.lookSnapshot?.time ?? num('t', 0);
      const { report, frames } = require('./look-compare.js').compare(world, cases, lib(),
        view({ t: time, px: num('px', 1) }), { opt, file, images: Boolean(opt.out) });
      if (opt.out) {
        const up = num('up', 1), cols = num('cols', Math.min(4, frames.length));
        if (![up, cols].every(n => Number.isSafeInteger(n) && n > 0)) die('--up and --cols need positive integers');
        const sheet = R.grid(frames.map(frame => R.upscale(frame, up)), cols, report.results.map(row => String(row.id)));
        fs.mkdirSync(path.dirname(path.resolve(opt.out)), { recursive: true });
        PNG.write(opt.out, sheet.w, sheet.h, sheet.rgb);
      }
      return require('./look.js').report(report, { out: opt.report }, file);
    }
    if (!id || !ref) die('compare <id> <reference.png> [--px 2 --up 3]');
    const C = require('./crisp.js');
    const k = num('px', 1),
      src = PNG.read(path.resolve(ref)),
      W = Math.floor(src.w / k),
      H = Math.floor(src.h / k),
      rimg = { w: W, h: H, rgb: new Uint8Array(W * H * 3) };
    for (let y = 0; y < H; y++)
      for (let x = 0; x < W; x++) {
        const s0 =
          (Math.min(src.h - 1, Math.floor(y * k + k / 2)) * src.w + Math.min(src.w - 1, Math.floor(x * k + k / 2))) * 3;
        rimg.rgb.set(src.rgb.subarray(s0, s0 + 3), (y * W + x) * 3);
      }
    // (a reference with more colours than a pixel artist's palette, as a JPEG has, is brought to --colours of them, 32 by default)
    const seen = new Set();
    for (let i = 0; i < W * H && seen.size <= 256; i++)
      seen.add((rimg.rgb[i * 3] << 16) | (rimg.rgb[i * 3 + 1] << 8) | rimg.rgb[i * 3 + 2]);
    if (seen.size > 256 || opt.colours) Object.assign(rimg, C.quantize(rimg, num('colours', 32)));
    const t = num('t', 2),
      w = buildPreview();
    pose(w, t);
    // Use one art pixel per reference pixel, regardless of the scene's detail setting.
    const im = R.render(w, view({ t, w: W, h: H, px: 1 })),
      cols = ['stray', 'specks', 'flat', 'fine', 'edges', 'spread', 'cool', 'colours'],
      fmt = (c, v) => {
        if (!Number.isFinite(v)) return 'n/a';
        if (c === 'fine') return v.toFixed(3);
        return c === 'colours' ? String(v) : (v * 100).toFixed(1) + '%';
      },
      mr = C.measure(rimg, { bg: (rimg.rgb[0] << 16) | (rimg.rgb[1] << 8) | rimg.rgb[2] }), // (its corner colour, joined to the edge, is its background)
      md = C.measure(im, { bg: (im.palette || w.pal)[0] });
    console.log(''.padEnd(16) + cols.map(c => c.padStart(10)).join(''));
    console.log(path.basename(ref).slice(0, 15).padEnd(16) + cols.map(c => fmt(c, mr[c]).padStart(10)).join(''));
    console.log(w.id.padEnd(16) + cols.map(c => fmt(c, md[c]).padStart(10)).join(''));
    const up = num('up', 3),
      a = R.upscale(rimg, up),
      b = R.upscale(im, up);
    save(w.id + '-vs-' + path.basename(ref).replace(/\.[a-z]+$/i, '') + '.png', R.grid([a, b], 2));
  },
  /* how crisp a diorama is at its own pixel size, beside what the pixel-art references came to: stray pixels (unlike all eight round
     them), specks (in same-colour patches of 3 or fewer), flat area (like all eight), the share of brightness variation at the finest
     frequencies, how much of it runs straight across or down, checker (dither) and how many colours make up 95% of it.
     A mark (!) is a target missed. --map writes where the stray pixels are. --t, and the view options, as for render */
  crisp() {
    const C = require('./crisp.js'),
      ids = pos[0] === 'all' ? lib().SCENES.map(s => s.id) : pos;
    if (!ids.length) die('crisp which diorama? (or: all)');
    const t = num('t', 2),
      pc = v => (v * 100).toFixed(1) + '%',
      cols = ['stray', 'specks', 'flat', 'fine', 'straight', 'edges', 'spread', 'cool', 'checker', 'colours'],
      fmt = (k, v) => {
        if (!Number.isFinite(v)) return 'n/a';
        if (k === 'fine' || k === 'straight') return v.toFixed(3);
        return k === 'colours' ? String(v) : pc(v);
      },
      miss = (k, v) =>
        C.FLOORS[k] !== undefined
          ? v >= C.FLOORS[k]
            ? ' '
            : '!'
          : C.TARGETS[k] === undefined
            ? ' '
            : (k === 'flat' ? v >= C.TARGETS[k] : v <= C.TARGETS[k])
              ? ' '
              : '!';
    console.log('diorama'.padEnd(16) + cols.map(c => c.padStart(11)).join(''));
    console.log(
      'references'.padEnd(16) +
        cols.map(c => (C.REFERENCE[c] ? fmt(c, C.REFERENCE[c][2]) : '').padStart(10) + ' ').join('') +
        '  (median of 8 at true pixel size)'
    );
    console.log(
      'targets'.padEnd(16) +
        cols
          .map(
            c =>
              (C.FLOORS[c] !== undefined
                ? '>' + fmt(c, C.FLOORS[c])
                : C.TARGETS[c] === undefined
                  ? ''
                  : (c === 'flat' ? '>' : '<') + fmt(c, C.TARGETS[c])
              ).padStart(10) + ' '
          )
          .join('')
    );
    let missed = 0;
    for (const id of ids) {
      const w = build(id);
      pose(w, t);
      const im = R.render(w, view({ t })),
        m = C.measure(im, { bg: (im.palette || w.pal)[0] });
      const marks = cols.map(c => (Number.isFinite(m[c]) ? miss(c, m[c]) : ' '));
      missed += marks.some(x => x === '!') ? 1 : 0;
      console.log(w.id.padEnd(16) + cols.map((c, i) => fmt(c, m[c]).padStart(10) + marks[i]).join(''));
      if (opt.map) {
        save(w.id + '-stray.png', R.upscale(C.strayMap(im, { bg: (im.palette || w.pal)[0] }), im.px));
        save(w.id + '-edges.png', R.upscale(C.edgeMap(im, { bg: (im.palette || w.pal)[0] }), im.px));
      }
    }
    if (ids.length > 1) console.log(missed + ' of ' + ids.length + ' miss a target');
  },
  check() {
    const files = fs.existsSync(SNAPS)
      ? fs
          .readdirSync(SNAPS)
          .filter(f => f.endsWith('.png') && (!pos.length || pos.includes(f.split('@')[0])))
          .sort()
      : [];
    if (!files.length) die('no reference pictures: make some with  ink-studio snap <id>');
    let fails = 0,
      cur = null,
      w = null;
    for (const f of files) {
      const [id, tt] = f.replace('.png', '').split('@'),
        t = +tt;
      if (id !== cur) {
        w = build(id);
        cur = id;
      }
      pose(w, t);
      const im = R.render(w, { t }),
        ref = PNG.read(path.join(SNAPS, f));
      let diff = 0;
      if (ref.w !== im.w || ref.h !== im.h) diff = im.w * im.h;
      else
        for (let i = 0; i < im.w * im.h; i++)
          if (
            ref.rgb[i * 3] !== im.rgb[i * 3] ||
            ref.rgb[i * 3 + 1] !== im.rgb[i * 3 + 1] ||
            ref.rgb[i * 3 + 2] !== im.rgb[i * 3 + 2]
          )
            diff++;
      const pct = (100 * diff) / (im.w * im.h),
        ok = pct <= num('allow', 0.2);
      if (!ok) {
        fails++;
        fs.mkdirSync(OUT, { recursive: true });
        const both = R.grid([R.upscale(ref.w === im.w && ref.h === im.h ? ref : im, 3), R.upscale(im, 3)], 2, [
          '0',
          '1'
        ]);
        PNG.write(path.join(OUT, 'check-' + id + '@' + t + '.png'), both.w, both.h, both.rgb);
      }
      console.log(
        (ok ? 'same     ' : 'CHANGED  ') +
          f.padEnd(26) +
          pct.toFixed(2) +
          '% of pixels differ' +
          (ok ? '' : '   (before | after in studio/out/check-' + id + '@' + t + '.png)')
      );
    }
    console.log(fails ? fails + ' changed' : 'all ' + files.length + ' the same');
    process.exit(fails ? 1 : 0);
  }
};
async function run() {
  const mode = Shot.modeFor(cmd,pos);
  if (opt.recipe !== undefined)
    shot = Shot.createRecorder(opt.recipe,{mode,scene:pos[cmd === 'sim' ? 1 : 0],options:opt,root:CWD});
  shotReplay = Shot.replayState(mode);
  shotRender = shot?.render ?? shotReplay?.render;
  if (worldCommands.has(cmd)) {
    await worldCLI().execute(cmd,pos);
    shotReplay?.verify();
    return;
  }
  if (/\.glb$/i.test(pos[0] || '') && opt.uv !== 'off') {
    try {
      importedAssets.set(path.resolve(pos[0]), await require('../index.js').readAsset(path.resolve(pos[0]), { size: 3 }));
    } catch (error) {
      if (opt.uv === true) throw error;
      console.error('UV asset import unavailable: ' + error.message + '. Using the geometry importer. Pass --uv to require UV import.');
    }
  }
  await (CMD[cmd] || (() => die('unknown command "' + cmd + '". try: ink-studio help')))();
  shotReplay?.verify();
}
run().catch(error => { console.error(error.message); process.exitCode = 1; });

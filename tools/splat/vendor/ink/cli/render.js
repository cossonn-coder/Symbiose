const { performance } = require('node:perf_hooks');
const frameBudget = require('../src/frame-budget.js');
// Draws a world without a browser: motion kinds, projection of each splat's covariance to a screen ellipse,
// blending from far to near, low-resolution sampling, dithering and palette quantization.
const FOV = (38 * Math.PI) / 180;
const PixelLook = require('../src/pixel-look.js');
const RenderStages = require('../src/render-stages.js');
const LookInputs = require('../src/look-inputs.js');
const TargetSelectors = require('../src/target-selectors.js');
const { createArtPasses, sampleFrames } = require('./art-passes.js');
const ArtPasses = require('../src/art-passes.js');
const { createEnvironmentPasses } = require('./environment-passes.js');
const ArtInk = require('../src/art-ink.js');
const ArtDirection = require('../src/art-direction.js');
const SilhouetteProtection = require('../src/silhouette-protection.js');
const DetailBudgets = require('../src/detail-budgets.js');
const ShadowArt = require('../src/shadow-art.js');
const SplatRelighting = require('../src/splat-relighting.js');
const MaterialPixelStyle = require('../src/material-pixel-style.js');
const EffectPalettes = require('../src/effect-palettes.js');
const ArtEffects = require('../src/art-effects.js');
const ArtStability = require('../src/art-stability.js');
const { footprint, sampledDepth } = require('./splat-sampling.js');
const { createMaskResolve, applyMasks } = require('./look-mask-resolve.js');
const { createLookPass } = require('./look-pass.js');
const { createAudit } = require('./render-audit.js');
const { contributionLook, contributionLayers } = require('./look-contributions.js');
const blueNoiseTiles = new WeakMap();
function blueNoise(world, { seed }) {
  if (!blueNoiseTiles.has(world)) blueNoiseTiles.set(world, new Map());
  const tiles = blueNoiseTiles.get(world);
  if (!tiles.has(seed)) {
    const { KIT } = require('../index.js').load();
    if (tiles.size >= 65) tiles.delete(tiles.keys().next().value);
    tiles.set(seed, KIT.procedural.materials.blueNoise({ seed }));
  }
  return tiles.get(seed);
}
const SampleCoverage = require('../src/sample-coverage.js');
const ContributionRules = require('../src/contribution-rules.js');
const Airflow = require('../src/airflow.js');
const LightSchedule = require('../src/light-schedule.js');
const LiveSun = require('./live-sun.js');
const surfaceShading = require('./surface-shading.js');
const SceneOptics = require('../src/scene-optics.js');
const SkyEnvironment = require('../src/sky-environment.js');
const HorizonBands = require('../src/horizon-bands.js');
const CloudField = require('../src/cloud-field.js');
const Lightning = require('../src/lightning.js');
const { resolveEnvironment, resolveWind, resolveLighting, atmosphereSources } = require('./environment.js');
const WindField = require('../src/wind-field.js');
const Precipitation = require('./precipitation.js');
const RainImpacts = require('./rain-impacts.js');
const AtlasSprites = require('../src/atlas-sprites.js');
const AtlasRaster = require('./atlas-sprites.js');
const SurfaceRaster = require('./sprite-surfaces.js');
let SplatFields, AtmosphereEmitters;
const { cameraRays, surfacePoint, reflectionSampler, atmosphereQuality, mediaSampler, applyAtmosphere } = require('./scene-optics.js');
const clamp = (x, a, b) => (x < a ? a : x > b ? b : x),
  sstep = (a, b, x) => {
    const t = clamp((x - a) / (b - a), 0, 1);
    return t * t * (3 - 2 * t);
  };
function viewMatrix(yaw, pitch, dist, T) {
  const cp = Math.cos(pitch),
    sp = Math.sin(pitch),
    e = [T[0] + dist * cp * Math.sin(yaw), T[1] + dist * sp, T[2] + dist * cp * Math.cos(yaw)];
  let zx = e[0] - T[0],
    zy = e[1] - T[1],
    zz = e[2] - T[2];
  const zl = Math.hypot(zx, zy, zz);
  zx /= zl;
  zy /= zl;
  zz /= zl;
  let xx = zz,
    xz = -zx;
  const xy = 0,
    xl = Math.hypot(xx, xz);
  xx = xl ? xx / xl : Math.cos(yaw);
  xz = xl ? xz / xl : -Math.sin(yaw);
  const yx = zy * xz - zz * xy,
    yy = zz * xx - zx * xz,
    yz = zx * xy - zy * xx;
  return [
    xx,
    yx,
    zx,
    0,
    xy,
    yy,
    zy,
    0,
    xz,
    yz,
    zz,
    0,
    -(xx * e[0] + xy * e[1] + xz * e[2]),
    -(yx * e[0] + yy * e[1] + yz * e[2]),
    -(zx * e[0] + zy * e[1] + zz * e[2]),
    1
  ];
}
// o: t (seconds), yaw, pitch, dist, target, w, h (the size of the stage in screen pixels), zoom (1 = the diorama's own distance), raw (skip the palette)
function render(world, o, preparedPalettes) {
  if (!o?.renderStats) return renderFrame(world, o, preparedPalettes);
  const start = performance.now();
  const counters = {
    rasterPasses:0, fragments:0, translucentFragments:0, peakDeferredFragments:0, deferredFlushes:0,
    volume:{ traces:0, boundsTests:0, boundsCacheHits:0, mediaQueries:0, mediaCacheHits:0, fullFogCacheHits:0, emptyFogIntervals:0, raySamples:0,
      analyticSegments:0, marchSteps:0, densitySamples:0, skipTests:0, skippedSteps:0, cloudTraces:0, cloudSamples:0 }
  };
  const frame = renderFrame(world, { ...o, renderStats:false, counters }, preparedPalettes);
  frame.renderStats = { ...counters, frameMs:performance.now()-start };
  return frame;
}

function renderFrame(world, o, preparedPalettes) {
  o = o || {};
  const counters = o.counters;
  if (counters) counters.rasterPasses++;
  const lensScale = o.lensScale ?? 1;
  if (!Number.isFinite(lensScale) || lensScale <= 0) throw new RangeError('Lens scale must be finite and positive');
  const tangent = Math.tan(FOV / 2) / lensScale;
  const look = world.look || {};
  const detailBudget = !o.raw && DetailBudgets.prepare(look.detailBudgets);
  const direction = ArtDirection.prepare(look.artDirection,o.artDirection);
  const protection = SilhouetteProtection.prepare(look.silhouetteProtection,o.silhouetteProtection);
  const subject = protection?.bind(world);
  const c = world.cam,
    sceneTime = o.t ?? world.lookSnapshot?.time ?? 0,
    t = ArtDirection.time(direction,sceneTime),
    yaw = o.yaw === undefined ? c.yaw : o.yaw,
    pitch = o.pitch === undefined ? c.pitch : o.pitch,
    an = world.anim || {},
    cameraMotion = o.lockCamera ? {} : an,
    dist0 = o.dist || c.dist / (o.zoom || 1),
    /* a diorama's own zoom (a camera punch) moves the eye, not the size of an art pixel */
    dist = dist0 / (cameraMotion.zoom || 1),
    T0 = o.target || c.target,
    T = cameraMotion.kick ? [T0[0] + cameraMotion.kick[0], T0[1] + cameraMotion.kick[1], T0[2] + cameraMotion.kick[2]] : T0,
    cw = o.w || 900,
    ch = o.h || 620;
  const audit = o.lookAudit === true ? createAudit() : o.lookAudit;
  const onPaletteClip = audit && ((scope, i, r, g, b) => audit.palette(scope, world.pal[i], r, g, b));
  const transparent = !!o.transparent && !o.captureCoverage;
  const integrateFootprint = o.splatFilter === 'footprint';
  const orderMode = o.splatOrder ?? look.splatOrder ?? 'center';
  const sortedSurfaces = orderMode === 'surface';
  const fragmentBudget = o.fragmentBudget ?? 500000;
  if (!['center', 'surface'].includes(orderMode) ||
      (sortedSurfaces && (!Number.isSafeInteger(fragmentBudget) || fragmentBudget < 1 || fragmentBudget > 2e6)))
    throw new RangeError('Invalid splat order or fragment budget');
  const probe = typeof o.fragmentProbe === 'function' ? o.fragmentProbe : null;
  const styled = !o.raw && !o.samples && !o.captureCoverage;
  const lookInputs = !o.raw && (o.lookInputSession ?? LookInputs.session(t, () =>
    world.lookSnapshot?.query ?? world.surfaceEffects?.query ?? require('../index.js').load().KIT.world.query.fromScene(world, t)));
  const lookOptions = { palette: world.pal, roles: world.paletteRoles, context: world.surfaceEffects, lookInputs,
    blueNoise: settings => blueNoise(world, settings), skipMasks: o.lookMasks === false };
  const stages = !o.raw && RenderStages.plan(world, lookOptions);
  const optics = o.raw ? null : RenderStages.optics(look.optics, lookOptions);
  const scopedReflection = world.reflections?.length && (look.paletteConstraints?.targets?.length ||
    world.surfaces?.some(({ settings }) => settings.paletteConstraint));
  const coverageAware = !o.raw && (o.coverageAware ?? look.coverageAware ?? Boolean(optics || scopedReflection)) === true;
  const retainContributions = coverageAware || Boolean(stages || optics);
  const legacyLook = styled && !retainContributions;
  const effectPaletteSettings = styled ? EffectPalettes.prepare(
    o.effectPalettes === true ? look.effectPalettes : o.effectPalettes ?? look.effectPalettes, world.pal
  ) : !o.raw && !o.captureCoverage ? o.effectPaletteCapture : null;
  const ink = styled ? ArtInk.prepare(o.ink ?? look.ink, world.pal) : null;
  const effects = styled ? ArtEffects.prepare(o.artEffects ?? look.effects, world.pal) : null;
  const stable = ArtStability.prepare(look.stable, o.stable);
  const specializedResolve = legacyLook && stable && stable.resolve !== 'native';
  const anchoring = !o.raw && !o.captureCoverage && !!stable?.anchorSpaces.size;
  const requestedPasses = ArtPasses.select(o.passes);
  const passSelection = new Set(requestedPasses);
  let lookPass;
  if (styled && stages?.owner) passSelection.add('splatId');
  if (styled && stages?.postMask) {
    for (const channel of ['position', 'objectPosition', 'normal']) passSelection.add(channel);
  }
  if (effects) for (const channel of ArtEffects.channels) passSelection.add(channel);
  if (effects?.smear && o.artHistory) passSelection.add('emissionMotion');
  if (ink) for (const channel of ArtInk.channels) passSelection.add(channel);
  if (effectPaletteSettings) {
    for (const channel of ['coverage', 'depth']) passSelection.add(channel);
    if (effectPaletteSettings.ramps.has('emission')) passSelection.add('emission');
    if (effectPaletteSettings.objects.size) passSelection.add('objectId');
    if (effectPaletteSettings.materials.size) passSelection.add('materialId');
  }
  if (anchoring) {
    passSelection.add('depth');
    if (stable.anchorSpaces.has('world')) passSelection.add('position');
    if (stable.anchorSpaces.has('object')) passSelection.add('objectPosition');
    if (stable.rules.some(rule => rule.object !== undefined)) passSelection.add('objectId');
    if (stable.rules.some(rule => rule.material !== undefined)) passSelection.add('materialId');
  }
  if (specializedResolve || (legacyLook && stable?.protect.size)) {
    for (const channel of ['objectId', 'materialId', 'emission', 'protected']) passSelection.add(channel);
  }
  const finishLook = (frame, passes, fog, effectSignals, source) => {
    if (ink) frame = ArtInk.apply(frame, passes, ink, world.pal, fog);
    if (effects) frame = ArtEffects.apply(frame, passes, effects, t, {
      history: o.artHistory, world, palette: world.pal, motionReference: frame.motionReference
    });
    const ditherAt = anchoring ? (x,y) => ArtStability.ditherCoordinates(stable, passes, y*frame.w+x, x, y) : undefined;
    if (styled && stages?.post) RenderStages.finish(frame, stages, passes, t, lookPass?.post, audit, ditherAt);
    if (effectSignals) {
      frame = EffectPalettes.apply(frame, passes, effectSignals, source, world.pal, o.captureEffectPalettes, ditherAt);
      if (audit) for (const ramp of effectSignals.rules.ramps.values()) audit.addPalette(ramp.packed);
    }
    if (audit) {
      frame.lookAudit = audit.report();
    }
    if (!o.captureMotion) delete frame.motionReference;
    if (requestedPasses.length) frame.passes = ArtPasses.subset(passes, requestedPasses);
    return frame;
  };
  if (look.pixelSize !== undefined && (!Number.isSafeInteger(look.pixelSize) || look.pixelSize < 1))
    throw new RangeError('look.pixelSize must be a positive integer');
  const tone = legacyLook ? PixelLook.prepareTone(o.tone ?? look.tone, settings => blueNoise(world, settings)) : null;
  const paletteRules = legacyLook || coverageAware ? PixelLook.preparePaletteConstraints(o.paletteConstraints ?? look.paletteConstraints, {
    palette: world.pal, roles: world.paletteRoles, blueNoise: settings => blueNoise(world, settings),
    context: world.surfaceEffects, skipMasks: o.lookMasks === false, skipMaskedStacks: o.colorStack === false, onPaletteClip
  }) : preparedPalettes;
  const animationGrade = o.ignoreLookGrade ? undefined : an.grade;
  const colorGrade = (legacyLook || coverageAware) && !tone && PixelLook.colorGrade(world.pal, world.paletteRoles, animationGrade,
    o.paletteRemap ?? look.paletteRemap, o.colorCurves ?? look.colorCurves, o.colorLut ?? look.colorLut,
    o.colorStack ?? look.colorStack,
    onPaletteClip && ((i, r, g, b) => onPaletteClip({
      assetId: o.colorStack === undefined ? look.colorStackAssetId : undefined, stack: (o.colorStack ?? look.colorStack)?.name
    }, i, r, g, b)));
  const grade = colorGrade || animationGrade;
  const evaluatedPalette = colorGrade ? PixelLook.gradePalette(grade) : undefined;
  if (audit) {
    if (legacyLook) audit.addPalette(tone?.palette || evaluatedPalette || (grade ? PixelLook.gradePalette(grade) : world.pal));
    audit.addPalette(stages?.palettes);
    audit.addPalette(optics?.palettes);
  }
  const globalPaletteMark = passSelection.has('target') && (tone || grade) ?
    { assetId: look.colorStackAssetId, stackName: tone ? 'Tone' : (o.colorStack ?? look.colorStack)?.name } : null;
  const rel = c.dist / dist0,
    rho = (world.detail ?? 12) * Math.pow(rel, rel > 1 ? 0.5 : 0.25),
    preferred = look.pixelSize || clamp(Math.round(ch / (2 * tangent * rho * dist0)), 1, 18),
    px = o.px || frameBudget.artScale(cw, ch, preferred, o.raw || o.samples || o.captureCoverage ? null : look.pixelBudget),
    W = Math.ceil(cw / px),
    H = Math.ceil(ch / px);
  if (!o.samples && !o.captureCoverage) o.shotFrame?.({
    time:sceneTime, skyTime:ArtDirection.time(direction,o.skyTime ?? sceneTime,'environment'), camera:{ target:Array.from(T), yaw, pitch, distance:dist, lensScale, orthographic:!!o.ortho },
    art:{ width:W, height:H, pixelSize:px }
  });
  const historyFrames = effects?.smear && o.artHistory ? o.artHistory.previous(t, W, H, world) : [];
  const motionFrame = historyFrames[Math.max(0, historyFrames.length - (effects?.smear?.frames || 1))];
  const motionFrom = o.motionFrom ?? motionFrame?.motionReference;
  const captureMotion = !!o.captureMotion || passSelection.has('motion') || passSelection.has('emissionMotion');
  if (legacyLook && (specializedResolve || (o.colored && !tone))) {
    const native = render(world, Object.assign({}, o, { colored: false, samples: true, worked: true, px, passes: [...passSelection], artInkActive: !!ink,
      captureMotion, motionFrom, maskGrade: !tone && grade, reflectionTint: effects?.reflection,
      previewPalette: globalPaletteMark, lookAudit: audit,
      effectPaletteCapture: effectPaletteSettings,
      captureFog: o.captureFog || ink?.ramps.has('fog'), resolveDetailCleanup: !!detailBudget?.affectsCleanup }), paletteRules);
    const samples = render(
      world,
      Object.assign({}, o, {
        colored: false,
        samples: true,
        lookMasks: false,
        pick: undefined,
        px: px / 2,
        w: W * px,
        h: H * px,
        reflectionScale: 2,
        artGridScale: 2,
        volumeHistory: null,
        artInkActive: !!ink,
        captureMotion: false, motionFrom: undefined, effectPaletteCapture: null, reflectionTint: effects?.reflection,
        passes: specializedResolve ? ['coverage'] : false,
        lookAudit: false
      })
    );
    const basePalette = tone?.palette || world.pal;
    const palette = basePalette.map(h => [((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255]);
    const local = native.localAt && {
      at: native.localAt, palettes: native.localPalettes,
      constraints: native.localConstraints,
      scene: palette, grade: !tone && grade,
      output: PixelLook.outputPalettes(evaluatedPalette || basePalette, native.localPalettes)
    };
    const amount = (o.dither === undefined ? 0.35 : o.dither) * 0.3 * world.dither;
    const img = specializedResolve ? ArtStability.resolve(native, samples, stable, palette, PixelLook, amount,
      { local, tone, grade: !tone && grade }) :
      PixelLook.resolve(Object.assign(samples, {
        palette, local, contour: !ink, grade, interiorColor: native.color, dither: amount,
        ditherAt: anchoring ? (x, y) => ArtStability.ditherCoordinates(stable, native.passes, (H - 1 - y) * W + x, x, y) : null
      }));
    native.cleanDetail?.(img.rgb, !!(o.clean || (look.clean && !tone?.preserveDots)));
    applyMasks(img.rgb, native.masked);
    return finishLook(Object.assign(img, { px, drawn: samples.drawn },
      evaluatedPalette && !local && { palette: evaluatedPalette },
      !specializedResolve && native.detail && { detail: native.detail },
      native.motionReference && { motionReference: native.motionReference },
      native.silhouetteMask && { silhouetteMask:native.silhouetteMask },
      native.alpha && { alpha: native.alpha },
      (native.orderFallback || samples.orderFallback) && { orderFallback: true },
      native.volumeStats && { volumeStats: native.volumeStats },
      o.captureFog && native.fog && { fog: native.fog }), native.passes, native.fog, native.effectSignals, native.color);
  }
  lookPass = createLookPass(W, H, passSelection, o.lookPassRegistry);
  /* orthographic (o.ortho): no perspective, every ray parallel, the picture as big as the perspective one is at the target. The eye
     is set well back, so nothing comes behind it however far in the camera zooms; the zoom is the size of the view */
  const ortho = !!o.ortho,
    oh = dist * tangent,
    eyeD = ortho ? dist + 2 * world.radius + 4 : dist,
    reflectionPlane = o.reflectionPlane,
    focal = ortho ? H / 2 / oh : H / 2 / tangent,
    cameraView = viewMatrix(yaw, pitch, eyeD, T),
    view = ortho && stable?.snap ? ArtStability.snapView(cameraView, focal / (o.artGridScale || 1), stable.anchor) : cameraView,
    V = reflectionPlane ? SceneOptics.reflectedView(view, reflectionPlane) : view,
    near = Math.max(0.4, 0.15 * dist),
    tp = 1 / tangent,
    asp = W / H,
    baseCount = world.count,
    R = world.radius;
  const hex = i => {
      const h = world.pal[i];
      return [((h >> 16) & 255) / 255, ((h >> 8) & 255) / 255, (h & 255) / 255];
    },
    bg = o.captureCoverage || transparent || tone ? [0, 0, 0] : hex(0),
    fog = hex(world.fog.c),
    limx = (1.3 * 0.5 * W) / focal,
    limy = (1.3 * 0.5 * H) / focal;
  const eye = [
    -(V[0] * V[12] + V[1] * V[13] + V[2] * V[14]),
    -(V[4] * V[12] + V[5] * V[13] + V[6] * V[14]),
    -(V[8] * V[12] + V[9] * V[13] + V[10] * V[14])
  ];
  const paintView = { direction: [V[2], V[6], V[10]], ...(ortho ? {} : { eye }) };
  const paint = o.paintCorrections === false ? null : world.paintCorrections;
  const climate = resolveEnvironment(world,o,sceneTime,direction);
  const { skyTime,environment,weather,exposure,cutouts } = climate;
  const effectRules = EffectPalettes.activate(effectPaletteSettings, environment?.parameters);
  const windState = resolveWind(world,o,climate);
  const { windConfig,flow,wind,localWind,airAt,windAt } = windState;
  const relative = SplatRelighting.frame(world, o, climate);
  const lightingOptions = (o.relighting ?? world.relighting) ? { ...o, liveSun: false } : o;
  const { celestial,sun,flash,clouds } = resolveLighting(world,lightingOptions,climate,windState,direction);
  const shadowFootprint = 2 * dist * tangent * (o.artGridScale || 1) / H;
  if (!sun && o.shadowArt !== false) world = ShadowArt.frame(world, shadowFootprint);
  const travel = (at, birth, time) => {
    const age = time - birth;
    return flow ? flow.travel(...at, skyTime - age, skyTime) : airAt(...at).velocity.map(v => v * age);
  };
  const splatSource = o.splatFields === true ? world.splatFields : o.splatFields ?? world.splatFields;
  const fields = splatSource && (SplatFields ??= require('../index.js').load().KIT.splatFields).compile(splatSource);
  const emitterSource = o.atmosphereEmitters === true ? world.atmosphereEmitters : o.atmosphereEmitters ?? world.atmosphereEmitters;
  const emitters = emitterSource ? (AtmosphereEmitters ??= require('../index.js').load().KIT.atmosphere.emitters).compile(emitterSource) : null;
  const emitted = emitters && emitters.frame(t, {
    volumes: o.atmosphere !== false, travel,
    socket(target, birth) {
      if (target.entity === undefined) return an.atmosphereSocket?.(target,birth);
      return world.atmospherePose ? world.atmospherePose(target,birth) : AtmosphereEmitters.entityPose(world.lookSnapshot?.query,target);
    }
  });
  const splatCount = fields?.count ?? 0, emittedCount = emitted?.count ?? 0;
  const N = baseCount + splatCount + emittedCount;
  const birthIds = N > baseCount && captureMotion ? new Float64Array(N) : undefined;
  let d = world.data;
  if (N > baseCount) {
    d = new Float32Array(N * 16);
    d.set(world.data.subarray(0, baseCount * 16));
    if (splatCount) fields.write(d, baseCount, t, { birthIds, travel });
    if (emittedCount) emitted.write(d, baseCount + splatCount, birthIds);
  }
  if (paint) {
    if (d === world.data) d = d.slice(0, baseCount * 16);
    paint.paint(d, world.pal, paintView);
  }
  const mediumLook = medium => optics?.transform(medium) ?? PixelLook.mediumTransform(paletteRules, medium);
  const colorForVolume = volume => mediumLook(TargetSelectors.medium(volume.id, volume.mediumKind ?? volume.type, volume.tags));
  const volumes = SceneOptics.prepareVolumes(atmosphereSources(world,o), world.pal, colorForVolume, weather?.fogGain);
  if (emitted?.volumes.length) volumes.push(...SceneOptics.prepareVolumes(emitted.volumes, world.pal, colorForVolume));
  const sourceWater = o.water !== false && world.water?.count && world.water.raySegments ? world.water : null;
  const water = sourceWater && (optics || paletteRules) ?
    sourceWater.mapColors((id, kind) => mediumLook(TargetSelectors.medium(id, kind))) : sourceWater;
  const glassIndex = optics && TargetSelectors.index(world);
  const glassLooks = glassIndex && new Map();
  const centers = captureMotion ? new Float32Array(N * 2).fill(NaN) : null;
  const motionReference = centers && { w: W, h: H, centers, ...(birthIds && { birthIds, baseCount, splatSource, emitterSource }) };
  const art = createArtPasses([...passSelection].filter(name => name !== 'target' && name !== 'mask' &&
    !ArtPasses.environment.includes(name)), W, H);
  const environmentPasses = createEnvironmentPasses(passSelection, W, H, world);
  const skyPass = environmentPasses?.passes.sky, fogPass = environmentPasses?.passes.fogTransmittance;
  const reflectPass = environmentPasses?.passes.reflections;
  const centerReflection = reflectPass && new Float64Array(3), fragmentReflection = reflectPass && new Float64Array(3);
  const rayAt = cameraRays(V, eye, W, H, focal, ortho);
  const baseSky = SkyEnvironment.withCelestials(environment?.sky, celestial, celestial && hex(0));
  const sky = baseSky && direction?.bands ? { ...baseSky, bands:direction.bands } : baseSky;
  const aerial = o.atmosphere !== false && !o.captureCoverage ?
    SkyEnvironment.aerial(world.aerialPerspective, o.aerialPerspective, environment?.parameters) : null;
  const cloudShadow = clouds?.shadow;
  const spriteAtlases=AtlasSprites.placements(world.spriteAtlases,o.spriteAtlases);
  const surfaceFragments=o.spriteSurfaces===false?[]:SurfaceRaster.rasterize(world.spriteSurfaces,{V,W,H,focal,ortho,near,
    clip:reflectionPlane && (p=>SceneOptics.planeDistance(reflectionPlane,...p)>reflectionPlane.bias)});
  const surfaceDepth=surfaceFragments.length?new Float32Array(W*H).fill(Infinity):null;
  for(const sample of surfaceFragments)surfaceDepth[sample.p]=sample.z;
  const sprites=AtlasRaster.rasterize(spriteAtlases,{
    eye,V,W,H,focal,ortho,near,rayAt,time:t,override:o.spriteAtlasMode,sun,
    objectDither: anchoring && stable.anchorSpaces.has('object'),
    subject: protection?.match,
    visibility:(position)=>(cloudShadow?.(...position)??1)*(exposure?.light?.(...position)??1),
    clip:reflectionPlane && (position=>SceneOptics.planeDistance(reflectionPlane,...position)>reflectionPlane.bias)
  });
  for(const sample of surfaceFragments)sprites.push(sample);
  sprites.sort((a,b)=>b.z-a.z);
  const cloudEye = ortho ? eye.map((value, i) => value - (eyeD - dist) * V[2 + i * 4]) : eye;
  const cloudView = clouds?.view?.(cloudEye, ortho ? [V[2],V[6],V[10]] : null);
  const axialDepth = volumes.length || water || aerial || cloudView ? new Float32Array(W * H).fill(Infinity) : null;
  const fogScales = protection?.affectsFog && axialDepth ? new Float64Array(W*H).fill(1) : null;
  const silhouetteMask = protection && o.captureSilhouetteProtection ? new Uint16Array(W*H) : null;
  function subjectPixel(pixel, rule) {
    if (fogScales) fogScales[pixel] = rule?.fogScale ?? 1;
    if (silhouetteMask) silhouetteMask[(H-1-Math.floor(pixel/W))*W+pixel%W] = rule?.slot ?? 0;
  }
  // The bands use the nominal eye and sky rays. The foreground still uses its original camera and depth.
  const horizonArt = (!transparent || skyPass) && !o.captureCoverage &&
    HorizonBands.prepare(look.horizonBands, o.horizonBands)?.frame({ eye:cloudEye, yaw, pitch, distance:dist, parameters:environment?.parameters });
  const backdropClouds = clouds?.visible && !cloudView;
  const skyBase = backdropClouds && !sky ? hex(0) : bg;
  const skyOverlay = (flash || cloudView) && !sky && !backdropClouds;
  const opticalSky = sky || clouds?.visible || flash;
  const skySample = (opticalSky || horizonArt) && ((direction, out, origin, reflection, cloudSignal) => {
    if (sky) SkyEnvironment.shade(sky, direction, out);
    else for (let c = 0; c < 3; c++) out[c] = skyBase[c];
    if (horizonArt && !reflection) horizonArt(direction, out);
    if (origin) {
      flash?.sky(origin, direction, out);
      if (!cloudView || reflection) clouds?.paint(origin, direction, out, flash?.light, cloudSignal, counters?.volume);
    }
    return out;
  });
  const showSky = (sky || backdropClouds || flash || horizonArt) && !transparent && !o.captureCoverage;
  const captureSky = skyPass && skySample;
  const skyRay = showSky || captureSky || aerial && ortho && sky ?
    cameraRays(V, eye, W, H, ortho ? H * .5 / Math.tan((sky?.orthoFov ?? Math.PI / 3) * .5) : focal, false) : null;
  const skyRayAt = pixel => skyRay(pixel % W + .5, Math.floor(pixel / W) + .5);
  const skyDirection = pixel => skyRayAt(pixel).direction;
  const skyColor = (showSky || captureSky) && [0, 0, 0];
  const trackMedia = effectRules && ['fog', 'clouds', 'sky'].some(kind => effectRules.ramps.has(kind));
  const backdropCloud = trackMedia && showSky && backdropClouds ? new Float32Array(W * H) : null;
  const cloudSignal = backdropCloud && [0];
  // Orthographic geometry uses an artificial camera setback. Measure aerial distance from the nominal eye.
  const air = aerial && { ...aerial, start: aerial.start + eyeD - dist,
    color: sky ? (pixel, direction) => SkyEnvironment.scattering(sky, ortho ? skyDirection(pixel) : direction) : () => hex(0) };
  const skyReflectionSource = o.skyReflections ?? world.skyReflections;
  if (skyReflectionSource !== undefined && !['scene', 'material'].includes(skyReflectionSource))
    throw new RangeError('Sky reflections source must be scene or material');
  const horizon = Math.max(eyeD + 2 * R, cloudView?.horizon(eye) ?? 0);
  const volumeLighting = o.volumeLighting ?? world.volumeLighting;
  let localLighting;
  const prepareVolumeLight = () => volumeLighting ? (localLighting ??= SceneOptics.lighting(volumeLighting, world.pal,
    { time: t, localLights: o.volumeLocalLights, localShadows: o.volumeLocalShadows, celestialSun: celestial?.sun })) : undefined;
  const daylight = o.lightDaylight ?? o.environment?.daylight ?? an.daylight ?? 1;
  const dusk = LightSchedule.gain(daylight);
  const lampEye = [
    T[0]+eyeD*Math.cos(pitch)*Math.sin(yaw),
    T[1]+eyeD*Math.sin(pitch),
    T[2]+eyeD*Math.cos(pitch)*Math.cos(yaw)
  ];
  const lamps = LightSchedule.select(world.lights || [], lampEye, { daylight, duskOnly: true });
  const rainConfig = RainImpacts.settings(world.rainImpacts, o.rainImpacts);
  const precipitation = Precipitation.frame(world, o.precipitation, {
    time: skyTime, wind: wind.velocity, windAt, weather, localWind, impacts: rainConfig, exposure,
    lamps: world.precipitationRanges?.length ? LightSchedule.select(world.lights || [], lampEye, { daylight }) : [],
    localLighting: prepareVolumeLight
  });
  const rain = RainImpacts.frame(rainConfig, precipitation?.contacts, skyTime);
  const volumeWind = !windConfig && world.volumeWind && !o.wind && !weather?.wind && !an.wind
    ? Airflow.frame(world.volumeWind).velocity : null;
  const volumeFlow = volumes.some(v => v.type === 'field') && (volumeWind && exposure?.wind
    ? WindField.create(WindField.settings(true), { ambient:() => volumeWind, exposure }) : flow)?.frame(skyTime);
  const atmosphereOptions = () => {
    const quality = atmosphereQuality({ ...world.volumeQuality, ...o.volumeQuality });
    quality.wind = volumeWind ?? wind.velocity;
    if (volumeFlow) quality.windOffset = volumeFlow.windOffset;
    const media = volumes.some(volume => volume.type === 'field') ? prepareVolumeLight() : undefined;
    return { ...quality, time: t, cloudShadow, flash, media, exposure, cutouts, cloud:cloudView, effectCoverage: trackMedia,
      cloudStart:cloudView && eyeD-dist, fogTransmittance:!!fogPass, bands:direction?.bands, counters:counters?.volume };
  };
  const geometrySample = probe || sortedSurfaces || aerial || cloudShadow || flash || cloudView ? sampleFrames(world, t) : null;
  const captured = o.captureCoverage || transparent ? new Float32Array(W * H) : null;
  // The reflected pass uses the same projection and reads only the plane's front side.
  const reflectionTint = effects?.reflection || o.reflectionTint;
  const reflection =
    o.surface !== false && o.reflections !== false && world.reflections?.length
      ? reflectionSampler(
          world.reflections,
          plane =>
            render(world, {
              ...o,
              samples: false,
              colored: false,
              worked: false,
              pick: undefined,
              lookInputSession: lookInputs,
              reflectionPlane: plane,
              captureCoverage: true,
              passes: reflectionTint ? ['emission'] : false,
              reflectionTint,
              captureMotion: false,
              fragmentProbe: undefined,
              lookAudit: false,
              atmosphere: false,
              water: false,
              reflections: false,
              edges: false
            }),
          V,
          eye,
          o.reflectionScale ?? 1
        )
      : null;
  let live;
  const sunGains = sun && [0, 0, 0];
  const surface = surfaceShading(world, stages && !coverageAware ? { ...o, paletteConstraints: false } : o, {
    eye,
    forward: [V[2], V[6], V[10]],
    reflection,
    sky: opticalSky && ((direction, out, origin) => {
      if (!skyOverlay) return skySample(direction,out,origin,true);
      flash?.sky(origin,direction,out);
      cloudView && clouds.paint(origin,direction,out,flash?.light,undefined,counters?.volume);
      return out;
    }),
    skyOverlay: Boolean(skyOverlay),
    skyReflectionSource,
    parallel: ortho ? [V[2], V[6], V[10]] : null,
    footprint: (dist * 2) / (tp * H),
    time: t,
    sun: sun?.direction,
    cloudShadow,
    exposure,
    weather: weather?.surface,
    rain,
    sunVisibility: sun && ((i, x, y, z) => live?.visibility(i, x, y, z)),
    blueNoise: settings => blueNoise(world, settings), onPaletteClip,
    onSurfaceClip: audit && ((r, g, b) => audit.sample('surface', r, g, b))
  });
  const surfaceGlint = surface ? new Uint8Array(W * H) : null;
  const layerPalettes = surface?.palettes ?? [];
  const localConstraints = paletteRules
    ? Object.assign(Array(layerPalettes.length).fill(undefined), surface?.constraints).concat(paletteRules.palettes)
    : surface?.constraints;
  const localPalettes = paletteRules ? layerPalettes.concat(paletteRules.palettes.map(policy => policy.swatches)) : layerPalettes;
  if (audit && !o.raw) audit.addPalette(PixelLook.outputPalettes([], localPalettes).packed);
  const localAt = localPalettes.length && !o.raw && !retainContributions ? new Uint32Array(W * H) : null;
  const targetSlots = paletteRules?.slots(world);
  const defaultSlot = paletteRules?.defaultSlot || 0;
  const overlay = localAt && localConstraints?.some(policy => policy?.mask) &&
    { slots: new Uint32Array(W * H), owners: new Uint32Array(W * H) };
  const fallbackSlot = defaultSlot ? layerPalettes.length + defaultSlot : 0;
  const contribution = coverageAware && localPalettes.length ? contributionLook(localPalettes, localConstraints, targetSlots,
    layerPalettes.length, fallbackSlot, Array.from(world.pal, (_, i) => hex(i)), grade) : null;
  const unmasked = slot => localConstraints?.[slot - 1]?.mask ? 0 : slot;
  function localSlot(i, layer, pixel) {
    const target = targetSlots?.[i];
    const slot = target ? layerPalettes.length + target : layer || fallbackSlot;
    if (!overlay) return slot;
    const masked = slot && !unmasked(slot);
    overlay.slots[pixel] = masked ? slot : 0;
    if (!masked) return slot;
    overlay.owners[pixel] = i;
    return unmasked(layer) || unmasked(fallbackSlot) || 0;
  }
  const hasEffectInk = N > baseCount || world.effectParticles?.length || world.surfaces?.some(({ settings }) =>
    Object.values(settings.layers || {}).some(layer => layer?.type === 'projected'));
  const detail = hasEffectInk ? new Uint8Array(W * H) : null;
  // where each splat is at this moment, and what it looks like
  const X = new Float32Array(N),
    Y = new Float32Array(N),
    Z = new Float32Array(N),
    AL = new Float32Array(N),
    SC = new Float32Array(N),
    depth = new Float32Array(N),
    add = new Float32Array(N),
    wet = new Float32Array(N);
  const sampleWithdrawal = SampleCoverage.amount(o.sampleWithdrawal ?? world.sampleWithdrawal ?? 0);
  for (let i = 0, q = 0; i < N; i++, q += 16) {
    let x = d[q],
      y = d[q + 1],
      z = d[q + 2],
      al = d[q + 3],
      sc = 1;
    const kraw = Math.round(d[q + 11]),
      kind = kraw % 16,
      ph = d[q + 12],
      sp = d[q + 13],
      rg = d[q + 14],
      ex = d[q + 15];
    if (!SampleCoverage.visible(kraw, sampleWithdrawal)) al = 0;
    if (precipitation?.rows[i]) {
      const pose = precipitation.pose?.(i, x, y, z, kind, ph, sp, rg, ex, al);
      if (pose) [x, y, z, al] = pose;
      else al = 0;
    } else if (kind === 1) al *= 0.62 + 0.38 * Math.sin(t * sp + ph);
    else if (kind === 2) {
      const profileRain = kraw & Airflow.packedFlag;
      const f = ((profileRain ? skyTime : t) * sp) / rg + ph,
        pr = f - Math.floor(f);
      y -= pr * rg;
      al *= 1 - pr * pr;
      if (profileRain) {
        const { velocity } = airAt(x,y,z);
        const age = pr * rg / Math.max(sp, 1e-5);
        x += velocity[0] * age;
        z += velocity[1] * age;
        al *= weather?.rainHere ? weather.rainHere(x,z) : weather?.rainGain ?? 0;
      }
      if (exposure?.rain) {
        al *= exposure.rain(x,y,z);
        if (al && exposure.rainBlocked?.([d[q],d[q+1],d[q+2]],[x,y,z])) al = 0;
      }
      sc *= 1 + pr * ex;
    } else if (kind === 3) {
      const f = (t * sp) / rg + ph,
        pr = f - Math.floor(f);
      y += pr * rg;
      x += Math.sin(pr * 7 + ph * 50) * 0.25 * pr;
      if (kraw & Airflow.packedFlag) {
        const age = pr * rg / Math.max(sp, 0.00001);
        const shift = flow ? flow.travel(d[q],d[q+1],d[q+2],skyTime-age,skyTime) : airAt(x,y,z).velocity.map(v => v*age);
        x += shift[0];
        z += shift[1];
      }
      al *= (1 - pr) * sstep(0, 0.1, pr);
      sc *= 0.6 + pr * ex;
    } else if (kind === 4) add[i] = 0.3 * sstep(0.75, 1, Math.sin(t * sp + ph));
    else if (kind === 5) {
      const a = t * sp,
        cs = Math.cos(a),
        sn = Math.sin(a),
        nx = cs * x + sn * z;
      z = -sn * x + cs * z;
      x = nx;
    } else if (kind === 6) y += Math.sin(t * sp + ph) * rg;
    else if (kind === 7 && ex !== LightSchedule.emissionMarker) al *= 0.82 + 0.18 * Math.sin(t * sp + ph);
    else if (kind === 8) {
      const f = 0.2 + 0.8 * Math.abs(Math.sin(t * sp + ph));
      x = rg + (x - rg) * f;
      z = ex + (z - ex) * f;
      y += 0.14 * Math.sin(t * sp * 0.31 + ph);
    } else if (kind === 9) {
      const k = 1 + rg * Math.sin(t * sp + ph - y * ex);
      x *= k;
      z *= k;
    } else if (kind === 15) {
      // flutter down: a leaf or a flake, swinging as it falls
      const f = (t * sp) / rg + ph,
        pr = f - Math.floor(f);
      y -= pr * rg;
      x += Math.sin(pr * 11 + ph * 40) * ex;
      z += Math.cos(pr * 7 + ph * 23) * ex * 0.6;
      al *= sstep(0, 0.05, pr) * (1 - sstep(0.92, 1, pr));
    } else if (kind === 14) {
      const hg = Math.max(0, y - ex);
      x += rg * hg * Math.sin(t * sp + ph);
      z += rg * 0.6 * hg * Math.sin(t * sp * 0.73 + ph * 1.7);
    } else if (kind === 11) {
      if (kraw & Airflow.packedFlag) {
        const displacement = Airflow.bend(t, ph, sp, rg);
        const { flex } = airAt(x,y,z);
        x += flex[0] * displacement;
        z += flex[1] * displacement;
      } else {
        const x0 = x;
        x += rg * Math.sin(t * sp + y * 1.3 + z * 0.9 + ph);
        y += rg * 0.6 * Math.sin(t * sp * 1.3 + x0 * 1.1 + ph);
      }
    }
    if (kraw & 512) {
      // born: not there till its time, then it grows to its size (as the page does it)
      const gw = world.grow || {};
      let gt = t * (gw.rate || 1);
      if (gw.loop > 0) gt -= Math.floor(gt / gw.loop) * gw.loop;
      const gs = Math.min(1, Math.max(0, (gt - ex) / (gw.fade || 0.5)));
      if (gs <= 0) al = 0;
      sc *= gs * (2 - gs);
    } else if (kraw & 1024) wet[i] = Math.min(1, Math.max(0, (t * ((world.grow || {}).rate || 1) - ex) / 2));
    X[i] = x;
    Y[i] = y;
    Z[i] = z;
    AL[i] = al;
    SC[i] = sc;
    depth[i] = V[2] * x + V[6] * y + V[10] * z + V[14];
  }
  if (sun) {
    const frames = sampleFrames(world, t), normals = [];
    const normalAt = i => normals[i] ?? (normals[i] = frames(i).normal ?? false);
    live = LiveSun.create(sun, world, { x: X, y: Y, z: Z, alpha: AL, scale: SC }, normalAt, cloudShadow, exposure?.light,
      { shadowArt: o.shadowArt, footprint: shadowFootprint });
  }
  const relight = relative && SplatRelighting.rows(world, relative, sampleFrames(world, t), { x: X, y: Y, z: Z, alpha: AL });
  let mn = Infinity;
  for (let i = 0; i < N; i++) if ((i < baseCount || AL[i] > 0) && depth[i] < mn) mn = depth[i];
  const mediumHorizon = aerial ? Math.max(horizon, -mn + R) : horizon;
  if (world.back) for (let j = 0; j < world.back.length; j++) depth[world.back[j]] = mn;
  const order = new Uint32Array(N);
  for (let i = 0; i < N; i++) order[i] = i;
  order.sort((a, b) => depth[a] - depth[b]);
  const mediaOptions = (water || aerial || cloudView) && atmosphereOptions();
  const hazeCoverage = effectRules?.ramps.get('fog')?.geometry && world.fog.max > 0 && new Float32Array(W * H);
  const rayMedia = mediaOptions && mediaSampler(volumes, water, rayAt, W, mediumHorizon, mediaOptions, air);
  const retainLayers = retainContributions || Boolean(rayMedia);
  const col = new Float32Array(W * H * 3),
    dep = new Float32Array(W * H),
    gls = new Float32Array(W * H);
  const skyCloud = skyPass && cloudView && [0, 0, 0, 1];
  for (let i = 0; i < W * H; i++) {
    const sampled = (showSky || captureSky) ? skySample(skyDirection(i), skyColor, cloudEye, false, cloudSignal) : null;
    const background = showSky ? sampled : bg;
    if (skyPass) {
      const q = environmentPasses.top(i) * 3, color = sampled ?? hex(0);
      if (skyCloud) {
        const { origin, direction, axial } = rayAt(i % W + .5, Math.floor(i / W) + .5);
        cloudView.trace(origin, direction, Math.max(0,eyeD-dist), horizon/axial, skyCloud, counters?.volume);
        for (let c = 0; c < 3; c++) skyPass[q + c] = skyCloud[c] + skyCloud[3] * color[c];
      } else skyPass.set(color,q);
    }
    if (backdropCloud) backdropCloud[i] = cloudSignal[0];
    const backdrop = rayMedia ? rayMedia.shade(i, horizon, background, false) : background;
    col[i * 3] = backdrop[0];
    col[i * 3 + 1] = backdrop[1];
    col[i * 3 + 2] = backdrop[2];
    if (captured && rayMedia) captured[i] = rayMedia.opacity();
    dep[i] = 1;
  }
  let drawn = 0;
  // colour per pixel (look.pixel): which dab is in front at each pixel, to be coloured afterwards from where the pixel lands on it
  const PIX =
      (o.pixel || (world.look && world.look.pixel)) && !o.raw && world.pix && world.pix.length >= baseCount * 8
        ? world.pix
        : null,
    win = PIX ? new Int32Array(W * H).fill(-1) : null;
  const materialStyles = o.raw ? null : world.materialPixelStyles;
  const artScale = o.artGridScale || 1;
  // Keep later translucent coats when the opaque receiver is recoloured per pixel.
  let surfaceOverlay = null;
  const bend = world.refract === undefined ? 6 : world.refract;
  const patternFlashes = flash && PIX ? new Map() : null;
  let contributions = retainLayers && PIX ? contributionLayers(col, captured, W, H, true, bend) : null;
  const stageMasks = stages?.surfaceMask || contribution && localConstraints?.some(policy => policy?.mask);
  const stagedFrames = stageMasks || anchoring && contribution ? sampleFrames(world, t) : null;
  const maskFrames = stagedFrames && new Map();
  function stageFrame(i) {
    if (i >= baseCount) return { normal: null };
    if (!maskFrames.has(i)) maskFrames.set(i, stagedFrames(i));
    return maskFrames.get(i);
  }
  function stageSample(i, point) {
    if (i >= baseCount) return { position: point, worldPosition: point, normal: null, time: t };
    const { rest, normal, localOffset } = stageFrame(i);
    const offset = localOffset(point[0] - X[i], point[1] - Y[i], point[2] - Z[i]);
    return { position: Array.from(rest, (n, k) => n + offset[k]), worldPosition: point, normal, time: t };
  }
  const renderMeta = world.renderMetadata;
  function fragmentRule(i) {
    if (!anchoring || !contribution) return null;
    const rule = stable.rules.length ? ArtStability.matching(stable, renderMeta?.objects?.[renderMeta.objectIds?.[i]],
      renderMeta?.materials?.[renderMeta.materialIds?.[i]]) : stable;
    return rule.dither === 'screen' ? null : rule;
  }
  function stagedMaterial(i, rules, rgb, sample) {
    const reference = world.materialAlbedo?.[i];
    return RenderStages.material(rules, rgb, reference ? reference - 1 : undefined, sample, undefined, lookPass?.stage);
  }
  let pixed = null,
    sprM = null;
  const defaultFine = o.fine || !!look.fine;
  const defaultCleanup = !!(o.clean || (look.clean && !tone?.preserveDots));
  const needsCleanupFlags = (styled || o.resolveDetailCleanup) && detailBudget?.affectsCleanup &&
    (defaultCleanup || detailBudget.enablesCleanup);
  const budgetAt = (needsCleanupFlags || detailBudget?.fineOn || detailBudget?.fineOff) ? detailBudget.bind(world) : null;
  const cleanupFlags = needsCleanupFlags && Uint8Array.from({length:baseCount}, (_, i) => DetailBudgets.flags(budgetAt(i)));
  const pixelBudgets = cleanupFlags && cleanupFlags.some(Boolean) ? new Uint8Array(W * H) : null;
  const FN =
      (defaultFine || detailBudget?.fineOn) && world.fine && world.fine.length >= baseCount * 12 ? world.fine : null,
    FPAL = FN ? world.pal.map((h, i) => hex(i)) : null;
  let deferred = sortedSurfaces ? new Map() : null, deferredCount = 0, orderFallback = false;
  const foreground = direction?.foreground;
  const contrastColor = (foreground || protection) && [0,0,0];
  const targetFog = (amount, rule) => rule && rule.fogScale !== 1 ? clamp(amount*rule.fogScale,0,1) : amount;
  function subjectColor(rule, r, g, b) {
    return ArtDirection.gradeContrast(r,g,b,rule.contrast-1,rule.pivot,contrastColor);
  }
  const foregroundDepth = z => z - (eyeD-dist);
  function composite(p, i, z, dn, a, pr, pg, pb, wd, emits, highlight, paletteId, detailParticle, projected, coat, glass, mark,
    opticalDepth = z, sprite, haze = 0, rule, reflected) {
    if(surfaceDepth&&!sprite?.surface&&opticalDepth>surfaceDepth[p]+1e-5)return;
    const p3 = p * 3, ia = 1 - a;
    if (counters) {
      counters.fragments++;
      if (!wd && a < 1) counters.translucentFragments++;
    }
    if (foreground && wd && (i < 0 ? !sprite?.emission : !(d[i*16+11] & 32)))
      [pr,pg,pb] = foreground(foregroundDepth(opticalDepth),pr,pg,pb,contrastColor);
    if (rule && rule.contrast !== 1 && (i < 0 ? !sprite?.emission : !(d[i*16+11] & 32)))
      [pr,pg,pb] = subjectColor(rule,pr,pg,pb);
    environmentPasses?.fragment?.(p, i, a, pr, pg, pb, reflected, wd && a > .5);
    if (rayMedia) [pr, pg, pb] = rayMedia.shade(p, opticalDepth, [pr, pg, pb], true, rule?.fogScale);
    if (retainLayers && glass && bend && !contributions) contributions = contributionLayers(col, captured, W, H, false, bend);
    if (contributions) contributions.before(p, pr, pg, pb, a, wd && a > .5, glass && !wd, dn);
    col[p3] = pr * a + col[p3] * ia;
    col[p3 + 1] = pg * a + col[p3 + 1] * ia;
    col[p3 + 2] = pb * a + col[p3 + 2] * ia;
    if (captured) captured[p] = a + captured[p] * ia;
    if (hazeCoverage) hazeCoverage[p] = haze*a + hazeCoverage[p]*ia;
    if (art) art.fragment(p, i, a, wd, z, emits, pr, pg, pb, sprite);
    if (lookPass) {
      const redraw = PIX?.[i * 8] && wd && a > .5 && !surface?.reveals(i);
      lookPass.fragment(p, a, redraw ? undefined : mark);
    }
    if (surfaceGlint && a > 0.5) surfaceGlint[p] = highlight > 0.22 || detailParticle;
    if (localAt && a > 0.5) localAt[p] = localSlot(i, paletteId, p);
    if (detail) {
      const q = (H - 1 - Math.floor(p / W)) * W + p % W;
      if (a > 0.5) detail[q] = 0;
      if (a > 0.24 && (detailParticle || (projected && highlight > 0.22))) detail[q] = 1;
    }
    if (surfaceOverlay) {
      const j = p * 4;
      if (wd && a > 0.5) surfaceOverlay.fill(0, j, j + 4);
      else if (!wd && (coat || surfaceOverlay[j + 3])) {
        surfaceOverlay[j] = pr * a + surfaceOverlay[j] * ia;
        surfaceOverlay[j + 1] = pg * a + surfaceOverlay[j + 1] * ia;
        surfaceOverlay[j + 2] = pb * a + surfaceOverlay[j + 2] * ia;
        surfaceOverlay[j + 3] = a + surfaceOverlay[j + 3] * ia;
      }
    }
    if (wd) {
      dep[p] = dn * a + dep[p] * ia;
      gls[p] *= ia;
      if (a > 0.5) {
        if (pixelBudgets) pixelBudgets[p] = (cleanupFlags[i] ?? 0) | DetailBudgets.OWNED;
        if (win) win[p] = surface?.reveals(i) ? -1 : i;
        if (axialDepth) axialDepth[p] = opticalDepth;
        if (fogScales || silhouetteMask) subjectPixel(p,rule);
      }
    } else if (glass) gls[p] = Math.min(1, gls[p] + a * 0.5);
    else if (win && !retainLayers && !coat && a > 0.5) win[p] = -1;
  }

  let spriteIndex=0;
  const normalizedDepth=z=>clamp((z-(eyeD-R))/(2*R),0,1);
  function spriteSample(sprite) {
    const {z,alpha,color,protection:rule}=sprite;
    const dn=normalizedDepth(z), fogMix=world.fog.max>0&&world.fog.start<1 ?
      targetFog(sstep(world.fog.start,1,dn)*world.fog.max*(exposure?.fog?.(...sprite.position)??1),rule) : 0;
    const rgb=color.map((value,c)=>value+(fog[c]-value)*fogMix);
    return [-1,z,dn,alpha,...rgb,alpha>=.5,false,0,0,false,false,alpha<.5,false,undefined,z,sprite,fogMix,rule];
  }
  function playSprites(through,queued) {
    while (spriteIndex<sprites.length && sprites[spriteIndex].z>=through) {
      const sprite=sprites[spriteIndex++], sample=spriteSample(sprite);
      if (queued) {
        if (!deferred.has(sprite.p)) deferred.set(sprite.p,[]);
        deferred.get(sprite.p).push({ sort:sprite.z,index:spriteIndex-sprites.length-1,center:sprite.z,sample });
      } else composite(sprite.p,...sample);
    }
  }
  function playFragments(sort,through=-Infinity) {
    if (sprites.length) playSprites(through,true);
    if (counters && deferred.size) counters.deferredFlushes++;
    for (const [p, layers] of deferred) {
      if (sort) layers.sort((a, b) => b.sort - a.sort || a.index - b.index);
      else if (sprites.length) layers.sort((a,b)=>b.center-a.center || a.index-b.index);
      for (const entry of layers) {
        const args = entry.sample;
        if (!sort) {
          args[1] = entry.center;
          args[2] = clamp((entry.center - (eyeD - R)) / (2 * R), 0, 1);
        }
        composite(p, ...args);
      }
    }
    deferred = null;
  }
  for (let n = 0; n < N; n++) {
    const i = order[n];
    if (!deferred && spriteIndex<sprites.length) playSprites(-depth[i],false);
    const q = i * 16,
      al = AL[i],
      x = X[i],
      y = Y[i],
      z = Z[i];
    if (al <= 0 || y < -30) continue;
    if (
      reflectionPlane &&
      (SceneOptics.planeDistance(reflectionPlane, x, y, z) <= reflectionPlane.bias ||
        (reflectionPlane.select && !reflectionPlane.select(i, x, y, z, world)))
    )
      continue;
    const cx = V[0] * x + V[4] * y + V[8] * z + V[12],
      cy = V[1] * x + V[5] * y + V[9] * z + V[13],
      cz = V[2] * x + V[6] * y + V[10] * z + V[14];
    if (cz > -near) continue;
    const kraw = Math.round(d[q + 11]),
      kind = kraw % 16,
      flags = Math.floor(kraw / 16),
      s2 = SC[i] * SC[i],
      pk = d[q + 7];
    const fieldParticle = i >= baseCount;
    const jStyle = i * 4, edgeStyle = materialStyles?.[jStyle] || 0;
    const styleKey = materialStyles?.[jStyle + 1] || 0;
    const staged = stages ? stages.at(fieldParticle ? -1 : i) : null;
    lookPass?.begin();
    const materialSample = staged?.material?.some(rule => rule.mask) ? stageSample(i, [x, y, z]) : undefined;
    const litMask = staged?.lit?.some(rule => rule.mask);
    const litNormal = litMask ? stageFrame(i).normal : null;
    const liveNormal = live?.normal(i), liveAlbedo = liveNormal && live.albedo(i);
    const lightSlot = i * 4, relit = relight?.[lightSlot + 3];
    let r = liveAlbedo ? liveAlbedo[0] : (pk % 256) / 255,
      g = liveAlbedo ? liveAlbedo[1] : (Math.floor(pk / 256) % 256) / 255,
      b = liveAlbedo ? liveAlbedo[2] : Math.floor(pk / 65536) / 255;
    if (staged?.material) [r, g, b] = stagedMaterial(i, staged.material, [r, g, b], materialSample);
    r += add[i];
    g += add[i];
    b += add[i];
    if (precipitation?.rows[i] && precipitation.lighting) {
      const [lr, lg, lb] = precipitation.lighting(x, y, z);
      r += lr;
      g += lg;
      b += lb;
    }
    if (wet[i]) {
      // wet: darker, and a little bluer, as the page does it
      r *= 1 - 0.42 * wet[i];
      g *= 1 - 0.38 * wet[i];
      b *= 1 - 0.3 * wet[i];
    }
    const hasSurface = surface?.has(i);
    const emits = art && (flags & 2) !== 0 && !world.renderMetadata?.muteEmission?.[i];
    const automatic = kind === LightSchedule.emissionKind && d[q + 15] === LightSchedule.emissionMarker;
    const sourceScale = automatic ? LightSchedule.emissionScale(dusk) : 1;
    const scheduled = lamps.length && !(flags & 22) && al >= 1 ? LightSchedule.transfer(lamps, x, y, z) : null;
    const dn = clamp((-cz - (eyeD - R)) / (2 * R), 0, 1);
    const iz = -1 / cz,
      tx = clamp(cx * iz, -limx, limx) / iz,
      ty = clamp(cy * iz, -limy, limy) / iz,
      j00 = ortho ? focal : focal * iz,
      j02 = ortho ? 0 : focal * tx * iz * iz,
      j12 = ortho ? 0 : focal * ty * iz * iz;
    const a0 = j00 * V[0] + j02 * V[2],
      a1 = j00 * V[4] + j02 * V[6],
      a2 = j00 * V[8] + j02 * V[10],
      b0 = j00 * V[1] + j12 * V[2],
      b1 = j00 * V[5] + j12 * V[6],
      b2 = j00 * V[9] + j12 * V[10];
    let c00 = d[q + 4] * s2,
      c01 = d[q + 5] * s2,
      c02 = d[q + 6] * s2,
      c11 = d[q + 8] * s2,
      c12 = d[q + 9] * s2,
      c22 = d[q + 10] * s2;
    if (kind === 2 && (precipitation?.rows[i] || (kraw & Airflow.packedFlag))) {
      // Profile and world precipitation rain are baked vertical. Rebuild its axial covariance along the current flow.
      const [wx, wz] = airAt(x,y,z).velocity, speed = d[q + 13];
      const length = Math.hypot(wx, speed, wz);
      const ax = wx / length, ay = -speed / length, az = wz / length;
      const cross = c00, stretch = c11 - cross;
      c00 = cross + stretch * ax * ax;
      c01 = stretch * ax * ay;
      c02 = stretch * ax * az;
      c11 = cross + stretch * ay * ay;
      c12 = stretch * ay * az;
      c22 = cross + stretch * az * az;
    }
    const u0 = c00 * a0 + c01 * a1 + c02 * a2,
      u1 = c01 * a0 + c11 * a1 + c12 * a2,
      u2 = c02 * a0 + c12 * a1 + c22 * a2,
      w0 = c00 * b0 + c01 * b1 + c02 * b2,
      w1 = c01 * b0 + c11 * b1 + c12 * b2,
      w2 = c02 * b0 + c12 * b1 + c22 * b2;
    const A = a0 * u0 + a1 * u1 + a2 * u2 + 0.15,
      Bq = b0 * u0 + b1 * u1 + b2 * u2,
      C = b0 * w0 + b1 * w1 + b2 * w2 + 0.15,
      det = A * C - Bq * Bq;
    if (det <= 0) continue;
    const k0 = C / det,
      k1 = -Bq / det,
      k2 = A / det,
      ex = Math.min(3 * Math.sqrt(A) + (integrateFootprint ? .25 : 0), 2048),
      ey = Math.min(3 * Math.sqrt(C) + (integrateFootprint ? .25 : 0), 2048);
    let sx = ortho ? ((cx / (oh * asp)) * 0.5 + 0.5) * W : ((((tp / asp) * cx) / -cz) * 0.5 + 0.5) * W,
      sy = ortho ? ((cy / oh) * 0.5 + 0.5) * H : (((tp * cy) / -cz) * 0.5 + 0.5) * H;
    if (kind === 1) {
      sx = Math.floor(sx) + 0.5;
      sy = Math.floor(sy) + 0.5;
    }
    if (centers) {
      centers[i * 2] = sx;
      centers[i * 2 + 1] = H - sy;
    }
    if (sx + ex < 0 || sx - ex > W || sy + ey < 0 || sy - ey > H) continue;
    let coverage = 1,
      glint = 0,
      centerPalette = 0;
    const planar = surface?.planar(i);
    const pixelSurface = PIX?.[i * 8] && !surface?.reveals(i) && (!planar || (al >= 1 && !(flags & 1)));
    const projected = surface?.projected(i);
    const reflectedSky = !skyOverlay && surface?.environment(i);
    const fragmentSurface = !pixelSurface && (planar || projected || reflectedSky || liveNormal && hasSurface);
    const ditherRule = fragmentRule(i);
    const detailParticle = fieldParticle || world.effectParticles?.some(({ first, count }) => i >= first && i < first + count);
    const centered = hasSurface && !pixelSurface && !fragmentSurface;
    if (centered) {
      [r, g, b, coverage, glint, centerPalette] = surface.shade(i, x, y, z, x, y, z, r, g, b, undefined, undefined,
        lookPass?.surface, centerReflection);
    }
    const splatFlash = flash && !(flags & 6) ? flash.light(x, y, z, liveNormal || (!fieldParticle ? geometrySample(i).normal : null)) : null;
    if (pixelSurface && splatFlash) patternFlashes.set(i, splatFlash);
    const coverGain = !liveNormal && !(flags & 6) && exposure?.light ?
      .24 + .76 * exposure.light(x,y,z) : 1;
    const rule = subject?.(i);
    const fogMix = !(flags & 2) && world.fog.max > 0 && world.fog.start < 1
      ? targetFog(sstep(world.fog.start,1,dn)*world.fog.max*(exposure?.fog?.(x,y,z)??1),rule) : 0;
    const reflectInRaster = (planar || reflectedSky) && !pixelSurface;
    const normal = fragmentSurface ? surface.surfaceNormal(i) : null;
    if (fogMix && !reflectInRaster && !staged?.lit && !liveNormal && !splatFlash && !relit && coverGain === 1) {
      r += (fog[0] - r) * fogMix;
      g += (fog[1] - g) * fogMix;
      b += (fog[2] - b) * fogMix;
    }
    const solid = al >= 1,
      writesDepth = solid && coverage === 1 && !(flags & 1),
      glass = (flags & 16) !== 0,
      x0 = Math.max(0, Math.floor(sx - ex)),
      x1 = Math.min(W - 1, Math.ceil(sx + ex)),
      y0 = Math.max(0, Math.floor(sy - ey)),
      y1 = Math.min(H - 1, Math.ceil(sy + ey));
    let glassLook;
    if (glass && glassIndex) {
      const target = glassIndex.row(i);
      if (!glassLooks.has(target)) glassLooks.set(target, optics.transform(target));
      glassLook = glassLooks.get(target);
    }
    const correction = paint && d[q + 14] === paint.marker;
    const coat = !retainLayers && PIX && (correction || fieldParticle ||
      hasSurface && (!writesDepth || reflectInRaster || surface.reveals(i)));
    if (coat && !surfaceOverlay) surfaceOverlay = new Float32Array(W * H * 4);
    if (audit && (r > 1 || g > 1 || b > 1)) audit.sample('splat', Math.max(0, r), Math.max(0, g), Math.max(0, b));
    r = Math.min(r, 1);
    g = Math.min(g, 1);
    b = Math.min(b, 1);
    drawn++;
    /* inked detail: a dab that carries a tile, and is still the colour it was baked, takes each pixel's colour from the tile, at the
       place on the surface the pixel looks at (the two half-axes of the tile, carried to the screen, and that turned inside out) */
    let fi = -1,
      i00 = 0,
      i01 = 0,
      i10 = 0,
      i11 = 0;
    if (!liveNormal && FN && FN[i * 12 + 11] && (budgetAt?.(i)?.fine ?? defaultFine) &&
        FN[i * 12 + 7] === pk && !add[i] && kind !== 5 && kind !== 12 && kind !== 13) {
      const f = i * 12,
        sc = SC[i],
        m00 = (a0 * FN[f + 4] + a1 * FN[f + 5] + a2 * FN[f + 6]) * sc,
        m01 = (a0 * FN[f + 8] + a1 * FN[f + 9] + a2 * FN[f + 10]) * sc,
        m10 = (b0 * FN[f + 4] + b1 * FN[f + 5] + b2 * FN[f + 6]) * sc,
        m11 = (b0 * FN[f + 8] + b1 * FN[f + 9] + b2 * FN[f + 10]) * sc,
        dt = m00 * m11 - m01 * m10;
      if (Math.abs(dt) > 1e-4 * (Math.abs(m00 * m11) + Math.abs(m01 * m10) + 1e-9)) {
        fi = f;
        i00 = m11 / dt;
        i01 = -m01 / dt;
        i10 = -m10 / dt;
        i11 = m00 / dt;
      }
    }
    const bakedCloud = cloudShadow && !liveNormal && !(flags & 6);
    const lowStyle = materialStyles?.[jStyle + 2], highStyle = materialStyles?.[jStyle + 3];
    const shadeMode = styleKey & 7;
    const shadeFraction = (styleKey - Math.floor(styleKey)) * 2;
    const shadeRaster = fi < 0 && (styleKey & MaterialPixelStyle.PAIR) && !pixelSurface &&
      !liveNormal && !staged?.material && !add[i] && !wet[i] && pk === (shadeFraction >= .5 ? highStyle : lowStyle);
    const wantsDepth = probe || deferred || aerial || cloudView;
    const probeNormal = !fieldParticle && (wantsDepth || bakedCloud) ? geometrySample(i).normal : null;
    const probeCenter = wantsDepth && [x, y, z];
    const probeReach = wantsDepth ? 3 * Math.sqrt(c00 + c11 + c22) : 0;
    const centerMark = lookPass && { ...lookPass.mark };
    for (let iy = y0; iy <= y1; iy++) {
      const dy = iy + 0.5 - sy;
      for (let ix = x0; ix <= x1; ix++) {
        const dx = ix + 0.5 - sx,
          pw = -0.5 * (k0 * dx * dx + k2 * dy * dy) - k1 * dx * dy;
        let a;
        if (integrateFootprint) a = footprint(dx, dy, k0, k1, k2, al, solid && !o.soft, edgeStyle);
        else a = ContributionRules.alpha(pw, al, solid && !o.soft, edgeStyle);
        if (a < ContributionRules.minimum) continue;
        lookPass?.begin(centerMark);
        let pr = r,
          pg = g,
          pb = b,
          alpha = coverage,
          highlight = glint,
          paletteId = centerPalette;
        if (shadeRaster) {
          const shade = shadeFraction > MaterialPixelStyle.thresholds(shadeMode,
            Math.floor(ix / artScale), Math.floor(iy / artScale)) ? highStyle : lowStyle;
          if (shade !== pk) {
            const visibility = reflectInRaster || staged?.lit || splatFlash || relit || coverGain < 1 ? 1 : 1 - fogMix;
            const gain = visibility / 255;
            pr += ((shade & 255) - (pk & 255)) * gain;
            pg += ((shade >> 8 & 255) - (pk >> 8 & 255)) * gain;
            pb += ((shade >> 16) - (pk >> 16)) * gain;
          }
        }
        if (fi >= 0) {
          const u = clamp(Math.floor((i00 * dx + i01 * dy) * 2 + 2), 0, 3),
            v = clamp(Math.floor((i10 * dx + i11 * dy) * 2 + 2), 0, 3),
            c = FPAL[Math.floor(FN[fi + v] / (u === 0 ? 1 : u === 1 ? 64 : u === 2 ? 4096 : 262144)) % 64];
          if (c) {
            pr = c[0];
            pg = c[1];
            pb = c[2];
            if (staged?.material) [pr, pg, pb] = stagedMaterial(i, staged.material, [pr, pg, pb], materialSample);
            if (!reflectInRaster && !staged?.lit && !splatFlash && !relit && coverGain === 1) {
              pr += (fog[0] - pr) * fogMix;
              pg += (fog[1] - pg) * fogMix;
              pb += (fog[2] - pb) * fogMix;
            }
          }
        }
        if (liveNormal) {
          const point = surfacePoint(rayAt(ix + .5, iy + .5), liveNormal, x, y, z, -cz, R);
          live.gains(i, ...point, sunGains);
          pr *= sunGains[0];
          pg *= sunGains[1];
          pb *= sunGains[2];
        }
        if (coverGain < 1) {
          pr *= coverGain;
          pg *= coverGain;
          pb *= coverGain;
        }
        if (automatic || scheduled) {
          const exposure = scheduled?.gain ?? sourceScale;
          const tint = scheduled?.color;
          pr = Math.min(1, pr * exposure + (tint?.[0] ?? 0));
          pg = Math.min(1, pg * exposure + (tint?.[1] ?? 0));
          pb = Math.min(1, pb * exposure + (tint?.[2] ?? 0));
        }
        let hit, reflected = centered ? centerReflection : undefined;
        if (fragmentSurface) {
          hit = surfacePoint(rayAt(ix + 0.5, iy + 0.5), normal, x, y, z, -cz, R);
          [pr, pg, pb, alpha, highlight, paletteId] = surface.shade(i, ...hit, x, y, z, pr, pg, pb, ix + 0.5, iy + 0.5,
            lookPass?.surface, fragmentReflection);
          reflected = fragmentReflection;
        }
        if (relit) {
          pr = Math.min(1, pr * relight[lightSlot]);
          pg = Math.min(1, pg * relight[lightSlot + 1]);
          pb = Math.min(1, pb * relight[lightSlot + 2]);
        }
        const scoped = contribution?.applies(i, paletteId);
        if (staged?.lit || scoped || glassLook) {
          let sample;
          if (litMask || (scoped && (ditherRule || contribution.masked(i, paletteId)))) {
            const sampleNormal = litNormal ?? stageFrame(i).normal;
            const point = hit ?? (sampleNormal ?
              surfacePoint(rayAt(ix + .5, iy + .5), sampleNormal, x, y, z, -cz, R) : [x, y, z]);
            sample = stageSample(i, point);
          }
          let rgb = [pr, pg, pb];
          if (scoped) {
            const [dx,dy] = ditherRule ? ArtStability.coordinates(ditherRule,
              ditherRule.dither === 'object' ? sample.position : sample.worldPosition, ix, H-1-iy) : [ix,H-1-iy];
            rgb = contribution.shade(i, paletteId, rgb, dx, dy, sample, highlight <= .22, lookPass?.palette);
          }
          if (staged?.lit) rgb = RenderStages.apply(staged.lit, rgb, sample, lookPass?.stage);
          [pr, pg, pb] = glassLook ? glassLook(rgb, lookPass?.optics) : rgb;
        }
        if (bakedCloud) {
          const point = hit ?? (probeNormal ?
            surfacePoint(rayAt(ix + .5, iy + .5), probeNormal, x, y, z, -cz, R) : [x, y, z]);
          const gain = CloudField.dim(cloudShadow(...point));
          pr *= gain;
          pg *= gain;
          pb *= gain;
        }
        if (splatFlash) {
          pr = Lightning.shade(pr, splatFlash[0]);
          pg = Lightning.shade(pg, splatFlash[1]);
          pb = Lightning.shade(pb, splatFlash[2]);
        }
        if (staged?.lit || (fragmentSurface && reflectInRaster) || liveNormal || splatFlash || relit || coverGain < 1) {
          pr += (fog[0] - pr) * fogMix;
          pg += (fog[1] - pg) * fogMix;
          pb += (fog[2] - pb) * fogMix;
        }
        a *= alpha;
        if (a < 0.004) continue;
        const p = iy * W + ix, wd = writesDepth && alpha === 1;
        const surfaceZ = wantsDepth ?
          sampledDepth(rayAt(ix + .5, iy + .5), probeNormal, probeCenter, -cz, probeReach) : -cz;
        if (probe) probe(p, i, -cz, surfaceZ, pr, pg, pb, a);
        if (deferred && deferredCount >= fragmentBudget) {
          playFragments(false,-cz);
          orderFallback = true;
        }
        if (deferred) {
          const entry = { sort: flags & 4 ? Infinity : surfaceZ, index: n, center: -cz,
            sample: [i, surfaceZ, clamp((surfaceZ - (eyeD - R)) / (2 * R), 0, 1), a, pr, pg, pb,
              wd, emits, highlight, paletteId, detailParticle, projected, coat, glass, lookPass && { ...lookPass.mark },
              aerial || cloudView ? surfaceZ : undefined, undefined, fogMix, rule, reflected?.slice()] };
          if (!deferred.has(p)) deferred.set(p, []);
          deferred.get(p).push(entry);
          deferredCount++;
          if (counters) counters.peakDeferredFragments = Math.max(counters.peakDeferredFragments,deferredCount);
        } else composite(p, i, -cz, dn, a, pr, pg, pb, wd, emits, highlight, paletteId, detailParticle, projected, coat, glass,
          lookPass?.mark, aerial || cloudView ? surfaceZ : undefined, undefined, fogMix, rule, reflected);
      }
    }
  }
  if (deferred) playFragments(true);
  else if (spriteIndex<sprites.length) playSprites(-Infinity,false);
  /* colour per pixel. Each pixel's line of sight is met with the plane of the dab in front there (the way its surface truly faces),
     and the pixel is coloured at that exact place: by its pattern, if it has one, or by its ramp. How lit it is is the mean over the
     pixels round it that lie on the same ramp and surface, so the edges between bands are drawn by the pixels, not by the dabs */
  if (PIX) {
    const PT = world.pixTex || [],
      RP = world.ramps || [],
      R00 = V[0],
      R01 = V[4],
      R02 = V[8],
      R10 = V[1],
      R11 = V[5],
      R12 = V[9],
      R20 = V[2],
      R21 = V[6],
      R22 = V[10],
      ex = -(R00 * V[12] + R10 * V[13] + R20 * V[14]),
      ey = -(R01 * V[12] + R11 * V[13] + R21 * V[14]),
      ez = -(R02 * V[12] + R12 * V[13] + R22 * V[14]),
      lit = new Float32Array(W * H),
      PALC = world.pal.map((h, k) => hex(k)),
      VW = world.pixView,
      shaper = o.lightShape === undefined ? !!(world.look && world.look.pixel) : !!o.lightShape;
    // (patterns drawn as little upright pictures need to know where the picture is looked at from, and which pixel is asked about)
    if (VW)
      Object.assign(VW, {
        on: true,
        t,
        R: [R00, R01, R02, R10, R11, R12, R20, R21, R22],
        e: [ex, ey, ez],
        tp,
        ortho,
        oh,
        asp,
        W,
        H
      });
    for (let y = 0; y < H; y++)
      for (let x = 0; x < W; x++) {
        const p = y * W + x,
          i = win[p];
        if (i < 0 || !PIX[i * 8]) continue;
        /* the light, smoothed over the same surface round the pixel: three by three; with the light shaper (o.lightShape, on for
           pixel-art dioramas, as on the page) also over seven by seven, only where the surface faces much the same way, so light and
           shade fall in a few big shapes with smooth edges. Near the edge of a surface the big window is cut in half and its mean
           would pull a lit rim toward the middle (shading that follows the outline): there the three by three is kept */
        let sum = 0,
          cnt = 0,
          s7 = 0,
          c7 = 0;
        const rad = shaper ? 3 : 1;
        for (let dy = -rad; dy <= rad; dy++)
          for (let dx = -rad; dx <= rad; dx++) {
            const X2 = x + dx,
              Y2 = y + dy;
            if (X2 < 0 || Y2 < 0 || X2 >= W || Y2 >= H) continue;
            const q = Y2 * W + X2,
              j = win[q];
            if (j < 0 || PIX[j * 8] !== PIX[i * 8]) continue;
            const dd = Math.abs(dep[q] - dep[p]);
            if (dx >= -1 && dx <= 1 && dy >= -1 && dy <= 1 && dd <= 0.01) {
              sum += PIX[j * 8 + 1];
              cnt++;
            }
            if (
              shaper &&
              ((dx + dy) & 1) === 0 && // (the wide window every other pixel, a checkerboard, as on the page)
              dd <= 0.03 &&
              PIX[i * 8 + 3] * PIX[j * 8 + 3] + PIX[i * 8 + 4] * PIX[j * 8 + 4] + PIX[i * 8 + 5] * PIX[j * 8 + 5] >= 0.8
            ) {
              s7 += PIX[j * 8 + 1];
              c7++;
            }
          }
        lit[p] = sum / cnt;
        if (shaper && c7) {
          const k = Math.min(1, Math.max(0, (c7 / 25 - 0.5) / 0.35)),
            sm = k * k * (3 - 2 * k);
          lit[p] += (s7 / c7 - lit[p]) * sm;
        }
      }
    pixed = new Uint8Array(W * H);
    const bounceTints = live?.hasBounce && new Float32Array(W * H * 3);
    const HX = new Float32Array(W * H),
      HY = new Float32Array(W * H),
      HZ = new Float32Array(W * H);
    const key = new Float64Array(W * H).fill(NaN),
      cB = new Int16Array(W * H).fill(-1),
      cBelow = new Int16Array(W * H),
      cAbove = new Int16Array(W * H),
      cLeft = new Int16Array(W * H),
      CELL = world.pixCell || { body: 0, below: 0, above: 0, left: 0 };
    for (let y = 0; y < H; y++)
      for (let x = 0; x < W; x++) {
        const p = y * W + x,
          i = win[p];
        if (i < 0 || !PIX[i * 8]) continue;
        const f = i * 8,
          ramp = RP[PIX[f] - 1];
        let nx = PIX[f + 3], ny = PIX[f + 4], nz = PIX[f + 5];
        if (surface?.has(i)) [nx, ny, nz] = surface.normalAt(i, [nx, ny, nz]);
        const vx = (((x + 0.5) / W) * 2 - 1) * (ortho ? oh * asp : asp / tp),
          vy = (((y + 0.5) / H) * 2 - 1) * (ortho ? oh : 1 / tp),
          // (orthographic: each ray starts at its own point on the picture's plane, and all run straight ahead)
          ox0 = ortho ? ex + R00 * vx + R10 * vy : ex,
          oy0 = ortho ? ey + R01 * vx + R11 * vy : ey,
          oz0 = ortho ? ez + R02 * vx + R12 * vy : ez,
          dxw = ortho ? -R20 : R00 * vx + R10 * vy - R20,
          dyw = ortho ? -R21 : R01 * vx + R11 * vy - R21,
          dzw = ortho ? -R22 : R02 * vx + R12 * vy - R22,
          den = nx * dxw + ny * dyw + nz * dzw,
          sd = Math.abs(den) > 1e-6 ? (nx * (X[i] - ox0) + ny * (Y[i] - oy0) + nz * (Z[i] - oz0)) / den : 0,
          px = sd ? ox0 + dxw * sd : X[i],
          py = sd ? oy0 + dyw * sd : Y[i],
          pz = sd ? oz0 + dzw * sd : Z[i],
          pat = PIX[f + 2],
          ev = pat ? PT[pat - 1] : null,
          /* (how big a screen pixel is, for the patterns' detail: one for the whole picture, from the camera's distance alone, as on the
             page; from each surface's slant it would differ from pixel to pixel and change as the view turns, and details flicker) */
          fp = (dist * 2) / (tp * H);
        if (VW) ((VW.x = x), (VW.y = y));
        HX[p] = px;
        HY[p] = py;
        HZ[p] = pz;
        if (live?.normal(i)) {
          if (bounceTints) {
            lit[p] = live.rampLevel(i, px, py, pz, sunGains);
            bounceTints.set(sunGains, p * 3);
          } else lit[p] = live.level(i, px, py, pz);
        }
        const styleKey = materialStyles?.[i * 4 + 1];
        if (styleKey) lit[p] = MaterialPixelStyle.pixelShade(lit[p], styleKey,
          Math.floor(x / artScale), Math.floor(y / artScale), ramp?.length || 1);
        if (ev && ev.cell) {
          key[p] = ev.cell(
            px,
            py,
            pz,
            ny,
            lit[p],
            nx,
            nz,
            null,
            fp,
            ramp,
            world.pixUnfold ? world.pixUnfold(PIX[f + 6], PIX[f + 7]) : null
          );
          cB[p] = CELL.body;
          cBelow[p] = CELL.below;
          cAbove[p] = CELL.above;
          cLeft[p] = CELL.left;
        } else
          cB[p] = ev
            ? ev.tex(
                px,
                py,
                pz,
                ny,
                lit[p],
                nx,
                nz,
                null,
                fp,
                ramp,
                world.pixUnfold ? world.pixUnfold(PIX[f + 6], PIX[f + 7]) : null
              )
            : ramp
              ? ramp[clamp(Math.floor(lit[p] * ramp.length), 0, ramp.length - 1)]
              : -1;
      }
    if (VW) VW.on = false;
    // a pixel at the edge of its cell takes that edge's colour: lower edge first, then the side, then the upper edge
    const kAt = (x, y) => (x < 0 || y < 0 || x >= W || y >= H ? NaN : key[y * W + x]),
      differs = (k, q) => q === q && q !== k;
    /* outlines (look.outline), as on the page: a pixel at the edge of a thing, where it meets another material, the background, or
       something well behind it, and is the nearer of the two, takes a darker step of its own ramp (two by default), so each thing is
       ringed in its own darker colour and a lit edge in a softer one. A material with line: false (clouds, water) has none */
    const OLo = ink || o.artInkActive ? null : look.outline,
      OL = OLo ? (OLo === true ? {} : OLo) : null,
      olK = OL && OL.k !== undefined ? OL.k : 2,
      olEps = OL ? (OL.eps === undefined ? 0.6 : OL.eps) / (world.detail || 12) / (2 * R) : 0,
      olGap = OL ? (OL.gap === undefined ? 0.3 : OL.gap) / (2 * R) : 0,
      OFF = world.rampOff || [],
      N4 = [
        [-1, 0],
        [1, 0],
        [0, -1],
        [0, 1]
      ];
    for (let y = 0; y < H; y++)
      for (let x = 0; x < W; x++) {
        const p = y * W + x,
          i = win[p];
        let ci = cB[p];
        if (ci < 0) continue;
        const k = key[p];
        if (k === k) {
          if (differs(k, kAt(x, y - 1))) ci = cBelow[p];
          else if (differs(k, kAt(x - 1, y))) ci = cLeft[p];
          else if (differs(k, kAt(x, y + 1))) ci = cAbove[p];
        }
        if (OL) {
          const rid = PIX[i * 8];
          if (!OFF[rid - 1]) {
            let edge = false,
              sky = false;
            for (const [dx, dy] of N4) {
              const X2 = x + dx,
                Y2 = y + dy;
              if (X2 < 0 || Y2 < 0 || X2 >= W || Y2 >= H) continue;
              const q = Y2 * W + X2,
                dd = dep[q] - dep[p];
              if (dd <= olEps) continue;
              const j = win[q];
              if (j < 0 || PIX[j * 8] !== rid || dd > olGap) {
                edge = true;
                sky = dep[q] >= 0.995;
                break;
              }
            }
            /* (and a crease: where its own surface turns sharply, as the edge of a block of stone or a crate, the lit side of the turn
                takes a step lighter and the other a step darker, a bevel two pixels wide. Not in leaves or grass) */
            let crease = 0;
            const pk = PIX[i * 8 + 2] ? (world.pats[PIX[i * 8 + 2] - 1] || {}).kind : null;
            if (!edge && OL.crease !== false && pk !== 'leaves' && pk !== 'turf')
              for (const [dx, dy] of N4) {
                const X2 = x + dx,
                  Y2 = y + dy;
                if (X2 < 0 || Y2 < 0 || X2 >= W || Y2 >= H) continue;
                const q = Y2 * W + X2,
                  j = win[q];
                if (j < 0 || PIX[j * 8] !== rid || Math.abs(dep[q] - dep[p]) > olGap) continue;
                if (
                  PIX[i * 8 + 3] * PIX[j * 8 + 3] + PIX[i * 8 + 4] * PIX[j * 8 + 4] + PIX[i * 8 + 5] * PIX[j * 8 + 5] >
                  0.7
                )
                  continue;
                crease = PIX[i * 8 + 1] >= PIX[j * 8 + 1] ? 1 : -1;
                break;
              }
            if (edge || crease) {
              const ramp = RP[rid - 1],
                b = ramp.indexOf(ci);
              /* (a rim in the light takes a softer line than one in shade, or none against another thing, as on the page: so the outline
                 does not darken a shape all round, whichever way it faces, which is pillow shading) */
              const k2 = b * 2 >= ramp.length ? (sky ? 1 : 0) : olK;
              if (b >= 0) ci = ramp[Math.max(0, Math.min(ramp.length - 1, edge ? b - k2 : b + crease))];
            }
          }
          pixed[p] = 1;
        }
        if (!PALC[ci]) continue;
        const fieldParticle = i >= baseCount;
    const staged = stages ? stages.at(fieldParticle ? -1 : i) : null;
        lookPass?.begin();
        const masked = staged?.material?.some(rule => rule.mask) || staged?.lit?.some(rule => rule.mask);
        const sample = masked ? stageSample(i, [HX[p], HY[p], HZ[p]]) : undefined;
        let base = staged?.material ? stagedMaterial(i, staged.material, PALC[ci], sample) : PALC[ci];
        if (exposure?.light && !live?.normal(i) && !(Math.round(d[i*16+11]) & (32 | 64))) {
          const gain = .24 + .76 * exposure.light(HX[p],HY[p],HZ[p]);
          if (gain < 1) base = base.map(value => value * gain);
        }
        if (bounceTints && live.normal(i)) base = base.map((value, channel) => value * bounceTints[p * 3 + channel]);
        const finishedSurface = surface?.has(i);
        const c = finishedSurface ? surface.shade(i, HX[p], HY[p], HZ[p], X[i], Y[i], Z[i], ...base, x + 0.5, y + 0.5,
          lookPass?.surface, fragmentReflection) : base;
        if (finishedSurface && reflectPass) environmentPasses.pattern(p,fragmentReflection);
        let rgb = c;
        const lightSlot = i * 4;
        if (relight?.[lightSlot + 3]) rgb = c.slice(0, 3).map((value, channel) =>
          Math.min(1, value * relight[lightSlot + channel]));
        if (contribution?.applies(i, c[5])) {
          const rule = fragmentRule(i);
          const site = sample ?? (rule || contribution.masked(i, c[5]) ? stageSample(i, [HX[p], HY[p], HZ[p]]) : undefined);
          const [dx,dy] = rule ? ArtStability.coordinates(rule, rule.dither === 'object' ? site.position : site.worldPosition, x, H-1-y) :
            [x,H-1-y];
          rgb = contribution.shade(i, c[5], rgb, dx, dy, site, !(c[4] > .22), lookPass?.palette);
        }
        let lit = staged?.lit ? RenderStages.apply(staged.lit, rgb, sample, lookPass?.stage) : rgb;
        if (cloudShadow && !live?.normal(i) && !(Math.round(d[i * 16 + 11]) & (32 | 64))) {
          const gain = CloudField.dim(cloudShadow(HX[p], HY[p], HZ[p]));
          lit = [lit[0] * gain, lit[1] * gain, lit[2] * gain];
        }
        const patternFlash = patternFlashes?.get(i);
        if (patternFlash) lit = lit.slice(0, 3).map((value, c) => Lightning.shade(value, patternFlash[c]));
        if (foreground && !(d[i*16+11] & 32))
          lit = foreground(foregroundDepth(eyeD-R+dep[p]*2*R),lit[0],lit[1],lit[2],contrastColor);
        if (lookPass) lookPass.fragment(p, retainLayers ? contributions.weight(p) : 1 - (surfaceOverlay?.[p * 4 + 3] || 0),
          lookPass.mark, true);
        const protectionRule = subject?.(i);
        if (protectionRule && protectionRule.contrast !== 1 && !(d[i*16+11] & 32))
          lit = subjectColor(protectionRule,lit[0],lit[1],lit[2]);
        const kf = world.fog.max > 0 && world.fog.start < 1
          ? targetFog(sstep(world.fog.start,1,dep[p])*world.fog.max*(exposure?.fog?.(HX[p],HY[p],HZ[p])??1),protectionRule) : 0;
        if (surfaceGlint) surfaceGlint[p] = c[4] > 0.22;
        if (retainLayers) {
          if (localAt) localAt[p] = localSlot(i, c[5], p);
          const shaded = [0, 1, 2].map(channel => lit[channel] + (fog[channel] - lit[channel]) * kf);
          contributions.replacePattern(p, rayMedia ? rayMedia.shade(p, axialDepth[p], shaded, true, protectionRule?.fogScale) : shaded);
          if (detail && surface?.projected(i) && c[4] > 0.22) detail[(H - 1 - y) * W + x] = 1;
          continue;
        }
        if ((surfaceOverlay?.[p * 4 + 3] || 0) < 0.5) {
          if (localAt) localAt[p] = localSlot(i, c[5], p);
          if (detail && surface?.projected(i) && c[4] > 0.22) detail[(H - 1 - y) * W + x] = 1;
        }
        col[p * 3] = lit[0] + (fog[0] - lit[0]) * kf;
        col[p * 3 + 1] = lit[1] + (fog[1] - lit[1]) * kf;
        col[p * 3 + 2] = lit[2] + (fog[2] - lit[2]) * kf;
        if (captured) {
          const coat = surfaceOverlay?.[p * 4 + 3] || 0;
          const baseAlpha = (captured[p] - coat) / Math.max(1e-6, 1 - coat);
          for (let channel = 0; channel < 3; channel++) col[p * 3 + channel] *= clamp(baseAlpha, 0, 1);
        }
        if (surfaceOverlay) {
          const j = p * 4,
            through = 1 - surfaceOverlay[j + 3];
          for (let channel = 0; channel < 3; channel++) {
            col[p * 3 + channel] = surfaceOverlay[j + channel] + col[p * 3 + channel] * through;
          }
        }
      }
    // (o.pick: where on the surface each pixel lies, for the paint-over tool; rows from the bottom, as everything here)
    if (o.pick) Object.assign(o.pick, { W, H, X: HX, Y: HY, Z: HZ, win, PIX, dep, camera: paintView });
    /* edge sprites (K.pixel.edge; o.edges, on by default), as on the page: little pixel pictures stood on points pinned to the
       surface (K.pixel.anchors; the world's pixAnchors), each moving with the dab it stands on, turned the way its surface faces
       on the screen (up, to a side, down), and shown only past the edge of that surface: over the background, over something well
       behind, or over anything that is not its own surface; never over what is nearer. So as the view turns, a sprite whose point
       goes round behind an edge sinks behind it a pixel at a time. Where two cover a pixel the nearer wins */
    const AN = o.edges !== false && world.pixAnchors ? world.pixAnchors(world) : null;
    if (AN && AN.n) {
      const EP = (world.pats || []).map(pt => pt && pt.edge),
        OLe = (world.look || {}).outline,
        eGap = (OLe && OLe !== true && OLe.gap !== undefined ? OLe.gap : 0.3) / (2 * R),
        fpe = (dist * 2) / (tp * H),
        keep = Math.min(1, (0.25 * (1 / (world.detail || 12))) / fpe),
        tol = 3 * fpe + 0.02,
        OD = [
          [0, 1],
          [1, 0],
          [-1, 0],
          [0, -1]
        ],
        TD = [
          [1, 0],
          [0, -1],
          [0, 1],
          [1, 0]
        ],
        A = AN.data,
        sprD = new Float32Array(W * H).fill(9),
        sprC = new Int16Array(W * H).fill(-1),
        sprOwner = art || foreground || subject || relight ? new Int32Array(W * H) : null;
      for (let a = 0; a < AN.n; a++) {
        const q0 = a * 12,
          ed = EP[A[q0 + 8]];
        if (!ed || A[q0 + 7] >= keep * (ed.share === undefined ? 0.7 : ed.share)) continue;
        const i = A[q0 + 3],
          ax = A[q0] + X[i] - d[i * 16],
          ay = A[q0 + 1] + Y[i] - d[i * 16 + 1],
          az = A[q0 + 2] + Z[i] - d[i * 16 + 2],
          nx = A[q0 + 4],
          ny = A[q0 + 5],
          nz = A[q0 + 6],
          cx = V[0] * ax + V[4] * ay + V[8] * az + V[12],
          cy = V[1] * ax + V[5] * ay + V[9] * az + V[13],
          cz = V[2] * ax + V[6] * ay + V[10] * az + V[14];
        if (cz > -near) continue;
        const sx = ortho ? ((cx / (oh * asp)) * 0.5 + 0.5) * W : ((((tp / asp) * cx) / -cz) * 0.5 + 0.5) * W,
          sy = ortho ? ((cy / oh) * 0.5 + 0.5) * H : (((tp * cy) / -cz) * 0.5 + 0.5) * H,
          px1 = Math.floor(sx),
          py1 = Math.floor(sy);
        if (px1 < -8 || py1 < -8 || px1 > W + 8 || py1 > H + 8) continue;
        // which way the surface faces on the screen; one that faces the eye has no way out, and stands nothing
        const vx = V[0] * nx + V[4] * ny + V[8] * nz,
          vy = V[1] * nx + V[5] * ny + V[9] * nz,
          vz = V[2] * nx + V[6] * ny + V[10] * nz,
          cl = Math.hypot(cx, cy, cz),
          facing = ortho ? -vz : (vx * cx + vy * cy + vz * cz) / cl;
        if (Math.abs(facing) > 0.95) continue;
        let dx = ortho ? vx : -vx * cz + cx * vz,
          dy = ortho ? vy : -vy * cz + cy * vz;
        const dl = Math.hypot(dx, dy);
        if (dl < 1e-12) continue;
        dx /= dl;
        dy /= dl;
        const cat = dy > 0.38 ? 0 : dy < -0.38 ? 3 : dx > 0 ? 1 : 2,
          list = cat === 0 ? ed.up : cat === 3 ? ed.down : ed.side;
        if (!list.length) continue;
        const sp = list[Math.min(list.length - 1, Math.floor(A[q0 + 11] * list.length))],
          ramp = RP[A[q0 + 9]],
          b = clamp(Math.floor(A[q0 + 10] * ramp.length), 0, ramp.length - 1),
          dA = (-cz - (eyeD - R)) / (2 * R),
          [odx, ody] = OD[cat],
          [tdx, tdy] = TD[cat];
        for (let r = 0; r < sp.h; r++)
          for (let c = 0; c < sp.w; c++) {
            const v = sp.cells[r * sp.w + c];
            if (!v) continue;
            const ou = r + 1 - sp.sink,
              al = c - sp.ax,
              X2 = px1 + odx * ou + tdx * al,
              Y2 = py1 + ody * ou + tdy * al;
            if (X2 < 0 || Y2 < 0 || X2 >= W || Y2 >= H) continue;
            const q = Y2 * W + X2,
              dp = dep[q];
            if (dA >= sprD[q]) continue;
            let show;
            if (dp >= 0.995) show = true;
            else if (dp < dA - 0.008)
              show = false; // (something nearer stands here)
            else if (r < sp.sink)
              show = true; // (the root rows lie over the thing itself)
            else {
              const j = win[q];
              show =
                j < 0 || !PIX[j * 8]
                  ? dp - dA > eGap
                  : Math.abs((HX[q] - ax) * nx + (HY[q] - ay) * ny + (HZ[q] - az) * nz) > tol;
            }
            if (!show) continue;
            sprD[q] = dA;
            if (sprOwner) sprOwner[q] = i;
            sprC[q] = v >= 100 ? v - 100 : ramp[clamp(b + v - 8, 0, ramp.length - 1)];
          }
      }
      sprM = new Uint8Array(W * H);
      for (let q = 0; q < W * H; q++) {
        if (sprC[q] < 0 || !PALC[sprC[q]]) continue;
        const depth = eyeD - R + sprD[q] * 2 * R;
        let c = PALC[sprC[q]];
        const lightSlot = sprOwner?.[q] * 4;
        if (relight?.[lightSlot + 3]) c = c.map((value, channel) => Math.min(1, value * relight[lightSlot + channel]));
        if (cloudShadow) {
          const { origin, direction, axial } = rayAt(q % W + .5, Math.floor(q / W) + .5);
          const distance = depth / axial;
          const gain = CloudField.dim(cloudShadow(origin[0] + direction[0] * distance,
            origin[1] + direction[1] * distance, origin[2] + direction[2] * distance));
          c = c.map(value => value * gain);
        }
        if (foreground && !(d[sprOwner?.[q]*16+11] & 32))
          c = foreground(foregroundDepth(depth),c[0],c[1],c[2],contrastColor);
        const rule = subject?.(sprOwner[q]);
        if (rule && rule.contrast !== 1 && !(d[sprOwner[q]*16+11] & 32))
          c = subjectColor(rule,c[0],c[1],c[2]);
        if (rayMedia) c = rayMedia.shade(q, depth, c, true, rule?.fogScale);
        if (fogScales || silhouetteMask) subjectPixel(q,rule);
        col[q * 3] = c[0];
        col[q * 3 + 1] = c[1];
        col[q * 3 + 2] = c[2];
        if (transparent) captured[q] = 1;
        if (axialDepth) axialDepth[q] = eyeD - R + sprD[q] * 2 * R;
        if (art) art.sprite(q, sprOwner[q], eyeD - R + sprD[q] * 2 * R);
        if (counters) counters.fragments++;
        environmentPasses?.fragment?.(q, -1, 1, 0, 0, 0);
        if (hazeCoverage) hazeCoverage[q] = 0;
        lookPass?.fragment(q, 1);
        if (localAt) localAt[q] = 0;
        if (overlay) overlay.slots[q] = 0;
        if (detail) detail[(H - 1 - Math.floor(q / W)) * W + q % W] = 0;
        dep[q] = sprD[q]; // (so the clean-up sees it as part of the thing, and leaves it as drawn)
        pixed[q] = 1;
        sprM[q] = 1;
      }
    }
  }
  contributions?.refract(gls, dep);
  let atmosphere, volumeStats = mediaOptions?.stats ? rayMedia.stats : undefined;
  const captureFog = ink?.ramps.has('fog') || o.captureFog;
  const effectMedia = trackMedia && axialDepth && new Float32Array(W * H * 3);
  if (rayMedia && (captureFog || effectMedia || fogPass)) {
    const fog = captureFog && new Float32Array(W * H);
    for (let p = 0; p < W*H; p++) {
      const depth = axialDepth[p], covered = Number.isFinite(depth);
      rayMedia.shade(p, covered ? depth : horizon, bg, covered, fogScales?.[p]);
      const q = (H - 1 - Math.floor(p / W)) * W + p % W;
      if (fog) fog[q] = rayMedia.opacity();
      if (fogPass) fogPass[q] = rayMedia.fogThrough();
      if (effectMedia) rayMedia.contributions(effectMedia, q * 3);
    }
    atmosphere = { fog };
  } else if (axialDepth && !rayMedia) {
    const quality = atmosphereOptions();
    atmosphere = applyAtmosphere(volumes, col, axialDepth, rayAt, W, H, horizon, quality, t, quality.media,
      captureFog || effectMedia || transparent || fogPass, o.volumeHistory,
      o.volumeHistory && [W, H, focal, ortho, o.volumeLocalLights, o.volumeLocalShadows, ...V].join('/'), fogScales);
    if (effectMedia) for (let p = 0; p < W*H; p++) {
      effectMedia[p*3] = atmosphere.fog[p];
      effectMedia[p*3+2] = 1-atmosphere.fog[p];
    }
    if (fogPass) for (let p = 0; p < W*H; p++) fogPass[p] = 1 - atmosphere.fog[p];
    if (quality.stats) volumeStats = atmosphere.stats;
  }
  const effectSignals = effectRules && { rules: effectRules, sky: showSky && !!sky, backdropCloud, media: effectMedia, haze: hazeCoverage };
  let passes = art?.finalize(world, t, { x: X, y: Y, z: Z, rayAt, span: R,
    detail, sprM, surfaceGlint, centers, motionFrom, motionReference });
  if (o.captureCoverage) {
    if (reflectionTint && passes?.emission) ArtEffects.tintReflection(col, captured, passes.emission, W, H, reflectionTint, t);
    const reflectionLook = reflectionPlane && optics?.transform(TargetSelectors.medium(reflectionPlane.id, 'reflection', reflectionPlane.tags));
    if (reflectionLook) for (let p = 0; p < captured.length; p++) {
      const coverage = captured[p];
      if (coverage <= 1e-6) continue;
      const q = p * 3;
      const rgb = reflectionLook([col[q] / coverage, col[q + 1] / coverage, col[q + 2] / coverage]);
      for (let channel = 0; channel < 3; channel++) col[q + channel] = rgb[channel] * coverage;
    }
    return { w: W, h: H, rgb: col, coverage: captured };
  }
  const alpha = transparent ? new Uint8Array(W * H) : null;
  if (alpha) {
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const p = y * W + x, q = (H - 1 - y) * W + x;
      const fog = rayMedia ? 0 : atmosphere?.fog?.[q] || 0;
      const a = fog + (1 - fog) * captured[p];
      alpha[q] = Math.round(clamp(a, 0, 1) * 255);
      if (a > 1e-6) for (let c = 0; c < 3; c++) col[p * 3 + c] /= a;
    }
  }
  const masks = overlay && createMaskResolve(world, { w: W, h: H, time: t, x: X, y: Y, z: Z, depth, rayAt, span: R },
    overlay, localConstraints, o.maskGrade ?? (!tone && grade), lookPass?.local);
  if (environmentPasses) passes = { w:W, h:H, ...passes, ...environmentPasses.passes };
  if (lookPass) passes = lookPass.finish(passes);
  if (o.samples) {
    // (the picture the contour look takes its insides from is worked on first, as the page does: glass bends it, contact shade darkens it)
    let c2 = col;
    if (o.worked) {
      const aoK = world.ao ? (world.ao.k === undefined ? 0.5 : world.ao.k) : 0,
        aoR = world.ao ? (world.ao.range || 0.6) / (2 * R) : 1,
        at = (x, y) => clamp(y, 0, H - 1) * W + clamp(x, 0, W - 1),
        TAPS = [2, 0, -2, 0, 0, 2, 0, -2, 1, 1, -1, 1, 1, -1, -1, -1];
      c2 = new Float32Array(col.length);
      for (let y = 0; y < H; y++)
        for (let x = 0; x < W; x++) {
          const p = y * W + x,
            gx = gls[at(x + 1, y)] - gls[at(x - 1, y)],
            gy = gls[at(x, y + 1)] - gls[at(x, y - 1)];
          let q = p;
          if (!retainLayers && gls[p] + Math.abs(gx) + Math.abs(gy) > 0) q = at(x + Math.round(gx * bend), y + Math.round(gy * bend));
          let k = 1;
          if (aoK > 0) {
            let occ = 0;
            for (let i = 0; i < 16; i += 2) {
              const dd = (dep[p] - dep[at(x + TAPS[i], y + TAPS[i + 1])]) / aoR;
              if (dd > 0.08 && dd < 3) occ += Math.min(1, dd);
            }
            k = 1 - aoK * Math.min(1, occ / 4);
          }
          c2[p * 3] = col[q * 3] * k;
          c2[p * 3 + 1] = col[q * 3 + 1] * k;
          c2[p * 3 + 2] = col[q * 3 + 2] * k;
        }
    }
    if (masks || lookPass && (localAt || o.previewPalette)) for (let p = 0; p < W * H; p++) {
      const policy = localConstraints?.[(localAt?.[p] || 0) - 1];
      if (lookPass && o.previewPalette && (!localAt?.[p] || policy?.source === 'graded')) lookPass.local(p, o.previewPalette);
      if (lookPass && policy) lookPass.local(p, policy);
      if (!masks) continue;
      if (!overlay.slots[p]) continue;
      const q = p * 3, x = p % W, y = H - 1 - Math.floor(p / W);
      const [dx, dy] = anchoring ? ArtStability.ditherCoordinates(stable, passes, y * W + x, x, y) : [x, y];
      masks.record(p, c2[q], c2[q + 1], c2[q + 2], dx, dy);
    }
    if (audit) for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 3;
      audit.pixel('interior', (H - 1 - y) * W + x, c2[i], c2[i + 1], c2[i + 2]);
    }
    return {
      w: W, h: H, color: Uint8Array.from(c2, v => Math.round(clamp(v, 0, 1) * 255)), depth: dep, drawn,
      ...(o.resolveDetailCleanup && pixelBudgets && { cleanDetail: cleanPixels }),
      ...(localAt && { localAt, localPalettes, localConstraints }), ...(detail && { detail }), ...(passes && { passes }), ...(motionReference && { motionReference }),
      ...(masks && { masked: masks.output }),
      ...(atmosphere?.fog && { fog: atmosphere.fog }), ...(silhouetteMask && {silhouetteMask}), ...(effectSignals && { effectSignals }), ...(volumeStats && { volumeStats }), ...(alpha && { alpha }), ...(orderFallback && { orderFallback })
    };
  }
  // the second pass: an outline where the picture steps back sharply, a little ordered noise, then the nearest colour of the palette
  const effectColor = effectSignals && new Uint8Array(W * H * 3);
  const out = new Uint8Array(W * H * 3),
    np = world.pal.length,
    pal = [];
  for (let i = 0; i < np; i++) pal.push(hex(i));
  const outlineIndex = world.outline?.c ?? 0,
    exactLine = colorGrade && Number.isInteger(outlineIndex) && outlineIndex >= 0 && outlineIndex < np,
    edge = world.outline && world.outline.edge ? world.outline.edge / (2 * R) : 0,
    line = hex(world.outline ? world.outline.c : 0),
    dith = (o.dither === undefined ? 0.35 : o.dither) * 0.3 * world.dither,
    localOutput = localAt && PixelLook.outputPalettes(tone?.palette || evaluatedPalette || world.pal, localPalettes),
    local = localAt && { constraints: localConstraints, palettes: localPalettes, output: localOutput, scene: pal, grade: !tone && grade },
    use = new Uint32Array(retainContributions ? 0 : localOutput?.packed.length ?? (tone ? tone.palette.length : np)),
    ln = look.lines ? (look.lines === true ? {} : look.lines) : null,
    lines = !ink && !!ln,
    lineGap = ln ? (ln.gap || 0.3) / (2 * R) : 1,
    lineK = ln && ln.k !== undefined ? ln.k : 0.55,
    lineLit = ln && ln.lit !== undefined ? ln.lit : 1.15;
  const D = (x, y) => dep[clamp(y, 0, H - 1) * W + clamp(x, 0, W - 1)],
    G = (x, y) => gls[clamp(y, 0, H - 1) * W + clamp(x, 0, W - 1)];
  // (as in the page: glass bends what is behind it, by how its own thickness changes across the picture; and, where a diorama asks for it,
  //  a pixel with nearer things close round it is shaded, so that what moves still sits in its own shadow)
  const aoK = world.ao ? (world.ao.k === undefined ? 0.5 : world.ao.k) : 0,
    aoR = world.ao ? (world.ao.range || 0.6) / (2 * R) : 1,
    AOT = [
      [2, 0],
      [-2, 0],
      [0, 2],
      [0, -2],
      [1, 1],
      [-1, 1],
      [1, -1],
      [-1, -1]
    ];
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const p = y * W + x;
      let r = col[p * 3],
        g = col[p * 3 + 1],
        b = col[p * 3 + 2];
      const yo = H - 1 - y,
        q = (yo * W + x) * 3;
      if (!o.raw && !retainLayers) {
        const gx = G(x + 1, y) - G(x - 1, y),
          gy = G(x, y + 1) - G(x, y - 1);
        if (gls[p] + Math.abs(gx) + Math.abs(gy) > 0) {
          const p2 = (clamp(y + Math.round(gy * bend), 0, H - 1) * W + clamp(x + Math.round(gx * bend), 0, W - 1)) * 3;
          r = col[p2];
          g = col[p2 + 1];
          b = col[p2 + 2];
        }
      }
      if (aoK > 0 && !o.raw) {
        const dc0 = dep[p];
        let occ = 0;
        for (const tq of AOT) {
          const dd = (dc0 - D(x + tq[0], y + tq[1])) / aoR;
          if (dd > 0.08 && dd < 3) occ += Math.min(1, dd);
        }
        const k = 1 - aoK * Math.min(1, occ / 4);
        r *= k;
        g *= k;
        b *= k;
      }
      if (o.raw) {
        if (audit) audit.pixel('composite', q / 3, r, g, b);
        out[q] = Math.round(clamp(r, 0, 1) * 255);
        out[q + 1] = Math.round(clamp(g, 0, 1) * 255);
        out[q + 2] = Math.round(clamp(b, 0, 1) * 255);
        continue;
      }
      const dc = dep[p],
        dm = dc - Math.max(2 * dc - D(x - 1, y) - D(x + 1, y), 2 * dc - D(x, y + 1) - D(x, y - 1));
      // part lines (look.lines), as on the page: the near side of a break in depth, darker, or lighter toward the light
      // (not where an outline was already worked out per pixel)
      if (lines && !(pixed && pixed[p])) {
        const dl = D(x - 1, y),
          dr = D(x + 1, y),
          du = D(x, y + 1),
          dd = D(x, y - 1),
          sx = dl + dr - 2 * dc,
          sy = du + dd - 2 * dc;
        if (Math.max(sx, sy) > lineGap) {
          const k = (sx >= sy ? dl > dr : du > dd) ? lineLit : lineK;
          r *= k;
          g *= k;
          b *= k;
        }
      }
      const outlined = !ink && edge > 0 && dc - dm > edge;
      if (outlined) {
        r = line[0];
        g = line[1];
        b = line[2];
      }
      if (effectColor) {
        const at = p*3;
        effectColor[at] = Math.round(clamp(r, 0, 1) * 255);
        effectColor[at+1] = Math.round(clamp(g, 0, 1) * 255);
        effectColor[at+2] = Math.round(clamp(b, 0, 1) * 255);
      }
      if (retainContributions) {
        if (audit) audit.pixel('composite', q / 3, r, g, b);
        out[q] = Math.round(clamp(r, 0, 1) * 255);
        out[q + 1] = Math.round(clamp(g, 0, 1) * 255);
        out[q + 2] = Math.round(clamp(b, 0, 1) * 255);
        continue;
      }
      const localId = outlined ? 0 : localAt?.[p];
      const localCoordinates = tone || localId || masks;
      const screenY = localCoordinates ? yo : y;
      const [ditherX, ditherY] = anchoring ?
        ArtStability.ditherCoordinates(stable, passes, yo*W+x, x, screenY) : [x,screenY];
      if (lookPass && globalPaletteMark && (!localId || localConstraints?.[localId - 1]?.source === 'graded'))
        lookPass.local(p, globalPaletteMark);
      if (lookPass && localId && localConstraints?.[localId - 1]) lookPass.local(p, localConstraints[localId - 1]);
      if (masks && !outlined) masks.record(p, r, g, b, ditherX, ditherY);
      if (tone || localId) {
        const index = localId ? PixelLook.localIndex(local, localId, [r, g, b], ditherX, ditherY, !surfaceGlint?.[p]) :
          PixelLook.toneIndex(tone, r, g, b, ditherX, ditherY);
        const color = (localOutput?.packed || tone.palette)[index];
        use[index]++;
        out[q] = color >> 16;
        out[q + 1] = (color >> 8) & 255;
        out[q + 2] = color & 255;
        continue;
      }
      if (!outlined && !surfaceGlint?.[p]) {
        const [dx,dy] = masks && screenY !== y ? (anchoring ?
          ArtStability.ditherCoordinates(stable, passes, yo*W+x, x, y) : [x,y]) : [ditherX,ditherY];
        const th = PixelLook.bayerRank(dx, dy) - 0.5;
        r = clamp(r + th * dith, 0, 1);
        g = clamp(g + th * dith, 0, 1);
        b = clamp(b + th * dith, 0, 1);
      }
      let bd = 1e9,
        bi = 0;
      if (exactLine && outlined) bi = outlineIndex;
      else for (let i = 0; i < np; i++) {
        const e = pal[i],
          dr = r - e[0],
          dg = g - e[1],
          db = b - e[2],
          dd = dr * dr * 0.3 + dg * dg * 0.55 + db * db * 0.15;
        if (dd < bd) {
          bd = dd;
          bi = i;
        }
      }
      use[bi]++;
      const h = world.pal[bi];
      if (grade) {
        out[q] = Math.round(grade[bi * 3] * 255);
        out[q + 1] = Math.round(grade[bi * 3 + 1] * 255);
        out[q + 2] = Math.round(grade[bi * 3 + 2] * 255);
      } else {
        out[q] = (h >> 16) & 255;
        out[q + 1] = (h >> 8) & 255;
        out[q + 2] = h & 255;
      }
    }
  /* pixel clean-up (an option, or a diorama's look.clean), as on the page: a speck (a pixel with no like neighbour of the eight round
     it, or one of a pair that has no other) takes the colour most of its eight neighbours share, if at least three share it, they are
     on the same surface, and it is not much brighter or darker than they are (a glint, an eye or a flower is kept). */
  if ((defaultCleanup || pixelBudgets) && !o.raw) cleanPixels(out);
  function cleanPixels(out, globalCleanup = defaultCleanup) {
    const src = out.slice(),
      keep = look.clean && look.clean.keep !== undefined ? look.clean.keep : 0.3,
      at = (x, y) => (clamp(y, 0, H - 1) * W + clamp(x, 0, W - 1)) * 3,
      same = (a, b) => src[a] === src[b] && src[a + 1] === src[b + 1] && src[a + 2] === src[b + 2],
      lum = a => (src[a] * 0.3 + src[a + 1] * 0.55 + src[a + 2] * 0.15) / 255,
      atDepth = a => {
        const i = a / 3;
        return (H - 1 - Math.floor(i / W)) * W + (i % W);
      },
      depA = a => dep[atDepth(a)],
      N8 = [
        [-1, 0],
        [1, 0],
        [0, -1],
        [0, 1],
        [-1, -1],
        [1, -1],
        [-1, 1],
        [1, 1]
      ];
    const likes = (x, y, q) => {
      let n = 0,
        one = null;
      for (const [dx, dy] of N8)
        if (same(q, at(x + dx, y + dy))) {
          n++;
          one = [x + dx, y + dy];
        }
      return [n, one];
    };
    const empty = (x, y) => depA(at(x, y)) >= 0.995,
      N4 = N8.slice(0, 4),
      lineClean = o.lineClean === undefined ? !!(world.look && world.look.pixel) : !!o.lineClean;
    for (let y = 0; y < H; y++)
      for (let x = 0; x < W; x++) {
        const q = at(x, y);
        const pixel = (H - 1 - y) * W + x;
        const flags = pixelBudgets?.[pixel] ?? 0;
        if (pixelBudgets && !DetailBudgets.cleans(flags, globalCleanup)) continue;
        if (localConstraints?.[(localAt?.[pixel] || 0) - 1] || (alpha && alpha[q / 3] < 128) || sprM?.[pixel] ||
            surfaceGlint?.[pixel] || detail?.[q / 3] || ArtStability.protectedPixel(stable, passes, q / 3)) continue;
        // outlines, as on the page: a notch is filled from what is round it, a bump against the background taken off
        const e0 = empty(x, y),
          en = N4.filter(([dx, dy]) => empty(x + dx, y + dy)).length;
        if (pixelBudgets) {
          if ((e0 || !(flags & DetailBudgets.OWNED)) &&
              N4.some(([dx, dy]) => DetailBudgets.protects(pixelBudgets[atDepth(at(x + dx, y + dy))]))) continue;
          if (!e0 && en > 0 && DetailBudgets.protects(flags)) continue;
        }
        if (e0 && en <= 1) {
          let kb = 0,
            best = -1;
          for (const [dx, dy] of N4) {
            if (empty(x + dx, y + dy)) continue;
            const a = at(x + dx, y + dy);
            let k = 0;
            for (const [ex, ey] of N4) if (same(a, at(x + ex, y + ey))) k++;
            if (k > kb) ((kb = k), (best = a));
          }
          if (best >= 0) {
            out[q] = src[best];
            out[q + 1] = src[best + 1];
            out[q + 2] = src[best + 2];
            continue;
          }
        }
        if (!e0 && en >= 3) {
          const [dx, dy] = N4.find(([ex, ey]) => empty(x + ex, y + ey)),
            a = at(x + dx, y + dy);
          out[q] = src[a];
          out[q + 1] = src[a + 1];
          out[q + 2] = src[a + 2];
          continue;
        }
        /* the line cleaner (an option, on for pixel-art dioramas, as on the page): a one-pixel kink in a straight edge between two
           colours taken off, and on a dark line one pixel thick the double at the inside corner of a step given the colour beside it */
        if (lineClean) {
          let to = -1;
          for (const [dx, dy] of N8.slice(0, 4)) {
            const ex = dy,
              ey = dx,
              X = at(x + dx, y + dy);
            if (same(X, q) || !same(at(x + ex, y + ey), X) || !same(at(x - ex, y - ey), X)) continue;
            if (
              same(at(x - dx, y - dy), q) &&
              same(at(x - dx + ex, y - dy + ey), q) &&
              same(at(x - dx - ex, y - dy - ey), q)
            ) {
              to = X;
              break;
            }
          }
          if (to < 0) {
            const lum = a => src[a] * 0.3 + src[a + 1] * 0.55 + src[a + 2] * 0.15,
              l0 = lum(q);
            for (const [gx, gy] of N8.slice(4)) {
              if (
                !same(at(x + gx, y), q) ||
                !same(at(x, y + gy), q) ||
                same(at(x + gx, y + gy), q) ||
                same(at(x - gx, y), q) ||
                same(at(x, y - gy), q)
              )
                continue;
              const goH = same(at(x + 2 * gx, y), q) || same(at(x + 2 * gx, y - gy), q),
                goV = same(at(x, y + 2 * gy), q) || same(at(x - gx, y + 2 * gy), q),
                a = at(x - gx, y),
                b = at(x, y - gy);
              if (goH && goV && lum(a) > l0 + 15 && lum(b) > l0 + 15) {
                to = same(a, b) ? a : at(x - gx, y - gy);
                break;
              }
            }
          }
          if (to >= 0) {
            out[q] = src[to];
            out[q + 1] = src[to + 1];
            out[q + 2] = src[to + 2];
            continue;
          }
        }
        const [n, one] = likes(x, y, q);
        if (!(n === 0 || (n === 1 && likes(one[0], one[1], q)[0] === 1))) continue;
        const nb = N8.map(([dx, dy]) => at(x + dx, y + dy));
        let kb = 0,
          best = -1;
        for (const a of nb) {
          if (same(a, q)) continue;
          let k = 0;
          for (const b of nb) if (same(a, b)) k++;
          if (k > kb) ((kb = k), (best = a));
        }
        if (kb < 3 || Math.abs(depA(q) - depA(best)) > 0.03 || Math.abs(lum(q) - lum(best)) >= keep) continue;
        out[q] = src[best];
        out[q + 1] = src[best + 1];
        out[q + 2] = src[best + 2];
      }
  }
  applyMasks(out, masks?.output);
  return finishLook({
    w: W, h: H, px, rgb: out, drawn, use,
    ...((localOutput || tone || evaluatedPalette) && { palette: localOutput?.packed || tone?.palette || evaluatedPalette }),
    ...(detail && { detail }), ...(motionReference && { motionReference }),
    ...(volumeStats && { volumeStats }), ...(silhouetteMask && {silhouetteMask}), ...(o.captureFog && atmosphere?.fog && { fog: atmosphere.fog }),
    ...(alpha && { alpha }), ...(orderFallback && { orderFallback })
  }, passes, atmosphere?.fog, effectSignals, effectColor);
}
// make every art pixel k screen pixels wide, the way the page shows it
function upscale(img, k) {
  const W = img.w * k,
    H = img.h * k,
    out = new Uint8Array(W * H * 3), alpha = img.alpha && new Uint8Array(W * H);
  for (let y = 0; y < H; y++) {
    const sy = (y / k) | 0;
    for (let x = 0; x < W; x++) {
      const s = (sy * img.w + ((x / k) | 0)) * 3,
        q = (y * W + x) * 3;
      out[q] = img.rgb[s];
      out[q + 1] = img.rgb[s + 1];
      out[q + 2] = img.rgb[s + 2];
      if (alpha) alpha[q / 3] = img.alpha[s / 3];
    }
  }
  return { w: W, h: H, rgb: out, ...(alpha && {alpha}) };
}
// several pictures in a grid, each with a small label in its corner
const FONT = {
  0: '111101101101111',
  1: '010110010010111',
  2: '111001111100111',
  3: '111001111001111',
  4: '101101111001001',
  5: '111100111001111',
  6: '111100111101111',
  7: '111001001001001',
  8: '111101111101111',
  9: '111101111001111',
  '.': '000000000000010',
  '-': '000000111000000',
  s: '000111110011111',
  ' ': '000000000000000',
  y: '101101111001111',
  t: '010111010010011'
};
function label(img, x0, y0, text, k) {
  k = k || 2;
  for (let c = 0; c < text.length; c++) {
    const g = FONT[text[c]] || FONT[' '];
    for (let j = 0; j < 15; j++)
      if (g[j] === '1')
        for (let a = 0; a < k; a++)
          for (let b = 0; b < k; b++) {
            const x = x0 + (c * 4 + (j % 3)) * k + a,
              y = y0 + ((j / 3) | 0) * k + b;
            if (x >= 0 && x < img.w && y >= 0 && y < img.h) {
              const q = (y * img.w + x) * 3;
              img.rgb[q] = 255;
              img.rgb[q + 1] = 255;
              img.rgb[q + 2] = 255;
              if (img.alpha) img.alpha[q / 3] = 255;
            }
          }
  }
}
function grid(imgs, cols, labels) {
  const w = imgs[0].w,
    h = imgs[0].h,
    rows = Math.ceil(imgs.length / cols),
    out = { w: w * cols, h: h * rows, rgb: new Uint8Array(w * cols * h * rows * 3) };
  if (imgs.some(image => image.alpha)) out.alpha = new Uint8Array(out.w * out.h);
  imgs.forEach((im, n) => {
    const ox = (n % cols) * w,
      oy = ((n / cols) | 0) * h;
    for (let y = 0; y < h; y++) {
      const start = (oy + y) * out.w + ox;
      out.rgb.set(im.rgb.subarray(y * w * 3, (y + 1) * w * 3), start * 3);
      if (im.alpha) out.alpha.set(im.alpha.subarray(y * w, (y + 1) * w), start);
      else out.alpha?.fill(255, start, start + w);
    }
    if (labels) label(out, ox + 6, oy + 6, labels[n]);
  });
  return out;
}
module.exports = { render, upscale, grid, label, viewMatrix, FOV };

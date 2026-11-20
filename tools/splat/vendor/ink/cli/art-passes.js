const ArtPasses = require('../src/art-passes.js');
const { surfacePoint } = require('./scene-optics.js');

const SplatFrames = require('../src/splat-frames.js');
let matrices;
function sampleFrames(world, time) {
  if (!matrices && (world.anim?.rig || world.anim?.bones)) matrices = require('../index.js').load().KIT.M;
  return SplatFrames.create(world, time, matrices);
}

function createArtPasses(request, w, h) {
  const selected = new Set(ArtPasses.select(request));
  if (!selected.size) return null;
  const size = w * h;
  const coverage = selected.has('coverage') ? new Float32Array(size) : null;
  const emission = selected.has('emission') ? new Float32Array(size * 3) : null;
  const emissionOwner = selected.has('emissionMotion') ? new Int32Array(size).fill(-1) : null;
  const emissionDepth = selected.has('emissionDepth') || emissionOwner ? new Float32Array(size).fill(Infinity) : null;
  const needsOwner = [...selected].some(channel => !['emission', 'emissionDepth', 'emissionMotion', 'coverage', 'protected'].includes(channel));
  const owner = needsOwner ? new Int32Array(size).fill(-1) : null;
  const depth = needsOwner ? new Float32Array(size).fill(Infinity) : null;

  let atlasOwners;
  function fragment(p, i, a, solid, z, emits, r, g, b, atlas) {
    const tint=atlas?.emission;
    emits ||= Boolean(tint);
    if (coverage) coverage[p] = a + coverage[p] * (1 - a);
    if (emission) {
      const j = p * 3;
      if (emits || emission[j] || emission[j + 1] || emission[j + 2]) {
        emission[j] = ArtPasses.over(tint ? tint[0] : emits ? r : 0, emission[j], a);
        emission[j + 1] = ArtPasses.over(tint ? tint[1] : emits ? g : 0, emission[j + 1], a);
        emission[j + 2] = ArtPasses.over(tint ? tint[2] : emits ? b : 0, emission[j + 2], a);
      }
    }
    if (emissionDepth && a > .03) {
      if (emits && z <= emissionDepth[p]) {
        emissionDepth[p] = z;
        if (emissionOwner) emissionOwner[p] = i;
      } else if (!emits && solid && a > .97 && z <= emissionDepth[p]) {
        emissionDepth[p] = Infinity;
        if (emissionOwner) emissionOwner[p] = -1;
      }
    }
    if (owner && ArtPasses.ownsSurface(a, solid, z, depth[p])) {
      owner[p] = i;
      depth[p] = z;
      if (atlas) (atlasOwners??=new Map()).set(p,atlas);
      else atlasOwners?.delete(p);
    }
  }

  function sprite(p, i, z) {
    atlasOwners?.delete(p);
    if (coverage) coverage[p] = 1;
    if (emission) emission.fill(0, p * 3, p * 3 + 3);
    if (emissionDepth) emissionDepth[p] = Infinity;
    if (emissionOwner) emissionOwner[p] = -1;
    if (owner) {
      owner[p] = i;
      depth[p] = z;
    }
  }

  function finalize(world, time, geometry) {
    const topDown = (values, components) => {
      const out = new values.constructor(values.length);
      const row = w * components;
      for (let y = 0; y < h; y++) out.set(values.subarray(y * row, (y + 1) * row), (h - 1 - y) * row);
      return out;
    };
    const result = { w, h };
    if (coverage) result.coverage = topDown(coverage, 1);
    if (emission) result.emission = topDown(emission, 3);
    if (selected.has('emissionDepth')) result.emissionDepth = topDown(emissionDepth, 1);
    if (selected.has('protected')) {
      const { detail, sprM, surfaceGlint } = geometry;
      result.protected = new Uint8Array(size);
      for (let p = 0; p < size; p++) {
        const bottom = (h - 1 - Math.floor(p / w)) * w + p % w;
        result.protected[p] = Number(Boolean(detail?.[p] || sprM?.[bottom] || surfaceGlint?.[bottom]));
      }
    }
    if (selected.has('depth')) result.depth = topDown(depth, 1);
    const normalOut = selected.has('normal') ? new Float32Array(size * 3) : null;
    const positionOut = selected.has('position') ? new Float32Array(size * 3) : null;
    const objectOut = selected.has('objectPosition') ? new Float32Array(size * 3) : null;
    if (normalOut || positionOut || objectOut) {
      const frames = new Map(), sample = sampleFrames(world, time);
      for (let p = 0; p < size; p++) {
        const atlas=atlasOwners?.get(p);
        if (atlas) {
          if (normalOut && atlas.normal) normalOut.set(atlas.normal,p*3);
          positionOut?.set(atlas.position,p*3);
          objectOut?.set(atlas.objectPosition,p*3);
          if (atlas.patternPosition) (result.ditherRest ??= new Map()).set((h-1-Math.floor(p/w))*w+p%w,atlas.patternPosition);
          continue;
        }
        const i = owner[p];
        if (i < 0) continue;
        if (!frames.has(i)) frames.set(i, sample(i));
        const frame = frames.get(i);
        if (normalOut && frame.normal) normalOut.set(frame.normal, p * 3);
        if (!positionOut && !objectOut) continue;
        const x = geometry.x[i], y = geometry.y[i], z = geometry.z[i];
        const hit = frame.normal ?
          surfacePoint(geometry.rayAt(p % w + .5, Math.floor(p / w) + .5), frame.normal, x, y, z, depth[p], geometry.span) :
          [x, y, z];
        if (positionOut) positionOut.set(hit, p * 3);
        if (objectOut) {
          const offset = frame.localOffset(hit[0] - x, hit[1] - y, hit[2] - z);
          for (let k = 0; k < 3; k++) objectOut[p * 3 + k] = (frame.rest[k] ?? 0) + offset[k];
        }
      }
      if (normalOut) result.normal = topDown(normalOut, 3);
      if (positionOut) result.position = topDown(positionOut, 3);
      if (objectOut) result.objectPosition = topDown(objectOut, 3);
    }
    for (const [channel, ids] of [['motion', owner], ['emissionMotion', emissionOwner]]) {
      if (!selected.has(channel)) continue;
      const vectors = new Float32Array(size * 2);
      const previous = geometry.motionFrom, current = geometry.motionReference;
      if (previous?.w === w && previous.h === h && previous.centers.length === geometry.centers.length) {
        for (let p = 0; p < size; p++) {
          const i = ids[p] * 2;
          if (i < 0 || !Number.isFinite(previous.centers[i]) || !Number.isFinite(geometry.centers[i])) continue;
          const ownerId = ids[p];
          if (current?.birthIds && ownerId >= current.baseCount &&
              (current.splatSource !== previous.splatSource || current.emitterSource !== previous.emitterSource ||
                current.baseCount !== previous.baseCount ||
                current.birthIds[ownerId] !== previous.birthIds?.[ownerId])) continue;
          vectors[p * 2] = geometry.centers[i] - previous.centers[i];
          vectors[p * 2 + 1] = geometry.centers[i + 1] - previous.centers[i + 1];
        }
      }
      result[channel] = topDown(vectors, 2);
    }
    if (selected.has('splatId')) result.splatId = topDown(Uint32Array.from(owner, i => i + 1), 1);
    for (const [channel, names] of [['objectId', 'objects'], ['materialId', 'materials']]) {
      if (!selected.has(channel)) continue;
      const ids = world.renderMetadata?.[channel + 's'];
      result[channel] = topDown(Uint32Array.from(owner, i => ids?.[i] || 0), 1);
      result[names] = world.renderMetadata?.[names] || [null];
    }
    return result;
  }

  return { fragment, sprite, finalize };
}

module.exports = { createArtPasses, sampleFrames };

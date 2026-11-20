// ink-studio: sculpt with signed distance, bake to pixel-art gaussian splats, and look at the result without a browser.
// The sources are plain scripts (they are concatenated into a web page as they stand), so this file offers them three ways:
//   files()   the library's source files, in the order they must be loaded
//   bundle()  those files as one piece of text, to put in a page or in front of your own scripts
//   load()    the same compiled for Node, with the demo dioramas: { makeBuilder, makeSculpt, KIT, SCENES, ... }
const fs = require('fs'),
  path = require('path'),
  { randomUUID } = require('crypto');
const KIT_DIR = path.join(__dirname, 'src', 'kit'),
  read = f => fs.readFileSync(f, 'utf8').replace(/\nif \(typeof module[^\n]*\n?$/, '\n');
const files = () =>
  [
    'src/frame-budget.js', 'src/ink-veil.js', 'src/textured-surface.js', 'src/sprite-surface.js', 'src/atlas-sprites.js', 'src/target-selectors.js', 'src/splat-provenance.js',
    'src/art-passes.js', 'src/art-direction.js', 'src/art-ink.js', 'src/art-effects.js', 'src/art-stability.js', 'src/material-pixel-style.js',
    'src/color-space.js', 'src/paint-corrections.js', 'src/color-curves.js', 'src/color-lut.js', 'src/color-stack.js', 'src/pixel-look.js', 'src/reflection-plane.js', 'src/airflow.js', 'src/wind-field.js', 'src/light-schedule.js',
    'src/route-visibility.js', 'src/sample-coverage.js', 'src/contribution-rules.js', 'src/sample-visibility.js', 'src/swept-disc.js', 'src/splat-order.js', 'src/splat-codec.js', 'src/ripple-field.js',
    'src/volume-field.js', 'src/geometry-density.js', 'src/volume-cutouts.js', 'src/cloud-recipes.js', 'src/cloud-detail.js', 'src/cloud-field.js', 'src/lightning.js', 'src/volume-light.js', 'src/celestial-tracks.js', 'src/sky-environment.js', 'src/environment-frame.js', 'src/weather-front.js', 'src/weather-binding.js', 'src/scene-optics.js', 'src/scene-exposure.js', 'src/splat-effects.js',
    'src/look-inputs.js', 'src/render-stages.js', 'src/effect-palettes.js', 'src/silhouette-protection.js', 'src/detail-budgets.js', 'src/shadow-art.js', 'src/horizon-bands.js', 'src/surface-look.js', 'src/splat-frames.js', 'src/splat-relighting.js', 'src/builder.js', 'src/sculpt.js'
  ]
    .map(f => path.join(__dirname, f))
    .concat(
      fs
        .readdirSync(KIT_DIR)
        .filter(f => f.endsWith('.js'))
        .sort()
        .map(f => path.join(KIT_DIR, f))
    );
const demoFiles = () => [path.join(__dirname, 'demos', 'labscenes.js')];
// the names the bundle defines at top level (add them to your own module.exports)
const EXPORTS =
  'makeBuilder, makeSculpt, basis, flame, motes, pondMat, lilies, courses, PALETTES, PAL_HEX, KIT, FrameBudget, InkVeil, TexturedSurface, SpriteSurface, TargetSelectors, SplatProvenance, ColorSpace, PaintCorrections, ColorCurves, ColorLUT, ColorStack, PixelLook, LookInputs, RenderStages, ContributionRules, SurfaceLook, SceneOptics, SceneExposure, SkyEnvironment, EnvironmentFrame, CelestialTracks, CloudField, Lightning, VOX, SplatEffects, ArtPasses, ArtDirection, ArtInk, EffectPalettes, SilhouetteProtection, DetailBudgets, HorizonBands, ArtStability, ArtEffects, VolumeField, VolumeLight';
module.exports = {
  files,
  demoFiles,
  EXPORTS,
  version: require('./package.json').version,
  bundle: () => files().map(read).join('\n'),
  // the seven built-in demo dioramas. They push onto an array called SCENES, which must already exist
  demos: () => demoFiles().map(read).join('\n'),
  // refuse-to-build check: code written after a // comment on the same line never runs. Returns the offending lines
  lint: require('./scripts/lint.js'),
  // a mesh file from disk, by its ending: .obj (with the .mtl beside it), .gltf (with its .bin files), .glb
  readMesh(file, { attributes = false } = {}) {
    const K = module.exports.load().KIT,
      ext = path.extname(file).toLowerCase(),
      dir = path.dirname(file);
    if (ext === '.obj') {
      const text = fs.readFileSync(file, 'utf8'),
        m = /^mtllib\s+(.+)$/m.exec(text),
        mf = m && path.join(dir, m[1].trim());
      const mtl = mf && fs.existsSync(mf) ? fs.readFileSync(mf, 'utf8') : null;
      const mesh = K.mesh.obj(text, mtl, { attributes });
      if (attributes && mtl && mesh.uvs) {
        let name;
        const textures = new Map();
        for (const raw of mtl.split('\n')) {
          const entry = /^(newmtl|map_Kd)\s+(.+)$/.exec(raw.trim());
          if (!entry) continue;
          if (entry[1] === 'newmtl') name = entry[2];
          else if (name && !entry[2].startsWith('-')) {
            const image = path.resolve(path.dirname(mf), entry[2].replace(/^["']|["']$/g, ''));
            const mimeType = { '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg' }[path.extname(image).toLowerCase()];
            if (mimeType && fs.existsSync(image)) textures.set(name, { bytes: fs.readFileSync(image), mimeType });
          }
        }
        mesh.mats = mesh.mats.map(m => ({ ...m, texture: textures.get(m.name) }));
      }
      return mesh;
    }
    if (ext === '.glb') return K.mesh.glb(fs.readFileSync(file));
    if (ext === '.gltf') {
      const g = JSON.parse(fs.readFileSync(file, 'utf8'));
      return K.mesh.gltf(
        g,
        (g.buffers || []).map(b =>
          b.uri && !b.uri.startsWith('data:') ? fs.readFileSync(path.join(dir, decodeURIComponent(b.uri))) : null
        )
      );
    }
    throw new Error('do not know how to read ' + ext + ' (obj, gltf and glb are read)');
  },
  async readAsset(file, options = {}) {
    if (path.extname(file).toLowerCase() !== '.glb') throw Error('Portable asset import expects a GLB file');
    const decodeImage = options.decodeImage || ((bytes, mime) => {
      if (mime !== 'image/png') throw Error('Supply decodeImage to import embedded JPEG images');
      const image = require('./cli/png.js').raster(Buffer.from(bytes));
      return { width: image.w, height: image.h,
        pixels: image.max === 255 ? image.data : Uint8Array.from(image.data, v => Math.round(v * 255 / image.max)) };
    });
    return module.exports.load().KIT.authoring.assetMeshes.importGLB(
      new Uint8Array(fs.readFileSync(file)), { ...options, decodeImage });
  },
  exportGlb: require('./cli/export-glb.js'),
  render: require('./cli/render.js').render,
  inspectEnvironment: require('./cli/environment-inspector.js').inspectEnvironment,
  silhouetteReview: require('./cli/silhouette-review.js').silhouetteReview,
  transitionReview: require('./cli/transition-review.js').transitionReview,
  spriteAtlas: require('./cli/sprite-atlas.js').spriteAtlas,
  readSpriteAtlas: require('./cli/sprite-atlas.js').readSpriteAtlas,
  readHorizonBands: require('./cli/horizon-bands.js').readHorizonBands,
  readEnvironmentImage: require('./cli/horizon-bands.js').readEnvironmentImage,
  previewTimeline: require('./cli/animation-timeline.js').previewTimeline,
  readRasterAsset(file) {
    return require('./cli/raster-asset.js').readRasterAsset(file, module.exports.load().KIT.procedural.graph.raster);
  },
  createSplatPicker(world, options) {
    return module.exports.load().KIT.procedural.contributions.create(world, options);
  },
  load() {
    const out = path.join(__dirname, 'dist', 'standalone.js'),
      srcs = files().concat(demoFiles()),
      newest = Math.max(...srcs.map(f => fs.statSync(f).mtimeMs));
    if (!fs.existsSync(out) || fs.statSync(out).mtimeMs < newest) {
      fs.mkdirSync(path.dirname(out), { recursive: true });
      // Parallel consumers may compile together. Publish only complete bundles.
      const temporary = out + '.' + randomUUID() + '.tmp';
      try {
        fs.writeFileSync(
          temporary,
          module.exports.bundle() +
            '\nconst SCENES = [];\n' +
            module.exports.demos() +
            '\nmodule.exports = { SCENES, ' +
            EXPORTS +
            ' };\n'
        );
        fs.renameSync(temporary, out);
      } finally {
        if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
      }
    }
    return require(out);
  }
};

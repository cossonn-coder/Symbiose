const fs = require('node:fs');
const path = require('node:path');
const { raster } = require('./png.js');

function readRasterAsset(file, create) {
  const location = path.resolve(file), directory = path.dirname(location);
  const manifest = JSON.parse(fs.readFileSync(location, 'utf8'));
  if (!manifest || typeof manifest.layers !== 'object' || !manifest.layers) throw new TypeError('Raster manifest needs layers');
  const { width, height } = manifest;
  let channels = 0;
  const layers = Object.fromEntries(Object.entries(manifest.layers).map(([name, layer]) => {
    if (!Array.isArray(layer?.frames)) throw new TypeError('Raster layer needs frames: ' + name);
    const frames = layer.frames.map(frame => {
      if (typeof frame !== 'string') return frame;
      const image = raster(path.resolve(directory, frame));
      if (image.w !== width || image.h !== height) throw new RangeError('Raster image dimensions do not match manifest: ' + frame);
      channels += image.data.length;
      if (channels > 64e6) throw new RangeError('Raster manifest exceeds the pixel budget');
      return image.max === 255 ? image.data : Uint8Array.from(image.data, value => Math.round(value * 255 / image.max));
    });
    return [name, { ...layer, frames }];
  }));
  return create({ ...manifest, layers });
}

module.exports = { readRasterAsset };

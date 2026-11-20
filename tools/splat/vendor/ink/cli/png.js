// PNG output is 8-bit RGB or RGBA. Import also handles non-interlaced grayscale and indexed PNGs.
const zlib = require('zlib'),
  fs = require('fs');
const CRC = new Uint32Array(256);
for (let n = 0; n < 256; n++) {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  CRC[n] = c >>> 0;
}
const crc = buf => {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = CRC[(c ^ buf[i]) & 255] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
};
const chunk = (type, data) => {
  const len = Buffer.alloc(4),
    td = Buffer.concat([Buffer.from(type, 'ascii'), data]),
    cr = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  cr.writeUInt32BE(crc(td));
  return Buffer.concat([len, td, cr]);
};
function scanlines(w, h, pixels, channels) {
  const stride = w * channels;
  if (![3, 4].includes(channels) || pixels.length !== stride * h) throw new Error('PNG pixel count does not match its shape');
  const raw = Buffer.alloc((stride + 1) * h);
  for (let y = 0; y < h; y++)
    Buffer.from(pixels.buffer, pixels.byteOffset + y * stride, stride).copy(raw, y * (stride + 1) + 1);
  return zlib.deflateSync(raw, { level: 6 });
}
function withAlpha(rgb, alpha) {
  if (rgb.length !== alpha.length * 3) throw new Error('PNG alpha count does not match its shape');
  const rgba = new Uint8Array(alpha.length * 4);
  for (let p = 0; p < alpha.length; p++) {
    rgba[p*4] = rgb[p*3];
    rgba[p*4+1] = rgb[p*3+1];
    rgba[p*4+2] = rgb[p*3+2];
    rgba[p*4+3] = alpha[p];
  }
  return rgba;
}
function encode(w, h, pixels, channels = 3) {
  const hd = Buffer.alloc(13);
  hd.writeUInt32BE(w, 0);
  hd.writeUInt32BE(h, 4);
  hd[8] = 8;
  hd[9] = channels === 4 ? 6 : 2;
  return Buffer.concat([
      Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
      chunk('IHDR', hd),
      chunk('IDAT', scanlines(w, h, pixels, channels)),
      chunk('IEND', Buffer.alloc(0))
  ]);
}
function write(file, w, h, rgb, alpha) {
  fs.writeFileSync(file, alpha ? encode(w, h, withAlpha(rgb, alpha), 4) : encode(w, h, rgb));
}
function raster(file) {
  const b = Buffer.isBuffer(file) ? file : fs.readFileSync(file);
  if (b.length < 33 || b.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a') throw new Error('Not a PNG file');
  let p = 8,
    w = 0,
    h = 0,
    bits,
    color,
    table,
    transparency;
  const parts = [];
  while (p + 12 <= b.length) {
    const len = b.readUInt32BE(p),
      type = b.toString('ascii', p + 4, p + 8),
      d = b.subarray(p + 8, p + 8 + len);
    if (p + 12 + len > b.length) throw new Error('Truncated PNG chunk');
    if (type === 'IHDR') {
      if (len !== 13 || d[10] || d[11] || d[12]) throw new Error('PNG must be non-interlaced with standard filtering and compression');
      w = d.readUInt32BE(0);
      h = d.readUInt32BE(4);
      bits = d[8];
      color = d[9];
    } else if (type === 'PLTE') table = d;
    else if (type === 'tRNS') transparency = d;
    else if (type === 'IDAT') parts.push(d);
    else if (type === 'IEND') break;
    p += 12 + len;
  }
  const ch = { 0: 1, 2: 3, 3: 1, 4: 2, 6: 4 }[color];
  const allowed = color === 0 ? [1, 2, 4, 8, 16] : color === 3 ? [1, 2, 4, 8] : [8, 16];
  if (!w || !h || w * h > 16777216 || !ch || !allowed.includes(bits) || (color === 3 && !table))
    throw new Error('Unsupported PNG dimensions or colour format');
  const rowBytes = Math.ceil(w * ch * bits / 8),
    bpp = Math.ceil(ch * bits / 8),
    st = rowBytes + 1,
    raw = zlib.inflateSync(Buffer.concat(parts), { maxOutputLength: h * st }),
    out = bits === 16 ? new Uint16Array(w * h * 4) : new Uint8Array(w * h * 4),
    row = new Uint8Array(rowBytes),
    prev = new Uint8Array(rowBytes),
    max = color === 3 ? 255 : (1 << bits) - 1;
  if (raw.length !== h * st) throw new Error('Invalid PNG scanline length');
  const sample = i => bits === 16 ? row[2 * i] * 256 + row[2 * i + 1]
    : bits === 8 ? row[i]
    : (row[(i * bits) >> 3] >> (8 - bits - (i * bits & 7))) & max;
  const transparent = i => transparency && transparency.length >= 2 * (i + 1) ? transparency.readUInt16BE(2 * i) : -1;
  for (let y = 0; y < h; y++) {
    const f = raw[y * st];
    if (f > 4) throw new Error('Invalid PNG filter');
    for (let i = 0; i < rowBytes; i++) {
      const x = raw[y * st + 1 + i],
        a = i >= bpp ? row[i - bpp] : 0,
        u = prev[i],
        c = i >= bpp ? prev[i - bpp] : 0;
      let v = x;
      if (f === 1) v = x + a;
      else if (f === 2) v = x + u;
      else if (f === 3) v = x + ((a + u) >> 1);
      else if (f === 4) {
        const q = a + u - c,
          pa = Math.abs(q - a),
          pb = Math.abs(q - u),
          pc = Math.abs(q - c);
        v = x + (pa <= pb && pa <= pc ? a : pb <= pc ? u : c);
      }
      row[i] = v & 255;
    }
    for (let x = 0; x < w; x++) {
      const dst = (y * w + x) * 4, src = x * ch;
      if (color === 3) {
        const index = sample(src);
        if (index * 3 + 2 >= table.length) throw new Error('PNG references a colour outside its palette');
        out[dst] = table[index * 3];
        out[dst + 1] = table[index * 3 + 1];
        out[dst + 2] = table[index * 3 + 2];
        out[dst + 3] = transparency?.[index] ?? 255;
      } else if (color === 0 || color === 4) {
        const gray = sample(src);
        out[dst] = out[dst + 1] = out[dst + 2] = gray;
        out[dst + 3] = color === 4 ? sample(src + 1) : gray === transparent(0) ? 0 : max;
      } else {
        const r = sample(src), g = sample(src + 1), b = sample(src + 2);
        out[dst] = r;
        out[dst + 1] = g;
        out[dst + 2] = b;
        out[dst + 3] = color === 6 ? sample(src + 3)
          : r === transparent(0) && g === transparent(1) && b === transparent(2) ? 0 : max;
      }
    }
    prev.set(row);
  }
  return { w, h, data: out, max };
}
function read(file) {
  const { w, h, data, max } = raster(file);
  const rgb = new Uint8Array(w * h * 3);
  for (let i = 0; i < rgb.length; i++) rgb[i] = Math.round(data[Math.floor(i / 3) * 4 + i % 3] * 255 / max);
  return { w, h, rgb };
}
// an animated PNG: the first frame is an ordinary picture, the rest ride along as extra chunks. Browsers play it; a plain viewer shows frame one
function animate(file, frames, fps) {
  const w = frames[0].w,
    h = frames[0].h,
    channels = frames[0].alpha ? 4 : 3;
  const hd = Buffer.alloc(13);
  hd.writeUInt32BE(w, 0);
  hd.writeUInt32BE(h, 4);
  hd[8] = 8;
  hd[9] = channels === 4 ? 6 : 2;
  const ac = Buffer.alloc(8);
  ac.writeUInt32BE(frames.length, 0);
  ac.writeUInt32BE(0, 4);
  const out = [Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', hd), chunk('acTL', ac)];
  let seq = 0;
  frames.forEach((f, i) => {
    const fc = Buffer.alloc(26);
    fc.writeUInt32BE(seq++, 0);
    fc.writeUInt32BE(w, 4);
    fc.writeUInt32BE(h, 8);
    fc.writeUInt16BE(1, 20);
    fc.writeUInt16BE(fps, 22);
    out.push(chunk('fcTL', fc));
    if (f.w !== w || f.h !== h || Boolean(f.alpha) !== (channels === 4))
      throw new Error('Animated PNG frames need the same dimensions and channels');
    const z = scanlines(w, h, f.alpha ? withAlpha(f.rgb, f.alpha) : f.rgb, channels);
    if (i === 0) out.push(chunk('IDAT', z));
    else {
      const sq = Buffer.alloc(4);
      sq.writeUInt32BE(seq++, 0);
      out.push(chunk('fdAT', Buffer.concat([sq, z])));
    }
  });
  out.push(chunk('IEND', Buffer.alloc(0)));
  fs.writeFileSync(file, Buffer.concat(out));
}
module.exports = { encode, write, read, raster, animate };

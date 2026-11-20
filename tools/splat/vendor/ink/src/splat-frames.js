/* Native splat frames for authored surface sampling and lighting. */
const SplatFrames = (() => {
  const surface = typeof SurfaceLook === 'undefined' ? require('./surface-look.js') : SurfaceLook;
  function create(world, time, M) {
      const { renderMetadata, pix, surfaceData, anim, data, rest } = world;
    const rig = anim?.rig, bones = anim?.bones;
    const matrices = new Map();
    function sample(i) {
      const offset = i * 3, p = i * 8, surfaceOffset = i * surface.STRIDE, q = i * 16;
      let normal;
      if (pix?.[p]) normal = [pix[p + 3], pix[p + 4], pix[p + 5]];
      else if (renderMetadata?.normals?.[offset] || renderMetadata?.normals?.[offset + 1] || renderMetadata?.normals?.[offset + 2])
        normal = Array.from(renderMetadata.normals.subarray(offset, offset + 3));
      else if (surfaceData?.[surfaceOffset])
        normal = [surfaceData[surfaceOffset + 1], surfaceData[surfaceOffset + 2], surfaceData[surfaceOffset + 3]];


      const packed = Math.round(data[q + 11]), kind = packed % 16;
      const part = rig?.free?.[i] ? 0 : rig?.bid[i] || 0;
      const restKind = Math.round(rest?.[q + 11] || 0) % 16;
      const skinned = bones && (restKind === 12 || restKind === 13);
      const matrix = part ? rig.M : skinned ? bones : null;
      const bone = part || (skinned ? rest[q + 12] : 0);
      const blend = skinned ? rest[q + 14] : 0;
      const second = blend ? rest[q + 13] : 0;
      if (matrix) {
        const key = [part ? 'rig' : 'bones', bone, second, blend].join(',');
        if (!matrices.has(key)) {
          const rows = matrix.slice(bone * 12, bone * 12 + 9);
          if (blend) for (let j = 0; j < 9; j++) rows[j] += (matrix[second * 12 + j] - rows[j]) * blend;
          const inverse = Math.abs(M.det(rows)) > 1e-8 ? M.inv(rows) : null;
          matrices.set(key, inverse && { inverse, normal: M.tr(inverse) });
        }
      }
      const transform = matrix ? matrices.get([part ? 'rig' : 'bones', bone, second, blend].join(',')) : null;
      const angle = kind === 5 ? time * data[q + 13] : 0;
      const c = Math.cos(angle), s = Math.sin(angle);
      if (normal && transform) normal = M.app(transform.normal, normal);
      if (normal && angle) normal = [c * normal[0] + s * normal[2], normal[1], c * normal[2] - s * normal[0]];
      const length = normal && Math.hypot(...normal);
      return { normal: length > 1e-8 ? normal.map(value => value / length) : null,
        rest: (skinned ? rest : anim?.base instanceof Float32Array ? anim.base : rest || data).subarray(q, q + 3),
        position() {
          let x = data[q], y = data[q + 1], z = data[q + 2];
          const ph = data[q + 12], sp = data[q + 13], rg = data[q + 14], ex = data[q + 15];
          if (kind === 5) [x, z] = [c * x + s * z, c * z - s * x];
          else if ((kind === 2 || kind === 3 || kind === 15) && rg) {
            const tick = time * sp / rg + ph, phase = tick - Math.floor(tick);
            y += (kind === 3 ? 1 : -1) * phase * rg;
            if (kind === 3) x += Math.sin(phase * 7 + ph * 50) * .25 * phase;
            if (kind === 15) {
              x += Math.sin(phase * 11 + ph * 40) * ex;
              z += Math.cos(phase * 7 + ph * 23) * ex * .6;
            }
          }
          else if (kind === 6) y += Math.sin(time * sp + ph) * rg;
          else if (kind === 8) {
            const flap = .2 + .8 * Math.abs(Math.sin(time * sp + ph));
            x = rg + (x - rg) * flap;
            z = ex + (z - ex) * flap;
            y += .14 * Math.sin(time * sp * .31 + ph);
          } else if (kind === 9) {
            const scale = 1 + rg * Math.sin(time * sp + ph - y * ex);
            x *= scale;
            z *= scale;
          } else if (kind === 10) y += rg * Math.min(1, Math.hypot(x, z) * .22) * Math.sin(time * sp + Math.hypot(x, z) * ex);
          else if (kind === 11) {
            x += rg * Math.sin(time * sp + ph + z * 1.3);
            y += rg * .6 * Math.sin(time * sp + ph + x * 1.1);
          } else if (kind === 14) {
            const spread = rg * Math.max(0, y - ex);
            x += spread * Math.sin(time * sp + ph);
            z += spread * .6 * Math.sin(time * sp * .73 + ph);
          } else if ((kind === 12 || kind === 13) && bones) {
            const component = (bone, axis) => bones[bone * 12 + axis * 3] * x +
              bones[bone * 12 + axis * 3 + 1] * y + bones[bone * 12 + axis * 3 + 2] * z + bones[bone * 12 + 9 + axis];
            [x, y, z] = [0, 1, 2].map(axis => component(ph, axis) * (1 - rg) + (rg ? component(sp, axis) * rg : 0));
            if (kind === 13) {
              x += .022 * Math.sin(time * 1.9 + y * 1.3 + z * .9);
              z += .0132 * Math.sin(time * 1.1 + x * 1.3);
            }
          }
          return [x, y, z];
        },
        localOffset(x, y, z) {
          const offset = [c * x - s * z, y, c * z + s * x];
          return transform ? M.app(transform.inverse, offset) : offset;
        }
      };
    }
    return sample;
  }
  return Object.freeze({ create });
})();
if (typeof module !== 'undefined') module.exports = SplatFrames;

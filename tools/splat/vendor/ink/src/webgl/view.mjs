const defaultFov = 38 * Math.PI / 180;

export function makeCamera(world, frame, width, height) {
  const camera = { target: [0, 0, 0], dist: 12, yaw: 0, pitch: 0, ...world.cam, ...frame.camera };
  const { yaw, pitch, dist, target, fov = defaultFov, ortho = false } = camera;
  if (![yaw, pitch, dist, fov, target?.[0], target?.[1], target?.[2]].every(Number.isFinite) ||
      dist <= 0 || fov <= 0 || fov >= Math.PI)
    throw new RangeError('The camera needs a finite orbit, positive distance, and field of view in (0, π)');
  const radius = world.radius ?? 14;
  const tanFov = Math.tan(fov / 2), aspect = width / height;
  const zoomedDistance = dist / (world.anim?.zoom || 1);
  const viewHeight = zoomedDistance * tanFov;
  const distance = ortho ? zoomedDistance + 2 * radius + 4 : zoomedDistance;
  const xs = Math.sin(yaw), cs = Math.cos(yaw), cy = Math.cos(pitch);
  const zx = cy * xs, zy = Math.sin(pitch), zz = cy * cs;
  const xl = Math.hypot(zz, zx);
  const xx = xl ? zz / xl : cs, xz = xl ? -zx / xl : -xs;
  const yx = zy * xz, yy = zz * xx - zx * xz, yz = -zy * xx;
  const kick = world.anim?.kick;
  const eye = [
    (target[0] + (kick?.[0] ?? 0)) + distance * zx,
    (target[1] + (kick?.[1] ?? 0)) + distance * zy,
    (target[2] + (kick?.[2] ?? 0)) + distance * zz
  ];
  const view = new Float32Array([
    xx, yx, zx, 0, 0, yy, zy, 0, xz, yz, zz, 0,
    -(xx * eye[0] + xz * eye[2]), -(yx * eye[0] + yy * eye[1] + yz * eye[2]),
    -(zx * eye[0] + zy * eye[1] + zz * eye[2]), 1
  ]);
  const near = 0.4, far = 400, scale = 1 / tanFov;
  const projection = ortho
    ? new Float32Array([1 / (viewHeight * aspect), 0, 0, 0, 0, 1 / viewHeight, 0, 0,
      0, 0, -2 / (far - near), 0, 0, 0, -(far + near) / (far - near), 1])
    : new Float32Array([scale / aspect, 0, 0, 0, 0, scale, 0, 0, 0, 0,
      (far + near) / (near - far), -1, 0, 0, 2 * far * near / (near - far), 0]);
  const depthCenter = ortho ? distance : dist;
  const result = {
    view, projection, eye, aspect, ortho, radius, distance, setback:distance-zoomedDistance,
    tangent: ortho ? viewHeight : tanFov,
    footprint: dist * 2 * tanFov / height,
    shadowFootprint: 2 * viewHeight / height,
    clipNear: Math.max(0.4, 0.15 * dist),
    clipFar: far,
    depthRange: [depthCenter - radius, depthCenter + radius]
  };
  return camera.pose ? withCameraPose(result, camera.pose) : result;
}

export function cameraPose({ eye, view }) {
  return { eye: eye.slice(), right: [view[0], view[4], view[8]],
    up: [view[1], view[5], view[9]], back: [view[2], view[6], view[10]] };
}

export function withCameraPose(camera, { eye, right, up, back }) {
  const axes = [right, up, back];
  const valid = v => Array.isArray(v) && v.length === 3 && Array.from(v).every(Number.isFinite);
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  if (!valid(eye) || !axes.every(valid) || axes.some(axis => Math.abs(dot(axis, axis) - 1) > 1e-4) ||
      Math.abs(dot(right, up)) > 1e-4 || Math.abs(dot(right, back)) > 1e-4 || Math.abs(dot(up, back)) > 1e-4 ||
      dot([right[1] * up[2] - right[2] * up[1], right[2] * up[0] - right[0] * up[2],
        right[0] * up[1] - right[1] * up[0]], back) < 0.9999)
    throw new RangeError('Camera pose needs a finite eye and a right-handed orthonormal basis');
  return { ...camera, eye: eye.slice(), view: new Float32Array([
    right[0], up[0], back[0], 0, right[1], up[1], back[1], 0, right[2], up[2], back[2], 0,
    -dot(right, eye), -dot(up, eye), -dot(back, eye), 1
  ]) };
}

function placedDepth(row, i, project) {
  const src = row.asset.data, a = row.matrix, at = row.at;
  const x = src[i], y = src[i+1], z = src[i+2], f = Math.fround;
  return f(project(f(a[0]*x + a[1]*y + a[2]*z + at[0]),
    f(a[3]*x + a[4]*y + a[5]*z + at[1]), f(a[6]*x + a[7]*y + a[8]*z + at[2])));
}

function depthBounds(row, view) {
  const a = row.matrix, at = row.at, { sortLo, sortHi } = row.asset;
  const x = view[2]*a[0] + view[6]*a[3] + view[10]*a[6];
  const y = view[2]*a[1] + view[6]*a[4] + view[10]*a[7];
  const z = view[2]*a[2] + view[6]*a[5] + view[10]*a[8];
  const mid = view[2]*at[0] + view[6]*at[1] + view[10]*at[2] + view[14];
  const largest = sortHi.reduce((sum,n,i)=>sum+Math.max(Math.abs(n),Math.abs(sortLo[i])),0);
  // Bound rounding in the three packed world coordinates and final sort depth.
  const slack = 1e-6 * (1+Math.abs(mid)+Math.abs(at[0])+Math.abs(at[1])+Math.abs(at[2])+largest*row.authored.scale);
  return [mid + Math.min(x*sortLo[0],x*sortHi[0]) + Math.min(y*sortLo[1],y*sortHi[1]) + Math.min(z*sortLo[2],z*sortHi[2]) - slack,
    mid + Math.max(x*sortLo[0],x*sortHi[0]) + Math.max(y*sortLo[1],y*sortHi[1]) + Math.max(z*sortLo[2],z*sortHi[2]) + slack];
}

export function createDepthSorter() {
  const counts = new Uint32Array(65536);
  let depth, keys, order;
  return function sort(world, view, time, instances, placements) {
    const { count, data } = world;
    const stride = instances ? 2 : 1;
    const total = count + (instances?.reduce((sum,row) => sum + row.asset.count, 0) ?? 0);
    if (!depth || depth.length < total) {
      const capacity = Math.max(total, Math.ceil((depth?.length ?? 0) * 1.25));
      depth = new Float32Array(capacity);
      keys = new Uint16Array(capacity);
    }
    if (!order || order.length < total * stride) order = new Int32Array(depth.length * stride);
    const m2 = view[2], m6 = view[6], m10 = view[10], m14 = view[14];
    const project = (x, y, z) => m2 * x + m6 * y + m10 * z + m14;
    for (let i = 0, o = 0; i < count; i++, o += 16)
      depth[i] = project(data[o], data[o + 1], data[o + 2]);
    for (const i of world.moving ?? []) {
      if (i >= count) continue;
      const o = i * 16, kind = data[o + 11] % 16;
      const phase = data[o + 12], speed = data[o + 13], range = data[o + 14];
      let x = data[o], y = data[o + 1], z = data[o + 2];
      if (kind === 2 || kind === 3) {
        const f = time * speed / range + phase;
        y += (kind === 2 ? -1 : 1) * (f - Math.floor(f)) * range;
      } else if (kind === 5) {
        const theta = time * speed, c = Math.cos(theta), s = Math.sin(theta);
        const nx = c * x + s * z;
        z = -s * x + c * z;
        x = nx;
      } else y += Math.sin(time * speed + phase) * range;
      depth[i] = project(x, y, z);
    }
    const bones = world.anim?.bones;
    if (bones) for (const i of world.anim.boned ?? []) {
      if (i >= count) continue;
      const o = i * 16, x = data[o], y = data[o + 1], z = data[o + 2];
      const weight = data[o + 14], primary = data[o + 12] * 12, secondary = data[o + 13] * 12;
      const axis = (b, a) => bones[b + a * 3] * x + bones[b + a * 3 + 1] * y +
        bones[b + a * 3 + 2] * z + bones[b + 9 + a];
      const position = a => {
        const p = axis(primary, a);
        return weight > 0 ? p + (axis(secondary, a) - p) * weight : p;
      };
      depth[i] = project(position(0), position(1), position(2));
    }
    let nextInstance = count;
    for (const row of instances ?? [])
      for (let o = 0; o < row.asset.data.length; o += 16) depth[nextInstance++] = placedDepth(row,o,project);
    let min = Infinity, max = -Infinity;
    for (let i = 0; i < total; i++) {
      const z = depth[i];
      if (z < min) min = z;
      if (z > max) max = z;
    }
    // Keep the same quantization as the fully expanded world. Most culled
    // placements cannot change the extrema and need only an AABB test.
    if (placements && instances.length < placements.length) {
      let visibleIndex = 0;
      for (const row of placements) {
        if (row === instances[visibleIndex]) { visibleIndex++; continue; }
        const [lo,hi] = depthBounds(row,view);
        if (lo >= min && hi <= max) continue;
        for (let o = 0; o < row.asset.data.length; o += 16) {
          const z=placedDepth(row,o,project);
          if (z < min) min = z;
          if (z > max) max = z;
        }
      }
    }
    for (const i of world.back ?? []) if (i < count) depth[i] = min;
    const scale = 65535 / (max - min || 1);
    counts.fill(0);
    for (let i = 0; i < total; i++) counts[keys[i] = (depth[i] - min) * scale | 0]++;
    let next = 0;
    for (let bucket = 0; bucket < counts.length; bucket++) {
      const size = counts[bucket];
      counts[bucket] = next;
      next += size;
    }
    if (!instances) {
      for (let i = 0; i < count; i++) order[counts[keys[i]]++] = i;
    } else {
      for (let i = 0; i < count; i++) {
        const j = counts[keys[i]]++ * 2;
        order[j] = i; order[j+1] = 0;
      }
      let i = count;
      for (const row of instances) {
        const start = count + row.start, ref = row.index + 1;
        for (let n = 0; n < row.asset.count; n++, i++) {
          const j = counts[keys[i]]++ * 2;
          order[j] = start + n; order[j+1] = ref;
        }
      }
    }
    return order.length === total * stride ? order : order.subarray(0,total * stride);
  };
}

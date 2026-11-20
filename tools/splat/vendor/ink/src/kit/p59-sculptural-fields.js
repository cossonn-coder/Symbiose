/* Bounded implicit forms sampled straight into the sculptor. */
(function (K) {
  const P = K.procedural, V = K.V, M = K.M, T = P.transforms,
    EPS = 1e-8, TAU = 2 * Math.PI,
    finite = n => Number.isFinite(n) && Math.abs(n) <= 1e7,
    point = (p, size) => Array.isArray(p) && p.length === size && p.every(finite),
    positive = n => finite(n) && n > EPS,
    clamp = (n, a, b) => Math.max(a, Math.min(b, n)),
    lerp = (a, b, t) => a + (b - a) * t;

  function form(sd, bounds, cost = 1) {
    const domain = P.spatial.bounds(bounds);
    if (!point(domain.min, 3) || !point(domain.max, 3) || domain.min.some((v, i) => domain.max[i] - v <= EPS))
      throw new Error('An implicit form needs finite bounds with positive extent');
    return Object.freeze({ sd, bounds: P.data.freeze(domain), cost });
  }
  function transformed(sd, bounds, poseSpec, cost) {
    if (!poseSpec) return form(sd, bounds, cost);
    const pose = T.local(poseSpec), inverse = M.inv(pose.R), scale = T.distanceScale(pose);
    return form((x, y, z) => sd(...M.app(inverse, [x - pose.t[0], y - pose.t[1], z - pose.t[2]])) * scale,
      T.bounds(pose, bounds), cost);
  }
  function intervalDistance(a, b) {
    return Math.min(Math.max(a, b), 0) + Math.hypot(Math.max(0, a), Math.max(0, b));
  }

  function superquadric({ radii = [1, 1, 1], exponents = [2, 2], pose } = {}) {
    if (!point(radii, 3) || !radii.every(positive) || !point(exponents, 2) || exponents.some(e => e < 0.5 || e > 32))
      throw new Error('Superquadrics need positive radii and two exponents from 0.5 to 32');
    const [rx, ry, rz] = radii, [p, q] = exponents, radial = Math.min(rx, ry, rz);
    return transformed((x, y, z) => {
      const a = Math.abs(x) / rx, b = Math.abs(z) / rz, c = Math.abs(y) / ry,
        m = Math.max(a, b, c);
      if (!m) return -radial;
      const ring = ((a / m) ** p + (b / m) ** p) ** (q / p);
      return (m * (ring + (c / m) ** q) ** (1 / q) - 1) * radial;
    }, { min: [-rx, -ry, -rz], max: [rx, ry, rz] }, pose);
  }

  function loft(sections, { pose } = {}) {
    if (!Array.isArray(sections) || sections.length < 2 || sections.length > 128)
      throw new Error('A loft needs between two and 128 ordered sections');
    const points = [];
    let maxEdges = 0, previous = -Infinity;
    const bands = sections.map(({ y, profile, center = [0, 0], scale = 1, roll = 0 } = {}) => {
      if (!finite(y) || y - previous <= EPS || !point(center, 2) || !positive(scale) || !finite(roll) ||
        !Array.isArray(profile) || profile.length < 3 || profile.length > 4096 || !profile.every(p => point(p, 2)))
        throw new Error('Loft sections need increasing elevations, positive scales and polygon profiles');
      previous = y;
      const c = Math.cos(roll), s = Math.sin(roll), f = P.geometry.profileDistance(profile);
      for (const [x, z] of profile)
        points.push([center[0] + scale * (x * c - z * s), y, center[1] + scale * (x * s + z * c)]);
      maxEdges = Math.max(maxEdges, profile.length);
      return { y, x: center[0], z: center[1], scale, roll, f };
    });
    const bounds = P.spatial.boxOf(points), first = bands[0], last = bands.at(-1);
    // The intermediate profile can turn past either authored extreme.
    for (const [i, { profile }] of sections.entries()) {
      const radius = profile.reduce((r, p) => Math.max(r, Math.hypot(...p)), 0);
      for (const b of [bands[i - 1], bands[i], bands[i + 1]]) {
        if (!b) continue;
        const r = radius * b.scale;
        bounds.min[0] = Math.min(bounds.min[0], b.x - r);
        bounds.min[2] = Math.min(bounds.min[2], b.z - r);
        bounds.max[0] = Math.max(bounds.max[0], b.x + r);
        bounds.max[2] = Math.max(bounds.max[2], b.z + r);
      }
    }
    return transformed((x, y, z) => {
      let low = 0, high = bands.length - 1;
      while (high - low > 1) {
        const mid = (low + high) >> 1;
        if (bands[mid].y <= y) low = mid;
        else high = mid;
      }
      const a = bands[low], b = bands[high], t = clamp((y - a.y) / (b.y - a.y), 0, 1),
        px = x - lerp(a.x, b.x, t), pz = z - lerp(a.z, b.z, t),
        angle = a.roll + Math.atan2(Math.sin(b.roll - a.roll), Math.cos(b.roll - a.roll)) * t,
        c = Math.cos(angle), s = Math.sin(angle), scale = lerp(a.scale, b.scale, t),
        u = (c * px + s * pz) / scale, v = (c * pz - s * px) / scale,
        lateral = lerp(a.f(u, v), b.f(u, v), t) * scale;
      return intervalDistance(lateral, Math.max(first.y - y, y - last.y));
    }, bounds, pose, maxEdges * 2);
  }

  function skeleton(nodes, { blend = 0, pose } = {}) {
    if (!Array.isArray(nodes) || !nodes.length || nodes.length > 2048 || !finite(blend) || blend < 0)
      throw new Error('An implicit skeleton needs a bounded parent forest and a nonnegative blend');
    const points = [], primitives = [], kids = new Uint16Array(nodes.length);
    const joints = nodes.map(({ point: at, radius, parent = -1 } = {}, i) => {
      if (!point(at, 3) || !positive(radius) || !Number.isSafeInteger(parent) || parent < -1 || parent >= i)
        throw new Error('Skeleton nodes need positions, radii and preceding parents');
      if (parent >= 0) kids[parent]++;
      const r = radius + blend;
      points.push(at.map(v => v - r), at.map(v => v + r));
      return { at: at.slice(), radius, parent };
    });
    for (const [i, { at, radius, parent }] of joints.entries()) {
      const sphere = (x, y, z) => Math.hypot(x - at[0], y - at[1], z - at[2]) - radius;
      if (parent < 0) {
        if (!kids[i]) primitives.push(sphere);
        continue;
      }
      const a = joints[parent], delta = V.sub(at, a.at), run = V.len(delta), rise = radius - a.radius;
      // When the taper is steeper than the centerline, the larger endpoint covers the sweep.
      if (run <= Math.abs(rise) + EPS) {
        primitives.push(rise >= 0 ? sphere : (x, y, z) => Math.hypot(x - a.at[0], y - a.at[1], z - a.at[2]) - a.radius);
        continue;
      }
      const direction = V.mul(delta, 1 / run), slope = rise / run, shift = slope / Math.sqrt(1 - slope * slope);
      primitives.push((x, y, z) => {
        const dx = x - a.at[0], dy = y - a.at[1], dz = z - a.at[2],
          axial = dx * direction[0] + dy * direction[1] + dz * direction[2],
          radial = Math.sqrt(Math.max(0, dx * dx + dy * dy + dz * dz - axial * axial)),
          t = clamp(axial + radial * shift, 0, run);
        return Math.hypot(radial, axial - t) - a.radius - slope * t;
      });
    }
    const field = (x, y, z) => {
      let d = primitives[0](x, y, z);
      for (let i = 1; i < primitives.length; i++) {
        const near = primitives[i](x, y, z), h = blend ? Math.max(0, 1 - Math.abs(d - near) / blend) : 0;
        d = Math.min(d, near) - 0.25 * blend * h * h;
      }
      return d;
    };
    return transformed(field, P.spatial.boxOf(points), pose, primitives.length);
  }

  function periodic({
    bounds, type = 'gyroid', period = 1, phase = [0, 0, 0],
    mode = 'sheet', thickness = 0.09, level = 0, host, pose
  } = {}) {
    const scales = typeof period === 'number' ? [period, period, period] : period;
    if (!['gyroid', 'schwarzP', 'diamond'].includes(type) || !['sheet', 'solid'].includes(mode) ||
      !point(scales, 3) || !scales.every(positive) || !point(phase, 3) || !positive(thickness) ||
      !finite(level) || (host !== undefined && typeof host !== 'function'))
      throw new Error('Periodic forms need a known surface, positive period and valid clipping field');
    const box = P.spatial.bounds(bounds), freq = scales.map(v => TAU / v), offset = phase.slice(),
      length = Math.min(...scales) / (type === 'schwarzP' ? TAU : TAU * 2);
    return transformed((x, y, z) => {
      const a = x * freq[0] + offset[0], b = y * freq[1] + offset[1], c = z * freq[2] + offset[2],
        s = Math.sin(a), t = Math.sin(b), u = Math.sin(c), p = Math.cos(a), q = Math.cos(b), r = Math.cos(c);
      let value;
      if (type === 'gyroid') value = s * q + t * r + u * p;
      else if (type === 'schwarzP') value = p + q + r;
      else value = s * t * u + s * q * r + p * t * r + p * q * u;
      const v = (value - level) * length,
        field = mode === 'sheet' ? Math.abs(v) - thickness * 0.5 : v,
        trim = Math.max(box.min[0] - x, x - box.max[0], box.min[1] - y, y - box.max[1], box.min[2] - z, z - box.max[2]);
      return Math.max(field, trim, host ? host(x, y, z) : -Infinity);
    }, box, pose);
  }

  function shell(host, { inner = 0.08, outer = 0, maxOuter } = {}) {
    const weight = v => typeof v === 'function' || (finite(v) && v >= 0);
    if (typeof host?.sd !== 'function' || !weight(inner) || !weight(outer) ||
      (typeof outer === 'function' && (!finite(maxOuter) || maxOuter < 0)))
      throw new Error('A local shell needs a host and bounded nonnegative thickness');
    const pad = typeof outer === 'function' ? maxOuter : outer, sample = host.sd;
    return form((x, y, z) => {
      const low = typeof inner === 'function' ? inner(x, y, z) : inner,
        high = typeof outer === 'function' ? outer(x, y, z) : outer;
      if (!finite(low) || low < 0 || !finite(high) || high < 0 || high > pad)
        throw new Error('Local shell thickness is outside its declared range');
      const d = sample(x, y, z);
      return Math.max(d - high, -d - low);
    }, P.spatial.expand(P.spatial.bounds(host.bounds), pad), host.cost ?? 1);
  }

  function samples(source, spacing, emit, maxWork) {
    const { sd, bounds, cost = 1 } = source,
      lo = bounds.min.map(v => v - spacing * 0.51),
      n = bounds.max.map((v, i) => Math.ceil((v - lo[i]) / spacing + 0.51) + 1),
      total = n[0] * n[1] * n[2];
    if (!Number.isSafeInteger(total) || total > 3000000 || total * cost > maxWork)
      throw new Error('Implicit form exceeds its sample budget');
    // Hold only two slices. Each edge crosses the zero level at most once at this resolution.
    const count = n[0] * n[1];
    let previous = new Float64Array(count), current = new Float64Array(count);
    for (let k = 0; k < n[2]; k++) {
      const z = lo[2] + k * spacing;
      for (let j = 0, i = 0; j < n[1]; j++) {
        const y = lo[1] + j * spacing;
        for (let a = 0; a < n[0]; a++, i++) {
          const x = lo[0] + a * spacing, d = sd(x, y, z);
          if (!Number.isFinite(d)) throw new Error('Implicit form returned a nonfinite sample');
          current[i] = d;
          if (a && ((d < 0) !== (current[i - 1] < 0))) emit(x - spacing * d / (d - current[i - 1]), y, z);
          if (j && ((d < 0) !== (current[i - n[0]] < 0))) emit(x, y - spacing * d / (d - current[i - n[0]]), z);
          if (k && ((d < 0) !== (previous[i] < 0))) emit(x, y, z - spacing * d / (d - previous[i]));
        }
      }
      [previous, current] = [current, previous];
    }
  }

  const sculpt = K.sculpt;
  K.sculpt = S0 => {
    const S = sculpt(S0) || S0;
    S.implicitForm = (source, mat, o = {}) => {
      if (typeof source?.sd !== 'function' || (o.cell !== undefined && !positive(o.cell)) ||
        (o.res !== undefined && !positive(o.res)) ||
        (o.maxWork !== undefined && (!Number.isSafeInteger(o.maxWork) || o.maxWork <= 0 || o.maxWork > 160000000)))
        throw new Error('Implicit form needs a signed field and valid sample controls');
      const { sd, bounds, cost } = form(source.sd, source.bounds, source.cost ?? 1);
      if (!positive(cost)) throw new Error('Implicit form cost must be positive');
      const bc = bounds.min.map((v, i) => (v + bounds.max[i]) * 0.5),
        br = V.len(V.sub(bounds.max, bc)), cell = o.cell,
        node = { bc, br, bounds, sd, sample(emit) {
          samples({ sd, bounds, cost }, cell ?? this.res * 0.76, emit, o.maxWork ?? 32000000);
        } };
      return S.add(node, mat, { reach: (cell ?? o.res ?? S.res) * 0.66, ...o });
    };
    return S;
  };

  P.forms = { superquadric, loft, skeleton, periodic, shell };
})(KIT);

/* Lattice aggregation and Gray–Scott fields on grids or supplied surface graphs. */
(function (K) {
  const P = K.procedural,
    integer = (n, a, b) => Number.isSafeInteger(n) && n >= a && n <= b,
    fraction = n => Number.isFinite(n) && n >= 0 && n <= 1,
    saturate = n => Math.max(0, Math.min(1, n)),
    compass = [[1, 0], [-1, 0], [0, 1], [0, -1]];

  function dimensions(width, height) {
    if (!integer(width, 3, 512) || !integer(height, 3, 512) || width * height > 180000)
      throw new Error('Growth grid dimensions exceed the cell budget');
  }

  function aggregate({
    width, height, seeds = [[Math.floor(width / 2), Math.floor(height / 2)]],
    walkers = 10000, lifetime = 450, target = Math.min(1200, width * height), launch = 5, escape = 13,
    stick = 1, mask, seed = 0, maxChecks = 7000000
  } = {}) {
    dimensions(width, height);
    const size = width * height;
    if (
      !Array.isArray(seeds) || !integer(seeds.length, 1, Math.min(size, 4096)) ||
      !integer(walkers, 1, 200000) || !integer(lifetime, 1, 40000) || !integer(target, seeds.length, size) ||
      !integer(launch, 1, 128) || !integer(escape, launch + 1, 512) || !fraction(stick) ||
      (mask !== undefined && typeof mask !== 'function') ||
      !Number.isSafeInteger(seed) || !integer(maxChecks, 1, 60000000)
    ) throw new Error('Aggregation needs bounded seeds, walkers and sticking controls');
    const dice = K.grow.dice(P.data.hash('lattice-aggregation', seed)),
      cells = new Uint32Array(size),
      allowed = new Uint8Array(size),
      within = (x, z) => x >= 0 && x < width && z >= 0 && z < height,
      iOf = (x, z) => z * width + x,
      nodes = [],
      work = { checks: 0, walkers: 0 };
    for (let z = 0; z < height; z++)
      for (let x = 0; x < width; x++) allowed[iOf(x, z)] = Number(!mask || mask(x, z));
    const center = [0, 0];
    for (const p of seeds) {
      if (!Array.isArray(p) || p.length !== 2 || !integer(p[0], 0, width - 1) || !integer(p[1], 0, height - 1))
        throw new Error('Aggregation seeds need valid grid points');
      const i = iOf(...p);
      if (!allowed[i] || cells[i]) throw new Error('Aggregation seeds must be distinct passable cells');
      center[0] += p[0] / seeds.length;
      center[1] += p[1] / seeds.length;
      nodes.push({ x: p[0], z: p[1], parent: -1 });
      cells[i] = nodes.length;
    }
    let span = Math.max(...nodes.map(({ x, z }) => Math.hypot(x - center[0], z - center[1]))),
      status = 'ok';
    outer:
    for (let attempt = 0; attempt < walkers && nodes.length < target; attempt++) {
      work.walkers++;
      const a = dice() * Math.PI * 2, r = span + launch;
      let x = Math.max(0, Math.min(width - 1, Math.round(center[0] + r * Math.cos(a)))),
        z = Math.max(0, Math.min(height - 1, Math.round(center[1] + r * Math.sin(a))));
      for (let j = 0; j < lifetime; j++) {
        if (work.checks >= maxChecks) {
          status = 'budget';
          break outer;
        }
        work.checks++;
        if (!allowed[iOf(x, z)] || cells[iOf(x, z)] ||
          Math.hypot(x - center[0], z - center[1]) > span + escape) break;
        let parent = -1;
        for (const [u, v] of compass) {
          const px = x + u, pz = z + v;
          if (within(px, pz) && cells[iOf(px, pz)]) {
            parent = cells[iOf(px, pz)] - 1;
            break;
          }
        }
        if (parent >= 0 && dice() < stick) {
          nodes.push({ x, z, parent });
          cells[iOf(x, z)] = nodes.length;
          span = Math.max(span, Math.hypot(x - center[0], z - center[1]));
          break;
        }
        const [dx, dz] = compass[Math.floor(dice() * compass.length)];
        if (within(x + dx, z + dz) && allowed[iOf(x + dx, z + dz)] && !cells[iOf(x + dx, z + dz)]) {
          x += dx;
          z += dz;
        }
      }
    }
    if (status === 'ok' && nodes.length < target) status = 'limit';
    return Object.freeze({ status, width, height, cells, nodes: P.data.freeze(nodes), work: Object.freeze(work) });
  }

  function react(points, links, {
    steps = 400, dt = 1, du = 0.8, dv = 0.39, feed = 0.0367, kill = 0.0649,
    spots, initial, seed = 0, maxWork = 34000000
  } = {}) {
    if (
      !Array.isArray(points) || !integer(points.length, 1, 180000) ||
      !Array.isArray(links) || links.length > points.length * 12 ||
      !integer(steps, 0, 20000) || !fraction(dt) || dt <= 0 || !fraction(du) || !fraction(dv) ||
      ![feed, kill].every(n => fraction(n) || typeof n === 'function') ||
      (initial !== undefined && typeof initial !== 'function') ||
      (spots !== undefined && (!Array.isArray(spots) || spots.length > points.length ||
        !spots.every(i => integer(i, 0, points.length - 1)))) ||
      !Number.isSafeInteger(seed) || !integer(maxWork, 1, 85000000)
    ) throw new Error('Gray–Scott needs a bounded domain, seed and stable integration controls');
    const n = points.length, work = (n + 2 * links.length) * steps;
    if (work > maxWork) throw new Error('Gray–Scott exceeds its integration budget');
    const neighbors = points.map(() => []),
      count = new Float64Array(n), f = new Float64Array(n), k = new Float64Array(n),
      dice = K.grow.dice(P.data.hash('reaction-diffusion', seed)),
      seeded = new Set(spots ?? [Math.floor(n / 2)]);
    let u = new Float64Array(n), v = new Float64Array(n),
      nextU = new Float64Array(n), nextV = new Float64Array(n);
    for (const link of links) {
      if (
        !Array.isArray(link) || link.length < 2 || link.length > 3 ||
        !integer(link[0], 0, n - 1) || !integer(link[1], 0, n - 1) || link[0] === link[1] ||
        (link[2] !== undefined && (!Number.isFinite(link[2]) || link[2] <= 0 || link[2] > 1e6))
      ) throw new Error('Gray–Scott surface links need distinct indices and positive weights');
      const [a, b, weight = 1] = link;
      neighbors[a].push({ i: b, weight });
      neighbors[b].push({ i: a, weight });
      count[a] += weight;
      count[b] += weight;
    }
    for (const [i, p] of points.entries()) {
      f[i] = typeof feed === 'function' ? feed(p, i) : feed;
      k[i] = typeof kill === 'function' ? kill(p, i) : kill;
      const value = initial ? initial(p, i) : seeded.has(i) ? [0.48 + 0.04 * dice(), 0.24 + 0.025 * dice()] : [1, 0];
      if (!fraction(f[i]) || !fraction(k[i]) || !Array.isArray(value) || value.length !== 2 || !value.every(fraction))
        throw new Error('Gray–Scott field values must be between zero and one');
      [u[i], v[i]] = value;
    }
    for (let step = 0; step < steps; step++) {
      for (let i = 0; i < n; i++) {
        let sumU = 0, sumV = 0;
        for (const neighbor of neighbors[i]) {
          sumU += u[neighbor.i] * neighbor.weight;
          sumV += v[neighbor.i] * neighbor.weight;
        }
        const a = u[i], b = v[i],
          lapU = count[i] ? sumU / count[i] - a : 0,
          lapV = count[i] ? sumV / count[i] - b : 0,
          reaction = a * b * b;
        nextU[i] = saturate(a + dt * (du * lapU - reaction + f[i] * (1 - a)));
        nextV[i] = saturate(b + dt * (dv * lapV + reaction - (f[i] + k[i]) * b));
      }
      [u, nextU] = [nextU, u];
      [v, nextV] = [nextV, v];
    }
    return Object.freeze({ u, v, work: Object.freeze({ steps, updates: work }) });
  }

  function grayScottSurface(points, links, options = {}) {
    if (
      !Array.isArray(points) || !integer(points.length, 1, 180000) ||
      !points.every(p => Array.isArray(p) && p.length === 3 && p.every(Number.isFinite))
    ) throw new Error('Surface reaction–diffusion needs finite XYZ samples');
    return react(points.map(p => p.slice()), links, options);
  }

  function grayScottGrid({ width, height, wrap = false, mask, ...options } = {}) {
    dimensions(width, height);
    if (typeof wrap !== 'boolean' || (mask !== undefined && typeof mask !== 'function'))
      throw new Error('Gray–Scott grid needs valid boundary rules');
    const points = [], links = [], allowed = new Uint8Array(width * height);
    for (let z = 0; z < height; z++) for (let x = 0; x < width; x++) {
      allowed[z * width + x] = Number(!mask || mask(x, z));
      points.push([x, z]);
    }
    for (const [i, [x, z]] of points.entries()) {
      if (!allowed[i]) continue;
      for (const [dx, dz, weight] of [[1, 0, 4], [0, 1, 4], [1, 1, 1], [-1, 1, 1]]) {
        let u = x + dx, v = z + dz;
        if (wrap) {
          u = (u + width) % width;
          v = (v + height) % height;
        }
        if (u < 0 || u >= width || v < 0 || v >= height || !allowed[v * width + u]) continue;
        links.push([i, v * width + u, weight]);
      }
    }
    const previous = options.initial, spots = new Set(options.spots ?? []),
      center = [Math.floor(width / 2), Math.floor(height / 2)],
      radius = Math.max(1, Math.min(4, Math.floor(Math.min(width, height) / 7))),
      seed = K.grow.dice(P.data.hash('gray-scott-grid', options.seed ?? 0)),
      result = react(points, links, { ...options, initial(p, i) {
        if (!allowed[i]) return [1, 0];
        if (previous) return previous(p, i);
        const seeded = options.spots ? spots.has(i) : Math.hypot(p[0] - center[0], p[1] - center[1]) <= radius;
        return seeded ? [0.48 + 0.04 * seed(), 0.28 + 0.03 * seed()] : [1, 0];
      } });
    return Object.freeze({ width, height, ...result,
      sample: (x, z) => integer(x, 0, width - 1) && integer(z, 0, height - 1)
        ? { u: result.u[z * width + x], v: result.v[z * width + x] } : null
    });
  }

  Object.assign(P.growth, { aggregate, grayScottGrid, grayScottSurface });
})(KIT);

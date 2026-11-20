/* k7-particles: loose splats, and the currents that carry them.
     const ps = st.add(K.particles(st, pool, { flow, sdf, ground }))
     ps.emit({ p, v, life, size, cols: [palette indices over its life], grav, drag, streak, glow, fade, spin, ride: 0..1 (how much the flow carries it) })
     ready-made: ps.dust(p, n, cols)  ps.sparks(p, n, cols, dir)  ps.embers(p, n, cols)  ps.smoke(p, n, cols)  ps.ring(p, r, cols, n)  ps.bolt(a, b, cols)  ps.rain(box, rate, cols)  ps.chips(p, n, cols, dir)
   Flow: a function (x, y, z, t, out) that fills out[0..2] with a velocity.
     K.flow.wind(v)  K.flow.curl(scale, speed)  K.flow.vortex(c, axis, strength, radius)  K.flow.sink(c, strength)  K.flow.sum(a, b, ...)
     K.flow.around(sdf, margin)   wraps the others: near a surface the current is turned along it, so nothing is carried through a solid */
(function (K) {
  const V = K.V;
  // smooth noise in 3D, 0..1 (value noise: cheap, and good enough to stir a current)
  const h3 = (x, y, z) => {
    const s = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453;
    return s - Math.floor(s);
  };
  K.noise3 = (x, y, z) => {
    const ix = Math.floor(x),
      iy = Math.floor(y),
      iz = Math.floor(z),
      fx = x - ix,
      fy = y - iy,
      fz = z - iz,
      u = fx * fx * (3 - 2 * fx),
      v = fy * fy * (3 - 2 * fy),
      w = fz * fz * (3 - 2 * fz),
      L = (a, b, t) => a + (b - a) * t;
    return L(
      L(L(h3(ix, iy, iz), h3(ix + 1, iy, iz), u), L(h3(ix, iy + 1, iz), h3(ix + 1, iy + 1, iz), u), v),
      L(L(h3(ix, iy, iz + 1), h3(ix + 1, iy, iz + 1), u), L(h3(ix, iy + 1, iz + 1), h3(ix + 1, iy + 1, iz + 1), u), v),
      w
    );
  };
  K.flow = {
    wind: v => (x, y, z, t, o) => {
      o[0] = v[0];
      o[1] = v[1];
      o[2] = v[2];
    },
    // a current with no sources or sinks (the curl of a noise potential): it swirls without bunching things up
    curl: (scale, speed) => {
      const e = 0.1,
        n = K.noise3;
      return (x, y, z, t, o) => {
        x = x * scale;
        y = y * scale;
        z = z * scale + t * 0.13;
        const a = n(x, y + e, z + 31) - n(x, y - e, z + 31) - (n(x, y + 17, z + e) - n(x, y + 17, z - e)),
          b = n(x + 5, y, z + e) - n(x + 5, y, z - e) - (n(x + e, y, z + 31) - n(x - e, y, z + 31)),
          c = n(x + e, y + 17, z) - n(x - e, y + 17, z) - (n(x + 5, y + e, z) - n(x + 5, y - e, z));
        const k = speed / (2 * e);
        o[0] = a * k;
        o[1] = b * k;
        o[2] = c * k;
      };
    },
    vortex: (c, axis, strength, radius) => {
      const ax = V.norm(axis);
      return (x, y, z, t, o) => {
        const r = [x - c[0], y - c[1], z - c[2]],
          h = V.dot(r, ax),
          q = V.mad(r, ax, -h),
          d = V.len(q),
          w = V.cross(ax, q),
          k = (strength * Math.exp(-d / radius)) / (d + 0.2);
        o[0] = w[0] * k - q[0] * 0.3 * k;
        o[1] = w[1] * k - q[1] * 0.3 * k;
        o[2] = w[2] * k - q[2] * 0.3 * k;
      };
    },
    sink: (c, strength) => (x, y, z, t, o) => {
      const r = [c[0] - x, c[1] - y, c[2] - z],
        d = V.len(r) + 0.3;
      o[0] = (r[0] / d) * strength;
      o[1] = (r[1] / d) * strength;
      o[2] = (r[2] / d) * strength;
    },
    sum: (...fs) => {
      const tmp = [0, 0, 0];
      return (x, y, z, t, o) => {
        let a = 0,
          b = 0,
          c = 0;
        for (const f of fs) {
          f(x, y, z, t, tmp);
          a += tmp[0];
          b += tmp[1];
          c += tmp[2];
        }
        o[0] = a;
        o[1] = b;
        o[2] = c;
      };
    },
    around: (flow, sdf, margin) => {
      margin = margin || 0.5;
      const e = 0.05;
      return (x, y, z, t, o) => {
        flow(x, y, z, t, o);
        const d = sdf(x, y, z);
        if (d > margin) return;
        const n = V.norm([sdf(x + e, y, z) - d, sdf(x, y + e, z) - d, sdf(x, y, z + e) - d]),
          into = o[0] * n[0] + o[1] * n[1] + o[2] * n[2],
          k = 1 - K.clamp(d / margin, 0, 1);
        if (into < 0) {
          o[0] -= n[0] * into * k;
          o[1] -= n[1] * into * k;
          o[2] -= n[2] * into * k;
        }
        if (d < 0.05) {
          o[0] += n[0] * 1.5;
          o[1] += n[1] * 1.5;
          o[2] += n[2] * 1.5;
        }
      };
    }
  };
  K.particles = (st, pool, o) => {
    o = o || {};
    const n = pool.n,
      P = [],
      fl = [0, 0, 0],
      palP = st.W.pal.map(h => ((h >> 16) & 255) + (h & 0xff00) + ((h & 255) << 16));
    for (let i = 0; i < n; i++) P.push({ life: 0 });
    let next = 0;
    const ps = {
      live: 0,
      flow: o.flow || null,
      emit(e) {
        const q = P[next],
          i = pool.first + next;
        next = (next + 1) % n;
        q.i = i;
        q.p = e.p.slice();
        q.v = (e.v || [0, 0, 0]).slice();
        q.life = q.max = e.life || 1;
        q.size = e.size || 0.05;
        q.cols = e.cols || [1];
        q.grav = e.grav === undefined ? 0 : e.grav;
        q.drag = e.drag || 0;
        q.streak = e.streak || 0;
        q.fade = e.fade === undefined ? 0.3 : e.fade;
        q.ride = e.ride || 0;
        q.grow = e.grow || 0;
        q.bounce = e.bounce === undefined ? -1 : e.bounce;
        q.alpha = e.alpha || 3;
        q.fixed = !!e.fixed;
        q.ax = e.ax || null;
        q.len = e.len || 0;
        return q;
      },
      update(dt, t) {
        let live = 0;
        for (let k = 0; k < n; k++) {
          const q = P[k];
          if (q.life <= 0) continue;
          q.life -= dt;
          if (q.life <= 0) {
            pool.hide(st, q.i);
            continue;
          }
          live++;
          const u = 1 - q.life / q.max;
          if (!q.fixed) {
            q.v[1] -= q.grav * dt;
            if (q.ride && ps.flow) {
              ps.flow(q.p[0], q.p[1], q.p[2], t, fl);
              const kk = Math.min(1, q.ride * dt * 6);
              q.v[0] += (fl[0] - q.v[0]) * kk;
              q.v[1] += (fl[1] - q.v[1]) * kk;
              q.v[2] += (fl[2] - q.v[2]) * kk;
            }
            if (q.drag) {
              const d = Math.max(0, 1 - q.drag * dt);
              q.v[0] *= d;
              q.v[1] *= d;
              q.v[2] *= d;
            }
            q.p[0] += q.v[0] * dt;
            q.p[1] += q.v[1] * dt;
            q.p[2] += q.v[2] * dt;
            const gy = o.ground ? o.ground(q.p[0], q.p[2]) : -1e9;
            if (q.p[1] < gy + q.size) {
              if (q.bounce < 0) {
                q.life = 0;
                pool.hide(st, q.i);
                continue;
              }
              q.p[1] = gy + q.size;
              q.v[1] = -q.v[1] * q.bounce;
              q.v[0] *= 0.6;
              q.v[2] *= 0.6;
            }
          }
          const size = q.size * (1 + q.grow * u) * (q.fade > 0 && u > 1 - q.fade ? (1 - u) / q.fade : 1),
            col = palP[q.cols[Math.min(q.cols.length - 1, Math.floor(u * q.cols.length))]];
          if (q.ax) pool.put(st, q.i, q.p[0], q.p[1], q.p[2], size, col, q.alpha, q.ax, q.len);
          else if (q.streak) {
            const sp = V.len(q.v);
            pool.put(
              st,
              q.i,
              q.p[0],
              q.p[1],
              q.p[2],
              size,
              col,
              q.alpha,
              sp > 1e-3 ? V.mul(q.v, 1 / sp) : [0, 1, 0],
              size + sp * q.streak
            );
          } else pool.put(st, q.i, q.p[0], q.p[1], q.p[2], size, col, q.alpha);
        }
        ps.live = live;
      }
    };
    const R = () => K.rnd(),
      rr = (a, b) => a + (b - a) * K.rnd(),
      ball = s => {
        const a = rr(0, 6.283),
          y = rr(-1, 1),
          r = Math.sqrt(1 - y * y);
        return [Math.cos(a) * r * s, y * s, Math.sin(a) * r * s];
      };
    ps.dust = (p, cnt, cols, spread) => {
      for (let k = 0; k < cnt; k++) {
        const a = rr(0, 6.283),
          s = rr(0.4, 1.6) * (spread || 1);
        ps.emit({
          p: [p[0] + Math.cos(a) * 0.2, p[1] + 0.05, p[2] + Math.sin(a) * 0.2],
          v: [Math.cos(a) * s, rr(0.2, 0.9), Math.sin(a) * s],
          life: rr(0.35, 0.8),
          size: rr(0.06, 0.13),
          cols,
          drag: 2.5,
          grow: 1.2,
          fade: 0.6,
          ride: 0.2
        });
      }
    };
    ps.sparks = (p, cnt, cols, dir, speed) => {
      for (let k = 0; k < cnt; k++) {
        const d = ball(1),
          s = (speed || 6) * rr(0.4, 1);
        ps.emit({
          p,
          v: [(d[0] + (dir ? dir[0] : 0)) * s, (d[1] + (dir ? dir[1] : 0.6)) * s, (d[2] + (dir ? dir[2] : 0)) * s],
          life: rr(0.25, 0.6),
          size: 0.035,
          cols,
          grav: 14,
          streak: 0.03,
          fade: 0.5,
          bounce: 0.3
        });
      }
    };
    ps.embers = (p, cnt, cols) => {
      for (let k = 0; k < cnt; k++) {
        const d = ball(0.25);
        ps.emit({
          p: V.add(p, d),
          v: [d[0], rr(0.8, 2), d[2]],
          life: rr(1.2, 3),
          size: rr(0.03, 0.05),
          cols,
          grav: -0.6,
          ride: 0.8,
          fade: 0.4,
          alpha: 3
        });
      }
    };
    ps.smoke = (p, cnt, cols) => {
      for (let k = 0; k < cnt; k++) {
        const d = ball(0.2);
        ps.emit({
          p: V.add(p, d),
          v: [d[0], rr(0.5, 1.1), d[2]],
          life: rr(1.5, 2.8),
          size: rr(0.12, 0.2),
          cols,
          grav: -0.4,
          ride: 0.6,
          grow: 1.5,
          fade: 0.7,
          drag: 0.6
        });
      }
    };
    ps.chips = (p, cnt, cols, dir, speed) => {
      for (let k = 0; k < cnt; k++) {
        const d = ball(1),
          s = (speed || 4) * rr(0.3, 1);
        ps.emit({
          p: V.add(p, V.mul(d, 0.15)),
          v: [(d[0] + (dir ? dir[0] : 0)) * s, Math.abs(d[1]) * s + 1.5, (d[2] + (dir ? dir[2] : 0)) * s],
          life: rr(0.7, 1.4),
          size: rr(0.05, 0.1),
          cols,
          grav: 16,
          bounce: 0.35,
          fade: 0.25
        });
      }
    };
    ps.ring = (p, r, cols, cnt, life) => {
      cnt = cnt || 40;
      for (let k = 0; k < cnt; k++) {
        const a = (k / cnt) * 6.283,
          s = r / (life || 0.5);
        ps.emit({
          p: [p[0], p[1] + 0.06, p[2]],
          v: [Math.cos(a) * s, 0, Math.sin(a) * s],
          life: life || 0.5,
          size: 0.07,
          cols,
          drag: 1.5,
          fade: 0.5,
          streak: 0.015
        });
      }
    };
    // lightning from a to b: a jagged line of short bright sticks that stays a moment and leaves a dimmer one
    ps.bolt = (a, b, cols, jag) => {
      const steps = Math.max(4, Math.ceil(V.dist(a, b) / 0.35));
      let prev = a;
      for (let k = 1; k <= steps; k++) {
        const t = k / steps,
          m = V.lerp(a, b, t),
          j = (jag === undefined ? 0.35 : jag) * Math.sin(Math.PI * t),
          q = k === steps ? b : [m[0] + rr(-j, j), m[1] + rr(-j, j), m[2] + rr(-j, j)],
          d = V.sub(q, prev),
          len = V.len(d) || 1e-3;
        ps.emit({
          p: V.lerp(prev, q, 0.5),
          life: 0.22,
          size: 0.045,
          cols,
          fixed: true,
          ax: V.mul(d, 1 / len),
          len: len * 0.55,
          fade: 0.6,
          alpha: 3
        });
        prev = q;
      }
    };
    ps.rain = (box, cnt, cols) => {
      for (let k = 0; k < cnt; k++)
        ps.emit({
          p: [rr(box[0], box[1]), box[3], rr(box[4], box[5])],
          v: [0.4, -rr(14, 18), 0],
          life: 1.2,
          size: 0.02,
          cols,
          streak: 0.02,
          fade: 0.1
        });
    };
    return ps;
  };
})(KIT);

// Prototype Symbiose → gaussian splats (ink-studio).
// Tige = VRAIE structure du moteur Python (tools/export_structure, Tomato 30 sem. d'été) ;
// rameaux, feuilles composées, grappes et tuteur = procédural (comme le fait la vue C#).
// Unité : 1 = 10 cm. Le moteur est Z-haut, ink-studio est Y-haut.
const fs = require('fs');
const path = require('path');
const STRUCT = JSON.parse(fs.readFileSync(path.join(__dirname, 'tomate.json'), 'utf8'));

module.exports = ({ makeBuilder, makeSculpt, KIT: K }) => ({
  id: 'tomate-symbiose',
  name: 'Tomate mûre (prototype splats)',
  seed: 42,
  build(seed) {
    const pal = [
      0x101a14, // 0 fond
      0x2a1d16, 0x4a3426, 0x6e5038, // 1-3 sol
      0x1f3a1f, 0x35602c, 0x56883a, // 4-6 tige
      0x173620, 0x2b622d, 0x4a923a, 0x8cc95a, // 7-10 feuille
      0x5e1414, 0x9c2420, 0xd8392a, 0xff7a55, // 11-14 rouge mûr
      0x3a5a20, 0x6fa040, 0xa9cf63, // 15-17 vert
      0xc8662a, 0xe8973f, // 18-19 tournant
      0xb39a22, 0xe8d24a, 0xfff2a0, // 20-22 fleur
      0x3b2a1a, 0x6b4b2e, 0x9a7448, // 23-25 bois
      0xf4f0d8 // 26 reflet
    ];
    const B = makeBuilder(seed, pal);
    const S = K.sculpt(makeSculpt(B));
    S.sun = K.V.norm([-0.55, 0.75, 0.45]);
    S.amb = 0.4; S.sky = 0.22; S.sunK = 0.6;

    const M = {
      sol: { r: [1, 2, 3] }, tige: { r: [4, 5, 6] }, feuille: { r: [7, 8, 9, 10] },
      mur: { r: [11, 12, 13, 14] }, tournant: { r: [11, 18, 19, 14] }, vert: { r: [15, 16, 17] },
      fleur: { r: [20, 21, 22] }, bois: { r: [23, 24, 25] }
    };
    const h = (i, j) => K.hash(seed, i, j); // aléa déterministe [0,1)
    const U = 0.1; // cm → unités
    const c0 = STRUCT.collet_cm;
    const P = v => [(v[0] - c0[0]) * U, v[2] * U, (v[1] - c0[1]) * U]; // moteur → ink
    const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
    const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
    const norm = K.V.norm;
    const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    const frame = (x, up) => { // repère (U,V,W) : U le long de x, V ~ up
      const X = norm(x), W = norm(cross(X, up)), Y = cross(W, X);
      return [X, Y, W];
    };

    // Sol paillé + tuteur.
    S.ground(M.sol, { rad: 3.2, res: 0.09 });
    const segs = STRUCT.segments.filter(s => s.length_cm > 0);
    const top = P(add(segs[segs.length - 1].base, mul(segs[segs.length - 1].dir, segs[segs.length - 1].length_cm)));
    S.tube([[0.28, -0.2, 0.05], [0.28, top[1] + 0.6, 0.05]], 0.07, 0.06, M.bois, { res: 0.03 });

    // Tige du moteur (épaisseur moteur = diamètre, ×2,5 pour lisibilité — à trancher).
    const tigePts = [P(segs[0].base), ...segs.map(s => P(add(s.base, mul(s.dir, s.length_cm))))];
    const r0 = segs[0].thickness_cm * U * 1.25, r1 = segs[segs.length - 1].thickness_cm * U * 1.25;
    S.tube(tigePts, r0, r1, M.tige, { res: 0.025 });
    const H = tigePts[tigePts.length - 1][1];
    const surTige = y => { // point de la tige à la hauteur y
      for (let i = 0; i < tigePts.length - 1; i++)
        if (y <= tigePts[i + 1][1]) {
          const t = (y - tigePts[i][1]) / Math.max(1e-6, tigePts[i + 1][1] - tigePts[i][1]);
          return add(tigePts[i], mul(add(tigePts[i + 1], mul(tigePts[i], -1)), t));
        }
      return tigePts[tigePts.length - 1];
    };

    // Feuille composée : pétiole arqué + folioles par paires + foliole terminale.
    function feuille(k, base, ang, long) {
      const out = [Math.cos(ang), 0, Math.sin(ang)];
      const pts = [];
      for (let i = 0; i <= 4; i++) {
        const t = i / 4;
        pts.push(add(base, [out[0] * long * t, 0.35 * long * t - 0.55 * long * t * t, out[2] * long * t]));
      }
      S.tube(pts, 0.025, 0.012, M.tige, { res: 0.02 });
      const nf = 4;
      for (let i = 1; i <= nf; i++) {
        const t = i / (nf + 0.6), p = pts[Math.round(t * 4)] || pts[4];
        const lat = norm(cross(out, [0, 1, 0]));
        for (const sgn of [-1, 1]) {
          const dir = norm(add(mul(lat, sgn), mul(out, 0.5)));
          const taille = 0.3 * (1.1 - 0.35 * t) * (0.85 + 0.3 * h(k * 31 + i, sgn + 2));
          const c = add(p, add(mul(dir, taille * 0.9), [0, -0.05 - 0.08 * h(k, i), 0]));
          S.ball(c, [taille, 0.022, taille * 0.55], M.feuille,
            { res: 0.03, ax: frame(dir, [0.1 * sgn, 1, 0.2]) });
          S.ball(add(p, add(mul(dir, 0.12), [0, -0.03, 0])), [0.08, 0.015, 0.05], M.feuille, { res: 0.025, ax: frame(dir, [0, 1, 0]) });
        }
      }
      const fin = pts[4];
      S.ball(add(fin, mul(out, 0.18)), [0.22, 0.022, 0.12], M.feuille, { res: 0.03, ax: frame(out, [0, 1, 0]) });
    }

    // Grappe : pédoncule qui pend + fruits en zigzag, maturité selon la hauteur.
    function grappe(k, base, ang, maturite) {
      const out = [Math.cos(ang), 0, Math.sin(ang)];
      const pts = [base, add(base, [out[0] * 0.25, 0.05, out[2] * 0.25]), add(base, [out[0] * 0.5, -0.25, out[2] * 0.5])];
      for (let i = 0; i < 5; i++) pts.push(add(pts[pts.length - 1], [out[0] * 0.2, -0.2, out[2] * 0.2]));
      S.tube(pts, 0.02, 0.012, M.tige, { res: 0.018 });
      const n = 6;
      for (let i = 0; i < n; i++) {
        const p = pts[2 + Math.min(i, pts.length - 3)];
        const lat = norm(cross(out, [0, 1, 0]));
        const sgn = i % 2 ? 1 : -1;
        const r = 0.27 * (1 - 0.12 * i) * (0.9 + 0.2 * h(k * 7 + i, 9));
        const c = add(p, add(mul(lat, sgn * r * 1.15), [0, -r * 0.95, 0]));
        const m = maturite - 0.18 * i; // le fruit de la base de la grappe mûrit en premier
        const mat = m > 0.66 ? M.mur : m > 0.33 ? M.tournant : M.vert;
        S.ball(c, [r, r * 0.86, r], mat, { res: 0.022 });
        // Calice : 5 sépales verts posés en étoile sur le fruit.
        for (let s = 0; s < 5; s++) {
          const a = (s / 5) * Math.PI * 2 + h(k, i + s);
          const d = [Math.cos(a), 0.15, Math.sin(a)];
          S.ball(add(c, [d[0] * 0.08, r * 0.86, d[2] * 0.08]), [0.09, 0.012, 0.025], M.feuille,
            { res: 0.014, ax: frame(d, [0, 1, 0]) });
        }
      }
    }

    function fleurs(k, base, ang) {
      const out = [Math.cos(ang), 0, Math.sin(ang)];
      const tip = add(base, [out[0] * 0.35, 0.12, out[2] * 0.35]);
      S.tube([base, tip], 0.015, 0.01, M.tige, { res: 0.015 });
      for (let i = 0; i < 4; i++) {
        const c = add(tip, [out[0] * 0.08 * i, -0.08 * i, (h(k, i) - 0.5) * 0.2]);
        for (let p = 0; p < 5; p++) {
          const a = (p / 5) * Math.PI * 2;
          const d = [Math.cos(a), -0.6, Math.sin(a)];
          S.ball(add(c, mul(d, 0.05)), [0.07, 0.01, 0.022], M.fleur, { res: 0.012, ax: frame(d, [0, 1, 0]) });
        }
      }
    }

    // Phyllotaxie 137,5° : une feuille tous les ~6 cm, une grappe toutes les 3 feuilles.
    const nNoeuds = Math.floor((H - 0.4) / 0.45);
    for (let k = 0; k < nNoeuds; k++) {
      const y = 0.4 + k * 0.45;
      const ang = k * 2.4 + 0.3;
      const base = surTige(y);
      feuille(k, base, ang, 1.5 - 0.6 * (k / nNoeuds));
      if (k >= 2 && (k - 2) % 3 === 0) {
        const haut = y / H;
        if (haut < 0.8) grappe(k, surTige(y + 0.25), ang + Math.PI, 1.1 - haut);
        else fleurs(k, surTige(y + 0.25), ang + Math.PI);
      }
    }
    // Apex : petites feuilles serrées.
    for (let i = 0; i < 3; i++) feuille(100 + i, surTige(H - 0.05), i * 2.1, 0.35);

    S.bake();
    return B.finish({
      cam: { target: [0, H * 0.48, 0], dist: 11, pitch: 0.25, yaw: 5.31 },
      detail: 20,
      dither: 0.25,
      radius: 4
    });
  }
});

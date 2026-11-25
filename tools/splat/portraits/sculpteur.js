// SYMBIOSE — tools/splat/portraits/sculpteur.js (sprint PRÉCUISSON SPLATS ⑥)
// POSER UNE PIÈCE DU JARDIN DANS UN PORTRAIT : les recettes des ②③ (feuilles, têtes,
// fruits) sont sculptées à leur ORIGINE (l'attache), l'organe vers +X, Y en haut. Un
// portrait les pose par dizaines, chacune déplacée, tournée, mise à l'échelle, et
// teinte en PLEINE COULEUR (pas en codes de palette indexée : un portrait est une
// illustration, conception §5).
//
// `place(S, Q, T, s)` rend un SCULPTEUR MANDATAIRE : mêmes méthodes que celui
// d'ink-studio (ball, tube, puff, lathe — les seules qu'emploient les recettes),
// qui transforment points, axes et rayons avant de les passer au vrai. La recette
// n'en sait rien : elle sculpte comme d'habitude.
//
// `res` (pas d'échantillonnage) a un PLANCHER `resMin` : une feuille de 10 cm vue à
// 3 px n'a pas besoin de splats de 2 mm (temps de cuisson borné, rendu identique).
//
// 📖 Pédagogie : c'est le patron « mandataire » (proxy) — un objet qui a la même
// interface qu'un autre et s'intercale. En C, ce serait une table de pointeurs de
// fonctions qui enrobe la vraie. La transformation est une similitude
// p ↦ s·Q·p + T (Q rotation 3×3 en colonnes, s échelle, T translation).
//
// Les recettes d'ORGANE (③) tassent leur verticale (× 0,816, oblique de la vue) ;
// `detasser` la rend : un portrait est une vraie vue 3D.

'use strict';

const { OBLIQUE } = require('../lib/organe');

const mulQ = (Q, v) => [
  Q[0][0] * v[0] + Q[1][0] * v[1] + Q[2][0] * v[2],
  Q[0][1] * v[0] + Q[1][1] * v[1] + Q[2][1] * v[2],
  Q[0][2] * v[0] + Q[1][2] * v[1] + Q[2][2] * v[2]
];

// Mandataire. Q = [X, Y, Z] colonnes (images des axes de la recette), T origine, s échelle.
function place(S, { Q, T, s, resMin = 0, detasser = false }) {
  const P = p => {
    const q = mulQ(Q, detasser ? [p[0], p[1] / OBLIQUE, p[2]] : p);
    return [T[0] + s * q[0], T[1] + s * q[1], T[2] + s * q[2]];
  };
  const r = v => (typeof v === 'function' ? t => s * v(t) : Array.isArray(v) ? v.map(x => s * x) : s * v);
  const opts = o => {
    if (!o) return { res: resMin };
    const c = { ...o, res: Math.max(resMin, (o.res || 0.02) * s) };
    if (o.ax) c.ax = o.ax.map(a => mulQ(Q, a));
    for (const k of ['maxRadius', 'width']) if (k in o) c[k] = s * o[k];
    return c;
  };
  return {
    ball(c, rad, mat, o) {
      const oo = opts(o);
      // ellipsoïde sans repère : ses axes sont ceux de la recette → les tourner aussi
      if (Array.isArray(rad) && !oo.ax) oo.ax = [mulQ(Q, [1, 0, 0]), mulQ(Q, [0, 1, 0]), mulQ(Q, [0, 0, 1])];
      return S.ball(P(c), r(rad), mat, oo);
    },
    tube(pts, r0, r1, mat, o) { return S.tube(pts.map(P), r(r0), r(r1), mat, opts(o)); },
    puff(loops, c, h, mat, o) { return S.puff(loops.map(l => l.map(([x, y]) => [s * x, s * y])), P(c), s * h, mat, opts(o)); },
    lathe(c, L, prof, mat, o) { return S.lathe(P(c), s * L, r(prof), mat, opts(o)); }
  };
}

// Repère d'une pièce : X = direction de l'organe, Y ≈ `haut` (orthonormé).
function repere(x, haut = [0, 1, 0]) {
  const n = v => { const l = Math.hypot(...v) || 1; return v.map(c => c / l); };
  const cr = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const X = n(x);
  let Z = cr(X, haut);
  if (Math.hypot(...Z) < 1e-6) Z = cr(X, [1, 0, 0]);
  Z = n(Z);
  return [X, cr(Z, X), Z];
}

// --- Couleurs ------------------------------------------------------------------
const hex = c => (typeof c === 'number' ? c : parseInt(String(c).replace('#', ''), 16));
const rgb = h => [(h >> 16) & 255, (h >> 8) & 255, h & 255];
const pack = ([r, g, b]) => (Math.round(r) << 16) | (Math.round(g) << 8) | Math.round(b);
const clamp = v => Math.max(0, Math.min(255, v));
// Mélange de deux couleurs (t = 0 → a).
const melange = (a, b, t) => pack(rgb(hex(a)).map((v, i) => v + (rgb(hex(b))[i] - v) * t));

// Palette d'un portrait : chaque couleur nommée devient une RAMPE de 4 crans
// (ombre profonde → reflet), comme les matériaux du prototype.
function palette(couleurs) {
  const pal = [0x101a14], M = {};
  for (const [nom, c] of Object.entries(couleurs)) {
    const [r, g, b] = rgb(hex(c));
    const crans = [0.45, 0.7, 1, 1.25].map(k => pack(k <= 1 ? [r * k, g * k, b * k]
      : [clamp(r + (255 - r) * 0.3), clamp(g + (255 - g) * 0.3), clamp(b + (255 - b) * 0.3)]));
    M[nom] = { r: crans.map((x, i) => pal.push(x) - 1) };
  }
  return { pal, M };
}

module.exports = { place, repere, palette, melange, hex };

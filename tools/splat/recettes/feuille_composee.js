// SYMBIOSE — tools/splat/recettes/feuille_composee.js (sprint PRÉCUISSON SPLATS ①)
// RECETTE d'une pièce : la FEUILLE COMPOSÉE (tomate, frêne, rosier…), reprise de
// la fonction `feuille` du prototype validé par Nico
// (docs/rendu/splatting/prototype/tomate.js) : pétiole arqué + 4 paires de
// folioles + une foliole terminale.
//
// Contrat d'une recette (lu par tools/splat/cuire.js) :
//   nom, rayonCm (rayon englobant depuis l'attache, borne la toile de rendu),
//   variantes (nombre de tirages au hash), sculpter(ctx) ; facultatifs (②) :
//   vue (noms de la vue servis), trous (degrés D5), tailles/lacets/inclinaisons.
//   ctx = { S, K, M, variante, inclinaison, trou } — S le sculpteur ink-studio, M.organe
//   le matériau (rampe des 3 tons de volume), inclinaison en radians (le bout de
//   la feuille relevé si > 0, tombant si < 0).
// L'ATTACHE (là où la feuille tient à sa tige) est l'ORIGINE : l'outil la
// projette pour écrire le point d'attache du manifeste.
//
// Unités ink-studio comme le prototype : 1 unité = 10 cm (les rayons d'occlusion
// d'ink-studio sont réglés pour cette échelle). Repère ink : Y en haut ; la
// feuille part vers +X (le lacet est donné par la caméra, pas par la recette).
//
// 📖 Pédagogie : une recette ne connaît NI le palier NI la caméra. Elle décrit
// l'objet en 3D, une fois ; l'outil le photographie sous chaque vue et à chaque
// zoom. C'est la séparation « modèle / rendu » : la même feuille servira demain
// à exporter des splats temps réel (vraie 3D), sans réécriture.
//
// Déterministe : tout aléa vient de K.hash(graine, i, j) (zéro Math.random).

'use strict';

const { percer } = require('../lib/trous');

// ② : moitié d'ellipse, pour situer bords et intérieur d'une foliole (trous D5).
const ELLIPSE = [[0, 0], [0.15, 0.71], [0.5, 1], [0.85, 0.71], [1, 0]];

const LONG = 1.5;          // longueur du pétiole (unités) — feuille basse du prototype
const NB_PAIRES = 4;       // paires de folioles le long du rachis

module.exports = {
  nom: 'feuille_composee',
  rayonCm: 21,
  variantes: 3,
  trous: true,
  vue: ['FormeFeuille.Composee', 'LeafShape.Composee'],
  sculpter({ S, K, M, variante, inclinaison, trou }) {
    const V = K.V;
    const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
    const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
    const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
    const frame = (x, up) => {
      const X = V.norm(x), W = V.norm(cross(X, up)), Y = cross(W, X);
      return [X, Y, W];
    };
    // Inclinaison = rotation autour de l'axe latéral (Z ink) passant par l'attache.
    const c = Math.cos(inclinaison), s = Math.sin(inclinaison);
    const R = p => [p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2]];
    const h = (i, j) => K.hash(1000 + variante, i, j);   // aléa de la variante
    const sites = [];   // folioles, pour les trous (②) — ne change rien à la sculpture

    const out = [1, 0, 0];
    const lat = [0, 0, 1];
    // Pétiole arqué (même courbe que le prototype), longueur modulée par variante.
    const long = LONG * (0.9 + 0.2 * h(0, 0));
    const pts = [];
    for (let i = 0; i <= 4; i++) {
      const t = i / 4;
      pts.push([long * t, 0.35 * long * t - 0.55 * long * t * t, 0]);
    }
    S.tube(pts.map(R), 0.025, 0.012, M.organe, { res: 0.02 });
    for (let i = 1; i <= NB_PAIRES; i++) {
      const t = i / (NB_PAIRES + 0.6), p = pts[Math.round(t * 4)] || pts[4];
      for (const sgn of [-1, 1]) {
        const dir = V.norm(add(mul(lat, sgn), mul(out, 0.5)));
        const taille = 0.3 * (1.1 - 0.35 * t) * (0.85 + 0.3 * h(i, sgn + 2));
        const ctr = add(p, add(mul(dir, taille * 0.9), [0, -0.05 - 0.08 * h(i, 7), 0]));
        const ax = frame(R(dir), R([0.1 * sgn, 1, 0.2]));
        S.ball(R(ctr), [taille, 0.022, taille * 0.55], M.organe, { res: 0.03, ax });
        sites.push({ c: add(R(ctr), mul(ax[0], -taille)), U: ax[0], V: ax[2], W: ax[1],
          long: 2 * taille, large: taille * 0.55, moitie: ELLIPSE });
        // Petite foliole intercalaire à l'aisselle (trait de la tomate).
        S.ball(R(add(p, add(mul(dir, 0.12), [0, -0.03, 0]))), [0.08, 0.015, 0.05], M.organe,
          { res: 0.025, ax: frame(R(dir), R([0, 1, 0])) });
      }
    }
    const fin = pts[4];
    const axT = frame(R(out), R([0, 1, 0]));
    S.ball(R(add(fin, mul(out, 0.18))), [0.22, 0.022, 0.12], M.organe, { res: 0.03, ax: axT });
    sites.push({ c: add(R(add(fin, mul(out, 0.18))), mul(axT[0], -0.22)), U: axT[0], V: axT[2], W: axT[1],
      long: 0.44, large: 0.12, moitie: ELLIPSE });
    percer({ S, K, M }, trou, sites, variante);
    return sites;   // RELIQUATS ③ : sites des détails (lib/details.js)
  }
};

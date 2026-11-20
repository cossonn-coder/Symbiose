// SYMBIOSE — tools/splat/lib/organe.js (sprint PRÉCUISSON SPLATS ③)
// Fabrique de RECETTES d'organes (têtes, fleurs, fruits, boutons, bois) et
// briques de sculpture communes. Pendant de lib/feuille.js pour ce qui n'est pas
// un limbe : pas de trous (D5 ne concerne que les feuilles), des COUCHES.
//
// COUCHES : un organe de plusieurs couleurs (pétales + cœur, disque + rayons,
// fruit + pédoncule) est cuit en une seule sculpture, mais chaque couche
// devient sa PROPRE pièce (même attache) : la vue pose une palette par couche
// (`modulate`), comme les pièces de fleur d'arbre d'aujourd'hui
// (PlantRenderer.PiecesFleur.cs, CouchePiece). `ctx.mat(k)` = matériau de la
// couche k (k = 0 par défaut) ; la recette déclare `couches: ['petales', 'coeur']`.
//
// OBLIQUE : la vue projette en oblique (verticales à l'échelle du sol), la
// caméra de cuisson en orthographique, qui grandit les verticales de 22 %
// (lib/iso.js, écart accepté au ① pour des feuilles couchées). Un épi, une
// gousse ou un tronc sont VERTICAUX : ici l'écart se voit (une gousse de 15 cm
// ferait 57 px au lieu de 47 à ×8). ③ corrige donc les POSITIONS et les AXES
// (`ctx.P` = inclinaison puis tassement vertical × cos 45° / cos 30° = 0,816) :
// la pièce tombe exactement sur la projection de la vue. Les RAYONS (une baie,
// un pétale) restent ronds : seul le squelette est tassé.
//
// 📖 Pédagogie : tasser l'axe vertical avant une projection orthographique,
// c'est fabriquer une projection oblique — la transformation linéaire est
// entièrement fixée par l'image des 3 axes (deux au sol, exacts ; le vertical,
// corrigé). C'est le principe d'une matrice : où vont les vecteurs de base.
//
// Déterministe : tout aléa vient de h(i, j) = K.hash(1000 + variante, i, j).

'use strict';

const { add, mul, cross, norm, cadre } = require('./limbe');

const CM = 0.1;                                            // 1 unité ink = 10 cm
const OBLIQUE = Math.cos(Math.PI / 4) / Math.cos(Math.PI / 6);   // 0,816
const INCLINAISONS = [-30, 0, 30];

// Repère [X, Y, W] d'un ellipsoïde : X le long de `x`, Y vers `haut`.
function repere(x, haut) {
  const X = norm(x), W = norm(cross(X, haut)), Y = cross(W, X);
  return [X, Y, W];
}

// Deux directions unitaires U, W perpendiculaires à `n` (et entre elles).
function perp(n) {
  const a = Math.abs(n[1]) < 0.9 ? [0, 1, 0] : [1, 0, 0];
  const W = norm(cross(n, a));
  return [cross(W, n), W];
}

// Recette d'organe. spec = { nom, rayonCm, vue, notes?, variantes?, couches?,
// lacets?, inclinaisons?, paliers?, tailles?, empriseCm?, sculpter(ctx, h) }.
// ctx reçoit P (point → incliné + oblique), R (direction → inclinée, sans
// tassement), mat(k) (matériau de la couche k) et h.
function recette(spec) {
  return {
    variantes: 3, inclinaisons: INCLINAISONS, ...spec, trous: false,
    sculpter(ctx) {
      const R = cadre(ctx.inclinaison);
      const P = p => { const q = R(p); return [q[0], q[1] * OBLIQUE, q[2]]; };
      const mat = (k = 0) => ctx.M.couches[k];
      const h = (i, j) => ctx.K.hash(1000 + ctx.variante, i, j);
      spec.sculpter({ ...ctx, R, P, mat }, h);
    }
  };
}

// Pétale (ou sépale, bractée) : ellipsoïde aplati de `long` × `large` × `epais`,
// la base en `base`, pointé selon `dir`, sa face tournée vers `haut`.
function petale(ctx, base, dir, long, large, epais, haut = [0, 1, 0], k = 0) {
  const ax = repere(ctx.R(dir), ctx.R(haut));
  const c = add(ctx.P(base), mul(ax[0], long / 2));
  ctx.S.ball(c, [long / 2, epais, large / 2], ctx.mat(k), { res: Math.min(0.02, large / 4), ax });
}

// Boule (fleuron, grain, baie) centrée en `c` (avant inclinaison).
function boule(ctx, c, r, k = 0, aplat = 1) {
  ctx.S.ball(ctx.P(c), aplat === 1 ? r : [r, r * aplat, r], ctx.mat(k), { res: Math.min(0.02, r / 3) });
}

// Tige / axe / pédicelle par une liste de points (avant inclinaison).
function tige(ctx, pts, r0, r1 = r0, k = 0) {
  const rRes = typeof r0 === 'function' ? r0(0.5) : r0;   // rayon fonction de 0..1 (gousse)
  ctx.S.tube(pts.map(ctx.P), r0, r1, ctx.mat(k), { res: Math.min(0.02, rRes * 1.2) });
}

// Petite corolle à 5 pétales ronds autour de `c`, face vers `haut` ; cœur en
// couche `kCoeur` (même couche que les pétales si non donnée).
function corolle(ctx, c, r, haut, phase, kCoeur = 0, coupe = 0.25) {
  const [U, W] = perp(haut);
  for (let i = 0; i < 5; i++) {
    const a = phase + (i * 2 * Math.PI) / 5;
    const d = norm(add(add(mul(U, Math.cos(a)), mul(W, Math.sin(a))), mul(haut, coupe)));
    petale(ctx, add(c, mul(d, r * 0.1)), d, r * 0.95, r * 0.75, r * 0.06 + 0.002, haut);
  }
  boule(ctx, add(c, mul(haut, r * 0.08)), r * 0.28, kCoeur, 0.7);
}

module.exports = { CM, OBLIQUE, INCLINAISONS, repere, perp, recette, petale, boule, tige, corolle, add, mul, norm, cross };

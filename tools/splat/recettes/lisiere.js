// SYMBIOSE — tools/splat/recettes/lisiere.js (sprint LISIÈRE & CHARGEMENT ①)
// Fabrique des pièces du KIT DE LA LISIÈRE (visuals/DecorLayer.Kit.cs, enum `Piece`) :
// les 10 formes posées au hash par le décor autour du jardin, sculptées en splats au lieu
// d'être peintes à la règle. Une recette par forme : recettes/lisiere_<forme>.js =
// require('./lisiere')('<forme>') (ce fichier-ci ne se cuit pas seul, comme touffe.js).
//
// CASES : chaque forme est cuite à ses TAILLES du décor (`Tailles` de DecorLayer.Kit.cs,
// recopiées dans BOITES ci-dessous — à garder en phase) × 3 variantes, une vue. cuire.js
// (`boites`) ajuste le zoom pour que la pièce REMPLISSE sa case sans la dépasser ;
// l'adaptateur visuals/DecorLayer.KitSplats.cs la pose pied en bas, centrée.
//
// RÉUTILISATION (les mots du jardin, conception §3.1) : la fleurette = la corolle de `fleuron` ; la ronce
// = `feuille_composee` posée le long de tiges arquées ; le sous-bois = `feuille_plume`
// (frondes) ; le bouquet feuillu = `feuille_ovale` en dôme ; le bouquet conifère =
// `rameau_aplati` en étages ; herbes et roseau = limbes en ruban (`lib/limbe.js`, l'arc de
// `feuille_ruban`). Neufs : galet (ellipsoïde poli), bloc anguleux (deux pavés), roseau.
// Les pièces du jardin sont posées par le SCULPTEUR MANDATAIRE des portraits
// (portraits/sculpteur.js `place`) : déplacées, tournées, mises à l'échelle.
//
// ÉPAISSEUR : à 4-25 px, un pixel couvre 2 à 8 cm ; un brin de 5 mm n'y laisse aucun
// pixel (règle « posé si la moitié du pixel est couverte », lib/codes.js). Les brins et
// tiges sont donc ÉLARGIS au regard du vrai : on cuit la silhouette lisible, pas le
// végétal au millimètre (la même règle que le kit à la règle qu'on remplace).
//
// Couches : `coeur` (fleur) et `massette` (roseau) sont des couches à part ; l'adaptateur
// leur donne leur ton propre (éclat jaune / creux brun), comme le dessin d'avant.
// Déterministe : tirages h(i, j) = K.hash(1000 + variante, i, j) seulement.
'use strict';
const { add, mul, limbe } = require('../lib/limbe');
const { CM, recette, boule, tige, corolle, norm } = require('../lib/organe');
const { place, repere } = require('../portraits/sculpteur');

const OR = 2.39996;   // angle d'or : rayons répartis sans motif

// = DecorLayer.Kit.cs `Tailles` (largeur, hauteur en px internes), même ordre.
const BOITES = {
  herbe: [[5, 4], [7, 6], [9, 7]],
  herbe_haute: [[5, 7], [7, 10], [9, 12]],
  fleur: [[3, 3]],
  roncier: [[7, 5], [11, 7], [15, 9]],
  sous_bois: [[7, 4], [11, 6], [15, 8]],
  feuillu: [[7, 6], [11, 9], [15, 12], [19, 15], [25, 20]],
  conifere: [[5, 7], [9, 11], [13, 15], [17, 19], [21, 25]],
  galet: [[3, 2], [5, 3], [7, 4]],
  bloc: [[5, 4], [7, 5], [11, 7]],
  roseau: [[4, 7], [5, 10], [7, 13]]
};

// Rotation autour de la verticale (a = 0 → +X, π/2 → +Z, comme limbe.direction).
const tourne = (v, a) => [v[0] * Math.cos(a) - v[2] * Math.sin(a), v[1], v[0] * Math.sin(a) + v[2] * Math.cos(a)];

// Pose une recette du jardin (feuille, rameau) : base T, direction `dir`, échelle s.
function poser(ctx, piece, T, dir, s, variante) {
  const S = place(ctx.S, { Q: repere(dir), T: ctx.P(T), s, resMin: 0.015 });
  piece.sculpter({ S, K: ctx.K, M: ctx.M, variante, inclinaison: 0, trou: null });
}

// BRIN en ruban : l'arc de feuille_ruban (monte puis retombe), en 4 tronçons de limbe,
// dans la direction a ; largeur pleine aux 2/3 puis effilée.
function brin(ctx, a, L, large, monte, retombe, base = [0, 0, 0]) {
  const p = t => add(base, tourne([L * t, L * (monte * t - retombe * t * t) * 0.5, 0], a));
  const w = t => (t < 0.66 ? 1 : Math.max(0.08, (1 - t) / 0.34));
  for (let k = 0; k < 4; k++) {
    const t0 = k / 4, t1 = Math.min(1, (k + 1.2) / 4), q0 = p(t0), q1 = p(t1);
    const d = [q1[0] - q0[0], q1[1] - q0[1], q1[2] - q0[2]], l = Math.hypot(...d);
    limbe(ctx, { base: q0, dir: mul(d, 1 / l), long: l, large, pli: 0.4,
      moitie: [[0, 0], [0, w(t0)], [1, w(t1)], [1, 0]] });
  }
}

// DÔME de `n` feuilles (une recette du jardin) sur un ellipsoïde de demi-axes `ray`,
// tournées vers l'extérieur, un peu tombantes ; un cœur plein dessous (pas de jour).
function dome(ctx, h, piece, n, ray, s) {
  const c = [0, ray[1] * 0.55, 0];
  boule(ctx, c, ray[0] * 0.8, 0, (ray[1] / ray[0]) * 0.8);
  for (let k = 0; k < n; k++) {
    const a = h(0, 0) * 6.28 + k * OR, el = Math.asin(Math.min(1, 0.15 + 0.85 * (k + 0.5) / n));
    const u = [Math.cos(a) * Math.cos(el), Math.sin(el), Math.sin(a) * Math.cos(el)];
    poser(ctx, piece, add(c, [u[0] * ray[0] * 0.6, u[1] * ray[1] * 0.6, u[2] * ray[2] * 0.6]),
      add(u, [0, -0.3, 0]), s * (0.8 + 0.4 * h(1, k)), k % 3);
  }
}

const FORMES = {
  // Touffe de prairie : 9 brins larges et courts, en éventail serré.
  herbe(ctx, h) {
    const ph = h(0, 0) * 6.28;
    for (let k = 0; k < 9; k++)
      brin(ctx, ph + k * OR, 14 * CM * (0.7 + 0.5 * h(1, k)), 1.6 * CM, 1.7 + 0.6 * h(2, k), 1.0 + 0.6 * h(3, k));
  },
  // Herbe haute de friche : longs brins qui VERSENT (la paille sèche qui se couche).
  herbe_haute(ctx, h) {
    const ph = h(0, 0) * 6.28;
    for (let k = 0; k < 13; k++)
      brin(ctx, ph + k * OR, 40 * CM * (0.7 + 0.4 * h(1, k)), 3.2 * CM, 3.4 + 0.8 * h(2, k), 1.2 + 1.0 * h(3, k));
  },
  // Fleurette de prairie : la corolle du fleuron (couches pétales | cœur), sa face TOURNÉE
  // vers l'œil (sud-est, au-dessus) — à plat, 3 px de large n'en feraient qu'un trait.
  fleur(ctx, h) {
    corolle(ctx, [0, 0, 0], 1.5 * CM * (0.9 + 0.2 * h(0, 0)), norm([0.5, 0.75, 0.5]), h(0, 1) * 6.28, 1, 0.15, 0.4);
  },
  // Roncier : un BUISSON bas en dôme de feuilles composées, d'où sortent 3 cannes arquées
  // qui replongent au sol (la ronce marcotte par le bout de ses tiges).
  roncier(ctx, h) {
    const fc = require('./feuille_composee'), ph = h(0, 0) * 6.28;
    dome(ctx, h, fc, 26, [30 * CM, 14 * CM, 30 * CM], 0.4);
    for (let k = 0; k < 3; k++) {
      const a = ph + k * 2.1, L = 45 * CM * (0.8 + 0.4 * h(1, k));
      const pt = t => tourne([L * t, 18 * CM + L * 0.5 * t * (1 - t) - 18 * CM * t * t, 0], a);
      tige(ctx, [0, 0.25, 0.5, 0.75, 1].map(pt), 1.4 * CM, 0.9 * CM);
      poser(ctx, fc, pt(0.7), [Math.cos(a + 1.3), 0.3, Math.sin(a + 1.3)], 0.4, k % 3);
    }
  },
  // Sous-bois : frondes plumeuses en rosette basse (fougère), qui se couchent.
  sous_bois(ctx, h) {
    const fp = require('./feuille_plume'), ph = h(0, 0) * 6.28;
    for (let k = 0; k < 8; k++) {
      const a = ph + k * OR;
      poser(ctx, fp, tourne([1.5 * CM, 0, 0], a), [Math.cos(a), 0.35 + 0.3 * h(1, k), Math.sin(a)],
        1.6 * (0.8 + 0.4 * h(2, k)), k % 3);
    }
  },
  // Bouquet feuillu : feuilles ovales posées sur un DÔME, tournées vers l'extérieur.
  feuillu(ctx, h) { dome(ctx, h, require('./feuille_ovale'), 22, [12 * CM, 12 * CM, 12 * CM], 0.9); },
  // Bouquet conifère : 4 étages de rameaux aplatis, de plus en plus courts vers le haut,
  // tombants, et une flèche (le sapin en étages, comme le sapin du jardin S2 ⑤).
  conifere(ctx, h) {
    const ra = require('./rameau_aplati'), H = 50 * CM;
    tige(ctx, [[0, 0, 0], [0, H, 0]], 1.2 * CM, 0.4 * CM);
    for (let e = 0; e < 4; e++) {
      const y = H * (0.12 + e * 0.22), s = 2.4 * (1 - e * 0.22), ph = h(0, e) * 6.28;
      for (let k = 0; k < 5; k++) {
        const a = ph + (k * 6.28) / 5;
        poser(ctx, ra, [0, y, 0], [Math.cos(a), -0.25, Math.sin(a)], s * (0.85 + 0.3 * h(1, e * 5 + k)), (e + k) % 3);
      }
    }
    poser(ctx, ra, [0, H * 0.85, 0], [0.05, 1, 0], 1.2, 0);   // la flèche
  },
  // Galet : ellipsoïde poli, couché, tourné au hash.
  galet(ctx, h) {
    const a = h(0, 0) * 6.28, r = 6 * CM;
    ctx.S.ball(ctx.P([0, r * 0.3, 0]), [r, r * 0.25, r * (0.5 + 0.2 * h(0, 1))], ctx.mat(0),
      { res: 0.03, ax: [tourne([1, 0, 0], a), [0, 1, 0], tourne([0, 0, 1], a)] });
  },
  // Bloc d'éboulis : deux pavés à arêtes vives (le second décalé, plus petit) → une pierre
  // ANGULEUSE à plusieurs faces, penchée au hash.
  bloc(ctx, h) {
    const a = h(0, 0) * 6.28, r = 12 * CM, pen = (h(0, 1) - 0.5) * 0.5;
    const ax = [tourne([Math.cos(pen), Math.sin(pen), 0], a), tourne([-Math.sin(pen), Math.cos(pen), 0], a), tourne([0, 0, 1], a)];
    ctx.S.box(ctx.P([0, r * 0.5, 0]), [r, r * 0.55, r * 0.75], ctx.mat(0), { res: 0.03, rd: r * 0.08, ax });
    const c2 = add([0, r * 0.4, 0], tourne([r * 0.6, 0, r * (0.3 + 0.4 * h(0, 2))], a + 0.6));
    ctx.S.box(ctx.P(c2), [r * 0.55, r * 0.45, r * 0.5], ctx.mat(0), { res: 0.03, rd: r * 0.06, ax: [ax[2], ax[1], mul(ax[0], -1)] });
  },
  // Roseau (massette) : 3 tiges droites, des feuilles en ruban qui montent, et une
  // massette brune (couche 1) en haut d'une tige sur deux.
  roseau(ctx, h) {
    const H = 120 * CM, ph = h(0, 0) * 6.28;
    for (let k = 0; k < 3; k++) {
      const pied = tourne([8 * CM, 0, 0], ph + k * 2.1), haut = H * (0.75 + 0.25 * h(1, k));
      const sommet = add(pied, [(h(2, k) - 0.5) * 10 * CM, haut, 0]);
      tige(ctx, [pied, sommet], 4 * CM, 3 * CM);
      if ((k + h(3, 0) * 2 | 0) % 2 === 0)
        tige(ctx, [add(pied, mul(add(sommet, mul(pied, -1)), 0.72)), add(pied, mul(add(sommet, mul(pied, -1)), 0.9))], 6 * CM, 6 * CM, 1);
      // Feuille DRESSÉE : portée courte (¼), montée forte → presque verticale, bout qui s'incline.
      brin(ctx, ph + k * 2.1 + 0.5, haut * 0.28, 5 * CM, 9, 2.5, pied);
    }
  }
};

module.exports = forme => recette({
  nom: 'lisiere_' + forme, rayonCm: { roseau: 140, galet: 10, bloc: 25, fleur: 2.5, herbe: 20, sous_bois: 35 }[forme] || 60, lacets: 1, inclinaisons: [0],
  couches: { fleur: ['petales', 'coeur'], roseau: ['tiges', 'massette'], conifere: ['aiguilles', 'stomates'] }[forme],
  boites: BOITES[forme], empriseCm: { fleur: 3, galet: 13, bloc: 30 }[forme] || 60,
  vue: ['DecorLayer Piece.' + forme],
  sculpter(ctx, h) { FORMES[forme](ctx, h); return []; }
});
module.exports.BOITES = BOITES;

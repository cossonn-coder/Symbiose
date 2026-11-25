// SYMBIOSE — tools/splat/lib/limbe.js (sprint PRÉCUISSON SPLATS ②)
// Le LIMBE : sculpter une lame de feuille en splats à partir d'un CONTOUR 2D, la
// brique commune de toutes les recettes de feuille (une recette = un contour +
// une disposition : folioles, doigts, pétiole…).
//
// Contour = sa MOITIÉ GAUCHE, comme `Symetrique(...)` de la vue
// (visuals/PlantRenderer.PortRosette.cs) : points (x le long de 0 base → 1 bout,
// y demi-largeur relative ≥ 0), de la base (0,0) au bout (1,0). Les contours des
// recettes sont RECOPIÉS de la vue (même dessin), le limbe les met en volume :
//   • chaque moitié est un COUSSIN mince (S.puff) : la normale se courbe au bord ;
//   • les deux moitiés sont relevées de `pli` autour de la nervure médiane (en V
//     ouvert vers le ciel) — la nervure devient une ARÊTE : deux faces, deux
//     orientations, lisible dès qu'une feuille fait quelques pixels ;
//   • `gaufre` : sillons creusés le long des nervures secondaires (marque de
//     relief, lisible ≥ ×16) ;
//   • `petiole` : tube de l'attache à la base du limbe.
// Retourne un SITE (repère + mesures) pour lib/trous.js (morsures, grêle).
//
// Repère ink : Y en haut. La recette donne `base` et `dir` AVANT inclinaison ;
// `ctx.R` (cadre(inclinaison)) tourne tout autour de l'axe latéral de l'attache.
//
// 📖 Pédagogie : S.puff est un « contour gonflé » — une SDF (distance signée)
// dont l'épaisseur suit la distance au bord. Le limbe n'est jamais une image :
// c'est un volume, photographié ensuite sous chaque vue.
//
// Déterministe : aucun aléa ici (la recette passe ses tirages K.hash).

'use strict';

const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = a => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
const tourner = (a, b, t) => add(mul(a, Math.cos(t)), mul(b, Math.sin(t)));   // a vers b de t

// Rotation d'inclinaison (autour de l'axe latéral Z ink passant par l'attache) :
// > 0 le bout relevé, < 0 tombant. Même formule que feuille_composee (①).
function cadre(inclinaison) {
  const c = Math.cos(inclinaison), s = Math.sin(inclinaison);
  return p => [p[0] * c - p[1] * s, p[0] * s + p[1] * c, p[2]];
}

// Direction horizontale d'angle `a` (radians, 0 = +X, π/2 = +Z ink = latéral),
// penchée de `penche` (radians, > 0 vers le haut).
const direction = (a, penche = 0) =>
  [Math.cos(a) * Math.cos(penche), Math.sin(penche), Math.sin(a) * Math.cos(penche)];

// Demi-largeur relative d'un contour (moitié) à l'abscisse t : max des segments
// qui la traversent (un contour lobé peut la traverser plusieurs fois).
function largeurA(moitie, t) {
  let y = 0;
  for (let i = 0; i + 1 < moitie.length; i++) {
    const [x0, y0] = moitie[i], [x1, y1] = moitie[i + 1];
    if ((t - x0) * (t - x1) > 0 || x0 === x1) continue;
    y = Math.max(y, y0 + ((y1 - y0) * (t - x0)) / (x1 - x0));
  }
  return y;
}

// Sculpte un limbe. o = { base, dir, haut?, long, large, moitie, epais?, pli?,
//   gaufre?, petiole?, res? } (unités ink ; `large` = demi-largeur max).
// Retourne le site { c, U, V, W, long, large, moitie } (déjà incliné).
function limbe(ctx, o) {
  const { S, M, R } = ctx;
  const res = o.res || 0.02, epais = o.epais || 0.022, pli = o.pli === undefined ? 0.2 : o.pli;
  let base = o.base;
  if (o.petiole) {
    const bout = add(base, mul(o.dir, o.petiole));
    S.tube([base, bout].map(R), 0.012, 0.009, M.organe, { res: 0.02 });
    base = bout;
  }
  // Repère du limbe : U le long, V latéral (vers +y du contour), W normale (ciel).
  const U = norm(R(o.dir)), W0 = norm(R(o.haut || [0, 1, 0]));
  const V = norm(cross(W0, U)), W = cross(U, V);
  const c = R(base);
  for (const sgn of [1, -1]) {
    // Moitié relevée de `pli` : son côté tourne vers le ciel autour de U.
    const Vs = mul(V, sgn), Vh = tourner(Vs, W, pli), Wh = tourner(W, mul(Vs, -1), pli);
    const boucle = o.moitie.map(([x, y]) => [x * o.long, y * o.large]);
    S.puff([boucle], c, epais, M.organe, { res, ax: [U, Vh, Wh] });
    if (o.gaufre) gaufrer(ctx, c, U, Vh, Wh, o, epais);
  }
  return { c, U, V, W, long: o.long, large: o.large, moitie: o.moitie, pli, epais };   // pli, epais : RELIQUATS ③ (lib/details.js)
}

// Gaufrage (ortie, menthe, consoude, tomate) : 3 sillons par moitié, de la
// nervure vers le bord en remontant, creusés dans la face du dessus — la même
// géométrie que PoserGaufrage de la vue (PlantRenderer.PortTigeFormes.cs).
function gaufrer(ctx, c, U, Vh, Wh, o, epais) {
  const { S, M } = ctx;
  const pt = (x, y) => add(c, add(mul(U, x * o.long), add(mul(Vh, y * o.large), mul(Wh, epais * 0.55))));
  for (let i = 1; i <= 3; i++) {
    const t = 0.15 + i * 0.18, w = largeurA(o.moitie, t + 0.15);
    if (w <= 0.05) continue;
    S.tube([pt(t, 0.05), pt(t + 0.08, w * 0.4), pt(t + 0.15, w * 0.8)], epais * 0.45, epais * 0.3,
      M.organe, { res: 0.012, neg: true });
  }
}

module.exports = { add, mul, cross, norm, tourner, cadre, direction, largeurA, limbe };

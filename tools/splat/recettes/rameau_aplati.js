// SYMBIOSE — tools/splat/recettes/rameau_aplati.js (sprint LISIÈRE & CHARGEMENT ①, décision L4)
// RAMEAU APLATI du SAPIN (Abies) : un rameau et deux ramilles latérales, garnis d'aiguilles
// PLATES rangées sur DEUX RANGS de part et d'autre de l'axe (« pectinées », en peigne), un
// peu relevées en V ouvert vers le ciel. Face du dessus vert sombre luisant ; DESSOUS, deux
// bandes de stomates argentées — la couche « stomates » (une palette claire à part pour
// la vue) est un second limbe à peine plus bas : on ne la voit qu'au bord et quand le
// rameau se relève (inclinaison +30°), comme sur l'arbre.
// Sert : le bouquet `Conifere` du kit de la lisière (recettes/lisiere.js, ①) ET les
// aiguilles du sapin du jardin aux paliers ×8-×32 (②).
//
// 📖 Pédagogie (botanique) : chez le sapin, chaque aiguille est attachée seule, par une
// petite ventouse ; elles poussent tout autour du rameau mais se TORDENT à la base pour
// se mettre à plat, à la lumière — d'où le rameau « aplati », typique des arbres d'ombre
// qui étalent leur surface (l'épicéa, arbre de lumière, garde ses aiguilles en goupillon).
// Le dessous argenté = les stomates, les pores par où la feuille respire.
//
// Contrat : celui des organes (lib/organe.js) ; l'attache = la base du rameau, l'organe
// vers +X. Déterministe : tirages h(i, j) seulement.
'use strict';
const { CM, recette, petale, tige, add, mul, norm, cross } = require('../lib/organe');

const LONG = 9 * CM, AIGUILLE = 2.4 * CM, PAS = 0.42 * CM;
const LARGE = 0.26 * CM, EPAIS = 0.05 * CM;
const AVANT = 0.35, RELEVE = 0.18;   // aiguille penchée vers le bout (rad) et relevée (V)

// Un axe de `a` à `b`, garni d'aiguilles sur ses deux flancs ; `g` = graine du tirage.
function axeGarni(ctx, h, a, b, g, r0) {
  tige(ctx, [a, b], r0, r0 * 0.6);
  const d = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], L = Math.hypot(...d), u = norm(d);
  const lat = norm(cross(u, [0, 1, 0]));   // latéral horizontal
  const n = Math.max(2, Math.floor(L / PAS));
  for (let i = 0; i < n; i++) {
    const t = (i + 0.5) / n, p = add(a, mul(d, t));
    for (const sgn of [1, -1]) {
      const long = AIGUILLE * (1 - 0.3 * t) * (0.85 + 0.3 * h(g + i, sgn > 0 ? 1 : 2));
      const dir = norm(add(add(mul(lat, sgn * Math.cos(AVANT)), mul(u, Math.sin(AVANT))), [0, RELEVE, 0]));
      petale(ctx, p, dir, long, LARGE, EPAIS, [0, 1, 0], 0);
      petale(ctx, add(p, [0, -EPAIS * 0.9, 0]), dir, long * 0.96, LARGE * 0.8, EPAIS * 0.8, [0, 1, 0], 1);
    }
  }
}

module.exports = recette({
  nom: 'rameau_aplati', rayonCm: 12, couches: ['aiguilles', 'stomates'],
  vue: ['Sapin rameau aplati (lisière Conifere, sapin du jardin ×8-×32)'],
  sculpter(ctx, h) {
    const L = LONG * (0.9 + 0.2 * h(0, 0)), chute = -0.12 * L * (0.5 + h(0, 1));
    const bout = [L, chute, 0];
    axeGarni(ctx, h, [0, 0, 0], bout, 10, 0.22 * CM);
    // Deux ramilles alternes, à 35 % et 65 % du rameau, ouvertes à ~45°.
    [[0.35, 1], [0.65, -1]].forEach(([t, sgn], k) => {
      const p = mul(bout, t), l = L * (0.45 - 0.12 * k) * (0.85 + 0.3 * h(1, k));
      const q = add(p, [l * 0.7, chute * 0.3, sgn * l * 0.7]);
      axeGarni(ctx, h, p, q, 40 + 30 * k, 0.15 * CM);
    });
    return [];
  }
});

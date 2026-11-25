// SYMBIOSE — tools/splat/lib/feuille.js (sprint PRÉCUISSON SPLATS ②)
// Fabrique de RECETTES de feuille : une feuille SIMPLE (un limbe, un pétiole
// facultatif) se décrit par une fiche — contour, longueur, largeur — et cette
// fabrique en fait une recette au contrat de tools/splat/cuire.js. Les feuilles
// à plusieurs limbes (composée, palmée, triade, plume) écrivent leur `sculpter`
// elles-mêmes avec lib/limbe.js, et passent par `recette` pour le reste.
//
// Ce qui varie au hash d'une variante à l'autre (zéro aléa vivant) : longueur et
// largeur ±10 %, courbure (le bout retombe plus ou moins), léger vrillage.
//
// `vue` : les noms de la vue que la recette sert (table « nom vue → recette »
// écrite dans le manifeste, à l'usage du ④) — ex. 'FormeFeuille.Ovale'.
//
// 📖 Pédagogie : c'est une « fabrique » au sens du patron de conception : on
// écrit les DONNÉES d'une feuille, le code commun la sculpte. Quinze feuilles ne
// font pas quinze copies du même code.

'use strict';

const { cadre, direction, limbe } = require('./limbe');
const { percer } = require('./trous');

const CM = 0.1;   // 1 unité ink = 10 cm (iso.CM_PAR_UNITE)

// Recette complète à partir d'un `sculpter(ctx, h)` qui retourne ses sites de trous.
// ctx reçoit R (cadre d'inclinaison) ; h(i, j) = aléa de la variante.
function recette({ nom, rayonCm, vue, notes, variantes = 3, sculpter }) {
  return {
    nom, rayonCm, variantes, vue, notes, trous: true,
    sculpter(ctx) {
      const c = { ...ctx, R: cadre(ctx.inclinaison) };
      const h = (i, j) => ctx.K.hash(1000 + ctx.variante, i, j);
      const sites = sculpter(c, h);
      percer(c, ctx.trou, sites, ctx.variante);
      return sites;   // RELIQUATS ③ : sites des détails (lib/details.js)
    }
  };
}

// Feuille simple. spec = { nom, vue, moitie, longCm, large (demi-largeur /
// longueur), petioleCm?, pli?, gaufre?, epaisCm?, penche? (rad, bout vers le bas) }.
function simple(spec) {
  const long = spec.longCm * CM, petiole = (spec.petioleCm || 0) * CM;
  const r = recette({
    nom: spec.nom, vue: spec.vue, notes: spec.notes,
    rayonCm: Math.ceil((spec.longCm + (spec.petioleCm || 0)) * 1.08 + 1),
    sculpter(ctx, h) {
      const l = long * (0.9 + 0.2 * h(0, 0));
      const penche = -(spec.penche === undefined ? 0.12 : spec.penche) * (0.6 + 0.8 * h(0, 1));
      const vrille = (h(0, 2) - 0.5) * 0.3;
      return [limbe(ctx, {
        base: [0, 0, 0], dir: direction(0, penche), haut: [0, Math.cos(vrille), Math.sin(vrille)],
        long: l, large: l * spec.large * (0.9 + 0.2 * h(0, 3)), moitie: spec.moitie,
        petiole: petiole * (0.9 + 0.2 * h(0, 4)), pli: spec.pli, gaufre: spec.gaufre,
        epais: spec.epaisCm ? spec.epaisCm * CM : undefined
      })];
    }
  });
  r.spec = spec;   // relu par les touffes (recettes/touffe.js)
  return r;
}

module.exports = { CM, recette, simple };

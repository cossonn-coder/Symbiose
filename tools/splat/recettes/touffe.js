// SYMBIOSE — tools/splat/recettes/touffe.js (sprint PRÉCUISSON SPLATS ②)
// Fabrique des TOUFFES du kit des paliers bas (×0,5 · ×1 · ×2, décision D4) :
// quelques feuilles d'une forme rayonnant d'un point — le bout d'un rameau — à la
// place des touffes dessinées à la règle de PlantRenderer.Kit.cs. Une touffe par
// `LeafShape` (6), cuite aux 4 TAILLES du kit (3, 5, 7, 9 px internes, `tailles`)
// × 3 variantes, une seule vue (comme le kit : une touffe n'a pas de sens).
// Les feuilles sont celles des recettes de feuille (mêmes contours) : la touffe
// est « construite à partir des feuilles ».
// Usage : recettes/touffe_<forme>.js = require('./touffe')('<forme>').
'use strict';
const { add, mul, direction, limbe } = require('../lib/limbe');
const { recette, CM } = require('../lib/feuille');

const R_CM = 6;   // rayon de la touffe : la largeur cuite est fixée par `tailles`
const OR = 2.39996;   // angle d'or : feuilles réparties sans motif

// forme → [recette de feuille (contour), nombre, longueur relative, montée (rad),
// emprise] ; emprise = largeur vue / diamètre, MESURÉE sur une 1re cuisson pour
// que la pièce fasse bien sa taille du kit (une touffe dressée est plus étroite).
const FORMES = {
  elliptique: ['feuille_ovale', 5, 0.85, 0.6, 1],
  cordee: ['feuille_coeur', 4, 0.8, 0.6, 0.9],
  lanceolee: ['feuille_lanceolee', 4, 1, 1.0, 0.75],
  lobee: ['feuille_paume', 3, 0.7, 0.5, 0.9],
  composee: ['feuille_composee', 4, 1, 0.6, 1.4],
  aciculaire: ['feuille_aiguille', 8, 0.8, 0.7, 0.8]
};
const KIT = { elliptique: 'Elliptique', cordee: 'Cordee', lanceolee: 'Lanceolee', lobee: 'Lobee',
  composee: 'Composee', aciculaire: 'Aciculaire' };

// Mini feuille composée de touffe : rachis + 3 paires de folioles ovales.
function composee(ctx, base, dir, L, ovale) {
  ctx.S.tube([base, add(base, mul(dir, L))].map(ctx.R), 0.008, 0.005, ctx.M.organe, { res: 0.01 });
  for (let i = 0; i < 3; i++)
    for (const a of [0.9, -0.9]) {
      const d = [dir[0] * Math.cos(a) - dir[2] * Math.sin(a), dir[1], dir[0] * Math.sin(a) + dir[2] * Math.cos(a)];
      limbe(ctx, { base: add(base, mul(dir, L * (0.25 + i * 0.25))), dir: d, long: L * 0.45 * (1 - i * 0.15),
        large: L * 0.2, moitie: ovale, pli: 0.15 });
    }
  limbe(ctx, { base: add(base, mul(dir, L)), dir, long: L * 0.4, large: L * 0.18, moitie: ovale, pli: 0.15 });
}

module.exports = forme => {
  const [nomFeuille, nb, rel, monte, emprise] = FORMES[forme];
  const spec = require('./' + nomFeuille).spec;
  const ovale = require('./feuille_ovale').spec.moitie;
  return Object.assign(recette({
    nom: 'touffe_' + forme, rayonCm: R_CM, vue: ['Kit LeafShape.' + KIT[forme]],
    sculpter(ctx, h) {
      const phase = h(0, 0) * 2 * Math.PI, L = R_CM * CM * rel;
      for (let k = 0; k < nb; k++) {
        const a = phase + k * OR, l = L * (0.8 + 0.25 * h(1, k));
        const dir = direction(a, monte * (0.3 + 1.4 * h(2, k))), base = mul(direction(a, 0), 0.008);
        if (forme === 'aciculaire')
          ctx.S.tube([base, add(base, mul(dir, l))].map(ctx.R), 0.01, 0.005, ctx.M.organe, { res: 0.006 });
        else if (forme === 'composee') composee(ctx, base, dir, l, ovale);
        else limbe(ctx, { base, dir, long: l, large: l * spec.large, moitie: spec.moitie, pli: spec.pli });
      }
      return [];
    }
  }), { trous: false, tailles: [3, 5, 7, 9], lacets: 1, inclinaisons: [0], empriseCm: 2 * R_CM * emprise });
};

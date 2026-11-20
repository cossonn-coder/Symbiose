// SYMBIOSE — tools/splat/recettes/feuille_palmee.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE PALMÉE, À DOIGTS (chanvre, figuier des rameaux : 7 doigts étroits en
// éventail, le médian le plus long). Disposition de PoserPalmee
// (PlantRenderer.PortTigeFormes.cs) : écart ±1,35 rad, longueur 1 − 0,45 |e|.
'use strict';
const { add, mul, direction, limbe } = require('../lib/limbe');
const { recette, CM } = require('../lib/feuille');
const LANCE = require('./feuille_lanceolee').spec.moitie;

const LONG = 15 * CM, PETIOLE = 6 * CM, DOIGTS = 7, LARGE = 0.13;

module.exports = recette({
  nom: 'feuille_palmee', rayonCm: 24, vue: ['FormeFeuille.Palmee'],
  sculpter(ctx, h) {
    const L = LONG * (0.9 + 0.2 * h(0, 0)), pet = PETIOLE * (0.9 + 0.2 * h(0, 1));
    const centre = mul(direction(0, 0.15), pet);
    ctx.S.tube([[0, 0, 0], centre].map(ctx.R), 0.014, 0.01, ctx.M.organe, { res: 0.02 });
    const sites = [];
    for (let i = 0; i < DOIGTS; i++) {
      const e = (i - (DOIGTS - 1) / 2) / ((DOIGTS - 1) / 2);
      const l = L * (1 - 0.45 * Math.abs(e)) * (0.92 + 0.16 * h(1, i));
      sites.push(limbe(ctx, {
        base: centre, dir: direction(e * 1.35, -0.12 - 0.12 * Math.abs(e) - 0.08 * h(2, i)),
        long: l, large: l * LARGE, moitie: LANCE, pli: 0.25
      }));
    }
    return sites;
  }
});

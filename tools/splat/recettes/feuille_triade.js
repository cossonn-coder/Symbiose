// SYMBIOSE — tools/splat/recettes/feuille_triade.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE TRIFOLIOLÉE (haricot : pétiole, deux folioles latérales écartées, la
// centrale plus loin). Disposition de PoserTriade (PlantRenderer.PortVolubile.cs),
// folioles au ContourCoeur de la vue.
'use strict';
const { add, mul, direction, limbe } = require('../lib/limbe');
const { recette, CM } = require('../lib/feuille');
const COEUR = require('./feuille_coeur').spec.moitie;

const LONG = 14 * CM, LARGE = 0.42;

module.exports = recette({
  nom: 'feuille_triade', rayonCm: 13, vue: ['FormeFeuille.Triade'],
  sculpter(ctx, h) {
    const L = LONG * (0.9 + 0.2 * h(0, 0)), l = L * 0.62, d0 = direction(0, -0.1);
    const centre = mul(d0, 0.42 * L);
    const sites = [];
    ctx.S.tube([[0, 0, 0], centre].map(ctx.R), 0.012, 0.009, ctx.M.organe, { res: 0.02 });
    [[1.35, 0.9], [-1.35, 0.9], [0, 1]].forEach(([a, k], i) => {
      const ll = l * k * (0.9 + 0.2 * h(1, i));
      sites.push(limbe(ctx, {
        base: add(centre, mul(direction(a, 0), 0.01)), dir: direction(a, -0.15 - 0.1 * h(2, i)),
        long: ll, large: ll * LARGE, moitie: COEUR, petiole: 0.008
      }));
    });
    return sites;
  }
});

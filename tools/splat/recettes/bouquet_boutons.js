// SYMBIOSE — tools/splat/recettes/bouquet_boutons.js (sprint BOIS & ARBRES ④)
// BOUQUET DE BOUTONS d'un arbre fruitier au palier ×4 (montée de la floraison) : même dôme que
// bouquet_corolles, mais des boutons fermés (ovoïdes) — PoserBouquetsArbre
// (PlantRenderer.BouquetsArbre.cs). Une couche, teinte du bouton de l'espèce (rose franc chez le
// pommier, blanc verdâtre chez le cerisier, FleursArbre.cs). Bouton relevé comme la fleur :
// 0,9 cm de rayon au lieu de 0,6 (recette `bouton`), sinon 2 px à ×4.
'use strict';
const { CM, recette, add, mul, norm } = require('../lib/organe');
module.exports = recette({
  nom: 'bouquet_boutons', rayonCm: 10, couches: ['petales'],
  lacets: 4, inclinaisons: [0], paliers: [4],
  vue: ['BouquetsArbre (boutons, ×4)'],
  sculpter(ctx, h) {
    const R = 7 * CM * (0.9 + 0.2 * h(0, 0)), n = 11, c0 = [0, 0.35 * R, 0];
    for (let i = 0; i < n; i++) {
      const a = i * 2.39996 + h(1, i), e = 1.45 * Math.sqrt((i + 0.5) / n);
      const d = norm([Math.cos(a) * Math.sin(e), Math.cos(e), Math.sin(a) * Math.sin(e)]);
      const r = 0.9 * CM * (0.85 + 0.3 * h(2, i)), p = ctx.P(add(c0, mul(d, 0.55 * R)));
      ctx.S.ball(p, [0.5 * r, 0.75 * r, 0.5 * r], ctx.mat(0), { res: 0.004 });
    }
  }
});

// SYMBIOSE — tools/splat/recettes/fruit_globe.js (sprint PRÉCUISSON SPLATS ③)
// FRUIT ROND : le globe de la vue (DrawFruits ×8, PoserFruit `Allonge` ≤ 1, fruits
// d'arbre) — tomate, poivron, fraise, pomme, cerise, figue, noix, gland… Cuit UNE
// fois : la maturité (vert → mûr → brun) est la palette, pas l'image (conception §3).
// Attache = CENTRE du fruit (le point où la vue centre son disque). Couche 1 = le
// pédoncule. Symétrie de révolution : une seule vue (1 lacet, inclinaison 0).
// Rayon nominal 2 cm (fiches : cerise 1, gland 1, noix 2,2, pomme 3,5).
'use strict';
const { CM, recette, tige } = require('../lib/organe');
module.exports = recette({
  nom: 'fruit_globe', rayonCm: 3.5, couches: ['fruit', 'pedoncule'], lacets: 1, inclinaisons: [0],
  vue: ['DrawFruits (globe ×8)', 'PoserFruit (Allonge <= 1)', 'DrawFruitsHouppier'],
  sculpter(ctx, h) {
    const r = 2 * CM * (0.95 + 0.1 * h(0, 0)), ry = r * (0.86 + 0.12 * h(0, 1));
    ctx.S.ball(ctx.P([0, 0, 0]), [r, ry, r * (0.96 + 0.08 * h(0, 2))], ctx.mat(0), { res: 0.012 });
    ctx.S.ball(ctx.P([0, ry, 0]), [0.3 * r, 0.25 * r, 0.3 * r], ctx.mat(0), { res: 0.01, neg: true });   // cuvette
    const t = (h(0, 3) - 0.5) * 0.6 * CM;
    tige(ctx, [[0, ry * 0.8, 0], [t, ry + 0.5 * CM, 0], [t * 2, ry + 0.9 * CM, 0.1 * CM]], 0.1 * CM, 0.07 * CM, 1);
  }
});

// SYMBIOSE — tools/splat/recettes/fruit_long.js (sprint PRÉCUISSON SPLATS ③)
// FRUIT LONG couché (courgette) — PoserFruit avec `Allonge` > 1 (PlantRenderer.Ports.cs) :
// cylindre arrondi aux deux bouts, côtes peu marquées, légère courbure. Cuit UNE fois
// (maturité = palette). Attache = CENTRE (la vue centre sa capsule sur le point du
// fruit) ; le fruit part vers ±X. Couche 1 = pédoncule. Nominal (fiche courgette) :
// rayon 3,2 cm, `Allonge` 3 → 16 cm de bout en bout (r × allonge + 2 r).
'use strict';
const { CM, recette, tige } = require('../lib/organe');
module.exports = recette({
  nom: 'fruit_long', rayonCm: 10, couches: ['fruit', 'pedoncule'], inclinaisons: [-15, 0, 15],
  vue: ['PoserFruit (Allonge > 1)'],
  sculpter(ctx, h) {
    const r = 3.2 * CM * (0.92 + 0.16 * h(0, 0)), demi = 1.5 * r, arc = 0.15 * r * (h(0, 1) - 0.3);
    const axe = t => [demi * (2 * t - 1), arc * (1 - (2 * t - 1) ** 2), 0];
    const pts = Array.from({ length: 9 }, (_, k) => axe(k / 8));
    tige(ctx, pts, 0.92 * r, 1.02 * r);
    for (const t of [0, 1]) ctx.S.ball(ctx.P(axe(t)), t ? 1.0 * r : 0.9 * r, ctx.mat(0), { res: 0.012 });
    for (let i = 0; i < 6; i++) {                          // côtes : sillons longitudinaux
      const a = (i * Math.PI) / 3 + 0.3 * h(1, i), dy = Math.cos(a) * r * 1.03, dz = Math.sin(a) * r * 1.03;
      ctx.S.tube(pts.slice(1, 8).map(p => ctx.P([p[0], p[1] + dy, p[2] + dz])), 0.12 * r, 0.12 * r, ctx.mat(0),
        { res: 0.01, neg: true });
    }
    const b = axe(0);
    tige(ctx, [[b[0] - 0.8 * r, b[1], 0], [b[0] - 1.2 * r, b[1] + 0.15 * r, 0]], 0.2 * r, 0.16 * r, 1);
  }
});

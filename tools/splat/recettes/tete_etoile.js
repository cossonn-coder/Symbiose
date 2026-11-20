// SYMBIOSE — tools/splat/recettes/tete_etoile.js (sprint PRÉCUISSON SPLATS ③)
// ÉTOILE à 5 pointes et cône sombre d'étamines (bourrache, poivron) — PoserEtoile
// (PlantRenderer.PortTigeFormes.cs). Fleur penchée de côté (la bourrache retombe).
// Une couche : le cœur sombre de la vue est le ton 0 de la même rampe (ici le creux).
// Rayon nominal 2,5 cm (fiches : poivron 2, bourrache 3).
'use strict';
const { CM, recette, petale, tige, perp, add, mul, norm } = require('../lib/organe');
module.exports = recette({
  nom: 'tete_etoile', rayonCm: 4,
  vue: ['FormeTete.Etoile'],
  sculpter(ctx, h) {
    const r = 2.5 * CM * (0.9 + 0.2 * h(0, 0));
    const n = norm([0.75, 0.65, 0.1 * (h(0, 1) - 0.5)]), [U, W] = perp(n);
    const c = mul(n, 0.3 * r);
    tige(ctx, [[0, 0, 0], c], 0.06 * r, 0.1 * r);
    const phase = h(0, 2) * 2 * Math.PI;
    for (let i = 0; i < 5; i++) {
      const a = phase + (i * 2 * Math.PI) / 5;
      const d = norm(add(add(mul(U, Math.cos(a)), mul(W, Math.sin(a))), mul(n, -0.12)));
      petale(ctx, add(c, mul(d, 0.08 * r)), d, r * 0.95, r * 0.36, 0.03 * r + 0.002, n);
    }
    // Cône d'étamines pointé hors de la fleur.
    ctx.S.lathe(ctx.P(c), 0.45 * r, [0.22 * r, 0.04 * r], ctx.mat(0), { res: 0.008, ax: [ctx.R(U), ctx.R(n), ctx.R(W)] });
  }
});

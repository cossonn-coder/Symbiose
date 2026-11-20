// SYMBIOSE — tools/splat/recettes/tete_trompette.js (sprint PRÉCUISSON SPLATS ③)
// TROMPETTE (fleur de courgette) — PoserTrompette (PlantRenderer.PortRampante.cs) :
// cornet évasé creux, pavillon à 5 lobes ; le fond orangé de la vue = le creux (ton 0
// par occlusion). Une couche. Rayon nominal 5 cm (fiche courgette).
'use strict';
const { CM, recette, petale, perp, add, mul, norm } = require('../lib/organe');
module.exports = recette({
  nom: 'tete_trompette', rayonCm: 10,
  vue: ['FormeTete.Trompette'],
  sculpter(ctx, h) {
    const r = 5 * CM * (0.9 + 0.2 * h(0, 0)), n = norm([0.55, 0.85, 0.15 * (h(0, 1) - 0.5)]), [U, W] = perp(n);
    const ax = [ctx.R(U), ctx.R(n), ctx.R(W)], L = 1.1 * r;
    const evase = t => 0.12 * r + 0.42 * r * t * t;
    ctx.S.lathe(ctx.P([0, 0, 0]), L, evase, ctx.mat(0), { res: 0.015, ax, maxRadius: 0.55 * r });
    ctx.S.lathe(ctx.P(mul(n, 0.25 * r)), L, t => Math.max(0.01, evase(0.25 + 0.75 * t) - 0.05 * r), ctx.mat(0),
      { res: 0.015, ax, neg: true, maxRadius: 0.55 * r });
    const bord = mul(n, L * 0.95), phase = h(0, 2) * 6.28;
    for (let i = 0; i < 5; i++) {
      const a = phase + (i * 2 * Math.PI) / 5;
      const d = norm(add(add(mul(U, Math.cos(a)), mul(W, Math.sin(a))), mul(n, 0.35)));
      petale(ctx, add(bord, mul(d, 0.1 * r)), d, r * 0.65, r * 0.75, 0.03 * r, norm(add(n, mul(d, -0.5))));
    }
  }
});

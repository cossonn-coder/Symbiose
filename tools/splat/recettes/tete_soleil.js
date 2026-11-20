// SYMBIOSE — tools/splat/recettes/tete_soleil.js (sprint PRÉCUISSON SPLATS ③)
// SOLEIL (tournesol) — PoserSoleil (PlantRenderer.PortTigeFormes.cs) : tête penchée,
// couronne de rayons (couche 0), disque de graines en spirale d'or (couche 1 = cœur,
// FruitRipe côté vue ; seul le disque reste quand la tête est fanée), dos vert à
// bractées (couche 2 = revers, teinte du feuillage). Rayon nominal 12,5 cm (fiche).
'use strict';
const { CM, recette, petale, tige, perp, add, mul, norm } = require('../lib/organe');
const OR = 2.39996;
module.exports = recette({
  nom: 'tete_soleil', rayonCm: 22, couches: ['rayons', 'coeur', 'revers'],
  vue: ['FormeTete.Soleil'],
  sculpter(ctx, h) {
    const r = 12.5 * CM * (0.92 + 0.16 * h(0, 0));
    const n = norm([0.85, 0.4 + 0.2 * h(0, 1), 0]), [U, W] = perp(n);
    const c = add([0.12 * r, 0.25 * r, 0], mul(n, 0.1 * r));
    const ax = [ctx.R(U), ctx.R(n), ctx.R(W)];
    tige(ctx, [[0, 0, 0], [0.05 * r, 0.2 * r, 0], add(c, mul(n, -0.1 * r))], 0.06 * r, 0.08 * r, 2);
    ctx.S.ball(ctx.P(add(c, mul(n, -0.08 * r))), [0.6 * r, 0.12 * r, 0.6 * r], ctx.mat(2), { res: 0.03, ax });   // dos
    ctx.S.ball(ctx.P(c), [0.56 * r, 0.06 * r, 0.56 * r], ctx.mat(1), { res: 0.025, ax });                      // disque
    for (let i = 0; i < 160; i++) {                                                        // graines (spirale d'or)
      const d = 0.52 * r * Math.sqrt((i + 0.5) / 160), a = i * OR;
      const p = add(add(c, mul(n, 0.05 * r)), add(mul(U, d * Math.cos(a)), mul(W, d * Math.sin(a))));
      ctx.S.ball(ctx.P(p), 0.028 * r, ctx.mat(1), { res: 0.012 });
    }
    for (let j = 0; j < 2; j++)                                                             // rayons, 2 rangs
      for (let i = 0; i < 17; i++) {
        const a = (i + 0.5 * j + 0.3 * h(1, i)) * (2 * Math.PI / 17);
        const d = norm(add(add(mul(U, Math.cos(a)), mul(W, Math.sin(a))), mul(n, 0.1 - 0.15 * j)));
        petale(ctx, add(c, mul(d, 0.5 * r)), d, r * (0.5 + 0.12 * h(2 + j, i)), r * 0.16, 0.02 * r, n);
      }
    for (let i = 0; i < 14; i++) {                                                          // bractées
      const a = (i + 0.5) * (2 * Math.PI / 14);
      const d = norm(add(add(mul(U, Math.cos(a)), mul(W, Math.sin(a))), mul(n, -0.5)));
      petale(ctx, add(c, mul(d, 0.45 * r)), d, r * 0.22, r * 0.12, 0.02 * r, n, 2);
    }
  }
});

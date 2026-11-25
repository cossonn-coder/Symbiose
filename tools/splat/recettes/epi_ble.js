// SYMBIOSE — tools/splat/recettes/epi_ble.js (sprint PRÉCUISSON SPLATS ③)
// ÉPI DE BLÉ (chaume) — PoserEpiChaume (PlantRenderer.PortChaume.cs) : épillets en deux
// rangs alternés sur le rachis, presque droit. Une couche. Nominal (fiche blé) : épi de
// 9 cm sur 2,3 cm de large, `Penche` 0,04. Attache = base de l'épi.
// RELIQUATS ④ : rend les SITES des anthères (un épillet sur trois : filet latéral, anthère qui
// pend), pour la sur-couche `antheres` (lib/details.js). La sculpture de l'épi est inchangée.
'use strict';
const { CM, recette, petale, tige, norm, add, mul } = require('../lib/organe');
module.exports = recette({
  nom: 'epi_ble', rayonCm: 11,
  vue: ['FicheChaume.Epi (ble, EpiLargeCm >= 1)'],
  sculpter(ctx, h) {
    const L = 9 * CM * (0.92 + 0.16 * h(0, 0)), pen = 0.04 + 0.06 * h(0, 1), n = 18;
    const axe = t => [pen * L * t * t, L * t, 0];
    tige(ctx, [axe(0), axe(0.5), axe(1)], 0.12 * CM, 0.08 * CM);
    const sites = [];
    for (let i = 0; i < n; i++) {
      const t = 0.04 + 0.9 * i / (n - 1), s = i % 2 ? 1 : -1, p = axe(t), w = 1 - 0.35 * Math.abs(2 * t - 0.9);
      const d = norm([0.15 * (h(1, i) - 0.5), 1, s * 0.75]);
      petale(ctx, p, d, 1.3 * CM * w, 0.75 * CM * w, 0.3 * CM * w, [1, 0, 0]);
      if (i % 3) continue;   // un épillet sur trois, des deux côtés
      const m = add(p, mul(d, 0.6 * CM * w)), bout = add(m, [0, -0.05 * CM, s * 0.45 * CM]);
      sites.push({ c: ctx.P(m), bout: ctx.P(bout), pend: ctx.P(add(bout, [0, -0.2 * CM, 0.05 * s * CM])) });
    }
    return sites;
  }
});

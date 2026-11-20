// SYMBIOSE — tools/splat/recettes/epi_barbu.js (sprint PRÉCUISSON SPLATS ③)
// ÉPI BARBU (seigle) — PoserEpiChaume avec `BarbeCm` (PlantRenderer.PortChaume.cs) :
// épi fin qui retombe (`Penche` 0,7) vers +X, épillets alternés et longues barbes.
// Une couche. Nominal (fiche seigle) : 13 cm × 0,7 cm, barbes de 5 cm.
'use strict';
const { CM, recette, petale, tige, norm, add, mul } = require('../lib/organe');
module.exports = recette({
  nom: 'epi_barbu', rayonCm: 16,
  vue: ['FicheChaume.Epi (seigle, BarbeCm > 0)'],
  sculpter(ctx, h) {
    const L = 13 * CM * (0.92 + 0.16 * h(0, 0)), arc = 0.9 + 0.3 * h(0, 1), n = 22;
    const axe = t => { const a = arc * t; return [L * (1 - Math.cos(a)) / arc, L * Math.sin(a) / arc, 0]; };
    const tan = t => norm([Math.sin(arc * t), Math.cos(arc * t), 0]);
    tige(ctx, Array.from({ length: 6 }, (_, k) => axe(k / 5)), 0.06 * CM, 0.04 * CM);
    for (let i = 0; i < n; i++) {
      const t = 0.03 + 0.95 * i / (n - 1), s = i % 2 ? 1 : -1, p = axe(t), T = tan(t);
      const d = norm(add(T, [0, 0, s * 0.5]));
      petale(ctx, p, d, 0.9 * CM, 0.4 * CM, 0.16 * CM, [T[1], -T[0], 0]);
      const b = add(p, mul(d, 0.8 * CM));
      tige(ctx, [b, add(b, mul(norm(add(T, [0, 0, s * 0.25])), 5 * CM * (0.85 + 0.3 * h(1, i))))], 0.025 * CM, 0.012 * CM);
    }
  }
});

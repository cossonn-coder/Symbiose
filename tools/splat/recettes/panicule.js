// SYMBIOSE — tools/splat/recettes/panicule.js (sprint PRÉCUISSON SPLATS ③)
// PANICULE (pâturin) — PoserPanicule (PlantRenderer.PortChaume.cs) : triangle ajouré,
// rameaux en verticilles qui s'écartent et raccourcissent vers le haut, petits épillets
// au bout. Une couche. Nominal (fiche pâturin) : 11 cm.
'use strict';
const { CM, recette, petale, tige, norm, add, mul } = require('../lib/organe');
module.exports = recette({
  nom: 'panicule', rayonCm: 13,
  vue: ['FicheChaume.Panicule'],
  sculpter(ctx, h) {
    const L = 11 * CM * (0.9 + 0.2 * h(0, 0));
    tige(ctx, [[0, 0, 0], [0.02 * L, 0.5 * L, 0], [0.05 * L, L, 0]], 0.06 * CM, 0.03 * CM);
    for (let v = 0; v < 5; v++) {
      const t = 0.1 + 0.18 * v, base = [0.05 * L * t * t, L * t, 0], l = 0.5 * L * (1 - 0.8 * t);
      for (let k = 0; k < 3; k++) {
        const a = v * 1.1 + k * 2.1 + 0.5 * h(1, v * 3 + k), d = norm([Math.cos(a), 0.9, Math.sin(a)]);
        const bout = add(base, mul(d, l));
        tige(ctx, [base, add(base, mul(d, 0.5 * l)), add(bout, [0, -0.08 * l, 0])], 0.025 * CM, 0.015 * CM);
        for (let e = 0; e < 3; e++) {
          const p = add(base, mul(d, l * (0.55 + 0.2 * e)));
          petale(ctx, p, norm(add(d, [0, 0.6, 0])), 0.45 * CM, 0.22 * CM, 0.08 * CM, [0, 1, 0]);
        }
      }
    }
  }
});

// SYMBIOSE — tools/splat/recettes/tete_grappe.js (sprint PRÉCUISSON SPLATS ③)
// GRAPPE en crosse (drosera, phacélie : cyme scorpioïde) — PoserGrappe
// (PlantRenderer.PortTetes.cs) : fleurs le long d'un axe qui s'enroule d'un côté.
// Une couche. Rayon nominal 1,5 cm (fiches : drosera 0,8, phacélie 3).
'use strict';
const { CM, recette, corolle, tige, norm } = require('../lib/organe');
module.exports = recette({
  nom: 'tete_grappe', rayonCm: 6,
  vue: ['FormeTete.Grappe'],
  sculpter(ctx, h) {
    const r = 1.5 * CM * (0.9 + 0.2 * h(0, 0)), n = 7, R = 2 * r;
    // Crosse : arc de cercle qui part vers le haut et s'enroule vers +X.
    const axe = t => { const a = Math.PI * (1 - 1.25 * t); return [R * (1 + Math.cos(a)), R * Math.sin(a) * 0.9 + 0.6 * r * t, 0]; };
    tige(ctx, Array.from({ length: 9 }, (_, k) => axe(k / 8)), 0.06 * r, 0.03 * r);
    for (let i = 0; i < n; i++) {
      const t = i / (n - 1), p = axe(t), q = axe(Math.min(1, t + 0.05));
      const out = norm([-(q[1] - p[1]), q[0] - p[0] + 0.6, 0.3 * (h(1, i) - 0.5)]);
      corolle(ctx, p, r * 0.42 * (1 - 0.5 * t), out, h(2, i) * 6.28, 0, 0.35);
    }
  }
});

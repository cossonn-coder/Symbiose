// SYMBIOSE — tools/splat/recettes/gousse.js (sprint PRÉCUISSON SPLATS ③)
// GOUSSE (haricot) — PoserGousses (PlantRenderer.PortVolubile.cs) : gousse fine qui pend
// sous son attache, bosselée par les grains, pointue au bout, un peu courbe vers +X.
// Une couche. Nominal (fiche) : 15 cm de long, ~0,9 cm d'épaisseur.
'use strict';
const { CM, recette, boule, tige } = require('../lib/organe');
module.exports = recette({
  nom: 'gousse', rayonCm: 17,
  vue: ['FormeTete.Papillon (hors fleur : gousses)'],
  sculpter(ctx, h) {
    const L = 15 * CM * (0.9 + 0.2 * h(0, 0)), arc = 0.12 + 0.12 * h(0, 1);
    const axe = t => [arc * L * t * t, -L * t, 0.03 * L * (h(0, 2) - 0.5) * t];
    tige(ctx, Array.from({ length: 9 }, (_, k) => axe(k / 8)), u => 0.42 * CM * Math.min(1, 6 * u, 3.5 * (1 - u)) + 0.04 * CM);
    for (let i = 0; i < 6; i++) boule(ctx, axe(0.14 + 0.13 * i), 0.4 * CM, 0, 1.15);   // grains
  }
});

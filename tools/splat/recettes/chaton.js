// SYMBIOSE — tools/splat/recettes/chaton.js (sprint PRÉCUISSON SPLATS ③)
// CHATON (noyer, chêne, hêtre, charme, bouleau, aulne, saule, sapin, noisetier) —
// PoserChaton (PlantRenderer.FleurSnes.cs) : épi d'écailles serrées qui pend sous son
// attache, plus fin au bout. Une couche. Nominal : 6 cm (ChatonCm).
'use strict';
const { CM, recette, boule, tige } = require('../lib/organe');
module.exports = recette({
  nom: 'chaton', rayonCm: 7.5,
  vue: ['PoserChaton (FleurSnes, FleursArbre)'],
  sculpter(ctx, h) {
    const L = 6 * CM * (0.9 + 0.2 * h(0, 0)), pen = 0.2 + 0.25 * h(0, 1), n = 46;
    const axe = t => [pen * L * t * t, -L * t, 0.05 * L * (h(0, 2) - 0.5) * t];
    tige(ctx, [axe(0), axe(0.4), axe(1)], 0.18 * CM, 0.1 * CM);
    for (let i = 0; i < n; i++) {
      const t = 0.05 + 0.92 * (i / (n - 1)), a = i * 2.39996, p = axe(t), e = 0.2 * CM * (1 - 0.45 * t);
      boule(ctx, [p[0] + e * Math.cos(a), p[1], p[2] + e * Math.sin(a)], 0.24 * CM * (1 - 0.45 * t), 0, 0.8);
    }
  }
});

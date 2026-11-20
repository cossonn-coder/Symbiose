// SYMBIOSE — tools/splat/recettes/tete_epi.js (sprint PRÉCUISSON SPLATS ③)
// ÉPI de fleurs serrées autour d'un axe, plus étroit au bout (molène, basilic, menthe,
// lavande, chanvre, armoise) — PoserEpi (PlantRenderer.PortTetes.cs). Une couche.
// Taille NOMINALE : rayon des fleurs 1,4 cm (médiane des fiches), épi de 8 cm ; la vue
// fait l'épi du tiers haut de la hampe (sa longueur suit la hampe) → cf. 00_etat ③.
'use strict';
const { CM, recette, boule, tige } = require('../lib/organe');
module.exports = recette({
  nom: 'tete_epi', rayonCm: 9,
  vue: ['FormeTete.Epi'],
  sculpter(ctx, h) {
    const r = 1.4 * CM * (0.9 + 0.2 * h(0, 0)), L = 8 * CM * (0.9 + 0.2 * h(0, 1)), n = 26;
    const pen = 0.06 * (h(0, 2) - 0.5);
    const axe = t => [pen * L * t * t, L * t, 0];
    tige(ctx, [axe(0), axe(0.5), axe(1)], 0.1 * r, 0.06 * r);
    for (let i = 0; i < n; i++) {
      const t = (i + 0.5) / n, a = i * 2.39996 + 0.5 * h(1, i), e = r * 0.45 * (1 - 0.5 * t);
      const p = axe(t);
      boule(ctx, [p[0] + e * Math.cos(a), p[1], p[2] + e * Math.sin(a)], r * 0.42 * (1 - 0.45 * t) * (0.85 + 0.3 * h(2, i)), 0, 0.75);
    }
  }
});

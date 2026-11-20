// SYMBIOSE — tools/splat/recettes/tete_chapelet.js (sprint PRÉCUISSON SPLATS ③)
// CHAPELET (bourse-à-pasteur) — PoserChapelet (PlantRenderer.PortTetes.cs) : petit
// bouquet de fleurs au sommet (couche 0) et silicules en cœur renversé le long du haut
// de la hampe (couche 1 = silicules, FruitUnripe côté vue), sur leurs pédicelles.
// L'axe de la hampe n'est PAS cuit (la vue le trace). Attache = sommet de la hampe.
// Nominal : fleurs 1,2 cm (fiche), hampe de 20 cm (silicules de 42 à 92 % de sa hauteur).
'use strict';
const { CM, recette, petale, corolle, tige, norm } = require('../lib/organe');
module.exports = recette({
  nom: 'tete_chapelet', rayonCm: 14, couches: ['fleurs', 'silicules'],
  vue: ['FormeTete.Chapelet'],
  sculpter(ctx, h) {
    const r = 1.2 * CM * (0.9 + 0.2 * h(0, 0)), H = 20 * CM;
    for (let k = 0; k < 4; k++) {
      const a = k * 2.39996, d = norm([0.6 * Math.cos(a), 1, 0.6 * Math.sin(a)]);
      corolle(ctx, [0.35 * r * d[0], 0.3 * r, 0.35 * r * d[2]], 0.35 * r, d, h(1, k) * 6.28);
    }
    for (let k = 0; k < 8; k++) {
      const y = -H * (1 - (0.42 + 0.5 * k / 7)), a = k * 2.39996 + 0.4 * h(2, k);
      const d = norm([Math.cos(a), 0.5, Math.sin(a)]), l = 1.1 * CM;
      const b = [d[0] * l, y + d[1] * l, d[2] * l];
      tige(ctx, [[0, y, 0], b], 0.03 * CM, 0.025 * CM, 1);
      // Cœur renversé : deux lobes plats en V, pointe vers la tige.
      for (const s of [-1, 1]) {
        const v = norm([d[0] - s * 0.5 * d[2], 0.7, d[2] + s * 0.5 * d[0]]);
        petale(ctx, b, v, 0.65 * CM, 0.42 * CM, 0.03 * CM, [-d[2], 0, d[0]], 1);
      }
    }
  }
});

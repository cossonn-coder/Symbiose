// SYMBIOSE — tools/splat/recettes/tete_bouquet.js (sprint PRÉCUISSON SPLATS ③)
// BOUQUET de petites fleurs serrées en dôme (mâche, moutarde, thym) — PoserBouquet
// (PlantRenderer.PortTetes.cs). Une couche. Rayon nominal 1,8 cm (fiches 1,6-3,8).
'use strict';
const { CM, recette, corolle, tige, add, mul, norm } = require('../lib/organe');
module.exports = recette({
  nom: 'tete_bouquet', rayonCm: 3.5,
  vue: ['FormeTete.Bouquet'],
  sculpter(ctx, h) {
    const r = 1.8 * CM * (0.9 + 0.2 * h(0, 0)), n = 9;
    for (let i = 0; i < n; i++) {
      const a = i * 2.39996 + h(1, i), e = 0.25 + 0.7 * ((i + 0.5) / n);
      const d = norm([Math.cos(a) * Math.sin(e * 1.2), Math.cos(e * 1.2), Math.sin(a) * Math.sin(e * 1.2)]);
      const p = add([0, 0.35 * r, 0], mul(d, 0.65 * r));
      tige(ctx, [[0, 0, 0], [0, 0.3 * r, 0], p], 0.035 * r);
      corolle(ctx, p, 0.3 * r * (0.85 + 0.3 * h(2, i)), d, h(3, i) * 6.28, 0, 0.3);
    }
  }
});

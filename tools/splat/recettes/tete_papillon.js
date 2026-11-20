// SYMBIOSE — tools/splat/recettes/tete_papillon.js (sprint PRÉCUISSON SPLATS ③)
// PAPILLONS (haricot) — PoserPapillons (PlantRenderer.PortVolubile.cs) : 3 fleurs
// papilionacées à l'aisselle, chacune un étendard dressé, deux ailes, une carène.
// Hors fleur, la vue dessine des gousses → recette `gousse`. Une couche.
// Rayon nominal 1,4 cm (fiche haricot).
'use strict';
const { CM, recette, petale, boule, tige, norm } = require('../lib/organe');
module.exports = recette({
  nom: 'tete_papillon', rayonCm: 6,
  vue: ['FormeTete.Papillon (en fleur)'],
  sculpter(ctx, h) {
    const r = 1.4 * CM * (0.9 + 0.2 * h(0, 0));
    tige(ctx, [[0, 0, 0], [1.5 * r, 0.3 * r, 0], [3 * r, 0.2 * r, 0]], 0.06 * r, 0.04 * r);
    for (let k = 0; k < 3; k++) {
      const s = k % 2 ? 1 : -1, c = [r * (0.8 + 1.05 * k), 0.4 * r, s * 0.5 * r];
      const out = norm([0.35, 0.25, s]);
      tige(ctx, [[c[0], 0.3 * r, 0], c], 0.04 * r);
      petale(ctx, c, norm([0.2, 1, s * 0.4]), 0.9 * r, 0.9 * r, 0.03 * r, out);          // étendard
      petale(ctx, c, norm([0.6, 0.2, s + 0.5]), 0.7 * r, 0.4 * r, 0.04 * r, [0, 1, 0]);  // ailes
      petale(ctx, c, norm([0.6, 0.2, s - 0.5]), 0.7 * r, 0.4 * r, 0.04 * r, [0, 1, 0]);
      boule(ctx, [c[0] + 0.15 * r, c[1] - 0.05 * r, c[2] + s * 0.35 * r], 0.22 * r);     // carène
    }
  }
});

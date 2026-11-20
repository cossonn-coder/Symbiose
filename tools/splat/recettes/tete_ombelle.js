// SYMBIOSE — tools/splat/recettes/tete_ombelle.js (sprint PRÉCUISSON SPLATS ③)
// OMBELLE (carotte, achillée) — PoserOmbelle (PlantRenderer.PortTetes.cs) : rayons
// partis d'un foyer (couche 1 = rayons, teinte du feuillage côté vue), ombelle plate
// d'ombellules au-dessus (couche 0). Rayon nominal 5 cm (fiches : achillée 4,5, carotte 6).
'use strict';
const { CM, recette, boule, tige } = require('../lib/organe');
module.exports = recette({
  nom: 'tete_ombelle', rayonCm: 7, couches: ['fleurs', 'rayons'],
  vue: ['FormeTete.Ombelle'],
  sculpter(ctx, h) {
    const r = 5 * CM * (0.9 + 0.2 * h(0, 0)), n = 11, haut = 0.55 * r;
    const ombellule = (c, rr, g) => {
      for (let j = 0; j < 9; j++) {
        const a = j * 2.39996 + h(g, j), d = rr * Math.sqrt((j + 0.5) / 9);
        boule(ctx, [c[0] + d * Math.cos(a), c[1] + 0.25 * rr * (1 - d / rr), c[2] + d * Math.sin(a)], 0.3 * rr, 0, 0.7);
      }
    };
    for (let i = 0; i < n; i++) {
      const a = i * 2.39996 + 0.4 * h(1, i), d = r * (0.25 + 0.75 * Math.sqrt((i + 0.5) / n));
      const p = [d * Math.cos(a), haut * (0.92 + 0.12 * h(2, i)), d * Math.sin(a)];
      tige(ctx, [[0, 0, 0], [p[0] * 0.5, p[1] * 0.75, p[2] * 0.5], p], 0.025 * r, 0.02 * r, 1);
      ombellule(p, 0.2 * r, 10 + i);
    }
    ombellule([0, haut * 1.02, 0], 0.18 * r, 30);
  }
});

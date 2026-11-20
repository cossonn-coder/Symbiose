// SYMBIOSE — tools/splat/recettes/tete_corolle.js (sprint PRÉCUISSON SPLATS ③)
// COROLLE à 5 pétales ronds et un cœur (fraisier, violette, framboisier) — PoserCorolle
// (PlantRenderer.PortTapis.cs). Sert aussi la fleur d'arbre de près, même dessin
// (PoserFleurSnes, PiecesFleur : 5 pétales autour d'un cœur). Couche 1 = le cœur
// (CoeurCorolle / FlowerHeart côté vue). Rayon nominal 1,3 cm (médiane des fiches).
'use strict';
const { CM, recette, corolle, tige } = require('../lib/organe');
module.exports = recette({
  nom: 'tete_corolle', rayonCm: 3, couches: ['petales', 'coeur'],
  vue: ['FormeTete.Corolle', 'PoserFleurSnes (5 lobes)', 'PiecesFleur (Petales, Coeur)'],
  sculpter(ctx, h) {
    const r = 1.3 * CM * (0.9 + 0.2 * h(0, 0));
    tige(ctx, [[0, 0, 0], [0, 0.25 * CM, 0]], 0.12 * CM, 0.2 * CM, 1);   // réceptacle
    corolle(ctx, [0, 0.3 * CM, 0], r, [0.1 * (h(0, 2) - 0.5), 1, 0], h(0, 1) * 2 * Math.PI, 1, 0.2 + 0.2 * h(0, 3));
  }
});

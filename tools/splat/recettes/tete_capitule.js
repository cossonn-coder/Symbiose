// SYMBIOSE — tools/splat/recettes/tete_capitule.js (sprint PRÉCUISSON SPLATS ③)
// CAPITULE de ligules (pissenlit) — PoserTete/Capitule (PlantRenderer.PortTetes.cs) :
// disque plein à plat, bombé, de rangs de ligules étroites. Une couche (la vue le
// teinte d'une seule couleur). La tête de graines (aigrette) est servie par
// tete_boule (la vue dessine PoserBoule). Rayon nominal 3 cm (pissenlit).
'use strict';
const { CM, recette, petale, boule, tige, add, mul, norm } = require('../lib/organe');
module.exports = recette({
  nom: 'tete_capitule', rayonCm: 4.5,
  vue: ['FormeTete.Capitule (en fleur)'],
  sculpter(ctx, h) {
    const r = 3 * CM * (0.9 + 0.2 * h(0, 0)), c = [0, 0.25 * r, 0];
    tige(ctx, [[0, 0, 0], c], 0.12 * r, 0.25 * r);
    const rangs = [[21, 1, 0.08], [17, 0.75, 0.3], [13, 0.5, 0.55]];
    rangs.forEach(([n, f, monte], j) => {
      const phase = h(1, j) * 6.28;
      for (let i = 0; i < n; i++) {
        const a = phase + (i * 2 * Math.PI) / n, d = norm([Math.cos(a), monte, Math.sin(a)]);
        petale(ctx, add(c, mul(d, 0.12 * r)), d, r * f * (0.85 + 0.2 * h(2 + j, i)), r * 0.18, 0.025 * r + 0.002, [0, 1, 0]);
      }
    });
    boule(ctx, add(c, [0, 0.12 * r, 0]), 0.22 * r, 0, 0.6);
  }
});

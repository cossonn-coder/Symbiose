// SYMBIOSE — tools/splat/recettes/tete_boule.js (sprint PRÉCUISSON SPLATS ③)
// BOULE de fleurons (ail, minette, pompon) — PoserBoule (PlantRenderer.Prairie.cs) ;
// sert aussi la tête de graines du capitule (aigrette, dessinée par PoserBoule ×1,3).
// Une couche. Rayon nominal 2 cm (fiches : minette 1,1, ail 2,8).
'use strict';
const { CM, recette, boule, tige } = require('../lib/organe');
module.exports = recette({
  nom: 'tete_boule', rayonCm: 3.5,
  vue: ['FormeTete.Boule', 'FormeTete.Capitule (tete de graines)'],
  sculpter(ctx, h) {
    const r = 2 * CM * (0.9 + 0.2 * h(0, 0)), c = [0, 0.9 * r, 0], n = 70;
    tige(ctx, [[0, 0, 0], c], 0.08 * r);
    boule(ctx, c, 0.78 * r);
    for (let i = 0; i < n; i++) {                       // fleurons : sphère de Fibonacci
      const y = 1 - (2 * (i + 0.5)) / n, s = Math.sqrt(1 - y * y), a = i * 2.39996 + 0.3 * h(1, i);
      const d = [s * Math.cos(a), y, s * Math.sin(a)], k = 0.85 + 0.2 * h(2, i);
      boule(ctx, [c[0] + d[0] * r * k, c[1] + d[1] * r * k, c[2] + d[2] * r * k], 0.17 * r);
    }
  }
});

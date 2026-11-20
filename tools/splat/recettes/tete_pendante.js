// SYMBIOSE — tools/splat/recettes/tete_pendante.js (sprint PRÉCUISSON SPLATS ③)
// GRAPPE PENDANTE (ortie, consoude, myrtille) — PoserPendante
// (PlantRenderer.PortTigeFormes.cs) : 4 grains qui pendent sous l'attache, de plus en
// plus petits, d'un côté (+X). Une couche. Rayon nominal 1,3 cm (fiches 0,8-2,2).
'use strict';
const { CM, recette, boule, tige } = require('../lib/organe');
module.exports = recette({
  nom: 'tete_pendante', rayonCm: 6,
  vue: ['FormeTete.Pendante'],
  sculpter(ctx, h) {
    const r = 1.3 * CM * (0.9 + 0.2 * h(0, 0)), pts = [[0, 0, 0]];
    for (let k = 0; k < 4; k++) {
      const p = [r * (0.5 + 0.28 * k), -r * 0.9 * k - 0.3 * r, r * 0.25 * (h(1, k) - 0.5)];
      pts.push(p);
      boule(ctx, p, r * (0.8 - 0.35 * k / 3) * (0.9 + 0.2 * h(2, k)), 0, 0.9);
    }
    tige(ctx, pts, 0.06 * r, 0.04 * r);
  }
});

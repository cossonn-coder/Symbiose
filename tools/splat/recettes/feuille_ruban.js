// SYMBIOSE — tools/splat/recettes/feuille_ruban.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE EN RUBAN (graminées, ail, poireau, iris : longue lame qui monte puis
// retombe en arc). Dessinée par PoserBrin dans la vue (PlantRenderer.PortRosette.cs).
// La marque `Pli` (ail : lame pliée en gouttière) est du RELIEF → cuite ici pour
// tous les rubans (la nervure en carène est aussi celle des graminées).
// L'arc est fait de 5 tronçons de limbe qui se chevauchent le long d'une parabole.
'use strict';
const { add, mul, direction, limbe } = require('../lib/limbe');
const { recette, CM } = require('../lib/feuille');

const LONG = 30 * CM, LARGE = 0.8 * CM, TRONCONS = 5, PLI = 0.5;

module.exports = recette({
  nom: 'feuille_ruban', rayonCm: 31, vue: ['FormeFeuille.Ruban', 'MarqueFeuille.Pli'],
  sculpter(ctx, h) {
    const L = LONG * (0.9 + 0.2 * h(0, 0)), monte = 0.9 + 0.5 * h(0, 1), retombe = 1.1 + 0.6 * h(0, 2);
    const p = t => [L * t, L * (monte * t - retombe * t * t) * 0.5, 0];
    const sites = [];
    for (let k = 0; k < TRONCONS; k++) {
      const t0 = k / TRONCONS, t1 = (k + 1.15) / TRONCONS;
      const a = p(t0), b = p(Math.min(t1, 1)), d = [b[0] - a[0], b[1] - a[1], 0];
      const l = Math.hypot(d[0], d[1]);
      // Largeur : pleine jusqu'aux 2/3, puis effilée jusqu'à la pointe.
      const w = t => (t < 0.66 ? 1 : Math.max(0.05, (1 - t) / 0.34));
      const s = limbe(ctx, {
        base: a, dir: mul(d, 1 / l), long: l, large: LARGE, pli: PLI,
        moitie: [[0, 0], [0, w(t0)], [1, w(Math.min(t1, 1))], [1, 0]]
      });
      if (k < 3) sites.push(s);
    }
    return sites;
  }
});

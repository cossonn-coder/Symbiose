// SYMBIOSE — tools/splat/recettes/feuille_plume.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE PLUMEUSE, FINEMENT DIVISÉE (carotte, achillée, fenouil : un rachis,
// des paires de lanières, elles-mêmes refendues). Disposition de PoserPlume
// (PlantRenderer.PortRosette.cs) : 5 paires à t = 0,2 + i·0,7/5, lanière jusqu'à
// (t + 0,12 ; ±(1 − 0,75 t)) de la largeur. Lanières = tubes fins (pas de limbe :
// rien à cribler, la vue n'y dessine pas de trous non plus).
'use strict';
const { add, mul } = require('../lib/limbe');
const { recette, CM } = require('../lib/feuille');

const LONG = 18 * CM, LARGE = 0.32, PAIRES = 5;

module.exports = Object.assign(recette({
  nom: 'feuille_plume', rayonCm: 19, vue: ['FormeFeuille.Plume'],
  sculpter({ S, M, R }, h) {
    const L = LONG * (0.9 + 0.2 * h(0, 0)), W = L * LARGE;
    const axe = t => [L * t, L * (0.3 * t - 0.45 * t * t), 0];   // rachis arqué
    S.tube([0, 0.25, 0.5, 0.75, 1].map(t => R(axe(t))), 0.014, 0.006, M.organe, { res: 0.012 });
    for (let i = 1; i <= PAIRES; i++) {
      const t = 0.2 + (i * 0.7) / PAIRES, lr = (1 - t * 0.75) * W * (0.85 + 0.3 * h(1, i));
      for (const sgn of [-1, 1]) {
        const a = axe(t - 0.1), b = add(axe(t + 0.02), [0, -0.03, sgn * lr]);
        S.tube([a, add(mul(add(a, b), 0.5), [0, 0.015, 0]), b].map(R), 0.012, 0.007, M.organe, { res: 0.008 });
        // Deux refentes par lanière, vers le bout.
        for (const f of [0.45, 0.75]) {
          const q = add(mul(a, 1 - f), mul(b, f));
          const bout = add(q, [lr * 0.3, -0.02, sgn * lr * 0.25 * (0.8 + 0.4 * h(2, i * 3 + (f > 0.5 ? 1 : 0)))]);
          S.tube([q, bout].map(R), 0.009, 0.005, M.organe, { res: 0.008 });
        }
      }
    }
    return [];
  }
}), { trous: false });

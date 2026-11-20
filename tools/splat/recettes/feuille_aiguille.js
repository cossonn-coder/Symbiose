// SYMBIOSE — tools/splat/recettes/feuille_aiguille.js (sprint PRÉCUISSON SPLATS ②)
// AIGUILLE (sapin, thym, fétuque : `LeafShape.Aciculaire` de la vue,
// PlantRenderer.Leaf.cs — « trait court épais »). Un tube effilé légèrement
// arqué : sa section ronde donne plusieurs orientations de face par pixel.
// Pas de trous : une aiguille ne se crible pas (la vue n'en dessine pas).
'use strict';
const { recette, CM } = require('../lib/feuille');

module.exports = Object.assign(recette({
  nom: 'feuille_aiguille', rayonCm: 4, vue: ['LeafShape.Aciculaire'],
  sculpter({ S, M, R }, h) {
    const L = 3 * CM * (0.9 + 0.2 * h(0, 0)), arc = 0.08 + 0.08 * h(0, 1);
    const pts = [0, 0.25, 0.5, 0.75, 1].map(t => R([L * t, L * arc * Math.sin(Math.PI * t), 0]));
    S.tube(pts, 0.012, 0.004, M.organe, { res: 0.006 });
    return [];
  }
}), { trous: false });

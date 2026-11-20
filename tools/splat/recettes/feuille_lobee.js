// SYMBIOSE — tools/splat/recettes/feuille_lobee.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE LOBÉE PENNÉE (chêne, moutarde lyrée, roquette : lobes le long de la
// nervure). Contour = ContourLobe de la vue (PlantRenderer.PortRosette.cs).
// ≠ `LeafShape.Lobee` (palmilobée : vigne, figuier, courge) → feuille_paume.
'use strict';
module.exports = require('../lib/feuille').simple({
  nom: 'feuille_lobee', vue: ['FormeFeuille.Lobee'],
  moitie: [[0, 0], [0.15, 0.5], [0.25, 0.2], [0.4, 0.7], [0.5, 0.25], [0.65, 0.85], [0.75, 0.35], [0.95, 0.7], [1, 0]],
  longCm: 12, large: 0.42, petioleCm: 1
});

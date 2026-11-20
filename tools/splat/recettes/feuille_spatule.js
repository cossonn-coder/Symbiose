// SYMBIOSE — tools/splat/recettes/feuille_spatule.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE SPATULE (mâche : étroite à la base, arrondie au bout).
// Contour = ContourSpatule de la vue (PlantRenderer.PortRosette.cs).
'use strict';
module.exports = require('../lib/feuille').simple({
  nom: 'feuille_spatule', vue: ['FormeFeuille.Spatule'],
  moitie: [[0, 0], [0.25, 0.22], [0.55, 0.8], [0.8, 1], [0.97, 0.6], [1, 0]],
  longCm: 8, large: 0.34
});

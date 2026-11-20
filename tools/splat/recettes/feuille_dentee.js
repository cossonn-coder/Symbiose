// SYMBIOSE — tools/splat/recettes/feuille_dentee.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE DENTÉE en rosette plaquée (pissenlit : dents rabattues vers la base).
// Contour = ContourDente de la vue (PlantRenderer.PortRosette.cs).
'use strict';
module.exports = require('../lib/feuille').simple({
  nom: 'feuille_dentee', vue: ['FormeFeuille.Dentee'],
  moitie: [[0, 0], [0.12, 0.35], [0.2, 0.12], [0.34, 0.65], [0.44, 0.2], [0.58, 0.9], [0.67, 0.3], [0.82, 1], [1, 0]],
  longCm: 15, large: 0.22, penche: 0.05
});

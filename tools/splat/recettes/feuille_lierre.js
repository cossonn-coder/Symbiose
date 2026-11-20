// SYMBIOSE — tools/splat/recettes/feuille_lierre.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE DE LIERRE (3-5 lobes anguleux, long pétiole). Contour = ContourLierre
// de la vue (PlantRenderer.Lianes.cs). Ses nervures pâles (marque `Nervures`)
// sont une COULEUR : peintes par la vue, pas cuites.
'use strict';
module.exports = require('../lib/feuille').simple({
  nom: 'feuille_lierre', vue: ['FormeFeuille.Lierre'],
  moitie: [[0, 0], [-0.08, 0.5], [0.12, 1], [0.3, 0.42], [0.52, 0.68], [0.62, 0.22], [1, 0]],
  longCm: 7, large: 0.85, petioleCm: 4
});

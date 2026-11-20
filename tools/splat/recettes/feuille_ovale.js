// SYMBIOSE — tools/splat/recettes/feuille_ovale.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE OVALE (limbe simple entier : poivron, bourrache, pommier, hêtre, aulne…).
// Contour = ContourOvale de la vue (PlantRenderer.PortRosette.cs). Sert aussi la
// forme `Elliptique` des paliers hauts et du kit (PlantRenderer.Leaf.cs).
'use strict';
module.exports = require('../lib/feuille').simple({
  nom: 'feuille_ovale', vue: ['FormeFeuille.Ovale', 'LeafShape.Elliptique'],
  moitie: [[0, 0], [0.15, 0.6], [0.45, 1], [0.75, 0.8], [0.95, 0.3], [1, 0]],
  longCm: 9, large: 0.45, petioleCm: 1.5
});

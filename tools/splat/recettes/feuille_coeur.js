// SYMBIOSE — tools/splat/recettes/feuille_coeur.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE EN CŒUR (tournesol, liseron, noisetier, bouleau : base échancrée).
// Contour = ContourCoeur de la vue (PlantRenderer.PortTigeFormes.cs). Sert aussi
// la forme `Cordee` des paliers hauts et du kit (PlantRenderer.Leaf.cs).
'use strict';
module.exports = require('../lib/feuille').simple({
  nom: 'feuille_coeur', vue: ['FormeFeuille.Coeur', 'LeafShape.Cordee'],
  moitie: [[0, 0], [-0.06, 0.6], [0.12, 1], [0.45, 0.85], [0.78, 0.4], [1, 0]],
  longCm: 10, large: 0.55, petioleCm: 3
});

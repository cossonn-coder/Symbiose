// SYMBIOSE — tools/splat/recettes/feuille_paume.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE EN PAUME, PALMILOBÉE (courgette, courge, vigne, figuier : grande, à
// lobes larges, long pétiole). Contour = ContourPaume de la vue
// (PlantRenderer.PortRampante.cs). Sert aussi `LeafShape.Lobee` des paliers hauts
// et du kit (PlantRenderer.Leaf.cs : « 3-5 lobes, vigne, érable, courge »).
'use strict';
module.exports = require('../lib/feuille').simple({
  nom: 'feuille_paume', vue: ['FormeFeuille.Paume', 'LeafShape.Lobee'],
  moitie: [[0, 0], [-0.05, 0.45], [0.14, 0.92], [0.27, 1], [0.34, 0.55], [0.53, 0.86], [0.66, 0.78],
    [0.66, 0.3], [0.92, 0.3], [1, 0]],
  longCm: 20, large: 0.95, petioleCm: 6, pli: 0.25
});

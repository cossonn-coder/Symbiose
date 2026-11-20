// SYMBIOSE — tools/splat/recettes/feuille_lanceolee.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE LANCÉOLÉE (plantain, saule, lavande, consoude : étroite, pointue).
// Contour = ProfilLanceole de la vue (PlantRenderer.Graminees.cs). Sert aussi la
// forme `Lanceolee` des paliers hauts et du kit (PlantRenderer.Leaf.cs).
// Variante gaufrée (consoude) : recettes/feuille_lanceolee_gaufree.js.
'use strict';
module.exports = require('../lib/feuille').simple({
  nom: 'feuille_lanceolee', vue: ['FormeFeuille.Lanceolee', 'LeafShape.Lanceolee'],
  moitie: [[0, 0], [0.2, 0.45], [0.5, 1], [0.8, 0.6], [1, 0]],
  longCm: 14, large: 0.22, petioleCm: 1
});

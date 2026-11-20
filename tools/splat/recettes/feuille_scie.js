// SYMBIOSE — tools/splat/recettes/feuille_scie.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE EN SCIE (ortie, menthe, mélisse : bord à grosses dents).
// Contour = ContourScie de la vue (PlantRenderer.PortTigeFormes.cs).
// Variante gaufrée (marque `Gaufre`) : recettes/feuille_scie_gaufree.js.
'use strict';
module.exports = require('../lib/feuille').simple({
  nom: 'feuille_scie', vue: ['FormeFeuille.Scie'],
  moitie: [[0, 0], [0.15, 0.7], [0.3, 0.45], [0.5, 1], [0.62, 0.55], [0.78, 0.55], [1, 0]],
  longCm: 9, large: 0.45, petioleCm: 1.5
});

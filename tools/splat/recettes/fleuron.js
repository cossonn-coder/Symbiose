// SYMBIOSE — tools/splat/recettes/fleuron.js (sprint PRÉCUISSON SPLATS ③)
// FLEURONS du kit des paliers bas (D4) — Fleuron.Point/Bouton/Etoile
// (PlantRenderer.Kit.cs) : une petite corolle vue d'en haut, cuite aux 3 tailles du
// kit (1, 2, 3 px internes) au lieu des 3 dessins à la règle. Couche 1 = le cœur (le
// niveau KitCoeur du kit). Une vue, comme le kit. Nominal 1,5 cm (FleurRayonCm).
// RELIQUATS ④ : cœur grossi (0,4 × r au lieu de 0,28) — à 3 px il possède enfin le pixel du
// centre (la couche était vide aux 3 tailles : le cœur jaune disparaissait). À 2 px il reste
// sous le pixel : la vue force alors le pixel de l'attache (PlantRenderer.KitSplats.cs).
'use strict';
const { CM, recette, corolle } = require('../lib/organe');
module.exports = recette({
  nom: 'fleuron', rayonCm: 2.5, couches: ['petales', 'coeur'], lacets: 1, inclinaisons: [0],
  tailles: [1, 2, 3], empriseCm: 3,
  vue: ['Kit Fleuron.Point (1 px)', 'Kit Fleuron.Bouton (2 px)', 'Kit Fleuron.Etoile (3 px)'],
  sculpter(ctx, h) {
    corolle(ctx, [0, 0, 0], 1.5 * CM * (0.9 + 0.2 * h(0, 0)), [0, 1, 0], h(0, 1) * 6.28, 1, 0.15, 0.4);
  }
});

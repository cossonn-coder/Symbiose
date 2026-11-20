// SYMBIOSE — tools/splat/recettes/bouton.js (sprint PRÉCUISSON SPLATS ③)
// BOUTON floral fermé (fleurs d'arbre à la montée de la floraison) — CoucheFleur.Boutons
// (PlantRenderer.GerbesFleurs.cs), CouchePiece.Bouton (PiecesFleur.cs), Fleuron.Bouton du
// kit. Ovoïde de pétales serrés (couche 0, teinte « bouton » d'espèce) dans 5 sépales
// (couche 1, feuillage). La vue ne dessine AUCUN bourgeon végétatif (vérifié au ③) : les
// « bourgeons » du kickoff sont ces boutons. Révolution : une vue. Nominal 0,6 cm.
'use strict';
const { CM, recette, petale, tige, norm } = require('../lib/organe');
module.exports = recette({
  nom: 'bouton', rayonCm: 1.6, couches: ['petales', 'sepales'], lacets: 1, inclinaisons: [0],
  vue: ['CoucheFleur.Boutons', 'CouchePiece.Bouton', 'Kit Fleuron.Bouton'],
  sculpter(ctx, h) {
    const r = 0.6 * CM * (0.9 + 0.2 * h(0, 0)), c = [0.05 * r * (h(0, 1) - 0.5), 1.1 * r, 0];
    tige(ctx, [[0, 0, 0], [0, 0.45 * r, 0]], 0.12 * r, 0.18 * r, 1);
    ctx.S.ball(ctx.P(c), [0.42 * r, 0.72 * r, 0.42 * r], ctx.mat(0), { res: 0.004 });
    for (let i = 0; i < 5; i++) {
      const a = (i * 2 * Math.PI) / 5 + h(0, 2) * 6.28, d = norm([Math.cos(a) * 0.9, 1, Math.sin(a) * 0.9]);
      petale(ctx, [0.2 * r * Math.cos(a), 0.45 * r, 0.2 * r * Math.sin(a)], d, 0.8 * r, 0.45 * r, 0.08 * r, [Math.cos(a), -0.3, Math.sin(a)], 1);
    }
  }
});

// SYMBIOSE — tools/splat/recettes/bouquet_corolles.js (sprint BOIS & ARBRES ④)
// BOUQUET DE FLEURS D'ARBRE au palier ×4 : un éperon fleuri (corymbe du pommier, ombelle du
// cerisier) cuit d'un tenant — PoserBouquetsArbre (PlantRenderer.BouquetsArbre.cs). Au-dessus de
// ×4 la vue pose les fleurs une à une (tete_corolle) ; en dessous, les gerbes de l'atlas.
// Couche 0 = pétales (teinte de fleur de l'espèce), couche 1 = cœurs (FlowerHeart).
//
// 📖 Pédagogie — pourquoi grossir la fleur. À ×4, 1 cm de sol ≈ 2 px : une fleur de pommier de
// 3,5 cm ferait 7 px, son cœur 1 px. La vue « relève » déjà la fleur d'arbre d'un tiers
// (FleurArbreRayonCm = 2 cm, FleursArbre.cs) ; on garde ce rayon. Le bouquet compte 11 corolles
// en dôme (une inflorescence de 5-6 fleurs sur un éperon qui en porte souvent deux [odg]) : c'est
// la seule façon de lire « couronne blanche » à ×4 sans des milliers de tracés.
// Une seule recette pour toutes les essences : à ×4 la forme ne se lit pas, la couleur oui.
'use strict';
const { CM, recette, corolle, add, mul, norm } = require('../lib/organe');
module.exports = recette({
  nom: 'bouquet_corolles', rayonCm: 10, couches: ['petales', 'coeur'],
  lacets: 4, inclinaisons: [0], paliers: [4],
  vue: ['BouquetsArbre (corolles, ×4)'],
  sculpter(ctx, h) {
    const R = 7 * CM * (0.9 + 0.2 * h(0, 0)), n = 11, c0 = [0, 0.35 * R, 0];
    for (let i = 0; i < n; i++) {
      // Phyllotaxie (angle d'or) sur un dôme : du sommet vers le bord, puis un peu sous l'équateur.
      const a = i * 2.39996 + h(1, i), e = 1.45 * Math.sqrt((i + 0.5) / n);
      const d = norm([Math.cos(a) * Math.sin(e), Math.cos(e), Math.sin(a) * Math.sin(e)]);
      const r = 2 * CM * (0.85 + 0.3 * h(2, i));
      corolle(ctx, add(c0, mul(d, 0.6 * R)), r, d, h(3, i) * 6.28, 1, 0.25, 0.3);
    }
  }
});

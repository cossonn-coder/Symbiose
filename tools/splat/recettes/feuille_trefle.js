// SYMBIOSE — tools/splat/recettes/feuille_trefle.js (sprint RELIQUATS DES PLANTES ④)
// FEUILLE DE TRÈFLE : 3 folioles obovales, échancrées au bout, étalées à plat autour du
// sommet du pétiole (DessinerTrefle, PlantRenderer.Prairie.cs : `ProfilFoliole`, foliole de
// 3 cm). L'attache est le CENTRE de la feuille : le pétiole reste un trait de la vue (sa
// hauteur suit le dôme du tapis, une pièce ne la connaît pas).
// `quatre(…)` fabrique la variante à 4 folioles (feuille_trefle4.js). Qui porte 4 folioles
// n'est PAS tiré ici : c'est le moteur (`sim/quatre_feuilles.py`, ~1 pied sur 200, geste
// `recolter`) — la vue pose cette variante sur tout le pied marqué, comme l'ancien dessin.
//
// 📖 Pédagogie : la feuille est plate (inclinaison 0 seule) ; ce qui varie d'une feuille à
// l'autre, c'est son azimut — le LACET de la caméra. 8 lacets suffisent à une étoile à 3
// branches (symétrie 120°) comme à 4 (90° : lacet 0 = « + », 45° = « × »).
'use strict';
const { direction, limbe } = require('../lib/limbe');
const { recette, CM } = require('../lib/feuille');

// ProfilFoliole de la vue, ramené au repère du limbe : la base décollée du centre (0,08)
// devient l'origine, la demi-largeur max (0,40) vaut 1.
const MOITIE = [[0, 0], [0.24, 0.375], [0.587, 1], [0.913, 0.95], [1, 0.35], [0.87, 0]];
const FOLIOLE = 3 * CM;

function trefle(nom, n, large, vue) {
  return Object.assign(recette({
    nom, rayonCm: 4, vue,
    sculpter(ctx, h) {
      const sites = [];
      for (let i = 0; i < n; i++) {
        const t = FOLIOLE * (0.92 + 0.16 * h(1, i));
        const a = (2 * Math.PI * i) / n + 0.12 * (h(2, i) - 0.5);
        sites.push(limbe(ctx, {
          base: direction(a, 0).map(x => x * 0.08 * t), dir: direction(a, 0.04 + 0.08 * h(3, i)),
          long: 0.92 * t, large: 0.4 * large * t, moitie: MOITIE, pli: 0.12, epais: 0.008, res: 0.006
        }));
      }
      return sites;   // trous D5 + sur-couches (nervures, chevron : lib/details.js)
    }
  }), { inclinaisons: [0] });
}

module.exports = Object.assign(trefle('feuille_trefle', 3, 1, ['PortPrairie.Trefle (3 folioles)']), {
  quatre: () => trefle('feuille_trefle4', 4, 0.9, ['PortPrairie.Trefle (4 folioles, QuatreFeuilles)'])
});

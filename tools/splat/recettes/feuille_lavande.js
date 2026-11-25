// SYMBIOSE — tools/splat/recettes/feuille_lavande.js (sprint RELIQUATS DES PLANTES ④)
// LAMES DE LAVANDE : la masse du buisson de lavande (PoserMasse, PlantRenderer.PortBuisson.cs,
// `GrainCm` 8 cm, feuille `Ruban`) était faite de traits ; ici une petite TOUFFE de 3 feuilles
// linéaires de ~8 cm, étroites (2-4 mm), bords enroulés, qui montent en s'écartant d'un même
// point. Le gris-vert est la teinte de l'espèce (palette de la vue), le feutrage = poils (③).
// Dressée vers +X (le lacet de la vue la tourne vers l'extérieur de la masse).
'use strict';
const { direction, limbe } = require('../lib/limbe');
const { recette, CM } = require('../lib/feuille');

const MOITIE = [[0, 0], [0.06, 0.75], [0.4, 1], [0.8, 0.8], [1, 0]];   // linéaire, pointue

module.exports = Object.assign(recette({
  nom: 'feuille_lavande', rayonCm: 10, vue: ['FicheBuisson.Grains (lavande, FormeFeuille.Ruban)'],
  sculpter(ctx, h) {
    const sites = [];
    for (let i = 0; i < 3; i++) {
      const l = 8 * CM * (0.75 + 0.3 * h(0, i)) * (i === 1 ? 1 : 0.85);
      sites.push(limbe(ctx, {
        base: [0, 0, 0], dir: direction((i - 1) * 0.45 + 0.2 * (h(1, i) - 0.5), 0.75 + 0.35 * h(2, i)),
        long: l, large: 0.16 * CM * (0.9 + 0.2 * h(3, i)), moitie: MOITIE, pli: 0.55, epais: 0.005, res: 0.004
      }));
    }
    return sites;
  }
}), { inclinaisons: [0] });

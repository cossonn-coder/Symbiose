// SYMBIOSE — tools/splat/recettes/feuille_cuillere.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE EN CUILLÈRE (drosera : long pétiole, limbe en disque creusé).
// Géométrie de PoserCuillere (PlantRenderer.PortRosette.cs) : disque centré aux
// 0,82 de la longueur, rayon = largeur. Les gouttes de glu (marque `Gouttes`)
// sont un ÉCLAT (brillance) → laissées à la vue.
'use strict';
const { direction, limbe } = require('../lib/limbe');
const { recette, CM } = require('../lib/feuille');

const LONG = 4 * CM, RAYON = 0.26;   // rayon du disque / longueur (fiche drosera)
const DISQUE = [[0, 0], [0.067, 0.5], [0.25, 0.866], [0.5, 1], [0.75, 0.866], [0.933, 0.5], [1, 0]];

module.exports = recette({
  nom: 'feuille_cuillere', rayonCm: 5, vue: ['FormeFeuille.Cuillere'],
  sculpter(ctx, h) {
    const L = LONG * (0.9 + 0.2 * h(0, 0)), r = L * RAYON, pied = 0.82 * L - r;
    return [limbe(ctx, {
      base: [0, 0, 0], dir: direction(0, 0.15 * h(0, 1)), long: 2 * r, large: r,
      moitie: DISQUE, petiole: pied, pli: 0.35, epais: 0.012
    })];
  }
});

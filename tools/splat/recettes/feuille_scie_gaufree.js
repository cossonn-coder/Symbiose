// SYMBIOSE — tools/splat/recettes/feuille_scie_gaufree.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE EN SCIE GAUFRÉE (marque `Gaufre` : ortie, menthe, mélisse) — même
// feuille que feuille_scie, nervures secondaires creusées (relief cuit).
'use strict';
const base = require('./feuille_scie').spec;
module.exports = require('../lib/feuille').simple({
  ...base, nom: 'feuille_scie_gaufree', vue: ['FormeFeuille.Scie + MarqueFeuille.Gaufre'], gaufre: true
});

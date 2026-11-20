// SYMBIOSE — tools/splat/recettes/feuille_lanceolee_gaufree.js (sprint PRÉCUISSON SPLATS ②)
// FEUILLE LANCÉOLÉE GAUFRÉE (marque `Gaufre` : consoude) — même feuille que
// feuille_lanceolee, nervures secondaires creusées (relief cuit).
'use strict';
const base = require('./feuille_lanceolee').spec;
module.exports = require('../lib/feuille').simple({
  ...base, nom: 'feuille_lanceolee_gaufree', vue: ['FormeFeuille.Lanceolee + MarqueFeuille.Gaufre'], gaufre: true
});

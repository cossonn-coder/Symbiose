#!/usr/bin/env node
// SYMBIOSE — tools/splat/inventaire_tailles.js (sprint RELIQUATS DES PLANTES ②)
// INVENTAIRE DES TAILLES RÉELLES que la vue demande à chaque recette, lu dans les
// fiches d'espèce du C# de la vue (portraits/table_cs.js, source unique), puis
// PROPOSITION de 3 classes de taille par recette (décision E8 de Nico).
//
// Usage : node tools/splat/inventaire_tailles.js   (lecture seule, rien n'est écrit)
// La sortie sert à régler `lib/classes.js` à la main (une proposition, pas un
// automatisme : un réglage de fiche ne doit pas recuire la bibliothèque en douce).
//
// MESURE de la vue, celle que le crochet passe (PlantRenderer.Splats.cs) :
//  • feuille : `FeuillePosee.Long` (cm au sol), formules RECOPIÉES des ports (le
//    stade adulte ; un jeune pied descend à ×0,4-0,6 de ces valeurs) ;
//  • tête, fruit, boule, corolle : le RAYON du disque que l'ancien dessin traçait (cm) ;
//  • épi, panicule : la longueur (cm).
// Formules (vérifiées au code le 2026-11-25) : rosette l = R·[0,47 ; 1] (PortRosette),
// feuilles de hampe R·[0,12 ; 0,5] (PortTetes), tige [0,7·haut ; bas] (PortTige),
// volubile bas·[0,5 ; 1], buisson [haut ; bas] (PortBuisson), tapis FeuilleCm·[0,6 ; 1],
// rampante R·[0,36 ; 0,5] (PortRampante), liane LongCm·[0,7 ; 1] (Lianes), rameaux
// d'arbre LimbeCm·[0,75 ; 1,1] (Houppier), plantain 17·[0,51 ; 1] (Graminees).
//
// 📖 Pédagogie : trois classes en progression GÉOMÉTRIQUE (×√2 entre crans voisins de
// l'échelle) parce que l'œil juge une taille en RAPPORT, pas en écart : 2 cm contre
// 3 cm se voit autant que 20 contre 30. C'est l'échelle des diaphragmes en photo.

'use strict';

const { lireTable } = require('./portraits/table_cs');
const { CLASSES, echelleVue } = require('./lib/classes');

const t = lireTable();
const inv = new Map();   // recette → [{ espece, lo, hi }]
const noter = (rec, espece, lo, hi = lo) => {
  if (!rec || !(hi > 0)) return;
  if (!inv.has(rec)) inv.set(rec, []);
  inv.get(rec).push({ espece, lo, hi });
};

// Feuilles des ports : RecetteFeuille de la vue (forme → recette, gaufrée selon la marque).
const FEUILLE = { Dentee: 'feuille_dentee', Spatule: 'feuille_spatule', Lobee: 'feuille_lobee',
  Ovale: 'feuille_ovale', Cuillere: 'feuille_cuillere', Plume: 'feuille_plume', Ruban: 'feuille_ruban',
  Coeur: 'feuille_coeur', Scie: 'feuille_scie', Lanceolee: 'feuille_lanceolee', Palmee: 'feuille_palmee',
  Paume: 'feuille_paume', Triade: 'feuille_triade', Composee: 'feuille_composee', Lierre: 'feuille_lierre' };
const recFeuille = (forme, marque) => FEUILLE[forme] &&
  (marque === 'Gaufre' && (forme === 'Scie' || forme === 'Lanceolee') ? FEUILLE[forme] + '_gaufree' : FEUILLE[forme]);
const TETE = { Capitule: 'tete_capitule', Bouquet: 'tete_bouquet', Chapelet: 'tete_chapelet', Epi: 'tete_epi',
  Ombelle: 'tete_ombelle', Boule: 'tete_boule', Grappe: 'tete_grappe', Soleil: 'tete_soleil', Etoile: 'tete_etoile',
  Pendante: 'tete_pendante', Corolle: 'tete_corolle', Trompette: 'tete_trompette', Papillon: 'tete_papillon' };

for (const [n, f] of Object.entries(t.ports)) {
  const rf = recFeuille(f.Feuille, f.Marque), R = f.RayonCm;
  if (f.Forme === 'Rosette') noter(rf, n, 0.47 * R, R);
  if (f.FeuillesHampe > 0) noter(rf, n + ' (hampe)', 0.12 * R, 0.5 * R);
  if (f.Forme === 'Tige' && f.Tige) noter(rf, n, 0.7 * f.Tige.FeuilleHautCm, f.Tige.FeuilleBasCm);
  if (f.Forme === 'Volubile' && f.Tige) noter(rf, n, 0.5 * f.Tige.FeuilleBasCm, f.Tige.FeuilleBasCm);
  if (f.Forme === 'Buisson' && f.Buisson && f.Buisson.FeuilleBasCm) noter(rf, n, f.Buisson.FeuilleHautCm, f.Buisson.FeuilleBasCm);
  if (f.Forme === 'Tapis' && f.Tapis && f.Tapis.FeuilleCm) noter(rf, n, 0.6 * f.Tapis.FeuilleCm, f.Tapis.FeuilleCm);
  if (f.Forme === 'Rampante') noter(rf, n, 0.36 * R, 0.5 * R);
  if (f.TeteCm > 0 && TETE[f.Tete]) noter(TETE[f.Tete], n, f.TeteCm);
  if (f.Tete === 'Capitule') noter('tete_boule', n + ' (aigrette)', 1.3 * f.TeteCm);
  if (f.Fruit) noter(f.Fruit.Allonge > 1 ? 'fruit_long' : 'fruit_globe', n, 0.5 * f.Fruit.RayonCm, f.Fruit.RayonCm);
  if (f.Chaume && f.Chaume.EpiCm > 0)
    noter(f.Chaume.Panicule ? 'panicule' : f.Chaume.BarbeCm > 0 ? 'epi_barbu' : 'epi_ble', n, 0.6 * f.Chaume.EpiCm, f.Chaume.EpiCm);
}
for (const [n, l] of Object.entries(t.lianes)) {
  noter(recFeuille(l.Organes.Feuille, l.Organes.Marque), n, 0.7 * l.LongCm, l.LongCm);
  if (TETE[l.Organes.Tete]) noter(TETE[l.Organes.Tete], n, l.Organes.TeteCm);
  if (l.Organes.Fruit) noter('fruit_globe', n, 0.5 * l.Organes.Fruit.RayonCm, l.Organes.Fruit.RayonCm);
}
for (const [n, r] of Object.entries(t.rameaux)) noter(recFeuille(r.Limbe), n, 0.75 * r.LimbeCm, 1.1 * r.LimbeCm);
for (const [n, f] of Object.entries(t.fruitsArbres)) noter('fruit_globe', n, 0.4 * f.RayonCm, f.RayonCm);
const P = t.constPrairie;
noter('feuille_lanceolee', 'PlantainLanceole', 0.51 * P.RayonPlantainCm, P.RayonPlantainCm);
noter('tete_boule', 'Clover (pompon)', P.RayonPomponCm);
noter('tete_corolle', 'arbres (FleurRayonCm)', 1.5);

// --- Proposition : 3 points géométriques (bas, médiane, haut) posés sur l'échelle ×√2 ---
const geo = xs => Math.exp(xs.reduce((s, x) => s + Math.log(x), 0) / xs.length);
const crans = Array.from({ length: 13 }, (_, i) => Math.SQRT2 ** (i - 8));   // k de 1/16 à 2√2
console.log('recette'.padEnd(26), 'nominal'.padStart(7), '  plage vue (cm)      médiane   → k proposés   | k retenus (lib/classes.js)');
for (const [rec, l] of [...inv].sort()) {
  const c = CLASSES[rec];
  if (!c) { console.log(rec.padEnd(26), '(absente de lib/classes.js)'); continue; }
  const lo = Math.min(...l.map(e => e.lo)), hi = Math.max(...l.map(e => e.hi)), med = geo(l.map(e => Math.sqrt(e.lo * e.hi)));
  const vue1 = c.nominalCm * echelleVue(c);   // taille vue de la classe k = 1
  const k = [...new Set([lo, med, hi].map(x => crans.reduce((b, q) =>
    Math.abs(Math.log(q * vue1 / x)) < Math.abs(Math.log(b * vue1 / x)) ? q : b)))].map(q => +q.toFixed(2));
  console.log(rec.padEnd(26), vue1.toFixed(1).padStart(7), `  ${lo.toFixed(1).padStart(5)} → ${hi.toFixed(1).padEnd(6)}  ${med.toFixed(1).padStart(6)}   →`,
    JSON.stringify(k).padEnd(16), '|', JSON.stringify(c.k));
  for (const e of l) console.log('   ', e.espece.padEnd(28), e.lo.toFixed(1), '→', e.hi.toFixed(1));
}

// SYMBIOSE — tools/splat/lib/classes.js (sprint RELIQUATS DES PLANTES ②)
// Les CLASSES DE TAILLE précuites par recette (décision E8 de Nico) : une pièce n'est
// plus cuite à UNE taille nominale, mais à 1-3 tailles ; la vue pose la classe la plus
// proche de la taille réelle de l'organe (PlantRenderer.Splats.cs, SplatPlanches.cs).
//
// Une classe = un facteur `k` sur la recette sculptée : la recette ne change PAS (même
// monde ink-studio), seule la caméra s'approche — photographier à l'échelle k au palier
// z, c'est photographier au zoom z·k (lib/iso.js). La classe k = 1 donne donc les pièces
// d'avant à l'octet, dans les mêmes planches (aucune régénération inutile, D2).
// Les k sont pris sur l'échelle ×√2 (… 0,5 · 0,71 · 1 · 1,41 …), choisis d'après
// l'inventaire des fiches de la vue (tools/splat/inventaire_tailles.js, 00_etat ②).
//
// `nominalCm` = taille de la classe k = 1 DANS LA MESURE DE LA VUE (celle que le crochet
// passe) : longueur `FeuillePosee.Long` d'une feuille, rayon du disque que l'ancien
// dessin traçait pour une tête ou un fruit, longueur d'un épi.
//
// ÉCHELLE √2 DES ORGANES RONDS (`rond`, kickoff ② §2) : l'ancien dessin trace un disque
// de r cm à r × 0,39 px/cm (PxPerCmX) ; la caméra, fidèle au losange du sol, montre une
// boule de r cm à r × 0,39·√2 = 0,55 px/cm. Une boule cuite de rayon r a donc la taille
// d'un disque de la vue de rayon r·√2 : c'est la taille VUE qu'écrit le manifeste
// (`taille_cm`), et la vue choisit sur elle → la correction est faite une fois, ici.
// Les feuilles, posées au sol (Iso), sont déjà à la bonne échelle : pas de correction.
//
// 📖 Pédagogie : c'est la gamme E12 des résistances — on ne fabrique pas toutes les
// valeurs, mais des crans en rapport constant ; on prend le cran le plus proche.

'use strict';

// recette → { nominalCm, rond?, k: [facteurs cuits] }. Absente = non concernée
// (touffes et fleuron du kit : tailles en px du kit, cf. recettes/touffe.js).
const CLASSES = {
  // Feuilles : longueur du limbe (cm au sol).
  feuille_ovale: { nominalCm: 9, k: [0.35, 1, 2] },
  feuille_scie: { nominalCm: 9, k: [0.71, 1, 1.41] },
  feuille_scie_gaufree: { nominalCm: 9, k: [0.25, 0.5, 1] },
  feuille_lanceolee: { nominalCm: 14, k: [0.5, 0.71, 1] },
  feuille_lanceolee_gaufree: { nominalCm: 14, k: [0.5, 1, 2] },
  feuille_dentee: { nominalCm: 15, k: [0.5, 0.71, 1] },
  feuille_spatule: { nominalCm: 8, k: [0.5, 0.71, 1] },
  feuille_lobee: { nominalCm: 12, k: [0.35, 0.71, 1.41] },
  feuille_coeur: { nominalCm: 10, k: [0.35, 1, 2] },
  feuille_lierre: { nominalCm: 7, k: [0.71, 1] },
  feuille_paume: { nominalCm: 20, k: [1] },
  feuille_palmee: { nominalCm: 15, k: [0.5, 1, 1.41] },
  feuille_triade: { nominalCm: 14, k: [0.35, 0.5, 0.71] },
  feuille_plume: { nominalCm: 18, k: [0.18, 0.35, 0.71] },
  feuille_ruban: { nominalCm: 30, k: [0.125, 0.25, 0.35] },
  feuille_cuillere: { nominalCm: 4, k: [0.71, 1, 1.41] },
  feuille_composee: { nominalCm: 18, k: [0.35, 1, 1.41] },
  feuille_aiguille: { nominalCm: 3, k: [1] },
  // Têtes, fruits, boutons : rayon (cm), organes ronds.
  tete_capitule: { nominalCm: 3, rond: true, k: [0.71] },
  tete_bouquet: { nominalCm: 1.8, rond: true, k: [0.71, 1.41] },
  tete_chapelet: { nominalCm: 1.2, rond: true, k: [0.71] },
  tete_epi: { nominalCm: 1.4, rond: true, k: [0.5, 0.71, 1.41] },
  tete_ombelle: { nominalCm: 5, rond: true, k: [0.71] },
  tete_boule: { nominalCm: 2, rond: true, k: [0.35, 0.71, 1.41] },
  tete_grappe: { nominalCm: 1.5, rond: true, k: [0.35, 1.41] },
  tete_soleil: { nominalCm: 12.5, rond: true, k: [0.71] },
  tete_etoile: { nominalCm: 2.5, rond: true, k: [0.25, 0.5, 1] },
  tete_pendante: { nominalCm: 1.3, rond: true, k: [0.5, 0.71, 1] },
  tete_corolle: { nominalCm: 1.3, rond: true, k: [0.5, 0.71] },
  tete_trompette: { nominalCm: 5, rond: true, k: [0.71] },
  tete_papillon: { nominalCm: 1.4, rond: true, k: [0.71] },
  fruit_globe: { nominalCm: 2, rond: true, k: [0.25, 0.5, 1] },
  fruit_long: { nominalCm: 3.2, rond: true, k: [0.35, 0.5, 0.71] },
  bouton: { nominalCm: 0.6, rond: true, k: [1] },
  // Organes allongés : longueur (cm).
  epi_ble: { nominalCm: 9, k: [0.71, 1] },
  epi_barbu: { nominalCm: 13, k: [0.71, 1] },
  panicule: { nominalCm: 11, k: [0.71, 1] },
  gousse: { nominalCm: 15, k: [1] },
  chaton: { nominalCm: 6, k: [1] },
};

// Taille vue d'une classe k = 1 rapportée à la taille sculptée (√2 pour un organe rond).
const echelleVue = c => (c.rond ? Math.SQRT2 : 1);

// Classes d'une recette : [{ k, tailleCm }] ; [{ k: 1 }] sans taille si non concernée.
function classesDe(nom) {
  const c = CLASSES[nom];
  if (!c) return [{ k: 1, tailleCm: null }];
  return c.k.map(k => ({ k, tailleCm: +(c.nominalCm * echelleVue(c) * k).toFixed(2) }));
}

// Suffixe de planche d'une classe : '' pour k = 1 (planches d'avant), '_k71' pour 0,71.
const suffixe = k => (k === 1 ? '' : '_k' + Math.round(k * 100));

module.exports = { CLASSES, echelleVue, classesDe, suffixe };

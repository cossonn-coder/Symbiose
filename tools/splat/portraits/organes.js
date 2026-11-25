// SYMBIOSE — tools/splat/portraits/organes.js (sprint PRÉCUISSON SPLATS ⑥)
// Les ORGANES d'un portrait = les recettes du jardin (②③), retrouvées par le nom
// que la VUE leur donne (champ `vue` de chaque recette : « FormeFeuille.Ovale »,
// « FormeTete.Soleil »…), posées en pleine couleur par le mandataire (sculpteur.js).
// Aucune table « forme → recette » recopiée ici : l'index se construit en lisant
// les recettes elles-mêmes.
//
// Le portrait travaille en CENTIMÈTRES (repère ink : Y en haut) ; `Portrait.g`
// convertit en unités ink. Toute la géométrie passe par `place`, qui tient aussi
// la BOÎTE ENGLOBANTE (cadrage automatique de la caméra, cuire_portraits.js).
//
// Tailles : une recette est cuite à sa taille NOMINALE (②③). Feuilles : longueur
// nominale = `spec.longCm`, sinon (rayonCm − 1) / 1,08 (la marge que lib/feuille.js
// ajoute au rayon). Têtes : rayon nominal des fleurs = table des classes (lib/classes.js,
// RELIQUATS ⑤), sinon ≈ rayonCm / 1,75 ; mise à l'échelle bornée [0,5 ; 2] (une tête de
// 1 cm sur une plante de 2 m resterait sinon invisible).
//
// 📖 Pédagogie : « index inversé » — au lieu d'écrire à la main quelle recette sert
// quelle forme, on demande à chaque recette ce qu'elle sert et on retourne la liste.
// Ajouter une recette au jardin l'ajoute aux portraits, sans toucher à ce fichier.

'use strict';

const fs = require('fs');
const path = require('path');
const { place, repere } = require('./sculpteur');
const details = require('../lib/details');
const { CLASSES } = require('../lib/classes');

const DOSSIER = path.join(__dirname, '..', 'recettes');

// vue (« FormeFeuille.Ovale », « FormeTete.Capitule (tete de graines) »…) → recette.
const INDEX = (() => {
  const idx = new Map();
  for (const f of fs.readdirSync(DOSSIER).sort()) {
    const r = require(path.join(DOSSIER, f));
    if (!r.nom || !r.sculpter || r.nom.startsWith('touffe')) continue;
    for (const v of r.vue || []) if (!idx.has(v)) idx.set(v, r);
  }
  return idx;
})();

const trouver = cle => {
  const r = INDEX.get(cle);
  if (!r) throw new Error('organes : aucune recette ne sert « ' + cle + ' »');
  return r;
};
// Une clé dont la vue précise une parenthèse : « FormeTete.Capitule (tete de graines) ».
const trouverDebut = (debut, mot) => {
  for (const [v, r] of INDEX) if (v.startsWith(debut) && v.includes(mot)) return r;
  return null;
};

// Recette d'une feuille de la vue (forme + marque de relief).
function recetteFeuille(forme, marque) {
  if (marque === 'Gaufre' && INDEX.has(`FormeFeuille.${forme} + MarqueFeuille.Gaufre`))
    return trouver(`FormeFeuille.${forme} + MarqueFeuille.Gaufre`);
  return trouver('FormeFeuille.' + forme);
}

// Recette d'une tête : en fleur, ou mûre (« graines », « gousses ») si la vue en a une.
function recetteTete(forme, mure = false) {
  if (forme === 'Aucune') return null;
  if (mure) {
    const r = trouverDebut('FormeTete.' + forme, 'graines') || trouverDebut('FormeTete.' + forme, 'gousses');
    if (r) return r;
  }
  return INDEX.get('FormeTete.' + forme) || trouverDebut('FormeTete.' + forme, 'en fleur');
}

const longueurNominale = r => (r.spec && r.spec.longCm) || (r.rayonCm - 1) / 1.08;
const rayonNominal = r => r.rayonCm / 1.75;
// RELIQUATS ⑤ : rayon nominal de la table des classes (lib/classes.js, rayon des FLEURS) quand il
// existe — `rayonCm` d'une recette allongée (épi, grappe, chapelet) englobe sa LONGUEUR, et
// rapportait sa tête à 0,5 (molène sans épi jaune, papillons du haricot minuscules).
const echelleTete = (r, tailleCm) =>
  Math.max(0.5, Math.min(2, tailleCm / ((CLASSES[r.nom] && CLASSES[r.nom].nominalCm) || rayonNominal(r))));

// Le contexte d'un portrait : sculpteur, matériaux, échelle, boîte englobante.
class Portrait {
  constructor(S, K, M, g, resMin) {
    Object.assign(this, { S, K, M, g, resMin });
    this.boite = [[Infinity, Infinity, Infinity], [-Infinity, -Infinity, -Infinity]];
  }
  noter(p, marge = 0) {
    for (let i = 0; i < 3; i++) {
      this.boite[0][i] = Math.min(this.boite[0][i], p[i] - marge);
      this.boite[1][i] = Math.max(this.boite[1][i], p[i] + marge);
    }
  }
  // Sculpteur à l'échelle du portrait, repère (Q, T en cm, échelle s de la recette).
  mandataire(Q, T, s, detasser = false) {
    // la recette sculpte en unités ink (1 = 10 cm) : échelle × 10 cm/unité × g unité/cm
    return place(this.S, { Q, T: T.map(v => v * this.g), s: s * 10 * this.g, resMin: this.resMin, detasser });
  }
  // Tige, tuteur, stolon : points en cm.
  tube(pts, r0, r1, mat) {
    for (const p of pts) this.noter(p, r0);
    this.S.tube(pts.map(p => p.map(v => v * this.g)), r0 * this.g, r1 * this.g, mat,
      { res: Math.max(this.resMin, Math.min(r0, r1) * this.g * 0.8) });
  }
  boule(c, r, mat, aplat = 1) {
    this.noter(c, r);
    this.S.ball(c.map(v => v * this.g), aplat === 1 ? r * this.g : [r * this.g, r * aplat * this.g, r * this.g], mat,
      { res: Math.max(this.resMin, r * this.g * 0.3) });
  }
  // Pose une recette : attache en `at` (cm), organe vers `dir` (3D), échelle `s`.
  // `dmats` (RELIQUATS ⑤) : une couleur par détail cuit de la recette (lib/details.js),
  // sculptés sur les sites que rend la recette, dans le même mandataire (drosera).
  poser(r, at, dir, s, mats, k = 0, haut = [0, 1, 0], dmats = null) {
    const Q = repere(dir, haut);
    const S = this.mandataire(Q, at, s, r.trous === false);   // organes ③ : verticale tassée
    this.noter(at, r.rayonCm * s * 0.6);   // rayonCm englobe large (marge de cuisson)
    const ctx = { S, K: this.K, M: { organe: mats[0], couches: dmats ? [...mats, ...dmats] : mats },
      variante: k % (r.variantes || 1), inclinaison: 0, trou: null };
    const sites = r.sculpter(ctx);
    if (dmats) details.sculpter(ctx, r, sites, mats.length);
  }
  feuille(forme, marque, at, dir, longCm, mat, k, dmats = null) {
    const r = recetteFeuille(forme, marque);
    this.poser(r, at, dir, longCm / longueurNominale(r), [mat], k, undefined, dmats);
  }
  // Tête : `tailleCm` = TeteCm de la fiche. mats = une couleur par couche de la recette.
  tete(forme, at, dir, tailleCm, mats, k, mure = false) {
    const r = recetteTete(forme, mure);
    if (!r) return;
    this.poser(r, at, dir, echelleTete(r, tailleCm), mats, k);
    return r;
  }
  fruit(rayonCm, allonge, at, dir, mats, k) {
    const r = trouver(allonge > 1 ? 'PoserFruit (Allonge > 1)' : 'PoserFruit (Allonge <= 1)');
    this.poser(r, at, dir, (rayonCm / (allonge > 1 ? 3.2 : 2)), mats, k);
  }
}

module.exports = { Portrait, recetteFeuille, recetteTete, echelleTete, trouver, INDEX };

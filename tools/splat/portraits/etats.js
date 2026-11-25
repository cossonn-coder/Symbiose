// SYMBIOSE — tools/splat/portraits/etats.js (sprint PRÉCUISSON SPLATS ⑥)
// Les TROIS ÉTATS d'un portrait (D6) et leurs couleurs.
//   jeune — taille du stade jeune du MOTEUR (hauteur du 2ᵉ stade / hauteur du dernier,
//           bornée [0,3 ; 0,6] : une plantule de 3 cm serait illisible), feuillage
//           clairsemé, ni fleur ni fruit ;
//   mure  — pleine saison : taille adulte, fleurs, fruits (mi-mûrs mi-verts) ;
//   fin   — selon le CYCLE DE VIE DU MOTEUR (`life_cycle`, `deciduous`) :
//           annuelle / bisannuelle → fin de cycle : feuillage sec, têtes en graines,
//           fruits mûrs ; caduque → hiver nu (bois seul) ; vivace persistante →
//           hiver : feuillage assombri, sans fleur.
// Le moteur est la source du cycle : l'ortie est « persistante » pour lui
// (`deciduous = False`), son portrait d'hiver garde donc ses feuilles.
//
// Couleurs : la palette d'espèce de la vue (OrganPalette : limbe, fleur, fruit vert,
// fruit mûr, tons d'automne), lue par table_cs.js. Les couleurs d'ÉTAT (sec, hiver)
// sont des mélanges vers des teintes fixes ci-dessous [choix, à juger au F5].
//
// 📖 Pédagogie : séparer « quoi » (l'état : fleurs oui/non, densité) de « comment »
// (les ports qui sculptent) — les ports ne testent jamais le nom d'un état, ils
// lisent ses drapeaux. Ajouter un 4ᵉ état ne toucherait aucun port.

'use strict';

const { melange } = require('./sculpteur');

const SEC = '#8a7048', HIVER = '#4a5048', SOMBRE = '#1f3a1f', CLAIR = '#c8e070', GRAINE = '#7a6040';

// Les 3 états d'une espèce (fiche moteur de moteur.py).
function etats(moteur) {
  const st = moteur.stades, hMax = Math.max(...st.map(s => s.hauteur_cm || 0)) || 1;
  const hJeune = (st[Math.min(1, st.length - 1)].hauteur_cm || hMax) / (st.length >= 3 ? 1 : 2.5);
  const jeune = Math.max(0.3, Math.min(0.6, hJeune / hMax));
  const cycle = moteur.life_cycle;
  const fin = cycle !== 'perennial'
    ? { nom: 'fin', libelle: 'fin de cycle', echelle: 1, densite: 0.55, fleurs: true, graines: true, fruits: true, maturite: 1, feuillage: 'sec', retombe: 0.35 }
    : moteur.deciduous
      ? { nom: 'fin', libelle: 'hiver (nu)', echelle: 1, densite: 0, fleurs: false, graines: false, fruits: false, maturite: 1, feuillage: 'nu', retombe: 0 }
      : { nom: 'fin', libelle: 'hiver (persistant)', echelle: 1, densite: 0.75, fleurs: false, graines: false, fruits: false, maturite: 1, feuillage: 'hiver', retombe: 0.15 };
  return [
    { nom: 'jeune', libelle: 'jeune', echelle: jeune, densite: 0.6, fleurs: false, graines: false, fruits: false, maturite: 0, feuillage: 'ete', retombe: 0 },
    { nom: 'mure', libelle: 'mûre, pleine saison', echelle: 1, densite: 1, fleurs: true, graines: false, fruits: true, maturite: 0.6, feuillage: 'ete', retombe: 0 },
    fin
  ];
}

const dieze = c => (String(c).startsWith('#') ? c : '#' + c);

// Couleurs nommées d'un portrait (→ sculpteur.palette). `pal` = OrganPalette de la vue.
function couleurs(etat, pal, tigeHex, automneDefaut) {
  const leaf = dieze(pal.leaf), tige = tigeHex ? dieze(tigeHex) : melange(leaf, '#5a4a30', 0.3);
  const aut = (pal.automne && pal.automne.length ? pal.automne : automneDefaut).map(dieze);
  const f = {
    ete: [leaf, melange(leaf, SOMBRE, 0.2), melange(leaf, CLAIR, 0.15)],
    hiver: [melange(leaf, HIVER, 0.4), melange(leaf, HIVER, 0.55), melange(leaf, SOMBRE, 0.35)],
    sec: [melange(aut[0], SEC, 0.35), melange(aut[1 % aut.length], SEC, 0.5), melange(leaf, SEC, 0.6)],
    nu: [leaf, leaf, leaf]
  }[etat.feuillage];
  const sec = etat.feuillage === 'sec';
  return {
    sol: '#4a3426', f0: f[0], f1: f[1], f2: f[2],
    tige: sec ? melange(tige, SEC, 0.5) : tige,
    bois: '#5a4430',
    fleur: dieze(pal.flower), coeur: '#d8a830',
    graine: melange(dieze(pal.ripe), GRAINE, 0.3),
    vert: dieze(pal.unripe), mur: dieze(pal.ripe)
  };
}

// Matériaux des couches d'une tête (noms des couches de la recette ③).
function matsTete(M, r, etat, forme) {
  const graines = etat.graines;
  return (r.couches || ['fleur']).map((c, k) => {
    if (k === 0) return graines ? M.graine : M.fleur;
    if (c === 'coeur') return forme === 'Soleil' || graines ? M.graine : M.coeur;   // disque du tournesol = fruit mûr (vue)
    if (c === 'revers' || c === 'sepales') return M.f1;
    if (c === 'silicules') return graines ? M.graine : M.vert;
    return M.tige;                                                                 // rayons d'ombelle, pédoncules
  });
}

// Matériaux d'un fruit (fruit | pédoncule) : mûr ou vert selon la maturité de l'état.
const matsFruit = (M, etat, h) => [h < etat.maturite ? M.mur : M.vert, M.tige];

module.exports = { etats, couleurs, matsTete, matsFruit };

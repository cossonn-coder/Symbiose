// SYMBIOSE — tools/splat/portraits/ports_bas.js (sprint PRÉCUISSON SPLATS ⑥)
// Les ports BAS d'une plante entière, pour son portrait : ROSETTE, TAPIS, RAMPANTE,
// et la PRAIRIE (trèfle, dactyle, fétuque, plantain), plus les outils communs aux
// ports (ports_hauts.js les réutilise).
//
// Chaque port lit la LIGNE DE L'ESPÈCE de la vue (FichePort, PlantRenderer.PortsFiches.cs,
// lue par table_cs.js) avec la MÊME grammaire que la vue — rayon, feuilles, dressée,
// têtes, hampes — mais en 3D vraie, sans palier ni pose de vent : c'est une
// illustration (conception §5), pas la plante du jardin (D1 : le jardin suit ses
// vrais segments ; le portrait n'a pas cette contrainte, D3).
//
// La prairie n'a pas de FichePort dans la vue (port codé, constantes de
// PlantRenderer.Prairie.cs / .Graminees.cs) : on lui compose une fiche à partir de
// ces constantes et de la hauteur du MOTEUR, puis on réutilise rosette / tapis /
// chaume. Aucun port n'est inventé.
//
// Repère : centimètres, Y en haut, la plante au collet (0, 0, 0).
// Déterministe : tout aléa = h(i, j) (K.hash), zéro Math.random (philo #3).
//
// 📖 Pédagogie : « l'angle d'or » 137,5° (2,39996 rad) — chaque feuille tourne de
// cet angle par rapport à la précédente ; aucune ne recouvre exactement une autre.
// C'est la phyllotaxie réelle de la plupart des rosettes, et celle de la vue.

'use strict';

const { matsTete, matsFruit } = require('./etats');
const { recetteTete, INDEX } = require('./organes');

const trouverVue = mot => [...INDEX].find(([v]) => v.includes(mot))[1];

const OR = 2.39996;
const dirA = (a, m = 0) => [Math.cos(a) * Math.cos(m), Math.sin(m), Math.sin(a) * Math.cos(m)];
const polaire = (r, a, y = 0) => [r * Math.cos(a), y, r * Math.sin(a)];
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const lerp = (a, b, t) => a + (b - a) * t;
const matFeuille = (M, h, k) => [M.f0, M.f1, M.f2][Math.min(2, Math.floor(h(k, 97) * 3))];

// Les outils d'un port : contexte du portrait, matériaux, aléa, état.
function outils(P, M, h, etat) {
  return {
    P, M, h, etat, E: etat.echelle,
    nb: n => Math.max(etat.densite > 0 ? 1 : 0, Math.round(n * etat.densite)),
    feuille(f, at, a, m, longCm, k) {
      if (etat.densite <= 0) return;
      P.feuille(f.Feuille, f.Marque, at, dirA(a, m - etat.retombe), longCm, matFeuille(M, h, k), k);
    },
    // `mure` : la tête mûre de la vue (graines, gousses) — en fin de cycle, ou forcée
    // (gousses vertes du haricot en pleine saison).
    tete(f, at, a, k, taille = f.TeteCm, mure = etat.graines) {
      if (!etat.fleurs || f.Tete === 'Aucune') return;
      const r = recetteTete(f.Tete, mure);
      if (!r) return;
      const mats = mure && !etat.graines ? (r.couches || [0]).map((_, i) => (i ? M.tige : M.vert)) : matsTete(M, r, etat, f.Tete);
      P.tete(f.Tete, at, dirA(a), taille * Math.sqrt(etat.echelle), mats, k, mure);
    },
    // Épi / panicule du chaume (recettes « FicheChaume.* » du ③), à sa longueur `EpiCm`.
    epi(c, sorte, at, a, k) {
      const r = trouverVue(sorte === 'Panicule' ? 'FicheChaume.Panicule' : sorte === 'Barbu' ? 'BarbeCm' : 'EpiLargeCm');
      const s = Math.max(0.4, Math.min(2.5, c.EpiCm * Math.sqrt(etat.echelle) / ((r.rayonCm - 1) / 1.08)));
      P.poser(r, at, dirA(a), s, [etat.graines ? M.graine : M.fleur], k);
    },
    fruit(fr, at, a, k) {
      if (!etat.fruits || !fr) return;
      P.fruit(fr.RayonCm, fr.Allonge, at, dirA(a), matsFruit(M, etat, h(k, 61)), k);
    },
    hampe(base, haut, rCm) { P.tube([base, add(base, [0.04 * (haut[0] - base[0]), 0.55 * (haut[1] - base[1]), 0.04 * (haut[2] - base[2])]), haut], rCm, rCm * 0.7, M.tige); }
  };
}

// Les stades de la vue où la hampe est montée (`StadesHampe`) → l'état la montre-t-il ?
const hampeVisible = (f, etat) => etat.fleurs;

// ROSETTE (pissenlit, mâche, molène, carotte, ail…) : feuilles depuis le collet, à
// l'angle d'or, d'autant plus dressées que `Dressee` ; hampes au centre.
function rosette(o, f) {
  const { P, M, h, E } = o;
  const n = o.nb(f.Feuilles), long = Math.hypot(f.RayonCm, f.HautFeuillesCm) * 0.85 * E;
  for (let k = 0; k < n; k++) {
    const a = k * OR + h(k, 1), t = k / Math.max(1, n - 1);
    const m = lerp(0.05, 1.15, f.Dressee) + 0.25 * t * (1 - f.Dressee) + 0.1 * (h(k, 2) - 0.5);
    o.feuille(f, [0, 0.3, 0], a, m, long * (1 - 0.35 * t) * (0.85 + 0.3 * h(k, 3)), k);
  }
  if (f.Pied) P.boule([0, 0.2, 0], Math.max(0.8, f.EpaisseurTigeCm * 2.2) * E, M.pied, 0.8);
  if (!hampeVisible(f, o.etat) || f.Hampes <= 0) return;
  const H = f.HauteurAdulteCm * E;
  for (let j = 0; j < f.Hampes; j++) {
    const a = j * OR + 0.7, ecart = f.Hampes > 1 ? 0.18 * f.RayonCm * E : 0.02 * f.RayonCm;
    const haut = polaire(ecart, a, H * (0.85 + 0.3 * h(j, 5)));
    o.hampe([0, 0, 0], haut, Math.max(0.15, f.EpaisseurTigeCm * 0.4));
    for (let i = 0; i < f.FeuillesHampe; i++) {
      const t = (i + 1) / (f.FeuillesHampe + 1);
      o.feuille(f, [haut[0] * t, haut[1] * t * 0.85, haut[2] * t], a + i * OR, 0.5, long * 0.45 * (1 - 0.6 * t), 50 + i);
    }
    o.tete(f, haut, a, 10 + j);
  }
}

// TAPIS (fraisier, violette, minette, sphaigne ; trèfle) : feuilles à `Folioles`
// folioles sur un pétiole court, sur `Couvre` du rayon ; stolons ; fleurs au-dessus.
function tapis(o, f) {
  const { P, M, h, E } = o, t = f.Tapis, R = f.RayonCm * E, H = f.HautFeuillesCm * E;
  if (t.Grains > 0) {                                  // sphaigne : coussin de capitules, sans feuille
    for (let k = 0; k < o.nb(t.Grains * 3); k++) {
      const p = polaire(R * Math.sqrt(h(k, 1)) * 0.95, k * OR, H * (0.6 + 0.4 * h(k, 2)));
      P.boule(p, 1.4 * Math.sqrt(E), matFeuille(M, h, k), 0.7);
    }
    return;
  }
  for (let k = 0; k < o.nb(f.Feuilles); k++) {
    const a = k * OR + h(k, 1), d = R * t.Couvre * (0.35 + 0.65 * Math.sqrt(h(k, 2)));
    const bout = polaire(d * 0.8, a, H * (0.45 + 0.55 * h(k, 3)));
    P.tube([[0, 0, 0], polaire(d * 0.4, a, bout[1] * 0.8), bout], 0.12, 0.08, M.tige);
    for (let i = 0; i < t.Folioles; i++) {
      const da = t.Folioles > 1 ? (i - (t.Folioles - 1) / 2) * 0.75 : 0;
      o.feuille(f, bout, a + da, 0.15, t.FeuilleCm * Math.sqrt(E), k * 5 + i);
    }
  }
  for (let s = 0; s < (o.etat.nom === 'jeune' ? 0 : t.Stolons); s++) {
    const a = s * OR + 0.4, fin = polaire(R * 1.05, a, 0.3);
    P.tube([[0, 0.3, 0], polaire(R * 0.5, a + 0.2, 1.5), fin], 0.15, 0.1, M.stolon || M.tige);
    if (t.Plantules) for (let i = 0; i < 3; i++) o.feuille(f, fin, a + i * 2.1, 0.4, t.FeuilleCm * 0.6, 300 + s * 3 + i);
  }
  for (let k = 0; k < t.Fleurs; k++) {
    const a = k * OR * 1.3 + 0.9, p = polaire(R * t.Couvre * 0.5 * Math.sqrt(h(k, 7)), a, H * 1.05);
    o.hampe([0, 0, 0], p, 0.1);
    o.tete(f, p, a, 400 + k);
  }
  if (f.Fruit) for (let k = 0; k < t.Fleurs; k++) {
    const fr = f.Fruit, a = k * OR + 2.2;
    o.fruit(fr, polaire(R * lerp(fr.DBas, fr.DHaut, h(k, 8)), a, H * lerp(fr.ZBas, fr.ZHaut, h(k, 9))), a, 500 + k);
  }
}

// RAMPANTE (courgette) : grandes feuilles au bout de longs pétioles, fleurs et
// fruits couchés au pied.
function rampante(o, f) {
  const { P, M, h, E } = o, R = f.RayonCm * E, H = f.HautFeuillesCm * E;
  for (let k = 0; k < o.nb(f.Feuilles); k++) {
    const a = k * OR + h(k, 1), d = R * (0.35 + 0.4 * h(k, 2)), y = H * (0.55 + 0.45 * h(k, 3));
    const bout = polaire(d, a, y);
    P.tube([[0, 2, 0], polaire(d * 0.4, a, y * 0.85), bout], f.EpaisseurTigeCm * 0.25, 0.25, M.tige);
    o.feuille(f, bout, a, lerp(0.05, 0.5, f.Dressee) + 0.1, R * 0.55, k);
  }
  P.tube([[0, 0, 0], [0, 4 * E, 0]], f.EpaisseurTigeCm * 0.6 * E + 0.3, f.EpaisseurTigeCm * 0.5 * E + 0.2, M.tige);
  for (let k = 0; k < 3; k++) o.tete(f, polaire(R * 0.15, k * 2.1 + 0.5, 6 * E), k * 2.1, 600 + k);
  if (f.Fruit) for (let k = 0; k < 2; k++) {
    const fr = f.Fruit, a = k * 3.3 + 1.1;
    o.fruit(fr, polaire(R * lerp(fr.DBas, fr.DHaut, 0.5 + 0.5 * h(k, 4)), a, fr.RayonCm), a, 700 + k);
  }
}

// PRAIRIE : une fiche composée des constantes de la vue et de la hauteur du moteur.
function fichePrairie(port, C, base, hCm) {
  const commun = { ...base, StadesHampe: null, FeuillesHampe: 0, MelangeFruit: 0, Marque: 'Aucune', Pied: null,
    Tige: null, Chaume: null, Tapis: null, Buisson: null, Fruit: null, EpaisseurTigeCm: 0.2 };
  if (port === 'Trefle')
    return { ...commun, Forme: 'Tapis', RayonCm: C.RayonTrefleCm, HautFeuillesCm: C.HauteurTrefleCm,
      HauteurAdulteCm: C.HauteurTrefleCm, Feuilles: C.FeuillesTrefle, Feuille: 'Coeur', LargeurFeuille: 0.8,
      Dressee: 0, Tete: 'Boule', TeteCm: C.RayonPomponCm, Hampes: 0,
      Tapis: { Folioles: 3, FeuilleCm: C.TailleFolioleCm, Couvre: 0.95, Fleurs: C.PomponsMax, SousCouche: true,
        Stolons: 0, Stolon: null, Plantules: false, Grains: 0 } };
  if (port === 'Plantain')
    return { ...commun, Forme: 'Rosette', RayonCm: C.RayonPlantainCm, HautFeuillesCm: C.LeveePlantainCm,
      HauteurAdulteCm: Math.min(36, hCm), Feuilles: C.FeuillesPlantain, Feuille: 'Lanceolee',
      LargeurFeuille: C.LargeurPlantain, Dressee: 0.35, Tete: 'Epi', TeteCm: 1.2, Hampes: 4 };
  const dactyle = port === 'Dactyle';                  // graminées : rayon et hauteur de la vue (Prairie.cs)
  const H = dactyle ? Math.min(100, Math.max(4, hCm)) : Math.min(30, Math.max(2, hCm));
  const R = dactyle ? Math.min(34, Math.max(3, hCm * 0.42)) : Math.min(16, Math.max(2, hCm * 0.6));
  return { ...commun, Forme: 'Chaume', RayonCm: R, HautFeuillesCm: H, HauteurAdulteCm: H, Feuilles: 0,
    Feuille: 'Ruban', LargeurFeuille: 0, Dressee: 1, Tete: dactyle ? 'Boule' : 'Aucune', TeteCm: 1.2, Hampes: 1,
    Chaume: { Brins: dactyle ? 5 : 6, EcartPied: 0.3, Evase: 0.35, Couleur: null, Rubans: dactyle ? C.BrinsDactyle : 16,
      RubanCm: dactyle ? C.LargeurDactyleCm : 0.4, EpiCm: H * 0.25, EpiLargeCm: 0, Penche: 0.2, BarbeCm: 0,
      Panicule: !dactyle, Noeuds: 0, Panaches: 0, PanacheCm: 0 } };
}

module.exports = { OR, dirA, polaire, add, lerp, matFeuille, outils, rosette, tapis, rampante, fichePrairie };

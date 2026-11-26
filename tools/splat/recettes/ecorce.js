// SYMBIOSE — tools/splat/recettes/ecorce.js (sprint BOIS & ARBRES ②)
// ÉCORCES CUITES : un cylindre sculpté PÉRIODIQUE en longueur, par essence × âge, que
// tools/splat/cuire_ecorces.js photographie de face → une BANDE DE TONS plaquée par la vue le
// long du tube lissé de ① (v = longueur d'arc en cm, u en travers).
//
// Âges (conception B2) : rameau lisse / branche / tronc à rhytidome — la vue choisit l'âge par
// l'épaisseur du bois. Chaque âge a un diamètre de référence (la bande en travers = ce
// diamètre × WoodWidthFactor 1,5, comme le bois dessiné) et une PÉRIODE en cm.
//
// PÉRIODICITÉ PAR CONSTRUCTION : chaque motif tiré au hash à la hauteur y0 ∈ [0, P) est posé
// en y0 − P, y0 et y0 + P ; le cylindre déborde la fenêtre photographiée [0, P) des deux côtés.
// Le pas d'échantillonnage du sculpteur est un diviseur de P (cuire_ecorces.js) : la rangée
// de splats en y et celle en y + P sont les mêmes → la coupure du haut rejoint celle du bas.
// La couture est MESURÉE à chaque cuisson (rangées de débord comparées à l'octet).
//
// COUCHES : 0 = relief (le ton vient de l'occlusion : crevasse = creux, bord = ombre) ;
// 1 = pigment sombre (lenticelles et base noire du bouleau, ton creux quel que soit le
// relief) ; 2 = pigment clair (lenticelles pâles du cerisier, du noisetier : ton clair).
//
// 📖 Pédagogie : un motif périodique se fabrique comme un papier peint — on dessine UN
// lé, et chaque motif qui déborde du bas réapparaît, identique, en haut. Le hash donne le
// motif, la répétition garantit le raccord.
//
// Déterministe : tout aléa vient de K.hash(3000 + n° d'essence, i, j).
'use strict';

const CM = 0.1;                                   // 1 unité ink = 10 cm
const LARGEUR_BOIS = 1.5;                         // = PlantRenderer.WoodWidthFactor
const AGES = [
  { nom: 'rameau', dCm: 1.5, periodeCm: 8 },
  { nom: 'branche', dCm: 6, periodeCm: 16 },
  { nom: 'tronc', dCm: 20, periodeCm: 32 },
];

// Motifs par essence et par âge (conception §3.3). Chaque entrée : [motif, réglages].
// Densités en motifs par période (sur la face vue) ; profondeurs en part du rayon dessiné.
const ESSENCES = {
  AppleTree: [   // gris-brun, écailleux en plaques
    [['lenticelles', { n: 6, couche: 2 }]],
    [['ecailles', { taille: 0.45, prof: 0.10 }]],
    [['ecailles', { taille: 0.42, prof: 0.09 }]]],
  CherryTree: [  // brun-rouge lisse, lenticelles en bandes horizontales
    [['lenticelles', { n: 10, couche: 2, bandes: 3 }]],
    [['lenticelles', { n: 22, couche: 2, bandes: 4, long: 0.10 }]],
    [['lenticelles', { n: 34, couche: 2, bandes: 5, long: 0.14 }], ['rides', { n: 5, prof: 0.04 }]]],
  WalnutTree: [  // gris, crevassé en losanges
    [['lenticelles', { n: 5, couche: 2 }]],
    [['fissures', { n: 9, prof: 0.10, larg: 0.045, long: 0.4 }]],
    [['reseau', { n: 10, prof: 0.08, larg: 0.045, mailles: 3 }]]],
  OakTree: [     // gris-brun, crevassé en long
    [['lenticelles', { n: 4, couche: 2 }]],
    [['fissures', { n: 10, prof: 0.10, larg: 0.045, long: 0.6 }]],
    [['fissures', { n: 22, prof: 0.10, larg: 0.05, long: 0.9 }], ['rides', { n: 8, prof: 0.05 }]]],
  BeechTree: [   // gris uni, lisse à tout âge
    [],
    [['rides', { n: 3, prof: 0.06 }]],
    [['rides', { n: 4, prof: 0.025 }], ['lenticelles', { n: 4, couche: 1, long: 0.05 }]]],
  BirchTree: [   // blanc à lenticelles noires ; tronc âgé : base noire crevassée
    [['lenticelles', { n: 8, couche: 2 }]],
    [['lenticelles', { n: 18, couche: 1, long: 0.16, bandes: 4 }]],
    [['taches', { n: 30, couche: 1 }], ['fissures', { n: 12, prof: 0.09, larg: 0.04, long: 0.5 }]]],
  HornbeamTree: [ // gris, tronc cannelé
    [],
    [['cannelures', { n: 4, prof: 0.07, larg: 0.14 }]],
    [['cannelures', { n: 6, prof: 0.06, larg: 0.12 }], ['rides', { n: 3, prof: 0.02 }]]],
  HazelTree: [   // brun-rouge lustré, lenticelles pâles
    [['lenticelles', { n: 10, couche: 2 }]],
    [['lenticelles', { n: 18, couche: 2, long: 0.08 }]],
    [['lenticelles', { n: 26, couche: 2, long: 0.10 }], ['fissures', { n: 4, prof: 0.04, larg: 0.02, long: 0.3 }]]],
  Alder: [       // brun sombre fissuré
    [['lenticelles', { n: 8, couche: 2 }]],
    [['fissures', { n: 10, prof: 0.10, larg: 0.04, long: 0.35 }]],
    [['ecailles', { taille: 0.22, prof: 0.07 }]]],
  Willow: [      // gris-brun en réseau
    [],
    [['fissures', { n: 9, prof: 0.10, larg: 0.045, long: 0.5 }]],
    [['reseau', { n: 12, prof: 0.10, larg: 0.045, mailles: 4 }]]],
  Fig: [         // gris lisse
    [],
    [['rides', { n: 4, prof: 0.06 }]],
    [['rides', { n: 6, prof: 0.03 }], ['lenticelles', { n: 4, couche: 1, long: 0.05 }]]],
  FirTree: [     // gris argent à poches de résine
    [],
    [['bosses', { n: 6, r: 0.10 }]],
    [['bosses', { n: 8, r: 0.06 }], ['ecailles', { taille: 0.35, prof: 0.04 }]]],
  Generique: [   // plante sans essence : une bande neutre
    [],
    [['fissures', { n: 7, prof: 0.08, larg: 0.04, long: 0.4 }]],
    [['fissures', { n: 10, prof: 0.05, larg: 0.03, long: 0.5 }]]],
};

// Point sur la surface du cylindre (axe = Y ink, face caméra = +Z) : angle a, hauteur y
// (unités), à `dr` du rayon R.
const surface = (R, a, y, dr = 0) => [(R + dr) * Math.sin(a), y, (R + dr) * Math.cos(a)];
const ANGLE_VU = 1.75;                            // ±100° : un peu plus que la face vue

// Angle du motif i sur n : STRATIFIÉ (une strate d'angle par motif, jitter au hash) — un
// tirage libre laissait des moitiés de fût vides (constaté sur la maquette).
const angle = (c, g, i, n) => (((i + 0.5 + 0.9 * (c.h(g, i) - 0.5)) / n) * 2 - 1) * ANGLE_VU;
const mod = (a, n) => ((a % n) + n) % n;

// Copies périodiques d'un motif tiré en y0 : y0 − P, y0, y0 + P.
const copies = (P, f) => { for (const k of [-1, 0, 1]) f(k * P); };

// Les motifs. ctx : S (sculpteur), mat(k), R (rayon), P (période), h(i, j) ∈ [0, 1).
const MOTIFS = {
  // Sillons longitudinaux qui serpentent (chêne, aulne, saule jeune).
  fissures(c, o, g) {
    for (let i = 0; i < o.n; i++) {
      const a0 = angle(c, g, i, o.n), y0 = c.P * c.h(g + 1, i), L = c.P * o.long * (0.6 + 0.8 * c.h(g + 2, i));
      const e = c.R * o.larg * (0.7 + 0.6 * c.h(g + 3, i)), ondule = (L / c.R) * 0.08;
      // Largeur en fuseau (fine aux deux bouts), tracé qui serpente.
      const r = t => e * (0.35 + 0.65 * Math.sin(Math.PI * t));
      copies(c.P, d => c.S.tube([0, 0.2, 0.4, 0.6, 0.8, 1].map((t, k) =>
        surface(c.R, a0 + ondule * (c.h(g + 4 + k, i) - 0.5), y0 + d + L * (t - 0.5), e * 0.3)),
      r, r, c.mat(0), { res: c.res, neg: true }));
    }
  },
  // Réseau de losanges (noyer, saule) : lignes en zigzag de période P / mailles, voisines
  // en opposition de phase et d'amplitude ≈ demi-écart → elles se touchent et ferment les
  // losanges. Sommets décalés au hash par (ligne, sommet mod la période) : irrégulier ET périodique.
  reseau(c, o, g) {
    const pas = c.P / o.mailles, e = c.R * o.larg, A = (Math.PI / o.n) * 1.05, nv = 2 * o.mailles;
    for (let i = 0; i < o.n; i++) {
      const a0 = (i / o.n) * 2 * Math.PI - Math.PI, sens = i % 2 ? -1 : 1;
      if (Math.abs(a0) > ANGLE_VU + A) continue;
      const som = [];
      for (let j = -o.mailles; j <= 3 * o.mailles; j++) {
        const jm = mod(j, nv), tri = j % 2 === 0 ? 1 : -1;
        som.push([a0 + sens * tri * A * (0.75 + 0.5 * c.h(g + 1, i * 64 + jm)),
          j * (pas / 2) + 0.3 * (pas / 2) * (c.h(g + 2, i * 64 + jm) - 0.5)]);
      }
      // Chaque arête subdivisée SUR la surface : une corde droite entre deux sommets éloignés
      // en angle passerait sous l'écorce (le sillon disparaissait au milieu, maquette).
      const pts = [];
      for (let k = 0; k + 1 < som.length; k++)
        for (let q = 0; q < 4; q++) {
          const t = q / 4;
          pts.push(surface(c.R, som[k][0] + (som[k + 1][0] - som[k][0]) * t, som[k][1] + (som[k + 1][1] - som[k][1]) * t, e * 0.3));
        }
      c.S.tube(pts, e, e, c.mat(0), { res: c.res, neg: true });
    }
  },
  // Écailles / plaques (pommier, aulne, sapin âgé) : un appareil de briques irrégulier —
  // fentes verticales décalées d'une rangée à l'autre, joints horizontaux pas toujours
  // fermés. Rangées : un nombre entier par période (périodique), décalages au hash par
  // (colonne, rangée mod nY).
  ecailles(c, o, g) {
    const nA = Math.max(3, Math.round((2 * ANGLE_VU) / o.taille)), nY = Math.max(2, Math.round(1 / (o.taille * 0.9)));
    const da = (2 * ANGLE_VU) / nA, dy = c.P / nY, e = c.R * o.prof * 0.6;
    const r = t => e * (0.4 + 0.6 * Math.sin(Math.PI * t));
    const fente = (a, y, b, z) => c.S.tube([surface(c.R, a, y, e * 0.3), surface(c.R, (a + b) / 2 + 0.1 * da, (y + z) / 2, e * 0.3),
      surface(c.R, b, z, e * 0.3)], r, r, c.mat(0), { res: c.res, neg: true });
    for (let j = -nY; j < 2 * nY; j++) {
      const jm = mod(j, nY), dec = jm % 2 ? 0.5 : 0;
      for (let i = 0; i <= nA; i++) {
        const k = i * 64 + jm, a = -ANGLE_VU + (i + dec + 0.5 * (c.h(g, k) - 0.5)) * da;
        const y = j * dy + 0.25 * dy * (c.h(g + 1, k) - 0.5);
        fente(a, y, a + 0.2 * da * (c.h(g + 2, k) - 0.5), y + dy * (0.85 + 0.3 * c.h(g + 3, k)));
        if (c.h(g + 4, k) < 0.7) fente(a, y, a + da * (0.8 + 0.4 * c.h(g + 5, k)), y + 0.3 * dy * (c.h(g + 6, k) - 0.5));
      }
    }
  },
  // Lenticelles : traits horizontaux courts, pigment (couche 1 sombre, 2 clair), parfois
  // rangés en bandes (cerisier, bouleau).
  lenticelles(c, o, g) {
    const long = o.long || 0.06;
    for (let i = 0; i < o.n; i++) {
      const a0 = angle(c, g, i, o.n);
      const y0 = o.bandes ? c.P * (Math.floor(c.h(g + 1, i) * o.bandes) + 0.5 + 0.15 * (c.h(g + 2, i) - 0.5)) / o.bandes
        : c.P * c.h(g + 1, i);
      const la = long * (0.6 + 0.8 * c.h(g + 3, i)) * (o.bandes ? 1.6 : 1), ep = Math.max(c.res * 1.2, c.R * 0.035);
      copies(c.P, d => {
        const ce = surface(c.R, a0, y0 + d, 0), X = [Math.cos(a0), 0, -Math.sin(a0)];
        c.S.ball(ce, [c.R * la, ep, c.R * 0.03 + c.res], c.mat(o.couche), { res: c.res, ax: [X, [0, 1, 0], [Math.sin(a0), 0, Math.cos(a0)]] });
      });
    }
  },
  // Rides horizontales (hêtre, figuier, cerisier âgé).
  rides(c, o, g) {
    for (let i = 0; i < o.n; i++) {
      const a0 = angle(c, g, i, o.n), y0 = c.P * c.h(g + 1, i), la = 0.08 + 0.14 * c.h(g + 2, i);
      const e = c.R * o.prof, r = t => e * (0.3 + 0.7 * Math.sin(Math.PI * t));
      copies(c.P, d => c.S.tube([-1, 0, 1].map(t => surface(c.R, a0 + la * t, y0 + d + 0.01 * c.P * t * t, e * 0.3)),
        r, r, c.mat(0), { res: c.res, neg: true }));
    }
  },
  // Cannelures (charme) : sillons larges et peu profonds sur toute la longueur, qui ondulent
  // avec la période (une ligne droite est périodique d'elle-même).
  cannelures(c, o, g) {
    for (let i = 0; i < o.n; i++) {
      const a0 = (i / o.n) * 2 * Math.PI - Math.PI + 0.3 * (c.h(g, i) - 0.5), e = c.R * o.larg;
      if (Math.abs(a0) > ANGLE_VU + 0.2) continue;
      const pts = [];
      for (let y = -0.5 * c.P; y <= 1.5 * c.P + 1e-9; y += c.P / 4)
        pts.push(surface(c.R, a0 + 0.06 * Math.sin((2 * Math.PI * y) / c.P + 6 * c.h(g + 1, i)), y, e * (1 - o.prof / o.larg)));
      c.S.tube(pts, e, e, c.mat(0), { res: c.res, neg: true });
    }
  },
  // Poches de résine (sapin) : cloques en relief — leur pourtour s'ombre.
  bosses(c, o, g) {
    for (let i = 0; i < o.n; i++) {
      const a0 = angle(c, g, i, o.n), y0 = c.P * c.h(g + 1, i), r = c.R * o.r * (0.7 + 0.6 * c.h(g + 2, i));
      copies(c.P, d => c.S.ball(surface(c.R, a0, y0 + d, -r * 0.4), [r, r * 1.5, r], c.mat(0), { res: c.res }));
    }
  },
  // Taches de pigment (base noire du bouleau) : grandes plaques sombres irrégulières.
  taches(c, o, g) {
    for (let i = 0; i < o.n; i++) {
      const a0 = angle(c, g, i, o.n), y0 = c.P * c.h(g + 1, i);
      const la = 0.15 + 0.2 * c.h(g + 2, i), hy = c.P * (0.025 + 0.04 * c.h(g + 3, i));
      copies(c.P, d => {
        const X = [Math.cos(a0), 0, -Math.sin(a0)], W = [Math.sin(a0), 0, Math.cos(a0)];
        c.S.ball(surface(c.R, a0, y0 + d, 0), [c.R * la, hy, c.R * 0.012 + c.res], c.mat(o.couche), { res: c.res, ax: [X, [0, 1, 0], W] });
      });
    }
  },
};

// Recette d'une bande : { nom, essence, age, rayonCm, periodeCm, sculpter(ctx) }.
// ctx (cuire_ecorces.js) : S, K, M.couches, res (pas du sculpteur, diviseur de P en unités).
function bande(essence, iAge) {
  const age = AGES[iAge], motifs = ESSENCES[essence][iAge], ie = Object.keys(ESSENCES).indexOf(essence);
  const R = (age.dCm / 2) * LARGEUR_BOIS * CM, P = age.periodeCm * CM;
  return {
    nom: `${essence}_${age.nom}`, essence, age: age.nom, dCm: age.dCm, periodeCm: age.periodeCm,
    rayonCm: (age.dCm / 2) * LARGEUR_BOIS,
    sculpter(ctx) {
      const c = { S: ctx.S, R, P, res: ctx.res, mat: k => ctx.M.couches[k], h: (i, j) => ctx.K.hash(3000 + ie, i, j) };
      // Le fût : de −P à 2P, trois tronçons de longueur P (le sculpteur échantillonne chaque
      // tronçon depuis son début : trois tronçons identiques = mêmes rangées de splats). La
      // fenêtre [0, P) et ses débords mesurés restent loin des calottes des bouts.
      ctx.S.tube([-1, 0, 1, 2].map(k => [0, k * P, 0]), R, R, c.mat(0), { res: ctx.res });
      motifs.forEach(([m, o], k) => MOTIFS[m](c, o, 100 * (k + 1)));
    }
  };
}

module.exports = { AGES, ESSENCES, LARGEUR_BOIS, bande };

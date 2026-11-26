// SYMBIOSE — tools/splat/recettes/limbe_graminee.js (sprint BOIS & ARBRES ③ — rubans des graminées)
// LIMBES DE GRAMINÉE CUITS : une bande de tons PÉRIODIQUE en longueur, plaquée par la vue sur les
// brins et rubans des graminées (PoserBrin : dactyle, fétuque, rubans du chaume, rosettes à
// ruban) avec la même primitive que l'écorce (RubanTexture.PoserBandePeriodique). La géométrie
// du brin reste celle de la vue : le vent le plie toujours, point par point.
//
// Même contrat que recettes/ecorce.js (cuit par cuire_ecorces.js --jeu limbes) : un cylindre
// photographié de face, ton de base (2) rendu transparent par la vue → seules les MARQUES se
// posent sur le brin déjà teint (espèce, saison, santé, orientation : la palette du brin) :
//   • nervures PARALLÈLES : traits fins sur toute la longueur, en pigment d'ombre (couche 1 →
//     ton 1 ; des sillons creusés ne donnaient presque aucune occlusion à cette finesse,
//     43 texels d'ombre sur 1 000 à ×32 : constaté à la cuisson) ;
//   • cœur plus clair : la nervure médiane en pigment clair (couche 2 → ton 3) ;
//   • bord : un trait d'ombre un peu plus large le long de chaque bord.
// Deux largeurs de référence : « large » (1,5 cm : dactyle, blé, rubans du poireau) et
// « etroit » (0,6 cm : seigle, pâturin). La bande s'étire sur la largeur réelle du brin : vers la
// pointe, les nervures convergent, comme sur une vraie feuille de graminée.
//
// 📖 Pédagogie : un trait droit est périodique de lui-même — n'importe quelle période convient.
// On en prend une courte (4 cm) : la bande est minuscule et la couture nulle par construction.
//
// Déterministe : aucun aléa (positions régulières).
'use strict';

const CM = 0.1;                                   // 1 unité ink = 10 cm
const PERIODE_CM = 4;
// Pas du sculpteur à ×32, en px : bien plus fin que l'écorce (2,5) — une nervure fait ~1 px.
const PAS_PX32 = 0.8;

// nervures : de chaque côté de la médiane, régulièrement réparties sur ±0,75 du rayon.
const LIMBES = {
  large: { dCm: 1.5, nervures: 2 },
  etroit: { dCm: 0.6, nervures: 1 },
};
// Âge unique (le chargeur de la vue range par essence × âge) : « limbe ».
const AGES = [{ nom: 'limbe', dCm: 1.5, periodeCm: PERIODE_CM }];
// Ton fixe par couche de pigment (cuire_ecorces.js) : 1 = ombre (nervures, bords), 2 = clair.
const TONS_COUCHE = [null, 1, 3];

const surface = (R, a, y, dr = 0) => [(R + dr) * Math.sin(a), y, (R + dr) * Math.cos(a)];

// Un trait de pigment droit à l'abscisse x (part du rayon), de −P à 2P : la fenêtre [0, P) et
// ses débords. Centré un peu sous la surface : il affleure sans faire de relief.
function trait(c, x, rayon, mat) {
  const a = Math.asin(Math.max(-0.99, Math.min(0.99, x)));
  const pts = [-1, 0, 1, 2].map(k => surface(c.R, a, k * c.P, -rayon * 0.5));
  c.S.tube(pts, rayon, rayon, mat, { res: c.res });
}

function bande(nom) {
  const L = LIMBES[nom], R = (L.dCm / 2) * CM, P = PERIODE_CM * CM;
  return {
    nom: `limbe_${nom}`, essence: nom, age: 'limbe', dCm: L.dCm, periodeCm: PERIODE_CM,
    rayonCm: L.dCm / 2, pasPx32: PAS_PX32,
    sculpter(ctx) {
      const c = { S: ctx.S, R, P, res: ctx.res };
      const mat = k => ctx.M.couches[k];
      // Le limbe : trois tronçons de longueur P (mêmes rangées de splats, cf. ecorce.js).
      ctx.S.tube([-1, 0, 1, 2].map(k => [0, k * P, 0]), R, R, mat(0), { res: ctx.res });
      const e = Math.max(R * 0.07, ctx.res);
      for (let i = 1; i <= L.nervures; i++) {
        const x = (0.75 * i) / (L.nervures + 0.5);
        for (const s of [-1, 1]) trait(c, s * x, e, mat(1));
      }
      for (const s of [-1, 1]) trait(c, s * 0.93, e * 1.3, mat(1));   // bords
      trait(c, 0, Math.max(R * 0.1, ctx.res), mat(2));                // cœur clair
    }
  };
}

module.exports = { AGES, LIMBES, TONS_COUCHE, bande };

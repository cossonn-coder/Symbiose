// SYMBIOSE — tools/splat/lib/iso.js (sprint PRÉCUISSON SPLATS ①)
// La CAMÉRA de cuisson : photographier une pièce comme la vue Godot la montre.
//
// Échelle LUE dans world/WorldView.Projection.cs (vérifiée le 2026-11-20) :
//   PxPerCmX = 0,39 px INTERNES par cm (losange 39×19,5 px internes pour un plot
//   de 50 cm ; les « 78×39 » de CLAUDE.md sont la taille d'avant le SubViewport
//   ×2 — même taille à l'écran, mais l'unité des pièces est le px interne).
//   À un palier z, une pièce dessinée par la vue fait `taille_px` px internes
//   (PlantRenderer.Assemblee.DrawPieceIndexee : rectangle Size / z en unités de
//   canevas, canevas ×z) → 1 cm d'organe = 0,39 × z px.
//
// Projection de la vue : écran = ((x − y)·0,39 ; (x + y)·0,195 − z·0,39) [moteur
// x est, y sud, z haut]. C'est une projection OBLIQUE (les verticales gardent
// l'échelle du sol). Une caméra orthographique ne peut reproduire que le sol :
// tangage 30° (losange 2:1) et lacet 45° → sol EXACT, verticales ×1,22 trop
// hautes (0,39 / (0,5515 × cos 30°) = 0,816). Écart accepté et signalé au ① :
// sur une feuille (organe surtout couché) il vaut < 1 px jusqu'à ×4.
//
// 📖 Pédagogie : en orthographique tous les rayons sont parallèles, donc la
// taille d'un objet à l'écran ne dépend pas de sa distance — exactement comme la
// vue iso du jeu. On règle le « zoom » par la demi-hauteur visible (dist × tan).

'use strict';

const PX_PAR_CM_X = 0.39;                 // WorldView.PxPerCmX (px internes, ×1)
const CM_PAR_UNITE = 10;                  // 1 unité ink = 10 cm (cf. recettes)
const LACET_ISO = Math.PI / 4;            // œil au sud-est (écran bas = x + y)
const TANGAGE_ISO = Math.PI / 6;          // sol en losange 2:1
const FOV = (38 * Math.PI) / 180;         // constante de vendor/ink/cli/render.js
const PALIERS = [0.5, 1, 2, 4, 8, 16, 32];

// px internes par unité ink au palier z : le vecteur sol (1 cm vers l'est) fait
// 0,39 px en X écran ; en ortho lacet 45°, il en fait ppu × cos 45° / 10.
const pxParUnite = z => (PX_PAR_CM_X * z * CM_PAR_UNITE) / Math.cos(Math.PI / 4);

// Base écran (droite, haut) en repère ink pour un lacet caméra — même calcul que
// viewMatrix() de vendor/ink/cli/render.js (œil = cible + dist·(cp·sin, sp, cp·cos)).
function baseEcran(lacetCam) {
  const cp = Math.cos(TANGAGE_ISO), sp = Math.sin(TANGAGE_ISO);
  const z = [cp * Math.sin(lacetCam), sp, cp * Math.cos(lacetCam)];
  const x = [Math.cos(lacetCam), 0, -Math.sin(lacetCam)];
  const y = [z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0]];
  return { droite: x, haut: y };
}

// Photographie une pièce (monde ink déjà cuit) au palier z, l'ORGANE tourné de
// `lacet` (radians, sens trigo vu du dessus : 0 = vers l'est, π/2 = vers le nord).
// Tourner l'organe de +a = tourner la caméra de −a autour de l'axe vertical.
// Toile carrée impaire : l'attache (origine) tombe au centre du pixel `demi`.
// SURÉCHANTILLONNAGE `ss` : la photo est prise à ss × la résolution de la pièce
// (même cadrage), codes.piece en fait la moyenne par bloc ss × ss.
const surEchantillon = z => Math.max(1, Math.min(4, Math.round(8 / z)));

function photographier(ink, monde, rayonCm, z, lacet) {
  const ppu = pxParUnite(z), ss = surEchantillon(z);
  const demi = Math.ceil((rayonCm / CM_PAR_UNITE) * ppu) + 2;
  const cote = 2 * demi + 1, grand = cote * ss;
  const lacetCam = LACET_ISO - lacet;
  const f = ink.render(monde, {
    w: grand, h: grand, px: 1, ortho: true, transparent: true,
    yaw: lacetCam, pitch: TANGAGE_ISO, target: [0, 0, 0],
    dist: grand / 2 / (ppu * ss * Math.tan(FOV / 2)),
    passes: ['coverage', 'normal', 'splatId']
  });
  if (f.passes.w !== grand || f.passes.h !== grand) throw new Error('toile inattendue ' + f.passes.w + '×' + f.passes.h);
  return { passes: f.passes, cote, demi, ss, lacet, base: baseEcran(lacetCam) };
}

module.exports = { PALIERS, CM_PAR_UNITE, PX_PAR_CM_X, pxParUnite, surEchantillon, baseEcran, photographier };

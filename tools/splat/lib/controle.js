// SYMBIOSE — tools/splat/lib/controle.js (sprint PRÉCUISSON SPLATS ①)
// PLANCHE DE CONTRÔLE pour un humain : chaque pièce recolorée par une rampe de 5
// tons et éclairée par un soleil FIXE, en appliquant la règle exacte du shader de
// la vue (palette_indexee.gdshader, via codes.tonEclaire). C'est « ce que la vue
// affichera », sans lancer Godot.
//
// Mise en page : une ligne par (palier, inclinaison) pour la variante 0, une
// colonne par lacet ; chaque pièce agrandie d'un facteur ENTIER (×16 à ×0,5,
// … ×1 à partir de ×8) pour être lisible à l'œil — c'est un AGRANDISSEMENT DE
// CONTRÔLE, jamais une pièce de jeu (les pièces de la planche, elles, ne sont
// jamais mises à l'échelle). À droite, `extra` (facultatif) : la pièce actuelle
// de la vue au même palier, quand on a pu la capturer.
//
// 📖 Pédagogie : la rampe 5 tons imite RampesDa (ombre vers le bleu-vert, éclat
// vers le jaune) ; elle n'est qu'un témoin — en jeu, la rampe vient de l'espèce,
// de la saison et de la santé (une géométrie, toutes les teintes).

'use strict';

const { tonEclaire } = require('./codes');

const RAMPE = [[0x1e, 0x3a, 0x2c], [0x2f, 0x5e, 0x34], [0x4f, 0x8a, 0x3a], [0x86, 0xb8, 0x4a], [0xd8, 0xe6, 0x7a]];
const FOND = [0x24, 0x20, 0x2a];
const SOLEIL = [-0.6, -0.8];   // direction écran vers le soleil : haut-gauche (unitaire)
const MARGE = 6;

const agrandi = z => Math.max(1, Math.round(8 / z));

function poser(img, W, piece, ox, oy, k) {
  for (let y = 0; y < piece.h; y++)
    for (let x = 0; x < piece.w; x++) {
      const q = (y * piece.w + x) * 4;
      if (!piece.rgba[q + 3]) continue;
      const c = piece.rgba[q + 1];
      const col = RAMPE[tonEclaire((c >> 4) & 7, c & 15, SOLEIL)];
      for (let j = 0; j < k; j++)
        for (let i = 0; i < k; i++) {
          const p = ((oy + y * k + j) * W + ox + x * k + i) * 3;
          img[p] = col[0]; img[p + 1] = col[1]; img[p + 2] = col[2];
        }
    }
}

// lignes : [[pièce, …], …] (déjà dans l'ordre d'affichage) ; zooms[l] = palier de
// la ligne l ; `annexe` (facultatif, { w, h, rgb }) = image collée sous la planche
// telle quelle (la capture de la pièce actuelle de la vue). Retourne { w, h, rgb }.
function composer(lignes, zooms, annexe) {
  const tailles = lignes.map((l, i) => {
    const k = agrandi(zooms[i]);
    return { k, w: l.reduce((s, p) => s + p.w * k + MARGE, MARGE), h: Math.max(...l.map(p => p.h * k)) + MARGE };
  });
  const hLignes = tailles.reduce((s, t) => s + t.h, MARGE);
  const W = Math.max(...tailles.map(t => t.w), annexe ? annexe.w + 2 * MARGE : 0);
  const H = hLignes + (annexe ? annexe.h + MARGE : 0);
  const img = new Uint8Array(W * H * 3);
  for (let i = 0; i < W * H; i++) img.set(FOND, i * 3);
  let y = MARGE;
  lignes.forEach((l, i) => {
    let x = MARGE;
    for (const p of l) { poser(img, W, p, x, y, tailles[i].k); x += p.w * tailles[i].k + MARGE; }
    y += tailles[i].h;
  });
  if (annexe)
    for (let j = 0; j < annexe.h; j++)
      img.set(annexe.rgb.subarray(j * annexe.w * 3, (j + 1) * annexe.w * 3), ((hLignes + j) * W + MARGE) * 3);
  return { w: W, h: H, rgb: img };
}

module.exports = { composer, agrandi, SOLEIL };

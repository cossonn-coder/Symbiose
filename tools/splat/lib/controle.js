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
// ③ : une rampe témoin par COUCHE (0 la rampe verte ci-dessus, 1 or-brun, 2 rose).
const RAMPES = [RAMPE,
  [[0x4a, 0x2a, 0x12], [0x7a, 0x4a, 0x1a], [0xb8, 0x80, 0x22], [0xe8, 0xc0, 0x40], [0xff, 0xf0, 0x9a]],
  [[0x4a, 0x1e, 0x3a], [0x80, 0x34, 0x5a], [0xc0, 0x5a, 0x80], [0xe8, 0x94, 0xb0], [0xff, 0xd8, 0xe8]]];
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
      const col = RAMPES[piece.ics ? piece.ics[q >> 2] : 0][tonEclaire((c >> 4) & 7, c & 15, SOLEIL)];
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

// ③ COUCHES : les pièces d'une même vue (une par couche) superposées en une
// pièce de contrôle, alignées sur leur attache ; `ics` = couche de chaque pixel.
// Les pièces sans couche passent telles quelles.
function fusionner(pieces) {
  const sortie = [], groupes = new Map();
  for (const p of pieces) {
    if (p.couche === undefined) { sortie.push(p); continue; }
    const cle = [p.palier, p.taille, p.inclinaison, p.variante, p.lacet].join('|');
    if (!groupes.has(cle)) { groupes.set(cle, []); sortie.push(cle); }
    groupes.get(cle).push(p);
  }
  return sortie.map(e => (typeof e === 'string' ? fusion(groupes.get(e)) : e));
}

function fusion(liste) {
  const pleines = liste.filter(p => p.w > 0);
  if (!pleines.length) return { ...liste[0], w: 0, h: 0 };
  const g = Math.min(...pleines.map(p => -p.attache[0])), t = Math.min(...pleines.map(p => -p.attache[1]));
  const w = Math.max(...pleines.map(p => p.w - p.attache[0])) - g;
  const h = Math.max(...pleines.map(p => p.h - p.attache[1])) - t;
  const rgba = new Uint8Array(w * h * 4), ics = new Uint8Array(w * h);
  for (const p of pleines) {
    const ox = -p.attache[0] - g, oy = -p.attache[1] - t;
    for (let y = 0; y < p.h; y++)
      for (let x = 0; x < p.w; x++) {
        const s = (y * p.w + x) * 4;
        if (!p.rgba[s + 3]) continue;
        const d = (y + oy) * w + x + ox;
        rgba.set(p.rgba.subarray(s, s + 4), d * 4);
        ics[d] = p.ic;
      }
  }
  return { ...liste[0], couche: undefined, w, h, rgba, ics, attache: [-g, -t] };
}

module.exports = { composer, agrandi, fusionner, SOLEIL };

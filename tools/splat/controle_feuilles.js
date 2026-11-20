#!/usr/bin/env node
// SYMBIOSE — tools/splat/controle_feuilles.js (sprint PRÉCUISSON SPLATS ②)
// PLANCHE DE CONTRÔLE DE LA BIBLIOTHÈQUE : relit les planches DÉJÀ CUITES de
// assets/splats (aucune recuisson) et compose une seule image pour un humain :
//   • une ligne par feuille : ×1 (lacet 0) | ×8, les 8 lacets (inclinaison 0,
//     variante 0) | ×16, la pièce saine puis ses degrés de trous ;
//   • en bas, les touffes du kit : 4 tailles × 3 variantes par forme.
// Même rendu que lib/controle.js (rampe 5 tons + soleil fixe haut-gauche).
//
// Usage : node tools/splat/controle_feuilles.js <sortie.png>
//
// 📖 Pédagogie : relire les fichiers produits plutôt que les recuire, c'est
// contrôler ce qui sera VERSIONNÉ — l'octet que la vue lira, pas une copie.

'use strict';

const fs = require('fs');
const path = require('path');
const png = require('./vendor/ink/cli/png.js');
const controle = require('./lib/controle');

const DOSSIER = path.resolve(__dirname, '..', '..', 'assets', 'splats');

// Une pièce du manifeste → { w, h, rgba } lue dans sa planche (cache par fichier).
const cache = new Map();
function piece(m, e) {
  const f = path.join(DOSSIER, m.planches[e.planche]);
  if (!cache.has(f)) {
    const r = png.raster(f);
    const rgba = new Uint8Array(r.w * r.h * 4);
    for (let i = 0; i < rgba.length; i++) rgba[i] = Math.round((r.data[i] * 255) / r.max);
    cache.set(f, { w: r.w, rgba });
  }
  const pl = cache.get(f), [x, y, w, h] = e.rect, rgba = new Uint8Array(w * h * 4);
  for (let j = 0; j < h; j++) rgba.set(pl.rgba.subarray(((y + j) * pl.w + x) * 4, ((y + j) * pl.w + x + w) * 4), j * w * 4);
  return { w, h, rgba };
}

function principal() {
  const sortie = process.argv[2];
  if (!sortie) throw new Error('usage : node tools/splat/controle_feuilles.js <sortie.png>');
  const manifestes = fs.readdirSync(DOSSIER).filter(f => f.endsWith('.json')).sort()
    .map(f => JSON.parse(fs.readFileSync(path.join(DOSSIER, f), 'utf8')));
  const lignes = [], zooms = [];
  const saine = e => !e.trou && e.inclinaison_deg === 0 && e.variante === 0;
  for (const m of manifestes.filter(m => m.recette.startsWith('feuille_'))) {
    const pick = f => m.pieces.filter(f).filter(e => e.rect[2] > 0).map(e => piece(m, e));
    lignes.push(pick(e => saine(e) && e.palier === 1 && e.lacet_deg === 0)
      .concat(pick(e => saine(e) && e.palier === 8)));
    zooms.push(8);
    lignes.push(pick(e => e.palier === 16 && e.lacet_deg === 0 && e.inclinaison_deg === 0 && e.variante === 0));
    zooms.push(16);
  }
  for (const m of manifestes.filter(m => m.recette.startsWith('touffe_'))) {
    lignes.push(m.pieces.filter(e => e.rect[2] > 0).map(e => piece(m, e)));
    zooms.push(1);
  }
  const garde = lignes.map((l, i) => (l.length ? i : -1)).filter(i => i >= 0);
  const img = controle.composer(garde.map(i => lignes[i]), garde.map(i => zooms[i]));
  png.write(sortie, img.w, img.h, img.rgb);
  console.log(`${sortie} : ${img.w}×${img.h}, ${manifestes.length} recettes`);
}

principal();

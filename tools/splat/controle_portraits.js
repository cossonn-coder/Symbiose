#!/usr/bin/env node
// SYMBIOSE — tools/splat/controle_portraits.js (sprint PRÉCUISSON SPLATS ⑥)
// PLANCHE DE CONTRÔLE des portraits, relue sur disque (ne recuit rien) : une ligne
// par espèce (jeune · mûre · fin), sur fond gris uni, en planches de `PAR_PLANCHE`
// espèces (lisibles d'un coup d'œil). L'ordre des espèces est celui du manifeste
// (alphabétique des classes Python), rappelé à la console.
//
// Usage : node tools/splat/controle_portraits.js DOSSIER_SORTIE [assets/portraits]
//
// 📖 Pédagogie : un portrait a un fond TRANSPARENT ; la planche le compose sur un
// gris (« alpha blending » : couleur = α·portrait + (1 − α)·fond) pour juger la
// silhouette comme l'encyclopédie la montrera sur son propre fond.

'use strict';

const path = require('path');
const fs = require('fs');
const png = require('./vendor/ink/cli/png.js');

const RACINE = path.resolve(__dirname, '..', '..');
const PAR_PLANCHE = 9, MARGE = 6, FOND = [96, 100, 92], SEP = [60, 62, 58];

function principal() {
  const sortie = path.resolve(RACINE, process.argv[2] || '.');
  const dossier = path.resolve(RACINE, process.argv[3] || 'assets/portraits');
  const man = JSON.parse(fs.readFileSync(path.join(dossier, 'portraits.json'), 'utf8'));
  const T = man.taille_px, especes = Object.keys(man.especes);
  fs.mkdirSync(sortie, { recursive: true });
  for (let p = 0; p * PAR_PLANCHE < especes.length; p++) {
    const lot = especes.slice(p * PAR_PLANCHE, (p + 1) * PAR_PLANCHE);
    const w = 3 * (T + MARGE) + MARGE, h = lot.length * (T + MARGE) + MARGE;
    const rgb = new Uint8Array(w * h * 3);
    for (let i = 0; i < w * h; i++) rgb.set(SEP, i * 3);
    lot.forEach((esp, r) => man.ordre.forEach((etat, c) => {
      const img = png.raster(path.join(dossier, man.especes[esp][etat].fichier));   // RGBA (read() perd l'alpha)
      const x0 = MARGE + c * (T + MARGE), y0 = MARGE + r * (T + MARGE);
      for (let y = 0; y < T; y++)
        for (let x = 0; x < T; x++) {
          const s = (y * img.w + x) * 4, a = img.data[s + 3] / img.max, d = ((y0 + y) * w + x0 + x) * 3;
          for (let k = 0; k < 3; k++) rgb[d + k] = Math.round(a * img.data[s + k] * 255 / img.max + (1 - a) * FOND[k]);
        }
    }));
    const f = path.join(sortie, `controle_portraits_${p + 1}.png`);
    png.write(f, w, h, rgb);
    console.log(`${path.relative(RACINE, f)} : ${lot.join(', ')}`);
  }
}

principal();

#!/usr/bin/env node
// SYMBIOSE — tools/splat/controle_organes.js (sprint PRÉCUISSON SPLATS ③)
// PLANCHE DE CONTRÔLE DES ORGANES (têtes, fleurs, fruits, boutons, fleurons) : relit les
// planches DÉJÀ CUITES de assets/splats (aucune recuisson), comme controle_feuilles.js :
//   • une ligne par recette : ×1 | ×8, les 8 lacets (inclinaison 0, variante 0) ;
//   • une ligne ×32 : lacet 0, les 3 inclinaisons ;
//   • fleurons du kit : les 3 tailles × 3 variantes.
// Couches d'une même vue superposées (lib/controle.js `fusionner`), une rampe témoin
// par couche (vert = couche 0, or-brun = 1, rose = 2).
//
// Usage : node tools/splat/controle_organes.js <sortie.png>

'use strict';

const fs = require('fs');
const path = require('path');
const png = require('./vendor/ink/cli/png.js');
const controle = require('./lib/controle');
const { piece, DOSSIER } = require('./controle_feuilles');

const ORGANES = /^(tete_|fruit_|gousse|chaton|epi_|panicule|bouton|fleuron)/;

// Le lecteur PNG d'ink-studio refuse plus de 16,7 Mpx : une telle planche (tournesol ×32)
// est sautée ici — sa planche de contrôle propre (cuire.js --controle) la montre.
const refus = new Set();
function lisible(m, e) {
  const f = m.planches[e.planche];
  if (refus.has(f)) return false;
  try { piece(m, e); return true; } catch (err) { refus.add(f); console.log(`  ${f} sautée : ${err.message}`); return false; }
}

function principal() {
  const sortie = process.argv[2];
  if (!sortie) throw new Error('usage : node tools/splat/controle_organes.js <sortie.png>');
  const manifestes = fs.readdirSync(DOSSIER).filter(f => f.endsWith('.json') && ORGANES.test(f)).sort()
    .map(f => JSON.parse(fs.readFileSync(path.join(DOSSIER, f), 'utf8')));
  const lignes = [], zooms = [];
  for (const m of manifestes) {
    const prendre = f => controle.fusionner(m.pieces.filter(f).filter(e => e.rect[2] > 0 && lisible(m, e)).map(e => ({ ...piece(m, e), palier: e.palier,
      taille: e.taille_px, inclinaison: e.inclinaison_deg, variante: e.variante, lacet: e.lacet_deg,
      ...(e.couche ? { couche: e.couche, ic: m.couches.indexOf(e.couche) } : {}), attache: e.attache }))).filter(p => p.w > 0);
    if (m.recette === 'fleuron') { lignes.push(prendre(() => true)); zooms.push(1); continue; }
    const i0 = m.inclinaisons_deg.includes(0) ? 0 : m.inclinaisons_deg[0];
    lignes.push(prendre(e => e.variante === 0 && e.inclinaison_deg === i0 && ((e.palier === 1 && e.lacet_deg === 0) || e.palier === 8)));
    zooms.push(8);
    lignes.push(prendre(e => e.variante === 0 && e.palier === 32 && e.lacet_deg === 0));
    zooms.push(32);
  }
  const garde = lignes.map((l, i) => (l.length ? i : -1)).filter(i => i >= 0);
  const img = controle.composer(garde.map(i => lignes[i]), garde.map(i => zooms[i]));
  png.write(sortie, img.w, img.h, img.rgb);
  console.log(`${sortie} : ${img.w}×${img.h}, ${manifestes.length} recettes`);
}

principal();

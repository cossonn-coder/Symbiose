#!/usr/bin/env node
// SYMBIOSE — tools/splat/couture_bois.js (sprint PRÉCUISSON SPLATS ③)
// MESURE DE LA COUTURE du bois en tronçons : 5 tronçons d'écorce (recettes/bois.js)
// posés bout à bout le long de VRAIS segments du « Pommier · an 10 »
// (data/code/tools/export_structure.py), à la projection oblique de la vue. Trois
// assemblages par segment et par palier, côte à côte sur la planche :
//   A. tronçons cuits à la direction EXACTE du segment → seuls les JOINTS sont jugés ;
//   B. tronçons à la vue la plus proche du catalogue (8 lacets × 0/30/60/90°) →
//      ce que l'assemblage du ④ ferait vraiment (joints + quantification de la vue) ;
//   C. référence : UN cylindre de toute la longueur, direction exacte.
// Chiffre aussi le décalage aux joints de B (px) : la fin d'un tronçon quantifié
// contre le début du suivant, posé sur l'axe vrai.
//
// Usage : node tools/splat/couture_bois.js <sortie.png>   (lance le moteur Python
// en lecture seule pour exporter le spécimen — golden non concerné)
//
// 📖 Pédagogie : une couture se juge sur l'assemblage, jamais sur la pièce seule —
// comme un carrelage : chaque carreau est beau, c'est le joint qui trahit la pose.

'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const ink = require('./vendor/ink');
const png = require('./vendor/ink/cli/png.js');
const iso = require('./lib/iso');
const codes = require('./lib/codes');
const controle = require('./lib/controle');
const { cuireMonde, tableTons } = require('./cuire');
const bois = require('./recettes/bois');

const RACINE = path.resolve(__dirname, '..', '..');
const N = 5, LONG = 8;                               // 5 tronçons de 8 cm = un segment de 40 cm
const LACETS = 8, INCLIS = [0, 30, 60, 90], DIAMS = [1, 2, 4, 8, 16];
const PX = 0.39, PY = 0.195;                         // WorldView.PxPerCmX / PxPerCmY

function specimen() {
  const f = path.join(os.tmpdir(), `symbiose_structure_${process.pid}.json`);
  execFileSync('python3', ['-m', 'tools.export_structure', 'structure', f], { cwd: path.join(RACINE, 'data', 'code'), stdio: 'ignore' });
  const d = JSON.parse(fs.readFileSync(f, 'utf8'));
  fs.unlinkSync(f);
  return (d.specimens || d).find(s => s.title.startsWith('Pommier · an 10'));
}

// Projection oblique de la vue (moteur x est, y sud, z haut) au palier z, en px internes.
const ecran = (p, z) => [(p[0] - p[1]) * PX * z, ((p[0] + p[1]) * PY - p[2] * PX) * z];
const proche = (v, liste) => liste.reduce((a, b) => (Math.abs(b - v) < Math.abs(a - v) ? b : a));

// Direction moteur → (lacet°, inclinaison°, sens) ; un segment qui descend se pose à l'envers.
function vue(dir) {
  const e = (Math.asin(Math.max(-1, Math.min(1, dir[2]))) * 180) / Math.PI;
  const sens = e < 0 ? -1 : 1, d = dir.map(c => c * sens);
  return { lacet: (Math.atan2(-d[1], d[0]) * 180) / Math.PI, incl: Math.abs(e), sens };
}

function photo(L, tons, recette, lacetDeg, inclDeg, z, variante) {
  const monde = cuireMonde(L, recette, variante, inclDeg);
  return codes.piece(iso.photographier(ink, monde, recette.rayonCm, z, (lacetDeg * Math.PI) / 180), monde, tons);
}

// Pose des pièces (avec leur point 2D d'attache) sur une toile ; ordre = profondeur.
function assembler(poses) {
  const g = Math.min(...poses.map(q => q.at[0] - q.p.attache[0])), t = Math.min(...poses.map(q => q.at[1] - q.p.attache[1]));
  const w = Math.ceil(Math.max(...poses.map(q => q.at[0] - q.p.attache[0] + q.p.w)) - g);
  const h = Math.ceil(Math.max(...poses.map(q => q.at[1] - q.p.attache[1] + q.p.h)) - t);
  const rgba = new Uint8Array(w * h * 4);
  for (const { p, at } of poses) {
    const ox = Math.round(at[0] - p.attache[0] - g), oy = Math.round(at[1] - p.attache[1] - t);
    for (let y = 0; y < p.h; y++)
      for (let x = 0; x < p.w; x++) {
        const s = (y * p.w + x) * 4;
        if (p.rgba[s + 3]) rgba.set(p.rgba.subarray(s, s + 4), ((y + oy) * w + x + ox) * 4);
      }
  }
  return { w, h, rgba };
}

function principal() {
  const sortie = process.argv[2];
  if (!sortie) throw new Error('usage : node tools/splat/couture_bois.js <sortie.png>');
  const sp = specimen(), segs = sp.segments;
  const choix = [segs[0], segs.find(s => Math.abs(s.dir[2]) < 0.6 && s.thickness_cm > 4),
    segs.find(s => Math.abs(s.dir[2]) < 0.8 && s.thickness_cm > 1 && s.thickness_cm < 2)];
  const L = ink.load(), tons = tableTons(), lignes = [], zooms = [];
  for (const s of choix) {
    const d = proche(s.thickness_cm, DIAMS), rec = bois(d, LONG), ref = bois(d, LONG * N);
    const v = vue(s.dir), q = { lacet: Math.round(v.lacet / (360 / LACETS)) * (360 / LACETS), incl: proche(v.incl, INCLIS) };
    const base = v.sens > 0 ? s.base : s.base.map((c, k) => c + s.dir[k] * s.length_cm);
    const dir = s.dir.map(c => c * v.sens), pas = s.length_cm / N;
    for (const z of [8, 16]) {
      const pts = Array.from({ length: N }, (_, k) => base.map((c, i) => c + dir[i] * pas * k));
      const ordre = pts.map((p, k) => [p[0] + p[1] + p[2], k]).sort((a, b) => a[0] - b[0]).map(e => e[1]);
      const asm = (lac, inc) => assembler(ordre.map(k => ({ p: photo(L, tons, rec, lac, inc, z, k % 3), at: ecran(pts[k], z) })));
      const A = asm(v.lacet, v.incl), B = asm(q.lacet, q.incl);
      const C = assembler([{ p: photo(L, tons, ref, v.lacet, v.incl, z, 0), at: ecran(base, z) }]);
      lignes.push([A, B, C]); zooms.push(z);
      // Décalage aux joints de B : vrai pas contre pas quantifié, projetés (px).
      const lq = (q.lacet * Math.PI) / 180, iq = (q.incl * Math.PI) / 180;
      const dq = [Math.cos(iq) * Math.cos(lq), -Math.cos(iq) * Math.sin(lq), Math.sin(iq)];
      const e0 = ecran(dir.map(c => c * pas), z), e1 = ecran(dq.map(c => c * pas), z);
      console.log(`segment ép. ${s.thickness_cm} cm (tronçon d${d}), dir [${s.dir}] → vue exacte ${v.lacet.toFixed(1)}°/${v.incl.toFixed(1)}°, ` +
        `catalogue ${q.lacet}°/${q.incl}° — ×${z} : décalage aux joints de B ${Math.hypot(e0[0] - e1[0], e0[1] - e1[1]).toFixed(1)} px`);
    }
  }
  const img = controle.composer(lignes, zooms);
  png.write(path.resolve(sortie), img.w, img.h, img.rgb);
  console.log(`${sortie} : ${img.w}×${img.h} (lignes : A exact | B catalogue | C référence d'un tenant)`);
}

principal();

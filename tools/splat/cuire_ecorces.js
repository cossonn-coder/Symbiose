#!/usr/bin/env node
// SYMBIOSE — tools/splat/cuire_ecorces.js (sprint BOIS & ARBRES ②)
// CUISSON DES ÉCORCES : pour chaque essence × âge (recettes/ecorce.js), un cylindre sculpté
// périodique, photographié DE FACE (caméra orthographique horizontale, axe vertical) à chaque
// palier où la vue dessine le tube (×4 → ×32) → une BANDE de tons, rangée dans une planche
// par palier : `assets/splats/ecorces_x<z>.png` + `assets/splats/ecorces.json`.
//
// Format d'un texel (celui des planches splat, lu par visuals/Ecorces.cs) : R = niveau du kit,
// G = code `128 | ton << 4 | 8` (orientation « plate » : l'orientation du flanc vient de la
// géométrie du tube, décision C3), A = 255 sur le fût. Tons : 0 creux · 1 ombre · 2 base
// (relief, par l'occlusion), 0 forcé pour le pigment sombre, 3 pour le pigment clair.
//
// Échelle : 1 texel = 1 px interne au palier (≈ 0,39 × z px/cm, ajusté pour que la période
// fasse un nombre PAIR de rangées) ; en travers, le diamètre de référence × 1,5 (le bois
// dessiné est 1,5 × plus large que sa projection, WoodWidthFactor).
//
// COUTURE MESURÉE : la photo déborde la période d'un quart en haut et en bas ; les rangées de
// débord doivent être, à l'octet, celles de l'autre bout de la bande (périodicité). Le nombre
// de texels différents est écrit à la console et dans le manifeste (`couture_texels`).
//
// Usage : node tools/splat/cuire_ecorces.js [--controle DOSSIER] [--cache DOSSIER]
//   --liste : les noms de bandes ; --seulement Essence_age --cache D : une bande, mise en cache
//   (parallèle : `node tools/splat/cuire_ecorces.js --liste | xargs -P 6 -I{} node
//   tools/splat/cuire_ecorces.js --seulement {} --cache D`, puis sans --seulement : assemblage).
// Déterministe : aucune horloge dans les fichiers ; deux cuissons = mêmes octets.
//
// 📖 Pédagogie : une caméra orthographique de face « déroule » le cylindre en une bande — le
// centre est vu de plein fouet, les bords en raccourci, exactement comme le tube dessiné.

'use strict';

const fs = require('fs');
const path = require('path');
const ink = require('./vendor/ink');
const png = require('./vendor/ink/cli/png.js');
const codes = require('./lib/codes');
const planche = require('./lib/planche');
const { PALETTE, rampeCouche, GRAINE, AMBIANT, CIEL } = require('./cuire');
const { AGES, ESSENCES, bande } = require('./recettes/ecorce');

const RACINE = path.resolve(__dirname, '..', '..');
const PALIERS = [4, 8, 16, 32];                 // la vue pose le tube à partir de ×4 (① : bas paliers non migrés)
const PX_CM = 0.39;                             // WorldView.PxPerCmX (px internes, ×1)
const CM = 0.1, FOV = (38 * Math.PI) / 180;     // 1 unité ink = 10 cm ; FOV de vendor/ink/cli/render.js
const PAS_PX32 = 2.5;                           // pas du sculpteur ≈ 2,5 px à ×32 (1,5 : 920 k splats, 54 s le tronc)
// Relief : 10 crans d'éclairement (occlusion) → ton. Plus sensible que les feuilles : une
// crevasse d'écorce est peu profonde à côté du fût.
const TON_RELIEF = [0, 0, 0, 1, 1, 1, 1, 2, 2, 2];
const TON_COUCHE = [null, 0, 3];                // pigment sombre / clair : ton fixe

const options = argv => {
  const o = { controle: null, seulement: null, cache: null, liste: false };
  for (let i = 0; i < argv.length; i += 2) {
    if (argv[i] === '--liste') { o.liste = true; i--; continue; }
    o[argv[i].replace(/^--/, '')] = argv[i + 1];
  }
  return o;
};

// Table couleur emballée → (couche << 3 | ton), comme cuire.js mais aux tons de l'écorce.
function tableTons() {
  const t = new Map();
  TON_COUCHE.forEach((fixe, c) => {
    const tonDe = fixe === null ? TON_RELIEF : TON_RELIEF.map(() => fixe);
    for (const [k, v] of codes.tableTons(PALETTE, rampeCouche(c), tonDe, c)) t.set(k, v);
  });
  return t;
}

// Pas du sculpteur : P / m, m PAIR (les rangées d'un tube sont décalées d'un demi-pas une
// sur deux) → la rangée en y et celle en y + P coïncident. Légèrement agrandi : ceil(P/pas)
// tombe sur m même avec l'arrondi flottant.
function pas(rec) {
  let m = Math.round(rec.periodeCm / (PAS_PX32 / (PX_CM * 32)));
  m += m % 2;
  return { res: ((rec.periodeCm * CM) / m) * (1 + 1e-9), m };
}

function monde(L, rec) {
  const B = L.makeBuilder(GRAINE, PALETTE);
  const S = L.KIT.sculpt(L.makeSculpt(B));
  S.sunK = 0; S.amb = AMBIANT; S.sky = CIEL;
  const { res } = pas(rec);
  rec.sculpter({ S, K: L.KIT, res, M: { couches: [0, 1, 2].map(c => ({ r: rampeCouche(c) })) } });
  S.bake();
  const r = (Math.max(rec.rayonCm, 2 * rec.periodeCm) * CM) + 1;
  return B.finish({ cam: { target: [0, 0, 0], dist: 5, pitch: 0, yaw: 0 }, detail: 20, dither: 0, radius: r });
}

// Photographie de face au palier z → { w, h, rgba, couture, tons } (bande de la période).
function photographier(L, mo, rec, tons, z) {
  let H = Math.round(rec.periodeCm * PX_CM * z); H += H % 2;
  const cpp = rec.periodeCm / H;                                 // cm par px
  let W = Math.round((2 * rec.rayonCm) / cpp); W += W % 2;
  const M = Math.max(2, Math.round(H / 4));
  let S = Math.max(H + 2 * M, W + 4); S += S % 2;
  const ss = Math.max(1, Math.round(8 / z)), G = S * ss, ppu = (1 / cpp) / CM;
  const f = ink.render(mo, {
    w: G, h: G, px: 1, ortho: true, transparent: true, yaw: 0, pitch: 0,
    target: [0, (rec.periodeCm / 2) * CM, 0], dist: G / 2 / (ppu * ss * Math.tan(FOV / 2)),
    passes: ['coverage', 'splatId']
  });
  if (f.passes.w !== G || f.passes.h !== G) throw new Error('toile inattendue');
  // Ton d'un pixel de la toile S × S (0 = vide, sinon code octetB).
  const code = (X, Y) => {
    let n = 0, sTon = 0;
    const parC = [0, 0, 0];
    const vals = [];
    for (let j = 0; j < ss; j++)
      for (let i = 0; i < ss; i++) {
        const id = f.passes.splatId[(Y * ss + j) * G + X * ss + i];
        if (!id) continue;
        const v = tons.get(mo.data[(id - 1) * 16 + 7]);
        if (v === undefined) throw new Error('couleur de splat hors rampe');
        n++; parC[v >> 3]++; vals.push(v);
      }
    if (2 * n < ss * ss) return 0;
    const c = parC[1] > parC[0] && parC[1] >= parC[2] ? 1 : parC[2] > parC[0] ? 2 : 0;
    for (const v of vals) if (v >> 3 === c) sTon += v & 7;
    return codes.octetB(Math.round(sTon / parC[c]), codes.ORIENT_PLAT);
  };
  const y0 = S / 2 - H / 2, x0 = S / 2 - W / 2;                 // rangée du haut (y = P⁻), colonne gauche
  const grille = (y, x) => code(x0 + x, y0 + y);
  const rgba = new Uint8Array(W * H * 4), hist = [0, 0, 0, 0, 0];
  let vides = 0;
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const c = grille(y, x), q = (y * W + x) * 4;
      if (!c) { vides++; continue; }
      const t = (c >> 4) & 7;
      hist[t]++;
      rgba[q] = t <= 1 ? 2 : t === 2 ? 3 : 4; rgba[q + 1] = c; rgba[q + 3] = 255;
    }
  // Couture : débord du haut (y > P) contre le bas de la bande, débord du bas contre le haut.
  let diff = 0, total = 0;
  for (let k = 1; k <= M; k++)
    for (let x = 0; x < W; x++) {
      diff += grille(-k, x) !== grille(H - k, x) ? 1 : 0;
      diff += grille(H - 1 + k, x) !== grille(k - 1, x) ? 1 : 0;
      total += 2;
    }
  return { w: W, h: H, rgba, couture: diff, coutureSur: total, hist, vides };
}

// Les photos d'une bande (4 paliers), depuis le cache si présent.
function cuireBande(L, tons, rec, cache) {
  const f = cache && path.join(cache, rec.nom + '.json');
  if (f && fs.existsSync(f)) {
    const c = JSON.parse(fs.readFileSync(f, 'utf8'));
    return c.map(p => ({ ...p, rgba: Uint8Array.from(Buffer.from(p.rgba, 'base64')) }));
  }
  let t = process.hrtime.bigint();
  const mo = monde(L, rec);
  const tSculpt = Number(process.hrtime.bigint() - t) / 1e6;
  const photos = [], ligne = [];
  for (const z of PALIERS) {
    t = process.hrtime.bigint();
    const p = photographier(L, mo, rec, tons, z);
    photos.push({ ...p, palier: z });
    ligne.push(`×${z} ${p.w}×${p.h} couture ${p.couture}/${p.coutureSur} tons ${p.hist.join('/')} (${(Number(process.hrtime.bigint() - t) / 1e6).toFixed(0)} ms)`);
  }
  console.log(`${rec.nom} : sculpture ${tSculpt.toFixed(0)} ms (${mo.count ?? '?'} splats) ; ${ligne.join(' ; ')}`);
  if (f) {
    fs.mkdirSync(cache, { recursive: true });
    fs.writeFileSync(f, JSON.stringify(photos.map(p => ({ ...p, rgba: Buffer.from(p.rgba).toString('base64') }))));
  }
  return photos;
}

function principal() {
  const o = options(process.argv.slice(2));
  const recs = Object.keys(ESSENCES).flatMap(e => AGES.map((_, a) => bande(e, a)));
  if (o.liste) { for (const r of recs) console.log(r.nom); return; }
  const L = ink.load(), tons = tableTons(), pieces = [], bandes = [];
  const t0 = process.hrtime.bigint();
  for (const rec of recs) {
    if (o.seulement && o.seulement !== rec.nom) continue;
    for (const p of cuireBande(L, tons, rec, o.cache)) {
      pieces.push({ ...p, attache: [0, 0], planche: planche.nomPalier(p.palier), inclinaison: 0, variante: 0, lacet: 0 });
      bandes.push({ essence: rec.essence, age: rec.age, palier: p.palier, d_cm: rec.dCm, periode_cm: rec.periodeCm, couture_texels: p.couture, couture_sur: p.coutureSur });
    }
  }
  // ranger() regroupe par planche (palier) : on trie d'abord, pour que l'entrée k du manifeste
  // soit bien la bande k (ordre stable : essence, âge au sein d'un palier).
  const ordre = pieces.map((_, k) => k).sort((a, b) => pieces[a].palier - pieces[b].palier || a - b);
  pieces.splice(0, pieces.length, ...ordre.map(k => pieces[k]));
  bandes.splice(0, bandes.length, ...ordre.map(k => bandes[k]));
  const { planches, entrees } = planche.ranger(pieces);
  const dossier = path.join(RACINE, 'assets', 'splats'), noms = {};
  if (!o.seulement) {
    for (const [z, pl] of planches) {
      const f = path.join(dossier, `ecorces_${z}.png`);
      fs.writeFileSync(f, png.encode(pl.w, pl.h, pl.rgba, 4));
      if (!fs.existsSync(f + '.import')) fs.writeFileSync(f + '.import', '[remap]\n\nimporter="keep"\n');
      noms[z] = path.basename(f);
      console.log(`  ${path.relative(RACINE, f)} ${pl.w}×${pl.h} ${fs.statSync(f).size} o`);
    }
    const manifeste = {
      recette: 'ecorces', format: 'R = niveau kit ; G = 128 | ton << 4 | 8 (plat) ; A = fût',
      ages: AGES.map(a => ({ nom: a.nom, d_cm: a.dCm, periode_cm: a.periodeCm })), planches: noms,
      bandes: bandes.map((b, k) => ({ ...b, planche: entrees[k].planche, rect: entrees[k].rect }))
    };
    fs.writeFileSync(path.join(dossier, 'ecorces.json'), JSON.stringify(manifeste, null, 1) + '\n');
  }
  if (o.controle) ecrireControle(path.resolve(RACINE, o.controle), pieces, bandes);
  console.log(`total ${(Number(process.hrtime.bigint() - t0) / 1e6).toFixed(0)} ms`);
}

// Planche de contrôle : une COLONNE par essence, les 3 âges empilés (tronc, branche, rameau)
// au ×16, chaque bande répétée 2 fois en hauteur → la couture se juge à l'œil au milieu. Tons
// sur une rampe brune témoin ; base = ton 2 (la vue la rend transparente sur le tube éclairé).
const RAMPE = [[0x2a, 0x1e, 0x16], [0x4e, 0x3a, 0x2a], [0x86, 0x6c, 0x52], [0xc8, 0xb0, 0x90], [0xf0, 0xe4, 0xc8]];
function ecrireControle(dossier, pieces, bandes) {
  const Z = 16, MARGE = 6, cols = new Map();
  pieces.forEach((p, i) => {
    if (p.palier !== Z) return;
    const e = bandes[i].essence;
    if (!cols.has(e)) cols.set(e, []);
    cols.get(e).unshift(p);                       // tronc en haut
  });
  const C = [...cols.values()];
  const W = C.reduce((s, l) => s + Math.max(...l.map(p => p.w)) + MARGE, MARGE);
  const H = Math.max(...C.map(l => l.reduce((s, p) => s + 2 * p.h + MARGE, MARGE)));
  const rgb = new Uint8Array(W * H * 3).fill(0x24);
  let x = MARGE;
  for (const l of C) {
    let y = MARGE;
    for (const p of l) {
      for (let r = 0; r < 2 * p.h; r++)
        for (let c = 0; c < p.w; c++) {
          const q = ((r % p.h) * p.w + c) * 4;
          if (p.rgba[q + 3]) rgb.set(RAMPE[(p.rgba[q + 1] >> 4) & 7], ((y + r) * W + x + c) * 3);
        }
      y += 2 * p.h + MARGE;
    }
    x += Math.max(...l.map(p => p.w)) + MARGE;
  }
  fs.mkdirSync(dossier, { recursive: true });
  const f = path.join(dossier, 'controle_ecorces.png');
  png.write(f, W, H, rgb);
  console.log(`  ${path.relative(RACINE, f)} ${W}×${H} (colonnes : ${[...cols.keys()].join(', ')})`);
}

principal();

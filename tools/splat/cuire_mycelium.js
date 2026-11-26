#!/usr/bin/env node
// SYMBIOSE — tools/splat/cuire_mycelium.js (sprint LISIÈRE & CHARGEMENT ④, décision L3)
// Cuit l'ÉCRAN DE CHARGEMENT en mycélium (scène : recettes/mycelium.js) en DEUX images :
//   • `mycelium_couleur.png` 960×270 RGBA : à gauche le FOND (décor sans âge, racine nue),
//     à droite le MYCÉLIUM seul (pixels dont le splat propriétaire porte un âge), couleurs de
//     la scène complète (occlusions justes : une hyphe derrière la racine n'y est pas) ;
//   • `mycelium_ages.png` 480×270 : niveau de gris = âge × 255 du splat propriétaire,
//     alpha 255 là où le mycélium est posé.
// Le shader de la vue (`shaders/chargement_mycelium.gdshader`) montre le mycélium là où
// âge ≤ progression, le fond partout ailleurs.
//
// Usage (racine du dépôt) :
//   node tools/splat/cuire_mycelium.js [--sortie assets/chargement] [--maquette DOSSIER]
// `--maquette` = la PORTE DE DÉCISION du ④ : pour p = 0,1 · 0,4 · 0,7 · 1, compare la
// révélation par carte des âges à la VÉRITÉ (ink-studio rendu au temps t = p, splats
// `born` ≤ p) ; écrit les deux images côte à côte (×2) et l'écart par p.
//
// 📖 Pédagogie : le « propriétaire » d'un pixel = le splat qui le couvre le plus (passe
// `splatId`) ; son âge est un ENTIER de la carte, jamais une moyenne — on ne mélange pas
// deux instants, comme on ne moyenne pas deux indices de palette.
'use strict';

const path = require('path');
const fs = require('fs');
const ink = require('./vendor/ink');
const png = require('./vendor/ink/cli/png.js');
const { palette } = require('./portraits/sculpteur');
const { COULEURS, scene } = require('./recettes/mycelium');

const RACINE = path.resolve(__dirname, '..', '..');
const W = 480, H = 270, PX_PAR_UNITE = 30;
const FOV = (38 * Math.PI) / 180;
const CAM = { yaw: 0, pitch: 0, target: [0, 0, 0] };

// Sculpte et cuit la scène (avec ou sans mycélium) → monde ink.
function monde(L, avecMycelium) {
  const { pal, M } = palette(COULEURS);
  const B = L.makeBuilder(7, pal), S = L.KIT.sculpt(L.makeSculpt(B));
  S.sun = L.KIT.V.norm([-0.5, 0.75, 0.45]); S.amb = 0.42; S.sky = 0.22; S.sunK = 0.6;
  const infos = scene(S, M, (i, j) => L.KIT.hash(4242, i, j), avecMycelium);
  S.bake();
  const m = B.finish({ cam: { target: CAM.target, dist: 11, pitch: CAM.pitch, yaw: CAM.yaw }, detail: 20, dither: 0.25, radius: 10 });
  m.grow = { rate: 1, fade: 1e-3 };   // `born` : apparition franche (vérité de la maquette)
  return { m, infos };
}

function photo(m, t, passes) {
  return ink.render(m, { w: W, h: H, px: 1, ortho: true, transparent: true, colored: true, t,
    yaw: CAM.yaw, pitch: CAM.pitch, target: CAM.target, dist: (H / 2 / PX_PAR_UNITE) / Math.tan(FOV / 2),
    ...(passes ? { passes } : {}) });
}

// Âge du splat propriétaire de chaque pixel (−1 : splat sans âge ou pixel vide).
function carteAges(m, f) {
  const id = f.passes.splatId, ages = new Float32Array(W * H).fill(-1);
  for (let i = 0; i < W * H; i++) {
    if (!id[i] || !f.alpha[i]) continue;
    const o = (id[i] - 1) * 16;
    if (m.data[o + 11] & 512) ages[i] = m.data[o + 15];
  }
  return ages;
}

function cuire(L) {
  const fond = photo(monde(L, false).m, 0);
  const { m, infos } = monde(L, true);
  const tout = photo(m, 10, ['splatId']);
  const ages = carteAges(m, tout);
  const rgb = new Uint8Array(2 * W * H * 3), alpha = new Uint8Array(2 * W * H);
  const gris = new Uint8Array(W * H * 3), agesA = new Uint8Array(W * H);
  let poses = 0;
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const i = y * W + x, g = y * 2 * W + x, d = g + W;
      for (let c = 0; c < 3; c++) rgb[g * 3 + c] = fond.rgb[i * 3 + c];
      alpha[g] = fond.alpha[i] >= 128 ? 255 : 0;
      if (ages[i] < 0) continue;
      for (let c = 0; c < 3; c++) rgb[d * 3 + c] = tout.rgb[i * 3 + c];
      alpha[d] = 255;
      const a = Math.max(1, Math.round(ages[i] * 255));   // 0 réservé : « rien »
      gris[i * 3] = gris[i * 3 + 1] = gris[i * 3 + 2] = a;
      agesA[i] = 255;
      poses++;
    }
  return { fond, tout, ages, rgb, alpha, gris, agesA, poses, infos, splats: m.count };
}

// Révélation de la vue (même règle que le shader, sans le front) : RGBA W×H.
function reveler(c, p) {
  const out = new Uint8Array(W * H * 3), a = new Uint8Array(W * H);
  for (let y = 0; y < H; y++)
    for (let x = 0; x < W; x++) {
      const i = y * W + x, g = y * 2 * W + x, src = c.ages[i] >= 0 && c.ages[i] <= p ? g + W : g;
      for (let k = 0; k < 3; k++) out[i * 3 + k] = c.rgb[src * 3 + k];
      a[i] = c.alpha[src];
    }
  return { rgb: out, alpha: a };
}

function maquette(L, c, dossier) {
  const { m } = monde(L, true);
  fs.mkdirSync(dossier, { recursive: true });
  for (const p of [0.1, 0.4, 0.7, 1]) {
    const vrai = photo(m, p), vue = reveler(c, p);
    // Écart, sur les pixels du mycélium (âge connu à pleine pousse) : la vérité y montre-t-elle
    // le mycélium (couleur plus proche de lui que du fond) ? La vue le montre si âge ≤ p.
    let myc = 0, manque = 0, enTrop = 0;
    const dist = (a, i, b, j) => Math.max(...[0, 1, 2].map(k => Math.abs(a[i * 3 + k] - b[j * 3 + k])));
    for (let y = 0; y < H; y++)
      for (let x = 0; x < W; x++) {
        const i = y * W + x, g = y * 2 * W + x;
        if (c.ages[i] < 0) continue;
        const ouVue = c.ages[i] <= p;
        const ouVrai = vrai.alpha[i] >= 128 && (c.alpha[g] < 128 || dist(vrai.rgb, i, c.rgb, g + W) < dist(vrai.rgb, i, c.rgb, g));
        if (ouVue) myc++;
        if (ouVue && !ouVrai) enTrop++;
        if (!ouVue && ouVrai) manque++;
      }
    const faux = manque + enTrop;
    // Planche : vue (gauche) | vérité (droite), ×2, fond de sol.
    const PW = 2 * W, S2 = 2, out = new Uint8Array(PW * S2 * H * S2 * 3);
    const sol = [0x96, 0x7a, 0x64];
    for (let y = 0; y < H * S2; y++)
      for (let x = 0; x < PW * S2; x++) {
        const sx = (x / S2) | 0, sy = (y / S2) | 0, droite = sx >= W, i = sy * W + (droite ? sx - W : sx);
        const src = droite ? vrai : vue, on = src.alpha[i] >= 128, q = (y * PW * S2 + x) * 3;
        for (let k = 0; k < 3; k++) out[q + k] = on ? src.rgb[i * 3 + k] : sol[k];
      }
    const f = path.join(dossier, `04_maquette_p${String(p).replace('.', '')}.png`);
    png.write(f, PW * S2, H * S2, out);
    console.log(`p=${p} : mycélium révélé ${myc} px, écart vue/vérité ${faux} px `
      + `(${(100 * faux / Math.max(1, myc)).toFixed(1)} % du révélé ; manquants ${manque}, en trop ${enTrop}) → ${f}`);
  }
}

function principal() {
  const argv = process.argv.slice(2);
  const opt = k => { const i = argv.indexOf(k); return i >= 0 ? argv.splice(i, 2)[1] : null; };
  const sortie = path.resolve(RACINE, opt('--sortie') || 'assets/chargement');
  const dossierMaquette = opt('--maquette');
  const L = ink.load(), t0 = Date.now();
  const c = cuire(L);
  fs.mkdirSync(sortie, { recursive: true });
  const fc = path.join(sortie, 'mycelium_couleur.png'), fa = path.join(sortie, 'mycelium_ages.png');
  png.write(fc, 2 * W, H, c.rgb, c.alpha);
  png.write(fa, W, H, c.gris, c.agesA);
  // Importeur « keep » (comme les planches, lib/planche.js) : Godot exporte l'octet tel quel.
  for (const f of [fc, fa]) if (!fs.existsSync(f + '.import')) fs.writeFileSync(f + '.import', '[remap]\n\nimporter="keep"\n');
  console.log(`${c.splats} splats, ${c.infos.noeuds.length} nœuds d'hyphes, contact à ${c.infos.contact.d.toFixed(2)} u, `
    + `${c.poses} px de mycélium, ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  console.log(`${fc} ${fs.statSync(fc).size} o · ${fa} ${fs.statSync(fa).size} o`);
  if (dossierMaquette) maquette(L, c, path.resolve(RACINE, dossierMaquette));
}

principal();

#!/usr/bin/env node
// SYMBIOSE — tools/splat/mesurer_vues.js (sprint PRÉCUISSON SPLATS ①)
// MESURE du nombre de vues V d'une recette : combien de lacets (et
// d'inclinaisons) faut-il cuire pour qu'un organe qui tourne ne « saute » pas ?
//
// Méthode : on photographie la pièce tous les 3,75° de lacet (96 photos par
// palier) et on compare les SILHOUETTES (masque posé/vide), recalées sur leur
// point d'attache, par 1 − IoU (intersection / union ; 0 = identiques, 1 =
// disjointes). Pour V lacets cuits (V multiple de 4 : la rotation D35 par quarts
// de tour retombe alors sur des vues cuites) on mesure :
//   • « saut »  = 1 − IoU entre deux vues cuites voisines (ce que l'œil voit au
//                 moment où l'assemblage bascule d'une vue à l'autre) ;
//   • « écart » = 1 − IoU entre l'organe à mi-chemin et la vue cuite retenue
//                 (l'erreur de forme au pire moment).
// Puis, en inclinaison, le saut entre 0° et ±15/30/45° (lacets 0° et 90°).
//
// Usage : node tools/splat/mesurer_vues.js feuille_composee [--paliers 0.5,1,2,4,8,16]
// Sortie : tableau console (temps compris), rien d'écrit sur disque.
//
// 📖 Pédagogie : IoU (indice de Jaccard) est la mesure standard de recouvrement
// de deux formes ; ici elle répond à « combien de pixels changent quand on passe
// d'une vue à l'autre », rapporté à la taille de la pièce.

'use strict';

const ink = require('./vendor/ink');
const iso = require('./lib/iso');
const codes = require('./lib/codes');
const atelier = require('./cuire.js');

const PAS = 96;                 // photos par tour (3,75°)
const CANDIDATS = [4, 8, 12, 16, 24];

// Masque posé/vide recalé sur l'attache : Set de "x,y" relatifs à l'attache.
function masque(p) {
  const m = new Set();
  for (let y = 0; y < p.h; y++)
    for (let x = 0; x < p.w; x++)
      if (p.rgba[(y * p.w + x) * 4 + 3]) m.add((x - p.attache[0]) + ',' + (y - p.attache[1]));
  return m;
}

function unMoinsIoU(a, b) {
  let inter = 0;
  for (const k of a) if (b.has(k)) inter++;
  const union = a.size + b.size - inter;
  return union ? 1 - inter / union : 0;
}

const moy = t => t.reduce((s, v) => s + v, 0) / t.length;

function principal() {
  const argv = process.argv.slice(2);
  const recette = require(`./recettes/${argv[0]}.js`);
  const i = argv.indexOf('--paliers');
  const paliers = i >= 0 ? argv[i + 1].split(',').map(Number) : [0.5, 1, 2, 4, 8, 16];
  const L = ink.load(), tons = atelier.tableTons();
  const photo = (monde, z, deg) =>
    codes.piece(iso.photographier(ink, monde, recette.rayonCm, z, (deg * Math.PI) / 180), monde, tons);
  const monde0 = atelier.cuireMonde(L, recette, 0, 0);
  console.log(`${recette.nom} — 1 − IoU des silhouettes (moyenne / max), variante 0, inclinaison 0`);
  for (const z of paliers) {
    const t0 = Date.now();
    const m = Array.from({ length: PAS }, (_, k) => masque(photo(monde0, z, (360 * k) / PAS)));
    const ligne = [];
    for (const V of CANDIDATS) {
      const d = PAS / V, sauts = [], ecarts = [];
      for (let v = 0; v < V; v++) {
        sauts.push(unMoinsIoU(m[v * d], m[((v + 1) * d) % PAS]));
        if (d % 2 === 0) ecarts.push(unMoinsIoU(m[v * d], m[v * d + d / 2]));
      }
      ligne.push(`V=${V} saut ${moy(sauts).toFixed(2)}/${Math.max(...sauts).toFixed(2)}` +
        (ecarts.length ? ` écart ${moy(ecarts).toFixed(2)}/${Math.max(...ecarts).toFixed(2)}` : ''));
    }
    const px = Math.round(moy(m.map(s => s.size)));
    console.log(`×${z} (~${px} px posés, ${((Date.now() - t0) / PAS).toFixed(0)} ms/photo) : ${ligne.join(' | ')}`);
  }
  console.log('Inclinaison (lacets 0° et 90°) : 1 − IoU par rapport à 0°');
  const zi = paliers.filter(z => z >= 1 && z <= 8);
  for (const inc of [-45, -30, -15, 15, 30, 45]) {
    const monde = atelier.cuireMonde(L, recette, 0, inc);
    const r = zi.map(z => {
      const v = [0, 90].map(deg => unMoinsIoU(masque(photo(monde0, z, deg)), masque(photo(monde, z, deg))));
      return `×${z} ${moy(v).toFixed(2)}`;
    });
    console.log(`  ${inc > 0 ? '+' : ''}${inc}° : ${r.join('  ')}`);
  }
}

principal();

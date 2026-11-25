#!/usr/bin/env node
// SYMBIOSE — tools/splat/cuire_portraits.js (sprint PRÉCUISSON SPLATS ⑥)
// Les PORTRAITS : 3 par espèce (D6 — jeune · mûre en pleine saison · fin de cycle ou
// hiver), plantes entières en gaussian splats, rendues comme le prototype tomate
// (palette pleine, lumière cuite) : des ILLUSTRATIONS pour l'encyclopédie et le
// magazine (affichage au ⑦), pas des pièces de jeu.
//
// Sources (aucune table recopiée) :
//   • la ligne de l'espèce dans la VUE, lue dans le C# (portraits/table_cs.js) ;
//   • le MOTEUR : cycle de vie, stades, et le squelette des lianes et arbres
//     (portraits/moteur.py, lecture seule — golden intact) ;
//   • les organes = recettes du jardin ②③ (portraits/organes.js).
//
// Usage (racine du dépôt, Node ≥ 18 + python3) :
//   node tools/splat/cuire_portraits.js [Espece …]   # sans espèce : toutes
//        [--sortie assets/portraits]
//   node tools/splat/cuire_portraits.js --manifeste  # écrit portraits.json
// En parallèle : `node tools/splat/cuire_portraits.js --liste | xargs -P 10 -n 1 node tools/splat/cuire_portraits.js`.
//
// Sortie : `<sortie>/<Espece>_{jeune,mure,fin}.png` — TAILLE × TAILLE px d'art (à
// afficher à échelle entière, filtre Nearest), fond TRANSPARENT (l'encyclopédie pose
// son propre fond) ; chaque portrait est cadré sur SA plante (pas d'échelle commune :
// un pommier et une violette remplissent le même cadre). Déterministe (graines fixes).
//
// 📖 Pédagogie : la caméra est ORTHOGRAPHIQUE (comme la vue iso du jeu), cadrée sur
// la boîte englobante que le portrait a notée en sculptant : on projette ses 8 coins
// sur les axes de l'écran et on règle la cible et le zoom pour qu'ils tiennent.

'use strict';

const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');
const ink = require('./vendor/ink');
const png = require('./vendor/ink/cli/png.js');
const { lireTable } = require('./portraits/table_cs');
const { Portrait } = require('./portraits/organes');
const { palette } = require('./portraits/sculpteur');
const { etats, couleurs } = require('./portraits/etats');
const bas = require('./portraits/ports_bas');
const hauts = require('./portraits/ports_hauts');
const { arbre, liane } = require('./portraits/arbres');

const RACINE = path.resolve(__dirname, '..', '..');
const TAILLE = 240;                                   // px d'art, carré
const LACET = 5.31, TANGAGE = 0.3;                    // caméra du prototype (trois quarts)
const FOV = (38 * Math.PI) / 180;                     // vendor/ink/cli/render.js
// La plante tient dans ~6 unités ink (échelle du prototype). Un ARBRE est sculpté plus grand :
// la grille d'ink-studio a des cellules d'au moins 0,9 unité, une couronne de 1 400 feuilles
// dans 6 unités en entasse des centaines par cellule (cuisson > 5 min) ; à 36 unités, ~1 min.
const UNITES = { port: 6, liane: 6, arbre: 36 };
const AGES_LIANE = [8, 30], AGES_ARBRE = [3 * 52, 10 * 52];   // semaines (prototype ; export_structure)

// Le moteur : fiches de toutes les espèces + structures des lianes et arbres.
function lireMoteur(table) {
  const args = [...Object.keys(table.lianes).map(e => `${e}:${AGES_LIANE}`),
    ...Object.keys(table.rameaux).map(e => `${e}:${AGES_ARBRE}`)];
  const out = execFileSync('python3', [path.join(__dirname, 'portraits', 'moteur.py'), ...args],
    { cwd: RACINE, maxBuffer: 1 << 28 });
  return JSON.parse(out);
}

// La sorte de portrait d'une espèce et sa taille approximative (cm), avant sculpture.
function sorte(table, moteur, esp) {
  if (table.rameaux[esp]) return { genre: 'arbre' };
  if (table.lianes[esp]) return { genre: 'liane' };
  const pr = table.prairie[esp];
  if (pr) {
    const hCm = Math.max(...moteur[esp].stades.map(s => s.hauteur_cm || 0));
    return { genre: 'port', fiche: bas.fichePrairie(pr, table.constPrairie, {}, hCm) };
  }
  if (table.ports[esp]) return { genre: 'port', fiche: table.ports[esp] };
  throw new Error('aucune ligne de vue pour ' + esp);
}

const tigeDe = f => (f.Tige && f.Tige.Tige) || (f.Chaume && f.Chaume.Couleur) || (f.Buisson && f.Buisson.Bois) || null;

// Sculpte un état d'une espèce dans le portrait P.
function sculpter(o, s, table, moteur, esp, etat) {
  if (s.genre === 'arbre') {
    const st = moteur[esp].structures[etat.nom === 'jeune' ? 0 : 1];
    return arbre(o, st, table.rameaux[esp], table.fruitsArbres[esp] || null, table.grappes[esp] || null);
  }
  if (s.genre === 'liane') return liane(o, moteur[esp].structures[etat.nom === 'jeune' ? 0 : 1], table.lianes[esp]);
  const port = { Rosette: bas.rosette, Tapis: bas.tapis, Rampante: bas.rampante,
    Tige: hauts.tige, Chaume: hauts.chaume, Buisson: hauts.buisson, Volubile: hauts.volubile }[s.fiche.Forme];
  return port(o, s.fiche);
}

// Taille de la plante (cm) pour fixer l'échelle ink avant de sculpter.
function etendueCm(s, table, moteur, esp, etat) {
  if (s.genre !== 'port') {
    const st = moteur[esp].structures[etat.nom === 'jeune' ? 0 : 1];
    return Math.max(30, st.footprint.height_cm, 2 * st.footprint.canopy_radius_cm);
  }
  const f = s.fiche;
  return Math.max(10, Math.max(f.HauteurAdulteCm, f.HautFeuillesCm, 2 * f.RayonCm) * etat.echelle);
}

// Base écran (droite, haut) de la caméra — même calcul que lib/iso.js, tangage libre.
function baseEcran(lacet, tangage) {
  const cp = Math.cos(tangage), sp = Math.sin(tangage);
  const z = [cp * Math.sin(lacet), sp, cp * Math.cos(lacet)], x = [Math.cos(lacet), 0, -Math.sin(lacet)];
  return { x, y: [z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0]] };
}

function cadrer(boite) {
  const { x, y } = baseEcran(LACET, TANGAGE), dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const coins = [];
  for (let i = 0; i < 8; i++) coins.push([0, 1, 2].map(k => boite[(i >> k) & 1][k]));
  const px = coins.map(c => dot(c, x)), py = coins.map(c => dot(c, y));
  const cx = (Math.min(...px) + Math.max(...px)) / 2, cy = (Math.min(...py) + Math.max(...py)) / 2;
  const c = [0, 1, 2].map(k => (boite[0][k] + boite[1][k]) / 2);
  const target = [0, 1, 2].map(k => c[k] + x[k] * (cx - dot(c, x)) + y[k] * (cy - dot(c, y)));
  const demi = 1.06 * Math.max(Math.max(...px) - Math.min(...px), Math.max(...py) - Math.min(...py)) / 2;
  return { target, demi, rayon: demi * 1.8 + 1 };
}

function portrait(L, s, table, moteur, esp, etat, k) {
  const pal = table.palettes[esp] || table.paletteDefaut;
  const coul = { ...couleurs(etat, pal, tigeDe(s.fiche || {}) || (table.lianes[esp] && table.lianes[esp].Organes.Tige.Tige), table.automneDefaut),
    ...(s.fiche && s.fiche.Pied ? { pied: s.fiche.Pied } : {}),
    ...(s.fiche && s.fiche.Tapis && s.fiche.Tapis.Stolon ? { stolon: s.fiche.Tapis.Stolon } : {}) };
  const { pal: hex, M } = palette(coul);
  const B = L.makeBuilder(11 + k, hex), S = L.KIT.sculpt(L.makeSculpt(B));
  S.sun = L.KIT.V.norm([-0.55, 0.75, 0.45]); S.amb = 0.4; S.sky = 0.22; S.sunK = 0.6;
  const u = UNITES[s.genre], g = u / etendueCm(s, table, moteur, esp, etat);
  const P = new Portrait(S, L.KIT, M, g, 0.8 * u * 1.2 / TAILLE);   // pas plancher ≈ 0,8 px d'art
  const h = (i, j) => L.KIT.hash(1000 + k, i, j);
  sculpter(bas.outils(P, M, h, etat), s, table, moteur, esp, etat);
  const b = P.boite, R = Math.max(b[1][0] - b[0][0], b[1][2] - b[0][2]) * 0.5;
  P.noter([0, 0, 0], 0);
  S.ground(M.sol, { rad: Math.max(R * 0.8, 3) * g, res: Math.max(P.resMin * 1.5, 0.02) });
  P.noter([R * 0.8, 0, R * 0.8]); P.noter([-R * 0.8, 0, -R * 0.8]);
  S.bake();
  const cad = cadrer(P.boite.map(c => c.map(v => v * g)));
  const monde = B.finish({ cam: { target: cad.target, dist: 11, pitch: TANGAGE, yaw: LACET }, detail: 20, dither: 0.25, radius: cad.rayon });
  const f = ink.render(monde, { w: TAILLE, h: TAILLE, px: 1, ortho: true, transparent: true, colored: true,
    yaw: LACET, pitch: TANGAGE, target: cad.target, dist: cad.demi / Math.tan(FOV / 2) });
  return { f, splats: monde.count };
}

function manifeste(table, moteur, sortie) {
  const especes = {};
  for (const esp of Object.keys(moteur).sort()) {
    const s = sorte(table, moteur, esp);
    especes[esp] = { port: s.genre === 'port' ? s.fiche.Forme : s.genre,
      ...Object.fromEntries(etats(moteur[esp]).map(e => [e.nom, { fichier: `${esp}_${e.nom}.png`, libelle: e.libelle }])) };
  }
  const doc = { taille_px: TAILLE, fond: 'transparent', ordre: ['jeune', 'mure', 'fin'],
    niveaux_encyclopedie: { 1: 'jeune', 2: 'mure', 3: 'fin' }, magazine: 'mure', especes };
  const f = path.join(sortie, 'portraits.json');
  fs.writeFileSync(f, JSON.stringify(doc, null, 1) + '\n');
  console.log(`${f} : ${Object.keys(especes).length} espèces`);
}

function principal() {
  const argv = process.argv.slice(2);
  const i = argv.indexOf('--sortie');
  const sortie = path.resolve(RACINE, i >= 0 ? argv.splice(i, 2)[1] : 'assets/portraits');
  const table = lireTable(), moteur = lireMoteur(table);
  if (argv[0] === '--liste') return console.log(Object.keys(moteur).sort().join('\n'));
  fs.mkdirSync(sortie, { recursive: true });
  if (argv[0] === '--manifeste') return manifeste(table, moteur, sortie);
  const L = ink.load();
  for (const esp of argv.length ? argv : Object.keys(moteur).sort()) {
    const s = sorte(table, moteur, esp);
    etats(moteur[esp]).forEach((etat, k) => {
      const t0 = process.hrtime.bigint();
      const { f, splats } = portrait(L, s, table, moteur, esp, etat, k);
      const fichier = path.join(sortie, `${esp}_${etat.nom}.png`);
      png.write(fichier, f.w, f.h, f.rgb, f.alpha);
      console.log(`${esp} ${etat.nom} : ${splats} splats, ${(Number(process.hrtime.bigint() - t0) / 1e9).toFixed(1)} s, ${fs.statSync(fichier).size} o`);
    });
  }
}

principal();

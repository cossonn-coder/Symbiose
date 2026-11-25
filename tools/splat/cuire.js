#!/usr/bin/env node
// SYMBIOSE — tools/splat/cuire.js (sprint PRÉCUISSON SPLATS ①)
// L'ATELIER DE CUISSON : une recette (un organe sculpté en splats, ink-studio) →
// ses pièces cuites sous V vues (lacet × inclinaison) × variantes × 7 paliers,
// dans la langue de la palette indexée de la vue (lib/codes.js), rangées en
// planches PNG + manifeste JSON (lib/planche.js), plus une planche de contrôle.
//
// Usage (depuis la racine du dépôt, Node ≥ 18, VM seulement) :
//   node tools/splat/cuire.js feuille_composee
//        [--sortie assets/splats] [--controle DOSSIER] [--lacets 8]
//        [--inclinaisons -30,0,30] [--paliers 0.5,1,2,4,8,16,32]
//        [--actuel capture.png:x,y,w,h]   (pièce actuelle de la vue, collée sous
//                                          la planche de contrôle pour comparer)
//
// Cuisson SANS SOLEIL (sunK = 0) : le soleil, c'est le shader de la vue qui le
// pose en jeu, côté soleil réel (philo « une géométrie, toutes les teintes »).
// Il ne reste que le volume : occlusion ambiante et ciel (revers plus sombre).
//
// 📖 Pédagogie : la boucle est « sculpter une fois, photographier N fois ». La
// cuisson des splats (S.bake, ~0,2 s) dépend de la forme (variante,
// inclinaison) ; le lacet et le palier ne sont que des réglages de caméra, donc
// une même cuisson sert toutes les photos — comme un modèle 3D qu'on tourne.
//
// ② : axes propres à une recette (lus dans la recette, sinon les défauts) :
//   • `trous: true` → en plus, les DEGRÉS DE TROUS (lib/trous.js, D5) aux seuls
//     paliers où la vue montre les symptômes (PALIERS_TROUS, cf.
//     PlantRenderer.PaliersHauts.cs), pour les TROUS_VARIANTES premières
//     variantes ; ajoutés APRÈS les pièces saines (celles-ci gardent leur place) ;
//   • `tailles: [3, 5, 7, 9]` (touffes du kit des paliers bas, D4) → la pièce est
//     cuite à ces largeurs en px internes au lieu des paliers (zoom déduit de
//     `empriseCm`, la largeur vue de la pièce, sinon du rayon), rangée dans la planche « kit » ; `lacets`, `inclinaisons` propres.
// RELIQUATS ② : CLASSES DE TAILLE (lib/classes.js, décision E8) — chaque palier est
//   cuit à 1-3 échelles k de la recette : photo au zoom z·k, même monde sculpté ; la
//   classe k = 1 garde ses planches et ses octets, les autres vont dans
//   `<recette>_x<z>_k<100·k>.png` ; chaque pièce porte `echelle` et `taille_cm`.
// ③ : `paliers` propres (le bois ne se cuit qu'aux paliers où il est large) et
//   `couches: ['petales', 'coeur']` → une pièce PAR COUCHE et par vue (même
//   cadrage, champ `couche` du manifeste ; lib/organe.js, lib/codes.js).
//
// RELIQUATS ③ : `--details` → les SUR-COUCHES de détail de la recette (lib/details.js :
//   nervures, duvet, poils, éclat, revers, pruine, glandes, gouttes, étamines). Même
//   sculpture, MÊMES vues, détails ajoutés au monde ; seules les couches de détail sont
//   extraites (un pixel leur appartient dès que leur splat est propriétaire d'un tiers de
//   ses échantillons), sans trous, aux paliers de la table → `<recette>_details.json`.
//   La pièce de base n'est pas recuite.
//
// Déterministe : graines fixes, aucune horloge dans les fichiers écrits (les
// temps ne vont qu'à la console). Golden non concerné (outil hors moteur).

'use strict';

const path = require('path');
const fs = require('fs');
const ink = require('./vendor/ink');
const png = require('./vendor/ink/cli/png.js');
const iso = require('./lib/iso');
const { TROUS } = require('./lib/trous');
const codes = require('./lib/codes');
const planche = require('./lib/planche');
const controle = require('./lib/controle');
const { CLASSES, classesDe, suffixe } = require('./lib/classes');
const details = require('./lib/details');

const RACINE = path.resolve(__dirname, '..', '..');
const GRAINE = 7;
// Rampe de volume : 10 crans de gris (couleurs distinctes, lues en retour par
// couleur emballée) ; t = occlusion × (ambiant + ciel·(½ + ½·n_y)).
const CRANS = 10;
const TON_DE = [0, 0, 1, 1, 1, 2, 2, 2, 2, 2];   // t < 0,2 creux · < 0,5 ombre · base
const AMBIANT = 0.75, CIEL = 0.25;              // revers (n_y = −1) : t × 0,75
const PALIERS_TROUS = [16, 32];                 // PalierSymptomesZoom et au-delà
const TROUS_VARIANTES = 1;                      // variantes trouées (poids, cf. 00_etat ②)
const INCLINAISONS = [-30, 0, 30];              // V retenu au ① (8 lacets × 3)

function options(argv) {
  const o = { recette: argv[0], sortie: 'assets/splats', controle: null, actuel: null, lacets: null,
    inclinaisons: null, paliers: null, details: false };
  for (let i = 1; i < argv.length; i += 2) {
    const k = argv[i].replace(/^--/, ''), v = argv[i + 1];
    if (k === 'details') { o.details = true; i--; }
    else if (k === 'lacets') o.lacets = +v;
    else if (k === 'inclinaisons') o.inclinaisons = v.split(',').map(Number);
    else if (k === 'paliers') o.paliers = v.split(',').map(Number);
    else if (k in o) o[k] = v;
    else throw new Error('option inconnue --' + k);
  }
  if (!o.recette) throw new Error('usage : node tools/splat/cuire.js <recette> [options]');
  return o;
}

// Palette du builder : 0 = fond, puis CRANS gris croissants PAR COUCHE (③) ; la
// couche c décale le rouge de c (couleurs distinctes, la couche 0 inchangée).
// RELIQUATS ③ : 8 couches (recette + détails ; lib/codes.js en code 8 au plus).
const COUCHES = 8;
const PALETTE = [0x000000, ...Array.from({ length: CRANS * COUCHES },
  (_, i) => (12 + (i % CRANS) * 24) * 0x010101 + ((i / CRANS) | 0) * 0x010000)];
const RAMPE = Array.from({ length: CRANS }, (_, k) => k + 1);
const rampeCouche = c => RAMPE.map(i => i + c * CRANS);
const tableTons = () => new Map(Array.from({ length: COUCHES },
  (_, c) => [...codes.tableTons(PALETTE, rampeCouche(c), TON_DE, c)]).flat());

// Sculpte et cuit la recette pour une (variante, inclinaison) → monde ink-studio ;
// `avecDetails` : ses détails ajoutés (RELIQUATS ③, couches après celles de la recette).
function cuireMonde(L, recette, variante, inclinaisonDeg, trou = null, avecDetails = false) {
  const B = L.makeBuilder(GRAINE, PALETTE);
  const S = L.KIT.sculpt(L.makeSculpt(B));
  S.sunK = 0; S.amb = AMBIANT; S.sky = CIEL;
  const ctx = { S, K: L.KIT, M: { organe: { r: RAMPE }, couches: Array.from({ length: COUCHES }, (_, c) => ({ r: rampeCouche(c) })) }, variante, trou,
    inclinaison: (inclinaisonDeg * Math.PI) / 180 };
  const sites = recette.sculpter(ctx);
  if (avecDetails) details.sculpter(ctx, recette, sites, (recette.couches || [0]).length);
  S.bake();
  const r = recette.rayonCm / iso.CM_PAR_UNITE + 1;
  return B.finish({ cam: { target: [0, 0, 0], dist: 5, pitch: 0.5, yaw: 0.8 }, detail: 20, dither: 0, radius: r });
}

// Les prises de vue d'une recette : [{ trou, variante, inclinaison, zooms }],
// zooms = [{ z, k, planche, taille?, tailleCm? }]. Pièces saines d'abord, trouées ensuite.
function plan(recette, o) {
  const zooms = recette.tailles
    ? recette.tailles.map(t => ({ z: t / ((recette.empriseCm || 2 * recette.rayonCm) * iso.PX_PAR_CM_X), k: 1, planche: 'kit', taille: t }))
    : o.paliers.flatMap(z => classesDe(recette.nom).map(({ k, tailleCm }) =>
      ({ z, k, tailleCm, planche: planche.nomPalier(z) + suffixe(k) })));
  const prises = [];
  for (const inclinaison of o.inclinaisons)
    for (let variante = 0; variante < recette.variantes; variante++)
      prises.push({ trou: null, variante, inclinaison, zooms });
  if (recette.trous && !o.details) {
    const zt = zooms.filter(q => PALIERS_TROUS.includes(q.z));
    for (const trou of TROUS.filter(Boolean))
      for (const inclinaison of o.inclinaisons)
        for (let variante = 0; variante < Math.min(TROUS_VARIANTES, recette.variantes); variante++)
          if (zt.length) prises.push({ trou, variante, inclinaison, zooms: zt });
  }
  return prises;
}

// Cuit toutes les pièces d'une recette. Retourne { pieces, temps }.
function cuireRecette(recette, o) {
  const L = ink.load();
  const tons = tableTons();
  const pieces = [], temps = { monde: [], photo: new Map() };
  for (const { trou, variante, inclinaison, zooms } of plan(recette, o)) {
    let t = process.hrtime.bigint();
    const monde = cuireMonde(L, recette, variante, inclinaison, trou, o.details);
    temps.monde.push(Number(process.hrtime.bigint() - t) / 1e6);
    for (const q of zooms)
      for (let k = 0; k < o.lacets; k++) {
        const lacetDeg = (360 * k) / o.lacets;
        t = process.hrtime.bigint();
        const photo = iso.photographier(ink, monde, recette.rayonCm, q.z * q.k, (lacetDeg * Math.PI) / 180);
        const couches = o.details ? coucheDetails(recette) : recette.couches || [null];
        const ps = couches.map((n, c) => (o.details ? (c < o.base ? codes.piece(photo, monde, tons, c)
          : codes.piece(photo, monde, tons, c, PART_DETAIL)) : codes.piece(photo, monde, tons, c)));
        const dt = Number(process.hrtime.bigint() - t) / 1e6;
        const cle = q.taille ? 't' + q.taille : q.z * q.k;
        const [n, s] = temps.photo.get(cle) || [0, 0];
        temps.photo.set(cle, [n + 1, s + dt]);
        ps.forEach((p, c) => pieces.push({ palier: q.z, planche: q.planche, taille: q.taille, k: q.k, tailleCm: q.tailleCm, trou, inclinaison,
          variante, lacet: lacetDeg, ...(couches[c] ? { couche: couches[c], ic: c } : {}), ...p }));
      }
  }
  return { pieces, temps };
}

// RELIQUATS ③ : couches photographiées en mode --details = celles de la recette (pour la
// planche de contrôle seulement, préfixées « base: ») puis ses détails.
const PART_DETAIL = 1 / 3;
const coucheDetails = r => [...(r.couches || ['limbe']).map(c => 'base:' + c), ...details.DETAILS[r.nom].couches];

// « capture.png:x,y,w,h » → la région de la capture, { w, h, rgb }.
function recadrer(spec) {
  const [f, r] = spec.split(':'), [x, y, w, h] = r.split(',').map(Number);
  const src = png.read(path.resolve(RACINE, f)), rgb = new Uint8Array(w * h * 3);
  for (let j = 0; j < h; j++)
    rgb.set(src.rgb.subarray(((y + j) * src.w + x) * 3, ((y + j) * src.w + x + w) * 3), j * w * 3);
  return { w, h, rgb };
}

function ecrireControle(dossier, nom, pieces, o) {
  pieces = controle.fusionner(pieces);   // ③ : couches d'une même vue superposées
  if (pieces.some(p => p.taille)) return ecrireControleKit(dossier, nom, pieces);
  // RELIQUATS ② : une ligne par classe de taille (×8, vue de face), puis les lignes
  // d'avant sur la classe la plus proche de k = 1.
  const ks = [...new Set(pieces.map(p => p.k))];
  const kRef = ks.reduce((b, k) => (Math.abs(Math.log(k)) < Math.abs(Math.log(b)) ? k : b));
  const classes = ks.map(k => pieces.find(p => p.k === k && p.palier === 8 && p.lacet === 0 && p.inclinaison === 0
    && p.variante === 0 && !p.trou && p.w > 0)).filter(Boolean);
  pieces = pieces.filter(p => p.k === kRef);
  const lignes = [classes], zooms = [8];
  for (const z of o.paliers)
    for (const inc of o.inclinaisons) {
      lignes.push(pieces.filter(p => p.palier === z && p.inclinaison === inc && p.variante === 0 && !p.trou && p.w > 0));
      zooms.push(z);
    }
  // Variantes côte à côte aux paliers bas (lacet 0) : le hash change-t-il la pièce ?
  for (const z of o.paliers.filter(z => z <= 2)) {
    lignes.push(pieces.filter(p => p.palier === z && p.lacet === 0 && !p.trou && p.w > 0));
    zooms.push(z);
  }
  // Degrés de trous (lacet 0, inclinaison 0) : ×16, une ligne.
  const troues = pieces.filter(p => p.trou && p.palier === 16 && p.lacet === 0 && p.inclinaison === 0 && p.w > 0);
  if (troues.length) {
    lignes.push([pieces.find(p => !p.trou && p.palier === 16 && p.lacet === 0 && p.inclinaison === 0), ...troues]);
    zooms.push(16);
  }
  // Lignes vides écartées (une aiguille de 3 cm ne fait aucun pixel à ×1).
  const garde = lignes.map((l, i) => (l.length ? i : -1)).filter(i => i >= 0);
  const img = controle.composer(garde.map(i => lignes[i]), garde.map(i => zooms[i]), o.actuel && recadrer(o.actuel));
  fs.mkdirSync(dossier, { recursive: true });
  const f = path.join(dossier, `controle_${nom}.png`);
  png.write(f, img.w, img.h, img.rgb);
  return f;
}

// Touffes du kit : une ligne par taille (variantes côte à côte), agrandies ×6.
function ecrireControleKit(dossier, nom, pieces) {
  const tailles = [...new Set(pieces.map(p => p.taille))];
  const img = controle.composer(tailles.map(t => pieces.filter(p => p.taille === t && p.w > 0)), tailles.map(() => 1));
  fs.mkdirSync(dossier, { recursive: true });
  const f = path.join(dossier, `controle_${nom}.png`);
  png.write(f, img.w, img.h, img.rgb);
  return f;
}

function principal() {
  const o = options(process.argv.slice(2));
  const recette = require(`./recettes/${o.recette}.js`);
  if (o.lacets === null) o.lacets = recette.lacets || 8;
  if (o.inclinaisons === null) o.inclinaisons = recette.inclinaisons || INCLINAISONS;
  if (o.details) {
    if (!details.DETAILS[recette.nom]) throw new Error(recette.nom + ' : aucun détail (lib/details.js)');
    if (o.paliers === null) o.paliers = details.DETAILS[recette.nom].paliers;
    o.base = (recette.couches || [0]).length;
  }
  if (o.paliers === null) o.paliers = recette.paliers || iso.PALIERS;
  const t0 = process.hrtime.bigint();
  const tout = cuireRecette(recette, o), temps = tout.temps;
  // --details : seules les couches de détail sont écrites ; la base sert au contrôle.
  const pieces = o.details ? tout.pieces.filter(p => !p.couche.startsWith('base:')) : tout.pieces;
  const meta = {
    format: 'R = niveau kit (2 ombre, 3 base, 4 lumière) ; G = 128 | ton << 4 | orientation ; A = posé',
    px_par_cm_x1: iso.PX_PAR_CM_X, seuil_plat: codes.SEUIL_PLAT,
    lacets: o.lacets, inclinaisons_deg: o.inclinaisons, variantes: recette.variantes,
    ...(recette.vue ? { vue: recette.vue } : {}), ...(recette.notes ? { notes: recette.notes } : {}),
    ...(o.details ? { couches: details.DETAILS[recette.nom].couches, base: recette.nom }
      : recette.couches ? { couches: recette.couches } : {}),
    ...(CLASSES[recette.nom] && !recette.tailles ? { classes: classesDe(recette.nom).map(c => ({ echelle: c.k, taille_cm: c.tailleCm })),
      taille_nominale_cm: CLASSES[recette.nom].nominalCm, rond: !!CLASSES[recette.nom].rond } : {}),
    ...(recette.trous ? { trous: { paliers: PALIERS_TROUS, variantes: TROUS_VARIANTES,
      degres: TROUS.filter(Boolean) } } : {}),
    attache: 'px de la pièce (coin haut-gauche = 0,0), peut sortir du rectangle'
  };
  const nom = recette.nom + (o.details ? '_details' : '');
  const fichiers = planche.ecrire(png, path.resolve(RACINE, o.sortie), nom, meta, pieces);
  if (o.controle) fichiers.push(ecrireControle(path.resolve(RACINE, o.controle), nom, o.details ? tout.pieces : pieces, o));
  const total = Number(process.hrtime.bigint() - t0) / 1e6;
  const vides = pieces.filter(p => p.w === 0).length;
  console.log(`${recette.nom} : ${pieces.length} pièces (${vides} vides), ${total.toFixed(0)} ms au total`);
  console.log(`  sculpture+bake : ${temps.monde.map(t => t.toFixed(0)).join(', ')} ms`);
  for (const [z, [n, t]] of temps.photo) console.log(`  ${z > 0 ? '×' + z : z} : ${(t / n).toFixed(1)} ms/pièce (${n})`);
  for (const f of fichiers) console.log(`  ${path.relative(RACINE, f)} ${fs.statSync(f).size} o`);
}

// Lancé en ligne de commande → cuisson ; requis (mesurer_vues.js) → la boîte à outils.
if (require.main === module) principal();
module.exports = { cuireMonde, tableTons, cuireRecette };

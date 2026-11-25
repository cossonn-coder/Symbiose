// SYMBIOSE — tools/splat/lib/planche.js (sprint PRÉCUISSON SPLATS ①)
// Range les pièces cuites en PLANCHES (une par palier) + écrit le MANIFESTE JSON.
//
// Pourquoi une planche PAR PALIER : la vue ne montre qu'un palier à la fois ; les
// planches ×16/×32 pèsent l'essentiel et pourront être chargées à la demande (④,
// conception §7). Et une recette modifiée ne régénère que ses propres fichiers
// (poids git, règle D2).
//
// Rangement « en étagères » : pièces dans l'ordre de cuisson, de gauche à droite,
// nouvelle étagère quand la largeur est pleine, 1 px de jour entre pièces (comme
// l'atlas du kit). Ordre fixe + aucune horloge dans le manifeste → deux cuissons
// donnent des fichiers identiques à l'octet (vérifié par sha256, cf. README).
//
// 📖 Pédagogie : un atlas évite des milliers de petits PNG (imports Godot, poids
// git) ; le manifeste est la « table des symboles » qui dit où est chaque pièce,
// comme le .map d'un éditeur de liens pointe chaque fonction dans le binaire.

'use strict';

const fs = require('fs');
const path = require('path');

const LARGEUR_MAX = 2048;
const JOUR = 1;

const nomPalier = z => 'x' + String(z).replace('.', '_');

// pieces : [{ palier, planche?, taille?, trou?, inclinaison, variante, lacet, w, h, rgba, attache }]
// → { planches: Map(nom de planche → { w, h, rgba }), entrees: [...] }
// Planche = `planche` de la pièce (② : « kit » pour les touffes), sinon son palier.
function ranger(pieces) {
  const parPalier = new Map();
  for (const p of pieces) {
    const cle = p.planche || nomPalier(p.palier);
    if (!parPalier.has(cle)) parPalier.set(cle, []);
    parPalier.get(cle).push(p);
  }
  const planches = new Map(), entrees = [];
  for (const [z, liste] of parPalier) {
    let x = 0, y = 0, hEtagere = 0, w = 0;
    const places = [];
    for (const p of liste) {
      if (x > 0 && x + p.w > LARGEUR_MAX) { x = 0; y += hEtagere + JOUR; hEtagere = 0; }
      places.push([x, y]);
      x += p.w + JOUR;
      w = Math.max(w, x - JOUR);
      hEtagere = Math.max(hEtagere, p.h);
    }
    const h = y + hEtagere, rgba = new Uint8Array(Math.max(1, w) * Math.max(1, h) * 4);
    liste.forEach((p, k) => {
      const [px, py] = places[k];
      for (let j = 0; j < p.h; j++)
        rgba.set(p.rgba.subarray(j * p.w * 4, (j + 1) * p.w * 4), ((py + j) * w + px) * 4);
      entrees.push({
        palier: p.palier, ...(p.taille ? { taille_px: p.taille } : {}),
        ...(p.tailleCm ? { echelle: p.k, taille_cm: p.tailleCm } : {}),   // RELIQUATS ② (lib/classes.js)
        inclinaison_deg: p.inclinaison, variante: p.variante,
        ...(p.trou ? { trou: p.trou.type, degre: p.trou.degre } : {}), lacet_deg: p.lacet,
        ...(p.couche ? { couche: p.couche } : {}),
        planche: z, rect: [px, py, p.w, p.h],
        attache: [p.attache[0], p.attache[1]]
      });
    });
    planches.set(z, { w: Math.max(1, w), h: Math.max(1, h), rgba });
  }
  return { planches, entrees };
}

// Sidecar Godot d'une planche : « keep » = le PNG est copié tel quel (SplatPlanches.cs).
const IMPORT = '[remap]\n\nimporter="keep"\n';

// Écrit `<dossier>/<recette>_<planche>.png` (+ son `.import` s'il manque) et
// `<dossier>/<recette>.json`. RELIQUATS ② : les planches de CETTE recette qui ne sont
// plus produites (classe de taille retirée) sont effacées avec leur `.import` — motif
// strict, une autre recette au nom plus long (`…_gaufree`) n'est jamais touchée.
// Retourne la liste des fichiers écrits (chemins absolus).
function ecrire(png, dossier, recette, meta, pieces) {
  fs.mkdirSync(dossier, { recursive: true });
  const { planches, entrees } = ranger(pieces);
  const fichiers = [];
  const noms = {};
  for (const [z, pl] of planches) {
    const f = path.join(dossier, `${recette}_${z}.png`);
    fs.writeFileSync(f, png.encode(pl.w, pl.h, pl.rgba, 4));
    if (!fs.existsSync(f + '.import')) fs.writeFileSync(f + '.import', IMPORT);
    noms[z] = path.basename(f);
    fichiers.push(f);
  }
  const motif = new RegExp(`^${recette}_(x[0-9_]+(_k\\d+)?|kit)\\.png$`);
  for (const f of fs.readdirSync(dossier))
    if (motif.test(f) && !Object.values(noms).includes(f)) {
      fs.rmSync(path.join(dossier, f));
      fs.rmSync(path.join(dossier, f + '.import'), { force: true });
    }
  const manifeste = { recette, ...meta, planches: noms, pieces: entrees };
  const fj = path.join(dossier, `${recette}.json`);
  fs.writeFileSync(fj, JSON.stringify(manifeste, null, 1) + '\n');
  fichiers.push(fj);
  return fichiers;
}

module.exports = { ranger, ecrire, nomPalier };

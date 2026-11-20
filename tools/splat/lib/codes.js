// SYMBIOSE — tools/splat/lib/codes.js (sprint PRÉCUISSON SPLATS ①)
// Des passes ink-studio à une PIÈCE dans la langue de la palette indexée de la vue.
//
// Format écrit = celui que l'assemblage sait DÉJÀ lire (atlas du kit,
// visuals/PlantRenderer.Kit.cs + PlantRenderer.Assemblee.cs AssurerMasques) :
//   R = NIVEAU du kit (2 ombre · 3 base · 4 lumière ; 0 vide), éclairé vers le BAS
//       de la pièce comme le kit actuel — ne sert qu'au rendu littéral (F11 OFF) ;
//   G = CODE indexé = 128 | ton << 4 | orientation (visuals/PaletteIndexee.cs:14) ;
//   B = 0 ; A = 255 posé / 0 vide (jamais de demi-transparence aux paliers bas).
//
// ORIENTATION = normale du splat PROPRIÉTAIRE du pixel (passe `normal`, repère
// de l'organe), ramenée au repère monde (lacet) puis projetée par la MÊME
// projection oblique que la vue (WorldView.WorldToScreenOffset + verticale vers
// le haut) — c'est exactement ainsi que PaletteIndexee.MajSoleil projette le
// soleil : face et soleil comparés dans le même repère. Quantifiée à 45°
// (0 = droite, 2 = bas, 6 = haut — même formule que KitCodes.Orientation).
// « Plat » (8) si la normale regarde la caméra à moins de ~17,5° (normale
// projetée sur le plan image plus courte que SEUIL_PLAT = 0,3, le seuil FacePlate
// du kit) : la face n'a pas de côté, elle ne réagit pas au soleil.
//
// TON = le VOLUME hors soleil, lu dans la couleur que ink-studio a cuite pour le
// splat propriétaire : la cuisson est faite SANS soleil (sunK = 0, cf. cuire.js),
// il reste occlusion ambiante × (ambiant + ciel·(½ + ½·n_y)) → creux occlus et
// revers de feuille (normale vers le bas) descendent d'un ton. Rampe du matériau
// = N crans de gris répartis en tons 0 (creux) · 1 (ombre) · 2 (base) par la
// table `tonDe` (cuire.js). Les tons 3-4 (clair,
// éclat) ne sont JAMAIS cuits : c'est le shader qui monte vers le soleil réel.
//
// 📖 Pédagogie : on lit le splat « propriétaire » (le plus proche, opaque à
// > 50 %) plutôt que la couleur mélangée du pixel : un code est un ENTIER, un
// mélange de deux codes n'a pas de sens (comme on ne moyenne pas deux indices de
// palette en embarqué).

'use strict';

const SEUIL_PLAT = 0.3;
const TON_BASE = 2, ORIENT_PLAT = 8;
const SOLEIL_KIT = [0, 1];                 // le kit littéral est éclairé vers le bas
const SEUIL = 0.3, SEUIL_ECLAT = 0.8;      // = palette_indexee.gdshader

const octetB = (ton, orient) => 128 | (ton << 4) | orient;

function orientation(n, base, lacet) {
  const d = base.droite, h = base.haut;
  const sx = n[0] * d[0] + n[1] * d[1] + n[2] * d[2];
  const sy = n[0] * h[0] + n[1] * h[1] + n[2] * h[2];
  if (Math.hypot(sx, sy) < SEUIL_PLAT) return ORIENT_PLAT;
  // Repère organe → monde (l'organe est tourné de `lacet` autour de la verticale),
  // puis ink (x, y haut, z sud) → moteur (x est, y sud, z haut) → écran oblique.
  const c = Math.cos(lacet), s = Math.sin(lacet);
  const mx = n[0] * c + n[2] * s, my = -n[0] * s + n[2] * c, mz = n[1];
  const ex = mx - my, ey = (mx + my) / 2 - mz;          // écran : y vers le bas
  return (((Math.round(Math.atan2(ey, ex) / (Math.PI / 4)) % 8) + 8) % 8);
}

// Même règle que le shader de lecture : ton monté/descendu selon le soleil.
function tonEclaire(ton, orient, soleil) {
  if (orient >= 8) return ton;
  const a = orient * Math.PI / 4, d = Math.cos(a) * soleil[0] + Math.sin(a) * soleil[1];
  return Math.max(0, Math.min(4, ton + (d > SEUIL_ECLAT ? 2 : d > SEUIL ? 1 : d < -SEUIL ? -1 : 0)));
}

// Table couleur emballée (r + g·256 + b·65536, cf. builder.js) → ton. La rampe du
// matériau a N couleurs distinctes (N crans de volume), `tonDe[k]` dit le ton du
// cran k : c'est là que se règlent les seuils creux / ombre / base.
function tableTons(palette, rampe, tonDe, couche = 0) {
  const t = new Map();
  rampe.forEach((idx, k) => {
    const c = palette[idx];
    t.set(((c >> 16) & 255) + ((c >> 8) & 255) * 256 + (c & 255) * 65536, tonDe[k] + 8 * couche);
  });
  return t;
}

// RÉDUCTION : la photo est prise SURÉCHANTILLONNÉE (photo.ss × photo.ss
// échantillons par pixel de la pièce, cf. iso.photographier). Un pixel est posé
// si au moins la moitié de ses échantillons ont un splat propriétaire ; sa
// normale = moyenne des normales des échantillons (puis quantifiée), son ton =
// moyenne arrondie des tons. Sans cette moyenne, un pixel de ×1 (2,5 cm de
// feuille) ne voit qu'UN splat tiré au hasard de la position : le grain du
// sculpteur devient un bruit poivre-et-sel illisible (constaté au ①).
//
// 📖 Pédagogie : c'est l'anti-crénelage par suréchantillonnage (SSAA) — on
// mesure plusieurs points dans le pixel et on résume, au lieu de n'en garder
// qu'un. Même idée qu'un filtre de décimation avant de sous-échantillonner un
// signal (sinon repliement de spectre).
// ③ COUCHES : la table code aussi la couche (valeur = ton + 8 × couche). Un
// pixel posé appartient à la couche MAJORITAIRE de ses échantillons (égalité →
// la plus basse) ; `couche` choisit celle qu'on extrait (une pièce par couche,
// même cadrage, attaches cohérentes). Une seule couche = comportement du ①/②.
function piece(photo, monde, tons, couche = 0) {
  const { passes: P, cote, demi, base, lacet, ss } = photo;
  const grand = cote * ss, n = cote * cote, codes = new Uint8Array(n);
  let x0 = cote, y0 = cote, x1 = -1, y1 = -1, plats = 0, posés = 0;
  const parCouche = new Int32Array(8);
  for (let i = 0; i < n; i++) {
    const X = i % cote, Y = (i / cote) | 0;
    let total = 0;
    parCouche.fill(0);
    for (let j = 0; j < ss; j++)
      for (let u = 0; u < ss; u++) {
        const id = P.splatId[(Y * ss + j) * grand + X * ss + u];
        if (!id) continue;
        const v = tons.get(monde.data[(id - 1) * 16 + 7]);
        if (v === undefined) throw new Error('couleur de splat hors rampe (splat ' + id + ')');
        total++; parCouche[v >> 3]++;
      }
    if (2 * total < ss * ss) continue;
    let maj = 0;
    for (let c = 1; c < 8; c++) if (parCouche[c] > parCouche[maj]) maj = c;
    if (maj !== couche) continue;
    let k = 0, sTon = 0;
    const nv = [0, 0, 0];
    for (let j = 0; j < ss; j++)
      for (let u = 0; u < ss; u++) {
        const q = (Y * ss + j) * grand + X * ss + u, id = P.splatId[q];
        if (!id) continue;
        const v = tons.get(monde.data[(id - 1) * 16 + 7]);
        if (v >> 3 !== couche) continue;
        k++; sTon += v & 7;
        nv[0] += P.normal[q * 3]; nv[1] += P.normal[q * 3 + 1]; nv[2] += P.normal[q * 3 + 2];
      }
    const l = Math.hypot(nv[0], nv[1], nv[2]) || 1;
    // Normales qui s'annulent (pli, arête) : moyenne courte → face « plate ».
    const o = l / k < SEUIL_PLAT ? ORIENT_PLAT : orientation([nv[0] / l, nv[1] / l, nv[2] / l], base, lacet);
    if (o === ORIENT_PLAT) plats++;
    codes[i] = octetB(Math.round(sTon / k), o);
    posés++;
    if (X < x0) x0 = X; if (X > x1) x1 = X; if (Y < y0) y0 = Y; if (Y > y1) y1 = Y;
  }
  if (x1 < 0) return { w: 0, h: 0, rgba: new Uint8Array(0), attache: [demi, demi], stats: { posés: 0, plats: 0 } };
  const w = x1 - x0 + 1, h = y1 - y0 + 1, rgba = new Uint8Array(w * h * 4);
  for (let y = 0; y < h; y++)
    for (let x = 0; x < w; x++) {
      const c = codes[(y + y0) * cote + x + x0];
      if (!c) continue;
      const t = tonEclaire((c >> 4) & 7, c & 15, SOLEIL_KIT);
      const q = (y * w + x) * 4;
      rgba[q] = t <= 1 ? 2 : t === 2 ? 3 : 4;
      rgba[q + 1] = c;
      rgba[q + 3] = 255;
    }
  return { w, h, rgba, attache: [demi - x0, demi - y0], stats: { posés, plats } };
}

module.exports = { TON_BASE, ORIENT_PLAT, SEUIL_PLAT, octetB, orientation, tonEclaire, tableTons, piece };

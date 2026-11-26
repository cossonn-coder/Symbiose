// SYMBIOSE — tools/splat/portraits/arbres.js (sprint PRÉCUISSON SPLATS ⑥)
// ARBRES et LIANES : le squelette est la VRAIE structure du moteur (segments rejoués
// par moteur.py → tools/export_structure._grow), comme la tige du prototype tomate.
// Seul l'habillage vient de la vue :
//   • arbres : `RecetteRameaux` (PlantRenderer.Rameaux.cs : rameaux par mètre de bois
//     feuillé, longueur, ouverture, port, limbe), fruits (`FruitsArbres`,
//     `GrappesFruits`, PlantRenderer.FruitsArbre.cs) ;
//   • lianes (tomate, lierre, jasmin) : `FicheLiane` (PlantRenderer.Lianes.cs : feuille
//     tous les `EspaceCm`, longueur `LongCm`, têtes par site, fruit), et un tuteur.
//
// Bois feuillé = segment fin (épaisseur < `FIN_CM`) ou bourgeon terminal : c'est là
// que la vue pose ses rameaux (elle densifie la couronne sans l'élargir).
// Plafond de feuilles par portrait (`FEUILLES_MAX`) : au-delà, on éclaircit
// uniformément (la silhouette est gardée, la cuisson reste sous la minute).
//
// Repère moteur : x est, y sud, z haut (cm) → portrait : (x, z, y) autour du collet.
// Zéro Math.random.
//
// 📖 Pédagogie : la fidélité « au segment près » est le choix D1 du JARDIN ; le
// portrait la garde pour le bois (c'est gratuit : le moteur le calcule déjà) et
// simplifie le reste — une illustration, pas un relevé.

'use strict';

const { OR, dirA, add, lerp } = require('./ports_bas');
const { trouver } = require('./organes');
const { cone, ramener, etages } = require('./cone');

const FIN_CM = 2.5;                // = LeafMaxThickCm et EcorcePleineCm de la vue
const FEUILLES_MAX = 1400;
const FRUITS_MAX = 70;
const BOUQUETS_MAX = 160;          // bouquets de fleurs par portrait [choix] : cuisson bornée
const LISIBLE = 1 / 160;           // rayon plancher d'un fruit, en part de l'étendue (~1,5 px d'art) [choix]
// Marques d'écorce visibles à l'échelle d'un portrait (~2 cm/px) : seul le bouleau en porte qui
// se lisent (ecorce.js : lenticelles noires, base noire). [choix] `parCm` lenticelles par cm de tronc.
const MARQUES = { BirchTree: { parCm: 0.12, base: 0.07, epaisMin: 3 } };
const mul = (a, k) => a.map(v => v * k);
const norm = a => { const l = Math.hypot(...a) || 1; return a.map(v => v / l); };
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

// `i` = indice d'origine du segment, `parent` = indice d'origine du porteur (null au collet).
function versPortrait(st) {
  const c0 = st.collet_cm;
  return st.segments.map((s, i) => {
    const b = [s.base[0] - c0[0], s.base[2] - c0[2], s.base[1] - c0[1]];
    const d = [s.dir[0], s.dir[2], s.dir[1]];
    return { i, parent: s.parent, b, d, L: s.length_cm, e: s.thickness_cm, apex: s.is_apex, bout: add(b, mul(d, s.length_cm)) };
  }).filter(s => s.L > 0);
}

// AXES (BOIS & ARBRES ⑤, comme BoisAxes.cs) : chaque segment se prolonge par l'enfant le plus
// aligné ; une chaîne = un tube lissé d'un tenant (plus de joint ni de coude à chaque nœud).
function axes(segs) {
  const par = new Map(segs.map(s => [s.i, s])), suite = new Map();
  for (const s of segs) {
    let m = null, best = 0.5;
    for (const x of segs) if (x.parent === s.i && dot(s.d, x.d) > best) { best = dot(s.d, x.d); m = x; }
    if (m) suite.set(s.i, m);
  }
  const suivis = new Set([...suite.values()].map(x => x.i));
  return segs.filter(s => !suivis.has(s.i)).map(s => {
    const ch = [s];
    for (let x = suite.get(s.i); x; x = suite.get(x.i)) ch.push(x);
    return ch;
  }).filter(ch => ch.every(x => par.has(x.i)));
}

// Bois : un tube par AXE ; l'écorce d'essence (fiche de la vue) sur le bois qui en a, le bois
// brun sur les rameaux fins (comme AvecEcorce) ; marques d'écorce lisibles (bouleau).
function bois(o, segs, mat, rMin, esp) {
  const { P, M, h } = o, mq = MARQUES[esp];
  axes(segs).forEach((ch, n) => {
    const pts = [ch[0].b, ...ch.map(s => s.bout)];
    const r0 = Math.max(rMin, ch[0].e * 0.5), r1 = Math.max(rMin, ch[ch.length - 1].e * 0.42);
    P.tube(pts, r0, r1, ch[0].e >= FIN_CM && M.ecorce ? M.ecorce : mat);
    if (!mq || !M.marque) return;
    for (const s of ch) {
      if (s.e < mq.epaisMin) continue;
      const r = s.e * 0.5;
      for (let j = 0; j < Math.round(s.L * mq.parCm); j++) {
        const u = h(n * 100 + s.i, j), a = 6.283 * h(n * 100 + s.i, 50 + j);
        const c = add(add(s.b, mul(s.d, s.L * u)), [Math.cos(a) * r * 0.92, 0, Math.sin(a) * r * 0.92]);
        P.boule(c, r * (0.18 + 0.2 * h(s.i, 90 + j)), M.marque, 0.3);
      }
    }
  });
  const pied = segs.find(s => s.parent == null || s.parent < 0);
  if (mq && M.marque && pied && pied.e >= mq.epaisMin) {
    const H = Math.max(...segs.map(s => s.bout[1]));
    P.tube([[0, 0, 0], [0, H * mq.base, 0]], pied.e * 0.53, pied.e * 0.5, M.marque);   // base noire du bouleau
  }
}

// Fleurs d'arbre (`fa` = FicheFleursArbre de la vue) : un bouquet cuit du ④ au bout des rameaux.
function bouquets(o, rameaux, fa) {
  const { P, M, h, etat } = o;
  if (!fa || !etat.floraisonArbre) return 0;
  const r = trouver('BouquetsArbre (corolles, ×4)'), part = Math.min(1, BOUQUETS_MAX / Math.max(1, rameaux.length));
  let n = 0;
  for (const ra of rameaux) {
    if (h(ra.k, 600) >= part) continue;
    P.poser(r, add(ra.p, mul(ra.d, ra.L * (0.75 + 0.25 * h(ra.k, 601)))), [0, 1, 0], fa.BouquetCm / 3, [M.fleur, M.coeur], ra.k);
    n++;
  }
  return n;
}

// ARBRE. `rr` = RecetteRameaux, `fr` = FicheFruit ou null, `gr` = grappe ou null,
// `fa` = fleurs d'arbre ou null, `regle` = règle du cône (table_cs `cone`), `esp` = espèce.
function arbre(o, st, rr, fr, gr, fa, regle, esp) {
  const { P, M, h, etat } = o;
  const segs = versPortrait(st);
  const H = Math.max(...segs.map(s => s.bout[1]));
  bois(o, segs, M.bois, H / 300, esp);
  const co = cone(segs, esp, regle);
  const feuilles = segs.filter(s => s.e < FIN_CM || s.apex || segs.length < 8);   // jeune arbre : feuillé partout
  const f = { Feuille: rr.Limbe, Marque: 'Aucune' };
  const rameaux = co ? etages(co, rr, h) : [];
  feuilles.forEach((s, i) => {
    const n = Math.max(1, Math.round(rr.ParMetre * s.L / 100));
    for (let k = 0; k < n; k++) {
      const u = (k + 0.5) / n, p = add(s.b, mul(s.d, s.L * u)), a = (i * 7 + k) * OR;
      const lat = norm([Math.cos(a), 0, Math.sin(a)]);
      const d = norm(add(add(mul(s.d, Math.cos(rr.Ouverture)), mul(lat, Math.sin(rr.Ouverture))), [0, rr.Port * 0.8, 0]));
      rameaux.push({ p, d, L: rr.LongCm * (0.6 + 0.4 * h(i, k)), a, k: i * 50 + k });
    }
  });
  if (co) for (const r of rameaux) ramener(co, r);
  const parRameau = rr.Brindilles * rr.FeuillesBrin;
  const garde = Math.min(1, FEUILLES_MAX / Math.max(1, rameaux.length * parRameau)) * etat.densite;
  // Fruits : une grappe sur une part des rameaux, au plus FRUITS_MAX fruits ; rayon relevé au plancher
  // lisible (une cerise de 1 cm ferait un demi-pixel d'art : invisible, cf. 00_etat ⑤).
  const grappe = gr ? gr.Grappe : 1, etendue = Math.max(H, ...segs.map(s => 2 * Math.hypot(s.bout[0], s.bout[2])));
  const frL = fr && etat.fruits ? { ...fr, RayonCm: Math.max(fr.RayonCm, etendue * LISIBLE) } : null;
  const partGrappes = frL ? Math.min(1, FRUITS_MAX / grappe / Math.max(1, rameaux.length)) : 0;
  let fruits = 0;
  for (const r of rameaux) {
    const bout = add(r.p, mul(r.d, r.L));
    P.tube([r.p, add(r.p, mul(add(r.d, [0, rr.Port * 0.3, 0]), r.L * 0.5)), bout], H / 500, H / 900, M.bois);
    for (let j = 0; j < parRameau; j++) {
      if (h(r.k, j) >= garde) continue;
      const u = 0.25 + 0.75 * h(r.k, 100 + j), p = add(r.p, mul(r.d, r.L * u));
      o.feuille(f, add(p, [0, (h(r.k, 200 + j) - 0.5) * 6, 0]), r.a + (j % 2 ? 1.2 : -1.2) + h(r.k, 300 + j),
        -0.25 + 0.3 * rr.Port, rr.LimbeCm * (0.8 + 0.3 * h(r.k, 400 + j)), r.k + j);
    }
    if (!frL || h(r.k, 500) >= partGrappes) continue;
    for (let j = 0; j < grappe; j++) {
      const p = add(bout, [(j - (grappe - 1) / 2) * 2.2 * frL.RayonCm, -(gr ? gr.QueueCm : 1) - frL.RayonCm * (1 + 0.4 * (j % 2)), 0]);
      o.fruit(frL, p, r.a, r.k + j);
      fruits++;
    }
  }
  const fleurs = bouquets(o, rameaux, fa);
  return { feuilles: rameaux.length * parRameau * garde, fruits, fleurs };
}

// LIANE : segments du moteur, feuilles tous les `EspaceCm`, sites de têtes et de
// fruits (une grappe tous les 3 nœuds, comme le prototype), tuteur.
function liane(o, st, l) {
  const { P, M, h, etat } = o, f = l.Organes;
  const segs = versPortrait(st);
  const H = Math.max(...segs.map(s => s.bout[1]));
  P.tube([[4, -2, 2], [4, H + 10, 2]], 0.35, 0.3, M.tuteur);         // tuteur (treillis, mur de la vue), effacé (RELIQUATS ⑤)
  bois(o, segs, M.tige, Math.min(l.TigeMaxCm, 0.6) * 0.5);
  let noeud = 0;
  for (const s of segs) {
    const n = Math.max(1, Math.round(s.L / l.EspaceCm));
    for (let k = 0; k < n; k++, noeud++) {
      const p = add(s.b, mul(s.d, s.L * (k + 0.5) / n)), a = l.Opposees ? noeud * Math.PI / 2 : noeud * OR;
      const t = p[1] / Math.max(1, H), long = l.LongCm * lerp(1, 0.55, t) * Math.sqrt(etat.echelle);
      o.feuille(f, p, a, 0.25 + f.Tige.Penche, long, noeud * 2);
      if (l.Opposees) o.feuille(f, p, a + Math.PI, 0.25 + f.Tige.Penche, long, noeud * 2 + 1);
      if (noeud % 3 !== 2) continue;
      const site = add(p, dirA(a + Math.PI, -0.4).map(v => v * 4));
      for (let j = 0; j < l.FleursSite; j++) {
        const q = add(site, [(j - 1) * 1.6, -j * 1.8, h(noeud, j) - 0.5]);
        if (f.Fruit && etat.fruits && t < 0.75) o.fruit(f.Fruit, add(q, [0, -f.Fruit.RayonCm, 0]), a, noeud * 5 + j);
        else o.tete(f, q, a, noeud * 5 + j);
      }
    }
  }
}

module.exports = { arbre, liane, versPortrait };

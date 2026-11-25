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

const FIN_CM = 2.5;
const FEUILLES_MAX = 1400;
const FRUITS_MAX = 70;
const mul = (a, k) => a.map(v => v * k);
const norm = a => { const l = Math.hypot(...a) || 1; return a.map(v => v / l); };

function versPortrait(st) {
  const c0 = st.collet_cm;
  return st.segments.filter(s => s.length_cm > 0).map(s => {
    const b = [s.base[0] - c0[0], s.base[2] - c0[2], s.base[1] - c0[1]];
    const d = [s.dir[0], s.dir[2], s.dir[1]];
    return { b, d, L: s.length_cm, e: s.thickness_cm, apex: s.is_apex, bout: add(b, mul(d, s.length_cm)) };
  });
}

// Bois : un tube par segment (rayon = demi-épaisseur, plancher lisible).
function bois(o, segs, mat, rMin) {
  for (const s of segs) o.P.tube([s.b, s.bout], Math.max(rMin, s.e * 0.5), Math.max(rMin, s.e * 0.42), mat);
}

// ARBRE. `rr` = RecetteRameaux, `fr` = FicheFruit ou null, `gr` = grappe ou null.
function arbre(o, st, rr, fr, gr) {
  const { P, M, h, etat } = o;
  const segs = versPortrait(st);
  const H = Math.max(...segs.map(s => s.bout[1]));
  bois(o, segs, M.bois, H / 300);
  const feuilles = segs.filter(s => s.e < FIN_CM || s.apex || segs.length < 8);   // jeune arbre : feuillé partout
  const f = { Feuille: rr.Limbe, Marque: 'Aucune' };
  const rameaux = [];
  feuilles.forEach((s, i) => {
    const n = Math.max(1, Math.round(rr.ParMetre * s.L / 100));
    for (let k = 0; k < n; k++) {
      const u = (k + 0.5) / n, p = add(s.b, mul(s.d, s.L * u)), a = (i * 7 + k) * OR;
      const lat = norm([Math.cos(a), 0, Math.sin(a)]);
      const d = norm(add(add(mul(s.d, Math.cos(rr.Ouverture)), mul(lat, Math.sin(rr.Ouverture))), [0, rr.Port * 0.8, 0]));
      rameaux.push({ p, d, L: rr.LongCm * (0.6 + 0.4 * h(i, k)), a, k: i * 50 + k });
    }
  });
  const parRameau = rr.Brindilles * rr.FeuillesBrin;
  const garde = Math.min(1, FEUILLES_MAX / Math.max(1, rameaux.length * parRameau)) * etat.densite;
  let fruits = 0;
  const fruitsRameau = fr && etat.fruits ? Math.min(gr ? gr.Grappe : 1, FRUITS_MAX / Math.max(1, rameaux.length)) : 0;
  for (const r of rameaux) {
    const bout = add(r.p, mul(r.d, r.L));
    P.tube([r.p, add(r.p, mul(add(r.d, [0, rr.Port * 0.3, 0]), r.L * 0.5)), bout], H / 500, H / 900, M.bois);
    for (let j = 0; j < parRameau; j++) {
      if (h(r.k, j) >= garde) continue;
      const u = 0.25 + 0.75 * h(r.k, 100 + j), p = add(r.p, mul(r.d, r.L * u));
      o.feuille(f, add(p, [0, (h(r.k, 200 + j) - 0.5) * 6, 0]), r.a + (j % 2 ? 1.2 : -1.2) + h(r.k, 300 + j),
        -0.25 + 0.3 * rr.Port, rr.LimbeCm * (0.8 + 0.3 * h(r.k, 400 + j)), r.k + j);
    }
    for (let j = 0; fruitsRameau && j < fruitsRameau && h(r.k, 500 + j) < fruitsRameau / (gr ? gr.Grappe : 1); j++) {
      const p = add(bout, [(j - 0.5) * 2, -(gr ? gr.QueueCm : 1) - fr.RayonCm, 0]);
      o.fruit(fr, p, r.a, r.k + j);
      fruits++;
    }
  }
  return { feuilles: rameaux.length * parRameau * garde, fruits };
}

// LIANE : segments du moteur, feuilles tous les `EspaceCm`, sites de têtes et de
// fruits (une grappe tous les 3 nœuds, comme le prototype), tuteur.
function liane(o, st, l) {
  const { P, M, h, etat } = o, f = l.Organes;
  const segs = versPortrait(st);
  const H = Math.max(...segs.map(s => s.bout[1]));
  P.tube([[4, -2, 2], [4, H + 10, 2]], 0.6, 0.5, M.bois);             // tuteur (support de la vue : treillis, mur)
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

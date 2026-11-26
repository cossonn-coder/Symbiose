// SYMBIOSE — tools/splat/portraits/cone.js (sprint BOIS & ARBRES ⑤)
// Le CÔNE d'un conifère au portrait, MÊME RÈGLE qu'en jeu (PlantRenderer.Sapin.cs, constantes et
// espèces lues dans le C# par table_cs.js — rien n'est recopié) :
//   • tronc = du collet, l'enfant le plus vertical à chaque nœud, tant qu'il monte ;
//   • un étage de `EtageRameaux` rameaux tous les `EtagePasCm`, dès `EtageBasCm` (non élagué) ;
//   • longueur L = R × (cime − y) / cime, R = rayon réel (bout de segment le plus écarté) ;
//   • tout rameau, étage ou non, ramené dans ce cône (au moins `ConeBoutCm` à la cime).
// Repère portrait : y haut (cm), autour du collet. Zéro Math.random : aléa = h(i, j).
//
// 📖 Pédagogie : le moteur donne au sapin une flèche et quelques latéraux courts ; c'est la vue
// qui « habille » le cône (arbitrage B3). Le portrait illustre ce que le jeu montre, donc il
// applique la même règle au même squelette — deux lecteurs, une seule règle.

'use strict';

const { OR } = require('./ports_bas');

const norm = a => { const l = Math.hypot(...a) || 1; return a.map(v => v / l); };
const horiz = p => Math.hypot(p[0], p[2]);

// Tronc dressé : indices dans `segs` (portrait, champ `parent` = indice d'origine).
function tronc(segs) {
  const out = [];
  let s = segs.find(x => x.parent == null || x.parent < 0);
  while (s) {
    out.push(s);
    let suivant = null, meilleur = 0.7;          // au-delà de ~45° de la verticale, plus la flèche
    for (const x of segs) if (x.parent === s.i && x.d[1] > meilleur) { meilleur = x.d[1]; suivant = x; }
    s = suivant;
  }
  return out;
}

// La règle du cône d'un arbre, ou null s'il n'est pas conique.
function cone(segs, esp, regle) {
  if (!regle || !regle.especes.includes(esp)) return null;
  const t = tronc(segs);
  if (!t.length) return null;
  const haut = t[t.length - 1], cime = haut.bout[1];
  if (cime <= regle.EtageBasCm) return null;
  const R = Math.max(...segs.map(s => horiz(s.bout)));
  const permis = y => Math.min(R, Math.max(regle.ConeBoutCm, R * (cime - y) / cime));
  return { tronc: t, cime, R, permis, regle };
}

// Raccourcit un rameau (p, d, L) pour que son bout reste dans le cône.
function ramener(c, r) {
  for (let k = 0; k < 6; k++) {
    const b = [0, 1, 2].map(j => r.p[j] + r.d[j] * r.L);
    if (horiz(b) <= c.permis(b[1]) + 0.5) return;
    r.L *= 0.8;
  }
}

// Les rameaux des étages, au format des rameaux d'arbres.js ({ p, d, L, a, k }).
function etages(c, rr, h) {
  const { EtagePasCm, EtageBasCm, EtageRameaux, EtageCimeMinCm } = c.regle, out = [];
  for (const s of c.tronc) {
    const y0 = s.b[1], y1 = s.bout[1];
    if (y1 <= y0) continue;
    for (let k = Math.max(0, Math.ceil((y0 - EtageBasCm) / EtagePasCm)); ; k++) {
      const y = EtageBasCm + k * EtagePasCm;
      if (y >= y1) break;
      const lon = c.R * (c.cime - y) / c.cime;
      if (lon < EtageCimeMinCm) continue;
      const u = (y - y0) / (y1 - y0), p = s.b.map((v, j) => v + (s.bout[j] - v) * u);
      const tour = 6.283 * h(700 + k, 0);
      for (let i = 0; i < EtageRameaux; i++) {
        const a = tour + 6.283 * (i + 0.35 * h(700 + k, 1 + i)) / EtageRameaux;
        const lat = [Math.cos(a), 0, Math.sin(a)], ouv = rr.Ouverture * (0.9 + 0.2 * h(700 + k, 10 + i));
        const d = norm([lat[0] * Math.sin(ouv), Math.cos(ouv) + rr.Port * 0.8, lat[2] * Math.sin(ouv)]);
        out.push({ p, d, L: lon * (0.85 + 0.25 * h(700 + k, 20 + i)), a: a + OR, k: 90000 + k * 10 + i });
      }
    }
  }
  return out;
}

module.exports = { cone, ramener, etages };

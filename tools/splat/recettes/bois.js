// SYMBIOSE — tools/splat/recettes/bois.js (sprint PRÉCUISSON SPLATS ③)
// Fabrique de TRONÇONS D'ÉCORCE : un cylindre court de diamètre `dCm` et de longueur
// `longCm`, posé de l'attache (origine) vers +X, à poser bout à bout le long d'un
// segment du moteur. Écorce : fissures longitudinales (solides négatifs) au-delà de
// 2 cm, lenticelles en dessous. Paliers où le bois est large seulement (×8 → ×32 :
// largeur vue = épaisseur × 0,39 × 1,5 × zoom, WoodWidthFactor de PlantRenderer.cs).
// Inclinaisons 0 → 90° (un tronc est vertical) ; un segment qui DESCEND se pose à
// l'envers (attache au bout). Axe tassé à l'oblique de la vue (lib/organe.js).
// Usage : require('./bois')(dCm, longCm) — la couture est MESURÉE avant toute
// livraison (tools/splat/couture_bois.js, cf. 00_etat ③).
'use strict';
const { CM, recette, tige } = require('../lib/organe');
module.exports = (dCm, longCm = 8) => recette({
  nom: `bois_d${dCm}`, rayonCm: Math.ceil(Math.hypot(longCm, dCm) + 1),
  lacets: 8, inclinaisons: [0, 30, 60, 90], paliers: [8, 16, 32],
  vue: ['DrawSegments (bois, paliers >= x8)'],
  sculpter(ctx, h) {
    const r = (dCm / 2) * CM, L = longCm * CM, n = Math.max(4, Math.round(3 + 1.2 * dCm));
    tige(ctx, [[0, 0, 0], [L / 2, 0, 0], [L, 0, 0]], r);
    for (let i = 0; i < n; i++) {
      const a = (i + 0.6 * h(1, i)) * (2 * Math.PI / n), ca = Math.cos(a), sa = Math.sin(a);
      if (dCm >= 2) {                       // fissure : sillon qui serpente le long du tronçon
        const pts = [0, 0.33, 0.66, 1].map((t, k) => {
          const b = a + 0.12 * (h(2 + k, i) - 0.5);
          return [L * (t * 1.1 - 0.05), Math.cos(b) * r * 1.02, Math.sin(b) * r * 1.02];
        });
        const e = 0.09 * r * (0.7 + 0.6 * h(6, i));
        ctx.S.tube(pts.map(ctx.P), e, e, ctx.mat(0), { res: Math.min(0.01, e), neg: true });
      } else ctx.S.ball(ctx.P([L * h(7, i), ca * r, sa * r]), [0.12 * r, 0.05 * r, 0.05 * r], ctx.mat(0), { res: 0.003, neg: true });
    }
  }
});

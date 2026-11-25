// SYMBIOSE — tools/splat/recettes/feuille_thym.js (sprint RELIQUATS DES PLANTES ④)
// RAMEAU DE THYM : le « grain » de la masse du buisson (PoserMasse, PlantRenderer.PortBuisson.cs,
// `GrainCm` 1,9 cm = RAYON du disque dessiné) devient un petit rameau ligneux couvert de feuilles minuscules (4-5 mm,
// opposées-décussées, bords enroulés) et terminé par un bouquet de jeunes feuilles.
// Attache = la base du rameau, posée sur le dôme sombre de la masse : des dizaines de
// rameaux dressés vers l'extérieur font le COUSSIN (le portrait raté du sprint (a) montrait
// des feuilles qui flottent ; ici chaque feuille tient à son rameau).
// Longueur 3,6 cm ≈ le DIAMÈTRE de l'ancien grain (1,9 cm laissait le dôme nu, captures ④).
// Rameau dressé de ~55° vers +X (le lacet de la vue le tourne vers l'extérieur du coussin).
'use strict';
const { add, mul, norm, direction, limbe } = require('../lib/limbe');
const { recette, CM } = require('../lib/feuille');

const MOITIE = [[0, 0], [0.15, 0.7], [0.5, 1], [0.85, 0.65], [1, 0]];   // elliptique

module.exports = Object.assign(recette({
  nom: 'feuille_thym', rayonCm: 5, vue: ['FicheBuisson.Grains (thym)'],
  sculpter(ctx, h) {
    const L = 3.6 * CM * (0.9 + 0.2 * h(0, 0)), az = 0.25 * (h(0, 1) - 0.5);
    const axe = norm(direction(az, 0.85 + 0.25 * h(0, 2)));
    const pt = t => add(mul(axe, L * t), [0, -0.12 * L * t * t, 0]);   // le bout s'incurve
    ctx.S.tube([pt(0), pt(0.5), pt(1)].map(ctx.R), 0.09 * CM, 0.04 * CM, ctx.M.organe, { res: 0.003 });
    const sites = [];
    const feuille = (p, a, pen, l) => sites.push(limbe(ctx, {
      base: p, dir: direction(a, pen), long: l, large: l * 0.32, moitie: MOITIE, pli: 0.45, epais: 0.004, res: 0.003
    }));
    for (let n = 0; n < 6; n++) {   // 6 nœuds de 2 feuilles opposées, croisés d'un nœud à l'autre
      const t = 0.12 + 0.15 * n, a = az + (n % 2 ? Math.PI / 2 : 0) + 0.3 * (h(1, n) - 0.5);
      const l = 0.65 * CM * (0.85 + 0.3 * h(2, n));
      for (const s of [0, Math.PI]) feuille(pt(t), a + s, 0.5 + 0.3 * h(3, n), l);
    }
    for (let i = 0; i < 5; i++)   // bouquet du bout : jeunes feuilles serrées, dressées
      feuille(pt(1), az + (2 * Math.PI * i) / 5 + h(4, i), 0.9, 0.5 * CM * (0.8 + 0.4 * h(5, i)));
    return sites;
  }
}), { inclinaisons: [0] });

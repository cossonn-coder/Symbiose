// SYMBIOSE — tools/splat/recettes/panicule_fetuque.js (sprint RELIQUATS DES PLANTES ④)
// PANICULE DE LA FÉTUQUE ROUGE — DessinerFetuque (PlantRenderer.Graminees.cs) : au bout de la
// tige nue, une panicule fine et lâche, quelques rameaux capillaires qui retombent, et des
// épillets roux de ~0,5 cm (l'ancien dessin : 5 points autour du bout, jusqu'à 2,3 cm).
// Une couche. Attache = le sommet de la tige (la tige reste un trait de la vue).
'use strict';
const { CM, recette, petale, tige, norm, add, mul } = require('../lib/organe');
module.exports = recette({
  nom: 'panicule_fetuque', rayonCm: 4, inclinaisons: [0],   // la vue ne pose que l'inclinaison 0
  vue: ['PortPrairie.Fetuque (panicule)'],
  sculpter(ctx, h) {
    const L = 1.4 * CM * (0.85 + 0.3 * h(0, 0));
    const axe = t => [0.15 * L * t * t, L * t, 0];
    tige(ctx, [axe(0), axe(0.5), axe(1)], 0.04 * CM, 0.025 * CM);
    petale(ctx, axe(1), norm([0.1, 1, 0]), 0.55 * CM, 0.16 * CM, 0.08 * CM, [1, 0, 0]);   // épillet terminal
    for (let r = 0; r < 4; r++) {
      const base = axe(0.15 + 0.22 * r), a = r * 2.4 + 0.6 * h(1, r);
      const d = norm([Math.cos(a), 0.25 - 0.9 * h(2, r), Math.sin(a)]);   // rameau qui s'écarte et retombe
      const l = (1.6 - 0.25 * r) * CM * (0.8 + 0.4 * h(3, r));
      const bout = add(base, mul(d, l));
      tige(ctx, [base, add(base, add(mul(d, 0.5 * l), [0, 0.1 * l, 0])), bout], 0.02 * CM, 0.012 * CM);
      for (let e = 0; e < 2; e++) {
        const p = e ? bout : add(base, mul(d, 0.55 * l));
        petale(ctx, p, norm(add(d, [0, -0.4, 0])), 0.5 * CM * (0.85 + 0.3 * h(4, r * 2 + e)), 0.16 * CM, 0.08 * CM, [0, 1, 0]);
      }
    }
  }
});

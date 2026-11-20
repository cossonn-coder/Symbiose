// SYMBIOSE — tools/splat/lib/trous.js (sprint PRÉCUISSON SPLATS ②)
// Les TROUS d'une feuille (décision D5) : précuits en degrés, comme des variantes.
//   • `morsure` (ravageurs) : le BORD grignoté — bouchées rondes centrées sur le
//     bord du limbe ; degré 1 = 1 bouchée, 2 = 3 bouchées.
//   • `grele` (criblage) : petits trous ronds DANS le limbe ; degré 1 = 3 trous,
//     2 = 7 trous. (Les encoches de grêle au bord de la vue, Froid.cs, sont lues
//     comme des morsures : même forme, cuite une seule fois.)
// Les COULEURS (nécrose, taches, givre) ne sont pas cuites : la vue les peint.
//
// Un trou = un solide NÉGATIF (`{ neg: true }` d'ink-studio) qui creuse tout ce
// qu'il traverse : on le fait plus épais que le limbe, aplati dans son plan.
// Les sites viennent de lib/limbe.js (un par limbe ou foliole) ; le tirage
// (quel site, où) est au hash K.hash(graine, …) : même trou à chaque cuisson.
//
// 📖 Pédagogie : la cuisson ne connaît pas l'état de santé — elle prépare des
// « degrés » ; c'est la vue qui choisira le degré selon les dégâts lus (④),
// comme un sprite d'animation choisi par un état.

'use strict';

const { add, mul, largeurA } = require('./limbe');

const TROUS = [null, { type: 'morsure', degre: 1 }, { type: 'morsure', degre: 2 },
  { type: 'grele', degre: 1 }, { type: 'grele', degre: 2 }];
const NOMBRE = { morsure: [0, 1, 3], grele: [0, 3, 7] };

// Creuse `trou` ({ type, degre }) dans les `sites` (sites de limbe.js).
function percer(ctx, trou, sites, graine) {
  if (!trou || !sites.length) return;
  const { S, K, M } = ctx;
  const h = (i, j) => K.hash(5000 + graine + (trou.type === 'grele' ? 97 : 0), i, j);
  // Les grands limbes d'abord : une morsure se voit sur une foliole, pas sur un pétiole.
  const tri = sites.map((s, i) => [s.long * s.large, i]).sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  const utiles = tri.slice(0, Math.max(1, Math.ceil(tri.length * 0.6))).map(([, i]) => sites[i]);
  const n = NOMBRE[trou.type][trou.degre];
  for (let k = 0; k < n; k++) {
    const s = utiles[Math.floor(h(k, 0) * utiles.length) % utiles.length];
    const t = 0.3 + 0.55 * h(k, 1), cote = h(k, 2) < 0.5 ? 1 : -1;
    const w = largeurA(s.moitie, t) * s.large;
    let centre, r;
    if (trou.type === 'morsure') {
      // Bouchée à l'échelle de la feuille (pas de sa seule largeur : un lierre large
      // perdrait tout), jamais sous 4,5 mm (un ruban se grignote aussi) ; centrée
      // un peu EN DEDANS du bord pour mordre même là où le contour est échancré.
      r = Math.max(0.045, Math.min(s.large, s.long * 0.4) * (0.3 + 0.1 * trou.degre)) * (0.8 + 0.4 * h(k, 3));
      centre = add(s.c, add(mul(s.U, t * s.long), mul(s.V, cote * Math.max(0, w - r * 0.35))));
    } else {
      r = Math.min(0.05, Math.max(0.018, s.large * 0.11)) * (0.8 + 0.4 * h(k, 3));   // grêlon : ≤ 1 cm
      centre = add(s.c, add(mul(s.U, t * s.long), mul(s.V, cote * w * 0.55 * h(k, 4))));
    }
    // Épaisseur du perçage : le limbe est plié en V (lib/limbe.js), son bord monte
    // de ~pli × largeur au-dessus du plan du site — le trou doit le traverser.
    S.ball(centre, [r, r, 0.12 + s.large * 0.4], M.organe, { res: 0.015, neg: true, ax: [s.U, s.V, s.W] });
  }
}

module.exports = { TROUS, percer };

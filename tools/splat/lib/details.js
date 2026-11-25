// SYMBIOSE — tools/splat/lib/details.js (sprint RELIQUATS DES PLANTES ③)
// Les DÉTAILS des feuilles et des organes, cuits en SUR-COUCHES (consigne E10 de Nico :
// « tous les détails des feuilles présents quand on zoome, beaux à chaque palier »).
//
// Avant ce tronçon, la vue traçait ces détails en vecteurs (nervures ×16, duvet de la
// molène, gouttes du drosera, éclat du basilic, revers de l'armoise, poils ×32, pruine,
// étamines…) ; dès qu'une feuille devenait une pièce splat, ils disparaissaient.
//
// PRINCIPE : une recette (feuille_ovale…) est sculptée comme d'habitude, puis ce module
// AJOUTE ses détails dans le même monde, chacun dans le matériau d'une couche à lui
// (couches 1, 2… après celles de la recette). cuire.js --details photographie ce monde
// sous les MÊMES vues que la pièce de base, et n'extrait QUE les couches de détail →
// `<recette>_details.json` + planches. La pièce de base n'est jamais recuite (ses octets
// ne bougent pas, D2) ; la vue pose la pièce, puis par-dessus la sur-couche de chaque
// détail que porte l'espèce, avec sa palette, à partir de son palier (table unique de
// la vue, PlantRenderer.SplatsDetails.cs).
//
// Occlusion juste : le détail est photographié AVEC la feuille ; un poil caché sous le
// limbe n'est le splat propriétaire d'aucun pixel, il n'apparaît pas.
//
// SITES : chaque recette rend les sites de ses limbes (lib/limbe.js : repère U le long,
// V latéral, W normale, demi-largeur, contour, pli, épaisseur) — les mêmes qui servent
// aux trous D5 — ou, pour un organe, son centre et son rayon (fruit, corolle).
//
// 📖 Pédagogie : c'est un calque de dessin. La feuille est le fond, chaque détail un
// calque transparent ajusté dessus au pixel près (même caméra, même point d'attache) ;
// on allume les calques qu'il faut, espèce par espèce, sans redessiner le fond.
//
// Déterministe : tout aléa vient de K.hash(2000 + variante, i, j) — un flux distinct de
// celui des recettes (1000 + variante), la sculpture de la feuille n'en dépend pas.

'use strict';

const { add, mul, norm, cross, tourner, largeurA } = require('./limbe');

const CM = 0.1;   // 1 unité ink = 10 cm

// recette → { couches: [détails, dans l'ordre des couches], paliers: [cuits] }.
// Paliers cuits = un cran SOUS le seuil de la vue ancienne (on choisit le seuil en
// regardant la planche de contrôle) jusqu'à ×32. Inventaire : 00_etat.md ③.
const DETAILS = {
  feuille_ovale: { couches: ['nervures', 'duvet', 'poils', 'eclat', 'pruine'], paliers: [4, 8, 16, 32] },
  feuille_scie: { couches: ['nervures', 'revers'], paliers: [4, 8, 16, 32] },
  feuille_scie_gaufree: { couches: ['nervures', 'poils'], paliers: [8, 16, 32] },
  feuille_lanceolee: { couches: ['nervures'], paliers: [8, 16, 32] },
  feuille_lanceolee_gaufree: { couches: ['nervures', 'poils'], paliers: [8, 16, 32] },
  feuille_dentee: { couches: ['nervures'], paliers: [8, 16, 32] },
  feuille_spatule: { couches: ['nervures'], paliers: [8, 16, 32] },
  feuille_lobee: { couches: ['nervures', 'revers', 'poils'], paliers: [4, 8, 16, 32] },
  feuille_coeur: { couches: ['nervures', 'poils'], paliers: [8, 16, 32] },
  feuille_lierre: { couches: ['nervures'], paliers: [4, 8, 16, 32], palmee: true },
  feuille_paume: { couches: ['nervures', 'poils'], paliers: [8, 16, 32], palmee: true },
  feuille_composee: { couches: ['nervures', 'poils'], paliers: [8, 16, 32] },
  feuille_triade: { couches: ['nervures'], paliers: [8, 16, 32] },
  feuille_cuillere: { couches: ['glandes', 'gouttes'], paliers: [8, 16, 32] },
  feuille_ruban: { couches: ['pruine'], paliers: [16, 32] },
  fruit_globe: { couches: ['pruine'], paliers: [16, 32] },
  tete_corolle: { couches: ['etamines'], paliers: [8, 16, 32] },
};

// --- Géométrie d'un site de limbe ----------------------------------------------------

// Point du DESSUS du limbe : x ∈ [0, 1] le long, y ∈ [-1, 1] en part de la demi-largeur
// locale, `h` = hauteur au-dessus du plan moyen en part de l'épaisseur. Rend le point,
// la normale de la moitié (relevée de `pli`) et sa direction latérale vers le bord.
function surLimbe(s, x, y, h = 0.6) {
  const sgn = y >= 0 ? 1 : -1, pli = s.pli || 0, epais = s.epais || 0.022;
  const Vs = mul(s.V, sgn), Vh = tourner(Vs, s.W, pli), Wh = tourner(s.W, mul(Vs, -1), pli);
  const p = add(s.c, add(mul(s.U, x * s.long), add(mul(Vh, Math.abs(y) * largeurA(s.moitie, x) * s.large), mul(Wh, epais * h))));
  return { p, n: Wh, lat: Vh };
}

// Abscisses des pointes de lobes (maxima locaux du contour) : ≥ 2 → limbe lobé.
function lobes(moitie) {
  const res = [];
  for (let i = 1; i + 1 < moitie.length; i++)
    if (moitie[i][1] > moitie[i - 1][1] && moitie[i][1] >= moitie[i + 1][1] && moitie[i][0] > 0.05 && moitie[i][0] < 0.97)
      res.push(moitie[i]);
  return res;
}

// Tube posé sur le dessus du limbe, d'un point (x, y) à l'autre, rayon en cm.
function veine(ctx, s, a, b, rCm, k) {
  const pa = surLimbe(s, a[0], a[1], 0.7).p, pb = surLimbe(s, b[0], b[1], 0.7).p;
  const m = surLimbe(s, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.8).p;
  ctx.S.tube([pa, m, pb], rCm * CM, rCm * CM * 0.7, ctx.couche(k), { res: Math.min(0.006, rCm * CM) });
}

// --- Détails de limbe (un sculpteur par détail : ctx, site, i du site, h, couche) -----

const LIMBE = {
  // Nervure médiane + secondaires : vers les lobes si le limbe en a (armoise, lierre,
  // courgette), sinon 5 paires pennées. `palmee` : les nervures partent toutes de la base.
  nervures(ctx, s, i, h, k) {
    const r = Math.max(0.05, Math.min(0.11, s.long / CM * 0.009));   // ∝ taille du limbe
    veine(ctx, s, [0.03, 0], [0.93, 0], r, k);
    const L = lobes(s.moitie);
    if (L.length >= 2)
      for (const [x, y] of L) for (const sg of [1, -1])
        veine(ctx, s, [ctx.palmee ? 0.04 : x * 0.55, 0], [x, sg * y * 0.85], r * 0.7, k);
    else
      for (let j = 1; j <= 5; j++) {
        const t = 0.1 + (0.68 * j) / 5;
        for (const sg of [1, -1]) veine(ctx, s, [t, 0], [t + 0.16, sg * 0.8], r * 0.6, k);
      }
  },
  // Duvet (molène, bourrache) : grain clair posé à plat sur le limbe.
  duvet(ctx, s, i, h, k) {
    for (let j = 0; j < 16; j++) {
      const { p, n, lat } = surLimbe(s, 0.12 + 0.8 * h(i, j), (h(i, 40 + j) - 0.5) * 1.7, 0.7);
      ctx.S.ball(p, [0.16 * CM, 0.05 * CM, 0.16 * CM], ctx.couche(k), { res: 0.006, ax: repere(lat, n) });
    }
  },
  // Poils / soies : courtes soies dressées sur le limbe et cils au bord, vers l'extérieur.
  poils(ctx, s, i, h, k) {
    for (let j = 0; j < 22; j++) {
      const { p, n, lat } = surLimbe(s, 0.1 + 0.82 * h(i, 80 + j), (h(i, 120 + j) - 0.5) * 1.8, 0.6);
      soie(ctx, p, norm(add(mul(n, 0.8), mul(lat, 0.5))), 0.3, k);
    }
    for (let j = 0; j < 18; j++) {
      const x = 0.08 + 0.86 * (j + 0.5) / 18, { p, n, lat } = surLimbe(s, x, j % 2 ? 1 : -1, 0.2);
      soie(ctx, p, norm(add(lat, mul(n, 0.4))), 0.28, k);
    }
  },
  // Éclat (basilic, poivron) : un reflet allongé sur une moitié, à plat sur le limbe.
  eclat(ctx, s, i, h, k) {
    const { p, n } = surLimbe(s, 0.47, 0.4, 0.55);
    ctx.S.ball(p, [s.long * 0.13, 0.04 * CM, s.long * 0.035 + 0.1 * CM], ctx.couche(k),
      { res: 0.006, ax: repere(s.U, n) });
  },
  // Revers (armoise, framboisier) : le DESSOUS clair, un coussin collé sous chaque moitié ;
  // il n'est propriétaire d'un pixel que là où la caméra voit la face inférieure (bord
  // relevé, feuille retournée) ou dépasse d'un cheveu à la marge.
  revers(ctx, s, i, h, k) {
    const epais = s.epais || 0.022;
    for (const sgn of [1, -1]) {
      const Vs = mul(s.V, sgn), Vh = tourner(Vs, s.W, s.pli || 0), Wh = tourner(s.W, mul(Vs, -1), s.pli || 0);
      const boucle = s.moitie.map(([x, y]) => [x * s.long, y * s.large * 1.02]);
      ctx.S.puff([boucle], add(s.c, mul(Wh, -epais * 0.4)), epais * 0.6, ctx.couche(k), { res: 0.02, ax: [s.U, Vh, Wh] });
    }
  },
  // Pruine (ail) : semis de points cireux pâles sur le limbe.
  pruine(ctx, s, i, h, k) {
    for (let j = 0; j < 14; j++) {
      const { p, n, lat } = surLimbe(s, 0.05 + 0.9 * h(i, 200 + j), (h(i, 240 + j) - 0.5) * 1.8, 0.65);
      ctx.S.ball(p, [0.07 * CM, 0.03 * CM, 0.07 * CM], ctx.couche(k), { res: 0.005, ax: repere(lat, n) });
    }
  },
  // Glandes du drosera : tentacules au bord du disque et sur le dessus.
  glandes(ctx, s, i, h, k) { tentacules(ctx, s, h, (p, d) => soie(ctx, p, d, 0.3, k, 0.035)); },
  // Gouttes de glu : une perle au bout de chaque tentacule.
  gouttes(ctx, s, i, h, k) {
    tentacules(ctx, s, h, (p, d) => ctx.S.ball(add(p, mul(d, 0.32 * CM)), 0.07 * CM, ctx.couche(k), { res: 0.005 }));
  },
};

// Soie : tube effilé de `lCm` depuis `p` selon `d`.
function soie(ctx, p, d, lCm, k, rCm = 0.03) {
  ctx.S.tube([p, add(p, mul(d, lCm * CM))], rCm * CM, rCm * CM * 0.45, ctx.couche(k), { res: 0.004 });
}

// 14 tentacules au bord du disque (vers l'extérieur et le haut) + 5 sur le dessus.
function tentacules(ctx, s, h, poser) {
  for (let j = 0; j < 14; j++) {
    const x = 0.06 + 0.88 * (j >> 1) / 6.5, { p, n, lat } = surLimbe(s, x, j % 2 ? 0.95 : -0.95, 0.3);
    poser(p, norm(add(mul(lat, 0.7), mul(n, 0.7))));
  }
  for (let j = 0; j < 5; j++) {
    const { p, n, lat } = surLimbe(s, 0.25 + 0.5 * h(9, j), (h(9, 10 + j) - 0.5), 0.6);
    poser(p, norm(add(n, mul(lat, 0.3))));
  }
}

function repere(x, haut) {
  const X = norm(x), W = norm(cross(X, haut)), Y = cross(W, X);
  return [X, Y, W];
}

// --- Détails d'organe (site = { c, r, ry?, haut? } en coordonnées finales) --------------

const ORGANE = {
  // Pruine du fruit (myrtille, prunelle) : voile de points pâles sur l'hémisphère haut.
  pruine(ctx, s, i, h, k) {
    for (let j = 0; j < 26; j++) {
      const a = 2 * Math.PI * h(i, j), e = Math.asin(h(i, 30 + j) * 0.95);   // élévation ≥ 0
      const d = [Math.cos(a) * Math.cos(e), Math.sin(e) * (s.ry / s.r), Math.sin(a) * Math.cos(e)];
      ctx.S.ball(add(s.c, mul(d, s.r * 1.02)), s.r * 0.05, ctx.couche(k), { res: 0.004 });
    }
  },
  // Étamines de la corolle : filets qui rayonnent du cœur, anthère au bout.
  etamines(ctx, s, i, h, k) {
    const a0 = [1, 0, 0], u = norm(cross(s.haut, Math.abs(s.haut[0]) < 0.9 ? a0 : [0, 0, 1])), w = cross(s.haut, u);
    for (let j = 0; j < 10; j++) {
      const a = (2 * Math.PI * (j + 0.3 * h(i, j))) / 10;
      const d = norm(add(add(mul(u, Math.cos(a)), mul(w, Math.sin(a))), mul(s.haut, 0.6)));
      const bout = add(s.c, mul(d, s.r * 0.55));
      ctx.S.tube([s.c, bout], 0.025 * CM, 0.02 * CM, ctx.couche(k), { res: 0.004 });
      ctx.S.ball(bout, 0.065 * CM, ctx.couche(k), { res: 0.004 });
    }
  },
};

// Ajoute au monde les détails de `recette` : `sites` rendus par sa sculpture, `base` =
// nombre de couches de la recette (la 1ʳᵉ couche de détail vient après).
function sculpter(ctx, recette, sites, base) {
  const d = DETAILS[recette.nom];
  if (!d || !sites) return;
  const h = (i, j) => ctx.K.hash(2000 + ctx.variante, i, j);
  const c = { ...ctx, palmee: !!d.palmee, couche: k => ctx.M.couches[base + k] };
  const table = sites[0] && sites[0].U ? LIMBE : ORGANE;
  d.couches.forEach((nom, k) => sites.forEach((s, i) => table[nom](c, s, i, h, k)));
}

module.exports = { DETAILS, sculpter, surLimbe, lobes };

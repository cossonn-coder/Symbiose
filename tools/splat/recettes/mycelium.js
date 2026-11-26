// SYMBIOSE — tools/splat/recettes/mycelium.js (sprint LISIÈRE & CHARGEMENT ④, décision L3)
// La SCÈNE de l'écran de chargement : une coupe de sol vue de côté. À gauche une SPORE ;
// ses hyphes s'arborisent dans la terre, attirés par la racine d'une PLANTULE à droite ;
// au contact, elles s'enroulent autour de la racine (MANTEAU mycorhizien) ; à la fin, un
// petit CARPOPHORE (laccaire) perce la litière. Cuite par `tools/splat/cuire_mycelium.js`.
//
// Chaque splat du mycélium porte un ÂGE ∈ [0, 1] (option `born` d'ink-studio : le moment
// où le splat apparaît) ; la vue révèle les pixels d'âge ≤ progression du chargement. Le
// décor (spore, litière, plantule, racine) n'a pas d'âge : il est là dès la 1ʳᵉ image.
//
// 📖 Pédagogie (biologie) : une hyphe ne pousse QUE par sa pointe (croissance apicale) ;
// l'âge d'un point du réseau est donc sa distance à la spore le long des hyphes, divisée
// par la vitesse de pousse. Les racines exsudent des sucres et des signaux (strigolactones)
// qui ATTIRENT les hyphes : la pointe se courbe vers la racine d'autant plus qu'elle en est
// proche (chimiotropisme). Au contact, le champignon gaine la racine : c'est la mycorhize
// (« champignon-racine »), l'échange sucres ↔ eau et phosphore — la symbiose du titre.
//
// Contrat : `scene(S, M, h)` sculpte dans le sculpteur ink S (repère : x à droite, y en
// haut, z vers l'œil ; 1 unité = 30 px de l'image 480×270), matériaux M (palette pleine,
// clés de COULEURS), h(i, j) ∈ [0, 1) déterministe. Rend { noeuds, contact } (mesures).
'use strict';

const COULEURS = {
  hyphe: '#ece4c8', manteau: '#f6f0dc', spore: '#4a2e1c', racine: '#c9a273',
  tige: '#6e9a3c', cotyledon: '#8fbf4c', litiere: '#5c3f24', feuille_morte: '#8a5e30',
  pied: '#e2b27c', chapeau: '#c0602e'
};

const SOL = 1.55;                       // y de la surface (litière)
const SPORE = [-6.2, -1.6];
const RACINE = [[4.1, SOL], [4.2, 0.6], [4.05, -0.5], [4.25, -1.6], [4.15, -2.9]];
const PAS = 0.11;                       // pas de pousse d'une pointe (unités)
const AGE_CONTACT = 0.74, AGE_MANTEAU = 0.88, AGE_MAX_RESEAU = 0.86;
const BORNES = { x0: -7.7, x1: 7.6, y0: -4.2, y1: SOL - 0.12 };

// Point le plus proche d'une polyligne → { p, s (abscisse), d }.
function proche(pl, x, y) {
  let best = { d: 1e9, p: pl[0], s: 0 }, cum = 0;
  for (let i = 1; i < pl.length; i++) {
    const [ax, ay] = pl[i - 1], [bx, by] = pl[i], dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy;
    const t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / l2));
    const px = ax + dx * t, py = ay + dy * t, d = Math.hypot(x - px, y - py), l = Math.sqrt(l2);
    if (d < best.d) best = { d, p: [px, py], s: cum + t * l };
    cum += l;
  }
  return best;
}

// RÉSEAU : pousse SYNCHRONE (un pas par tour pour toutes les pointes) → la distance à la
// spore = tour × PAS, le front avance d'un même pas partout (la vraie forme d'une colonie).
function reseau(h) {
  const noeuds = [{ x: SPORE[0], y: SPORE[1], d: 0, gen: 0 }];
  const occupe = new Map(), cle = (x, y) => `${Math.floor(x / 0.09)},${Math.floor(y / 0.09)}`;
  let pointes = [0, 1, 2].map(k => ({ n: 0, th: -0.5 + k * 0.9 + (h(1, k) - 0.5) * 0.4, gen: 0, br: k }));
  let contact = null, tour = 0, brSuivant = 3;
  while (pointes.length && tour < 400) {
    tour++;
    const suivantes = [];
    for (const [i, t] of pointes.entries()) {
      const a = noeuds[t.n];
      const r = proche(RACINE, a.x, a.y);
      const attrait = 0.22 * Math.exp(-r.d / 2.2);                    // chimiotropisme
      const vise = Math.atan2(r.p[1] - a.y, r.p[0] - a.x);
      let dth = Math.atan2(Math.sin(vise - t.th), Math.cos(vise - t.th));
      let th = t.th + (h(10 + tour, i * 7 + t.br) - 0.5) * 0.5 + dth * attrait;
      const x = a.x + PAS * Math.cos(th), y = a.y + PAS * Math.sin(th);
      if (x < BORNES.x0 || x > BORNES.x1 || y < BORNES.y0 || y > BORNES.y1) continue;
      const k = cle(x, y);
      if (occupe.has(k) && occupe.get(k) !== t.br) continue;           // anastomose : la pointe s'arrête
      const n = noeuds.push({ x, y, d: a.d + PAS, gen: t.gen, parent: t.n, br: t.br }) - 1;
      occupe.set(k, t.br);
      if (!contact && proche(RACINE, x, y).d < 0.12) { contact = { n, d: a.d + PAS, p: [x, y] }; continue; }
      suivantes.push({ n, th, gen: t.gen, br: t.br });
      // Ramification latérale, plus rare loin de la spore (le réseau se densifie à l'arrière).
      if (suivantes.length < 70 && h(30 + tour, i * 13 + t.br) < 0.075) {
        const cote = h(31 + tour, t.br) < 0.5 ? -1 : 1;
        suivantes.push({ n, th: th + cote * (0.6 + 0.5 * h(32 + tour, t.br)), gen: t.gen + 1, br: brSuivant++ });
      }
    }
    pointes = suivantes;
    if (contact && tour * PAS > contact.d * AGE_MAX_RESEAU / AGE_CONTACT) break;
  }
  if (!contact) throw new Error('le réseau n\'a pas atteint la racine : régler PAS / attrait');
  for (const nd of noeuds) nd.age = Math.min(AGE_MAX_RESEAU, AGE_CONTACT * nd.d / contact.d);
  return { noeuds, contact };
}

// Hyphes = une polyligne par branche, âge linéaire en abscisse (`along` d'ink = 0 → 1).
function hyphes(S, M, noeuds) {
  const parBranche = new Map();
  for (let i = 1; i < noeuds.length; i++) {
    const nd = noeuds[i];
    if (!parBranche.has(nd.br)) parBranche.set(nd.br, [noeuds[nd.parent]]);
    parBranche.get(nd.br).push(nd);
  }
  for (const chaine of parBranche.values()) {
    if (chaine.length < 2) continue;
    const a0 = chaine[0].age, a1 = chaine[chaine.length - 1].age, g = chaine[1].gen;
    const r = g === 0 ? 0.026 : g === 1 ? 0.021 : 0.017;
    S.tube(chaine.map(nd => [nd.x, nd.y, 0.1]), r, r * 0.8, M.hyphe,
      { res: 0.011, born: (x, y, z, along) => a0 + (a1 - a0) * along });
  }
}

// Plantule de chêne : racine pivot + 4 radicelles, tigelle, deux cotylédons et une feuille.
function plantule(S, M, h) {
  S.tube(RACINE.map(([x, y]) => [x, y, 0]), 0.075, 0.03, M.racine, { res: 0.015 });
  for (let k = 0; k < 4; k++) {
    const c = k % 2 ? -1 : 1, [x, y] = RACINE[k + 1];
    S.tube([[x, y, 0], [x + c * 0.5, y - 0.25, 0], [x + c * (0.9 + 0.3 * h(40, k)), y - 0.65, 0]], 0.03, 0.014, M.racine, { res: 0.012 });
  }
  S.tube([[4.1, SOL, 0], [4.05, SOL + 0.7, 0], [4.12, SOL + 1.3, 0]], 0.05, 0.04, M.tige, { res: 0.015 });
  S.ball([3.75, SOL + 0.2, 0.15], [0.28, 0.16, 0.2], M.cotyledon, { res: 0.015 });
  S.ball([4.45, SOL + 0.2, 0.15], [0.28, 0.16, 0.2], M.cotyledon, { res: 0.015 });
  S.ball([4.4, SOL + 1.35, 0.05], [0.42, 0.13, 0.22], M.tige, { res: 0.015 });
  S.ball([3.85, SOL + 1.1, 0.05], [0.34, 0.11, 0.2], M.tige, { res: 0.015 });
}

// Litière : brindilles et feuilles mortes à plat le long de la surface, et la spore.
function decor(S, M, h) {
  for (let k = 0; k < 46; k++) {
    const x = -7.8 + 15.6 * (k + h(50, k)) / 46, y = SOL + (h(51, k) - 0.4) * 0.12;
    if (h(52, k) < 0.55) S.ball([x, y, 0], [0.18 + 0.12 * h(53, k), 0.05, 0.2], k % 3 ? M.litiere : M.feuille_morte, { res: 0.02 });
    else S.tube([[x - 0.25, y, 0], [x + 0.25, y + (h(54, k) - 0.5) * 0.1, 0]], 0.025, 0.02, M.litiere, { res: 0.015 });
  }
  S.ball([SPORE[0], SPORE[1], 0.12], [0.13, 0.1, 0.1], M.spore, { res: 0.012 });
}

// Manteau : deux hyphes en hélice autour du pivot, du point de contact vers les deux bouts.
function manteau(S, M, contact) {
  const c = proche(RACINE, contact.p[0], contact.p[1]);
  let total = 0;
  for (let i = 1; i < RACINE.length; i++) total += Math.hypot(RACINE[i][0] - RACINE[i - 1][0], RACINE[i][1] - RACINE[i - 1][1]);
  const loin = Math.max(c.s, total - c.s);
  for (const phase of [0, Math.PI]) {
    const pts = [];
    for (let s = 0.05; s <= total - 0.05; s += 0.03) {
      let acc = 0, i = 1;
      for (; i < RACINE.length - 1; i++) {
        const l = Math.hypot(RACINE[i][0] - RACINE[i - 1][0], RACINE[i][1] - RACINE[i - 1][1]);
        if (acc + l >= s) break;
        acc += l;
      }
      const [ax, ay] = RACINE[i - 1], [bx, by] = RACINE[i], l = Math.hypot(bx - ax, by - ay), t = (s - acc) / l;
      const rr = 0.075 - 0.045 * s / total + 0.012, w = s * 9 + phase;
      pts.push([ax + (bx - ax) * t + rr * Math.cos(w) * (-(by - ay) / l), ay + (by - ay) * t, rr * Math.sin(w) + 0.02]);
    }
    const ages = pts.map((_, k) => AGE_CONTACT + (AGE_MANTEAU - AGE_CONTACT) * Math.abs(0.05 + k * 0.03 - c.s) / loin);
    // Âge au point le plus proche de la polyligne (l'hélice monte ET descend du contact).
    S.tube(pts, 0.016, 0.016, M.manteau, { res: 0.01, born: (x, y) => {
      let bk = 0, bd = 1e9;
      for (let k = 0; k < pts.length; k++) { const d = (pts[k][0] - x) ** 2 + (pts[k][1] - y) ** 2; if (d < bd) { bd = d; bk = k; } }
      return ages[bk];
    } });
  }
}

// Carpophore : primordium sur l'hyphe la plus proche de la surface, près de la plantule ;
// le pied monte (âge ∝ hauteur), le chapeau s'ouvre en dernier.
function carpophore(S, M, noeuds) {
  let base = null;
  for (const nd of noeuds) if (nd.x > 1.2 && nd.x < 3.4 && (!base || nd.y > base.y)) base = nd;
  if (!base) base = { x: 2.6, y: SOL - 0.2, age: 0.8 };
  const x = base.x, y0 = base.y, haut = SOL + 0.75, a0 = 0.88;
  S.tube([[x, y0, 0.1], [x, SOL, 0.1]], 0.02, 0.03, M.hyphe, { res: 0.01, born: (_x, y) => a0 + 0.02 * (y - y0) / (SOL - y0) });
  S.tube([[x, SOL - 0.05, 0.12], [x + 0.03, SOL + 0.4, 0.12], [x + 0.02, haut, 0.12]], 0.075, 0.06, M.pied,
    { res: 0.012, born: (_x, y) => 0.9 + 0.06 * Math.max(0, y - SOL) / (haut - SOL) });
  S.ball([x + 0.02, haut + 0.06, 0.12], [0.34, 0.13, 0.3], M.chapeau,
    { res: 0.012, born: (xx) => 0.96 + 0.04 * Math.min(1, Math.abs(xx - x) / 0.34) });
  return { x, y: haut };
}

// La scène entière. `avecMycelium` = false → le FOND seul (décor sans âge), rendu à part
// pour que la vue montre la racine nue sous une hyphe pas encore née.
function scene(S, M, h, avecMycelium = true) {
  decor(S, M, h);
  plantule(S, M, h);
  const { noeuds, contact } = reseau(h);
  if (!avecMycelium) return { noeuds, contact };
  hyphes(S, M, noeuds);
  manteau(S, M, contact);
  const champi = carpophore(S, M, noeuds);
  return { noeuds, contact, champi };
}

module.exports = { COULEURS, scene, SOL };

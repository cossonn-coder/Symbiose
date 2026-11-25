// SYMBIOSE — tools/splat/portraits/ports_hauts.js (sprint PRÉCUISSON SPLATS ⑥)
// Les ports HAUTS d'une plante entière, pour son portrait : TIGE (tournesol, ortie,
// basilic…), CHAUME (blé, seigle, pâturin, bambou ; dactyle et fétuque via
// fichePrairie), BUISSON (thym, lavande, myrtille, framboisier), VOLUBILE (haricot).
// Même lecture de la ligne de l'espèce que ports_bas.js (mêmes noms de champs que
// les records FicheTige / FicheChaume / FicheBuisson de la vue).
//
// Repère : centimètres, Y en haut, collet en (0, 0, 0). Zéro Math.random.
//
// 📖 Pédagogie : un AXE est une courbe paramétrée par t ∈ [0, 1] (pied → sommet) ;
// feuilles, rameaux et têtes s'y posent à un t donné. C'est la même idée que la
// vue (`PointAxe`), sans sa projection : on reste en 3D.

'use strict';

const { OR, dirA, polaire, add, lerp } = require('./ports_bas');

// Un axe : pied → sommet, légèrement courbé (s'écarte en montant de `evase`).
function axe(pied, sommet) {
  const at = t => [lerp(pied[0], sommet[0], t * t), lerp(pied[1], sommet[1], t), lerp(pied[2], sommet[2], t * t)];
  return { at, pts: [0, 0.25, 0.5, 0.75, 1].map(at) };
}

// TIGE : `Axes` tiges depuis le pied, feuilles aux nœuds (paires ou alternes),
// rameaux, têtes au sommet et aux aisselles du haut.
function tige(o, f) {
  const { P, M, h, E } = o, t = f.Tige, R = f.RayonCm * E, H = f.HautFeuillesCm * E;
  const rTige = Math.max(0.15, f.EpaisseurTigeCm * 0.5 * Math.sqrt(E));
  for (let i = 0; i < t.Axes; i++) {
    const a0 = i * OR + h(i, 1), pied = polaire(t.EcartPied * R, a0);
    const A = axe(pied, polaire(t.EcartPied * R + t.Evase * R, a0, H * (i ? 0.8 + 0.2 * h(i, 2) : 1)));
    P.tube(A.pts, rTige, rTige * 0.5, M.tige);
    const n = f.Feuilles;
    for (let j = 0; j < n; j++) {
      const u = t.BasNu + (1 - t.BasNu - t.HautNu) * (j + 0.5) / n, p = A.at(u);
      const long = lerp(t.FeuilleBasCm, t.FeuilleHautCm, u) * Math.sqrt(E);
      const a = t.Opposees ? j * Math.PI / 2 + a0 : j * OR + a0, m = 0.35 + 1.4 * t.Penche;
      if (h(j, 3 + i) < o.etat.densite || j === n - 1) o.feuille(f, p, a, m, long, i * 40 + j * 2);
      if (t.Opposees && h(j, 13 + i) < o.etat.densite) o.feuille(f, p, a + Math.PI, m, long, i * 40 + j * 2 + 1);
      if (j >= n - t.TetesAisselle && j < n - 1) o.tete(f, add(p, dirA(a + 1.2, 0.3).map(v => v * 3 * E)), a, 100 + i * 10 + j);
    }
    for (let r = 0; r < t.Rameaux; r++) {           // rameaux : de RameauDes au sommet
      const u = lerp(t.RameauDes, 0.92, (r + 0.5) / t.Rameaux), p = A.at(u), a = r * OR + a0 + 1;
      const L = t.RameauLong * R * lerp(1, t.RameauFin, u);
      const d = dirA(a, Math.atan(t.RameauMonte)), bout = add(p, d.map(v => v * L));
      P.tube([p, add(p, d.map(v => v * L * 0.5)), bout], rTige * 0.6, rTige * 0.3, M.tige);
      for (let k = 0; k < t.FeuillesRameau; k++)
        o.feuille(f, add(p, d.map(v => v * L * (k + 0.6) / (t.FeuillesRameau + 0.4))), a + (k % 2 ? 1.3 : -1.3), 0.3,
          lerp(t.FeuilleBasCm, t.FeuilleHautCm, 0.7) * Math.sqrt(E), 200 + r * 9 + k);
      o.tete(f, bout, a, 300 + i * 20 + r);
    }
    const sommet = A.at(1);
    if (t.EpiCm > 0 && o.etat.fleurs) P.tube([sommet, add(sommet, [0, t.EpiCm * 0.4 * E, 0])], rTige * 0.4, rTige * 0.3, M.tige);
    o.tete(f, t.EpiCm > 0 ? add(sommet, [0, t.EpiCm * 0.4 * E, 0]) : sommet, a0, 400 + i);
  }
}

// CHAUME : `Brins` droits, `Rubans` feuilles en lanière à la base, épi ou panicule ;
// bambou : nœuds et panaches de 3 feuilles.
function chaume(o, f) {
  const { P, M, h, E } = o, c = f.Chaume, R = f.RayonCm * E, H = f.HautFeuillesCm * E;
  const rBrin = Math.max(0.12, f.EpaisseurTigeCm * 0.5 * Math.sqrt(E));
  const brins = Math.max(1, Math.round(c.Brins * (o.etat.nom === 'jeune' ? 0.5 : 1)));
  const ruban = { ...f, Feuille: 'Ruban' };
  for (let i = 0; i < brins; i++) {
    const a0 = i * OR + h(i, 1), pied = polaire(c.EcartPied * R * h(i, 2), a0);
    const A = axe(pied, polaire(c.EcartPied * R + c.Evase * R, a0, H * (0.8 + 0.2 * h(i, 3))));
    if (o.etat.nom !== 'jeune' || c.Noeuds > 0) P.tube(A.pts, rBrin, rBrin * 0.6, M.tige);
    for (let k = 0; k < c.Noeuds; k++) P.boule(A.at((k + 1) / (c.Noeuds + 1)), rBrin * 1.25, M.tige, 0.5);
    for (let k = 0; k < c.Panaches; k++) {
      const p = A.at(0.45 + 0.5 * k / c.Panaches);
      for (let j = 0; j < 3; j++) o.feuille({ ...f, Feuille: 'Lanceolee' }, p, a0 + k * 2 + j * 0.9, -0.2, c.PanacheCm, 50 + k * 3 + j);
    }
    const tete = c.Panicule ? 'Panicule' : c.BarbeCm > 0 ? 'Barbu' : c.EpiCm > 0 ? 'Epi' : null;
    if (tete && o.etat.fleurs && o.etat.nom !== 'jeune') o.epi(c, tete, A.at(1), a0, 100 + i);
    else if (f.Tete !== 'Aucune' && o.etat.fleurs) o.tete(f, A.at(1), a0, 100 + i);
  }
  const n = o.nb(c.Rubans * (o.etat.nom === 'jeune' ? 1.5 : 1));
  for (let k = 0; k < n; k++)                          // rubans : de la base, en arc
    o.feuille(ruban, [0, 0.5, 0], k * OR, 0.9 + 0.4 * h(k, 4), Math.min(H * 0.7, 60) * (0.7 + 0.3 * h(k, 5)), 200 + k);
}

// BUISSON : bois bas, masse de grains-feuilles, cannes (droites ou en arc) à
// feuilles, têtes en surface ou au bout des cannes.
function buisson(o, f) {
  const { P, M, h, E } = o, b = f.Buisson, R = f.RayonCm * E, H = f.HautFeuillesCm * E;
  for (let k = 0; k < b.BoisBas; k++) {
    const a = k * OR, bout = polaire(R * 0.5, a, H * 0.45);
    P.tube([[0, 0, 0], polaire(R * 0.15, a, H * 0.2), bout], f.EpaisseurTigeCm * 0.5 * E + 0.2, 0.2, M.bois);
  }
  // masse : petites feuilles serrées en dôme — absente si Grains = 0 (framboisier, myrtille) :
  // nb() rend au moins 1, et une feuille de 0 cm fait boucler le puff d'ink (pas nul).
  for (let k = 0; b.Grains > 0 && k < o.nb(b.Grains * 1.5); k++) {
    const u = Math.sqrt(h(k, 1)), a = k * OR, p = polaire(R * 0.9 * u, a, H * (0.35 + 0.65 * Math.sqrt(1 - u * u)) * (0.8 + 0.2 * h(k, 2)));
    o.feuille(f, p, a, 0.5 + 0.6 * (1 - u), b.GrainCm * Math.sqrt(E), k);
  }
  for (let k = 0; k < b.FleursMasse; k++)
    o.tete(f, polaire(R * 0.7 * Math.sqrt(h(k, 3)), k * OR + 1, H * 0.95), k * OR, 100 + k);
  const cannes = Math.max(1, Math.round(b.Cannes * lerp(0.5, 1, E)));
  for (let i = 0; b.Cannes > 0 && i < cannes; i++) {
    const a = i * OR + h(i, 4), pied = polaire(b.Ecart * R * h(i, 5), a);
    const haut = b.EpiCm > 0 ? H + b.EpiCm * E : H * (0.8 + 0.2 * h(i, 6));
    const loin = b.Ecart * R + b.Evase * R;
    const at = u => add(pied, polaire(loin * u, a, haut * (u - b.Arc * 0.6 * u * u * u)));
    P.tube([0, 0.25, 0.5, 0.75, 1].map(at), Math.max(0.2, f.EpaisseurTigeCm * 0.5 * Math.sqrt(E)), 0.15, M.bois);
    for (let j = 0; j < b.FeuillesCanne; j++) {
      const u = b.BasNu + (1 - b.BasNu) * (j + 0.5) / b.FeuillesCanne;
      o.feuille(f, at(u), a + (j % 2 ? 1.4 : -1.4), 0.3 + b.Penche, lerp(b.FeuilleBasCm, b.FeuilleHautCm, u) * Math.sqrt(E), 200 + i * 20 + j);
      if (b.Rameaux && j % 2 === 1) o.feuille(f, at(u), a + 2.5, 0.5, b.FeuilleHautCm * Math.sqrt(E), 600 + i * 20 + j);
    }
    o.tete(f, at(1), a, 300 + i);
    if (f.Fruit && b.FeuillesCanne) for (let j = 0; j < 2; j++)
      o.fruit(f.Fruit, add(at(0.6 + 0.3 * j), [0, -2, 0]), a, 400 + i * 2 + j);
  }
}

// VOLUBILE (haricot) : tuteur, tige qui s'y enroule, feuilles aux nœuds, fleurs et
// gousses aux aisselles du haut.
function volubile(o, f) {
  const { P, M, h, E } = o, t = f.Tige, H = f.HauteurAdulteCm * E;
  P.tube([[3, -2, 0], [3, H + 8 * E, 0]], 0.9, 0.8, M.bois);           // tuteur
  const spire = u => [3 + 2.2 * Math.cos(u * H / 18), u * H, 2.2 * Math.sin(u * H / 18)];
  P.tube(Array.from({ length: 25 }, (_, i) => spire(i / 24)), 0.3, 0.2, M.tige);
  const n = Math.round(f.Feuilles * Math.sqrt(E));
  for (let j = 0; j < n; j++) {
    const u = (j + 0.6) / (n + 0.2), p = spire(u), a = j * OR;
    if (h(j, 1) < o.etat.densite || j === n - 1) o.feuille(f, p, a, 0.2, lerp(t.FeuilleBasCm, t.FeuilleHautCm, u) * Math.sqrt(E), j);
    if (j < n - t.TetesAisselle || j >= n - 1) continue;
    o.tete(f, add(p, dirA(a + 1, -0.2).map(v => v * 3)), a, 100 + j);
    if (o.etat.fruits && !o.etat.graines && j % 2) o.tete(f, add(p, dirA(a - 1, -0.2).map(v => v * 3)), a - 1, 200 + j, f.TeteCm, true);
  }
}

module.exports = { tige, chaume, buisson, volubile };

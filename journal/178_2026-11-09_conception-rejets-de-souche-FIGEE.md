# 2026-11-09 — Conception REJETS DE SOUCHE (reliquat D130) — FIGÉE

`/conception`, décisions de Nico. Doc :
`docs/vegetal/regeneration/conception_rejets_de_souche.md`. Sprint :
`sprints/vegetal/regeneration/sprint_frein_rejets_figuier/` (5 tronçons, golden
`a10b7225…` inchangé attendu).

## Diagnostic (verger_mur, seed 42, n=1 run, VM)
- Les 164 rejets de figuier de 25 ans sont nés en hiver : les portes du clonal
  (lumière au sol, couverture) sont calibrées pour la saison feuillée et grandes
  ouvertes en dormance. Un rejet est mère à 5 ans → 4 générations en 25 ans.
- Sans l'hiver : 0 rejet (portée sous la couronne, lumière 0,25 sous la mère).
- Golden : le trèfle émet 36 ramets, 0 en hiver → la dormance clonale est neutre.

## Décisions
- Pas de clonage en hiver, pour toutes les clonales.
- Rejet de souche = réponse à la perte de la partie aérienne (mort, ou grosse
  perte de couronne dont la taille du joueur → recépage émergent), au pied, sans
  gate de lumière à la naissance ; souche vivante lue sur les mémoires de dommage
  au pied (ombre, sécheresse, asphyxie, racines rongées, pourridié).
- Trait `rejet_souche` pour tous les ligneux (fort : figuier, cerisier, charme,
  aulne, saule, chêne ; moyen : pommier, noyer ; faible : bouleau, hêtre ; sapin 0).
- Gel des rameaux d'un ligneux adulte → dette D131.
- Le ⑤ vue de `sprint_releve_ligneuse` est absorbé par le ⑤ de ce sprint.

# 2026-11-09 — Conception ZOOCHORIE (D42) — FIGÉE

`/conception D42`, décisions de Nico. Doc :
`docs/faune/vie_macro/conception_zoochorie.md`. Sprint :
`sprints/faune/vie_macro/sprint_zoochorie/` (8 tronçons ; golden `a10b7225…`
inchangé sauf au ⑥, re-figé annoncé).

## Constats (code, 2026-11-09)
- Fruits traçables et recrue des ligneux sans lien : `_reproduction` tire toute
  l'année sans regarder les fruits.
- Le merle lit le fruit tombé sans le prendre ; aucune faune ne consomme de fruit.
- Une graine d'arbre en banque-sol ne germe jamais (germination par archétypes).
- `GrainEnAttente` (graine du joueur) est le bon véhicule d'une graine sauvage.

## Décisions
- Quatre disperseurs : merle (sème sous les perchoirs), geai (caches en découvert,
  fait entrer la forêt de la ceinture), écureuil (caches près des arbres, cimes
  connexes), mulot (prédateur de graines, petites caches, proie rapace/couleuvre).
- Recrue unifiée sur les vrais fruits pour les fruitiers pérennes fertiles : fruit
  tombé → grains au pied, fruit mangé → grains au loin ; recalibrage de la relève
  accepté.
- Geste `poser_perchoir`. Chêne et hêtre fruitiers, années de glandée synchrones,
  noisetier ajouté avec ses 5 voix.
- Grains sauvages : dormance jusqu'au printemps suivant, durée de vie par espèce,
  plafond par plot ; grains du joueur inchangés.
- Dettes à ouvrir à la clôture : granivorie du mulot sur la banque-sol et les
  semis du joueur ; myrtille et lierre fruitiers ; mammifères des pommes ;
  annuelles fruitières.

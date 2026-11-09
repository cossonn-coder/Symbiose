# 2026-11-09 — Sprint FREIN REJETS FIGUIER (reliquat D130) — CLOS côté code

Sprint : `sprints/vegetal/regeneration/sprint_frein_rejets_figuier/` (`/sprint-auto`, ①→⑤).
Conception : `docs/vegetal/regeneration/conception_rejets_de_souche.md`.
Golden `a10b7225…` **inchangé** sur les 5 tronçons.

## Tronçons
- ① `4d44afe` — dormance clonale : `emettre_ramets` ne tire rien en hiver (toutes
  clonales). `full` 5 ans [seed 42, n=1 run] : 117 ramets d'hiver → 0.
- ② `1b2968b` — trait `rejet_souche` (10 ligneux, sapin 0), figuier sans drageon ;
  `souche_vivante` lue sur les mémoires de dommage au pied (racines rongées /
  pourridié : seuil 0,2 = apparition du signe « parasite », choix d'implémentation) ;
  une vague de rejets hors hiver à la mort (`sim/souche.py`). Log en 🌳.
- ③ `63dd026` — mémoire `perte_couronne` (casse + taille joueur, cumul composé,
  oubli 6 %/sem hors hiver) ; > 0,5 → une vague de rejets d'un arbre vivant
  (taille sévère = recépage).
- ④ `bfef9c5` — événement `rejet` (causes `souche` / `perte_couronne`), carnet,
  encyclopédie (capacité par arbre), `diag_releve` voie `rejet`.
- ⑤ `539f864` — voix `attente` du ligneux ombragé sous seuil ; rendu des rejets
  sans code C# (même sérialisation), pont inchangé ; ⑤ de `sprint_releve_ligneuse`
  absorbé. D130 → « code fait, reste F5 ».

## Mesure 200 ans [verger_mur, seed 42, n=1 run, VM, 102 min]
Fourré max 4 petits ligneux sous une couronne (193 avant) ; remplacement ≥ 1 pour
chaque espèce dont le fondateur meurt ; figuier : 2 vagues de 3 rejets en 200 ans.
**À trancher par Nico** : figuier et pommier s'éteignent vers l'an 173-176 (rejets
morts d'ombre ; souche morte d'ombre ne repart pas) — consigné dans DETTE.md.
Perf `full` tick médian ans 3/4/5 : 1087/1095/1039 → 992/1071/1030 ms [n=1 run, VM chargée].

## F5 attendu
1. Turbo verger_mur : plus de colonie de figuiers. 2. Taille sévère du figuier →
rejets au pied au printemps suivant. 3. Mort d'un fruitier âgé → rejets au pied
(sauf sapin, sauf mort d'ombre). 4. Info-bulle d'un jeune arbre ombragé : « j'attends… ».

## F5 validé (2026-11-09)
Nico : « ça fonctionne », après `git pull`. Sa taille large (342 → 139 segments) n'a pas fait rejeter, et c'est attendu : les 60 % de segments les plus fins ne pèsent que 0 à 3 % du bois [an 8, n=1 run, VM]. Recéper = couper au ras du tronc. D130 fermée (lot Q de `DETTE_ARCHIVE.md`) ; extinction ~an 175 et seuil d'étêtage acceptés tels quels.

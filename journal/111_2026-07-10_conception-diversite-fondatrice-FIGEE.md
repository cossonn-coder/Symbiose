# 2026-07-10 — Conception DIVERSITÉ FONDATRICE (D74) — FIGÉE (`/conception`)

## Demande de Nico
Régler les **conditions de départ** de la simu sur deux axes couplés : (1) que
chaque plante n'ait PAS exactement le même patrimoine génétique et qu'il mute à
chaque génération (compléter la sélection naturelle) ; (2) que les **champs
écologiques** soient initialisés hétérogènes dès le départ (pas seulement l'humus).
**Comportement émergent visé : chaque plante a son propre rythme.**

## Diagnostic (code de vérité `data/code/`)
Le moteur génétique est déjà à ~90 % en place : vecteur 10 gènes, mutation par
génération (`sim/reproduction.py:child_genes`), héritage biparental, sélection
darwinienne émergente câblée (`_germ_gene_mean` lit `GeneStat.mean`). **Le manque =
la variance FONDATRICE = 0** : `GENE_INIT_SIGMA=0.10` défini (`genetics.py`) mais
JAMAIS utilisé → toute plante née sans lignée reçoit `genes={}` → clones parfaits.
Côté sol : sur `init_eco`, seuls `om_stable` (D56) et `altitude` sont hétérogènes ;
`ph/n/p/k/structure_sol/microbiome/humidite` démarrent uniformes.

## Revue critique A-E (tranchée avec Nico — j'ai challengé ma propre v1)
- **A** — au lieu de tirer `founder_genes` à chaque naissance, **ENSEMENCER la
  banque-sol** (`SeedBank.species` GeneStat) au démarrage pour WEED_CATALOGUE :
  `sample_genes` tire alors avec variance immédiate (philo #4, le sol porte la
  diversité latente). `founder_genes` ne sert plus qu'aux SEMIS DIRECTS.
- **B** — hash de `founder_genes` discriminé par (espèce, gène, position CONTINUE
  `x_cm/y_cm`, semaine) → deux plantes de même espèce au même plot ne sont plus des
  clones (compétition intra-plot, philo #3).
- **C** — champs édaphiques en **catena topographique** : corrélés à l'`altitude`
  déjà posée (NPK/microbiome riches en bas de pente) = part topo + bruit propre
  décorrélé, **amplitude PROPRE par champ** (pH/structure petites, NPK plus fortes).
  Réordonner `init_eco` : altitude AVANT les édaphiques. `om_stable`/`altitude` NON
  retouchés (D56 surgical) ; `humidite` EXCLUE (ruissellement) ; temperature\*
  exclues (climatiques, ré-écrites au tick).
- **D** — garde-fous : amplitudes pH/NPK PETITES (portes dures `bell`, faim d'azote
  D41) ; re-passer `diag_population` (le sprint invasion D69 a calibré des plateaux).
- **E** — division du travail : le rythme VISIBLE vient surtout de l'hétérogénéité
  des CHAMPS (plasticité au milieu) ; la GÉNÉTIQUE apporte la part héritable /
  sélectionnable. Le sprint enrichit le substrat de TOUS les acteurs.
- **Flag unifié `heterogene=False`** sur `init_eco` active À LA FOIS A et C, posé
  `True` par les seuls sites monde-réel (harnais golden, main.py, sim_server, bancs)
  → tests unitaires ciblés INTACTS, seul le golden re-fige.

## Découpage (3 tronçons)
- **① Génétique fondatrice** — `founder_genes` + `seed_founder_pool` (banque
  ensemencée) + naturalisation semis directs + graine `planter` sans lignée + flag
  `heterogene`. **Golden re-figé LARGE (GENES, annoncé).**
- **② Champs — catena topographique** — `init_eco` réordonné + primitive
  `_init_catena` + amplitudes propres + sens topo. **Golden re-figé (ECO, annoncé).**
- **③ Vue Godot** — banc F5 `diversite_fondatrice` (rythmes désynchronisés) +
  heatmaps catena `FieldOverlay` (F6) + survol gènes debug + re-passage
  `diag_population` (garde-fou). **Golden INTACT.**

## Livrables
`docs/conception/CONCEPTION_DIVERSITE_FONDATRICE.md` +
`sprints/sprint_diversite_fondatrice/` (00_etat + 01→03). DETTE **D74** + BACKLOG à
jour. **PRÊT pour `/sprint-auto sprint_diversite_fondatrice`.**

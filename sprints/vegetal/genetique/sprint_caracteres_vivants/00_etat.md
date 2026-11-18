# Sprint CARACTÈRES VIVANTS — état (D139, sprint ③ sur 3)

> Conception figée le 2026-11-16 : `docs/vegetal/genetique/conception_caracteres_vivants.md`
> (à lire en entier). **Prérequis** : `sprint_genetique_infinitesimale` et
> `sprint_niche_thermique` CLOS (registre, unités, F, `cout_defense` et coût thermique).

## But
20 caractères héritables qui relient la plante aux butineurs, aux fruits mangés, aux
herbivores, aux gestes et au sol, chacun lu par une mécanique existante et chacun payé
d'un compromis.

## Décisions clés (Nico, 2026-11-16)
- Q7 Liste validée + `parfum` + `couleur_fleur` en **dégradé visible**. Couleur inspirée du
  réel : axe de couleur par espèce, préférence par type de butineur, **guides à nectar**
  (piste d'atterrissage) → caractère `guide_nectar`.
- Q8 Toxicité **par organe** (`appetence_feuille`, `appetence_fruit`) : manger un organe
  toxique coûte de la Vigueur (D31) ; certaines plantes ont besoin d'être mangées pour se
  disperser.
- Ajouts de Nico retenus après vérification au code : `dominance_apicale`, `vigueur_clonale`,
  `portee_graine`, `fixation_azote`, `allelopathie`, `mycorhization` (`autofecondation` est
  parti au sprint ①). Écartés : voir conception §2.5.
- Règle : un gène n'entre que si une mécanique le lit ; tout ajout **en queue**.

## Golden
Départ = hash de fin du sprint ②. ①, ①b (deux fois : scénario puis mécanique), ①c, ①d,
②-④ **RE-FIGÉ annoncé** chacun (clés neuves + lecteurs)
· ⑤ INTACT · ⑥ INTACT.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_fleurs.md` — taille, nectar, pollen, couleur, guides, parfum + `cout_genetique` | **FAIT** (2026-11-18, commit `968704c`) — voir §① |
| ①b | `01b_fecondation.md` — pommier mûr au smoke, `fecondation` à la fanaison, part autofécondée | **FAIT côté code** (2026-11-18, non commité) — voir §①b |
| ①c | `01c_paternite.md` — compteur `pollen_donne`, père tiré ∝ pollen exporté | à faire |
| ①d | `01d_levee_graines.md` — annuelles qui se ressèment, espèce spontanée ∝ son pool | à faire |
| ② | `02_fruits_comestibilite.md` — taille des fruits, appétence feuille/fruit, Vigueur négative | à faire |
| ③ | `03_feuille_gestes.md` — coriacité, repousse, bouture, dormance, dominance apicale | à faire |
| ④ | `04_sol_expansion.md` — clonalité, portée, fixation, allélopathie, mycorhization | à faire |
| ⑤ | `05_signes_pont.md` — export des signes visibles, voix | à faire |
| ⑥ | `06_vue_banc.md` — rendu, banc `caracteres_vivants`, recette F5, clôture D139 | à faire |

## ① Fleurs — bilan (2026-11-18)
- **Fait** : 6 caractères en queue (`plants/caracteres.py`, σ_A 0,15 ; `couleur_fleur` en
  unité « position » ∈ [−1, 1]) ; champ `cout` du registre + `PlantInstance.cout_genetique()`
  appliqué aux 2 sites de `cout_defense` (croissance, convalescence) ; **K_THERMO rapatrié**
  dans le registre (`cout` = K_THERMO × σ_A des 3 thermiques), `cout_defense` ne multiplie
  plus `cout_thermique` (gardé pour tests/diagnostic). Couleur : `plants/couleurs.py` (plan
  chroma teinte+saturation, le blanc au centre), `PlantBase.axe_couleur` posé sur les 32
  espèces nectarifères, `PollinatorSpec.pref_couleur` par type (osmie = blanc/jaune/violet,
  choix de jeu). `poids_floral` = ressource×gène (`nectar`, ou `pollen` sur la voie vibrée)
  × √(taille×parfum×guide) × préférence couleur ; agents : dépôt réparti ∝ poids floral
  (avant : ∝ floraison). Ruche : passe aussi la préférence. Anémophilie : dose × `pollen` de
  l'émetteur. Herbivorie : × (1 − 0,5·(parfum − 1)) ∈ [0,7 ; 1,3]. Greffe : les 6 gènes
  floraux suivent le greffon.
- **Golden RE-FIGÉ** `88cca899…` → `d05997a459af41704c840ee692e4408bd702de28ae942193f01b12770edfa621`
  (6 clés neuves au digest ; 1ʳᵉ divergence = pression d'herbivorie via `parfum`, puis coût
  génétique et nourriture des butineurs ; 37 → 35 plantes au digest final). `population_hash`
  re-figé → `63153a0a…` (nourriture florale). Suites vertes sauf `test_peripherie` 70/71,
  **rouge AVANT ce tronçon** (vérifié au stash).
- **Perf** : smoke +0,7 % [n=4 paires alternées, bruit ±5 %] ; sous profileur +1,2 %.
  Axe → chroma mémoïsé (`plants/couleurs._AXES`).
- **Banc** `mesures/banc_fleurs.py` : (a) bourraches, la moitié bleue reçoit **+16 %** de
  pollen des butineurs [n=16 pieds, 1 génération], MAIS banque-sol +0,050 contre fondateurs
  +0,023 : **aucun différentiel réalisé**. (b) phacélie nectar 0,7/1,0/1,3 → nourriture
  abeille 0,391/0,441/0,492, densité d'abeilles 0,1091/0,1094/0,1095 (champ saturé,
  `FLOWER_REF`), pollen/pied identique (1 pied par plot).
- ⚠ **TROU DE CONCEPTION (à arbitrer, Nico/orchestrateur)** : chez les herbacées
  entomophiles, le NOMBRE de graines ne dépend pas des visites (`_reproduction` tire au
  hash contre `reproduction_rate` ; `pollen_recu` n'est lu que par la nouaison des
  `fruitier`, et seule la relève des fruitiers PÉRENNES passe par les fruits). Le père
  est le voisin le plus proche (`find_father`), pas le plus visité. Donc la couleur, le
  nectar, la taille… ne sont **sélectionnés que chez pommier/cerisier** (maturité 5 ans) ;
  ailleurs ils dérivent et leur coût les fait baisser. Piste : graines d'une entomophile ×
  `frac_nouaison(pollen_recu)` avec remise à zéro par cohorte — mécanique neuve, golden
  et dynamique des populations touchés → /conception, pas ce tronçon. Note annexe :
  `pollen_recu` cumule sans fin chez les non-fruitiers (12-16 en 1 an au banc).
- Taille : `fields/population/registry.py` 360 LDC (339 avant, déjà 🟡),
  `plants/species/cultivees.py` 381 (374 avant, données).
- Vue G : `couleur_fleur` (unité « position ») s'affiche en « × » par défaut et les 6
  caractères sans libellé (`tools/simserver/genes_pont.py`) — à traiter au ⑤.

## ①b Fécondation — bilan (2026-11-18)
- **Fait** : smoke = pommier pré-vieilli à `maturity_years` (`tests/test_golden.py`) → il
  noue s8 et s61 (« 🍎 Nouaison »). `PlantInstance.fecondation` (hors digest, défaut 0).
  `decompo.feconder(plant)` = `a + (1 − a)·frac_nouaison(pollen_recu)` (`self` → 1), remet
  `pollen_recu` à 0 et désarme ; appelée à la fanaison de **toute** plante fleurie dans
  `_tick_fruits` (armement généralisé) et par la nouaison des fruitiers (`frac = feconder ×
  glandée`). **Stérilité thermique étendue aux herbacées** (décision : un pollen stérile ne
  féconde rien ; la fanaison attend une semaine plus fraîche). Lecteurs : `_reproduction`
  (`rate × fecondation`, porte de hash ET densité), `semer_fin_de_cycle` (archétype ET pool),
  récolte joueur (rien si `fecondation == 0`). Remise à 0 de toute la tuile juste après
  `_reproduction` (11b), même tick que la récolte (11) → ordre vérifié. `heredite` : seuil
  d'autofécondation `min(1, a/fecondation)`, `a` seul si `fecondation <= 0`.
- **Appelants de `heredite`** (grep) : `mortalite._reproduction`, `fin_de_cycle.semer_fin_de_cycle`,
  `boucle` (récolte joueur), `decompo.semer_chute`, `zoochorie` (merle), `caches` (geai/écureuil),
  `reproduction.child_genes` ; hors moteur `bancs/lignees.py` + tests. Les trois chemins de
  fruits tombés/emportés lisent `fecondation` tant qu'elle n'est pas remise à 0 (jusqu'à s39),
  puis `a` seul.
- **Golden RE-FIGÉ deux fois** (non commité, consigné ici — l'orchestrateur fera les deux
  commits ou un seul) : (1) scénario `d05997a4…` → `3b727984fe6e6f1ad899c9216c0be2fe65171739664bfe1d817cf28991805a3f`
  (vérifié reproductible depuis HEAD + seul `test_golden.py` changé) ; (2) mécanique →
  `db9418142e1ca4baf101c5d1630ec0eb426b800aa21e0fa7324dc1cc6339a8b2`. 1ʳᵉ divergence (2) :
  **nouaison du pommier s8** (frac 0,67 → 0,76, part autofécondée `a` = 0,15 ajoutée), avant
  toute herbacée — attendu, la formule change aussi pour les fruitiers. `population_hash`
  re-figé → `b76871aca851a70c3695cd3ea22c5fe502601f4d64e2d2266f3ba4b4f5aa15cc` (mécanique).
- **Tests** : `tests/test_fecondation.py` 11/11 (self → 1, sans pollen → a, croît → 1, pollen
  à 0, fanaison d'herbacée, non fleurie ne dépose rien, sans pollen F > 0). Adaptés :
  `test_fruits` (nouaison sans pollen = part `a`), `test_banque_semis`, `test_chute_seme`,
  `test_reponse_thermique` (parent marqué fécondé), `tests/simserver/planter.py` (la 1ʳᵉ graine
  récoltée arrive à la récolte d'été s26, plus au printemps : boucle bornée à s45). Toutes
  les suites vertes sauf `test_peripherie` (rouge avant).
- **Inventaire de risque** (`mesures/banc_fecondation.py`, monde full, 3 ans [n=1 seed]) :
  **aucune espèce ne perd toutes ses graines**. Mises en graine avant→après : bourse 327→228,
  trèfle 643→453, lupuline 257→206, pâturin 86→63, plantain 32→21, autres ≈ (pieds sans
  floraison fanée dans l'année). Doses à la fanaison (méd.) : pommier 7,0 (fec 0,91), cerisier
  0,0 (fec 0,165 : seul, autostérile), trèfle 0,39 (0,42), achillée 0,34 (0,31), lupuline 3,1,
  phacélie 13,6, pissenlit 7,2, graminées `wind` 2-6 (0,7-0,86). Saturation : `POLLEN_DEMI` = 1
  est dépassé ×5-15 chez les bien visitées (fec ≈ 0,9) — non calibré (hors tronçon).
  Sphaigne (`self`) fleurit au moteur et fait fec = 1 : pas d'exception nécessaire.
  ⚠ **`PoaAnnua` est en mode `insect` sans nectar** : pollen 0 sur 68 fanaisons → fec = a
  (0,085). Le pâturin annuel réel est anémophile/autogame : donnée à corriger (mode `wind`
  ou neutre d'`autofecondation` haut) — **non corrigé**, à arbitrer.
- ⚠ **Pollen après la fanaison** (constaté, non corrigé) : le dépôt des butineurs est réparti
  ∝ poids floral parmi les conspécifiques DU PLOT, donc un pied seul capte toute la charge même
  à `floraison` résiduelle (0,00x) ; ce pollen tardif s'accumule jusqu'à la fanaison de l'an
  suivant (pommier du smoke : 4,5 reçus s23-26, fleurs fanées). Biais : la dose de l'an N
  inclut la queue de l'an N−1. Piste : ne déposer que sur `floraison ≥ SEUIL_NOUAISON`, ou
  remettre à 0 à l'armement — à trancher (①c touche ce code).
- **Banc fleurs (a)** : fécondation moitié bleue **0,673** contre rose **0,631** [n=16 pieds,
  1 génération], densité déposée/pied 0,0404 contre 0,0379 → le différentiel existe désormais
  côté mère (+7 %). Banque-sol couleur +0,032 contre fondateurs +0,023 (paternité et levée
  pas encore branchées : ①c, ①d).
- **Perf** : smoke 4,351 s → 4,367 s, +0,4 % [n=5 paires alternées, bruit ±3 %].
- Taille : `sim/engine/boucle.py` 306 LDC (🟡, 303 avant), `decompo.py` 192, `mortalite.py` 248.
- Écart au kickoff : une annuelle qui finit son cycle APRÈS s39 voit sa `fecondation` remise
  à 0 par l'automne → `semer_fin_de_cycle` ne dépose plus rien (elle a grené à s39 : un seul
  dépôt au lieu de deux). Conforme à « remise à 0 après le dernier lecteur », à garder en tête.

## Conception FÉCONDATION (trou du ①) — ARBITRÉE et FIGÉE (Nico, 2026-11-18)
Doc : `docs/vegetal/genetique/conception_caracteres_vivants.md` §6. Diagnostic : le nombre de
graines ne dépendait ni des visites, ni ne faisait le nombre de descendants (annuelles
sans archétype : pool jamais levé) ; le père était le plus proche ; `pollen_recu` cumulait
à vie hors fruitiers.
- **Q1 = S3** : `fecondation` lue partout où `rate` l'est + annuelles qui se ressèment
  depuis leur pool + espèce spontanée tirée ∝ (ε + densité de son pool). Emballement
  possible du trèfle **assumé** : on l'observe, on le corrigera plus tard par davantage
  d'espèces en compétition (pas de garde-fou dans ce sprint).
- **Q2 = vrai compteur** `pollen_donne` (recharges des butineurs + panache anémophile),
  père tiré au hash ∝ `pollen_donne × (1 − d²/reach²)`.
- **Q3** : `fecondation = a + (1 − a)·g(pollen_recu)` pour toute plante, nouaison des
  fruitiers comprise ; part autofécondée des graines = `a / fecondation`. **Un pommier
  mûr entre dans le smoke** (pré-vieilli comme `cmd_init` « full ») pour que le golden
  exerce la nouaison.
Tronçons insérés avant ② : `01b_fecondation.md`, `01c_paternite.md`, `01d_levee_graines.md`.

## REPRISE
①b fait côté code (non commité : deux hashes consignés au §①b). Lire `CLAUDE.md`, ce
fichier, puis le kickoff du premier tronçon « à faire » (①c). Deux points à arbitrer avant
ou pendant ①c : mode de pollinisation du pâturin annuel, pollen déposé après la fanaison.

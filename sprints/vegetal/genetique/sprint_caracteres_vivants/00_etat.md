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
Départ = hash de fin du sprint ②. ①, ①b (deux fois : scénario puis mécanique), ①d,
(①c annoncé re-figé, resté **INTACT** : voir §①c),
② (`c6fd8275…`), ③ (`5bfbd8a3…`), ④ (`db4d6b75…`)
· ⑤ INTACT · ⑥ INTACT.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_fleurs.md` — taille, nectar, pollen, couleur, guides, parfum + `cout_genetique` | **FAIT** (2026-11-18, commit `968704c`) — voir §① |
| ①b | `01b_fecondation.md` — pommier mûr au smoke, `fecondation` à la fanaison, part autofécondée | **FAIT** (2026-11-18, commit `b157ee6`) — voir §①b |
| ①c | `01c_paternite.md` — compteur `pollen_donne`, père tiré ∝ pollen exporté | **FAIT** (2026-11-18, commit `96505f5`) — voir §①c |
| ①d | `01d_levee_graines.md` — annuelles qui se ressèment, espèce spontanée ∝ son pool | **FAIT** (2026-11-18, commit `9fdcbe9`) — voir §①d |
| ② | `02_fruits_comestibilite.md` — taille des fruits, appétence feuille/fruit, Vigueur négative | **FAIT** (2026-11-18, commit `0134bd5`) — voir §② |
| ③ | `03_feuille_gestes.md` — coriacité, repousse, bouture, dormance, dominance apicale | **FAIT** (2026-11-18, commit `bc22825`) — voir §③ |
| ④ | `04_sol_expansion.md` — clonalité, portée, fixation, allélopathie, mycorhization | **FAIT** (2026-11-18, commit `dac1231`) — voir §④ |
| ⑤ | `05_signes_pont.md` — export des signes visibles, voix | **FAIT** (2026-11-18, commit `5b17796`) — voir §⑤ |
| ⑥ | `06_vue_banc.md` — rendu, banc `caracteres_vivants`, recette F5, clôture D139 | **FAIT** (2026-11-18, commit `df5a57f`) — voir §⑥ |

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

## ①c Paternité — bilan (2026-11-18)
- **Fait** : `PlantInstance.pollen_donne` (hors digest). Butineurs : `sample_foragers`
  rend un 3ᵉ élément `recharges` (espèce, r, c, `params.recharge`) **à chaque visite** ;
  `_apply_deposits(…, attr="pollen_donne")` les crédite ∝ poids floral, même vent que le
  dépôt. Vent : chaque émetteur crédité de `coef × vent × floraison × gène pollen` qu'il
  envoie à chaque cible, la cible de sa part auto (Σ donné = Σ reçu). Remise à 0 en
  **semaine 1** dans `_tick_floraison` (avec `gdd_accum`/`bloom_week`). `find_father` :
  poids `pollen_donne × (1 − d²/reach²)`, tirage au hash canal `week * 79` (vérifié libre),
  repli « le plus proche » si Σ poids = 0 ; signature intacte.
- **Écart au kickoff** : le crédit butineur n'est PAS le gain de `charge` — la charge n'est
  jamais vidée au dépôt et sature à 1 dès la 2ᵉ visite (recharge 0,5) : seules les 2
  premières fleurs d'une tournée auraient exporté. Crédit = `params.recharge` par visite.
- **Golden INTACT** `db941814…` (kickoff : re-figé attendu). Vérifié non inerte : sur les
  27 appels de `find_father` du smoke, **9 pères changent** (bourse s78-90, trèfle s91),
  mais leurs graines vont aux pools (archétype/espèce) et aucune ne lève en 4 ans (levée
  des pools = ①d) → digest final et log inchangés. `population_hash` non concerné.
- **Tests** : `tests/test_paternite.py` 13/13 (recharge par visite, partage ∝ poids,
  croît avec les visites, source au vent créditée, Σ donné = Σ reçu, gros donneur tiré
  0,73 pour 0,75 attendu [n=200], poids nuls → plus proche, hors portée jamais tiré,
  remise à 0 s1). Vertes : genetique, heredite, fecondation, caracteres(_fleurs), vent,
  fruits, ruche, population, banque_semis, chute_seme, niche/réponse thermique,
  biennial, lifecycle, faune_dediee, fleurs_lisiere, figuier, automate_determinisme.
- **Banc** `mesures/banc_paternite.py` (mère neutre, pères à 100 cm, nectar+taille 1,3
  contre 0,7, côtés alternés) : part attendue du père attirant **0,80** [n=6 mondes où il
  survit ; 2 mondes sur 8 il n'exporte rien, part 0] ; moyenne brute 0,60 [n=8]. Tirages
  réels 3 contre 4 [n=7 : **une seule mise en graine par mère et par an**, et un seul père
  par événement — le pool est une statistique de gènes, pas des graines individuelles].
  Banc fleurs (a) : banque-sol couleur **+0,016** (contre +0,032 au ①b, fondateurs +0,023)
  → différentiel réalisé enfin négatif = vers le bleu préféré de l'abeille, −0,007
  [n=16 pieds, 1 génération, 1 seed]. Plusieurs générations impossibles avant ①d
  (la bourrache ne relève pas de son pool).
- **Perf** : smoke 5,191 → 5,197 s, +0,1 % [n=5 paires alternées, bruit ±3 %].
- Non traités (hors kickoff, toujours à arbitrer) : pollen déposé après la fanaison (même
  biais côté mâle : un pied fané seul sur son plot reçoit tout le crédit de la recharge),
  mode de pollinisation de `PoaAnnua`.
- Taille : `sim/reproduction.py` 115 LDC, `fields/foragers.py` 109, `butineurs.py` 62.

## ①d Levée des graines — bilan (2026-11-18)
- **Fait** (`sim/succession.py`) : **S3** `choisir_espece(…, banque)` tire au hash (canal
  `week × 61` inchangé) ∝ `PLUIE_EXTERIEURE + densité du pool` (0,02, levier non calibré) ;
  aucun pool → tirage uniforme historique au bit près. **S2** `_ressemis` : sur un plot où
  aucun archétype ne lève (pas de candidat, ou flore sans espèce éligible à cet azote),
  chaque annuelle/bisannuelle sans archétype (= sans recrue directe, règle de
  `_reproduction` : arbres et vivaces sans archétype seuls recrutés) dont le pool dépasse
  `SPECIES_POOL_MIN_DENSITY` a `w = niche_eff × densité / RESSEMIS_DENSITE_REF` ; le plot lève
  avec `1 − Π(1 − w)` (canal `week × 97`), l'espèce tirée ∝ `w` (canal `week × 101`, tous deux
  vérifiés libres). Portes partagées sans doublon : `_porte_ph`, `_porte_temp`,
  `_porte_allelo` servent aux `arch_*` ET au ressemis ; levée commune `_germer` (offset,
  form_seed, gènes du pool + tri thermique, F, priming). Log `🌿 Germination : … [niche=… ressemis]`.
- **Écart au kickoff (à arbitrer)** : `RESSEMIS_DENSITE_REF = 0,05` ajouté. La formule
  `niche_eff × densité` brute ne faisait rien lever : le pool d'une espèce reçoit
  `rate × fecondation` une fois par an (≈ 0,03-0,05 par mère) alors que la banque
  d'archétype, nourrie chaque semaine, sature vers 1 → banc (g) **0 levée en 6 ans**
  [16 bourraches, 1 seed]. Avec la référence (un pied qui a grené une fois remplit son
  plot) : 7, 8, 2, 0, 0, 0 levées par an.
- **Ordre vérifié** : fin de cycle (sénescence) et `_reproduction` (s39) déposent AVANT la
  succession du même tick ; `tick_species_aging` (×0,997/sem, demi-vie ≈ 4,4 ans) s'applique
  à tous les pools, annuelles comprises. Une levée ne vide pas le pool (comme pour
  l'archétype) : un pool de 0,05 reste au-dessus du seuil ≈ 15 ans.
- **Golden RE-FIGÉ** `db941814…` → `5d26af06bc79f4c5ad586cbfc3c1cb54c14441d355dad2b1e5890122d3a19351`.
  1ʳᵉ divergence : **s23, ressemis S2 d'une phacélie** @(1,6) (pool déposé par sa fin de
  cycle) ; puis s53 tirage S3 (plantain au lieu d'ortie, @(5,2)). 1 seul ressemis au smoke ;
  digest final 35 plantes, même composition sauf ortie 1 → 0 / plantain 2 → 3. Sans la
  référence (S3 seul), le hash était `1769f8d6…`. `population_hash` RE-FIGÉ `b76871ac…` →
  `20b8184064f82317220b6b13ba0335518659e6d6ebe3574afb9f618625a39a7a` (cause S2 vérifiée :
  référence neutralisée ⇒ ancien hash).
- **Banc population** `mesures/banc_levee.py` (monde full, 10 ans, [n=1 seed]) : max pieds en
  été 878 → 930, max/tuile 205 → 234 (cap 800 jamais atteint). Levées S3 cumulées : pâturin
  annuel 212 → 276 (+30 %), pissenlit 84 → 116, dactyle 163 → 115, fétuque 83 → 51, plantain
  119 → 92 (bourse, minette ≈). En été an 10 : pâturin 55 → 66, pissenlit 48 → 73, dactyle
  60 → 57, trèfle 398 → 342 (pic an 4 : 499 → 574, effet indirect : le trèfle n'est pas dans
  S3). **Pas d'emballement constaté** → pas de dette ouverte ; dérive « riche s'enrichit » vers
  le pâturin (déjà mal typé `insect`, cf. ①b) et le pissenlit, à surveiller. S2 : **13 levées
  de phacélie** (ans 1-3) puis extinction an 4 ; aucune autre annuelle dans ce monde.
- **Banc sélection** `banc_fleurs.py g 6` (nouveau scénario) : fondateurs +0,023 ; pieds nés
  an 1 −0,053, an 2 −0,136 ; pool +0,016 → **−0,047** (dérive vers le bleu de l'abeille,
  critère d'acceptation atteint) [n=16 fondateurs, 1 seed] ; mais la lignée s'éteint an 4-5
  (1 pied né an 3-4, 0 ensuite) : les levées ne survivent pas à la flore férale.
- **Perf** : smoke 4,340 → 4,387 s, **+1,1 %** [n=5 paires alternées, bruit ±2 %] ; tick
  moyen banc population 0,911 → 0,904 s [n=1 run chacun, VM chargée en parallèle : non
  significatif].
- **Tests** : `tests/test_levee_graines.py` 11/11 (S3 sans pool = uniforme, pool dominant
  0,988, pluie extérieure ; S2 lève, pas sous ombre, pas hors pH (fenêtre resserrée : la
  bourrache réelle a `ph_tol` 3), lève dans sa fenêtre, pool sous seuil, trèfle sans double
  voie, archétype prioritaire). Toutes les suites vertes sauf `test_peripherie` 70/71
  (rouge avant le sprint).
- Taille : `sim/succession.py` **306 LDC** (🟡, 245 avant ; une seule responsabilité : la
  levée férale) — scission possible (portes + ressemis → module dédié) si elle grossit.

## ② Fruits et comestibilité — bilan (2026-11-18)
- **Fait** : 3 caractères en queue (`plants/caracteres.py`) : `taille_fruit` (facteur, σ_A
  0,15, sans `cout` : compromis structurel), `appetence_fruit` / `appetence_feuille` (unité
  neuve « goût », [−1, 1], σ_A 0,10, neutres 0,3 / 0). Neutres d'espèce du tableau §2.2 posés
  en `genetique` sur les 20 espèces (tomate, poivron, courgette, lierre, armoise, consoude,
  noyer, fraisier, myrtille, cerisier, basilic, mâche, menthe, thym, pissenlit, ortie,
  bourrache, framboisier, figuier, pommier). Lecteurs : `decompo.nouer` (masse × g ; nombre
  ÷ g chez les arbres, arrondi existant ; herbacées : masse seule) ; `herbivory_pressure` ×
  `max(0,2, 1 + appetence_feuille)` ; `manger` via `sim/gout.py` (module pur) : valeur =
  `base × (1 + a)`, sous `SEUIL_TOXIQUE` −0,3 la bouchée **retire** `PERTE_TOXIQUE 0,5 ×
  HARVEST_GAIN_FULL × |a|` (débit par `spend`, seul point de débit ; geste toujours gratuit ;
  « Vigueur infinie » masque la perte, comme les champignons). Fruit ciblé : aussi ×
  `taille_fruit`. Carnet : ligne `👅 Goûté [T] @(r, c) : Nom, cause` écrite par `manger`
  (canal `log`, patron `lignee`), relue par `evenements` (kind `gout`, causes
  `amer|toxique` × `feuille|fruit`), 8 gabarits, concept NEUF « comestibilité » (propre au
  carnet). Greffe : les 3 gènes suivent le greffon. Pont : `vigueur_en_mots` dit une valeur
  négative (« le ventre se noue »).
- **Vérifié, rien à faire** : zoochorie (`prendre`) ne lit que le NOMBRE de fruits (déjà ÷
  taille), pas la masse ni le goût (oiseaux tolérants, §2.2) ; le mulot ne mange que des
  graines au sol, aucun lecteur de fruit → `appetence_fruit` n'y est pas branchée.
- **Golden RE-FIGÉ** `5d26af06…` → `c6fd82754af9f9624a38d2d339e545f7f601f3c942a92dbecf798628835c05da`
  (3 clés neuves au digest). 1ʳᵉ divergence : **nouaison du pommier s8**, 8 → 10 fruits
  (gène `taille_fruit` < 1 du fondateur) ; puis pression d'herbivorie s14 (`appetence_feuille`
  du fondateur). Digest final 35 → 41 plantes vivantes (trèfle 15 → 22, minette 6 → 8,
  pissenlit 1 → 0) : cascade, pas un effet ciblé. `population_hash` **INTACT** `20b81840…`.
- **Tests** : `tests/test_caracteres_fruits.py` 21/21 (taille ↔ nombre, masse conservée ±5 % ;
  feuille de tomate −4,5, basilic 16,8 contre 10,5 neutre, amer −0,2 nourrit moins ; fruit de
  lierre −6 ; poivron fruit +, Vigueur infinie masque ; ligne → événement → note « mal au
  ventre » ; bouchée savoureuse sans note ; pression croît avec l'appétence, plancher).
  **Adaptés** : `test_caracteres` (3 entrées du registre), `tests/vigueur/manger.py` (D1, D2,
  D4 mangeaient une feuille de tomate, désormais toxique → goût neutre forcé, le test porte sur
  la façade). Toutes les suites `tests/test_*.py` vertes sauf `test_peripherie` 70/71 (rouge
  avant). Bancs `tests/bancs/` : `climatique`, `edaphique`, `bancs_grimpe`, `verger_mur`
  rouges **à HEAD aussi** (mêmes messages, vérifié sur un worktree de 9fdcbe9).
- **Perf** : smoke 4,46 → 4,80 s [n=4 paires alternées ; monde divergent, 35 → 41 plantes,
  surcoût des lectures non isolé] — les lectures ajoutées sont O(1) par plante.
- Taille : `sim/effects/perturbations.py` **301 LDC** (🟡, 299 avant) ; `plants/species/cultivees.py`
  384 (données, 381 avant) ; `sim/carnet.py` 293 ; `sim/actions/gestes.py` 282 ; `sim/gout.py` 28.
- **Décisions de jeu prises ici (à valider F5)** : `1 + a` pour un organe mangeable (le fruit
  neutre +0,3 nourrit donc 30 % de plus qu'avant ce tronçon) ; discontinuité assumée au seuil
  (−0,29 → 0,71 × base, −0,31 → perte) = seuil de dose ; la perte ne dépend ni de la maturité
  ni de la santé (la plante se défend à tout âge) ; pas de note de carnet pour une bouchée
  savoureuse ; le concept « comestibilité » n'est crédité par aucune détection de maîtrise
  (note toujours descriptive hors vision / réglage anticipé) — à brancher au ⑤ si voulu.

## ③ Feuille et gestes — bilan (2026-11-18)
- **Fait** : 5 caractères en queue (`plants/caracteres.py`) : `coriacite_feuille` (facteur,
  σ_A 0,15, `cout` K_FLEUR), `repousse`, `dormance_graine`, `dominance_apicale` (facteurs,
  σ_A 0,15, prix structurels), `aptitude_bouture` (probabilité, neutre 1,0 = reprise certaine
  d'avant, σ_A 0,10, bornes [0, 1]). Lecteurs :
  - coriacité : grêle `suscept = 1/(hail_resistance_base × gène)` (`mortalite._mediated_damage`,
    branche `species_base`, seule utilisée par la grêle) ; ravageurs `÷ gène`
    (`herbivory_pressure`, borné par les bornes du caractère ⇒ × [0,63 ; 2,5]) ; litière :
    champ neuf `Parcelle.lenteur` (moyenné par la masse à la fusion, même garde que
    `diam_cm`), taux du tissu `÷ lenteur` dans `tick_decomposition` ; posé au dépôt de la
    mort (`perturbations`, parties molles) et de l'abscission (`decompo`) ; conservé par le
    transport éolien (`transport.py`) et la copie de conteneur (`world/container.py`).
  - repousse : champ neuf `PlantInstance.semaine_reprise` (hors digest) posé par
    `_noter_geste_vu` (tailler, pincer, arracher ; TOUTES espèces) ; `grow_plant` × gène sur
    l'élongation pendant `REPRISE_SEMAINES` = 8 ; herbacées sans squelette : rabattu sur
    `semaines_rabattu(plant) = RABATTU_SEMAINES ÷ gène` (dépôt ET pont `taille_pont`) ;
    convalescence `heal × gène` (toute convalescence, broutage compris). Prix : floraison
    plafonnée à `min(1, 1 ÷ repousse)` (`floraison.py`, une lecture ; ≥ 0,625 donc toujours
    « fleuri » au seuil 0,5).
  - bouture : `bouture_prend` = `_hash_noise(seed, week × 131, r, c) < gène` (canal libre,
    grep). Échec APRÈS paiement : Vigueur dépensée, mère fatiguée, aucun clone, pas de
    marqueur D12.
  - dormance : `tick_species_aging` perte du pool = `1 − (1 − 0,997) ÷ moyenne du gène`
    (1 lecture par enregistrement) ; `SeedBank.densite_levable` = densité ÷ moyenne, lue par
    S3 (`choisir_espece`) et S2 (`_ressemis` ; le seuil de pool reste sur la densité brute).
  - dominance : `apical_dominance_base × gène` dans `_update_auxin` ET `_debourrement`.
  - Greffe : coriacité, aptitude_bouture, dormance, dominance suivent le greffon ; repousse
    reste au porte-greffe.
- **Écarts au kickoff** : (a) « tige plus haute » : en isolé l'élongation de l'apex ne lit
  pas l'auxine, la hauteur ne diffère qu'après ~70 semaines (tomate : 0,6 → 64 cm /
  19 latérales ; 1,5 → 138 cm / 1 latérale), via l'élagage au plafond de segments ;
  « moins de fleurs latérales » N'EXISTE PAS au moteur (la floraison n'est pas portée par
  les segments) → prix de la dominance = forme seule. (b) Récolte non branchée à la repousse
  (kickoff ne la listait pas). (c) La convalescence lit la repousse pour TOUT dégât, pas
  seulement l'herbivorie (elle n'a pas de cause).
- **Golden RE-FIGÉ** `c6fd8275…` → `5bfbd8a359cf07e60e1c4a8c5c6c133387d89213fd9ca16af52f1aace23f6728`
  (5 clés neuves au digest). 1ʳᵉ divergence : **s6, rosée T1** 0,266 → 0,267 (coût de la
  coriacité du pommier fondateur, 1,585 ≈ +3,9 σ → croissance −12 %) ; puis **nouaison du
  pommier s7** au lieu de s8, 4 fruits (frac 0,28) au lieu de 10 (0,76) : sa `repousse` 1,25
  plafonne la floraison à 0,80 → fanaison une semaine plus tôt, moins de pollen. s60 :
  13 fruits (0,95) contre 13 (0,94). Vérifié : coriacité neutralisée ⇒ 1ʳᵉ divergence = s7.
  Digest final 43 → 47 vivantes (trèfle 22 → 27, minette 8 → 5, pissenlit 0 → 2) : cascade.
- **Perf** : smoke médiane 5,24 → 5,17 s [n=5 paires alternées, bruit ±10 %, monde
  divergent] ; `tick_species_aging` 0,140 → 0,150 µs/stat [banc 2000 pools, meilleur de 7],
  dont +5 stats/pool (gènes neufs) et ≈ 0,27 µs/pool pour la lecture de dormance.
- **Tests** : `tests/test_caracteres_feuille.py` 18/18 (grêle, ravageurs, litière +
  fusion, rabattu, élongation après coupe et sans coupe, plafond floral, bouture 0/0,5/1 +
  déterminisme + échec, dormance persistance + levée, dominance).
- **Adaptés** : `test_caracteres` (5 entrées du registre), `tests/simserver/taille.py`
  (`rabattu` une semaine après = 7/8 au neutre, désormais ∈ ]0,79 ; 0,96[ selon la repousse
  du pied, non exportée). `population_hash` **RE-FIGÉ** `20b81840…` →
  `9f7f348c8159b4c22b638e02f5274d2ebc160ad3411a6e897580c9fa67ed1877` (monde divergent dès
  s6 : coût de coriacité, repousse → floraison → nourriture florale). Toutes les suites
  `tests/test_*.py` vertes (sim_server 349/349) sauf `test_peripherie` 70/71 (rouge avant).
  Bancs `tests/bancs/` : rouges = `bancs_grimpe`, `climatique`, `edaphique`, `verger_mur`, les mêmes quatre que ceux constatés rouges à HEAD au ② (pas revérifiés au stash ce tronçon).
- Taille : `fields/seedbank.py` **320 LDC** (🟡), `sim/effects/perturbations.py` **303** (🟡),
  `sim/succession.py` 306 (🟡, inchangé), `sim/growth/phases.py` 186, `mortalite.py` 250.
- **À valider F5 / arbitrer** : le pommier du smoke tire une coriacité à +3,9 σ (fondateur) ;
  pression des ravageurs ×2,5 à coriacité 0,4 ; repousse sans fenêtre pour la récolte.

## ④ Sol et expansion — bilan (2026-11-18)
- **Fait** : 5 caractères en queue (`plants/caracteres.py`, facteurs σ_A 0,15) :
  `vigueur_clonale`, `portee_graine` (prix structurels), `fixation_azote`, `allelopathie`,
  `mycorhization` (`cout` K_FLEUR). Lecteurs :
  - clonalité (`sim/clonal.py`) : chance d'émission `gène / clonal_interval`, rayon ×
    gène. Prix : `PlantInstance.taux_graines()` = `reproduction_rate ÷ gène` chez une
    clonale seulement, lu aux 3 sites de mise en graine (`_reproduction`,
    `semer_fin_de_cycle`, `SeedBank.tick_plant_production`). Ramet = gènes + F + expression
    de la mère : **vérifié** (déjà au code).
  - portée : `_plot_sous_le_vent(…, force × gène de la mère)`. Prix : `densite_levable`
    ÷ moyenne du gène dans le pool, **anémochores seulement** (lue par S2 et S3).
  - fixation : clé neuve `"gene"` d'un effet `inject_field` (`sim/effects/resolution.py`,
    la plante émettrice y est déjà accessible) : `amount × plant.gene(clé)`. Posée sur
    les 4 fixatrices (Fabaceae, minette, effet d'espèce de lupuline/`adventices` l.115,
    aulne). Frein en sol riche = `sature_a` (D126) existant.
  - allélopathie : toute émission du champ `allelopathie` lit le gène (règle par variable,
    même endroit) → 6 émettrices sans retoucher leurs données ; l'autotoxicité suit.
  - mycorhization : `fields/ecofields/uptake.myco_effectif(myc, gène) = min(1, myc × gène)`,
    source unique des 4 lecteurs du réseau côté plante : P de `plant_uptake`,
    `facteur_racinaire` (uptake ET `racines.eau_percue`), `qi_local`, `nutrition_plante`.
    Param `mycorhization` de `plant_uptake` passé par la croissance et les conteneurs.
    **Vérifié** : le gain est nul en sol riche (`nutrition_plante` sature à
    `NUTRITION_SEUIL_PLEIN`) ; le prix (`cout_genetique`) est payé partout.
  - Greffe : `portee_graine` suit le greffon ; les 4 autres (racinaires) restent au
    porte-greffe.
- **Écarts au kickoff** : (a) le prix de la portée est lu dans `densite_levable`
  (`fields/seedbank.py`, appelée par `succession.py`), pas dans `succession.py` même :
  même patron que la dormance, et deux côtés (graine lourde = lève mieux) ; (b) **aulne :
  `sature_a` 1,5 ajouté** (il n'avait pas de frein ; hors smoke) ; (c) les numéros de
  ligne du kickoff (`familles.py` ≈ 385/546) avaient dérivé.
- **Golden RE-FIGÉ** `5bfbd8a3…` → `db4d6b7516685b33ba53ddc5fd0cc10107c4d4d74c28adf418c8c258a6eb0d85`.
  1ʳᵉ divergence : **s1**, azote du haricot +0,013 → +0,014, allélopathie du tournesol
  0,080 → 0,061, azote du trèfle 0,011 → 0,010 (gènes des fondateurs). Effet dominant :
  le trèfle fondateur tire `vigueur_clonale` 1,185 → ramets 47 → 68, digest final trèfle
  27 → 42 vivants (dactyle 3 → 2, plantain 3 → 2). Vérifié : `vigueur_clonale` neutralisé
  ⇒ ramets 47, trèfle 27 (comme avant). `population_hash` RE-FIGÉ `9f7f348c…` →
  `84cba4d08d6bb3ea37f51df1f9c60504ca8c108da4c4a2ac94a99ec84a731873`.
- **Population** (`tools/diag_population.py`, `full`, 262 sem. [n=1 seed]) : pic an 2
  hiver 598 → 751, an 3 été 813 → 915, tuile_max 290 → 334 (cap 800 loin) ; an 5 été
  738 → 728, an 6 663 → 658 : pic de trèfle plus haut et plus tôt, puis même plateau.
  Pas d'emballement → pas de dette.
- **Perf** : lectures seules (vigueur_clonale neutralisé, même monde) 4,93 → 4,91 s
  [n=5 paires alternées, VM chargée, bruit ±5 %] ; smoke réel ≈ +15 % [n=4, bruit ±15 %]
  = le trèfle plus nombreux, pas le code.
- **Tests** : `tests/test_caracteres_sol.py` 17/17 (ramets plus nombreux et plus loin,
  héritage gènes + F, graines ÷ gène clonale seulement ; graine posée plus loin sous le
  vent, pool léger lève moins, barochore non lue ; azote ∝ gène et freiné à N 1,2 ;
  allélopathie ∝ gène ; P prélevé ↑, nutrition ↑ en sol pauvre seulement, coût).
  Adaptés : `test_caracteres` (5 entrées), `test_caracteres_feuille` (ordre lu par
  position, plus en queue). Toutes les suites `tests/test_*.py` vertes sauf
  `test_peripherie` 70/71 (rouge avant) ; bancs rouges = les 4 mêmes (grimpe, climatique,
  edaphique, verger_mur).
- Taille : `plants/base/familles.py` **303 LDC** (🟡, 302 avant), `fields/seedbank.py`
  **325** (🟡, 320), `resolution.py` 224, `uptake.py` 69, `instance.py` 262.
- **À valider F5 / arbitrer** : trèfle fondateur à +1,2 σ de clonalité = +45 % de ramets
  (le gène est fort sur la couvre-sol dominante) ; un caractère coûteux (fixation,
  allélopathie, mycorhization) se paie aussi chez une espèce qui ne l'exprime pas
  (sélection vers le neutre, comme `nectar` chez les anémophiles). Pont : 5 caractères
  sans libellé dans la vue G (`genes_pont.py`) → ⑤.

## ⑤ Signes et pont — bilan (2026-11-18)
- **Fait** : `sim/signes_caracteres.py` (pur, une fonction par signe, bornés) : `teinte_fleur`
  [°, sat] (axe d'espèce × `couleur_fleur`, None sans axe), `echelle_fleur` = √taille,
  `contraste_guides` ∈ [0,1], `echelle_fruit` = ∛taille (fruitiers), `matite_feuille` ∈ [0,1]
  (coriacité), `port` ∈ [−1,1] (dominance), `rejets` ∈ [0,1] (0 si non clonale ou immature,
  même `_mature` que l'émission). `sim/fanaison.py` : `sans_graines` = 0 < fécondation < 0,35 ;
  `noter_fanaisons` (HORS tick, pont avant `consigner`) = ligne `🥀 Fané sans graines`, une par
  espèce et par an, cause `sans_graines` (insectes) / `sans_graines_vent` (anémophile).
- **Pont 0.6.20** : plante neuve `signes_car` (constants, même règle que `genes` ; cache ajouté
  dans `core/PontDelta.cs` et le miroir `tests/simserver/delta.py`) ; chaque plante vivante (sol
  et conteneur) `rejets`, `sans_graines`, `fecondation` = {fec, donne, auto} (survol G). Table
  `caracteres` : libellés des 20 caractères + `groupes`. Snapshot comparé avant/après (2 mondes ×
  4 semaines, complet + delta) : seules ces clés s'ajoutent + 15 libellés changent.
- **Survol G** (`WorldView.Genes.cs`) : groupes fleurs / fruits / feuille / gestes / sol /
  chaleur et froid (+ « autres » de repli) ; unités « position » et « goût » en valeur signée
  (fini le « × ») ; ligne « fécondation · pollen donné · autofécondées % » sous la lignée
  (`PlantRenderer.Caracteres.cs`, `PlanteLue.Fecondation`).
- **Voix** : carnet `("fanaison", cause)` → concept pollinisation, 4 gabarits D/I. Goût : la
  note n'est écrite qu'à la **première** bouchée par (espèce, cause) (`gs["gouts_notes"]`).
  Concept **« comestibilité »** (= « goût et défense » du kickoff, nom gardé du ②) entre à
  l'encyclopédie (fiche 3 niveaux, découvert au hook A, crédité par `detecter`) — ferme le point
  ouvert du ②. « Pollinisation guidée » versée dans la fiche **pollinisation** (N3 = guides à
  nectar, ce que voit l'abeille ; N2 = fleur fanée sans visite), pas un concept neuf. « Lignée »
  complétée (père = pollen qui a voyagé, autofécondation faute de visiteurs).
- **Golden INTACT** `db4d6b75…`. Tests : `tests/test_caracteres_signes.py` 31/31 ; `test_*.py`
  verts sauf `test_peripherie` 70/71 (rouge avant) ; bancs : les 4 mêmes rouges. dotnet build vert.
- Taille : `tools/simserver/serialize.py` **322 LDC** (🟡, 311 avant, une seule responsabilité),
  `sim/carnet.py` 299, `sim/actions/gestes.py` 288.
- **Pour ⑥ / F5** : au monde `full`, `sans_graines` touche dès s21 achillée, minette, pissenlit,
  aulne, bouleau, pâturin [n=1 run, 60 sem.] ; la fécondation reste posée jusqu'à la récolte
  d'automne, donc une plante qui fane APRÈS la récolte (trèfle s41) garde le signe jusqu'à
  l'automne suivant — la vue doit le croiser avec la saison / `floraison` (pas de semaine de
  fanaison au moteur). Rejets : 7 → 186 plantes de s22 à s60 (trèfle).

## ⑥ Vue et banc — bilan (2026-11-18)
- **Fait (pure vue C# + un banc, golden INTACT `db4d6b75…`, pont inchangé 0.6.20)** :
  `core/SignesCaracteres.cs` lit `signes_car` ; `PlanteLue` lit aussi `rejets`, `sans_graines` ;
  `PlantRenderer.SetCaracteres` (Caracteres.cs, appelé après SetStructure en pleine terre ET en
  conteneur) pose une **palette d'individu** (`PaletteIndividu()`, remplace la palette d'espèce aux
  27 sites de lecture des partials) : fleur = HSV(teinte arrondie à 10°, saturation à 0,1 ×
  0,75, valeur de l'espèce → blanc chaux quand la saturation tombe), limbe assombri (mat) ou
  éclairci (luisant) par pas de 1/8 de matité. Têtes de port (`PoserTete`) : rayon × √taille en
  fleur, **guides** sur les corolles ouvertes dès ×8 (œil pâle < 0,35, moyen, sombre + 5 lignes
  ≥ 0,65), **tête fanée** brune (terre 2 de la palette maître) × 0,7 ; pompons du trèfle idem.
  Port (Tige, Buisson) : rayon dessiné × (1 − 0,4·port). Rejets : 1 à 5 pousses à 3 brins au
  pied (dès ×4). Recuisson seulement au changement (clé quantifiée), copie vers le pinceau (Bake.cs).
- **« Sans graines » croisé avec la saison** : loquet par pied « vu en fleur depuis le dernier
  hiver », remis à 0 en hiver ; signe = sans_graines ∧ loquet ∧ floraison < 0,5. Limite : un pied
  chargé d'une sauvegarde après sa floraison ne montre pas le signe cette année.
- **Écarts au kickoff** : (a) **pas de quantification sur la palette maître** : elle n'a que 4
  accents de fleur (rouge, jaune, rose, violet) → la bourrache n'aurait que 2 teintes, contraire
  au « dégradé visible » (Q7). Nuancier fini à la place (10°, 0,1), via la palette indexée ;
  (b) **`echelle_fruit` non lu** : la masse des fruits du pont porte déjà `taille_fruit`, la vue la
  dessine (`RayonFruit`) — le relire compterait le gène deux fois ; (c) taille des fleurs et
  guides non branchés sur les fleurs d'ARBRE (pièces d'atlas), seule la couleur l'est.
- **Banc** `bancs/caracteres_vivants.py` (départ s10, survol G ouvert) : 64 fondateurs par
  rangée (`founder_genes`), 8 gardés aux quantiles du caractère montré, rangés gauche → droite :
  bourraches couleur (r0) et guides (r1), phacélies couleur (r3), tomates taille de fruit (r4),
  basilics dominance (r5), fraisiers clonalité (r7). Mesuré à s22 [n=1, seed 42] : bourrache
  242° → 279°, guides 0,24 → 0,74, basilic port −0,48 → +0,55, fraisier rejets 0,15 → 0,62 ;
  phacélie saturation 0,30 → 0,16 (dégradé faible) ; **tomates en fleur sans fruit à s22** (taille
  des fruits à juger plus tard, Turbo) ; 1 basilic et 1 tomate morts avant s22.
- **Captures** : `planche/banc_x8.png`, `planche/bourraches_x16.png` (étoiles violettes à œil,
  survol G). FPS du banc : **0,8 FPS** [VM llvmpipe ×8, n=1, charge ≈ 6] — non représentatif du PC.
- Tests : voir rapport ; `dotnet build` vert. Taille : `Organs.cs` 318 LDC (🟡, 312 avant),
  `Prairie.cs` 301 (🟡, 299), `Caracteres.cs` 134, `PortTetes.cs` 152, `Ports.cs` 201.

## Recette F5 (sprint entier) — banc `caracteres_vivants`, puis monde `full`
1. Banc, ×8 puis ×16 : rangée 0 de la bourrache, la plus bleue à gauche, la plus rose à droite ;
   le dégradé se voit-il d'un pied à l'autre ? Trop cru, trop terne (`SaturationVue` 0,75) ?
2. Rangée 1 : œil pâle à gauche, œil sombre + lignes à droite (dès ×8). Lisible ?
3. Rangée 3 phacélies : lavande → blanc (dégradé faible attendu, saturation de l'axe faible).
4. Rangée 5 basilics : buisson large à gauche, flèche étroite à droite (±40 %). Assez marqué ?
5. Rangée 7 fraisiers : de plus en plus de petites pousses au pied vers la droite.
6. Feuilles : d'un pied à l'autre, plus mates/sombres ou plus claires — visible sans être bruit ?
7. Tomates (r4) : Turbo jusqu'aux fruits ; gros fruits peu nombreux à droite.
8. Survol G : groupes, « couleur sur l'axe », « goût », ligne fécondation · pollen donné · autofécondées.
9. Monde `full`, été-automne : achillée, minette, pissenlit, trèfle aux têtes **brunes rabougries**
   (fané sans graines) ; disparues l'hiver, pas réapparues avant la floraison suivante.
10. Manger une feuille de tomate → « le ventre se noue », note de carnet à la 1ʳᵉ bouchée seulement.
11. Carnet : « a fané sans graines » ; encyclopédie : concept « comestibilité », pollinisation N3.
12. Calibrages ①-④ à juger (cf. §REPRISE).

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
**Sprint CLOS côté code** (①→⑥ commités, golden INTACT `db4d6b75…`, pont 0.6.20) → **F5 de Nico**
(recette ci-dessus). D139 close côté code (DETTE/BACKLOG mis à jour). Points à arbitrer au F5 :
`RESSEMIS_DENSITE_REF` (①d), extinction des annuelles ressemées sous la flore férale, mode de
pollinisation du pâturin annuel, pollen déposé/crédité après la fanaison, calibrage du goût (②),
dominance sans « fleurs latérales » et repousse non lue par la récolte (③), trèfle très clonal et
coût payé par les espèces qui n'expriment pas le caractère (④), nuancier de fleurs hors palette
maître et `echelle_fruit` non lu (⑥).

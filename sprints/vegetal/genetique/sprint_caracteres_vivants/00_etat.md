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
Départ = hash de fin du sprint ②. ①-④ **RE-FIGÉ annoncé** chacun (clés neuves + lecteurs)
· ⑤ INTACT · ⑥ INTACT.

## Tronçons
| # | Kickoff | État |
|---|---|---|
| ① | `01_fleurs.md` — taille, nectar, pollen, couleur, guides, parfum + `cout_genetique` | **FAIT côté code** (2026-11-18, non commité) — voir §① |
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

## REPRISE
Lire `CLAUDE.md`, ce fichier, puis le kickoff du premier tronçon « à faire » (②).
**Avant ②** : trancher le trou de conception du ① (fitness des fleurs herbacées).

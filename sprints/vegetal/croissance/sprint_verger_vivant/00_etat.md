# Sprint VERGER VIVANT (D129) — état

**Conception figée le 2026-11-05** : `docs/vegetal/croissance/conception_verger_vivant.md`. 4 tronçons, à exécuter par `/sprint-auto sprint_verger_vivant`. Golden `a10b7225…` attendu intact partout, aucun re-figeage prévu.

## Tronçons

| # | Kickoff | État |
|---|---|---|
| ① | `01_bourgeons_dormants.md` | **fait** (non commité, golden intact) |
| ② | `02_floraison_realiste.md` | à faire |
| ③ | `03_fruits_cohortes.md` | à faire |
| ④ | `04_vue_fleurs_fruits.md` | à faire |

## Décisions (Nico, 2026-11-05)

1. Bourgeons dormants : réveil quand la couronne est sous son plafond, arbre vivant et éclairé, après toute perte.
2. Limites de fruits relevées **dans le moteur** (cohortes avec un nombre).
3. Noyer : dose anémophile recalibrée, après correction de sa floraison.
4. Fleurs nombreuses et belles, densité continue dans la vue.
5. Floraison réaliste dans le moteur (ordre, date, durée, pic).

## Constats de départ (2026-11-05, HEAD `b55ee3f`, patchs mémoire)

- Déclin : un seul `has_bud` par segment, jamais renouvelé ; sans tempête, sans neige et sans ombre, les arbres restent au plafond [`verger_mur`, seed 42, n=1 run par variante, 5 ans, VM].
- Patch brut (un bourgeon toutes les 4 semaines, sous 85 % du plafond) : cerisier de `full` an 5, 17 segments, 1 apex, 4 fruits → 34, 17, 10 ; tick médian 1 017 → 1 051 ms [`full`, seed 42, n=1 run par côté, VM, charge < 1] ; golden identique [smoke].
- Banc trop serré : pommier à 0,23-0,35 de lumière, mort en an 4 même avec le patch [`verger_mur`, n=1 run].
- Noyer : `pollen_recu` 0,01 à 0,41 par an ; floraison s11-s17 [mêmes conditions].
- Fleurs : pic 0,73 ; vue en tout ou rien à 0,5.
- Hors sprint : humidité du sol en hausse (2,5 à 2,8), asphyxie des aulnes de `full` → D127.

## §REPRISE

`/sprint-auto sprint_verger_vivant` : ① fait (à commiter par l'orchestrateur), **reprendre au ②** (`02_floraison_realiste.md`). Chaque tronçon met à jour ce tableau et ajoute son bilan ci-dessous.

## Bilans

### ① Bourgeons dormants + banc espacé (2026-11-06)

**Code** : `sim/growth/dormance.py` (neuf, 51 LDC) — `peut_reveiller` (vitalité > 0, couronne < 85 % de `max_segments`, fenêtre d'1 semaine sur 4 déphasée par `form_seed`) puis `reveiller_bourgeon` (remet `has_bud` sur UN segment : collet exclu, ni apex ni bourgeon, auxine sous le seuil, choix par `_hash_noise(form_seed, semaine, indice)`). Branché dans `grow_plant` (`phases.py`, 184 LDC) entre l'élongation et `_debourrement`, ligneux procéduraux seuls, hors hiver. Pur, sans `eco`, imports dans `sim/growth` seulement.
**Gate anti-boucle** : lumière LOCALE au point de réveil (lumière de la plante × transmission des grappes plus hautes, formule de `lumiere_pointes`) ≥ 1,5 × seuil de cladoptose de l'arbre. Mesure, ancien banc serré, réveil en jeu ON/OFF sur le même arbre de départ : cladoptoses/an pommier ombragé (0,27-0,33 de lumière) 7/7/3/1 dans les deux cas, figuier (0,29) 6/7/7/5 dans les deux cas [seed 42, n=1 run par côté, 5 ans, VM] → aucune boucle casse-repousse.
**Pré-croissance** : la dormance s'y applique (même `grow_plant`, plein soleil) → les arbres de départ changent : pommier de `full` 47 segments/20 apex → 70/35, cerisier 70/27 → 69/30 [seed 42, n=1, VM]. Choix : même port qu'en jeu (couper la dormance en pré-croissance demanderait un drapeau dans `grow_plant`).
**Banc `verger_mur`** : tuile 40×40 (monde entier). Cerisier, pommier, figuier au sud de la maison à 8 m les uns des autres ; deux noyers au nord-est côte à côte, 4,5 m (pollen 600 cm). Lumière s10-s35 : pommier 0,94-0,98 (avant 0,27-0,32), figuier 1,0 (avant 0,29-0,34), cerisier 0,98-1,0 ; noyers 0,64-0,83 [seed 42, n=1 run, 5 ans, VM]. Oracle `test_verger_mur` vert (noyer : 5,25 de fruits tombés contre 2,85). Tick du banc ~500 ms (avant ~180 : tuile 3,3× plus grande).
**Effet, `verger_mur`** (segments/apex/fruits max de l'an, an 1→5) [seed 42, n=1 run, VM] :
- avant : cerisier 64/23/9 → 12/1/1 ; pommier mort an 4 ; figuier 41→10 segments, vitalité 0,47 ; noyers 1-3 fruits.
- après : cerisier 58/19/8 → 39/15/10 ; pommier 56→54 segments, 9 fruits/an, vivant ; figuier 74→90 segments, 10 fruits/an ; noyers 41→21 et 60→18 segments, 4-8 fruits/an.
**Effet, `full`** : cerisier an 5 17 segments/1 apex/4 fruits → 38/13/10 ; pommier 55/14/10 → 60/24/9 [seed 42, n=1 run par côté, VM].
**Tick médian `full`** (ms, an 1→5) : avant 549/889/1073/1100/988, après 552/918/1132/1117/1006, soit +0 à +5 % [seed 42, n=1 run par côté lancés en parallèle, VM, charge 2-4 sur 16 cœurs]. Couronnes plus fournies = plus de segments à éclairer.
**Suites** : golden `a10b7225…` INTACT ; `test_croissance` 134/134, `test_bois_mort` 42/42, `test_dormance` (neuf) 7/7, `test_verger_mur`, `test_phototropisme`, `test_competition`, `test_quetes`, `test_grimpe`, `test_desync_phenologie`, `test_fruits`, `test_squelette_herbacees`, bancs grimpe/planche/liane : verts. Pas de C#.
**Reste / à savoir** : les noyers du banc fondent encore, par le VENT (102 segments cassés en 3 ans pour les deux, contre 25 par l'ombre [n=1 run]) : coin nord-est exposé, `CASSE_*` hors périmètre. Un bourgeon par 4 semaines ne suit pas une tempête. À regarder au ② (noyer) ou en dette si Nico veut un verger abrité.

# ② Moteur — tick an 2 plus léger, BIT-IDENTIQUE

**Lire d'abord** : `CLAUDE.md`, `00_etat.md` (référence ① = baseline), le doc de conception.
**Golden** : **INCHANGÉ** `fecccded…` — exigence absolue. Toute optimisation qui bouge le hash
est **abandonnée** (pas re-figée). Suites ciblées vertes (`tests/`), sauf `test_epaisseur_500ans`
(NE JAMAIS lancer).

## Objectif
**−20 % sur le tick moyen an 2** [VM, `tools/banc_cadence.py`, n ≥ 3 runs, graine 1521550718,
`full`], **à population identique** (bit-identique ⇒ même monde). Ne pas brider la population.

## Carte de départ (cProfile s88, 584 plantes, HEAD `5c69ac6`) [n=1 run, 3 ticks]
Part du tick (cumulé, appelés directement par `tick_semaine`) : `tick_populations` 17 %
(`fields/ecofields/vie_macro.py`) · `apply_disturbances` 11 % (`sim/effects/perturbations.py`)
· `tick_light` 10 % · `grow_plant` 8 % · `_apply_uptake` 7 % · `tick_soil_memory` 6 % ·
`succession` 4 % · `_update_physiology` 4 % · `tick_seed_bank` 3 % · `tick_decomposition` 3 %.
Temps propre : `field.tick` (diffusion des champs) en tête ; `PlantInstance.is_alive`
(propriété `vitalite > 0`) ~200 k appels/tick ; `grids.at_plot` ~210 k ; `sum` builtin.
**Re-profiler d'abord** (`tools/profile_monde.py --week 90 --seed 1521550718`, et le script de
phases décrit ci-dessous) : la carte a pu bouger avec le ①.

Profil par phase : cProfile autour de N ticks, puis pour chaque fonction dont les appelants
contiennent `tick_semaine`, lire le cumul de cet appel (`pstats.Stats(...).stats[f][4]`).
Le recopier en `data/code/tools/profile_phases.py` (petit outil, lecture seule).

## Leviers pressentis (INTENTION — placement à vérifier au code)
- **`_local_density` / `_spore_load`** (`sim/effects/perturbations.py`) : pour chaque plante
  testée, on parcourt encore TOUTES les plantes de la tuile (`for p in tile.plants … if
  p.position in voisinage`) → O(N²) par tuile. Indexer les plantes vivantes par plot UNE fois
  par appel de phase, en **conservant l'ordre de `tile.plants`** (l'ordre des sommes flottantes
  fait le bit-identique).
- **Recalculs dans le tick** (règle projet : jamais recalculer ce qui l'a déjà été — mémoïser
  avec une clé auto-invalidante) : listes « plantes vivantes » refiltrées par plusieurs
  phases, `at_plot` répété sur le même plot dans une boucle.
- **`tick_populations` / `field.tick`** : coût borné aux plots (pas aux plantes) ; chercher les
  travaux répétés par guilde (listes de prédateurs, voisinages hexagonaux recalculés).
- Toute réécriture d'une somme doit garder **le même ordre d'addition** (flottants).

## Ne PAS faire
- Changer une formule, un seuil, une constante, ou l'ordre des phases du tick.
- Passer à numpy (absent de la VM et du packaging).
- Toucher au pont ou à la vue (③/④).

## Fin de tronçon
Golden INCHANGÉ ; suites `tests/` concernées vertes ; mesure avant/après au banc ① (n ≥ 3
runs, charge < 4) consignée dans `00_etat.md` avec ses limites ; si un levier touche un fichier
au-delà de 300 LDC (`tools/compte_ldc.py`), le signaler ; commit.

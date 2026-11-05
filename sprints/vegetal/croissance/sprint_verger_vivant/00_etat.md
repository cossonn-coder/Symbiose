# Sprint VERGER VIVANT (D129) — état

**Conception figée le 2026-11-05** : `docs/vegetal/croissance/conception_verger_vivant.md`. 4 tronçons, à exécuter par `/sprint-auto sprint_verger_vivant`. Golden `a10b7225…` attendu intact partout, aucun re-figeage prévu.

## Tronçons

| # | Kickoff | État |
|---|---|---|
| ① | `01_bourgeons_dormants.md` | à faire |
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

`/sprint-auto sprint_verger_vivant` : tronçon ① d'abord. Chaque tronçon met à jour ce tableau et ajoute son bilan ci-dessous.

## Bilans

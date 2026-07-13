# ④ AUTOTOXICITÉ / fatigue du sol

> Kickoff autosuffisant. Reprise à froid = `CLAUDE.md` + `00_etat.md` + ce fichier
> + `CONCEPTION_ALLELOPATHIE.md` §D. Prérequis : ①②③ faits. Golden **RE-FIGÉ
> MAÎTRISÉ — ANNONCÉ** (touche la monoculture du smoke).

## Objectif

La pépite pédagogique permaculture : une **monoculture répétée s'empoisonne**. Quand
la **même espèce émettrice** ré-occupe un plot saison après saison sans rotation, un
accumulateur `autotox` monte et **alimente l'inhibition** (niche/croissance) de cette
même espèce sur ce plot. La **rotation** (autre espèce / sol nu) fait retomber
`autotox` → le sol « se repose ». `soil_memory` ne trace PAS l'espèce (mémoire de
fertilité fast/deep, vérifié `sol.py`) → il faut un **traceur d'espèce séparé**.

## Fichiers à toucher

- `fields/ecofields/container.py` — champ **`autotox`** (`GridField`) + traceur léger
  d'**identité d'espèce récurrente par plot** (clé espèce/famille de l'occupant +
  compteur). ⚠️ garde-fou RAM : dimensionner léger (un champ float + une clé par
  plot, ou petit dict creux), pas une structure lourde. ⚠️ taille fichier :
  `container.py` déjà proche du seuil → scinder si dépassement.
- `fields/ecofields/sol.py` (tick sol) — montée de `autotox` quand l'espèce
  émettrice récurrente occupe le plot ; **redescente** à la rotation / sol nu ;
  résorption **accélérée par microbiome/mycélium** (cohérent §A.3).
- `fields/seedbank.py` (②) et `sim/growth.py` (③) — faire **lire `autotox`** comme
  terme additionnel de l'inhibition **pour la même espèce** : soit `autotox` alimente
  `allelopathie` lu par ces points, soit terme dédié `f_autotox`. Préférence :
  alimenter le champ `allelopathie` effectif vu par l'espèce fatigante (surgical,
  réutilise ②③).

## Modèle

- Montée : `autotox[r,c] += K_MONTEE` par saison où l'espèce émettrice E récurrente
  occupe le plot (clé espèce stable). Redescente : `autotox[r,c] *= (1 − K_REPOS −
  K_MICROBE · microbiome[r,c])` sinon. Bornés, placeholders calibrage.
- L'effet ne frappe que **l'espèce traceée** (spécificité de la fatigue) : rotation
  = échappatoire lisible.

## Golden attendu

**RE-FIGÉ MAÎTRISÉ — ANNONCÉ.** Le smoke porte des successions/monocultures locales
→ `autotox` peut modifier la levée/croissance sur plots ré-occupés. **Invariant
dur** : à `autotox = 0` partout (rotation parfaite / traceur neutralisé), germination
ET croissance **strictement identiques au pré-④** → toute dérive est attribuable au
**seul** traceur d'autotoxicité. Procédure : lancer `python3 -m tests.test_golden`,
constater la dérive, **vérifier qu'elle disparaît** en forçant `autotox=0` (preuve
d'isolation), puis **re-figer** et **consigner le nouveau hash** dans `00_etat.md`
avec la raison. `/sprint-auto` accepte ce re-figeage **parce qu'il est annoncé ici**.

## Ce qu'il NE faut PAS faire

- Ne PAS tracer l'espèce dans `soil_memory` (mémoire de fertilité, ne pas polluer).
- Ne PAS re-figer sans avoir prouvé l'isolation (dérive nulle à `autotox=0`).
- Ne PAS rendre la fatigue non spécifique (elle ne frappe QUE l'espèce récurrente).
- Ne JAMAIS lancer `test_epaisseur_500ans`.

## Vérif

Golden re-figé isolé + test ad hoc : simuler N saisons de monoculture d'un émetteur
sur un plot → `autotox` monte, levée/croissance de l'espèce s'effondrent ; introduire
une rotation → `autotox` retombe, le plot redevient accueillant.

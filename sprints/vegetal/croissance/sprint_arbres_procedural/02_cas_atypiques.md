# T2 — Cas atypiques : aulne, figuier, sapin

**Sprint :** migration des 9 arbres en croissance procédurale (D91).
**Doc de conception :** `docs/vegetal/croissance/conception_migration_arbres.md` (§4, §5, §7).
**Prérequis :** T1 clos (levier `auxin_release_scale` en place, défauts procéduraux
d'arbre sur `PerennialWoody`).
**Golden attendu : INCHANGÉ** (`57c166d8…`). Ne PAS re-figer.

## Objectif
Migrer les 3 arbres à comportement particulier, en réutilisant le levier et les
défauts posés en T1 :
- **Aulne** (`Alder`) — `etale` élancé, **rôle hydrologique D61 à préserver**.
- **Figuier** (`Fig`) — `buissonnant`, bas & large, **mono-collet** (multi-tronc
  reporté en option F5).
- **Sapin** (`FirTree`) — `fleche` conifère, persistant, **survie hydrique critique**.

## Contexte technique
- Ces 3 classes sont dans `data/code/plants/perennials.py` : `Fig` (126),
  `FirTree` (366), `Alder` (405). Chacune a déjà `girth_max_cm` posé + `age_curve`.
- `port_archetype` est **descriptif** (jamais lu par la sim) : le port vient de
  `apical_dominance_base` + `auxin_release_scale`. `buissonnant` = dominance
  **modérée** (débourrement précoce) ; `fleche` = dominance **haute** + release long.
- **Aulne D61** : porte `family_effects` (fixation N₂ Frankia, lignes 452-459) et
  `asphyxie_tolerance_base=3.0` — **indépendants de la morphologie** ; la migration
  n'y touche pas, mais vérifier la non-régression (le rôle hydro reste actif).
- **Sapin D69** : `deciduous=False` (persistant, ombre hivernale), `mulch_source`,
  `ph_opt` — **inchangés**. Attention `foliage_halfwidth` : une flèche étroite de
  conifère est le cas **le plus exposé** à la mort hydrique (§1.3 du doc).

## Fichiers à toucher
- `data/code/plants/perennials.py` — profils de `Alder`, `Fig`, `FirTree`.
- `data/code/tests/` — compléter le test de croissance libre (sapin au moins).

## Étape — migrer les 3 espèces
Ajouter à chaque classe (sur la base des défauts T1) :

**Aulne (`Alder`)** — `etale`, pionnier élancé de berge :
```python
procedural_growth   = True
growth_speed        = <calibré, croissance rapide de pionnier>
max_height_cm       = <cible age_curve>
max_extent_cm       = <cible age_curve — houppier moyen>
auxin_release_scale = <plus petit que le chêne : pionnier qui s'étale vite>
```
Vérifier après migration que la fixation N₂ (`family_effects` inject_field "n")
s'applique toujours sur l'empreinte racinaire dérivée (cible "local").

**Figuier (`Fig`)** — `buissonnant`, bas & large :
```python
procedural_growth     = True
port_archetype        = "buissonnant"
apical_dominance_base = <MODÉRÉ, < 2.0 : débourre volontiers → ramifie bas>
growth_speed          = <calibré, bas et large>
max_height_cm         = <bas — age_curve figuier plafonne ~500>
max_extent_cm         = <large — étalement marqué>
```
**Mono-collet** : ne PAS tenter le multi-tronc (structure initiale = un seul
`Segment(parent=None)`, instance.py:187). Le port bas-ramifié doit lire correctement
avec une dominance modérée. Consigner dans `00_etat.md` : « multi-tronc figuier =
option F5 différée si le port mono-collet lit mal » (amorce « moindre urgence »).

**Sapin (`FirTree`)** — `fleche`, dominance haute :
```python
procedural_growth     = True
port_archetype        = "fleche"
apical_dominance_base = <HAUT, ex. 2.5-3.0 : flèche tenue → port conique>
auxin_release_scale   = <LONG : reste dressé longtemps (conifère)>
growth_speed          = <lent — le sapin pousse lentement>
max_height_cm         = <grand, étroit>
max_extent_cm         = <ÉTROIT — houppier serré>
foliage_halfwidth     = <AUGMENTER si la sonde révèle une mort hydrique jeune :
                         flèche étroite → racines étroites → assèchement>
```
> **Aiguilles + phyllotaxie verticillée = HORS T2** : ce sont des concerns de
> **rendu** (T4). Ici on règle seulement le **port** (flèche conique). Une flèche
> dense lit déjà « conifère » ; la vraie verticille est laissée en polish différé.

## Méthode de calibrage
Identique à T1 : sonde de croissance libre (`growth_factor=1.0`, cycle saisonnier,
~520 ticks), viser l'allure de l'`age_curve` au point ~10 ans, vérifier montée
monotone bornée et **pas de mort hydrique précoce** (surveiller le sapin en
priorité). Placeholders → F5 (Nico affine au T4).

## Ce qu'il NE faut PAS faire
- Ne PAS implémenter le multi-tronc figuier (option F5, pas de sur-ingénierie #2).
- Ne PAS dessiner d'aiguilles ni de verticille ici (T4, rendu).
- Ne PAS toucher aux `family_effects` de l'aulne, ni à `deciduous`/`mulch_source`
  du sapin, ni aux rôles écologiques D61/D69.
- Ne PAS toucher le bouleau (T3).
- Ne PAS re-figer le golden (les 3 espèces sont hors scénario).

## Tests / vérification
- **Golden** : `python3 -m tests.test_golden` → **INCHANGÉ**.
- Test de croissance libre : sapin (flèche bornée, étroite), figuier (bas, large,
  ramifié), aulne (élancé) — déterminisme + bornage.
- Vérifier que l'aulne enrichit toujours le N local (test ciblé existant s'il y en
  a un, sinon assertion simple sur `family_effects` inchangés).
- **Ne PAS** lancer `test_epaisseur_500ans`.

## Mise à jour en fin de tronçon
- `00_etat.md` : cocher T2, valeurs retenues, note multi-tronc figuier différé,
  hash golden inchangé, reste (T3).
- Commit : `feat(arbres ②) : aulne + figuier buissonnant + sapin flèche migrés (D91)`.

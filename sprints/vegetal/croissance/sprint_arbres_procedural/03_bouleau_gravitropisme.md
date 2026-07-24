# T3 — Bouleau + levier gravitropique (port pleureur)

**Sprint :** migration des 9 arbres en croissance procédurale (D91).
**Doc de conception :** `docs/vegetal/croissance/conception_migration_arbres.md` (§3, §7).
**Prérequis :** T1 + T2 clos.
**Golden attendu : INCHANGÉ** (`57c166d8…`). Ne PAS re-figer.

## Objectif
1. Ajouter le levier **gravitropique** `gravitropism_gain` (moteur) — le port
   pleureur exige une **force mécanique**, pas un simple nom d'archétype (§1.2/§3).
2. Migrer le **bouleau** (`BirchTree`) : `fleche` élancé + rameaux distaux qui
   **retombent** = *Betula pendula*.

## Contexte technique (établi par lecture du code)
- `port_archetype` n'est **jamais lu** par la sim → « archétype pleureur » comme
  string ne ferait rien. Il faut un vrai biais géométrique.
- Dans `_elongate_emit` (sim/growth/phases.py:46), le segment émis reçoit sa
  direction via `_phototropic_bias` (phases.py:78) :
  ```python
  new_dir = _phototropic_bias(s.dir, tip[0], tip[1], light_field, strength, z_floor)
  new_segs.append(_mk(i, tip, new_dir, s.auxin))
  ```
- Les helpers géométriques vivent dans `sim/growth/geometrie.py`
  (`_phototropic_bias`, `_lateral_dir`, `_depths`, …). `_depths(segs)` donne la
  profondeur de chaque segment (déjà utilisé par `_update_auxin`).
- **Déterminisme (philo #3)** : le biais gravitropique est **géométrique pur**
  (aucun `_hash_noise`, aucun RNG).

## Fichiers à toucher
- `data/code/sim/growth/geometrie.py` — helper neuf `_gravitropic_droop`.
- `data/code/sim/growth/phases.py` — appel dans `_elongate_emit`.
- `data/code/plants/base/familles.py` — attribut `gravitropism_gain`.
- `data/code/plants/perennials.py` — profil du bouleau.
- `data/code/tests/` — test du pleureur (voir §Tests).

## Étape 1 — attribut `gravitropism_gain` (défaut neutre)
Sur `PlantBase` (familles.py, à côté de `phototropism_strength`) :
```python
gravitropism_gain: float = 0.0  # retombée des rameaux sous leur poids (port
# pleureur, ex. bouleau/saule). 0 = aucune retombée → golden intact (personne ne
# le règle sauf le bouleau). >0 = les rameaux DISTAUX ploient vers le bas.
```

## Étape 2 — helper `_gravitropic_droop` (geometrie.py)
Un helper pur qui incline une direction vers le bas, **échelonné par la
profondeur** (le tronc/flèche à faible depth NE ploie PAS ; seuls les rameaux
distaux ploient) :
```python
def _gravitropic_droop(d: tuple, depth: int, gain: float) -> tuple:
    """Retombée gravitropique : incline `d` vers le bas (0,0,-1) proportionnellement
    à `gain` et à la profondeur `depth` du segment porteur (distal ploie, tronc non).
    Biais géométrique pur, déterministe. gain=0 → d inchangé (renvoyé tel quel)."""
    if gain <= 0.0 or depth <= 0:
        return d
    # poids croissant avec la profondeur, borné : w ∈ [0, 1)
    w = gain * (1.0 - 1.0 / (1.0 + depth))
    # blend vers le bas puis renormalisation (comme _phototropic_bias)
    ...
    return dir_normalisée
```
> Calibrer la forme exacte du poids au F5 ; l'important est : **borné**, **croissant
> avec depth**, **nul à depth 0** (tronc dressé), et une **renormalisation** pour
> garder un vecteur direction unitaire. S'aligner sur le style de `_phototropic_bias`
> (même convention de normalisation).

## Étape 3 — greffe dans `_elongate_emit`
Le caller doit connaître la profondeur du segment porteur `s`. `_depths(segs)` est
déjà importable ; le calculer une fois en tête de `_elongate_emit` (comme
`_update_auxin` le fait), passer `gain = cls.gravitropism_gain` en paramètre de
`_elongate_emit` (via `grow_plant`, comme les autres leviers de profil), puis :
```python
new_dir = _phototropic_bias(s.dir, tip[0], tip[1], light_field, strength, z_floor)
new_dir = _gravitropic_droop(new_dir, depth[i], gain)   # retombée APRÈS phototropisme
new_segs.append(_mk(i, tip, new_dir, s.auxin))
```
**Ordre impératif** : axial → phototropisme → gravitropisme. La retombée ne doit
pas écraser la recherche de lumière (le rameau pousse vers le clair PUIS ploie).
`gain=0` → `new_dir` inchangé → **golden bit-identique** pour toutes les espèces.

## Étape 4 — profil du bouleau (`BirchTree`, perennials.py:315)
```python
procedural_growth   = True
port_archetype      = "fleche"
apical_dominance_base = <flèche élancée — leader net>
auxin_release_scale = <COURT : pionnier, cime légère>
growth_speed        = <RAPIDE — croissance de pionnier>
max_height_cm       = <haut>
max_extent_cm       = <grêle — houppier léger, foliage_density déjà 0.45>
gravitropism_gain   = <> 0 : rameaux distaux pendants (calibrer au F5)>
foliage_halfwidth   = <surveiller la survie hydrique : bouleau grêle = exposé>
```

## Ce qu'il NE faut PAS faire
- Ne PAS utiliser de RNG dans la retombée (biais géométrique pur, #3).
- Ne PAS faire ploier le tronc/la flèche (depth 0) — seuls les rameaux distaux.
- Ne PAS régler `gravitropism_gain` sur une autre espèce (bouleau seul ; prépare le
  saule D23 mais le saule n'est pas dans ce sprint).
- Ne PAS re-figer le golden (défaut 0 + bouleau hors scénario).

## Tests / vérification
- **Golden** : `python3 -m tests.test_golden` → **INCHANGÉ**.
- Test unitaire `_gravitropic_droop` : `gain=0` renvoie `d` inchangé ; `gain>0`
  incline vers le bas (composante z du résultat < composante z d'entrée) ; vecteur
  résultat normalisé ; `depth=0` → inchangé.
- Test croissance libre bouleau : la structure a des **extrémités plus basses que
  leur point d'insertion** (retombée) tout en gardant une flèche montante ;
  déterminisme (deux runs identiques) ; bornage.
- **Ne PAS** lancer `test_epaisseur_500ans`.

## Mise à jour en fin de tronçon
- `00_etat.md` : cocher T3, valeur `gravitropism_gain` retenue, hash golden inchangé,
  reste (T4 vue).
- Commit : `feat(arbres ③) : levier gravitropique + bouleau pleureur (D91)`.

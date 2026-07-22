# Tronçon ② — Identité morphologique héritable (`form_seed`)

> Kickoff autosuffisant. Lis `CLAUDE.md` (racine) + `00_etat.md` (ce dossier) +
> `docs/rendu/spatial/conception_modele_spatial.md` (§2), puis exécute.
> Lancement des tests depuis `data/code/`. **Le tronçon ① est fait** (les plantes
> germées ont déjà une position sous-plot / au pixel cliqué).

## Objectif
Un clone doit **ressembler** à sa mère : partager le patron de branches. On donne
à chaque plante une identité morphologique `form_seed` **héritée par le clone**,
et la morphogénèse tire ses angles de branches à partir de cette identité (au lieu
de la position + semaine, qui décorrélait tout).

## Principe (NE PAS dévier)
- **Déterministe** (philo #3), aucun `random`.
- Ressemblance ≠ copie conforme : deux clones partagent le patron mais **divergent
  finement** par la lumière/phototropisme local (déjà géré ailleurs dans
  `grow_plant` — NE PAS y toucher). Le seul aléa qu'on rend héritable est le
  **débourrement** (`_debourrement`).
- **Pas de coup de pouce d'établissement** (décision Nico) : le ramet reste
  juvénile (stade 0). On ne change RIEN à sa vigueur/stade de naissance.

## A. Deux champs sur `PlantInstance`
Fichier `plants/base/instance.py`, dataclass `PlantInstance` (près des autres
champs d'état, ex. après `expression`) :
```
form_seed: int = 0        # identité morphologique héritable ; 0 = non posé (repli)
branch_count: int = 0     # ordinal monotone de branches émises (index stable du patron)
```
Ni l'un ni l'autre dans `_PLANT_ATTRS` du golden (ils agissent via les `segments`,
qui sont déjà comparés).

## B. Fabrique d'identité (couche basse, réutilisable)
Fichier `fields/noise.py`, à côté de `_hash_noise` :
```
def form_seed_at(seed: int, x_cm: float, y_cm: float, week: int) -> int:
    """Identité morphologique déterministe, ENTIÈRE et NON NULLE (0 = 'non posé').
    Sert de graine au patron de branches ; héritée telle quelle par les clones."""
    u = _hash_noise(seed, week, int(x_cm), int(y_cm))
    return int(u * 1_000_003) + 1
```
Exporte-la si `fields/__init__.py` liste explicitement les symboles réexportés
(vérifie : `_hash_noise` y est déjà — ajoute `form_seed_at` au même endroit).

## C. Poser l'identité à la naissance
Fichier `sim/succession.py`, aux DEUX sites de levée (déjà modifiés au tronçon ①,
la position y est posée) :
- levée d'un grain planté (`_lever_grains_en_attente`, après avoir posé
  `new_plant.x_cm,y_cm`) ;
- germination férale (`succession`, après `_offset_subplot(...)`).
Dans les deux cas, juste après la position :
```
new_plant.form_seed = form_seed_at(seed, new_plant.x_cm, new_plant.y_cm, week)
```
(importe `form_seed_at` depuis `fields`.)

## D. Le clone HÉRITE
Fichier `sim/clonal.py`, dans `emettre_ramets`, là où le ramet copie déjà la mère
(~ligne 148-149 : `ramet.genes = dict(mother.genes)` /
`ramet.expression.update(...)`), ajoute :
```
ramet.form_seed = mother.form_seed      # air de famille : même patron de branches
```
(`branch_count` reste 0 : le ramet REJOUE la séquence depuis le début → sa
branche k tire le même angle que la branche k de la mère.)

## E. La morphogénèse lit l'identité (cœur du tronçon)
Fichier `sim/growth/phases.py`, fonction `_debourrement` (lignes 84-100).
Remplacer l'amorçage par la position (`bx,by` + `week`) par l'identité + ordinal :
```
def _debourrement(plant, seed, week, branch_angle, dominance):
    segs = plant.segments
    fs = plant.form_seed or form_seed_at(0, plant.x_cm, plant.y_cm, 0)   # repli robuste
    new_segs = []
    for i, s in enumerate(list(segs)):
        if s.is_apex or not s.has_bud or s.auxin >= AUXIN_INHIB_THRESHOLD:
            continue
        k = plant.branch_count            # ordinal STABLE, pas la semaine
        plant.branch_count += 1
        phi = _hash_noise(fs, 0, k, 0) * 2.0 * math.pi
        jit = (_hash_noise(fs, 0, k, 1) - 0.5) * JITTER_RAD
        ldir = _lateral_dir(s.dir, branch_angle + jit, phi)
        s.has_bud = False
        new_segs.append(_mk(i, _tip(s), ldir, dominance))
    segs.extend(new_segs)
```
Notes :
- On DROPPE `week` de l'aléa de branche : c'était lui qui décorrélait mère/clone
  (le ramet débourre à d'autres semaines). L'ordinal `branch_count` fixe l'angle
  de la k-ième branche indépendamment du calendrier.
- `seed`/`week` deviennent inutilisés DANS `_debourrement` : garde les paramètres
  (le caller `grow_plant` les passe) — ne change pas la signature.
- Ajoute `from fields import _hash_noise, form_seed_at` en tête (l'import
  `_hash_noise` existe déjà, ligne 15).

## Golden (RE-FIGÉ — annoncé)
Change les entrées du hash de débourrement pour TOUTES les plantes → silhouettes
reseed → le smoke dérive. **Re-fige attendu et maîtrisé** (cause unique : amorçage
morphologique). Procédure identique au tronçon ① :
1. `python3 -m tests.test_golden` (échoue).
2. Sanity : silhouettes plausibles (pas de segments dégénérés, `branch_count`
   croît, pas d'explosion mémoire — `MAX_SEGMENTS` borne toujours).
3. Re-fige le golden + note la nouvelle empreinte dans `00_etat.md`.
4. Relance les suites ciblées (`tests/`) — en particulier tout test de croissance
   procédurale ; re-fige celles qui dépendent des angles de branches, en le notant.

## NE PAS faire
- Ne pas toucher le phototropisme / l'intégration lumière de `grow_plant` (c'est
  la divergence VOULUE entre clones).
- Ne pas donner de stade/segments d'avance au ramet.
- Ne pas mettre `form_seed`/`branch_count` dans `_PLANT_ATTRS`.
- Ne pas réintroduire `week` dans l'aléa de branche.

## Aparté (hors scope, à noter seulement)
Quand le save JSON arrivera, `branch_count` devra être sérialisé avec la structure
(sinon une plante rechargée re-tire ses futures branches sur un compteur remis à
0). Le save n'existe pas encore → juste une ligne dans `00_etat.md`, aucune action.

## Fin de tronçon
Mets à jour `00_etat.md` (§REPRISE + nouvelle empreinte golden), commit. Tronçon
③ (banc + vue) ensuite.

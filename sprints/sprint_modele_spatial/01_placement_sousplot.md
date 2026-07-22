# Tronçon ① — Placement sous-plot (pixel cliqué + offset féral)

> Kickoff autosuffisant. Lis `CLAUDE.md` (racine) + `00_etat.md` (ce dossier) +
> `docs/rendu/spatial/conception_modele_spatial.md` (§0 et §1), puis exécute.
> Lancement des tests depuis `data/code/`.

## Objectif
Que les plantes GERMÉES ne naissent plus au **centre du plot** :
- **plantée par le joueur** → au **PIXEL CLIQUÉ EXACT** ;
- **férale** (succession spontanée) → à un **offset déterministe** dans le plot.
Le `plot_foyer` reste le plot cible dans les deux cas (chimie stable).

## Principe (NE PAS dévier)
- **Déterministe** (philo #3) : offset via `_hash_noise` (`fields/noise.py:16`,
  signature `_hash_noise(seed, week, r, c) -> float ∈ [0,1)`). **Aucun `random`.**
- On ne touche PAS `add_plant` (`world/tile.py`) ni `__post_init__` : ils
  continuent de centrer par défaut. On **écrase** `x_cm,y_cm` juste APRÈS
  `add_plant`, aux sites de levée (comme on y écrit déjà `genes`).
- Les **clones** (`sim/clonal.py`) posent DÉJÀ une position continue → **ne pas
  y toucher**.
- `PLOT_CM` vient de `constants.py`. `OFFSET_MIN = 10.0` cm.

## A. Le grain porte le pixel cliqué
Fichier `fields/seedbank.py`, dataclass `GrainEnAttente` (~ligne 112). Ajouter
deux champs optionnels (défaut `None` = « pas de pixel », cas non-joueur) :
```
x_cm: float | None = None
y_cm: float | None = None
```

## B. `planter` reçoit et stocke le pixel
Fichier `sim/actions/gestes.py`, fonction `planter` (~ligne 99). Aujourd'hui la
signature est `planter(game_state, player, tile, eco, species, r, c)`. Le pont a
le pixel mais le rabat en `(r,c)` avant l'appel.
1. Étendre la signature avec deux optionnels rétro-compatibles :
   `planter(..., r, c, x_cm=None, y_cm=None)`.
2. Au dépôt du grain (~ligne 142), transmettre le pixel :
   `GrainEnAttente(species=..., genes=..., expression=..., cultive=True,
   player=..., semaine_depot=..., x_cm=x_cm, y_cm=y_cm)`.
   Si `x_cm/y_cm` sont `None` (appel sans pixel : bancs, tests), comportement
   inchangé.

## C. Le pont passe le pixel à `planter`
Fichier `tools/simserver/` — la route de `planter`. `actions_cibles.py:42`
dérive déjà `rc = _plot_at(tile, target.x_cm, target.y_cm)`. Trouver l'appel à
`planter(...)` (grep `planter(` dans `tools/simserver/`) et lui passer EN PLUS
`x_cm=target["x_cm"], y_cm=target["y_cm"]` (le repère est déjà tuile-local, cf.
`actions_cibles`). Ne pas changer la dérivation `(r,c)` (elle reste la clé de
niche/FIFO).

## D. La levée place à la bonne position
Fichier `sim/succession.py`.

**D.1 — Levée d'un grain planté** (`_lever_grains_en_attente`, ~ligne 207).
Après `new_plant = tile.add_plant(plant_class, r, c)` et le `if new_plant is
None`, poser la position AVANT toute lecture de `root_plots` (ligne 221) :
```
if grain.x_cm is not None and grain.y_cm is not None:
    new_plant.x_cm, new_plant.y_cm = grain.x_cm, grain.y_cm      # pixel cliqué exact
else:
    _offset_subplot(new_plant, seed, week)                        # grain sans pixel → féral
```
(le grain planté a normalement un pixel ; le `else` couvre les dépôts de test.)
**Important** : `root_plots`/`foliar_plots` sont mémoïsés sur `(x_cm,y_cm,rayon)`
→ écrire `x_cm,y_cm` AVANT `occupied_roots.update(new_plant.root_plots)` suffit
à invalider le cache (clé changée). Ne pas réordonner après.

**D.2 — Germination férale** (`succession`, ~ligne 425). Après
`new_plant = tile.add_plant(plant_class, r, c)` / `if new_plant:` et AVANT la
lecture de `new_plant.x_cm, new_plant.y_cm` passée à `founder_genes` (ligne 430) :
```
_offset_subplot(new_plant, seed, week)
```
⚠ l'offset doit précéder `founder_genes(...)` (ligne 430) qui LIT `x_cm,y_cm` :
sinon les gènes fondateurs seraient tirés sur la position centrée. C'est
volontaire — la lignée fondatrice suit la position réelle.

**D.3 — Helper d'offset** (haut de `succession.py`, près des imports/const) :
```
OFFSET_MIN = 10.0   # marge (cm) garantissant plot_foyer inchangé

def _offset_subplot(plant, seed: int, week: int) -> None:
    """Décale la plante DANS son plot-foyer, déterministe (philo #3). Bornes
    [OFFSET_MIN, PLOT_CM-OFFSET_MIN] → floor(pos/PLOT_CM) inchangé → chimie
    stable. Canaux de hash dédiés (×53/×59) décorrélés des autres usages."""
    r, c = plant.position
    span = PLOT_CM - 2 * OFFSET_MIN
    u1 = _hash_noise(seed, week * 53, r, c)
    u2 = _hash_noise(seed, week * 59, r, c)
    plant.x_cm = c * PLOT_CM + OFFSET_MIN + u1 * span
    plant.y_cm = r * PLOT_CM + OFFSET_MIN + u2 * span
```
(`_hash_noise` et `PLOT_CM` sont déjà importés dans `succession.py` — vérifie et
ajoute l'import manquant le cas échéant.)

## Golden (RE-FIGÉ — annoncé)
Le cas FÉRAL déplace les germinations spontanées du smoke → lumière/empreintes →
toute la trajectoire dérive. **Re-fige attendu et maîtrisé** (cause unique :
offset de placement féral). Procédure :
1. `python3 -m tests.test_golden` (échoue : hash changé).
2. Vérifie que l'écart est cohérent (positions/effectifs plausibles, pas de
   crash, pas d'explosion de population).
3. Re-fige le golden (mets à jour la valeur attendue dans `tests/test_golden.py`)
   et **note la nouvelle empreinte** dans `00_etat.md`.
4. Relance les suites ciblées (`tests/`) : elles doivent passer (au besoin,
   re-fige UNIQUEMENT celles qui dépendent de positions férales, en le notant).

## NE PAS faire
- Ne pas toucher `clonal.py` (clones déjà continus).
- Ne pas modifier `add_plant`/`__post_init__` (le centrage par défaut reste le
  repli des plantes créées hors germination : bancs, démo).
- Ne pas déplacer une plante hors de son plot (respecter `OFFSET_MIN`).
- Ne pas introduire de `random` ni de dépendance à l'ordre d'itération.

## Fin de tronçon
Mets à jour `00_etat.md` (§REPRISE + nouvelle empreinte golden), puis commit
(message style projet). Tronçon ② ensuite.

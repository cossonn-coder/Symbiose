# Tronçon ③ — Paillage moteur : champ `paillage` + geste `pailler` + effets

**Prérequis** : `CLAUDE.md`, `00_etat.md`, `docs/faune/trophique/conception_equilibre_invasion.md` §2.
Patron de référence : `fields/ecofields/couverture.py` (champ scatter + mixin) et
son couplage évaporation dans `fields/ecofields/hydrologie.py`.

## Objectif
Le levier central : un champ `paillage` par plot, posé par un geste `pailler`,
qui **freine la germination férale**, **épuise la banque de graines**, **réduit
l'évapotranspiration** et **se décompose en OM**. Sans geste joueur,
`paillage=0` partout → **golden INTACT**.

## Fichiers à toucher
1. **`fields/ecofields/paillage.py`** (créer) — `PaillageMixin` : champ
   `self.paillage` (GridField par plot ∈[0,1]) + `tick_paillage()` :
   décroissance `paillage *= (1 - PAILLAGE_DECAY)` et **dépôt de l'équivalent
   décomposé dans `om_stable`** (`self.om_stable.add(r,c, decompose * PAILLAGE_OM_W)`).
   La rétention d'humidité passe par la lecture dans hydrologie (point 4), pas par
   un écrit ici.
2. **`fields/ecofields/__init__.py`** — brancher le mixin dans `EcoFields`,
   instancier `paillage`, appeler `tick_paillage()` dans l'ordre de tick
   (`ticks.py`), APRÈS la couverture/avant l'uptake (à vérifier — cohérent avec
   les autres champs qui alimentent le sol).
3. **`sim/succession.py`** — germination férale : après le gate couverture,
   `paillage_local = eco.paillage.at_plot(r,c)` puis `niche *= (1 - paillage_local)`
   et cutoff dur si `paillage_local >= PAILLAGE_GERM_SEUIL`. `paillage=0` → ×1.0.
4. **`fields/ecofields/hydrologie.py`** — dans le calcul d'évaporation (là où
   `couverture_sol` réduit déjà l'évaporation, ~ligne 110), ajouter la réduction
   par `paillage` (mulch = barrière d'évaporation). `paillage=0` → neutre.
5. **`fields/seedbank.py`** — `tick_aging` accepte un accès au champ paillage :
   sous mulch, viabilité dégradée plus vite (`SEED_VIABILITY_LOSS ** (1 +
   PAILLAGE_AGING_BOOST * paillage_local)`). `paillage=0` → exposant 1 → inchangé.
   (Threader l'`eco`/le champ jusqu'à `tick_aging` — vérifier l'appelant dans
   `engine`/`ecofields`.)
6. **`sim/actions/gestes.py`** — `pailler(game_state, player, eco, r, c, *,
   nature="paille", depth=..., stock=...)` : dépose `paillage` sur le plot/zone,
   coût Vigueur via `cout_action` (ajouter l'entrée `"pailler"` dans
   `sim/actions/couts.py`), consomme le stock (tronçon ④ — en ③, autoriser un
   dépôt sans stock derrière un paramètre, le stock sera câblé en ④). Binaire
   (patron `epandre`).

## Constantes (calibrage post-test, valeurs de départ à commenter)
`PAILLAGE_DECAY` (~0.03/sem, mulch dure ~1 saison), `PAILLAGE_OM_W`,
`PAILLAGE_GERM_SEUIL` (~0.5), `PAILLAGE_AGING_BOOST`.

## Golden
**INTACT** (`84d35983…` ou le hash re-figé de ② si ② est passé avant). Le champ
naît à 0 partout, le smoke n'appelle jamais `pailler` → tous les facteurs ×1.
Vérifier `test_golden` + `test_population` inchangés vs l'état post-②.

## NE PAS
- Pas d'effet direct sur une plante (#2) — on écrit des CHAMPS.
- Pas de RNG. Pas de distinction de natures ici (c'est ④ — en ③, une seule
  profondeur générique suffit ; le paramètre `nature` est posé mais inerte).

## Vérif / F5
Test unitaire dédié (`tests/test_paillage.py`) : un plot paillé ne laisse pas
lever d'adventice ; le champ décroît et alimente `om_stable` ; l'évaporation y
est réduite. F5 = câblé au tronçon ⑧.

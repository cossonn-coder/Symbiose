# ③ — Plante-hôte vivante comme support + détachement + étranglement émergent

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + CE fichier. Conception :
> `docs/conception/CONCEPTION_GRIMPANTES.md` §5. **Golden NEUTRE** (vérifié :
> Bean(4,2) n'a aucune haute à portée). Repose sur ①②. Lancement depuis `data/code/`.

## Objectif
Étendre la recherche d'accroche (②) aux **plantes voisines vivantes** : une
grimpante libre monte sur une plante plus haute de tige compatible, **suit** sa
croissance, se **détache** à sa mort. L'**étranglement** (la grimpante finit par
ombrager son hôte) doit ÉMERGER du `LightField` — AUCUNE règle dédiée.

## Fichiers
- `sim/growth/phases.py` (ou `sim/grimpe.py` du ②) : étendre `chercher_support`
  aux **plantes** de la tuile dans le rayon borné : une voisine `other` est un
  support valide si `other is not plant`, `other.is_alive`,
  `other.current_height > plant.hauteur_autoportante`, et la compatibilité de
  tige tient (crampon : n'importe quelle tige ligneuse/haute ; vrille_volubile :
  tige d'une plante ; sarmenteux : jamais auto). Départage déterministe (distance
  puis `id`). L'`height_appui` d'un hôte vivant = **`other.current_height`, relue
  chaque tick** (l'hôte grandit → la grimpante suit).
- Détachement : si `plant.support` référence une plante et que celle-ci meurt
  (`not is_alive`) ou disparaît de la tuile → `plant.support = None` (la grimpante
  redevient libre → retombe via ① ou re-cherche au tick suivant).
- **Étranglement** : NE RIEN coder. La grimpante accrochée est à ~sa position
  (proche de l'hôte), sa canopée haute projette son ombre NORMALE dans le
  `LightField` ; le tri hauteur-décroissante (`fields/light.py:164`, auto-ombrage
  exclu) fait que l'hôte plus bas reçoit cette ombre. Vérifier seulement qu'aucune
  exclusion ne saute l'ombrage entre deux plantes distinctes proches.

## Golden
**NEUTRE** (même hash que ①/②). Vérifié en conception (§1.6) : `Bean(4,2)` — les
plots voisins (rows 3-5, cols 1-3) ne contiennent AUCUNE plante ; `Sunflower` est
en `(0,1)`, hors rayon. Donc aucune accroche vivante ne se déclenche.
1. `python3 -m tests.test_golden` → **inchangé** vs hash ①.
2. S'il bouge : le rayon d'accroche est trop large (il attrape une voisine hors
   du plot-foyer+8) → resserrer ; ne PAS re-figer.
3. Ajouter/adapter une suite ciblée (ex. `tests/test_grimpe.py`) qui PROUVE le ③
   hors golden : deux plantes rapprochées → accroche + suivi + détachement à la
   mort de l'hôte + ombrage émergent de l'hôte.

## Ce qu'il NE faut PAS faire
- Pas de règle d'étranglement (malus direct sur l'hôte = viole #2) — c'est le
  `LightField` qui le fait émerger.
- Pas de compagnonnage scripté (le mutualisme haricot→N sur l'hôte émerge déjà
  via le sol).
- Ne pas élargir le rayon au point de casser le golden.

## F5
- (au banc ⑥) haricot planté contre un tournesol : il doit grimper le tournesol,
  le suivre, puis l'ombrager quand il le dépasse.

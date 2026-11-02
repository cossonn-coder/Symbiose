# ① Fiches des arbres + banc de mesure — golden INTACT

**Lire d'abord** : `CLAUDE.md`, `00_etat.md`, `docs/rendu/ambiance/conception_automne_visible.md`.

## Objectif

Poser la référence : ce que chaque arbre DEVRAIT être (fiches) et ce qu'il EST (banc + captures).
Aucune modification du moteur ni de la vue.

## À faire

1. `docs/vegetal/croissance/fiches_arbres.md` : une fiche pour chacun des 11 arbres de
   `PERENNIAL_CATALOGUE` (`plants/catalogue.py`, classes dans `plants/perennials.py`) : port et
   forme de couronne, hauteur et rayon à 10 et 30 ans (fourchettes réelles), tronc/écorce, feuille
   (forme, disposition, taille), couleur d'été, **couleur et date d'automne**, fruit, floraison.
   Pour chacune, la **traduction jeu** : archétype de port visé (dressé, ovoïde, pleureur, étalé…)
   et cibles à 10 ans (hauteur, rayon). Écart avec le réalisme assumé pour le gameplay : l'écrire
   (les arbres du jeu restent à l'échelle d'un jardin de 20×20 m).
2. `data/code/bancs/mesure_arbres.py`, lecture seule, déterministe, 11 arbres × 5/10/15/25 ans via
   `sim.precroissance.pre_croitre` : segments, hauteur, rayon de couronne, apex, part de segments
   feuillés. Patron : `bancs/mesure_calendrier.py`. Tient en quelques secondes.
3. Écrire `mesures/avant.md` : le tableau du banc, chaque chiffre marqué `[seed 42, sans lumière, VM]`.
4. Diagnostiquer (sans corriger) **pourquoi la hauteur s'effondre** entre 10 et 15 ans (bouleau 765 →
   274 cm) et consigner la cause vérifiée dans `00_etat.md` pour le ②.
5. Captures de référence avec `tools/capture_vm.sh` (`-b full -w 33 -z 4 -c 975,1475 -n 6` vise le
   pommier en s33) : les noter dans `mesures/avant.md`, sans committer les PNG.

## Golden

**INTACT.** Vérifier `python3 -m tests.test_golden`.

## NE PAS

Modifier `plants/`, `sim/`, `fields/` ou le C#. Lancer `tests/test_epaisseur_500ans.py`.

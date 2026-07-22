# Tronçon 2 — Mécanique clonale (densification par ramets)

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` (D1, D4) +
> `docs/vegetal/grimpantes/conception_luxuriance_stratification.md §2.2`.
> **Pré-requis : tronçon 1 fait** (champ `couverture_sol` disponible = gate).
> **Golden : RE-FIGÉ maîtrisé et annoncé.**

## Objectif
Poser **UNE mécanique clonale paramétrée** : une plante clonale mature émet des
**ramets** (clones génétiques) dans le voisinage → tapissage + colonies
envahissantes ÉMERGENTS. Absorbe D62 côté mécanique (les espèces viennent aux
tronçons 4-5 ; ici on active le trèfle déjà au catalogue).

## Modèle (déterministe, zéro RNG live — philo #3)
- **Trait d'espèce** : `clonal_mode ∈ {none, stolon, rhizome, drageon}` (défaut
  `none`) + `clonal_radius_cm` + `clonal_interval` (cadence). Un seul chemin de
  code, les modes ne changent que les paramètres/gate (table §2.2 du doc).
- **Émission** : une plante mature de `clonal_mode != none` émet, tous les
  `clonal_interval`, un ramet à un **offset hashé** (direction + distance ≤ radius)
  via `_hash_noise`/`hash_gauss` (cf. `sim/reproduction.py`). Le ramet est une
  `PlantInstance` neuve, **vecteur de gènes COPIÉ** de la mère (clone, pas de
  brassage), posée via `world/tile.py::add_plant` (co-occupation déjà permise).
- **Gate d'établissement** (le ramet ne prend QUE si) :
  - couverture du plot cible `< COUVERTURE_SATURATION` (sinon saturé → refus) →
    **auto-limitation + cap perf** ;
  - gate de mode : `stolon`/`drageon` exigent de la **lumière au sol** (lire le
    `LightField` au sol du plot cible) ; `rhizome` tolère l'ombre (réserve) → pas
    de gate lumière → caractère envahissant émergent.
- **Coût Vigueur** : l'émission puise la Vigueur propre de la mère (cf.
  `sim/vigueur_plante.py`) → arbitrage émergent graines ↔ ramets. Pas assez de
  Vigueur → pas de ramet.
- **Trèfle** : lui donner `clonal_mode="stolon"` (couvre-sol stolonifère réel).

## Fichiers à toucher
- `plants/base/` (déclarer les traits `clonal_mode`/`clonal_radius_cm`/
  `clonal_interval` sur `PlantBase`, défauts neutres).
- Nouveau `sim/clonal.py` (émission + gate + coût), câblé dans `sim/engine.py`
  au bon moment du tick (après croissance/Vigueur, cohérent avec la reproduction).
- `plants/species/cultivees.py` (Clover → `clonal_mode="stolon"`).
- Constantes (`COUVERTURE_SATURATION`, seuils de mode) près du module clonal.

## Golden — RE-FIGÉ (annoncé)
Le trèfle du golden devient stolonifère → ramets → population dérive. Re-figeage
LOCALISÉ attendu. Vérifier que la colonie de trèfle **reste bornée** (le gate de
couverture doit plafonner ; si le nombre de plantes explose = bug de gate → NE PAS
figer, corriger). Consigner nouveau hash + raison dans `00_etat.md`. Lancer
`test_competition`, `test_senescence`.

## Ce qu'il NE faut PAS faire
- Pas de 3 chemins de code séparés par mode (un seul, paramétré — D4).
- Pas de RNG live (hash uniquement).
- Pas de flag « envahissant » : le caractère envahissant ÉMERGE de `rhizome`.
- Pas d'ajout d'espèces neuves (tronçons 4-5).
- Ne pas laisser une colonie exploser : le gate couverture EST le cap perf.

## Fin de tronçon
MAJ `00_etat.md` (§REPRISE + hash + raison), commit.

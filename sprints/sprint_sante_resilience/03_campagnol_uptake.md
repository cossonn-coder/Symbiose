# ③ Canal campagnol → uptake + mycorhize (fix chronique replié)

> Kickoff autosuffisant. Lis `CLAUDE.md` + `00_etat.md` + ce fichier. Prérequis :
> ① (`vitalite`/`erode`) + ② (`resilience_base`). Doc :
> `docs/vegetal/sante/conception_sante_resilience.md` §3. **Golden NEUTRE attendu.**

## Objectif

Rebrancher l'herbivorie racinaire du campagnol selon la philo #2 : au lieu d'un
`ReduceHealth −1` plat (aujourd'hui « avalé » par `_cap_chronique`), le campagnol
**affame** la plante — racines rongées → **perte d'uptake** → souffrance par les
voies eau/azote EXISTANTES. Ajoute la niche **`root_loss_tolerance_base`** et la
**compensation mycorhize**. **Annélation létale conservée.**

## Modèle (rappel doc §3)

1. **`root_herbivory_memory`** (nouvel état d'instance) : lerp lent ∝ densité
   `herbivore_vertebre` locale.
2. **Perte d'uptake** : la mémoire réduit l'uptake effectif, compensée par la
   mycorhize et modulée par la niche d'espèce.
3. **Annélation létale** (jeune ligneux, dens ≥ `ROOT_HERBIVORY_LETHAL`) :
   sectionnement mécanique → `vitalite = 0` DIRECT (bypass `erode()`), certain.

## Fichiers à toucher

1. **`plants/base/instance.py`** : ajoute l'état `root_herbivory_memory: float =
   0.0` (à côté des autres `*_memory`, avec commentaire pédagogique). Ajoute
   l'attribut de classe `root_loss_tolerance_base: float = 1.0` sur PlantBase
   (`plants/base/familles.py`, à côté de `resilience_base` du ②) ; overrides sur
   quelques espèces (racines profondes / mycorhizo-dépendantes = >1 tolèrent mieux ;
   bulbeuses / racines superficielles = <1). Défaut 1.0 neutre acceptable.

2. **`sim/engine/croissance.py` `_update_physiology`** : intègre la mémoire, en
   MIROIR des autres (`drought_memory` etc.) :
   ```
   rong = eco.category_density("herbivore_vertebre", r, c)
   plant.root_herbivory_memory += (rong - plant.root_herbivory_memory) * ROOT_HERBIVORY_MEMORY_LERP
   plant.root_herbivory_memory = max(0.0, min(1.0, plant.root_herbivory_memory))
   ```
   À densité nulle (smoke) → mémoire reste 0 → GOLDEN NEUTRE.

3. **`sim/engine/croissance.py` `_apply_uptake`** : passe à `plant_uptake` deux
   scalaires neufs — `root_herbivory_memory=plant.root_herbivory_memory` et
   `root_loss_tolerance=plant.plant_class.root_loss_tolerance_base`.

4. **`fields/ecofields/uptake.py` `plant_uptake`** : ajoute les deux paramètres
   (`root_herbivory_memory: float = 0.0`, `root_loss_tolerance: float = 1.0`).
   Calcule un **facteur racinaire** par plot, AVANT la boucle `UPTAKE` :
   ```
   root_loss = root_herbivory_memory / root_loss_tolerance          # niche espèce
   root_loss *= max(0.0, 1.0 - MYCO_ROOT_COMPENS * self.mycelium.at_plot(r, c))  # mycorhize compense
   root_factor = max(ROOT_UPTAKE_FLOOR, 1.0 - root_loss * ROOT_HERBIVORY_UPTAKE_MALUS)
   ```
   Multiplie `asphyxie_factor *= root_factor` (se propage à eau ET N/P/K, comme
   l'asphyxie). À `root_herbivory_memory=0` → `root_factor=1.0` → uptake
   bit-identique → GOLDEN NEUTRE. `self.mycelium.at_plot` est DÉJÀ lu ici pour le
   bonus P (ligne ~131) → zéro coût de lecture neuf.

5. **`sim/effects/perturbations.py` `root_herbivory`** : SUPPRIME le `ReduceHealth`
   chronique modeste (le `_hash_noise < pressure → ReduceHealth(plant,1,…)`).
   GARDE l'**annélation létale** mais bascule-la en mort mécanique directe :
   jeune ligneux annelé (dens ≥ `ROOT_HERBIVORY_LETHAL`) → `plant.vitalite = 0`
   (bypass `erode()` — sectionnement, la constitution n'y peut rien) + déposer la
   nécromasse comme les autres morts si le chemin l'exige (regarde comment les
   morts sont déposées ailleurs ; reste cohérent avec `deposer_mort`). La fonction
   ne renvoie donc PLUS de mutation chronique — la souffrance vient de l'uptake.
   Le signe `rongeur_racinaire` (sémiologie) reste inchangé (il lit la densité).

## Constantes à poser (`fields/ecofields/constants.py`, calibrage post-test)

- `ROOT_HERBIVORY_MEMORY_LERP = 0.05` (miroir des autres mémoires).
- `ROOT_HERBIVORY_UPTAKE_MALUS = 0.5` (mémoire saturée → −50 % d'uptake max, avant
  tolérance/mycorhize — placeholder).
- `ROOT_UPTAKE_FLOOR = 0.3` (une plante rongée boit encore un minimum).
- `MYCO_ROOT_COMPENS = 0.5` (réseau saturé → compense la moitié de la perte).

## Golden — NEUTRE (invariant)

Au smoke, densité `herbivore_vertebre` = 0 → `root_herbivory_memory` reste 0 →
`root_factor` = 1.0 → uptake inchangé ; `root_herbivory` ne produit plus de
mutation (annélation jamais atteinte sans campagnol). **Le hash NE DOIT PAS
bouger.** S'il bouge → une des voies fuit à densité nulle, corrige (ne fige pas).
Vérifie explicitement dans le commit que le hash = celui du ②.

## Ce qu'il NE faut PAS faire

- Ne pas ré-introduire d'érosion de santé DIRECTE par le campagnol (hors
  annélation létale) — toute la souffrance passe par l'uptake (philo #2).
- Ne pas toucher à la vue (④) ni recalibrer la constitution (②).
- Ne pas lancer `test_epaisseur_500ans` (interdit — long/inutile).

## Vérif de sortie

`python3 main.py` sans crash ; `python3 -m tests.test_golden` **hash inchangé**
(= ②) ; suites `tests/` vertes. Idéalement, un mini-test dédié (facultatif, cf.
mémoire « conserver le code ») : forcer une densité `herbivore_vertebre` locale et
vérifier que l'uptake chute puis que la mycorhize/tolérance l'atténuent.

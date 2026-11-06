# ① Banque de semis — un petit ligneux tient sous une ombre plus profonde

À lire d'abord : `CLAUDE.md`, `00_etat.md`, `docs/vegetal/regeneration/conception_releve_ligneuse.md` §1-§3.1.

## Objectif
Un jeune ligneux ombragé **végète au lieu de mourir** : le seuil de `shade_memory`
au-delà duquel `shade_stress_damage` abîme une plante monte avec la petitesse,
pour les ligneux seulement. Pourquoi : le point de compensation lumineux monte avec
la taille (un semis a peu de tissus à entretenir) — c'est la lumière reçue qui
décide, pas une prime (philo #2).

## Modèle
Dans `data/code/sim/effects/perturbations.py`, à côté de `SHADE_DAMAGE_THRESHOLD` :

    H_GAULE     = 200.0   # cm — au-delà, plus d'avantage de semis [choix, calibré au ④]
    SEUIL_SEMIS = 0.75    # shade_memory de dégât d'un semis (lumière ~0,25) [choix, calibré au ④]

    def seuil_ombre(plant) -> float:
        # herbacée : SHADE_DAMAGE_THRESHOLD inchangé
        # ligneux (plant.plant_class.ligneux) :
        #   petitesse = clamp(1 − plant.plant_class.height_at(plant) / H_GAULE, 0, 1)
        #   return SHADE_DAMAGE_THRESHOLD + (SEUIL_SEMIS − SHADE_DAMAGE_THRESHOLD) × petitesse

`shade_stress_damage` lit `seuil = seuil_ombre(plant)` à la place de la constante,
y compris dans la sévérité `(sm − seuil)/(1 − seuil)`. Le canal de hash (week·41)
et `SHADE_DAMAGE_RATE` ne changent pas.

`sim/semiologie.py` (signe `ombre`, ~l.115) importe déjà depuis `perturbations` :
le signe rampe désormais de `seuil_ombre(plant)` à 1.0 (un semis qui attend ne
montre pas de souffrance). Vérifier au code la signature de la fonction du signe
(elle reçoit `plant`).

Commentaire pédagogique au cœur du code : point de compensation, banque de semis,
reprise à la trouée déjà portée par `growth_factor` dans `grow_plant`.

## Fichiers
- `data/code/sim/effects/perturbations.py` (constantes + `seuil_ombre` + usage).
- `data/code/sim/semiologie.py` (signe `ombre`).
- Test neuf `data/code/tests/test_banque_semis.py` : à lumière reçue imposée
  constante (patron `run_shade` de `tests/test_stress_chronique.py` : surcharge de
  `eco.lumiere.light_received`, germination/ravageurs/campagnol/risée neutralisés),
  (a) un petit pommier (âge 0) à lumière 0,35 **survit** 5 ans ; (b) le même à
  lumière 0,10 **meurt** ; (c) `seuil_ombre` d'un ligneux haut (≥ H_GAULE) = 0,55
  et d'une herbacée = 0,55. Si un pommier jeune meurt d'autre chose (vent,
  herbivorie…), neutraliser cette voie comme le fait `_lab_tile`, ne pas toucher
  au moteur.

## Golden
**INCHANGÉ** attendu (`a10b7225…`). Espion mesuré en conception : le seul ligneux
du smoke (Pommier) passe 3 fois le seuil 0,55, 0 dégât [smoke, n=1 run, VM]. Si le
golden bouge : STOP, ce n'est pas prévu — chercher pourquoi, ne jamais re-figer.

## Tests à faire passer
`python3 -m tests.test_golden`, `tests.test_stress_chronique` (invariant
héliophile/sciaphile sur courgette, inchangé), `tests.test_banque_semis`, les
suites de sémiologie/signes (`grep -l "ombre" tests/test_*sign*.py tests/test_semio*.py`).
**Ne jamais lancer `test_epaisseur_500ans`.**

## Ne PAS faire
- Toucher aux herbacées, à `SHADE_DAMAGE_RATE` ou au seuil 0,55.
- Changer `ok_light` (croissance) ou la pose des recrues (c'est le ②).
- Appeler DeepSeek en routine.

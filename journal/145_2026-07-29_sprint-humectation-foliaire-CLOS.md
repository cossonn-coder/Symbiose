# 2026-07-29 — Sprint HUMECTATION FOLIAIRE (D38) — CLOS

`/sprint-auto sprint_humectation_foliaire` (①→④). Solde **D38** en corrigeant
non pas « une hygrométrie à poser » mais **un proxy faux déjà en production** :
`fungal_disease` lisait l'humidité du **SOL** comme proxy de l'humectation du
**FEUILLAGE** → `arroser` au pied (bonne pratique permacole) rendait la plante
malade (violation dormante de la philo #6). Le durcissement `/conception` avait
recadré le sujet et écarté deux fausses pistes (rosée déjà close de fait ;
évaporation/VPD abandonnée = double comptage avec `tick_hydrology`, D1).

**Golden `57c166d8…` INCHANGÉ sur les 4 tronçons** — y compris ② où un
re-figeage était prévu et **n'a pas eu lieu** (voir ci-dessous). `dotnet build`
non concerné (moteur Python pur, aucun C# touché). Suite neuve
`tests/test_humectation.py` (①②③④) verte.

## ① `wetness_memory` — mémoire d'humectation inerte (`5d81446`)

Champ `float [0,1]` par plante (`PlantInstance`, hors `_PLANT_ATTRS`), alimenté
dans la boucle physiologie existante (patron `drought_memory`/`wind_memory`,
O(N) borné, aucune passe de champ neuve) : **mouillage** rosée+pluie,
**séchage** vent+soleil, **aération** par densité de couvert. Lu par personne
(socle du proxy correct). 8 constantes dans `fields/ecofields/constants.py`
(dont `ASPERSION_WET_GAIN` réservé au ③). **Golden NEUTRE.**

*Écart kickoff assumé* : `foliage_density_at(plant)` (accesseur sûr, jamais
None) au lieu de `plant_class.foliage_density` qui vaut `None` sur toutes les
herbacées (`None × float` planterait).

## ② bascule du proxy (`8de6e21`)

`fungal_disease` (`perturbations.py`) et `infection_memory` (`croissance.py`)
lisent désormais `plant.wetness_memory` au lieu de `min(1, hum_sol/3)`. Le bloc
`wetness_memory` remonté **avant** `infection_memory` dans `_update_physiology`
(tick courant à jour avant lecture). `damping_off` (fonte des semis) reste sur
le sol — biologiquement correct.

**Re-figeage prévu au kickoff, mais golden INCHANGÉ.** Vérifié empiriquement,
pas supposé : (a) `fungal_disease` ne déclenche jamais dans le smoke (0
événement) ; (b) `infection_memory` change bien (toggle prouvé non no-op :
wetness max 0.295, 2684 plant-semaines >0), mais son seul aval `cout_defense`
déplace le timing de stade **sous la résolution** qui bougerait un attribut
digéré. Leçon récurrente (cf. D90/D91) : une grandeur santé/plasticité dont
l'effet ne franchit pas la maille du digest laisse le golden byte-identique.
**Rien re-figé** — conforme à la règle « ne pas figer si rien ne bouge ».

## ③ `arroser` pied ou feuillage (`ac13e0b`)

Le geste `arroser` gagne un mode `feuillage` (défaut `False` = pied, inchangé).
En `feuillage=True` il pose `eco.aspersion_last` (patron `rosee_last`), lu par
`ASPERSION_WET_GAIN` dans l'humectation puis remis à plat chaque tick. **Coût
identique** dans les deux modes. Arroser au pied ne mouille plus le feuillage →
n'ouvre plus la porte au mildiou : la bonne pratique cesse d'être punie, le
dilemme devient **jouable**. Pont **0.5.41 → 0.5.42** (champ optionnel
`params.feuillage`, tolérant côté binaire ancien). **Golden NEUTRE.**

*Écarts kickoff assumés* : reset `aspersion_last` **après** `_update_physiology`
(le geste s'applique hors tick — un reset en tête effacerait l'apport avant
lecture) ; `DOSE_ARROSAGE` déplacé en `constants.py` (l'import
`engine → sim.actions.gestes` du kickoff créait un cycle).

## ④ guilde oïdium — la courgette interdit la solution unique (`3394888`)

Seconde guilde cryptogamique au **signal inverse** du mildiou : `oidium_disease`
se déclenche sur feuillage **sec et chaud** (`(1−wetness_memory)×chaleur`, canal
`_hash_noise` `week·47`, **sans** assèchement-vent = c'est le dilemme). Attribut
additif `oidium_susceptibility` (courgette 0.9 Cucurbitaceae, pommier 0.3,
défaut 0.0), médié par `resistance_pathogene` — **aucun gène neuf, aucune espèce
ajoutée** (QC). Dilemme prouvé en test : feuillage mouillé → mildiou 27/oïdium 2,
sec → mildiou 2/oïdium 22. Pas de geste unique gagnant. **Golden NEUTRE**
(neutralité prouvée : le pommier EST dans le smoke mais oïdium=0.3 ne franchit
jamais le seuil → sortie byte-identique).

## Intendance

- **Refactor auto-léger : no-op.** Aucun fichier touché en zone rouge (>400 LDC
  pur) ; le plus haut, `perennials.py` à 356 🟡, l'était déjà avant (le sprint
  n'y a ajouté qu'un trait). `perturbations.py` 273, `croissance.py` 212.
- Canal `_hash_noise` `week·47` consommé (oïdium) — restaient libres 47/61/67,
  désormais **61/67 libres**.
- **DETTE D38 → ✅ CLOS.**

## Reste F5 Nico

- **Rendu C# des signes** : gouttes/givre de rosée (D24) et signe `oïdium`
  (feutrage blanc) — à tracer côté `PlantRenderer` s'ils sont absents.
- **Toggle pied/feuillage** dans la vue Godot (le pont expose `params.feuillage`,
  la vue pourrait ajouter le choix — non implémenté).
- **Calibrage** `oidium_susceptibility` du pommier (0.3 placeholder ; s'il monte,
  revérifier le golden) et les constantes d'humectation.

Aucun bug connu. `dotnet build` vert.

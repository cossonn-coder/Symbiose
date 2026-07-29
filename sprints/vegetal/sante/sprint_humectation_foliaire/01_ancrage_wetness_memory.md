# ① Ancrage — `wetness_memory` posée et alimentée, lue par PERSONNE

**Sprint** : `sprint_humectation_foliaire` · **Golden attendu : NEUTRE (inchangé)**
**Conception** : `docs/vegetal/sante/conception_humectation_foliaire.md` §2.1, §2.2, §2.3

## Objectif

Poser la mémoire d'humectation foliaire sur `PlantInstance` et l'alimenter chaque
semaine dans `_update_physiology`, **sans aucun consommateur**. Patron éprouvé : la
plasticité ① avait posé `expressed_gene` inerte avant de le brancher au ②.

À la fin du tronçon, `wetness_memory` vit, bouge, est bornée — et **rien ne la lit**.
Le golden doit être **bit-identique**.

## Fichiers à toucher

1. `data/code/plants/base/instance.py` — le champ (~ligne 49-63, avec les 6 autres mémoires)
2. `data/code/fields/ecofields/constants.py` — les constantes (§ neuf en fin de fichier)
3. `data/code/sim/engine/croissance.py` — l'alimentation dans `_update_physiology`
4. `data/code/sim/engine/boucle.py` — passer `nebulosite` à `_update_physiology` (ligne ~381)

## Modèle

### Le champ

Dans `instance.py`, à côté de `wind_memory` / `root_herbivory_memory` :

```python
wetness_memory: float = 0.0     # durée d'humectation foliaire intégrée [0-1]
```

### Les constantes

```python
# --- Humectation foliaire (sprint humectation ①, §2.2) ---
# Durée d'humectation du FEUILLAGE (≠ humidité du SOL) : l'eau posée sur les feuilles
# est le vrai signal des maladies cryptogamiques (règle de Mills, périodes de Smith).
# Lerp VOLONTAIREMENT plus rapide que les autres mémoires (0.05 = stress chronique
# décennal) : l'humectation se mesure en heures ; à l'échelle du tick (1 semaine) le
# signal utile est « combien de nuits mouillées cette semaine », avec juste assez
# d'inertie pour que « trois nuits sans vent » émerge comme critère de DURÉE.
WETNESS_MEMORY_LERP  = 0.35
ROSEE_WET_GAIN       = 0.9    # la rosée est la source d'humectation la plus RÉGULIÈRE
PLUIE_WET_GAIN       = 0.8    # la pluie mouille fort mais passe
PLUIE_WET_REF        = 0.5    # pluie_event saturant le signal d'humectation
ASPERSION_WET_GAIN   = 1.0    # arroser AU FEUILLAGE : la source la plus mouillante (③)
VENT_WET_DRY         = 0.7    # part du séchage imputable au vent à force 1
RAD_WET_DRY          = 0.5    # part du séchage imputable au soleil à ciel clair
COUVERT_WET_SHELTER  = 0.8    # un couvert dense empêche le vent de pénétrer (aération)
```

Toutes des **PLACEHOLDERS** — calibrage F5 / bancs d'essai (⑥).

### L'alimentation — dans `_update_physiology`

⚠️ **Le point délicat du tronçon.** La rosée captée sur l'empreinte foliaire est **déjà
calculée** (`croissance.py:286-288`) mais **sous le garde `if drought_stress > 0.0`**.
Il faut la **remonter hors du garde** pour que l'humectation en dispose toujours, en
laissant le calcul de `relief` (le rabot de `drought_stress`) sous son garde d'origine.

Forme cible :

```python
# Rosée moyenne captée sur l'empreinte foliaire — calculée UNE fois, deux
# consommateurs (captation foliaire du drought_stress + humectation ①). On ne
# recalcule JAMAIS dans un tick ce qui l'a déjà été.
capte = 0.0
rosee = getattr(eco, "rosee_last", None)
if rosee is not None and plant.foliar_plots:
    capte = sum(rosee.at_plot(fr, fc) for (fr, fc) in plant.foliar_plots
                if 0 <= fr < eco.rows and 0 <= fc < eco.cols)
    capte /= len(plant.foliar_plots)

# … puis, INCHANGÉ, sous son garde d'origine :
if capte > 0.0 and drought_stress > 0.0:
    relief = ROSEE_FOLIAIRE_MAX * min(1.0, capte / ROSEE_SURFACE_REF)
    drought_stress = max(0.0, drought_stress * (1.0 - relief))
```

**Vérifie que `drought_stress` reste bit-identique** : la condition d'origine était
`rosee is not None and drought_stress > 0.0 and plant.foliar_plots` ; la nouvelle doit
lui être **strictement équivalente** (`capte > 0.0` implique `rosee is not None` et
`plant.foliar_plots` non vide — mais attention au cas `capte == 0.0` avec rosée présente :
`relief` valait alors 0.0 et `drought_stress` était multiplié par 1.0, donc inchangé →
l'équivalence tient).

Puis, à la fin des mémoires (après `root_herbivory_memory`) :

```python
# Humectation foliaire (§2.2) : l'eau se POSE (rosée/pluie/aspersion) puis SÈCHE
# (vent, soleil). Le vent ne pénètre pas un couvert dense → l'aération devient un
# levier de MILIEU (espacer, tailler — philo #1). INERTE au ① : lu par PERSONNE.
dens = plant.plant_class.foliage_density
vent_eff = vent_local * (1.0 - COUVERT_WET_SHELTER * dens)
mouillage = (ROSEE_WET_GAIN * min(1.0, capte / ROSEE_SURFACE_REF)
             + PLUIE_WET_GAIN * min(1.0, max(0.0, pluie_event) / PLUIE_WET_REF))
sechage = ((1.0 - VENT_WET_DRY * min(1.0, max(0.0, vent_eff)))
           * (1.0 - RAD_WET_DRY * (1.0 - nebulosite)))
wet_sig = max(0.0, min(1.0, mouillage * sechage))
plant.wetness_memory += (wet_sig - plant.wetness_memory) * WETNESS_MEMORY_LERP
plant.wetness_memory = max(0.0, min(1.0, plant.wetness_memory))
```

Le terme `ASPERSION_WET_GAIN` arrive au **③** (pas de `aspersion_last` encore).

### Signature

`_update_physiology(self, tile, eco)` → `_update_physiology(self, tile, eco, nebulosite=1.0, pluie_event=0.0)`.
Défauts **inertes conservateurs** ; `boucle.py:381` passe les vraies valeurs (`nebul` de
la ligne 95, et le `pluie_event` déjà calculé pour `tick_hydrology` ligne ~293).

## Golden

**NEUTRE, bit-identique.** `wetness_memory` n'est lue par personne, et le refactor de
`capte` préserve `drought_stress`. Lance `python3 -m tests.test_golden` depuis
`data/code/` : le hash **doit** être inchangé. S'il bouge, c'est que le déplacement de
`capte` a modifié `drought_stress` → corrige, ne re-fige pas.

## Ce qu'il ne faut PAS faire

- ❌ Brancher un consommateur (c'est le ②) — le tronçon doit rester inerte.
- ❌ Toucher `tick_hydrology` / `hydrologie.py` (décision de conception §1.2 : double
  comptage, et D39 a déjà tué un pommier sur cette formule).
- ❌ Créer un `GridField hygrometrie` ou une grandeur « HR » (§1.3).
- ❌ Calculer l'humectation par segment/organe (D29) — granularité plante, point.
- ❌ Recalculer la rosée captée une seconde fois.
- ❌ Lancer `test_epaisseur_500ans` (long, inutile — interdit).

## Vérification

1. `python3 -m tests.test_golden` → hash **inchangé**.
2. Écris `data/code/tests/test_humectation.py` (conserver le fichier — on ne jette
   jamais un test) : au moins (a) la mémoire monte sous rosée + vent nul, (b) elle
   **redescend** vers 0 quand le mouillage cesse (philo #4 : décroissance garantie),
   (c) elle reste bornée [0,1] sur 200 ticks saturés, (d) un couvert dense
   (`foliage_density` haute) sèche moins qu'un couvert clair à vent égal.
3. `python3 tools/compte_ldc.py` sur `croissance.py` — s'il franchit 400, **signale-le**
   dans `00_etat.md` (le ② n'a pas à hériter d'un fichier rouge).

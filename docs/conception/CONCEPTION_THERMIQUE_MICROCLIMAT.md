# CONCEPTION — THERMIQUE & MICROCLIMAT

> Conception figée le 2026-06-18 (Sprint thermique-microclimat). Source de vérité
> du modèle ; les kickoffs `sprints/sprint_thermique_microclimat/0N_*.md` en
> dérivent. Mémoire : voir l'entrée de journal de clôture du sprint.

## 0. Objectif & intuition

Aujourd'hui la température est **une seule valeur par semaine** répartie
uniformément sur tous les plots (`boucle.py` : `eco.temperature.fill(temp_now)`).
Le jardin n'a donc **aucun microclimat** : un coin en plein soleil et un coin à
l'ombre de la maison sont à la même température, perdent autant d'eau, gèlent en
même temps. Or c'est faux, et c'est précisément le levier pédagogique de la
permaculture : **l'ombre, le paillis, l'eau et le couvert nuageux fabriquent des
micro-refuges**.

Ce sprint **spatialise la thermique** en la couplant au `LightField` (qui sait
déjà, par plot, combien de soleil arrive). Tout émerge ensuite : évaporation
différenciée soleil/ombre, cercle vicieux de la sécheresse, espalier chaud
devant le mur sud, gel qui épargne les zones abritées.

Philosophie respectée :
- **#2 flux → contrainte → réponse** : rayonnement solaire (flux) → surchauffe
  locale + assèchement (contrainte) → germination/stress/gel (réponse biologique).
  Jamais de bonus/malus direct sur la plante.
- **#3 déterminisme** : tout est fonction pure des champs déjà calculés, zéro RNG.
- **Interconnexion des acteurs** : la litière (décompo) isole le sol, la canopée
  (croissance) et la maison (monde) ombragent, les nuages (météo) tamponnent.

## 1. État de départ (ce qui existe déjà)

| Brique | Où | Statut |
|---|---|---|
| T air globale `temp_norm(week)` (sinusoïde Normandie + dérive + deltas) | `sim/weather.py` | OK, conservée telle quelle |
| Champ `temperature` (GridField par plot) | `fields/ecofields/container.py` | existe mais **rempli uniformément** |
| Évaporation **déjà couplée** à `temperature.data[r][c]` | `tick_hydrology` | OK — suivra dès que la carte sera non-uniforme |
| `LightField` : lumière-sol par plot (intégrale diurne) + lumière reçue par plante | `fields/light.py` | OK — la donnée spatiale clé |
| Gel **global** `if temp_now < 0` → `_mediated_damage` toute la tuile | `sim/engine/boucle.py` | à localiser (⑥) |
| Catalogue météo : 7 événements, **pas de Neige ni Orage** | `sim/weather.py` `_CATALOGUE` | à compléter (⑦) |

**Le chaînon manquant tient en une phrase : la lumière-sol n'alimente pas encore
la température.**

## 2. Le modèle thermique

On distingue **deux températures** physiquement distinctes (c'est le cœur) :

- **T_air** : grandeur de masse, le vent la brasse → quasi homogène. C'est la
  météo existante (`temp_norm + delta`). Le champ `temperature` la porte
  (rempli uniforme par la boucle, **inchangé**).
- **T_sol** : le **microclimat de surface**, TRÈS hétérogène. Nouveau champ
  `temperature_sol` (par plot). C'est lui qui pilote l'évaporation et (dérivé) la
  croissance et le gel.

### 2.1 Carte diurne T_sol (tronçons ①–④)

Cible thermique d'un plot, somme de quatre termes (chacun ajouté à son tronçon) :

```
cible[r,c] = T_air
           + GAIN_SOLAIRE · lumière_sol[r,c] · intensité_saison · (1 − k_nébul·nébulosité)   ⟵ ① puis ④
           − REFROID_EVAP · humidité_norm[r,c]                                                ⟵ ②
           − ISOLATION    · litière_norm[r,c]                                                 ⟵ ③
```

- `lumière_sol[r,c]` ∈ [0.15, 1] : **déjà** une moyenne diurne (intégrale des
  tranches pondérée par l'intensité solaire dans `LightField.compute`). L'ombre
  (maison, canopée, squelettes) y est déjà encodée.
- `intensité_saison` ∈ [0,1] : un soleil d'hiver chauffe moins (table §3).
- `humidité_norm` = `humidite / 3` (échelle humidité = [0,3]) : **chaleur
  latente** — un sol humide reste frais (l'eau qui s'évapore prend de l'énergie).
  C'est ce terme qui crée le **cercle vicieux sécheresse** : sec → moins de
  refroidissement → plus chaud → évapore plus → plus sec.
- `litière_norm` = `min(1, masse_litière / LITIERE_REF)` : le paillis naturel
  tamponne. Réutilise `om_fresh_at(r,c)` (Σ masses de parcelles du plot).
- `nébulosité` ∈ [0,1] (table §3) : les nuages bloquent le soleil → moins de
  surchauffe (et, la nuit, protègent du gel, cf. 2.3).

### 2.2 Inertie thermique (tronçon ①)

T_sol ne **saute** pas à sa cible : le sol garde la chaleur d'une semaine sur
l'autre. Lissage temporel (comme `soil_memory`) :

```
temperature_sol[r,c] += (cible[r,c] − temperature_sol[r,c]) · THERMAL_INERTIA
```

`THERMAL_INERTIA` ∈ ]0,1] (≈ 0.5) : 1.0 = pas d'inertie (recalcul à neuf), petit
= sol très tamponné. Init = `T_AMBIENT_INIT` (comme `temperature`).

### 2.3 T minimale nocturne — pour le GEL (tronçon ⑥)

⚠️ **Le gel est nocturne et la logique s'inverse.** La nuit, le soleil ne chauffe
plus ; ce sont les zones **découvertes** qui gèlent le plus car elles rayonnent
leur chaleur vers le ciel **clair**. On ne peut donc PAS réutiliser T_sol diurne.

```
T_min_nuit[r,c] = T_air − RAYONNEMENT_NOCTURNE · (1 − couvert_norm[r,c]) · (1 − nébulosité)
```

- `couvert_norm` = couvert protecteur (litière + **manteau neigeux** si Neige
  active, ⑦) : plus c'est couvert, moins ça rayonne, moins ça gèle.
- `(1 − nébulosité)` : ciel couvert = peu de gel (les nuages renvoient la
  chaleur). C'est pourquoi les gelées arrivent par nuit claire et calme.

Pédagogie : c'est exactement ce qu'imitent **paillage et voiles d'hivernage**
(déjà dans la mécanique météo « préparation »).

### 2.4 T ressentie par la plante — pour la CROISSANCE (tronçon ⑤)

Une feuille n'est pas à la température du sol nu (son feuillage est dans l'air,
modéré par le microclimat) :

```
T_plante = α · T_air + (1 − α) · temperature_sol_local      (α ≈ 0.5)
```

Le gate de croissance (`sim/engine/croissance.py`, lit aujourd'hui
`eco.temperature.at_plot`) basculera sur cette T ressentie. Émergent gratuit :
**GDD locaux** (un coin chaud accumule ses degré-jours plus vite → fleurit plus
tôt) et **stress chaud** (si le gate a un optimum/plafond thermique).

## 3. Constantes & calibrages (knobs — placeholders, calibrage post-test)

À placer dans `fields/ecofields/constants.py` (valeurs PURES) :

```python
# Carte thermique diurne
GAIN_SOLAIRE      = 15.0   # °C — surchauffe max (plein soleil d'été, sol sec découvert)
THERMAL_INERTIA   = 0.5    # lissage temporel de T_sol vers sa cible (1 = pas d'inertie)
REFROID_EVAP      = 6.0    # °C — refroidissement max d'un sol saturé (humidité_norm=1)
ISOLATION_COUVERT = 4.0    # °C — tampon max d'une litière dense
LITIERE_REF       = 2.0    # masse de litière au-dessus de laquelle le couvert sature
K_NEBUL_DIURNE    = 0.8    # part de surchauffe annulée par un ciel totalement couvert

# Gel nocturne (⑥)
RAYONNEMENT_NOCTURNE = 5.0 # °C — refroidissement nocturne max (ciel clair, sol découvert)

# T ressentie (⑤)
T_PLANTE_ALPHA    = 0.5    # poids de T_air vs T_sol_local dans la T de croissance

# Intensité solaire saisonnière (fraction du rayonnement d'été)
INTENSITE_SAISON  = {"hiver": 0.35, "printemps": 0.70, "automne": 0.60, "ete": 1.0}

# Nébulosité par événement météo (0 = ciel clair, 1 = couvert)
NEBULOSITE = {
    "Beau temps": 0.10, "Sécheresse": 0.05, "Canicule": 0.10, "Gelée tardive": 0.05,
    "Redoux": 0.60, "Pluie prolongée": 0.90, "Tempête": 0.80, "Grêle": 0.70,
    "Orage": 0.85, "Neige": 0.70,   # Orage/Neige ajoutés au catalogue en ⑦
}
```

## 4. Ordre des ticks (PIÈGE structurant)

Dans `boucle.py`, la boucle par tuile fait : **2. lumière → 3. hydrologie**. Le
calcul thermique doit s'insérer **entre les deux** (il a besoin de la lumière à
jour, et l'hydrologie a besoin de T_sol) :

```
2.  tick_light          (eco.lumiere recalculée)
2b. tick_thermique  ⟵ NOUVEAU : calcule temperature_sol depuis lumiere + humidite + litiere + T_air
3.  tick_hydrology      (évaporation lit DÉSORMAIS temperature_sol)
```

`T_air` reste calculée hors boucle (`temp_norm + delta`) et continue de remplir
`eco.temperature` → croissance et gel **inchangés jusqu'à ⑤/⑥**.

## 5. Découpage en tronçons & invariants golden

Le **champ `temperature` est partagé** par l'évaporation, la croissance et le
gel. Spatialiser d'un coup dériverait les trois ensemble. Le découpage isole
chaque dérive en introduisant `temperature_sol` à part, puis en rebranchant un
consommateur à la fois.

### Bloc moteur (golden re-figé MAÎTRISÉ, une dérive isolée par tronçon)

- **①** `temperature_sol` (nouveau champ) + `tick_thermique` = T_air + surchauffe
  solaire (lumière × intensité_saison) **avec inertie lerp**. `tick_hydrology`
  lit `temperature_sol` au lieu de `temperature`. Croissance/gel **inchangés**.
  → *Dérive = hydrologie seule.*
- **②** Ajoute le terme `− REFROID_EVAP · humidité_norm` à la cible. → *Dérive
  température/hydro (cercle vicieux sécheresse).*
- **③** Ajoute le terme `− ISOLATION · litière_norm`. → *Dérive température légère.*
- **④** Ajoute la modulation `(1 − K_NEBUL·nébulosité)` (table par événement). →
  *Dérive température selon la météo.*
- **⑤** Le gate de croissance bascule de `eco.temperature` (T_air) vers la **T
  ressentie** `mix(T_air, temperature_sol)`. → *Dérive croissance.*
- **⑥** Le gel global est remplacé par un **gel nocturne localisé** : `T_min_nuit`
  par plot, dégât aux plantes des plots où `T_min < 0` (couvert + nébulosité +
  manteau neigeux protègent). → *Dérive gel.*
- **⑦** Ajoute **Neige** et **Orage** au catalogue `weather.py` + leurs effets
  (nébulosité, manteau neigeux isolant pour ⑥, mapping milieu). → *Dérive météo
  (tirages `weather_at` modifiés).*

### Bloc vue Godot (golden NEUTRE — 0 logique de tick, F5 chez Nico)

- **⑧** Exposer au **snapshot** : événement météo courant (kind/intensité/
  nébulosité) + carte `temperature_sol`. Python, simulation inchangée → golden
  neutre (on ajoute des champs au JSON).
- **⑨** **Rendu des événements météo** : pluie, neige, vent, grêle, orage
  (particules + voile + assombrissement du ciel). Vue pure, lit le snapshot.
- **⑩** **Heatmap température** debug dans `visuals/FieldOverlay.cs` (touche F6).
  Vue pure.

## 6. Reporté en dette (hors périmètre, décidé 2026-06-18)

- **D37 — Vent continu** : champ directionnel + géométrie de brise-vent (abri),
  effet desséchant (↑ évapotranspiration). Gros morceau → sprint dédié. La
  Tempête/Orage gardent leur effet ponctuel actuel.
- **D38 — Rosée nocturne + hygrométrie de l'air** : apport d'eau matinal par ciel
  clair (couplé à la nébulosité) ; air humide → ↓ évaporation + ↑ maladies
  fongiques. Raffinement touchant le système maladies.

## 7. Garde-fous

- **Taille** : `container.py` est déjà dense (337 ldc max du dépôt sur
  `ecofields`). `tick_thermique` doit rester court ; si le bloc thermique grossit,
  l'isoler dans un module `fields/ecofields/thermique.py` (helper pur appelé par
  le conteneur), `container.py` ne portant que l'orchestration.
- **Golden** : chaque tronçon re-fige `tests/test_golden.py` de façon **annoncée**
  (commit « golden RE-FIGÉ MAÎTRISÉ — <cause de dérive> »). Vérifier que la
  dérive correspond bien à la mécanique touchée et à rien d'autre.
- **Couches** : `fields` n'importe jamais `sim`. La nébulosité (table dans
  `constants.py`, donnée pure) est lue par le conteneur ; l'événement météo
  courant est passé en argument depuis l'engine (qui, lui, importe `weather`).

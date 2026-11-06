# Conception — la relève des ligneux (D130)

> Conçue le 2026-11-06 avec Nico (`/conception D130`). Sprint :
> `sprints/vegetal/regeneration/sprint_releve_ligneuse/`. Origine : chronique
> 200 ans de D127 (`verger_mur`, seed 42) — 30 recrues, 25 morts sur 34 par
> ombre, 0 recrue adulte, verger éteint [n=1 run, VM].

## 1. Le problème, mesuré

Diag par recrue (verger_mur, seed 42, 75 ans, n=1 run, VM) :

- Recrutement direct d'un arbre (`MortaliteMixin._reproduction`) : la recrue est
  posée sur le plot le plus lumineux à moins de `RESEED_RADIUS_CM` = 150 cm du
  parent, si la lumière y dépasse 0,35. Or la couronne d'un fruitier adulte fait
  plusieurs mètres : **toute recrue naît sous un parent**.
- `shade_stress_damage` frappe dès `shade_memory` > 0,55, soit une lumière d'été
  sous ~0,45, **quelle que soit la taille** de la plante. Les recrues mortes
  recevaient 0,25 à 0,55 de lumière ; les survivantes à l'an 75, 0,5 à 0,8.
- Le moteur **pose donc des recrues là où il les tue ensuite** (seuil de pose 0,35
  < seuil de dégât ~0,45).
- L'arbre le plus proche d'une recrue morte est le parent ou une sœur posée dans
  le même rayon.

## 2. L'écologie

**Banque de semis.** Le point de compensation lumineux d'une plante (la lumière
où photosynthèse = respiration) monte avec sa taille : un semis a peu de tissus
non photosynthétiques à entretenir. Un jeune arbre survit à 5-10 % de la pleine
lumière ; un héliophile y pousse à peine mais vit, et pousse correctement vers
20-30 %. Sous couvert, les semis **végètent** des années (sciaphiles : des
décennies) puis **repartent** quand une trouée s'ouvre (mort du parent, chute de
branche, tempête). La relève des héliophiles passe par la **trouée** ou la
**dispersion loin du parent** (merle, renard, geai, écureuil) — rarement sous le
parent vivant.

**Critère de fin (Q1, Nico)** : chaque espèce ligneuse se remplace au moins une
fois par génération (taux de remplacement ≥ 1) — sous le parent pour les
sciaphiles, en trouée ou au loin pour les héliophiles — **sans fourré**.

**Figuier (Q3, Nico : réalisme).** La figue commune (*Ficus carica*) noue sans
pollinisation (parthénocarpie) mais ses graines ne sont fertiles que pollinisées
par le blastophage (*Blastophaga psenes*), guêpe qui hiverne dans les figues du
caprifiguier. Son aire est méditerranéenne. En Normandie, pas de blastophage →
pas de graine fertile : le figuier s'y propage par **rejets de souche**. On le
code comme une **condition climatique**, pas comme un « non » en dur, pour que
d'autres climats ouvrent la graine sans toucher au code.

## 3. Les mécaniques (philo #2 : aucune prime à la plante, seule la lumière reçue et le climat décident)

### 3.1 Banque de semis (tronçon ①)
Dans `shade_stress_damage`, pour un **ligneux** (`cls.ligneux`) seulement :

    petitesse = clamp(1 − hauteur / H_GAULE, 0, 1)
    seuil     = SHADE_DAMAGE_THRESHOLD + (SEUIL_SEMIS − SHADE_DAMAGE_THRESHOLD) × petitesse

Départ : `H_GAULE` = 200 cm, `SEUIL_SEMIS` = 0,75 (un semis souffre sous ~0,25
de lumière) [choix de conception, calibrés au ④]. La sévérité se calcule sur ce
seuil effectif (`(sm − seuil)/(1 − seuil)`). Herbacées inchangées : la vis B du
self-thinning (perf ③) et l'invariant sciaphile de `test_stress_chronique`
(courgette) restent intacts. Le signe `ombre` (`sim/semiologie.py`) lit le même
seuil effectif. La reprise à la trouée existe déjà : `grow_plant` règle sa
vitesse sur `growth_factor` (lumière intégrée).

### 3.2 Pose cohérente (tronçon ②)
Pour un arbre (`age_curve`) dans `_reproduction` : le rayon de recherche devient
le **rayon de couronne actuel du parent** (le fruit tombe sous la couronne) ; le
seuil de pose devient la lumière de survie d'un semis, dérivée de `SEUIL_SEMIS`
(une seule source). Le choix du « plot le plus lumineux » reste : c'est
l'abstraction de « parmi tous les semis tombés, celui qui est le mieux placé
s'installe ». Non-arbres inchangés.

### 3.3 Figuier réaliste (tronçon ③)
- Donnée d'espèce (couche `plants`) : un pollinisateur obligatoire et son
  enveloppe climatique (blastophage : mois le plus froid ≥ ~7 °C [ordre de
  grandeur pour le climat méditerranéen, à sourcer]).
- Prédicat `sim` : graine fertile si l'enveloppe est satisfaite par les normales
  de `sim/weather.py` (mois le plus froid = `T_MOY − T_AMP` ≈ 4 °C en Normandie →
  stérile). Il gate le dépôt banque-sol + la recrue directe (`_reproduction`) et
  la graine récoltée (`boucle.py`, pont récolte → banque-joueur). **`is_seed_bearing`
  ne change pas** : il gate aussi la floraison et la paternité.
- Rejets : `clonal_mode = "drageon"` sur le figuier ; `sim/clonal._mature` lit
  `maturity_years` pour un arbre (`age_curve`), sinon un arbre serait « mûr » dès
  sa naissance.
- Voix : fiche encyclopédie (pas de graine sans blastophage, rejets), carnet.

### 3.4 Hors sprint
Dispersion animale (merle, geai, renard) → **D42** (sprint suivant, décision Q2).

## 4. Coût perf
① un facteur dans une fonction déjà appelée : nul. ② balayage sous la couronne
une fois par fructification (~200 plots pour 4 m de rayon) : négligeable. ③ nul.
Risque réel : plus de semis vivants → plus de plantes dans le LightField. Borne :
un plot occupé n'accueille pas de recrue. Mesuré au ④ (≤ +10 % de tick sur `full`).

## 5. Golden
Neutre partout. Espion sur `shade_stress_damage` pendant `tests.test_golden` :
le seul ligneux du smoke (Pommier, < 5 ans) passe 3 fois `shade_memory` > 0,55,
0 dégât [smoke, n=1 run, VM]. ② et ③ ne touchent que des arbres en âge de
fructifier et le figuier, absents du smoke.

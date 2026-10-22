# Conception — « le sol qui respire » (D111)

> **FIGÉE le 2026-10-22** (`/conception`, arbitrages Nico Q1-Q8). Sprint :
> `sprints/champs/sol/sprint_sol_qui_respire/` (8 tronçons). Reprend D110 (g)(h)(i).

## 0. Pourquoi ce sprint

Retour F5 du 2026-10-22 : jardin « pessimiste » (voile cireux bleu-gris d'`acclimatation`
partout), aucun champignon en 5 automnes, butineurs « rares ». Le diagnostic mesuré
(`sprints/champs/sol/sprint_sol_qui_respire/mesures/bilan_eau.py`) montre une cause amont
commune pour l'eau, et deux trous distincts pour les champignons et le nectar.

### 0.1 Bilan hydrique mesuré [monde `full`, 3 graines, 1 run de 3 ans chacune]

| graine | humidité médiane an 0 → 1 → 2 | semaines de pluie/an |
|---|---|---|
| 1515525502 | 1,34 → 0,41 → 0,08 | 3 / 2 / 1 |
| 1521550718 (défaut serveur) | 1,34 → 0,27 → 0,07 | 6 / 2 / 1 |
| 7 | 1,02 → 0,17 → 0,06 | 1 / 1 / 1 |

Prélèvement racinaire 0,012-0,019 /plot/sem contre un apport net ≤ +0,012 ; rosée
0,0079 → 0,0014 /plot/sem quand le sol sèche [graine 1521550718, n=1 run].

### 0.2 Causes vérifiées au code

1. **Climat méditerranéen** : `sim/weather.py` `P_EVENT = 0.15` → 85 % de semaines « Beau
   temps » à nébulosité 0,10. Pluie = aléa seulement (« Pluie prolongée » sem. 27-52 en
   concurrence avec 3 autres ; « Orage » local d'été). Aucune pluie au printemps.
2. **Pluie sans poids** : `PLUIE_APPORT["Pluie prolongée"] = +0.012` ≈ `BASE_RAIN` 0,015.
3. **Rosée prisonnière du sol** : `fields/ecofields/rosee.py` dérive le point de rosée de
   l'humidité du SOL → sol sec ⇒ peu de rosée ⇒ sol plus sec (boucle sèche).
4. **Transpiration sans saison** : `fields/ecofields/uptake.py` `UPTAKE["humidite"]` par
   stade ; une plante dormante boit l'hiver comme l'été → jamais de recharge.
5. **Bois mort qui s'évapore** : `sim/growth/phases.py::_elaguer` retire les segments morts
   sans rien déposer → 0 plot de bois mort sur 1 188, mycélium ≤ 0,24 < seuil 0,30.
6. **Fructification sans pluie** : `fields/population/perception.py` ne gate que l'automne.
7. **Nectar sans espèce** : `fields/population/registry.py::_make_nectar_grid` =
   floraison × goût de famille ; une tomate vaut une phacélie.

## 1. L'eau (tronçon ①)

Pédagogie : en climat océanique, le jardin vit sur la **recharge d'hiver** (plantes
dormantes, pluie qui remplit le sol) puis s'épuise doucement l'été. La rosée est régulière
mais modeste ; elle ne remplace pas la pluie. On corrige le **flux** (climat) et la
**physiologie** (une plante sans feuilles ne transpire pas), jamais la plante (philo #2).

- **1a. Humidité de l'air** : grandeur PURE et déterministe `f(seed, semaine)` (océanique,
  saisonnière, plus sèche sous un épisode sec, saturée sous la pluie), calculée côté `sim`
  et passée en argument à la rosée (les `fields` n'importent pas `sim`). Le point de rosée
  la lit **à la place** de l'humidité du sol. La rosée redevient régulière.
- **1b. Épisodes de pluie dans toutes les saisons** (D-pluie, Nico : **jamais de pluie
  chaque semaine en jeu**). Fréquences cibles : hiver ~1 semaine sur 3, printemps et
  automne ~1 sur 4, été ~1 sur 6 (orages). Un épisode recharge vraiment le sol
  (`PLUIE_APPORT` recalibré). La semaine pluvieuse est couverte (nébulosité haute). Les
  aléas existants (sécheresse, canicule…) restent ; une sécheresse **supprime** la pluie.
  Le préavis diégétique (`sim/ciel.py`) doit voir ces épisodes comme des événements.
- **1c. Transpiration foliaire saisonnière** : le prélèvement d'eau ∝ demande climatique
  (chaleur, ciel clair, vent) × **feuillage présent** (≈ 0 en dormance, défeuillé, ou hors
  végétation) × **type de feuillage** de l'espèce. Constante PAR ESPÈCE, pas un gène
  (patron `resilience_base` ; `tolerance_secheresse` = tolérance de croissance, autre
  notion) : `large` (courge, figuier, tournesol) > `moyen` > `fin` > `cireux`/`duveteux`
  (thym, sauge) > `aiguilles` (sapin). Nico : « les feuilles grandes et ouvertes
  transpirent plus que les épines ».
- **1d. Cible de calibrage** (validée) sur 3 graines, monde `full`, 3 ans : humidité
  médiane annuelle ∈ [1,0 ; 2,0] ; sol presque plein en fin d'hiver ; creux visible en fin
  d'été sans désert. Budget perf : tick ≤ +10 % ET population mesurée (plus d'eau ⇒ plus de
  plantes ⇒ tick ∝ N) — dépassement = arrêt + remontée, pas de contournement.
- **1e. Banc « pluie chaque semaine »** (TEST seulement) : il doit produire SANS réglage
  ad hoc tous les effets aval — sol au plafond 3,0 puis flaques (`eau_surface`), marécage
  dans les creux (`marais_memory`), asphyxie sur argile, recul de l'`acclimatation`, (après
  ③) carpophores chaque semaine. Un maillon muet = couplage cassé.

## 2. Le bois mort (tronçon ②)

Une branche qui meurt (`_elaguer` : sénescence sans apex, plafond de segments) **tombe** :
sa masse (∝ longueur × épaisseur²) est déposée en litière `bois` au plot sous elle. C'est la
source naturelle de bois mort d'un jardin (cladoptose, élagage naturel). Le bois mort doit
être **VISIBLE** au sol et sa dégradation lisible au fil des semaines (Nico) : le pont
expose la masse de bois par plot et son âge ; la vue (⑧) le dessine en sprite à stades de
décomposition (branche fraîche → grise → moussue → fragments).

## 3. Le règne fongique (tronçons ③ ④ ⑤)

### 3.1 Principe moteur (coût de tick nul)

Un seul champ `mycelium` reste la **fonction** écologique (décomposeur, liant, mycorhize).
L'**espèce** qui fructifie est déduite à l'échantillonnage (perception, hors tick) de la
**niche locale** : substrat (bois / humus riche / prairie de graminées), arbre hôte vivant
dont les racines exploitent le plot (familles), saison de l'espèce, pH éventuel. Égalités →
hash spatial déterministe (zéro RNG). Registre **data-driven** : ajouter une espèce = une
entrée de données ; aucun hôte codé en dur.

**Fructification** : la semaine qui suit une semaine de pluie (≈ 3 jours après, tick
hebdomadaire), sur mycélium suffisant et sol humide, dans la fenêtre saisonnière de
l'espèce (plus seulement l'automne). Seuils `CARPO_*` recalibrés après ① et ②.

### 3.2 Catalogue (13 espèces, validé « j'adore »)

| Groupe | Espèce | Comestibilité | Niche / raison d'être |
|---|---|---|---|
| Bois mort | Pleurote en huître | comestible | saprophyte classique : laisser le bois au sol est récompensé |
| Bois mort | Hypholome en touffes | vénéneux | mêmes souches que armillaire/collybie : leçon du sosie |
| Bois mort | Collybie à pied velouté | comestible | seul champignon d'hiver, fructifie après le gel |
| Humus | Coprin chevelu | comestible | sol riche et remué, compost : répond aux gestes |
| Prairie | Rosé des prés | comestible | prairie : récompense de laisser l'herbe |
| Prairie | Clitocybe blanchâtre | mortel | ronds de sorcière, sosie du rosé : piège de la prairie |
| Prairie | Psilocybe lancéolé | psychédélique | graminées humides d'automne : la vision |
| Verger | Morille | comestible | seul champignon de printemps, sous vieux pommiers |
| Mycorhize | Cèpe | comestible | chêne/hêtre adultes : récompense du temps long |
| Mycorhize | Amanite phalloïde | mortel | même hôte que le cèpe : danger sous le même chêne |
| Mycorhize | Amanite tue-mouches | psychédélique + toxique | bouleau pionnier : vision qui coûte |
| Parasite | Armillaire couleur de miel | comestible cuit | feuillus affaiblis puis souche : boucle complète |
| Parasite | Polypore du bouleau | non comestible | achève le bouleau ; amadou d'Ötzi (page secrète) |

### 3.3 Parasite de faiblesse (tronçon ④)

Un parasite n'attaque **que les hôtes déjà affaiblis** (vitalité basse : sécheresse, ombre,
blessure), de ses familles hôtes (données). Il passe par le canal racinaire existant du
campagnol (`plant.root_herbivory_memory` → `plant_uptake`) : l'hôte boit moins, décline,
meurt ; son bois tombe (②) et nourrit les saprophytes. Le joueur agit sur la **cause** (le
milieu qui affaiblit), pas sur le champignon (philo #1-#2).

### 3.4 Une fiche par champignon (tronçon ⑤)

Renverse la décision Q2 du sprint vie macro identifiable (fiche générique unique). Chaque
espèce reçoit ses **5 voix** : encyclopédie 3 niveaux, carnet (concepts : saprophytie,
mycorhize, parasitisme de faiblesse, sosies), page secrète si lore (polypore/Ötzi,
psilocybe, morille, amanite tue-mouches…), magazine (rattachement), événements
(fructification consignée au ledger). Le nom se révèle par l'observation saisonnière
(mécanique existante `sim/signes.crediter_saison`, désormais par espèce).

## 4. Manger un champignon et la vision (tronçon ⑥)

- **Comestible** → Vigueur (comme un fruit). **Vénéneux** → Vigueur effondrée, jamais de
  mort (pas de game over). Tant que l'espèce n'est pas nommée, manger est un pari : le
  savoir protège (philo #6).
- **Psychédélique** → **une semaine de vision** : couleurs plus vives, informations plus
  claires « comme un palier transcendant de compréhension » (carnet interprétatif,
  info-bulle complète), et **plantes et animaux parlent** dans leur info-bulle : ils disent
  leurs besoins (eau, lumière, sol, voisins, nourriture). Phrases **GÉNÉRÉES par le moteur**
  depuis leurs vrais besoins (gabarits), **au survol seulement**.
- **Overdose** (Nico) : un 2ᵉ psychédélique pendant l'effet → TOUTES les phrases sont
  générées à chaque snapshot (déluge d'informations), le temps de l'effet. Coût perf à
  mesurer, borné à la durée de l'effet.
- **Ce qui reste** (Nico) : les êtres sur lesquels le jardinier a passé du temps pendant la
  vision lui laissent un savoir durable — chaque espèce suffisamment survolée gagne un
  palier permanent (au plus une fois par vision, jamais jusqu'au transcendant).
- L'amanite tue-mouches donne la vision ET coûte de la Vigueur.
- Version des voix écrite à la main par espèce = dette lointaine (finition du jeu).

## 5. Nectar par espèce (tronçon ⑦)

Valeur `nectar` ∈ [0,1] par espèce (donnée) : phacélie, bourrache, trèfle, tilleul haut ;
pommier moyen et bref ; tomate ≈ 0 (pollen vibré) ; graminées 0. Nourriture d'un butineur
= floraison × nectar de l'espèce × goût de sa famille. Re-mesurer D110 (i).

## 6. Vue Godot (tronçon ⑧)

Bois mort au sol en sprite à stades de décomposition ; carpophores dessinés **par espèce**
(absorbe la part carpophores de D112 a) ; info-bulle de l'espèce ; geste manger sur un
carpophore ; vision (saturation des couleurs, info-bulle qui parle, overdose). Puis
re-mesure finale de D110 (g)(h)(i). Golden intact.

## 7. Garde-fous

Déterminisme strict (hash, zéro RNG). Couches `plants ← fields ← sim ← engine` : les
grandeurs climatiques se calculent en `sim` et descendent en argument. Ne jamais lancer
`test_epaisseur_500ans`. L'interrupteur « Vigueur infinie » (ON par défaut, test) masque
les effets de manger : bancs de ⑥/⑧ à jouer avec l'interrupteur OFF.

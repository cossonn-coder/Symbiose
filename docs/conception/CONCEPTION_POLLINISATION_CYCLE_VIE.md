# Conception — Arc Pollinisation & Cycle de vie (SYMBIOSE)

> **Document de conception. Aucun code moteur écrit tant qu'il n'est pas figé.**
> Spec de référence pour le futur sprint d'implémentation (MOTEUR → re-fige le
> golden), découpé en sous-sprints. Kickoff :
> `sprints/sprint_pollinisation_cycle_vie/00_conception_kickoff.md`.
>
> Origine : idée Nico (vue·rattrapage 02, gravée 2026-06-16). S'appuie sur
> l'horloge `daylength(wiy)` (sprint saisonnalité vie macro, 2026-06-16). Mémoires
> liées : [[design_pollinisation_cycle_vie]], [[regle_interconnexion_acteurs]],
> [[project_vie_macroscopique]].
>
> **État de rédaction** : **CONCEPTION ÉLARGIE & FIGÉE (2026-06-17)**. La première
> passe (§A–§E, 2026-06-16) était **incomplète** : il manquait (1) un vrai
> **catalogue d'acteurs** pollinisateurs avec cycles de vie multi-rôles (abeille,
> syrphe, papillon), (2) la **trajectoire de butinage** fleur-en-fleur, et (3) la
> **couche joueur ruche & miel**. Cette passe les ajoute et **réorganise le doc en
> deux parties** : Partie I = MOTEUR écologique (source de vérité, re-fige le
> golden) ; Partie II = COUCHE JOUEUR (ruche, miel, piqûre — sprint distinct, mêle
> tick hebdo et temps réel). Toutes les décisions ci-dessous sont tranchées par Nico.

---

## 0. Constat & périmètre

L'arc relie **floraison → pollinisation → fruit → graine** et boucle des **cycles
de vie inter-guildes** (chenille→papillon, larve de syrphe→syrphe). Il ajoute une
**couche joueur** autour de l'abeille (ruche, miel, piqûre). Audit de l'existant
(kickoff §2) :

**Déjà fait (à NE PAS reconstruire)** :
- **Brassage génétique pollinisé** (`sim/reproduction.py`) : `find_father` +
  `child_genes` (biparental/autoféc./introgression) + `pollinator_reach` **modulé
  par la densité locale du champ `pollinisateur`** (D31.2). Modes `wind/insect/self`.
- **Fruits traçables** (`engine/decompo.py:_tick_fruits`) : nouaison annuelle,
  maturation, chute, `manger` ciblé (absorbe D19).
- **Champ `pollinisateur`** saisonnier (`fields/population.py`), ressource =
  proxy `_flower_grid` (stade ≥ 2). Modèle vie macro = **hybride** (champ
  déterministe + sprites échantillonnés perceptifs) — cf [[project_vie_macroscopique]].
- **Structures posables** (`bac`/`pile`, sprint décompo ⑤) : modèle de structure
  joueur réutilisable pour la **ruche**.
- **Sources de Vigueur joueur** (récolte, manger) : canal réutilisable pour le **miel**.

**Le périmètre de l'arc (les vrais gaps)** :

*Partie I — Moteur :*
- **A** Floraison RÉELLE + phénologie (aujourd'hui : proxy de rendu + semaine fixe).
- **B** Nouaison CONDITIONNÉE à la pollinisation (aujourd'hui : inconditionnelle).
- **C** Champ pollinisateur **par type** + ressource = nectar floral réel.
- **D** **Ponts de cycle de vie** : chenille→papillon ET larve de syrphe→syrphe.
- **E** **Registre data-driven** des types de pollinisateurs (`PollinatorSpec`).
- **F** **Butineurs déterministes** (trajectoire fleur-en-fleur, constance florale
  mécanique, dépôt de pollen conspécifique).
- **G** (option) Raffinement du brassage — **NON RETENU**.

*Partie II — Couche joueur :*
- **H** Ruche (structure qui capture un essaim sauvage).
- **I** Miel (production par butinage, récolte → Vigueur, équipement par maîtrise).
- **J** Piqûre (alarme émergente : écraser une abeille → phéromone → piqûre).

**Garde-fous** : **philo #1** (le joueur agit sur le MILIEU ; l'action directe —
écraser une abeille — reste possible mais coûteuse et perturbatrice), **#2** (flux
→ contrainte → réponse émergente, jamais de malus direct sur la plante), **#3**
(déterministe), **#6** (apprentissage diffus, pas de chiffres HUD), **interconnexion**
(tout coexiste). Re-figeage golden MOTEUR attendu, **maîtrisé et annoncé**, isolé
par tronçon.

---

# PARTIE I — MOTEUR ÉCOLOGIQUE (source de vérité, re-fige le golden)

## A. Floraison réelle & phénologie — FIGÉ (2026-06-16)

**Décisions Nico** : état = **scalaire `floraison ∈ [0,1]`** ; déclencheur =
**photopériode + chaleur cumulée** ; **une fenêtre par espèce** (surtout estivale,
défauts par famille/strate).

### A.1 État moteur
- Nouveau champ `floraison: float = 0.0` sur `PlantInstance` (intensité de
  floraison courante). **Pas** d'organes-fleurs en moteur : le rendu les régénère
  procéduralement (contrat `organs` inchangé). `floraison` est l'**assiette** qui :
  - alimente la ressource des champs pollinisateurs (remplace le proxy
    `_flower_grid` stade ≥ 2 — voir §C) ;
  - porte la cible des butineurs (voir §F) et la dose de pollen (voir §B).

### A.2 Double porte de déclenchement (deux signaux complémentaires)
La floraison s'ouvre quand **les DEUX** conditions sont vraies — calque du couple
`phenology`/`warmth` des guildes :

1. **Chaleur cumulée (forçage thermique, GDD)** — *« la plante est prête »* :
   accumulateur **par plante** `gdd_accum`, incrémenté chaque tick de
   `max(0, T_semaine − T_BASE_FLORAISON)` (`T_BASE_FLORAISON` ≈ 6 °C, réutilise
   l'esprit de `T_COLD_ZERO`). **Remis à 0 au passage d'année** (reset annuel,
   déterministe). Porte franchie quand `gdd_accum ≥ gdd_floraison(espèce)`.
2. **Photopériode** — *« c'est la saison »* : `daylength(wiy)` dans la fenêtre
   `[bloom_daylen_min, bloom_daylen_max]` de l'espèce (réutilise `daylength`).
   La quasi-totalité du catalogue = fenêtre estivale (jours longs). Stratégie
   jours-courts (automne) laissée extensible (un seul couple de seuils à régler).

### A.3 Dynamique de l'intensité
- Les deux portes ouvertes → `floraison` **monte** vers 1 (relaxation douce) ;
  une porte retombe (jour trop court / fin de chaleur / fanaison) → `floraison`
  **redescend** vers 0. Knobs de montée/descente = calibrage post-test.
- Gate de **maturité** : une plante trop jeune ne fleurit pas (réutilise
  `maturity_years` pour les fruitiers ; pour les annuelles, un stade minimal). Les
  espèces non reproductrices peuvent garder `floraison` à 0 (neutre).

### A.4 Paramètres par espèce (placeholders, calibrage post-test)
- `gdd_floraison: float` — seuil de degrés-jours (défaut par famille/strate).
- `bloom_daylen_min/max: float` — fenêtre photopériodique (h de jour).
- Réutilise `T_BASE_FLORAISON`, `daylength`, `maturity_years` existants.

### A.5 Golden
En soi l'ajout d'un scalaire neutre + accumulateur **peut rester golden-neutre**
tant qu'il n'est lu par rien (B/C/F branchés ensuite). À confirmer au tronçon ①.

---

## B. Nouaison conditionnée à la pollinisation — FIGÉ (2026-06-16, révisé 2026-06-17)

**Décisions Nico** : gate **continu** ; nouaison en **fin de floraison, par
plante** (remplace `FRUIT_NOUAISON_WEEK`) ; **`self`/`wind` nouent toujours**,
**entomophiles SANS plancher** (0 pollinisateur → 0 fruit, extinction locale
possible — assumée). **Révision 2026-06-17** : la dose `pollen_recu` n'est plus une
intégrale de champ, mais l'**accumulation des dépôts d'agents butineurs
conspécifiques** (voir §F, constance florale mécanique).

### B.1 Dose de pollinisation (depuis les agents, §F)
- Accumulateur **par plante** `pollen_recu: float = 0.0`. Il n'est plus alimenté
  par `densité_champ × floraison`, mais **incrémenté à chaque visite d'un butineur
  porteur de pollen conspécifique** (un agent fidèle à l'espèce X dépose du pollen
  X sur une fleur X — voir §F.4). Déterministe (agents déterministes).
- Remis à 0 à la nouaison (cohorte annuelle suivante repart de zéro).

### B.2 Nouaison en fin de floraison (par plante)
- **Remplace le rendez-vous global `FRUIT_NOUAISON_WEEK`** : chaque plante noue
  quand **sa** `floraison` retombe sous un seuil (fleurs fanées), après avoir
  intégré sa dose. Toujours déterministe (`floraison` dérive de `daylength`+`gdd`).
- Gate complet de mise à fruit : `fruitier` ET `age_years ≥ maturity_years` ET
  a fleuri cette année.
- **Fraction nouée (continue)** : `frac = g(pollen_recu)` ∈ [0,1] (rampe douce,
  saturante — knob calibrage). Nombre de fruits = `round(frac × |organ_sites|)`,
  borné `MAX_ORGANS`. `frac` faible → quelques fruits ; `frac` ≈ 0 → aucun.
- **Par mode** : `self`/`wind` court-circuitent la dose → `frac = 1` (nouaison
  pleine, sans insectes). `insect` → `frac = g(pollen_recu)` **sans plancher**
  (aucun butineur ⇒ 0 fruit ⇒ pression écologique : l'espèce peut décliner
  localement, ce qui valorise les volets C/D/F).

### B.3 Conséquences & interconnexion
- La survie reproductive des fruitiers entomophiles dépend désormais de la
  **chaîne pollinisateur** : floraison (A) → butineurs (F) ← types & saisonnalité
  (C/E) ← cycles larvaires (D). Boucle vivante, philo #6.
- `_tick_fruits` (decompo.py) : la nouaison annuelle inconditionnelle devient
  conditionnelle (lit `pollen_recu`, mode, et le déclencheur passe au seuil de
  fin de floraison par plante). Maturation/chute inchangées.

### B.4 Golden
Re-figeage à évaluer. La seule `fruitier` précoce du smoke est la **tomate**
(`maturity_years=0`) qui **meurt w2-3** (froid de démarrage, [[tomate_mort_precoce]])
AVANT toute floraison/nouaison estivale → **probablement golden-neutre** pour B
(à confirmer). Le pommier (`maturity_years=5`) ne fructifie pas sur 2 ans.

---

## C. Champ pollinisateur PAR TYPE & nectar — FIGÉ (2026-06-16, révisé 2026-06-17)

**Décisions Nico** : ressource du champ = **floraison réelle pondérée par
l'attractivité du TYPE** ; **pas de Vigueur joueur pour le butinage** (récompense
écosystémique ; le miel — Partie II — est un canal séparé). **Révision 2026-06-17** :
un champ `PopulationField` **par type** de pollinisateur (registre §E), pas un seul
champ agrégé.

### C.1 Reconnexion de la ressource (par type)
- `_flower_grid` (proxy stade ≥ 2) **remplacé**. Pour un type `T` donné, sa
  ressource devient :
  `res_T(plot) = Σ_plantes_du_plot (floraison × attractivite_T(espèce))`, normalisée
  (réutilise `FLOWER_REF`). Le butinage qui fait prospérer la guilde devient *vrai*
  (philo #2 : flux floral → capacité de charge → densité émergente).
- Nouveau trait espèce **`attractivite_pollinisateur`** : non plus un scalaire
  unique mais une **préférence par type** (un fruitier à fleur ouverte attire le
  syrphe ; une fleur tubulaire le papillon ; une mellifère profonde l'abeille).
  Défaut par famille florale. → **stratégie joueur** : semer les bonnes mellifères
  soutient le bon pollinisateur (interconnexion). Modélisation concrète du trait
  fixée en §E (registre).

### C.2 Pas de Vigueur joueur (pour le butinage)
Le joueur agit sur le **milieu** (philo #1), il n'est pas l'insecte. La récompense
de cultiver des mellifères reste **indirecte/écosystémique** : plus de
pollinisateurs → plus de nouaison (B) → plus de récolte et de graines. **Le miel
(Partie II) est une exception assumée et distincte** : c'est une récolte de
structure (ruche), pas un crédit lié au butinage de ses fleurs.

### C.3 Golden
La reconnexion de la ressource des champs pollinisateurs **re-figera** (les champs
lisent désormais `floraison × attractivite` au lieu de stade ≥ 2 ; et le
pollinisateur, lu par `pollinator_reach`, influe sur la repro). Re-figeage
MAÎTRISÉ attendu, à isoler. (Se cumule au re-figeage de D.)

---

## D. Ponts de cycle de vie (chenille→papillon, larve→syrphe) — FIGÉ (2026-06-16, généralisé 2026-06-17)

**Décisions Nico** : un cycle de vie n'est PAS une 5ᵉ guilde trophique — c'est un
**stade**, traité à part dans le tick (cohérent avec la décision décompo ④).
**Généralisation 2026-06-17** : le pont chenille→papillon devient **un cas d'un
patron général** — un *pont de cycle de vie* = `(champ_larvaire, effet_trophique
larvaire, → type_adulte)`. Deux instances au démarrage, plus l'abeille (sans pont
au sol).

### D.1 Le patron « pont de cycle de vie »
Chaque pont est data-driven (déclaré dans le registre §E) :

| Pont | Champ larvaire | Effet trophique de la LARVE | → Adulte |
|---|---|---|---|
| **Papillon** | `chenille` | **+herbivorie** (mange le feuillage, comme ravageur) | `papillon` |
| **Syrphe** | `syrphe_larve` | **−ravageur** (prédateur de pucerons, comme auxiliaire) | `syrphe` |
| **Abeille** | *(aucun — nid hors sol)* | — | `abeille` direct (habitat = ruche/rondelle) |

Le syrphe est le **symétrique exact** de la chenille : même moule (champ larvaire +
maturité + ponte + famine + métamorphose), mais l'effet larvaire est *bénéfique*
(il **mange du ravageur**) au lieu de nuisible. Boucle d'interconnexion :
pucerons (ravageur) → nourrissent `syrphe_larve` → métamorphose → `syrphe`
pollinisateur ; et chenilles (herbivores) → `papillon` pollinisateur.

### D.2 Champs par pont (légers, `EcoFields`)
Pour chaque pont, **deux grilles** `[rows][cols] ∈ [0,1]` :
- `<larve>` — densité de larves (ex. `chenille`, `syrphe_larve`).
- `<larve>_nourrie` — maturité moyenne cumulée de la cohorte.
- **Pas un `PopulationField`/`TrophicSpec`** (pas les 4 fonctions trophiques) :
  c'est un cycle de vie, traité à part dans le tick. Coût RAM/CPU négligeable
  (~3,5 Ko/tuile/grille ; tick O(plots) — cf chiffrage kickoff/conversation).

### D.3 Cycle (dans le tick, après les guildes) — générique par pont
1. **Ponte** (fenêtre de ponte ancrée sur `daylength`) : `<larve> += PONTE_RATE ·
   <type_adulte>_local · ressource_larve_local`, bornée. Les adultes pondent là où
   il y a la **ressource de la larve** :
   - papillon → pond où il y a du **feuillage** (la chenille mangera des feuilles) ;
   - syrphe → pond où il y a du **ravageur** (la larve mangera des pucerons).
   → **boucle** adulte → larve.
2. **Action trophique larvaire** : la larve agit selon son pont :
   - `chenille` **s'ajoute** à la pression d'herbivorie — `HERBIVORY_GAIN` (D31.2,
     `sim/effects/perturbations.py`) lit désormais `ravageur + chenille` ;
   - `syrphe_larve` **prédate** le ravageur — entre comme champ prédateur
     supplémentaire de la guilde `ravageur` (réutilise le mécanisme `predators`
     du `TrophicSpec`).
3. **Maturation par la nourriture** : `<larve>_nourrie += MATUR_RATE ·
   nourriture_consommée` (∝ min(`<larve>`, ressource_larve locale)). Pas de
   nourriture → ne mûrit pas.
4. **Famine** : sans ressource, `<larve>` **décline** (mortalité) en plus de ne
   pas mûrir → régulation boom-bust (trop de larves épuisent leur ressource et
   s'effondrent). Réaliste, auto-limitant.
5. **Métamorphose** : `<larve>_nourrie ≥ METAM_SEUIL` → `<type_adulte> +=
   <larve> · (1 − METAM_PERTE)` (perte = prédation/parasitisme/échec), puis
   `<larve> = 0`, `<larve>_nourrie = 0`. **Boucle** larve → adulte.

### D.4 Effet émergent recherché
Pic de larves au printemps → métamorphose → **bouffée de pollinisateurs en été**,
pile pour la floraison/nouaison (B). Le papillon : ravageurs du printemps →
pollinisateurs de l'été (répit d'herbivorie en prime). Le syrphe : flambée de
pucerons → larves prédatrices → moins de pucerons ET plus de pollinisateurs.
Cycle complet, interconnexion maximale (philo #6).

### D.5 Paramètres (placeholders, calibrage post-test)
Par pont : `PONTE_RATE`, fenêtre de ponte (seuils `daylength`), `MATUR_RATE`,
`METAM_SEUIL`, `METAM_PERTE`, taux de mortalité de famine. Tous à régler jeu en main.

### D.6 Golden
**Re-figeage MOTEUR MAÎTRISÉ attendu** (annoncé) : (a) `HERBIVORY_GAIN` lit
`ravageur + chenille` → pression d'herbivorie change ; (b) `syrphe_larve` entre
comme prédateur du ravageur → densité ravageur change → herbivorie change. À
isoler. **Invariant** : à `chenille = 0` ET `syrphe_larve = 0` partout (aucun
adulte pour pondre, ou hors fenêtre), la pression d'herbivorie et la prédation du
ravageur sont **strictement inchangées** vs aujourd'hui → toute dérive est
attribuable aux seuls cycles larvaires.

---

## E. Registre data-driven des pollinisateurs — FIGÉ (2026-06-17)

**Décision Nico** : pas un ensemble figé en dur, mais un **registre extensible
par données**. On démarre à 3 types ; on en ajoute (bourdon, abeille solitaire…)
sans recoder, juste en déclarant un `PollinatorSpec`.

### E.1 `PollinatorSpec` (un type = une donnée)
Champs (placeholders, calibrage post-test) :
- `name: str` — clé du champ `PopulationField` (`abeille`, `syrphe`, `papillon`…).
- `attractivite: dict[famille_florale → float ∈[0,1]]` — préférence florale (le
  nectar perçu par CE type ; alimente `res_T` en §C). Défaut générique.
- `daylen_min/full: float` — fenêtre d'activité photopériodique (réutilise la
  porte saisonnière des guildes).
- `bridge: LifeCycleBridge | None` — pont larvaire optionnel (§D) : `(champ_larve,
  effet_trophique, ressource_larve)`. `None` pour l'abeille (nid hors sol).
- `habitat_fn` — terme-source d'habitat (rondelle dédiée et/ou **ruche** pour
  l'abeille, §H).
- `forager: ForagerParams` — paramètres d'agent butineur (§F) : nombre max
  d'agents échantillonnés, vitesse, rayon de perception, ténacité de constance.

### E.2 Trois types au démarrage
| Type | Préférence florale | Fenêtre | Pont larvaire | Habitat |
|---|---|---|---|---|
| `abeille` | mellifères profondes (nectarifères) | été large | aucun | ruche (§H) + rondelle |
| `syrphe` | fleurs ouvertes (ombellifères, composées) | printemps→été | `syrphe_larve` (−ravageur) | rondelle auxiliaire |
| `papillon` | fleurs tubulaires | été | `chenille` (+herbivorie) | rondelle / friche |

### E.3 Couches & golden
Le registre vit dans `fields/population.py` (ou un module data dédié) ; il
**instancie N `PopulationField`** (un par type) dans `EcoFields` (container.py).
Re-figeage cumulé avec C/D (plus de champs lus par `pollinator_reach`/herbivorie),
**maîtrisé**. Invariant : à attractivité/ponte nulles, comportement identique.

---

## F. Butineurs déterministes & constance florale — FIGÉ (2026-06-17)

**Décision Nico** : **trajectoire d'agents explicite**, **mécanique** (pas
décorative) : les butineurs marchent de fleur en fleur et **déposent réellement**
le pollen. **Constance florale mécanique** : pollen conspécifique uniquement.

### F.1 Le basculement assumé (évolution de [[project_vie_macroscopique]])
Le modèle vie macro tranché = deux couches : mécanique = **champs déterministes** ;
perception = **sprites échantillonnés** (purement visuels, `activite()` = « PUR
rendu »). Ici, **une partie de la perception passe dans la mécanique** : les
butineurs portent le transport de pollen. Conséquences ACTÉES :
- Les agents sont **simulés en Python** (source de vérité), **déterministes**
  (position et choix dérivés de `seed + _hash_noise(tuile, agent_id, semaine)`,
  **jamais de RNG vivant**, philo #3).
- Ils sont **exposés au snapshot** (positions, espèce-cible, état) → Godot les rend.
- Les champs `PopulationField` par type (§C/E) **restent** : ils donnent le
  **réservoir** (combien d'agents de chaque type, et où) ; les agents en sont
  **échantillonnés déterministement** et portent la mécanique fine du transport.

### F.2 Échantillonnage des agents
Pour chaque type `T` et chaque tuile : nombre d'agents borné = `round(densité_moy_T
× N_max_T)` (pop bornée, `ForagerParams`). Positions initiales dérivées du hash
(canaux dédiés, décorrélés par type — réutilise le pattern des canaux `_hash_noise`
de population.py). Recréés/réensemencés chaque tick à partir du champ (pas d'état
persistant entre ticks au-delà du champ — déterminisme reproductible).

### F.3 Marche guidée par gradient (foraging)
Chaque agent a une **espèce-cible** (constance florale, §F.4). À chaque sous-pas
du tick :
- il se déplace vers le **plot voisin maximisant `floraison` de son espèce-cible**
  (montée de gradient locale, rayon de perception `ForagerParams`), avec
  tie-break déterministe par hash ;
- s'il n'y a plus de fleur de son espèce à portée, il **change d'espèce-cible**
  (fin de tournée) vers l'espèce dominante en floraison à portée.

### F.4 Constance florale & dépôt conspécifique (le cœur mécanique)
- Un agent **porte** une charge de pollen étiquetée par espèce (`carried_species`).
- En visitant une fleur de l'espèce X (`floraison_X(plot) > 0`) :
  1. **dépose** sa charge si `carried_species == X` → `plante.pollen_recu +=
     DEPOT · charge` (philo #2 : flux de visites → dose → nouaison) ;
  2. **recharge** sur X (`carried_species = X`, charge ↑).
- Si l'agent change d'espèce, sa charge précédente est **perdue** (pollen déposé
  sur la mauvaise fleur = gaspillé, comme dans la nature) → la constance émerge
  comme un *avantage* sans règle ad hoc.
- **Modes plante** : `self`/`wind` (§B) ignorent les agents (nouaison pleine). Seuls
  les `insect` lisent `pollen_recu`.

### F.5 Coût & déterminisme
O(agents × sous-pas) par tuile, borné (~20–50 agents/tuile) → négligeable face au
budget hebdomadaire (1 tick = 1 semaine = 60 s réel). Entièrement reproductible
(hash + champs). **Aucune** dépendance à l'ordre d'itération non déterministe.

### F.6 Golden
Re-figeage MAÎTRISÉ : `pollen_recu` (donc la nouaison B) provient maintenant des
agents. Mais (cf B.4) la tomate meurt avant nouaison estivale et le pommier ne
fructifie pas sur 2 ans → **impact golden probablement nul sur le smoke** (à
confirmer). Invariant : à 0 agent (0 pollinisateur), `pollen_recu` reste 0 →
nouaison `insect` = 0, identique au comportement « sans plancher » de B.

---

## G. Brassage multi-pères (option) — FIGÉ : NON RETENU (2026-06-16)

**Décision Nico** : garder l'existant. `pollinator_reach` (rayon du père ∝
densité pollinisateur, D31.2) + `child_genes` biparental couvrent déjà le
« mélange des pollens ». **Pas de tronçon dédié.** Raffinement multi-pères
laissé en backlog lointain si le calibrage le réclame. *(Note : avec les agents
§F, le « père » pourrait à terme être l'espèce effectivement transportée par les
butineurs — raffinement futur, hors périmètre.)*

---

# PARTIE II — COUCHE JOUEUR : RUCHE & MIEL (sprint distinct, hebdo + temps réel)

> Cette partie quitte le pur moteur écologique. Elle mêle **tick hebdomadaire**
> (production de miel) et **temps réel** (piqûre au curseur, côté Godot). Elle
> s'implémente **APRÈS** le moteur (Partie I), en sprint séparé.

## H. Ruche — FIGÉ (2026-06-17)

**Décision Nico** : la ruche **capture un essaim sauvage existant** (elle ne
fabrique pas d'abeilles ex nihilo) — il faut d'abord soigner le milieu (philo #1).

### H.1 Structure
- Nouvelle **structure posable** (modèle `bac`/`pile` du sprint décompo ⑤) :
  `ruche`, posée par le joueur sur un plot.
- État : `essaim ∈ [0,1]` (peuplement), `miel ∈ [0, MIEL_MAX]` (réserve).

### H.2 Capture de l'essaim (agir sur le milieu d'abord)
- Une ruche vide **attire un essaim** si le champ `abeille` local est suffisant :
  `essaim += CAPTURE_RATE · abeille_local` (saturant), seulement au-dessus d'un
  seuil `ESSAIM_MIN`. Pas d'abeilles dans la nature → **ruche vide** (le joueur
  doit d'abord semer des mellifères, offrir habitat — philo #1/#2).
- Une ruche peuplée devient à son tour un **terme-source d'habitat** `abeille`
  (via `habitat_fn` du `PollinatorSpec` abeille, §E) → renforce la population
  locale → boucle vertueuse (interconnexion).
- Abandon/famine : essaim décline si l'habitat/nectar s'effondre (déterministe).

### H.3 Golden
La ruche est une structure joueur **optionnelle** : absente du smoke golden →
**golden neutre**. (Le golden n'instancie pas de ruche.)

---

## I. Miel & récolte — FIGÉ (2026-06-17)

**Décision Nico** : récolte du miel → **Vigueur joueur**, **gated par un
équipement débloqué par MAÎTRISE** (pas de craft/atelier). Canal de Vigueur
distinct du butinage (cf C.2).

### I.1 Production
- `ruche.miel += MIEL_RATE · essaim · nectar_butine_local` chaque tick, plafonné
  `MIEL_MAX`. `nectar_butine_local` = ressource florale réellement exploitée par
  l'abeille (réutilise `res_abeille` de §C : `floraison × attractivite_abeille`).
  → Le miel est **l'intégrale du nectar mellifère butiné** : pas de fleurs
  nectarifères = pas de miel (philo #2, interconnexion floraison↔miel).

### I.2 Récolte (action joueur, gated équipement)
- Nouvelle action `recolter_miel` (geste joueur, `sim/actions.py`) : transfère
  `ruche.miel` → **Vigueur joueur** (canal récolte, comme cueillir un fruit),
  vide la réserve.
- **Gate équipement** : l'action n'est « sûre » que si le joueur possède
  l'**équipement apicole** (combinaison + enfumoir). Sans équipement → la récolte
  déclenche l'**alarme** et la **piqûre** (§J) : coût Vigueur, récolte partielle
  ou ratée. Apprentissage diffus (philo #6) : on apprend à ses dépens qu'il faut
  l'équipement.

### I.3 Équipement débloqué par maîtrise
- L'équipement apicole **n'est pas fabriqué** : il **apparaît** comme capacité
  quand le joueur atteint un **palier de maîtrise** du concept « pollinisateurs /
  abeilles » (cohérent avec « l'extension du terrain par maîtrise » — la
  connaissance ouvre l'accès). Pas de système d'inventaire/craft introduit ici.
- → relie l'arc au système **maîtrise** existant (D12) : récolter le miel sans se
  faire piquer est une **récompense de compréhension**, pas un achat.

### I.4 Golden
Récolte = action joueur, absente du smoke → **golden neutre**.

---

## J. Piqûre — alarme émergente — FIGÉ (2026-06-17)

**Décision Nico** : pas une pénalité forfaitaire en dur, mais une **réaction
émergente** : écraser une abeille (ou récolter sans équipement) libère une
**phéromone d'alarme** locale ; les abeilles dans le rayon **piquent le curseur**.

### J.1 Déclencheur (action directe coûteuse — philo #1)
- **Écraser une abeille** (action directe `ecraser` à proximité du curseur) OU
  **récolter du miel sans équipement** (§I.2) → pose un **signal d'alarme** local
  (phéromone) au point d'action : un terme transitoire (champ ou événement) qui
  décroît dans le temps.

### J.2 Réponse (temps réel, côté saison/Godot)
- Tant que l'alarme est active, les abeilles présentes dans le rayon **piquent le
  curseur** : chaque piqûre **coûte de la Vigueur joueur** + ajoute de la
  **perturbation** locale (la guilde se replie — la perturbation est déjà un
  intrant des `PopulationField`, philo #2).
- L'équipement apicole (§I.3) **annule/atténue** la piqûre (l'enfumoir calme,
  la combinaison protège) → la récolte protégée devient possible.

### J.3 Nature & implémentation
- C'est une mécanique **temps réel** (phase saison), partiellement **côté Godot**
  (réaction au curseur), pilotée par l'état moteur (densité `abeille`, alarme).
  Le moteur Python expose l'alarme + la densité ; Godot anime la piqûre et
  applique le coût Vigueur.
- Philo #1 incarnée : l'action directe (écraser) **reste possible** mais
  **émergemment punie** (l'écosystème répond), sans règle « −X Vigueur » arbitraire.

### J.4 Golden
Mécanique joueur temps réel, hors tick déterministe du smoke → **golden neutre**.

---

# SYNTHÈSE & DÉCOUPE

## K. Synthèse moteur

### K.1 Nouveaux éléments moteur
| Élément | Où | Rôle |
|---|---|---|
| `floraison: float` | `PlantInstance` | intensité de floraison (assiette) |
| `gdd_accum: float` | `PlantInstance` | degrés-jours cumulés (reset annuel) |
| `pollen_recu: float` | `PlantInstance` | dose conspécifique déposée par agents (reset à la nouaison) |
| `gdd_floraison`, `bloom_daylen_min/max` | famille/espèce | seuils thermique + photopériode de floraison |
| `attractivite` (par type) | espèce × `PollinatorSpec` | nectar perçu par chaque type (ressource du champ) |
| `PopulationField` par type | `EcoFields` | `abeille`, `syrphe`, `papillon` (registre §E) |
| `PollinatorSpec` (registre) | `fields/population.py` | type data-driven (préférence, fenêtre, pont, forager, habitat) |
| ponts larvaires `chenille(_nourrie)`, `syrphe_larve(_nourrie)` | `EcoFields` | cycles de vie (densité + maturité) |
| butineurs (agents) | nouveau module sim + snapshot | trajectoire fleur-en-fleur, constance florale, dépôt pollen |
| structure `ruche` (`essaim`, `miel`) | `world` structures | Partie II (hub abeille + réserve miel) |
| action `recolter_miel` | `sim/actions.py` | Partie II (miel → Vigueur, gated maîtrise) |
| alarme / piqûre | moteur + Godot | Partie II (réaction temps réel) |
| constantes `T_BASE_FLORAISON`, `PONTE_RATE`, `MATUR_RATE`, `METAM_SEUIL`, `METAM_PERTE`, `CAPTURE_RATE`, `MIEL_RATE`, `MIEL_MAX`… | constantes | calibrage post-test |

### K.2 Points de greffe
- `fields/population.py` : registre `PollinatorSpec` + N `PopulationField` ;
  ressource par type ← `floraison × attractivite` (remplace `_flower_grid`).
- `fields/ecofields/container.py` : instanciation des champs par type + ponts.
- `sim/effects/perturbations.py` : `HERBIVORY_GAIN` lit `ravageur + chenille` ;
  `syrphe_larve` ajouté comme prédateur du `ravageur`.
- `sim/engine/decompo.py:_tick_fruits` : nouaison conditionnelle (lit `pollen_recu`,
  mode) déclenchée en **fin de floraison par plante** (remplace `FRUIT_NOUAISON_WEEK`).
- nouveau pas de tick : floraison (GDD + `daylength`) → agents butineurs (dépôt
  pollen) → ponts larvaires (ponte/trophie/maturation/famine/métamorphose).
- Partie II : structures (`ruche`), `sim/actions.py` (`recolter_miel`), pont
  snapshot (agents + alarme), Godot (piqûre temps réel).

## L. Découpe en sous-sprints (chacun préserve ou re-fige le golden de façon isolée)

**Partie I — MOTEUR (re-fige le golden, isolé) :**
1. **① Floraison réelle + phénologie** (A) : `floraison`, `gdd_accum`, fenêtre par
   espèce. Rien ne lit encore `floraison` → **golden visé NEUTRE** (tronçon sûr).
2. **② Registre + champs par type + nectar** (C/E) : `PollinatorSpec`, N
   `PopulationField`, ressource `floraison × attractivite`. **Golden re-figé
   MAÎTRISÉ** (le champ pollinisateur change de ressource).
3. **③ Butineurs déterministes** (F) : agents, constance florale, dépôt
   `pollen_recu` + exposition snapshot. **Golden probablement neutre** sur le smoke
   (tomate/pommier, cf F.6) — à confirmer.
4. **④ Nouaison pollinisée** (B) : `_tick_fruits` lit `pollen_recu`, modes, fin de
   floraison par plante. **Golden probablement neutre** (cf B.4).
5. **⑤ Ponts de cycle de vie** (D) : `chenille`→`papillon` ET
   `syrphe_larve`→`syrphe` ; `HERBIVORY_GAIN` lit `ravageur + chenille` ;
   `syrphe_larve` prédateur du ravageur. **Golden re-figé MAÎTRISÉ** (invariant :
   larves=0 ⇒ herbivorie/prédation inchangées).

Ordre conseillé ①→②→③→④→⑤ (le neutre d'abord, puis les re-figeages isolés).
Pas de tronçon brassage (G non retenu).

**Partie II — COUCHE JOUEUR (golden neutre, sprint distinct APRÈS le moteur) :**
6. **⑥ Ruche & miel** (H/I) : structure `ruche`, capture d'essaim, production
   miel, action `recolter_miel` gated maîtrise. **Golden neutre** (structure absente
   du smoke).
7. **⑦ Piqûre — alarme émergente** (J) : signal d'alarme + réaction temps réel
   (moteur + Godot). **Golden neutre.**

**La vue Godot** (sprites papillons/chenilles/syrphes/abeilles, butineurs animés
fleur-en-fleur, fleurs réelles, fruits gated, ruche, piqûre) suit/accompagne —
la vue échantillonne déjà les champs et lit le snapshot (agents exposés en §F).

## M. Invariants transverses
Déterminisme (`seed`/`_hash_noise`/`daylength`, jamais de RNG vivant — y compris
les agents §F) ; **philo #1** (action directe possible mais coûteuse/émergente —
la piqûre §J) ; **philo #2** (flux→contrainte→émergence, jamais de malus direct
sur la plante) ; interconnexion (fleurs ↔ types de pollinisateurs ↔ butineurs ↔
fruits ↔ graines ↔ larves ↔ ravageurs ↔ ruche/miel) ; re-figeages golden annoncés
et isolés par tronçon ; couches `plants ← fields ← sim` respectées.

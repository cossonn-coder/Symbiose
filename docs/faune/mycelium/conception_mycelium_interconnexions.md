# CONCEPTION — Mycélium & interconnexions du jardin (champignons décomposeurs + symbiose mycorhizienne + raffinement compost)

> **Statut : conception FIGÉE (2026-06-25, conversation de design tranchée par Nico).**
> Prête pour l'implémentation. Fait suite à la gravure backlog « Raffinement
> compost & interconnexions du jardin » (2026-06-16, retour F5 vue·rattrapage 03)
> et **prolonge** `docs/champs/sol/conception_decomposition_compost.md` (sprint décompo ①–⑤,
> structures bac/pile) qu'il faut avoir en tête.
>
> **Acteur NEUF : le mycélium.** Il n'existait jusqu'ici que par allusions
> (substrat `mycelium_use`, maladies fongiques M5, « part fongique incluse » dans
> le terme vers `fields/population.py:391`). Ce sprint le **promeut en acteur de
> plein droit** : un champ déterministe + des carpophores visibles, qui décompose
> le bois, lie le sol, **se relie aux racines vivantes** (wood-wide-web) et nourrit
> la faune.
>
> **Choix d'ambition (Nico, 2026-06-25)** : acteur **visible complet** (champ +
> sprites + interaction faune) ; **mycorhize INCLUSE** (symbiose champignon ↔
> racines) ; **les 6 facets a–f dans un seul doc figé**.
>
> **Re-figeage golden LARGE annoncé** : décompo (terme fongique sur le bois) +
> uptake (boost phosphore mycorhizien) + structure (liant `om_stable`) +
> population (faune fongivore). Maîtrisé et documenté (§6). Carpophores et UX
> 2 clics = **golden-neutres**.

---

## 0. L'intention (source de vérité du « quoi »)

Gravure Nico (2026-06-16), six facets :

- **(a)** bac/pile = **stock au niveau TUILE**, pas posé à un plot — `composter`
  sur N'IMPORTE quel plot verse dans le bac de la tuile, `empiler_bois` idem.
- **(b)** `epandre` en **2 clics** : clic sur le bac → clic sur le plot ciblé.
- **(c)** cycle de **maturation du compost explicite** (lisible, présent).
- **(d)** faune attirée par le compost **ET** la pile (abris + nourriture).
- **(e)** **NOUVEL acteur : champignons / mycélium** dans la décomposition + leur
  attrait nourricier pour certains animaux.
- **(f)** **RÈGLE TRANSVERSE** : tisser des liens explicites entre chaque acteur
  (plantes, faune, champignons, sol, structures) — tout coexiste
  (cf. mémoire `regle_interconnexion_acteurs.md`).

Principe **non négociable** (philo #2) : aucune action, aucun acteur ne touche la
plante par un bonus/malus direct. Tout passe par un **champ / un dépôt** ; la
réponse biologique (microbes, vers, champignons, faune, succession) est
**émergente** au tick suivant.

---

## 1. Le mycélium — modèle (facet e)

### 1.1 Représentation : un champ + des carpophores

- **Réseau** = nouveau champ scalaire `mycelium` dans `EcoFields`
  (`fields/ecofields/container.py`, patron `microbiome` : `GridField`,
  `max_val=1.0`, granularité **plot**, **zéro RNG** — déterministe, philo #3).
  Le mycélium est **sessile et lié au substrat** → ce n'est **PAS** une 5ᵉ guilde
  de `PopulationField` (cohérent avec le refus du 5ᵉ guilde du sprint décompo §4).
  Sa place naturelle est parmi les champs édaphiques (à côté de `microbiome`).
- **Carpophores** (champignons visibles) = sprites **échantillonnés**
  déterministes (patron vie macro `sample_sprites`), **dérivés** du champ — aucun
  état propre. Ils apparaissent là où `mycelium` est haut **+** pic d'humidité
  récent (après pluie) **+** saison favorable (automne). **Golden-neutres** :
  c'est de la **perception**, pas de la simulation.

> Décision figée (i) : **un seul champ** `mycelium` rend les deux services
> (saprophyte ET mycorhizien). On ne sépare pas en deux champs — un seul réseau,
> plus simple à calibrer et à lire. La distinction des deux services se fait au
> point de branchement (décompo vs uptake), pas dans l'état.

### 1.2 Dynamique par tick et par plot (placeholders, calibrage post-test)

```
croissance = K_G × substrat × humidite × fenetre_temp
declin     = K_D × mycelium × (secheresse + epuisement_substrat)
mycelium  += croissance − declin            # clampé [0, 1] par le GridField
```

- **`substrat`** = carbone disponible, **pondéré bois** : la litière `bois` du
  plot (fort — c'est la spécialité fongique), `om_active`, et un bonus de
  **proximité d'une pile** (§3). Substrat épuisé → `epuisement_substrat` ↑ → le
  réseau régresse (pas de nourriture, pas de réseau).
- **`humidite`** : le mycélium a besoin d'eau (le champ humidité existant). La
  **sécheresse** (humidité basse) alimente le terme de déclin.
- **`fenetre_temp`** : cloche douce sur `temperature_sol` (le mycélium ralentit
  au gel et à la canicule). Repli neutre si non calibré.
- **Travail du sol = perturbation EVENT-DRIVEN, pas un terme de tick.** ⚠️ Le
  champ `disturbance` du moteur est **environnemental** (bruit, sol nu favorisant
  les pionnières dans la succession) — **ce n'est PAS** le travail du sol du
  joueur. Le bon branchement (cohérent avec le jumeau existant) : **`becher`
  retire un quantum de `mycelium`** (`gestes.py:407`, miroir EXACT de son malus
  `microbiome`/`lombric`/`structure_sol`) ; **`grelinette` le préserve**
  (`gestes.py:428`, ne touche pas le mycélium, voire le favorise via le `lombric`/
  la structure). C'est ce qui donne enfin un **sens écologique différencié** à
  bêcher (détruit le réseau) vs grelinette (le préserve) — à l'œil, comme les vers.

### 1.3 État de repos NEUTRE (garde-fou golden ①)

Au lancement, `mycelium = 0` partout. Tant que le champ est nul, **aucun de ses
effets (§2) ne s'applique** (tous sont `× mycelium` ou `× (1 + mycelium)` avec
`mycelium = 0`). Le sous-sprint ① (champ + dynamique seuls, effets débranchés)
vise donc un golden **re-figé localisé** uniquement par la présence du champ dans
le pipeline, pas par un changement de comportement écologique.

---

## 2. Trois rôles → les interconnexions (facet f, le cœur)

Le mycélium est l'acteur **connectif** par excellence. Chaque rôle est un lien
explicite vers un autre acteur, via un champ (jamais en direct sur la plante).

| Rôle | Acteur relié | Branchement moteur | Golden |
|---|---|---|---|
| **Saprophyte** (décompose le bois) | litière / sol | terme fongique `× (1 + α·mycelium)` sur la décompo du tissu **`bois`** dans `tick_decomposition` | re-fige (décompo) |
| **Liant du sol** (glomaline) | sol | `mycelium` ajoute **lentement** à `om_stable` (et/ou `structure_sol`) — le réseau agrège le sol | re-fige (léger) |
| **Mycorhizien** (wood-wide-web) | **plantes vivantes** | dans `plant_uptake` (`container.py:701`), **boost borné du `p`** (phosphore) ∝ `mycelium` sous l'empreinte racinaire `root_plots` ; **miroir** dans la façade read-only `qi_local` (`sim/vigueur_plante.py`) | re-fige (uptake) |
| **Nourriture faune** | **faune** | une fraction `mycelium`/carpophores gonfle la guilde fongivore — **`detritivore`** est le meilleur candidat (collemboles, déjà une guilde de `population.py`) ; à défaut `auxiliaire`. Patron de l'attraction `fruit` du décompo §4 | re-fige (population) |
| **Perturbation** | sol travaillé | **event-driven** : `becher` retire un quantum de `mycelium` (`gestes.py:407`, miroir microbiome/lombric) ; `grelinette` préserve (`gestes.py:428`). PAS le champ `disturbance` (environnemental, ≠ travail joueur — cf. §1.2) | event-driven (golden ~intact) |

### 2.1 Le saprophyte ferme la boucle du bois

Le `bois` est le tissu « très lent » (~0.02/sem, `CONCEPTION_DECOMPOSITION_COMPOST`
§1.2). Le mycélium est **l'acteur manquant** qui explique pourquoi une pile de BRF
/ un squelette finit par devenir humus forestier. La décompo `bois` reste lente
**sans** champignon, et s'accélère **là où le réseau s'est installé** (sol non
travaillé, humide, riche en bois). Pédagogie : « le bois nu pourrit mal ; couvert,
humide, non bêché, le champignon le digère ».

### 2.2 La mycorhize : « pourquoi mon phosphore ne passe pas »

Le `p` est le nutriment le plus **étroit** chez nous (`PH_WIDTH["P"]=1.0`,
bloqué des deux côtés de la fenêtre pH). La mycorhize **étend la portée racinaire
effective pour le phosphore** : `plant_uptake` puise plus de `p` là où `mycelium`
est présent sous l'empreinte. C'est l'interconnexion plante ↔ champignon ↔ sol,
et une **réponse partielle** à un cas pédagogique roi déjà identifié dans le code
(`constants.py:287` « pourquoi mon phosphore ne passe pas »).

> Décision figée (ii) : la mycorhize boost **`p` seulement** (pas N/K). C'est le
> service réel (le P est immobile et difficile ; N/K le sont moins) et ça reste
> pédagogiquement net. Le boost est **borné** (un plafond `MYCO_P_BONUS`, comme
> `UPTAKE_MICRO_BONUS`) — jamais un uptake infini.

> Garde-fou philo #2 : la mycorhize ne pose **aucun bonus sur la plante** ; elle
> modifie ce que le sol **rend disponible** au prélèvement. Une plante mal placée
> (mauvais pH) reste mal placée — la mycorhize aide à puiser, elle ne déverrouille
> pas la fenêtre pH.

### 2.3 Distinction stricte avec le pathogène

Le mycélium ajouté est **bénéfique** (saprophyte + mycorhizien). Les **maladies
fongiques M5** (`sim/effects/perturbations.py`) restent un acteur **distinct** et
inchangé. Aucun couplage entre les deux dans ce sprint (un mycélium de
décomposition n'attaque pas une plante vivante).

---

## 3. Structures revues (facets a, b, c, d)

Prolonge `docs/champs/sol/conception_decomposition_compost.md` §5 et son implémentation
(`sim/actions/compost.py`, `fields/ecofields/litiere.py:Structure`).

### 3.1 (a) Bac & pile au niveau TUILE

Aujourd'hui `Structure(plot=(r,c))` est liée à un plot, et `composter`/
`empiler_bois` ne ramassent que le **plot porteur**. Désormais :

- La `Structure` est **rattachée à la tuile** (un identifiant de tuile, plus un
  plot). Une tuile porte **au plus un bac et une pile** (à confirmer au ⑤ : un
  seul de chaque par tuile, simple et lisible).
- `composter(plot → bac de la tuile)` et `empiler_bois(plot → pile de la tuile)`
  acceptent **n'importe quel plot de la tuile** et versent dans la structure de
  cette tuile.
- L'habitat `auxiliaire` de la pile est **déjà** au niveau tuile (rondelle,
  `compost.py:poser_pile`) → on **aligne** le bac sur ce niveau.

### 3.2 (b) `epandre` en 2 clics

Le moteur gère **déjà** `q=None ⇒ tout` + bornage par `compost_mur`
(`compost.py:epandre`). Le neuf est **l'UX à 2 cibles** : clic sur le bac (source)
→ clic sur le plot cible (destination). C'est un ajout **protocole pont + Godot**
(`tools/simserver`, `WorldView`), pas une mécanique écolo. → traité au ⑥ (vue).

### 3.3 (c) Maturation explicite + colonisation fongique

La maturation existe (`tick_structures`, drapeau `retourne_restant`,
`litiere.py`). On la rend **présente et lisible**, et on la **relie au mycélium** :

- Le tas (bac, pile) est un **habitat fongique de choix** → il se fait **coloniser
  par le `mycelium`** (le tas porte sa propre valeur de colonisation fongique).
- La présence de champignon **accélère et structure** la maturation : phases
  lisibles **frais → en cours → mûr**. La pile (bois) mûrit surtout par voie
  fongique ; le bac (tendre) par voie microbienne + fongique.
- Lie **(c) maturation**, **(d) faune** et **(e) mycélium** en un seul geste de
  design : le tas vit, héberge le champignon, qui attire la faune.

### 3.4 (d) Faune sur le compost ET la pile

- La **pile** garde son habitat `auxiliaire` existant (§4.1 décompo).
- Le **bac** attire **désormais aussi** : la colonisation fongique du tas (§3.3)
  gonfle une fraction **`auxiliaire`** (fongivores) — même patron que l'attraction
  du `fruit` (`CONCEPTION_DECOMPOSITION_COMPOST` §4). Compost vivant = compost
  habité.

---

## 4. Vue — carpophores, tas colonisé (conçue ici, rendue quand Godot reprend)

> Non implémentable/testable tant que l'intégration Godot est en pause. On
> **conçoit**, on rendra plus tard, on ajustera au besoin.

- **Carpophores** : sprites échantillonnés (§1.1) là où le réseau est dense et
  humide — le joueur **voit** les champignons pousser après la pluie, en automne,
  sur le bois mort et les zones non bêchées. Indice diégétique direct de la santé
  fongique du sol.
- **Tas colonisé** : bac/pile montrent leur **avancement de maturation** (frais →
  mûr) et un voile fongique quand le mycélium les habite.
- **`epandre` 2 clics** : retour visuel source → cible (§3.2).
- Le réseau lui-même reste **invisible** (souterrain) sauf via l'overlay debug F6
  (le registre `fields` par introspection exposera `mycelium` automatiquement —
  palette à ajouter côté vue).

---

## 5. Découpage en sous-sprints indépendants

| # | Sous-sprint | Contenu | Golden |
|---|---|---|---|
| ① | **Champ `mycelium` + dynamique** | nouveau `GridField` dans `EcoFields`, croissance/déclin (§1.2), lecture `disturbance`/humidité/`temperature_sol`, état de repos NEUTRE, effets §2 **débranchés** | re-figé localisé |
| ② | **Saprophyte + liant** | terme fongique `× (1+α·mycelium)` sur la décompo `bois` ; liant `om_stable` lent | re-figé (décompo) |
| ③ | **Mycorhize** | boost borné du `p` dans `plant_uptake` ∝ `mycelium` sous l'empreinte ; **miroir** `qi_local` | re-figé (uptake) |
| ④ | **Faune fongivore + carpophores** | fraction `auxiliaire` ∝ mycélium/carpophores ; sprites échantillonnés (perception) | population re-figée ; sprites neutres |
| ⑤ | **Structures niveau tuile** | `Structure` → tuile ; `composter`/`empiler` depuis tout plot de la tuile ; faune bac ; maturation lisible + colonisation fongique du tas | event-driven (~intact) |
| ⑥ | **`epandre` 2 clics + vue** *(Godot repris)* | protocole pont 2 cibles ; carpophores, tas colonisé, palette overlay `mycelium` | — |

Chaque sous-sprint est une **unité testable** qui préserve (ou re-fige de façon
**maîtrisée**) le golden. Boucle CLAUDE.md : `0N` → travailler → vérifier/re-figer
golden → `00_etat.md` → commit → `/clear` → `0N+1`. Kickoffs `0N_*.md` à écrire au
démarrage du sprint.

---

## 6. Coûts golden — re-figeage LARGE annoncé

Conforme au choix « wood-wide-web inclus ». Les chemins re-figés, dans l'ordre des
sous-sprints :

- **①** présence du champ dans le pipeline (effets débranchés) → dérive nulle ou
  localisée.
- **②** décompo du `bois` modulée par le mycélium → golden écolo.
- **③** uptake du `p` modulé par la mycorhize → golden écolo (le plus structurant).
- **④** terme fongivore dans la population `auxiliaire` → **golden de population**.
- **⑤** event-driven (gestes joueur hors tick) → golden ~intact.

Carpophores (④), UX 2 clics (⑥) et palette overlay = **golden-neutres**. Chaque
re-figeage est **maîtrisé, localisé et expliqué** au commit du sous-sprint.

---

## 7. Philosophie & garde-fous

- **Philo #1** (agir sur le milieu) : tous les gestes liés (composter, empiler,
  retourner, épandre) restent le **canal vertueux bon marché** ; bêcher reste
  coûteux **et** détruit le réseau fongique (`becher` retire un quantum de
  `mycelium`, event-driven §1.2 — double peine pédagogique), là où `grelinette`
  le préserve.
- **Philo #2** (émergence) : le mycélium modifie des **champs** (décompo, `p`
  disponible, `om_stable`, `auxiliaire`), jamais une plante en direct. La réponse
  (croissance, faune, succession) émerge au tick.
- **Philo #4** (le sol porte la mémoire) : le réseau fongique **fait grandir le
  sol** (liant `om_stable`, digestion du bois) — il s'installe lentement et
  s'effondre au travail du sol. Mémoire fragile, récompense de la non-perturbation.
- **Philo #6** (apprentissage diffus) : laisser le sol couvert, humide, non bêché
  → champignons, bois digéré, phosphore qui passe. Bêcher → réseau cassé. **La
  conséquence enseigne, sans sermon.**
- **Déterminisme** (philo #3) : champ scalaire à dynamique pure, échantillonnage
  de carpophores déterministe, fusion/ordre stables — **pas de `Random`**, golden
  reproductible.
- **Interconnexion** (`regle_interconnexion_acteurs.md`) : le mycélium relie
  explicitement **sol ↔ litière ↔ plantes vivantes ↔ faune ↔ structures**. C'est
  le tissu conjonctif demandé par la facet (f).

---

## Annexe — knobs de calibrage (placeholders, post-test)

- **Dynamique** : `K_G` (croissance), `K_D` (déclin), pondération `substrat`
  (poids bois / `om_active` / proximité pile), fenêtre `temperature_sol`,
  sensibilité à la sécheresse ; `BECHAGE_MYCELIUM_MALUS` (quantum retiré par
  `becher`, event-driven §1.2).
- **Saprophyte** : `α` (intensité du terme fongique sur la décompo `bois`).
- **Liant** : taux d'ajout à `om_stable` (lent).
- **Mycorhize** : `MYCO_P_BONUS` (plafond du boost `p`), forme de la réponse
  ∝ `mycelium` sous l'empreinte.
- **Faune** : fraction `auxiliaire` ∝ mycélium ; seuils de carpophores
  (densité × humidité × saison) pour l'échantillonnage des sprites.
- **Structures** : colonisation fongique du tas (vitesse), effet sur la vitesse de
  maturation (bac vs pile), seuils des phases frais/en cours/mûr.
- **Coûts Vigueur** : inchangés pour les gestes existants ; `epandre` 2 clics ne
  change pas le coût (même geste, UX différente).

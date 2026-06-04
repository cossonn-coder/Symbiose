# Journal Symbiose

Trace écrite vivante du développement. Une entrée par sprint, par décision
structurante, ou par incident notable. À jour à la fin de chaque session.

**Conventions** :
- Dates en `YYYY-MM-DD`.
- Une entrée commence par un titre `## YYYY-MM-DD — Titre court`.
- Les décisions sont préfixées `**Décision :**`, les questions ouvertes `**Question :**`.
- Dette et backlog ne sont plus dans ce fichier : voir `DETTE.md` et `BACKLOG.md`.

---

## Index

**Dette technique** → [`DETTE.md`](DETTE.md) · **Backlog des sprints** → [`BACKLOG.md`](BACKLOG.md)

### Entrées archivées (`journal_archive/`)

- [2026-05-29 — Sprint 0 : reprise et infrastructure documentaire](journal_archive/01_2026-05-29_sprint-0-reprise-et-infrastructure-documentai.md)
- [2026-05-29 — Sprint conception : redéfinition de la vision du jeu](journal_archive/02_2026-05-29_sprint-conception-redéfinition-de-la-vision-d.md)
- [2026-05-29 — Sprint conception bis : zones blanches refermées](journal_archive/03_2026-05-29_sprint-conception-bis-zones-blanches-refermée.md)
- [2026-05-29 — Zone Z7 : éclairement spatial pixel-exact](journal_archive/04_2026-05-29_zone-z7-éclairement-spatial-pixelexact.md)
- [2026-05-29 — Sprint conception éclairement & reproduction (recadrage Z7)](journal_archive/05_2026-05-29_sprint-conception-éclairement-reproduction-re.md)
- [2026-06-02 — Sprint sol vivant : le sol devient organisme (Python)](journal_archive/06_2026-06-02_sprint-sol-vivant-le-sol-devient-organisme-py.md)
- [2026-06-02 — Consolidation sol vivant : puits microbien (Python)](journal_archive/07_2026-06-02_consolidation-sol-vivant-puits-microbien-pyth.md)
- [2026-06-02 — Mini-sprint succession : gradient pionnier → prairie ∝ maturité du sol](journal_archive/08_2026-06-02_minisprint-succession-gradient-pionnier-prair.md)
- [2026-06-02 — Sprint éclairement : ombres-capsules astronomiques + pérennes (Python)](journal_archive/09_2026-06-02_sprint-éclairement-ombrescapsules-astronomiqu.md)
- [2026-06-02 — Conception mini-sprint mortalité réaliste (sénescence)](journal_archive/10_2026-06-02_conception-minisprint-mortalité-réaliste-séne.md)
- [2026-06-02 — Mortalité réaliste passe 1 : santé dynamique + sénescence (Python)](journal_archive/11_2026-06-02_mortalité-réaliste-passe-1-santé-dynamique-sé.md)
- [2026-06-02 — Mortalité réaliste passe 2 : fonte, fongique, ravageurs régulés, renouvellement (Python)](journal_archive/12_2026-06-02_mortalité-réaliste-passe-2-fonte-fongique-rav.md)

### Entrées récentes (ci-dessous)

- [2026-06-02 — Attire-auxiliaires + monde 9 tuiles (Python)](#2026-06-02-attire-auxiliaires-monde-9-tuiles-python)
- [2026-06-03 — Sprint génétique / reproduction : banques + héritage biparental (Python)](#2026-06-03-sprint-g-n-tique-reproduction-banques-h-ritage-biparental-python)
- [2026-06-03 — Sprint refactor structurel : paquets + golden + assainissement docs (Python)](#2026-06-03-sprint-refactor-structurel-paquets-golden-assainissement-docs-python)
- [2026-06-03 — Sprint conception météo / climat + signes diégétiques](#2026-06-03-sprint-conception-m-t-o-climat-signes-di-g-tiques)
- [2026-06-03 — Sprint implémentation météo : déterminisation → température → réponses médiées → forecast/signes (Python)](#2026-06-03-sprint-impl-mentation-m-t-o-d-terminisation-temp-rature-r-ponses-m-di-es-forecast-signes-python)
- [2026-06-04 — Sprint conception Vie macroscopique : D31 (conception seule)](#2026-06-04-sprint-conception-vie-macroscopique-d31-conception-seule)
- [2026-06-04 — Sprint impl. D31.3 : façades `vigueur_*` + gestes joueur (Python)](#2026-06-04-sprint-impl-d313-fa-ades-vigueur_-gestes-joueur-python)
- [2026-06-04 — Sprint impl. D31.1 : champs de population + perception (Python)](#2026-06-04-sprint-impl-d311-champs-de-population-perception-python)
- [2026-06-04 — Sprint impl. maîtrise D12·i1 : cœur + progression intra-objet (Python)](#2026-06-04-sprint-impl-ma-trise-d12-i1-c-ur-progression-intra-objet-python)

---

## 2026-06-02 — Attire-auxiliaires + monde 9 tuiles (Python)

### Contexte

Demande de Nico après la passe 2 : **ajouter des plantes qui attirent les
prédateurs des ravageurs**, et passer `main.py` sur **plusieurs tuiles**.
Décisions actées : **espèce(s) dédiée(s) + signal explicite** (rondelle
`auxiliaire`) ; **9 tuiles** (monde 3×3 complet).

### Réalisé

- **Rondelle `auxiliaire`** (`models.py`, `RONDELLE_TYPES`) — miroir discret de
  `pollinisateur`, posée par les plantes compagnes à la floraison.
- **2 espèces compagnes** : **Achillée millefeuille** (`Yarrow`, Asteraceae,
  vivace — ombelles) et **Phacélie** (`Phacelia`, Boraginaceae, annuelle —
  engrais vert mellifère). Toutes deux posent `auxiliaire` (Phacélie aussi
  `pollinisateur`). Ajoutées au `PLANT_CATALOGUE`.
- **Terme prédateur** (`effects.py`, `herbivory_pressure`) : intègre la rondelle
  `auxiliaire` avec un poids fort →
  `predator = 0.4·biodiversité + 0.2·pollinisateur + 0.15·stabilité + 0.4·auxiliaire`.
- **`main.py` réécrit en monde 3×3** (9 tuiles, sols contrastés terre/argile/
  sable). Tuiles paires = attire-auxiliaires (achillée+phacélie+trèfle), impaires
  = témoins. Rapport agrégé + table par tuile + **contraste attire-aux vs témoins**
  (rondelles `auxiliaire`, vitalité, vivantes). Défaut `N_YEARS=30` (9 tuiles
  lourdes ; CLI pour runs longs).

### Recalibration clé

Le test a révélé que `HERBIVORY_BASE=0.02` plafonnait la pression herbivore
**sous le seuil de morsure** (0.015) → l'herbivorie ne mordait jamais et la
régulation prédateurs (donc les attire-auxiliaires) était **inerte**. Relevé à
**0.05** : désormais une monoculture appauvrie sans auxiliaires **mord** (−1
santé), et diversité **ou** rondelles `auxiliaire` **ou** microbiome riche la
ramènent sous le seuil. La leçon permaculture (critère 4) devient réelle.

### Validation

- Contraste direct : monoculture+sol pauvre+0 aux → pression 0.018 (mord) ;
  +3 `auxiliaire` → régulée ; polyculture → régulée ; sol riche → régulée.
- `main.py` 9 tuiles : exit 0, rondelles `auxiliaire`=3 sur tuiles attire-aux,
  0 sur témoins (contraste net).
- Stabilité : mono-tuile 200 ans, aucune extinction, santé dynamique (1/2/3
  mêlées), vitalité 0.192 — la hausse d'`HERBIVORY_BASE` ne déstabilise pas.

### Note

Mécanique provisoire cohérente avec la **régulation émergente** (passe 2) : le
**champ auxiliaire ambiant dédié** (dynamique proie-prédateur + sprites visibles,
fiche Auxiliaires de `CLAUDE.md`) reste un sprint futur. Portage C# → D27/D24.

### Vérification du contraste (run 500 ans + test dédié)

Le run `main.py` 9 tuiles / 500 ans (69 min, exit 0, 20 plantes/tuile, vitalité
~0.21, mosaïque %vivace 23–87 %) **noie le contraste** attire-aux vs témoins :
à maturité, toutes les tuiles sont diverses + microbiome riche → la régulation
des ravageurs est déjà saturée par la diversité/le sol, les auxiliaires
deviennent redondants (écologiquement correct : un jardin établi s'auto-régule).

Pour **isoler** l'effet, `test_auxiliaires.py` (gardé) : 2 tuiles jumelles sous
**stress chronique** (sol sableux pauvre + monoculture tomate re-semée chaque
an). Instrumentation : wrap de `herbivory_pressure` comptant les dégâts par
tuile. Résultat sur 30 ans, déterministe : **AUX = 0 dégât herbivorie, TÉMOIN =
6** (écart monotone). Le mécanisme attire-prédateurs est donc fonctionnel de
bout en bout (rondelle posée → terme prédateur → dégâts ravageurs réduits) ;
l'amplitude reste modeste car `HERBIVORY_BASE` bas (ravageurs = nuisance, pas
fléau — philo non-punitive).

---

## 2026-06-03 — Sprint génétique / reproduction : banques + héritage biparental (Python)

**Objectif** : lever D17 (deux banques de graines) + D22 (génétique des
populations) et **remplacer** le renouvellement provisoire M7 (`_renewal`) par
la vraie reproduction génétique. Python seul (source de vérité) ; le portage C#
rejoint la dette D24 — le C# n'a aujourd'hui que des stubs Godot de 15 lignes,
aucun moteur à porter, donc la « parité 1 saison » du kickoff était intestable
(décision actée en début de session).

**Zones blanches tranchées (2026-06-03)** :
- Granularité banque-sol = **moyenne + variance par espèce × plot** (pas
  d'échantillons stockés) → `GeneStat` (Welford pondéré).
- Compatibilité d'hybridation = **par famille botanique** (`species_compatible`).
- Coût Vigueur de la récolte sélective = **différé** (hook `HARVEST_VIGUEUR_COST
  = 0`, branché au Sprint 4 Vigueur / D11).

**Vecteur de gènes (D22)** — `models.GENE_NAMES = ("hauteur",)`, extensible sans
refactor. Plage normale [0.7, 1.3] (gaussienne σ=0.10), bornes dures [0.4, 1.6]
que l'introgression peut atteindre (vigueur hybride). `PlantInstance.genes` (vide
⇒ neutre 1.0) + `gene()`. `genetic_factor` enfin **branché** :
`current_height = potentiel × growth_factor × gene("hauteur")` (annuelles ET
pérennes ligneuses).

**Deux banques (D17)** :
- **Banque-sol** = couche `species` ajoutée **par-dessus** les archétypes dans
  `fields.SeedBank` (`add_species`, `sample_genes`, `tick_species_aging`). Par
  espèce × plot : densité + distribution `GeneStat` par gène. Vieillit (0.997/sem),
  les dépôts récents pèsent plus → la lignée locale dérive. Reste au terrain.
- **Banque-joueur** = `seeds.py` (`Seed`, `PlayerSeedBank`) : lots par espèce,
  transportable (suit l'avatar), **sérialisation JSON** (save lisible).

**Reproduction biparentale (D22)** — `reproduction.py`, déterministe (hash, pas
de RNG live) :
- `find_father` : père de même famille, en âge de fleurir, à portée de
  pollinisation. `pollination_mode` (wind/insect/self) + `pollination_radius_cm`
  par espèce (graminées + chêne/noyer = anémophiles longue portée).
- En mode insecte, le rayon est modulé par les rondelles `pollinisateur` +
  `auxiliaire` de la tuile (×0.5 sans → ×1.5 à saturation) : **favoriser les
  auxiliaires = plus de brassage = meilleures graines** (mécanique permaculture).
  Sans partenaire à portée → **autofécondation** (mutation réduite, consanguinité).
- `child_genes` : moyenne(parents) + mutation gaussienne par gène. Introgression
  intra-famille = père hétérospécifique décale les gènes, l'enfant **garde
  l'espèce de la mère** (aucune nouvelle `PlantData`).

**Intégration moteur** — `_renewal` (M7) **supprimé**, remplacé par
`_reproduction` (même phase : récolte d'automne). Chaque parent fécond qui
fructifie dépose ses graines (gènes hérités) dans la banque-sol [pont chute→sol],
puis recrute directement **uniquement** ce que la succession par archétype ne
germe pas (vivaces/arbres sans archétype — ex-domaine de M7), gated par la
lumière. Les germinations de `_succession`/`_spring_flush` échantillonnent les
gènes du pool du plot (vide ⇒ neutre, rétro-compatible). Pont récolte→banque-
joueur dans la phase récolte (inerte si aucune banque-joueur attachée au
`game_state`, donc `main.py` inchangé).

**Tests** (`test_genetique.py`, gardé) — **20/20** déterministe :
genetic_factor branché ; **sélection émergente** (lignée sélectionnée 1.00→1.33
sur 14 générations vs dérive neutre ~1.00) ; **brassage** (auxiliaires → rayon
75→225 cm → outcrossing au lieu d'autoféc.) ; introgression intra-famille,
inter-familles interdite ; banque-sol dépôt/échantillonnage ; intégration moteur
4 ans + pont récolte. Non-régression : `main.py 30` stable, sans crash ;
circulation des gènes féraux confirmée (été an 25, 6/33 vivantes portent des
gènes hérités, dérive autour de 1.0).

**Reste** : portage C# (→ D24, avec tout le moteur) ; nouveaux gènes du vecteur
(vigueur, résistance pathogène, tolérance sécheresse) = extensions futures ;
coût Vigueur récolte = Sprint 4 (D11).

---

## 2026-06-03 — Sprint refactor structurel : paquets + golden + assainissement docs (Python)

### Contexte

Après sol vivant / succession / éclairement / sénescence / génétique, les
fichiers de `data/code/` avaient enflé et mélangeaient les responsabilités
(`models.py` 1307 l., `fields.py` 1058, `engine.py` 815, `effects.py` 570).
`journal.md` (1438 l.) dupliquait la dette + le backlog présents aussi dans
`CLAUDE.md`. Sprint **structurel** : zéro changement de comportement, le succès
se mesure à l'**identité de sortie** (déterminisme = règle de design #3).

### Zones blanches tranchées (début de session)

- **Constantes** : `constants.py` partagé pour l'échelle (`PLOT_CM`),
  `plants/genetics.py` pour les gènes (séparation propre des deux familles).
- **Archive journal** : un fichier par entrée de sprint dans `journal_archive/`,
  `journal.md` pointe vers eux.
- **Golden** : scénario 3 tuiles / 100 ans (couvre multi-sol + succession +
  reproduction + sénescence du pommier + hiver).

### Réalisé

- **Filet golden** (`tests/test_golden.py`) : rejoue un scénario déterministe,
  hashe (sha256) le **log complet semaine par semaine** + un **digest d'état
  final** (chaque plante + champs éco). Hash de référence figé dans
  `tests/golden_hash.txt` **avant** tout déplacement :
  `fbb0c16b…129ca7`.
- **Arborescence en paquets** (couches basses jamais importatrices des hautes,
  `plants ← fields ← sim`) :
  - `constants.py` (`PLOT_CM`)
  - `plants/` : `genetics.py` (gènes, `clamp_gene`, `species_compatible`),
    `base.py` (`GrowthStage`/`PlantInstance`/`ConflictNotification`/`PlantBase`
    + 5 familles + empreintes + registre d'effets), `species.py`,
    `perennials.py`, `catalogue.py` (3 catalogues)
  - `world/` : `tile.py` (`Tile`, `StakeSlot`, `RONDELLE_TYPES`)
  - `fields/` : `noise.py` (fondation : `_hash_noise`/`hash_gauss`/
    `climate_stress`), `grids.py`, `light.py`, `seedbank.py`, `ecofields.py`
  - `sim/` : `effects.py`, `seeds.py`, `reproduction.py`,
    **`succession.py` (extrait d'`engine`** : `choisir_archetype`,
    `succession`, `spring_flush` — méthodes Engine → fonctions, comportement
    identique), `engine.py` allégé
  - `tests/` : `test_golden.py`, `test_genetique.py`, `test_auxiliaires.py`
- **Point de vigilance levé** : l'import paresseux `from models import
  clamp_gene` dans `SeedBank.sample_genes` est remplacé par un import direct
  `from plants.genetics import clamp_gene` (pas de cycle : `plants` n'importe
  jamais `fields`).
- **Migration par shims** : Phase A (anciens fichiers plats → ré-export depuis
  les paquets) → golden **identique**. Phase B (sites d'appel repointés, shims
  supprimés) → golden **identique** à nouveau. Lancement : `python3 main.py`,
  `python3 -m tests.test_golden` depuis `data/code/`.
- **Docs** : `DETTE.md` + `BACKLOG.md` (source unique) extraits ; `journal.md`
  archivé (12 entrées → `journal_archive/`, 2-3 récentes gardées) ;
  duplication dette/backlog supprimée de `CLAUDE.md`.

### Validation (déterministe)

- **golden identique avant/après** : `fbb0c16b…129ca7` (Phase A et Phase B).
- `python3 -m tests.test_genetique` → 20/20 ; `python3 -m tests.test_auxiliaires`
  → contraste AUX < témoin préservé ; `python3 main.py` → exit 0, scores
  inchangés.

### Reste

Portage C# non concerné (dette D24). Dette consolidée en **D28** (refactor fait).

---

## 2026-06-03 — Sprint conception météo / climat + signes diégétiques

**Conception seule, aucun code.** Livrable = spec dédiée à étudier :
[`data/code/CONCEPTION_METEO.md`](data/code/CONCEPTION_METEO.md). Couvre **D16**
(forecast) et **Z2** (signes diégétiques). Climat de référence : Normandie
~49°N, océanique tempéré.

### Le pivot

**Décision :** remplacer le tirage météo `random.choice(ALEAS_METEO)`
(`sim/engine.py`) — un **RNG live qui viole la philo #3**, ne tenant que par la
béquille `random.seed(42)` — par une **fonction pure `weather_at(seed, week)`**
à base de `_hash_noise`. Tout le reste du moteur a déjà migré vers le hash
déterministe ; la météo était le dernier îlot non conforme. Une fonction pure du
temps est *évaluable en avance sans avancer la simulation* → débloque
gratuitement le forecast, les signes et la prévisibilité au transcendant.

**Principe-colonne :** la météo est intégralement déterministe. La maîtrise ne
change pas *ce qui arrive*, seulement *combien le joueur sait le lire*.
L'imprévisibilité ressentie est **informationnelle (UX)**, jamais simulatoire.

### Décisions actées

- **Modèle climatique** à 3 échelles : normales saisonnières lisses (sinusoïdes
  température/pluie), dérive interannuelle (réutilise `climate_stress`), et
  événements hebdo tirés par hash (canaux-sentinelles `K_OCC/K_PICK/K_MAG`).
  Catalogue : gel/gelée tardive, canicule, sécheresse (état multi-sem.), tempête,
  grêle (localisée), pluie prolongée (état), redoux. Distinction
  **événement ponctuel** vs **état climatique** (déduit sur fenêtre, sans état
  stocké).
- **Couplage par le milieu uniquement** (philo #1/#2) : chaque événement = des
  deltas de champ + durée, la réponse biologique émerge (`drought_memory`,
  `disease_probability`, gates de croissance, nécromasse).
- **Décision :** ajouter un **champ `temperature` ambiant** (`GridField`, comme
  `lumiere`/`disturbance`) + gate `ok_temp` dans `_avancer_stades` (Option B,
  recommandée). Option A « température implicite » écartée (gel/redoux
  acrobatiques). **Coût assumé : re-figer le golden** au sprint d'implémentation.
- **Décision :** gel/grêle/verse ne sont plus des malus directs (`ReduceHealth`)
  mais `sévérité × (1 − gène_rusticité) × (1 − protection_locale)` → flux ×
  génotype × milieu. Implique un **gène de rusticité au froid** (vecteur
  génétique extensible).
- **Forecast (D16) reformulé/simplifié** : `forecast = [weather_at(seed, week+k)]`,
  cohérent par construction, reproductible. Plus de « tirage décalé à stocker ».
- **Signes (Z2)** : table signe→événement ; le signal est toujours parfait,
  c'est l'**interprétation** qui dépend de la maîtrise. **~20 % sans signe**
  via masque déterministe `_hash_noise(...) > 0.20`, levé au transcendant.
- **Palier météo** (5 niveaux) : découverte (signes non nommés) → investissement
  (co-occurrences) → **maîtrise** (carnet/encyclo interprétatifs, seuil clé) →
  expertise (horizon 2 sem. + intensité/localité) → transcendant (les 20 %
  deviennent lisibles).
- **Vigueur** : préparation (temps figé, modérée — paillage, voiles, brise-vent,
  ombrière, buttes, réserve d'eau) vs réaction (temps réel, élevée — arrosage
  ciblé, sauvetage, tuteurage, récolte d'urgence). Anticiper coûte peu, réagir
  coûte cher (philo #1).

### Reste (sprint d'implémentation ultérieur, découpé en sous-sprints)

`weather_at`/`forecast`/`WeatherEvent` + masque de signe ; champ `temperature` +
`ok_temp` ; gène de rusticité ; réécriture `appliquer_alea` ; retrait de
`random.seed(42)`. **Doit préserver / re-figer `tests/test_golden.py`.**

---

## 2026-06-03 — Sprint implémentation météo : déterminisation → température → réponses médiées → forecast/signes (Python)

### Contexte

Implémentation de la conception météo figée (`data/code/CONCEPTION_METEO.md`),
couvrant **D16** (forecast) + **Z2** (signes). Sprint **gros** découpé en
**4 sous-sprints autosuffisants** (`sprints/sprint_meteo_impl/`), chacun une unité
testable préservant ou re-figeant le golden une seule fois.

### Réalisé (par sous-sprint)

1. **Déterminisation** — `sim/weather.py` créé : `weather_at(seed, week)` PURE
   (catalogue + saisonnalité §1.3) + `WeatherEvent(kind, intensity,
   duration_weeks, scope)` + `forecast`. **Retrait de `random.seed(42)`** : les
   3 derniers `random.random()` live de `sim/effects.py` (add_rondelle,
   reduce_health, PropagateDisease) migrés vers `_hash_noise` (canaux 19/23/29).
   Golden re-figé `fbb0c16b…→a2fefba2…`.
2. **Température** — champ ambiant `EcoFields.temperature` (normales saisonnières
   `temp_norm` + deltas météo `temperature_delta`), gate `ok_temp` dans la
   croissance (stagnation hivernale), couplage évaporation↔température. **Cadence
   météo passée en HEBDOMADAIRE** (décision Nico), `P_EVENT 0.60→0.15`. Golden
   re-figé `a2fefba2…→4bcae3a3…`.
3. **Réponses médiées par gène** — gène `rusticite_froid` ajouté au vecteur
   génétique (héritage décorrélé, golden-neutre tant que le dégât ne change pas) ;
   gel et grêle quittent la voie `health` plate pour un dégât **médié**
   (`sévérité_milieu × susceptibilité_gène × (1 − protection_paillage)`, helper
   `Engine._mediated_damage`). **Gel piloté par le MILIEU** (`temp < 0`), pas par
   le nom de l'événement — forme la plus pure flux→contrainte→réponse. Golden
   re-figé `4bcae3a3…→63bfdac4…`.
4. **Forecast + signes (read-only)** — `weather_signs(seed, week, horizon=2)` PURE
   + `WeatherSign(kind, in_weeks, signs, signed)` + table `SIGN_TABLE` (§4.1) +
   masque `is_signed` (canal `K_SIGN`, §4.3, ~80 % signés). Test dédié
   `tests/test_signes.py` (8/8). **Golden INCHANGÉ `63bfdac4…`** (PASS sans
   `--capture`) → preuve qu'aucun couplage n'a fui dans la simulation.

### Décisions

- **Path A (déterminisation totale)** : les `random.random()` live cachés derrière
  `random.seed(42)` étaient incompatibles avec « déterminisme sans seed global » →
  tous migrés vers `_hash_noise`. Le golden devient vraiment reproductible.
- **Cadence météo hebdomadaire** : `weather_at` consulté chaque semaine (plus
  seulement au passage de saison) → le **forecast est pleinement honnête** (ce
  qui est prévu *est* ce qui tombe, prouvé sur 1040 semaines × horizon 2).
- **Température = champ ambiant (Option B)** : gel/canicule/redoux deviennent des
  **deltas de température** transitoires, plus des malus directs.
- **Retour `weather_signs` = structure complète + flag `signed`** (décision Nico) :
  l'appelant (palier/UI, D12) filtre selon la maîtrise — « marche transcendant
  gratuite » sans re-toucher `weather.py`. L'événement ne change jamais ; seule la
  visibilité du signe dépend du palier (philo #3 intacte).

### Hors périmètre (gated, non fait)

- **Vigueur** préparation/réaction (voiles d'hivernage, tuteurs, brise-vent) —
  gated **D11**. La **verse (tempête)** est « prête côté gène `hauteur` » mais
  attend le système de tuteur.
- **Paliers de maîtrise météo** + bascule interprétative du carnet + révélation
  transcendant côté UI — gated **D12**.
- **Rendu des signes** (sprites oiseaux/ciel/anneau) — côté Godot, plus tard.
- **Portage C#** — dette **D24**.

### Observation à creuser (post-test, pas un bug)

Sur 40 ans, le jardin se fait dominer par les **pionnières de la succession
spontanée** (sans vecteur génétique) → la **sélection visible du froid** reste
discrète tant que les populations vivantes sont quasi-neutres. La médiation mord
bien (survie/score baissent) mais l'émergence génétique demande un recalibrage
(intensités de gel, balance pionnières/cultivées) — sprint ultérieur.

### Hash golden (journal de re-figeage)

`fbb0c16b…` → `a2fefba2…` (01) → `4bcae3a3…` (02) → `63bfdac4…` (03) →
`63bfdac4…` **inchangé** (04, read-only).

---

## 2026-06-03 — Sprint gènes du vecteur : vigueur + résistance pathogène + tolérance sécheresse (Python)

Extension du vecteur de gènes héréditaire (D22) de **2 → 5 gènes**, chacun branché
sur une mécanique existante selon le patron `rusticite_froid` (susceptibilité =
`1/gène`, aucun bonus/malus direct — philo #2/#7). Découpage acté avec Nico : les
**coûts en Vigueur joueur** (couche transversale D11) restent une conception
séparée à venir — ce sprint ne touche que les traits héréditaires des plantes.

**Décision (3 questions) :** (1) **découper** — gènes maintenant, Vigueur joueur
ensuite ; (2) définir **`vigueur`** tout de suite comme multiplicateur de fitness
**PROVISOIRE** (à recâbler sur la Vigueur D11) ; (3) ajouter une **vraie voie
sécheresse → santé** (pas seulement la stagnation de croissance).

### Ce qui est fait
- `plants/genetics.py` : `GENE_NAMES` = (`hauteur`, `rusticite_froid`, **`vigueur`**,
  **`resistance_pathogene`**, **`tolerance_secheresse`**). Héritage biparental et
  banque-sol suivent **automatiquement** (canaux de hash décorrélés par index → les
  deux gènes existants restent bit-pour-bit identiques en isolation).
- **`vigueur`** (fitness générale) — `engine` : accélère l'avancement de stade
  (`needed = duration_weeks / gène`) et la convalescence (`heal × gène`).
- **`resistance_pathogene`** — `effects` : `susc /= gène` dans `fungal_disease` ET
  la fonte des semis (`damping_off`) → sélection émergente des lignées résistantes.
- **`tolerance_secheresse`** — abaisse le seuil d'humidité de stagnation
  (`ok_hum = 0.15 / gène`, `engine`) ET **nouvelle** voie `drought_stress_damage`
  (`effects`, canal week·37) : une sécheresse sévère **prolongée**
  (`drought_memory > 0.6`) abîme le tissu, médiée par le gène. Vraie pression de
  sélection sans nouveau champ.

### Vérifs
- **Golden re-figé** `63bfdac4…` → `ee79dd66…` (comportement intentionnellement
  modifié — ce n'est pas un refactor ; re-vérif PASS sur le nouveau hash).
- **Stabilité 200 ans × 3 sols** : effectifs ~2–16 plantes/tuile, **aucun
  effondrement ni emballement** ; dérives génétiques douces et bidirectionnelles
  (0.93–1.06) → la couche mord sans runaway.
- `test_genetique` **20/20**, `test_auxiliaires` OK.

### Hors périmètre (gated)
- **Vigueur joueur + coûts d'action** (manger, récolte, déracinage) — **D11**,
  conception séparée. `HARVEST_VIGUEUR_COST` reste 0 ; le gène `vigueur` y sera
  recâblé.
- **Calibrage fin de la pression de sélection** (intensités, balance pionnières /
  cultivées) — même observation qu'au sprint météo 03, sprint ultérieur.
- **Portage C#** — **D24**.

### Hash golden (journal de re-figeage)
`63bfdac4…` (météo 04) → `ee79dd66…` (gènes du vecteur).

---

## 2026-06-04 — Sprint conception Vigueur : couche transversale D11 (conception seule)

Conception de la **Vigueur universelle** (D11), aucun code. Produit la spec
`data/code/CONCEPTION_VIGUEUR.md`, sur le modèle de `CONCEPTION_METEO.md`.

**Le pivot :** la Vigueur n'est pas *un* système mais **deux strates**. Le moteur
modélise déjà la quasi-totalité de la « Vigueur des plantes » sous d'autres noms
(uptake = puiser, nécromasse = retour au sol, santé/`vitalite`/gène = énergie
propre, `game_state["current_player"]`/`scores` = logement joueur,
`HARVEST_VIGUEUR_COST` = hook coût déjà câblé). Le seul *vrai nouveau* système est
la **couche Vigueur joueur + coûts d'action**, event-driven, **au-dessus** du tick.

**Décisions (2 questions) :** (1) **Vigueur des plantes = façade dérivée**
(`vigueur_plante = sante × maturite × qi_local × gène`), read-only, zéro état
nouveau, **golden intact** — vs champ stocké rejeté ; (2) **interface paliers
stubbée** : Vigueur conçue de façon autonome, `palier_bonus()` renvoie `1.0` tant
que D12 absent, se branche plus tard sans retoucher la Vigueur.

**Propriété clé actée :** le golden écologique est une succession spontanée pure
(aucune action joueur) → activer les coûts, la régen joueur, la façade
**ne re-fige PAS le golden**. Si un hash bouge à l'implémentation, c'est un bug
(fuite dans le tick). Un *golden joueur* distinct testera la couche gameplay.

Le gène `vigueur` provisoire (D22b) est **enveloppé** par la façade, pas recâblé
de façon destructrice → son sens passe de « provisoire » à « stabilisé ».

**Catalogue d'actions joueur** (§3 du doc) : trois axes (cible milieu/vivant ·
phase planif./saison · signe Vigueur ±). Milieu (canal vertueux philo #2 : semer,
**multiplier végétativement** (clone), arroser, **drainer**, pailler, amender,
**inoculer**, **favoriser un auxiliaire**, **grelinette/biner**, structures/tuteur)
→ modifie un **champ**, jamais la plante. Vivant (coûteux philo #1 : manger,
récolter, déraciner, écraser, **tailler**) → net positif sur le mûr, net négatif
sec sur déraciner/écraser, pas de punition scriptée (philo #6). Ressourcement :
méditer (source), **observer (gratuit)**.

Deux trous comblés (suggestion Nico) : **favoriser un auxiliaire** = pendant
vertueux d'« écraser » (agir sur l'habitat → régulation émergente, pas de
suppression manuelle) ; couple **biner/grelinette** = pédagogie par l'outil (même
but décompacter, le bêchage casse le `microbiome`, la grelinette le préserve —
no-dig). `Pailler` élargi en **`Pailler / mulcher`** (paille/BRF/feuilles/broyat).
Ouvre une question de modélisation inscrite en dette **D30** : champ
`structure/compaction du sol` pour porter le bénéfice d'aération de la grelinette.

**Dette surfacée : D29 (auxine / dominance apicale).** `tailler` est acquis en v1
(effet géométrique : réduction d'empreinte → lumière), mais sa vraie richesse
hormonale (levée de dominance apicale → débourrement latéral → ramification/mise à
fruit) **mérite un sprint dédié** (décision Nico). Hook posé, D29 s'y branchera.

**Périmètre impl. à venir** (sprint moyen, découpable, golden préservé sans
re-figeage) : couche Vigueur joueur → coûts d'action → façade lecture diégétique →
(tandem D19) action manger. Gated : paliers réels (D12), magazine (D13), prépa
météo (Godot), auxine/taille riche (D29), portage C# (D24).

### Hash golden (journal de re-figeage)
`ee79dd66…` (gènes du vecteur) → **inchangé** (conception seule, aucun code).

---

## 2026-06-04 — Sprint conception paliers de maîtrise : D12 (conception seule)

**Conception seule, aucun code.** Spec → `data/code/CONCEPTION_MAITRISE.md`.
Couvre **D12** ; remplit l'interface stubbée par le Sprint Vigueur
(`sim/vigueur.py:palier_bonus() == 1.0`). **Périmètre : squelette réutilisable
seulement** (décision Nico) — le câblage fin est déclaré en sous-sprints.

**Pivot structurant (décision Nico).** L'unité atomique de maîtrise n'est **ni la
famille ni l'espèce** mais l'**objet de maîtrise** générique, data-driven,
catalogue-agnostique — coller la maîtrise aux 5 familles condamnerait le modèle au
premier ajout (catalogue qui grossit, D23/D26). Catégories ouvertes : êtres
vivants (espèces), concepts transversaux, **outils, structures, techniques/gestes**
— vision Nico d'un « énorme ensemble d'objets interfaçables, système vivant aux
milliers de secrets ». Chaque objet porte un palier `0..5`
(`inconnu → découverte → investissement → maîtrise → expertise → transcendant`).

**Progression intra-objet.** Découverte (`0→1`) = **observation seule** (gratuite,
motive). Paliers sup. = **succès conditionnés**, de plus en plus pointus et
**répétés** aux hauts paliers (fiabilité/régularité valorisées). Difficulté
**log/exponentielle** (`preuves(k) ≈ BASE·R^(k-1)`) : qui sait déjà passe le début
vite puis ralentit. **Réversibilité monotone** (un palier ne se perd pas ; philo #6
+ le savoir voyage à l'avatar).

**Agrégats.** Famille = spillover **intra-famille uniquement** (tomate accélère
aubergine, pas haricot). **Deux mesures globales distinctes** (désamorce la
dilution par catalogue grossissant) : *complétude-ratio* sur les **découverts**
(→ seuils de déblocage) ≠ *accumulation-log absolue* (→ Vigueur max + régen,
« jardinier actif = vigoureux mais pas super-héros »).

**Trois effets, deux seams (décision Nico).** `palier_bonus(player)` reste
**scalaire intact** = `1 + K·log1p(accumulation)` → plafond Vigueur (log) + régen ;
**`sim/vigueur.py` non retouché** (découplage acté tient). Le **coût d'action** est
un **seam SÉPARÉ** sur `actions.py`, **contextuel** : `cout_action(player, action,
objets_touchés)` lit (1) connaissance globale éco/bio + (2) maîtrise des **objets
que l'action touche**. **Maîtrise stockée PAR OBJET, action = lecteur** (pas d'état
par paire action×objet → pas d'explosion combinatoire). Exemple : tailler
framboisier lit maîtrise(framboisier)+maîtrise(sécateur)+global → indépendant de
construire(serre) ; pratiquer la taille fait monter *l'objet framboisier* →
spillover gratuit sur tous ses gestes. Deux **sources ponctuelles** de Vigueur en
plus : découverte (+ motivation), succès/palier (+ récompense).

**Méta-état** dans `game_state["maitrise"][player]`, **par avatar** (pas de
méta-savoir inter-avatars), au-dessus du tick. Golden écolo (sans joueur) **intact,
jamais re-figé** — un hash qui bouge serait un bug.

**Sous-sprints déclarés (hors squelette) :** (1) définition du « succès » par
axe ; (2) table palier→déblocage (D13/D14/D15 + encyclopédie) ; (3) taxonomie des
objets + liste des objets-touchés par action ; (4) calibrage (`K/BASE/R`,
atténuations) ; (5) portage C# (D24).

**Question ouverte (calibrage, post-test) :** valeurs `K`, `BASE`, `R`,
atténuations de coût et gains ponctuels — comme toute la couche Vigueur.

### Hash golden (journal de re-figeage)
`ee79dd66…` → **inchangé** (conception seule, aucun code).

---

## 2026-06-04 — Sprint D12.1 : succès par axe (conception seule)

Premier sous-sprint de D12. Précédé de la **lecture moteur** actée comme point de
vigilance : inventaire des signaux discrets que le tick émet déjà (stade,
`advance_stage`, santé, mort par cause, reproduction + tag `biparental`, météo +
`_mediated_damage` vide=zéro perte, stagnation `⏸/🌑/❄`, succession férale, champs
`eco.summary()`, actions joueur). Constat : tous les signaux existent pour les
**êtres vivants** et **concepts** ; **outils/structures/techniques absents du
moteur** → fixés comme **patron** (câblage → D12.3). Aboutit à
`CONCEPTION_MAITRISE.md` **§9**.

**Pivot acté (Nico).** Un succès = **une action joueur dont l'effet émergent
améliore le résultat au-delà du cours spontané, observée**. Ni un événement
émergent (*tomate qui pousse seule = bonnes conditions, pas maîtrise*), ni une
action simplement payée. Opérationnalisé sans contrefactuel : *stress présent
levé* ou *stress prévenu chez les protégés*. La couche maîtrise **lit** ces
signaux, n'écrit rien dans le tick → golden intact.

**Nature de preuve croissante par palier (Nico, Q2).** Espèce : observer → lever
une stagnation → reproduction → optimisation répétée saine → **palier 5**.

**Palier 5 = conjonction (Nico).** Transcendance très dure : **(a)** action
experte/extraordinaire réussie (le ~20 % météo imprévisible, un sauvetage) **ET**
**(b)** naturalisation — génération **férale** non replantée qui boucle son cycle
en pleine santé dans le sol façonné, « accueillie comme native ». Réconcilie les
deux principes CLAUDE.md : l'action est la **preuve**, l'auto-suffisance l'**état**.

**État gameplay minimal induit** (au-dessus du tick, par avatar) : tag de
provenance *féral*/*replanté* (pour 5b) + fenêtre d'imputation geste→amélioration ;
gate d'observation (succès registré quand observé). Aucun état tick nouveau.

**Reste ouvert (différé) :** les **Nᵢ** (répétitions/palier, courbe log §2.3) →
calibrage D12.4 ; le **câblage par objet** (objets touchés par action) → D12.3.

### Hash golden (journal de re-figeage)
`ee79dd66…` → **inchangé** (conception seule, aucun code moteur).

---

## 2026-06-04 — Sprint D12.3 : taxonomie des objets de maîtrise (conception seule)

Troisième sous-sprint de D12 (D12.2 reste bloqué, attend D13/D14/D15). Précédé de
la **lecture des catalogues moteur** (point de vigilance acté) : `plants/`
(17 espèces / 11 familles), `sim/actions.py` (4 gestes codés) + le catalogue
d'actions *conçu* de `CONCEPTION_VIGUEUR.md` §3.2/§3.3. La taxonomie **reflète**
ces catalogues, n'en invente aucun. Aboutit à `CONCEPTION_MAITRISE.md` **§10**.

**Découpage : passage unique** (pas de `00_etat.md`+`0N`). Motif acté : conception
= un seul fichier (pas de fichiers de code couplés), contexte déjà chargé,
livrables couplés (table ↔ taxonomie), sur-découpage déconseillé (CLAUDE.md).

**Taxonomie (§10.1–10.3).** Êtres vivants = les 17 espèces réparties sur 11
familles ; le **spillover §3.1 est data-driven sur la famille réelle** → actif
aujourd'hui pour Solanaceae, Fabaceae, Asteraceae, **Rosaceae** (≥2 espèces), pas
pour les 7 singletons. Les 5 familles « cœur » de `base.py` **ne sont pas
privilégiées** (Rosaceae spille comme Solanaceae) — honore le pivot §0. Concepts =
les 6 de §9.3 → **terme global** de `cout_action`. Outils/structures/techniques =
inventaire dérivé des actions, **déclarés non câblés** (D29/D30/D31).

**Livrable central (§10.4) : table objets-touchés par action.** Précise le modèle
§4.2 — terme 1 = global (concepts + vivants), terme 2 = `{technique, espèce cible
(→famille), outil, structure}` que CE geste manipule.

**Décision :** maîtrise.md §10.4, le succès figé en D12.1 reçoit son support data.
- **Outil ≠ technique** comme deux objets distincts (sécateur vs taille). Honore
  les catégories §1 et **raffine** l'exemple §4.2 (dont l'espèce « framboisier »
  était illustrative, hors catalogue).
- **Concepts hors terme 2** : ils ne nourrissent que le terme global (connaissance
  holistique) — fidèle au texte littéral de §4.2.
- **Milieu sans cible vivante** (philo #2) ; **vivant** ajoute l'espèce →
  spillover famille gratuit. `observer`/`méditer`/`manger` (coût NUL) → terme 2 vide.

**Reste ouvert (différé) :** câblage des objets *en cursive* (outil/structure/
technique + nuisible) → D29/D30/D31 + sprints d'action ; Nᵢ + atténuations → D12.4.

### Hash golden (journal de re-figeage)
`ee79dd66…` → **inchangé** (conception seule, aucun code moteur).

---

## 2026-06-04 — Sprint conception Vie macroscopique : D31 (conception seule)

Conception de la **vie macroscopique observable** (auxiliaires, ravageurs,
pollinisateurs, vers de terre). Le moteur ne tenait jusqu'ici que des **flux
abstraits** (`herbivory_pressure` scalaire, terme `predator` reconstruit de
proxies, `ALEAS_RAVAGEURS` événementiels) — aucune entité à vitalité propre.
Modèle technique **hybride** déjà tranché le 2026-06-04 après profilage (D32).
Aboutit à `data/code/CONCEPTION_VIE_MACRO.md`.

**Découpage : passage unique** (conception, un seul fichier, contexte chargé).

**Décision structurante (golden) :** la dynamique vit **DANS le tick écologique**
(les champs nourrissent herbivorie/prédation/`pollinator_reach`/aération et
remplacent la reconstruction `predator`) → **re-figeage golden assumé**, unique,
journalisé (comme météo). Motif : la boucle d'apprentissage *vois → agis →
observe* ne se referme que si **le champ qui dessine est le champ qui agit** ;
un découplage « décoratif » créerait une dérive visuel↔santé. Contraste assumé
avec la Vigueur (qui, elle, ne re-figeait jamais).

**Pivot (réponse de Nico sur les champs) :** pas 4 dynamiques au cas par cas mais
**un `PopulationField` générique** (ressource trophique / prédateurs / habitat)
instancié **4 fois** — chaque guilde attirée par la ressource dont elle se nourrit
(ravageur ← feuillage ; auxiliaire ← ravageur + nectar ; pollinisateur ← fleurs ;
vers_de_terre ← microbiome/OM, part fongique incluse). Même esprit data-driven que
l'objet de maîtrise générique (D12.3). L'**inertie** crée le **décalage
proie-prédateur** → boom-bust visible (la pédagogie).

**Perception (§3) :** sprites échantillonnés, **1 sprite = 1 quantum** de densité,
position `_hash_noise(seed,r,c,slot)` **indépendante de la semaine** (pas de
téléportation), **activité** = vitesse d'anim (pur rendu), **cap + marge** (coût
borné — le seul point hors budget au profilage). **Golden-neutre** (lecture pure).

**Façades `vigueur_*` (§4) :** patron `CONCEPTION_VIGUEUR.md` §1 mais `qi_local`
**trophique** (= la ressource du champ) ; **populations, pas individus** (les
sprites ne portent pas de Vigueur).

**Gestes (§5) :** « favoriser un auxiliaire » (↑ plancher habitat), « écraser »
devient **réel** (retire **un quantum**, la pression revient), « fourche-bêche →
**vers morts visibles** » (feedback viscéral *avant* la dette microbiome — visuel
avant santé ; grelinette = pas de vers morts). Granularité **individu** (Nico).

**Découpe impl. proposée :** D31.1 champs+perception (golden intact) → D31.2
câblage écolo (**re-fige**) → D31.3 façades+gestes (golden intact).

**Décisions annexes :**
- Le **gain signé de « manger un individu »** (limace `−`, etc.) → **renvoyé en
  dette côté D19** (« option rigolote, pas prioritaire », Nico) ; D31 fournit le
  **prérequis** (entité ciblable / sprite cliquable). `DETTE.md` D19+D31 mis à jour.
- Recoupe **D27** (« champ auxiliaire dédié » = ce sprint), **D30** (vers =
  support possible de l'aération), **D32** (champ gratuit vs agents ∝ population).

### Hash golden (journal de re-figeage)
`ee79dd66…` → **inchangé** (conception seule). Le re-figeage interviendra à
**l'implémentation D31.2** (câblage écologique), pas avant.

---

## 2026-06-04 — Sprint impl. D31.1 : champs de population + perception (Python)

**Périmètre** (strictement le visuel, aucun câblage à la santé) : implémenter le
mécanisme `PopulationField` générique conçu en `CONCEPTION_VIE_MACRO.md`, ses 4
instances, et la règle d'échantillonnage sprite — **calculés mais lus par rien**,
golden engine intact.

**Livré :**
- `fields/population.py` (nouveau) — `TrophicSpec` (data-driven : ressource /
  habitat / prédateurs / canal `_hash_noise` dédié), `PopulationField`
  (sous-classe `GridField`, patron `DisturbanceField`), les 4 specs
  (`build_population_specs` : ravageur ← feuillage, monoculture ; auxiliaire ←
  ravageur, nectar+stabilité ; pollinisateur ← fleurs, rondelle ; vers_de_terre
  ← microbiome/OM, sol non perturbé), et `sample_sprites` (fonction PURE
  densité→entités, position `_hash_noise(seed, salt+slot, r, c)` **indépendante
  de la semaine**, cap par plot, scalaire `activite`).
- `fields/ecofields.py` — `EcoFields` détient `populations` (créés en
  `__post_init__`) et les ticke via `tick_populations(tile, plants)` dans l'ordre
  trophique (ravageur d'abord → lit l'auxiliaire de la semaine précédente =
  décalage). **Pas ajouté à `summary()`** (sinon le digest golden bougerait).
- `sim/engine.py` — appel `eco.tick_populations(tile, tile.plants)` en **étape
  13b**, après les autres champs (température/perturbation à jour). Aucun log
  produit.
- `tests/test_population.py` (+ `population_hash.txt`) — golden de champ
  (densités reproductibles, hash `2e6c3075…`) + bornes ∈[0,max] + cap sprites +
  positions indépendantes de la semaine.

**Décision technique (itération en cours de sprint) :** la forme du tick conçue
« cible = naissance − mort » (mort = somme de termes ABSOLUS : froid, perturbation)
**plafonnait toutes les densités à zéro** — à basse population les morts absolues
l'emportent et la cible est clampée à 0, rien ne s'établit. Remplacée par une forme
**multiplicative** : `cible = capacité_de_charge × survie`, où
`capacité = clamp(resource_w·ressource + habitat_w·habitat)` et
`survie = chaleur · (1−préd) · (1−perturbation)`. La cible **ne dépend pas de la
pop courante** → colonisation depuis zéro ; le froid (chaleur→0 l'hiver) et la
famine (pop>capacité) deviennent **implicites**. Trace de validation : montée
estivale, pic automnal ~0.2, déclin hivernal, et **décalage proie→prédateur
visible** (ravageur devance l'auxiliaire qui rattrape puis dépasse). Quantum
sprite calé à 0.06 sur cette plage émergente (2-3 sprites/plot au pic).

**Garde-fous tenus :** golden engine **INTACT** (`ee79dd66…`, vérifié avant *et*
après le changement de modèle — rien ne lit les champs en D31.1) ; canaux
`_hash_noise` dédiés par guilde, décorrélés ; terme `predator` (`effects.py:487`)
laissé en place (retiré seulement en D31.2) ; règle de couches respectée
(`population` n'importe que `grids`+`noise`, `ecofields` l'orchestre) ;
`test_genetique` 20/20, `test_auxiliaires` OK, `main.py` démarre.

**Reste D31 :** D31.2 (câblage écolo : herbivorie←ravageur, prédation←auxiliaire,
`pollinator_reach`←pollinisateur, aération←vers → **re-figeage golden unique**) ;
D31.3 (façades `vigueur_*` + gestes favoriser/écraser/fourche-bêche). Calibrage
(quantum, inerties, amplitude boom-bust) = post-test.

### Hash golden (journal de re-figeage)
`ee79dd66…` → **inchangé** (D31.1 golden-neutre par construction). Nouveau golden
de champ dédié : `population_hash.txt` = `2e6c3075…`.

---

## 2026-06-04 — Sprint impl. D31.2 : câblage écologique de la vie macroscopique (Python)

**Périmètre.** Brancher les 4 champs de population (calculés mais lus par rien en
D31.1) dans la simulation : *ce qu'on voit devient ce qui agit* (boucle vu↔agi,
`CONCEPTION_VIE_MACRO.md` §1). **Re-figeage golden assumé et unique**, comme le
sprint météo.

**Livré (4 câblages, lecture de la densité locale du champ — plus aucun proxy
reconstruit) :**
- **Herbivorie ← `ravageur`** (`sim/effects.py:herbivory_pressure`). La pression
  sur la santé dérive désormais de `eco.populations["ravageur"].at_plot(r,c)` ·
  `HERBIVORY_GAIN` (0.20) — c'est le **ravageur visible** qui mord, plus la
  reconstruction `biomass_local × HERBIVORY_BASE`.
- **Prédation ← `auxiliaire`.** Le terme `predator` reconstruit de proxies
  (biodiversité + rondelles + stabilité) **disparaît du calcul** (commenté
  « SUPPLANTÉ D31.2 — conservé pour mémoire », non supprimé). **Décision
  anti-double-comptage :** le champ ravageur intègre **déjà** la régulation par
  l'auxiliaire (sa survie est rabotée par la densité auxiliaire au tick) → lire le
  ravageur, c'est lire une pression **déjà régulée**. L'auxiliaire est donc lu
  **directement** seulement pour la **bascule létale** (`aux < 0.20 ∧ micro < 0.20`
  → dégâts doublés), pas comme second multiplicateur continu (qui double-compterait).
- **`pollinator_reach` ← `pollinisateur`** (`sim/reproduction.py`). Le rayon de
  croisement insecte est modulé par la **densité locale du champ pollinisateur**
  (saturation `POLLINATOR_SAT` = 0.40), plus par les rondelles. **Changement
  d'interface** : `pollinator_reach(mother, tile, eco)` et
  `find_father(mother, plants, tile, eco, seed, week)` (eco threadé depuis
  `engine._reproduction`). Les rondelles `pollinisateur`/`auxiliaire` restent
  **terme-source d'habitat du champ** (via `_pollinisateur_habitat_grid` /
  `_stability_grid`) → favoriser les auxiliaires nourrit toujours le brassage,
  **via le champ, pas en double**. Ancienne modulation rondelles commentée.
- **Aération/structure ← `vers_de_terre` — point ouvert tranché SOBRE.** D30
  (système structure/compaction) **n'est pas implémentée** ; je n'invente pas D30
  ici. **Couplage léger et borné** retenu (option (b) du kickoff) : la
  bioturbation des vers **accélère « un poil » la décomposition locale**
  (`tick_decomposition` : `speed += WORM_DECOMP_BONUS·worms`, 0.25 max). C'est le
  **seul** service rendu par le champ ver à la sim pour l'instant ; le système
  complet aération/infiltration/brassage des horizons **reste différé à D30**.
  Choisi plutôt que « laisser non câblé » pour **refermer vu↔agi sur les 4
  guildes** ; un retour à l'option (a) serait une ligne. *(À l'arbitrage de Nico.)*

**Ordre de tick (cohérence).** Décomposition (642), herbivorie (709) et
reproduction (698, automne) lisent toutes les populations de la semaine
**précédente** (mises à jour en 718) → décalage uniforme d'une semaine, déterministe,
**aucun nouveau RNG**.

**Validation comportementale.** `test_auxiliaires` (stress chronique monoculture,
2 tuiles jumelles) : le contraste **persiste** par le nouveau chemin — dégâts
cumulés AUX **2469** < TÉMOIN **2877** sur 30 ans, écart monotone à long terme. La
boucle « habitat → auxiliaires → champ ravageur reflue → moins de dégâts »
fonctionne. Magnitudes bien plus élevées qu'avant (l'ancien proxy donnait ~26 :
le ravageur visible mord franchement) — c'est le re-figeage attendu. `main.py`
tourne (500+ ans, sans crash, scores cohérents) ; `test_genetique` adapté (faux
`eco` exposant le champ pollinisateur) **20/20**.

**Garde-fous tenus :** code supplanté **commenté, jamais effacé** ; règle de
couches respectée ; déterminisme préservé (canaux `_hash_noise` inchangés) ;
**un seul re-figeage**, les deux hash bougent une fois (la boucle écologique se
referme : herbivorie modifie le feuillage → ressource du ravageur → densités).

### Hash golden (journal de re-figeage)
`ee79dd66…` → **`c950f06c…`** (golden engine re-figé : la santé dépend désormais
des champs). Golden de champ `population_hash.txt` : `2e6c3075…` → **`b005d9ba…`**
(la boucle écologique refermée change le feuillage, donc les densités).

---

## 2026-06-04 — Sprint impl. D31.3 : façades `vigueur_*` + gestes joueur (Python)

**Dernier tronçon de D31 — clôt la dette côté Python.** Au-dessus du tick câblé
en D31.2, on pose la **couche joueur** : des **lectures diégétiques** de la
vitalité des populations et trois **gestes** qui touchent les champs comme donnée
d'entrée. **Contraste assumé avec D31.2 :** ici le golden écolo **NE re-fige PAS**
(exactement comme le sprint Vigueur D11) — tout est event-driven, jamais appelé
par le tick. Les deux hash écolo restent **`c950f06c…`** (engine) et
**`b005d9ba…`** (champ) — **vérifiés inchangés** avant *et* après.

**A. Façades `vigueur_macro.py`** (nouveau module `sim/`, miroir read-only de
`vigueur_plante.py`). Quatre fonctions pures `vigueur_nuisible/auxiliaire/
pollinisateur/ver(r, c, eco)` = `densité(r,c) × qi_local_trophique(r,c)`, où le
`qi_local` n'est PAS le sol racinaire mais la **ressource trophique** de la guilde
— réutilisée telle quelle via `PopulationField.activite()` (déjà mémorisée au
tick, **rien à recalculer**). **Populations, pas individus** (la façade lit une
vitalité de population à un endroit ; les sprites sont des échantillons sans
Vigueur). Descripteur qualitatif `decrire_vigueur_pop` (voix naturaliste :
absente / clairsemée / vigoureuse / florissante, philo #5). Zéro écriture, zéro
nouvel état.

**B. Trois (puis quatre) gestes dans `sim/actions.py`**, granularité **§5 « un
geste = un quantum »** (`DENSITE_PAR_SPRITE = 0.06`) :
- **`favoriser_auxiliaire(gs, player, tile)`** — coût `MODÉRÉ`. Pose une rondelle
  `auxiliaire` (déjà lue par `_stability_grid` comme nectar/refuge → plancher
  d'habitat **persistant**). Le canal vertueux : les auxiliaires s'installent
  **et restent**.
- **`ecraser(gs, player, eco, r, c, urgence=True)`** — **rendu RÉEL** (l'aveu
  « aucune entité nuisible n'existe encore » est levé). Retire un quantum de
  `ravageur` au plot ciblé ; binaire tout-ou-rien, `MODÉRÉ × URGENCE` conservé.
  **Changement d'interface** (ajout `eco, r, c`) — appelants de test adaptés.
- **`becher(gs, player, eco, r, c)`** — coût `FAIBLE`. Tue la faune du sol
  (↓ `vers_de_terre` d'un quantum + ↓ `microbiome` de `BECHAGE_MICROBIOME_MALUS`
  = 0.5, knob sobre, la conception ne chiffrait pas). **Visuel avant santé** : les
  sprites de vers disparaissent *avant* la dette différée `microbiome → uptake`.
- **`grelinette(gs, player)`** — **livré** (point ouvert #2 tranché). Le jumeau
  qui **préserve** : coût `MODÉRÉ`, **ne touche ni vers ni microbiome**. Ancre le
  couple pédagogique becher/grelinette dès maintenant (contraste enseigné à
  l'œil). Son **bonus d'aération attend D30** — d'ici là il ne dépense que la
  Vigueur du travail du sol, sans dette biologique.

**Points ouverts tranchés sobre (signalés) :** (#1) habitat **tuile** (rondelle
existante), pas de champ habitat-par-plot neuf → renvoyé D30/futur ; (#2)
grelinette livrée en jumeau-qui-préserve, aération → D30.

**Hors périmètre tenu :** gain signé « manger un individu » reste **D19** (le
prérequis ciblable est désormais complet : sprite + `ecraser` réel) ; sprites
« vers morts » animés = rendu Godot ; bénéfice structure du sol = D30.

**Validation :** golden joueur `tests/test_vigueur.py` étendu **59 → 87/87**
(façades E1-E3, favoriser E4, becher/grelinette E5, et **E6 « la pression
revient »** : densité de fond installée 0.152 → écrasée 0.092 → remonte 0.130 en
4 ticks, philo #1 prouvée). Hash de trajectoire joueur **inchangé**. `main.py`
tourne (exit 0).

### Hash golden (journal — AUCUN re-figeage)
Golden engine **`c950f06c…`** et golden de champ **`b005d9ba…`** : **inchangés**
(façades read-only, gestes event-driven hors tick). C'est le test du sprint —
réussi.

---

## 2026-06-04 — Sprint impl. maîtrise D12·i1 : cœur + progression intra-objet (Python)

**Premier des 4 tronçons de l'implémentation D12** (`sprints/sprint_D12_impl/`).
On pose le **cœur** de la maîtrise — l'état par avatar, la découverte, la
progression de palier par preuves — **sans** agrégats, ponts Vigueur, seam de
coût ni détection auto (tout ça vient en i2/i3/i4). Miroir structurel exact de la
couche Vigueur D11 : couche gameplay **au-dessus du tick**, opt-in, golden écolo
intact.

**A. `sim/maitrise.py`** (nouveau, pur — lib std `math` seule, n'importe ni
`vigueur.py` ni le tick). État `game_state["maitrise"][player] = {"objets":
{<objet>: {"palier": 0..5, "preuves": int}}}`, catalogue-agnostique (un objet =
une clé string). Cinq fonctions :
- `ensure_player_maitrise` — opt-in (geste identique à `vigueur.ensure_player`).
- `palier(gs, player, objet)` — lecture pure, `0` si inconnu, ne crée rien.
- `decouvrir` — 0→1 gratuit (§2.1), idempotent, renvoie `True` ssi nouvelle.
- `preuves_requises(k)` — `ceil(BASE·R**(k-1))` (§2.3).
- `enregistrer_preuve` — crédite une preuve, franchit autant de paliers que le
  crédit le permet, renvoie le palier courant. **Monotone** (§2.4, aucun
  décrément exposé), plafonné à 5.

**Décisions i1 (sobre, signalées) :** (1) **invariant** « un objet n'entre dans le
dict qu'au palier ≥ 1 » → l'**absence** du dict EST le palier 0 (inconnu) ; lecture
d'un inconnu ne crée aucune clé (pas d'opt-in parasite). (2) **Auto-découverte** :
`enregistrer_preuve` sur un inconnu le découvre d'abord (une preuve implique qu'on
l'a observé). (3) **Consommation cumulative** : une grosse fournée franchit
plusieurs paliers d'un coup, le reliquat reste au crédit du palier suivant.
(4) **Placeholders nommés** `PREUVES_BASE=2`/`PREUVES_R=2` (courbe 2,4,8,16, visible
et croissante) → vrai calibrage `K`/`BASE`/`R` en **D12.4 post-test**.

**B. Golden joueur `tests/test_maitrise.py`** (nouveau, déterministe sans RNG,
preuves injectées). **18/18** : no-op golden (clone de `test_vigueur` — 20 ticks
engine, `"maitrise" not in gs`), découverte/idempotence/inconnu=0, courbe
croissante, progression + reliquat + auto-découverte, plafond (sur-injection 10 000
preuves → reste 5), monotonie (200 preuves non décroissantes), déterminisme.

### Hash golden (journal — AUCUN re-figeage)
Golden engine **`c950f06c…`**, golden de champ **`b005d9ba…`**, golden joueur
Vigueur **87/87** : **tous VÉRIFIÉS INCHANGÉS** avant *et* après (la maîtrise n'a
aucun point d'entrée depuis le tick — c'est le test du tronçon). `main.py` tourne
(exit 0).

---

## 2026-06-04 — Sprint impl. maîtrise D12·i2 : agrégats + ponts Vigueur (Python)

**Deuxième des 4 tronçons** (`sprints/sprint_D12_impl/`). On branche la strate 2
(agrégats dérivés) et la strate 3 (ponts vers la Vigueur §4.1/§4.3). Toujours
couche gameplay **au-dessus du tick**, golden écolo intact.

**A. `sim/maitrise.py`** (étendu, reste pur côté Vigueur — importe désormais
`plants.catalogue` pour la famille). Ajouts :
- **Spillover intra-famille (§3.1)** dans `enregistrer_preuve` : une preuve est
  pondérée par `_facteur_spillover` = `1 + SPILLOVER_RATE · Σ(palier−1 des sœurs
  découvertes de même famille)`. « Être avancé sur la tomate accélère l'aubergine,
  jamais le haricot. » Le seuil « ≥2 espèces découvertes » (§10.1) **tombe
  naturellement** : une sœur juste découverte (palier 1) transfère `palier−1 = 0`.
  Mapping famille **dérivé** de `PLANT_CATALOGUE`+`PERENNIAL_CATALOGUE` (reflète
  `plants/`, ne duplique rien) ; objet sans famille (concept/outil) → facteur 1.0.
- **Agrégats (§3.2, calculés, jamais stockés)** : `accumulation_globale` = Σ paliers
  (pool unique espèces+concepts, brut, avant log) ; `completude_ratio` = Σ /
  (PALIER_MAX × découverts) — **dénominateur = découverts seuls → aucune dilution**
  quand le catalogue grossit. Lecture pure (no-op golden préservé).
- **`palier_bonus(game_state, player)` (§4.1)** = `1 + K·log1p(accumulation)` :
  remplit l'ex-stub, **neutre 1.0** sans savoir (log1p(0)=0), rendements décroissants
  (anti-super-héros §3.2).

**B. `sim/vigueur.py`** — `palier_bonus` **délègue** à `maitrise.palier_bonus`.
**Point ouvert i2 tranché → (a)** : la signature gagne `game_state` (l'accumulation
est par-joueur ; pas d'état caché module-level → déterminisme). 5 sites internes mis
à jour. **Sens de dépendance posé : Vigueur → Maîtrise** (la capacité de Vigueur
dérive du savoir), jamais l'inverse → `maitrise.py` n'importe pas `vigueur.py`.
L'idéal §4.1 « ne pas retoucher vigueur.py » était inatteignable (bonus par-joueur) :
retouche assumée, la *forme* du pont (plafond/régen × `palier_bonus`) est inchangée.

**C. `sim/actions.py`** — sources ponctuelles §4.3 (orchestration, là où vivent déjà
`manger`/`recolter`) : `observer` (découvre + `GAIN_DECOUVERTE`, idempotent) et
`crediter_succes` (preuve + `GAIN_SUCCES` × paliers franchis). Placées ici, pas dans
`maitrise.py`, pour éviter le cycle d'import (actions voit les deux couches).

**Décisions (sobre, signalées) :** dépendance Vigueur→Maîtrise ; gains §4.3 dans la
couche d'orchestration ; `preuves` devient flottant quand le spillover joue
(`0.5×int` → exactement représentable, déterministe). Placeholders nommés
`PALIER_BONUS_K=0.05`, `SPILLOVER_RATE=0.5`, `GAIN_DECOUVERTE`/`GAIN_SUCCES` →
**calibrage D12.4**.

**D. Golden joueur** — `test_maitrise.py` **35/35** (+ agrégats, spillover,
`palier_bonus`), `test_vigueur.py` **96/96** (A4 adaptée à la nouvelle signature
+ section F : pont actif vigueur_max↑ & gains ponctuels).

### Hash golden (journal — AUCUN re-figeage)
Golden engine **`c950f06c…`**, golden de champ **`b005d9ba…`** : **VÉRIFIÉS
INCHANGÉS** avant *et* après (le pont est neutre sans couche maîtrise — golden =
succession pure sans joueur). `main.py` tourne (exit 0). **Prochain : i3** (seam
`cout_action` + table objets-touchés §10.4 sur `actions.py`).

## 2026-06-04 — Sprint impl. maîtrise D12·i3 : seam `cout_action` + table objets-touchés (Python)

**Troisième des 4 tronçons** (`sprints/sprint_D12_impl/`). On pose le **second
seam** de la maîtrise (le premier, `palier_bonus`, fait en i2) : la **réduction
du coût d'action**. La maîtrise rend les gestes moins chers en Vigueur,
*contextuellement* — geste par geste, selon ce que l'action touche. Tout dans
`sim/actions.py`, la couche d'orchestration qui voit Vigueur **et** Maîtrise ;
`maitrise.py` reste **pur** (sens de dépendance acté i2).

**A. `cout_action(game_state, player, action, objets_touches)` (§4.2)** =
`base × f_globale × f_objets`, atténuation ∈ ]0,1].
- **`f_globale`** (terme 1, connaissance écologique générale) lit la
  **complétude-ratio** de i2 (∈ [0,1], borné → pas de log) : `1 − ATT_GLOBALE_MAX
  · completude_ratio`, décroissant vers le plancher `1−ATT_GLOBALE_MAX > 0`.
- **`f_objets`** (terme 2, objets concrets touchés) = **moyenne** des
  `1 − ATT_OBJET_MAX · palier/PALIER_MAX` ; objet inconnu (palier 0) → neutre 1.0.
  Moyenne choisie (sobre, bornée : reste ∈ [plancher, 1], jamais →0 même avec
  beaucoup d'objets). `None`/`[]` → 1.0.
- **Coût NUL préservé** (§10.5) : `base == 0` (`manger`) → 0 sans rien lire.

**B. Tables data-driven.** `COUTS` regroupe les littéraux d'avant (ils deviennent
la `base` — constantes conservées, rien supprimé). `OBJETS_TOUCHES` reflète §10.4
**telle quelle** (objets STATIQUES : technique + outil/structure ; la cible vivante
est dynamique). Helpers : `_cle_espece` (reverse classe→clé catalogue, dégradation
gracieuse si introuvable) + `_objets_action` (statique ∪ clé d'espèce cible → le
**spillover famille** vient gratuitement, la maîtrise de l'espèce monte déjà via i2).

**C. Branchement des 6 gestes payants.** `recolter`/`deraciner` ajoutent la clé
d'espèce ; `ecraser`/`becher`/`grelinette`/`favoriser_auxiliaire` (actions milieu,
philo #2) = statique seule. **`ecraser`** : l'`URGENCE_MULT` reste un facteur
**séparé** appliqué par-dessus le seam (l'urgence est la phase saison, pas de la
maîtrise). `manger` inchangé (base NUL, aucun `spend`). Aucune signature publique
touchée.

**Dégradation gracieuse (§10.5).** Outils/structures/techniques n'ont **aucun état
moteur** aujourd'hui → `M.palier == 0` → contribution neutre 1.0. La table les
**nomme** pour quand leur sprint (D29/D30/D31) les câblera. Aujourd'hui seuls les
**espèces** (cible vivante) et la **complétude globale** allègent réellement.

**Décisions (sobre, signalées) :** `completude_ratio` pour le terme global (borné,
propre) ; moyenne pour le terme objets ; urgence séparée. Atténuations
`ATT_GLOBALE_MAX`/`ATT_OBJET_MAX = 0.5` = **placeholders nommés → calibrage D12.4**.

**D. Golden joueur** — `test_vigueur.py` **103/103** : A5–E **inchangés** (sans
maîtrise, `cout_action == base` → non-régression gratuite) + **section G** nouvelle
(avec maîtrise : `deraciner` coûte strictement < ELEVE ; plancher > 0 ; objet non
maîtrisé reste à base ; `manger` NUL préservé ; récolte branchée bout-en-bout).
`test_maitrise.py` **35/35** (i1/i2 intacts).

### Hash golden (journal — AUCUN re-figeage)
Golden engine **`c950f06c…`**, golden de champ **`b005d9ba…`** : **VÉRIFIÉS
INCHANGÉS** avant *et* après (le coût d'action vit au-dessus du tick — golden =
succession pure sans joueur). `main.py` tourne (exit 0). **Prochain : i4**
(détection automatique de succès §9 : signaux du tick, fenêtre d'imputation, tag
féral, gate d'observation).

## 2026-06-04 — Sprint impl. maîtrise D12·i4 : détection de succès branchée (Python) — impl. D12 COMPLÈTE

**Dernier des 4 tronçons**, le plus délicat (`sprints/sprint_D12_impl/`). Jusqu'ici
les preuves de maîtrise arrivaient **par injection** (`crediter_succes`/
`enregistrer_preuve` appelés à la main). i4 **branche la détection automatique** :
une couche **lit les signaux que le tick émet déjà** (§9.1) et en déduit, toute
seule, quand un **succès** a eu lieu (§9.0 : *une action joueur dont l'effet
émergent améliore le résultat au-delà du cours spontané, et qui est observée*).

**Nouveau module `sim/maitrise_detection.py`.** Logement **(a)** (point ouvert
majeur tranché) : module dédié appelé par le **driver** APRÈS chaque
`tick_semaine` — symétrique de `tick_player_vigueur`. Il importe `maitrise` +
`plants` ; `engine` ne l'importe **jamais** (pas d'inversion de couche). Pur au
sens golden : il **observe** le résultat d'un tick, ne le fait jamais avancer.

**A. Lecture des signaux.** Parsing du `log` retourné par le tick (marqueurs
`🌱` advance / `⏸🌑❄` stagnation / `🌰` reproduction avec tag) via regex, en
suivant la tuile courante (`[T0]`) — l'identité d'un plot = `zone=(tile_id,r,c)`.
Le **nom** de la ligne → clé catalogue (`_CLE_DE_NOM`, dérivé, non dupliqué). La
**santé** et la **naturalisation** se lisent dans l'état post-tick (`tiles[].plants`).

**B. État gameplay neuf (§9.6), au-dessus du tick.** Logé dans
`maitrise[player]["_detection"]` (maitrise.py possède `objets`, la détection
possède `_detection` → maitrise.py **reste pur**, il ignore cette clé). Contient :
*fenêtre d'imputation* (journal des gestes récents `(semaine, zone)`, largeur
`FENETRE_IMPUTATION=4`), *stagnations en attente de levée*, *tag de provenance*
(ensemble `replante` ; tout le reste **féral** par défaut — pas encore de geste
`planter`), flags `naturalise`/`experte` pour la conjonction palier 5.

**C. Règles de crédit.**
- **Lever une stagnation** (§9.2, 1→2) : `⏸/🌑/❄` en *t*, puis `🌱` de la **même
  zone** dans la fenêtre, **après un geste joueur imputable** → preuve sur
  l'espèce + le **concept lié à la cause** (sec→eau, ombre→lumière, froid→météo).
- **Amener à reproduction** (§9.2, 2→3 / 3→4) : `🌰` avec geste imputable → preuve
  espèce ; tag **biparental** → preuve **pollinisation** (§9.3).
- **Naturalisation férale** (§9.4(b)) : recrue **non `replante`** atteignant le
  stade `STAGE_NATURALISATION=2` en **pleine santé** → flag. Palier **4→5** =
  **conjonction** (`experte ∩ naturalise`).

**Garde-fous d'architecture (décisions posées, signalées).**
- **Gate d'observation** (§9.6, minimal) : on ne crédite qu'un objet **découvert**
  (`palier ≥ 1`) — jamais d'auto-découverte par la détection.
- **Nature croissante** (§9.2) : un succès ne crédite l'espèce que si sa nature
  correspond au **palier courant** (`NATURE_REQUISE`) — impossible de sauter une
  marche ; les concepts ont une nature uniforme.
- **Négatif §9.0** : une amélioration **sans geste imputable** (émergent pur, « ça
  pousse tout seul ») ne crédite **rien**.
- **Détection pure maîtrise** : elle crédite des preuves, **pas** de Vigueur (sens
  Vigueur→Maîtrise). Le pont Vigueur §4.3 d'un succès **auto** reste au driver.
- **`actions.py` inchangé** : la détection est event-driven *par tick*, les gestes
  *par clic* → le **driver** relie geste→`noter_geste` et tick→`detecter`.

**D. Golden joueur** — nouveau `tests/test_maitrise_detection.py` **20/20** :
positif (stagnation levée → espèce + concept, palier 1→2 sans appel manuel),
négatif (émergent sans geste → rien), concept par cause, gate d'observation,
nature croissante, pollinisation (biparental + geste vs autofécondation),
tag féral / naturalisation, **intégration sur un vrai `Engine`** (le parser
reconnaît le format réel du log). `test_maitrise.py` **35/35**, `test_vigueur.py`
**103/103** (injection i1–i3 intacte).

**Placeholders → calibrage D12.4** : `FENETRE_IMPUTATION`, `STAGE_NATURALISATION`,
et les Nᵢ (répétitions/palier) hérités de la courbe log d'i1.

### Hash golden (journal — AUCUN re-figeage)
Golden engine **`c950f06c…`**, golden de champ **`b005d9ba…`** : **VÉRIFIÉS
INCHANGÉS** avant *et* après (la détection lit, le tick est inchangé ; le golden =
succession pure sans joueur, ne touche jamais ce module). `main.py` tourne
(`import main OK`). **Impl. Python de D12 COMPLÈTE** — reste D12.2 (conception
bloquée), D12.4 (calibrage post-test) et D12.5 (portage C#, D24).

---

> Les anciennes entrées sont dans [`journal_archive/`](journal_archive/). La dette est dans [`DETTE.md`](DETTE.md), le backlog dans [`BACKLOG.md`](BACKLOG.md) (source unique, plus de duplication).

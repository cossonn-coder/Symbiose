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

> Les anciennes entrées sont dans [`journal_archive/`](journal_archive/). La dette est dans [`DETTE.md`](DETTE.md), le backlog dans [`BACKLOG.md`](BACKLOG.md) (source unique, plus de duplication).

# Sprint MÉMOIRE D'INOCULUM DU SOL — état vivant (FIGÉ, prêt /sprint-auto)

> Carnet de bord `/conception` (D10). Reprise à froid = lire `CLAUDE.md` + ce
> fichier + `docs/champs/sol/conception_memoire_inoculum.md`. Conception FIGÉE
> (2026-07-24) : 4 kickoffs `01→04` autosuffisants présents. Prêt pour
> `/sprint-auto sprint_memoire_inoculum`.

## Origine
`/conception D10` — « réconcilier `PathogenPressure` C#→Python ». Diagnostic :
formulation caduque (Option B, le C# est une vue). D10 se scinde en :
- **ménage** : `PathogenPressure`/`TickPathogen`/`EvaluateIndicators` sont du
  **code C# MORT** (rien de vivant ne les appelle) → à supprimer, divergence close ;
- **idée écologique retenue par Nico** : porter dans Python (source de vérité)
  une **mémoire d'inoculum de TUILE** persistante que le modèle actuel n'a pas.

## Constats de code (vérifiés)
- Python a déjà un modèle fongique riche PAR PLANTE : `fungal_disease`
  (`sim/effects/perturbations.py:166`), `damping_off` (:104), `infection_memory`
  par plante (SAR, `croissance.py:316`), vent séchant/dispersant (`_spore_load`).
- **Écart unique** vs C# : `disease_probability` (`fields/ecofields/sol.py:108`)
  = `base × (1−protection_microbiome)` — SANS terme d'inoculum accumulé.
  C# avait `base × (1 + PathogenPressure×0.5) × (1−protection)`.
- **`disease_probability` = point de greffe UNIQUE** : lu par `damping_off`,
  `fungal_disease`, mildiou-rondelle (`resolution.py:138`) ET la MAJ de
  `infection_memory` (`croissance.py:316`). ⚠ boucle de rétroaction possible si
  l'inoculum est nourri par `infection_memory` ET amplifie le signal SAR →
  borner / ne pas amplifier le canal SAR.
- **Molène ABSENTE** du catalogue Python (indicatrice C# `PathogenPressure>0.6`
  → à raviver = espèce Scrophulariaceae neuve + 5 voix).
- ~25 familles botaniques (coût d'un inoculum PAR famille = sparse mais réel).

## Problème que la mécanique résout
`infection_memory` meurt avec la plante → une tuile ayant porté une monoculture
malade repart VIERGE. Faux pour pathogènes sol/résidus (mildiou hivernant,
verticillium, fonte). Prive le jeu de la **pédagogie de rotation** (philo #2/#6).

## Décisions ARRÊTÉES
- D1 — périmètre : mémoire d'inoculum Python + ménage C# + molène. `champs/sol`. [Nico]
- D2 — source = **conséquence** : les infections RÉALISÉES qui ont vécu sur le
  plot (dépôt continu ∝ `infection_memory` au-dessus d'un seuil) + **pulse de
  résidu** à la mort d'une plante infectée. PAS de re-dérivation humidité×mono
  (évite le double-comptage avec la densité même-famille de `fungal_disease`). [Nico]
- D3 — **inoculum PAR FAMILLE** : charge indexée par famille botanique (dict
  sparse par plot). Rotation vers une autre famille = échappe à l'inoculum
  hôte-spécifique, ÉMERGENT (pas de règle spéciale : le bucket décroît quand
  l'hôte est absent). Vraie pédagogie de rotation (philo #2/#6). [Nico]
- D4 — molène INCLUSE : espèce Scrophulariaceae neuve + 5 voix, apparition par
  facteur de niche `arch_inoculum` (patron `arch_ph`/`arch_temp` de
  `seedbank.germinate_candidates`) sur inoculum total du plot élevé. [Nico]
- D5 — point de greffe UNIQUE = `disease_probability(r,c,base,family=None)` :
  `× (1 + INOC_GAIN·load[family])` SI family passée. Le signal SAR
  (`croissance.py:316`, family=None) reste SANS inoculum → **casse la boucle de
  rétroaction** inoculum→SAR→infection_memory→inoculum. [Claude, anti-runaway]
- D6 — suppression = décroissance passive `×INOC_DECAY` (hiverne puis s'efface
  en ~2 saisons) + microbiome (sols suppressifs). PAS de perturbation/bêchage
  comme réducteur (éviterait un « biner pour guérir » anti-permaculture). [Claude]

## Tronçonnage figé (perf-first, vue en dernier)
- ① **CLOS 2026-07-24** — champ `InoculumField` + alimentation (2 canaux) +
  décroissance/microbiome, DORMANT (rien ne le lit) → **golden INTACT**
  (`57c166d8d3626444e0fc9b88b360edc62c047927f7608c45fefae35a6bba08da`).
  `test_inoculum.py` 15/15. Fichiers : `fields/ecofields/inoculum.py` (neuf),
  `constants.py` (7 constantes INOC), `container.py` (champ `inoculum` + init),
  `ecofields/__init__.py` + `fields/__init__.py` (exports), `perturbations.py`
  (canal 1 dans `apply_disturbances`, canal 2 dans `deposer_mort`), `boucle.py`
  (`eco.inoculum.tick_decay(eco)` étape 4g).
- ② **CLOS 2026-07-24** — couplage `disease_probability(family)` LIVE →
  fungal_disease/damping_off/mildiou-rondelle amplifiés par l'inoculum hôte-spécifique
  (`× (1 + INOC_GAIN·load[family])`, `INOC_GAIN=1.5`) ; SAR `croissance.py:316`
  reste `family=None` (anti-runaway D5, vérifié). **golden INTACT `57c166d8…`**
  (voir §REPRISE : re-figeage attendu mais l'accumulation du smoke reste sous le
  seuil de flip discret). `test_inoculum.py` 20/20. Fichiers : `constants.py`
  (`INOC_GAIN`), `ecofields/sol.py` (signature + terme inoculum),
  `sim/effects/perturbations.py` (2 appels), `sim/effects/resolution.py` (1 appel),
  `tests/test_inoculum.py` (bloc [e] couplage).
- ③ **CLOS 2026-07-24** — molène (*Verbascum thapsus*, Scrophulariaceae, bisannuelle)
  ajoutée au catalogue + archétype `disease_indicator` (HORS gradient) + porte de RELÂCHE
  `arch_inoculum` (`germination_candidates`) + 5 voix. **golden INTACT `57c166d8…`**
  (NEUTRE atteint, PAS de re-figeage : `arch_inoculum` gate molène à 0 sur sol sain, et
  `choisir_archetype` calcule son rang sur `GRADIENT_ARCHETYPES` seul → l'ajout du 5ᵉ
  archétype ne déplace AUCUN choix des 4 classiques). `test_inoculum.py` 32/32.
  Fichiers : `ecofields/constants.py` (`INOC_MOLENE_SEUIL`), `seedbank.py`
  (`GRADIENT_ARCHETYPES`+`disease_indicator`, param `arch_inoculum`), `fields/__init__.py`
  (export), `plants/species/adventices.py` (`Molene`), `plants/species/__init__.py`,
  `plants/catalogue.py` (PLANT+WEED), `sim/succession.py` (build+pass `arch_inoculum`,
  priorité molène dans `choisir_archetype`), `sim/encyclopedie_corpus.py` (fiche),
  `sim/carnet.py` (CONCEPT_DE+GABARIT concept « maladie »), `sim/evenements.py`
  (germination molène → cause `sol_vicie`), `sim/pages_corpus.py` (P37),
  `tests/{test_inoculum,test_pages,test_encyclopedie}.py`.
- ④ **CLOS 2026-07-24** — ménage C# (`PathogenPressure`/`TickPathogen`/`Summary("pathogen")`/
  lambda indicatrice molène morts supprimés → **divergence D10 close**) + vue Godot
  (snapshot `inoculum` par tuile + F6 heatmap + banc F5 `rotation_inoculum`) —
  **golden INTACT `57c166d8…`**, `dotnet build` VERT. `test_inoculum.py` 32/32.
  Fichiers : `core/EcoFields.cs` (retrait champ+TickPathogen+Summary+ToString ;
  `DiseaseProbability` conservée mais délestée du terme `PathogenPressure`),
  `core/PlantCatalogue.Indicatrices.cs` (bloc `UnlockCondition` molène retiré),
  `tools/simserver/serialize.py` (bloc `inoculum` par tuile, liste creuse
  `[[r,c,famille_dominante,charge_totale],…]`), `tools/simserver/version.py`
  (0.5.38→**0.5.39**), `tools/simserver/commands.py` (`inoculum` au registre
  `fields` + grille dense `inoculum.total`, patron `vitalite`), `visuals/FieldOverlay.cs`
  (palette `["inoculum"]`), `bancs/edaphique.py` (`rotation_inoculum`),
  `bancs/__init__.py` (registre), 3 checks `engine_version` alignés à 0.5.39
  (`tests/simserver/{structures,conteneurs,voix}.py`, piège D76).

## SPRINT TERMINÉ (2026-07-24)
Tronçons ①②③④ TOUS CLOS. Golden INTACT `57c166d8…` de bout en bout. D10 CLOSE.

## Coût perf estimé
+1 GridField (scalaire) OU dict sparse famille→charge par plot ; accumulation
O(plots) scatter/tick, décroissance ; négligeable. Zéro RNG (accumulateur
déterministe). Golden RE-FIGÉ maîtrisé (proba de maladie change).

## §REPRISE
**SPRINT TERMINÉ 2026-07-24 — tous les tronçons ①②③④ CLOS.** Golden INTACT
`57c166d8…` de bout en bout, `test_inoculum.py` 32/32, `test_sim_server` 269/270
(le seul rouge = pommier-fruit PRÉEXISTANT, hors sujet), `dotnet build` VERT,
pont 0.5.39. **D10 CLOSE** (DETTE.md + BACKLOG.md à jour). Rien à reprendre.

Note ④ : la heatmap F6 lit l'inoculum via le registre `fields` (grille dense de
`inoculum.total` matérialisée à la demande côté pont, patron `vitalite`) plutôt que
par une lecture directe du bloc snapshot côté C# comme le suggérait le kickoff — ce
choix mirrore le précédent `vitalite`/`marais_memory` (champ dérivé → cmd_fields), ne
demande QUE la palette côté FieldOverlay, et laisse le bloc snapshot `inoculum` servir
la future vue-jeu diégétique (indice de sol vicié). Golden NEUTRE dans les deux cas.

Tronçons ①+②+③ **CLOS** (golden INTACT `57c166d8…`, `test_inoculum.py` 32/32).

**③ — molène (`03_molene.md`).** Espèce *Verbascum thapsus* (bisannuelle, rosette→hampe,
monocarpique) ajoutée en `plants/species/adventices.py`, clé `"molene"` (PLANT_CATALOGUE,
pour les voix) + archétype `"disease_indicator"` (WEED_CATALOGUE). Nouvel archétype appendu
en FIN de `SEED_ARCHETYPES` ; `GRADIENT_ARCHETYPES` (= les 4 classiques) isolé pour que
`choisir_archetype` calcule son rang cible SANS l'indicatrice → aucun choix des 4 déplacé.
Porte de RELÂCHE `arch_inoculum` dans `germination_candidates` (patron `arch_ph`) :
`smoothstep(inoculum.total, INOC_MOLENE_SEUIL, 2·SEUIL)` sur le SEUL `disease_indicator`,
1.0 partout ailleurs. `succession.py` construit et passe le dict ; `choisir_archetype`
PRIORISE molène si candidate (sa présence = terre viciée). 5 voix : encyclopédie (fiche
3 niveaux), carnet (concept NEUF « maladie » via `CONCEPT_DE`/`GABARIT` + cause `sol_vicie`
posée sur la germination molène dans `evenements.py`), pages secrètes (P37, lore médicinal),
magazine (famille Scrophulariaceae, automatique via catalogue), événements (marqueurs de
cycle au ledger). Concept « maladie » = carnet-interne (comme carnivorie), PAS dans
`encyclopedie_types.CONCEPTS` → n'a PAS touché le corpus concept (test d'alignement intact).

**GOLDEN : INTACT `57c166d8…`, NON re-figé.** NEUTRE atteint : sur le sol sain du smoke
l'inoculum reste nul → `arch_inoculum[disease_indicator]=0` → molène jamais candidate → aucun
tirage déplacé. Vérifié aussi : suites `test_encyclopedie` (65/68 = 3 échecs geste/outil
PRÉEXISTANTS, hors sujet), `test_pages` 64/64, `test_carnet` 19/19, `test_biennial`,
`test_magazine`, `test_evenements`, `test_diversite_fondatrice`, `test_competition`,
`test_paillage`, `test_maitrise_detection`, `test_genetique` — toutes vertes.

**Prochaine étape = tronçon ④** (`04_menage_cs_vue.md` s'il existe, sinon le kickoff ④) :
ménage C# (`PathogenPressure`/`TickPathogen`/`Summary("pathogen")`/lambda indicatrice morts
dans `core/EcoFields.cs`+`PlantCatalogue.Indicatrices.cs`) + vue Godot (snapshot `inoculum`,
heatmap F6, banc F5 `rotation_inoculum`) — golden INTACT, `dotnet build` à garder vert.

**② — couplage LIVE (`02_couplage_maladie.md`).** `disease_probability(r,c,base,
family=None)` lit désormais `self.inoculum.at(r,c,family)` et amplifie
`× (1 + INOC_GAIN·charge)` (`INOC_GAIN=1.5` placeholder §10). Appelants qui passent
la famille : `damping_off` + `fungal_disease` (`perturbations.py`), mildiou-rondelle
(`resolution.py`, branche `reduce_health`). Le signal SAR `croissance.py:316` reste
`family=None` → inoculum-free (anti-runaway D5 VÉRIFIÉ).

**GOLDEN : INTACT, PAS re-figé — décision assumée.** Le kickoff PRÉVOYAIT un re-figeage
maîtrisé, mais le contrôle a montré que le smoke (2 tuiles × 4 ans) accumule au plus
**0.058** d'inoculum sur **1 seul plot** (infection_memory alive plafonne à 0.284,
JUSTE sous INOC_DEPOT_SEUIL=0.3 → canal 1 tire rarement ; l'essentiel vient des pulses
de mort canal 2). L'amplification résultante (~+8,7 % sur 1 plot) ne FLIPPE aucun tirage
discret `_hash_noise < p` → hash strictement inchangé. Le couplage est bien BRANCHÉ et
change la proba CONTINUE (prouvé par `test_inoculum` bloc [e]), il ne fait juste pas
bouger le smoke. Contrôle du kickoff satisfait : à `INOC_GAIN=0` le hash retombe aussi
sur `57c166d8…` (donc la voie family=None/SAR est intouchée). **Aucun re-figeage forcé**
(cohérent avec l'interdit « ne jamais fabriquer une dérive »). Suites voisines vertes :
`test_senescence`, `test_population`.

**Prochaine étape = tronçon ③** (`03_molene.md`) : espèce Scrophulariaceae + niche
`arch_inoculum` sur `inoculum.total` élevé + 5 voix. Golden NEUTRE visé. Puis ④ ménage
C# (`PathogenPressure`/`TickPathogen` morts) + vue Godot (snapshot inoculum, heatmap F6,
banc `rotation_inoculum`).

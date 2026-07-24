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
- ② couplage `disease_probability` (family) → fungal_disease/damping_off/mildiou —
  **golden RE-FIGÉ MAÎTRISÉ** (proba maladie change, dérive localisée annoncée).
- ③ molène (espèce + `arch_inoculum` + 5 voix) — golden NEUTRE visé (re-figeage
  localisé annoncé SI l'ajout catalogue déplace un tirage smoke).
- ④ ménage C# (`PathogenPressure`/`TickPathogen` morts supprimés) + vue Godot
  (snapshot inoculum + heatmap F6 + banc F5 `rotation_inoculum`) — golden INTACT.

## Coût perf estimé
+1 GridField (scalaire) OU dict sparse famille→charge par plot ; accumulation
O(plots) scatter/tick, décroissance ; négligeable. Zéro RNG (accumulateur
déterministe). Golden RE-FIGÉ maîtrisé (proba de maladie change).

## §REPRISE
Tronçon ① **CLOS** (golden INTACT `57c166d8…`, `test_inoculum.py` 15/15). Le champ
`InoculumField` est en place, alimenté (2 canaux) et décroissant, mais DORMANT :
personne ne lit `eco.inoculum` dans la math du tick. Placeholders de calibrage posés
(INOC_MAX/EPSILON/DECAY/MICRO_SUPPRESS/DEPOT_SEUIL/FROM_MEMORY/FROM_DEATH, §10).
**Prochaine étape = tronçon ②** (`02_couplage_maladie.md`) : greffer `family` à
`disease_probability` (`× (1 + INOC_GAIN·load[family])`) pour fungal_disease/
damping_off/mildiou-rondelle, le signal SAR (`croissance.py:316`, family=None) reste
SANS inoculum (casse la boucle de rétroaction, D5). Ajouter `INOC_GAIN`.
→ **golden RE-FIGÉ MAÎTRISÉ attendu** (proba de maladie change, dérive localisée
annoncée). Puis ③ molène (NEUTRE visé) · ④ ménage C# + vue (INTACT).

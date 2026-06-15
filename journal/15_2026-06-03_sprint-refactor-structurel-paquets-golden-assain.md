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

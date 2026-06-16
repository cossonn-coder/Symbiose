## 2026-06-16 — Sprint REFACTOR GLOBAL · SS①–⑦ TOUS CLOS — golden inchangé tout le sprint

Sprint de rangement de tout le dépôt (Python + C# + docs) : regrouper par
nature, purger les fossiles, **un fichier = une responsabilité cohérente**,
fichiers courts pour relire vite. **Invariant tenu sur les 7 tronçons** : golden
`908f591bee…` JAMAIS re-figé (refactor = zéro changement de comportement) ; build
C# vert après chaque tronçon C#. Détail granulaire de chaque tronçon dans
`sprints/sprint_refactor_global/00_etat.md` (journal de bord).

**Les sept tronçons :**
- **SS① Déchets & docs** : fossiles purgés (sortie.txt 19 Mo, CV, SVG
  régénérables→gitignore), 11 `CONCEPTION_*.md` → `docs/conception/`, sprints
  clos → `sprints/_clos/`, helper `tools/compte_ldc.py` livré.
- **SS② Journal éclaté** : `journal.md` (2385 l) → `journal/` 41 fichiers
  (entrées 13→53) + `journal.md` = index de pointeurs (extraction par script
  déterministe, copie verbatim). `journal_archive/` (01-12) laissé tel quel.
- **SS③ Python cœur sim 1** : `engine.py`/`ecofields.py`/`effects.py` éclatés en
  paquets (Engine scindé par **mixins**, API ré-exportée par `__init__` → zéro
  appelant modifié).
- **SS④ Python cœur sim 2** : `base.py`/`species.py`/`growth.py`/`actions.py`
  éclatés en paquets (même méthode).
- **SS⑤ Python outils & tests** : `sim_server.py`/`render_structure.py`/
  `test_vigueur.py`/`test_sim_server.py` éclatés (entrées minces préservées,
  pont Godot intact, 19/19 suites vertes).
- **SS⑥ C# WorldView** : `WorldView.cs` (1759 l) → 9 `partial class` par concept.
  `dotnet` SDK 8.0 installé sur la VM (filet de compilation). Build vert + F5 OK.
- **SS⑦ C# reste & finition** (ce tronçon) :
  - **Purge Option B** : 15 stubs vides du portage C# abandonné (datés du
    Snapshot initial 05-29) + `Main.cs/.tscn` + `TileGrid.cs/.tscn` supprimés
    (`git rm`, historique préservé ; zéro référence en code/scène, vérifié grep
    nom-de-classe + chemin ; scène principale = `WorldView.tscn`). Décision Nico
    (AskUser) face à la tension « mai/juin = jamais supprimer » sur `TileGrid.cs`
    (202 l, juin) : tout supprimer, git récupère.
  - **Éclatements** (1 fichier = 1 classe/concept) : `PlantData` → 3, `TileData`
    → 4 (`Tile`/`StakeSlot`/`ConflictNotification`/`RondelleRules`), `GridField`
    → 3 (`GridField`/`LightField`/`EcoFields`), `PlantRenderer` → +`.Organs.cs`
    (partial) +`PlantShadow.cs`, `PlantCatalogue` (604 code, seul > 500) → shell +
    3 partials par catégorie.
  - **Règles gravées dans `CLAUDE.md`** : taille fichiers (garde-fou **~350**
    code pur, max empirique **337** = `fields/ecofields/container.py`, comptage
    `compte_ldc.py`, commentaires exclus), un fichier = une responsabilité, arbo
    cible. Le seuil descend de ~500 → ~350 (recalibrage prévu dès SS①).

**Reste à Nico** : F5 de validation visuelle finale (SS⑥+SS⑦ = refactor pur).
Branche `refactor/ss7-finition`.

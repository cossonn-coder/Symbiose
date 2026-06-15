# Sprint REFACTOR GLOBAL — état partagé

> État léger, mis à jour en **fin de chaque tronçon**. Lire ce fichier +
> le `0N_*.md` du tronçon courant suffit à reprendre à froid.

## But du sprint

Refactor de tout le dépôt (Python + C# + docs) pour s'y retrouver :
regrouper les fichiers par nature, supprimer les fossiles, et faire passer
**chaque fichier sous ~500 lignes de CODE PUR** (commentaires pédagogiques
exclus du décompte et **conservés au cœur des fichiers**).

## Invariants ABSOLUS (toute la durée du sprint)

1. **Golden jamais re-figé.** `cd data/code && python3 -m tests.test_golden`
   reste vert et le hash golden **ne bouge pas** : un refactor ne change
   AUCUN comportement. Si le hash bouge → on s'est trompé, on revient.
2. **Build Godot OK** après tout tronçon C# (compile sans erreur).
3. **~500 lignes de code pur max par fichier.** Convention de comptage =
   `tools/compte_ldc.py` (livré au SS①). Exception tolérée seulement si
   signalée + justifiée à Nico.
4. **Commentaires pédagogiques préservés et centraux** — jamais sacrifiés
   pour gagner des lignes.
5. **Granularité pragmatique** : un fichier = une classe / un concept
   cohérent (PAS une-fonction-par-fichier). Python éclaté → paquet avec
   `__init__.py` qui ré-exporte l'API publique (imports existants intacts).
6. **Avant chaque tronçon : git à jour.** Un commit par tronçon, puis
   `/clear`. Pas de suppression de code utile (cf décision ci-dessous).

## Décisions actées (2026-06-15, conversation kickoff)

- **Suppression** : seulement les fossiles (non modifiés depuis avril ET
  inutiles). Tout ce qui date de mai/juin = rangé/archivé, jamais supprimé.
- **Racine conservatrice** : Python reste dans `data/code/`, Godot à la
  racine (chemins `res://`, `.csproj`, pont `SimBridge` inchangés).
- **`docs/desktop/`** : gardé tel quel (usage propre : export app desktop).
- **Journal** : éclaté par sprint + `journal.md` = index de pointeurs.
- **Seuil 500** : recalibré en clôture (SS⑦) sur le max empirique mesuré.

## Tronçons

| SS | Titre | Risque | Statut |
|----|-------|--------|--------|
| ① | Déchets & docs/conception + helper comptage | nul | ✅ CLOS (2026-06-15) |
| ② | Journal éclaté (index + par sprint) | faible | ✅ CLOS (2026-06-15) |
| ③ | Python cœur sim 1 (engine, ecofields, effects) | élevé | ⬜ |
| ④ | Python cœur sim 2 (actions, base, species, growth) | élevé | ⬜ |
| ⑤ | Python outils & tests (sim_server, render, 2 tests) | moyen | ⬜ |
| ⑥ | C# WorldView (1759 l) | moyen | ⬜ |
| ⑦ | C# reste & finition + grave règles dans CLAUDE.md | moyen | ⬜ |

## Reprise

Tronçon courant : **SS③**. Lire `03_*.md` (Python cœur sim 1 — engine, ecofields, effects).

## Journal de bord (rempli en fin de tronçon)

- **SS① CLOS (2026-06-15)** — golden inchangé `908f591bee…` (aucun code moteur
  touché, vérifié avant/après).
  - **Helper** : `tools/compte_ldc.py` (nouveau dossier `tools/` racine = outil
    *du dépôt*, pas du moteur ; `tokenize` pour Python, repli ligne-à-ligne pour
    C#). Testé sur `.py` et `.cs`. `--seuil` (défaut 500), tri sur code pur ⚠.
  - **Fossiles purgés** : `sortie.txt` (19 Mo, avril), CV PDF (avril), 6 SVG
    maquettes régénérables (juin mais sorties de `render_structure.py` → ajoutées
    à `.gitignore`). ⚠️ **À signaler Nico** : les SVG dataient de juin (règle
    « mai/juin = ne pas supprimer ») mais le kickoff §B les classe régénérables ;
    choix de les sortir du suivi + gitignore.
  - **Conception regroupée** : 11 `CONCEPTION_*.md` → `docs/conception/` (`git mv`).
    `CONCEPTION_MAITRISE` (561 l) scindé → `maitrise/01_modele` (204) +
    `02_succes_par_axe` (100) + `03_taxonomie_objets` (140) + index (22). Contenu
    intégral préservé. **Pointeurs `data/code/CONCEPTION_` → `docs/conception/`
    corrigés** dans docstrings .py (commentaires only, golden intact) + doc vivante
    (DETTE/BACKLOG/journal/dette_kickoffs/decompo). Archives `_clos/` et
    `journal_archive/` laissées telles quelles.
  - **Sprints clos archivés** sous `sprints/_clos/` (22 entrées). Gardés en place :
    refactor_global (courant), integration_godot (t7 active), decomposition_compost
    (⑥ différé = doute), dette_kickoffs, sprint_1/2/3/4 (C# futurs), etude_sol_vivant
    (référencée Sprint 3).
  - **`integration_godot/00_etat.md`** (707 l, sprint actif) scindé : historique
    tranches 1-6 → `_avancement_t1_t3.md` (120) + `_avancement_t4_t6.md` (439) ;
    `00_etat.md` ramené à 176 l (en-tête + Tranche 7 + REPRISE, flux de reprise
    préservé).
  - **docs/desktop/** : laissé tel quel (tous < 500), RAS.
- **SS② CLOS (2026-06-15)** — golden inchangé `908f591bee…` (aucun code moteur
  touché). `journal.md` (2385 l) éclaté → **`journal/` 41 fichiers** (entrées
  inline, numérotées 13→53, convention `NN_date_slug.md`) + `journal.md` réduit
  à un **index de pointeurs (89 l)**.
  - **Extraction par script déterministe** (copie verbatim, zéro reformulation) :
    découpe aux frontières `## YYYY-MM-DD`. Complétude prouvée : 1948 lignes
    non-blanches identiques source↔fichiers (seule normalisation = lignes
    blanches inter-entrées collapsées). Tous < 500 l (max 82).
  - **`journal_archive/` LAISSÉ tel quel** (décision tranchée) : déjà éclaté
    même convention, nommé emplacement historique stable dans `CLAUDE.md` ET
    référencé par sprints clos (`sprints/_clos/`, mémoire figée) → unification
    casserait des pointeurs historiques, donc pas « propre ». Deux dossiers à
    sémantique claire : `journal_archive/` (01-12, avant refactor structurel) +
    `journal/` (13-53, le reste).
  - **Liens** : aucune ancre profonde `journal.md#section` externe. 53 liens de
    l'index vérifiés (0 cassé). Renvois « voir `journal.md` » (CLAUDE.md l.81/330,
    BACKLOG, _clos) restent valides : `journal.md` existe comme index.
  - ⚠️ **À signaler Nico** : `CLAUDE.md` l.330 dit « `journal.md` (entrées
    récentes) + `journal_archive/` » — désormais légèrement imprécis (les entrées
    récentes sont dans `journal/`, pointées par l'index). Laissé tel quel
    (surgical / un fichier à la fois) ; à rafraîchir au SS⑦ qui grave les règles
    dans CLAUDE.md.
